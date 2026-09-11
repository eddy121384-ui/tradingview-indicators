#!/usr/bin/env python3
"""Issue #64 additive portfolio contribution diagnostics.

The Issue #64 contract requires average allocation by regime, asset contribution,
and regime contribution. This module computes those diagnostics from the exact
portfolio daily output without changing any allocation rule.

Contribution convention
-----------------------
For each day and asset, gross arithmetic return contribution is
`invested_weight * asset_return`. Transaction costs (including the small
cost/return interaction implied by deducting cost before applying the day's
asset-mix return) are retained as a separate residual:
`net_return - gross_asset_mix_return`.

This makes the asset components plus cost residual reconcile exactly to the
portfolio's arithmetic net return. Regime contribution uses the *lagged* V6.6
regime available for that trading day, so it does not introduce lookahead.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from asset_allocation_phase_a import ASSETS
from asset_allocation_phase_a_frozen import load_frozen_transitions, map_regimes_to_outcome_calendar
from issue_64_outcome_snapshot import load_frozen_prices

SEGMENTS = {
    "full_reused_history": (None, None),
    "development_pre2020": (None, "2019-12-31"),
    "post2019_reused_exploratory": ("2020-01-01", None),
}


def _segment_index(index: pd.DatetimeIndex, start: str | None, end: str | None) -> pd.DatetimeIndex:
    mask = pd.Series(True, index=index)
    if start is not None:
        mask &= index >= pd.Timestamp(start)
    if end is not None:
        mask &= index <= pd.Timestamp(end)
    return index[mask.to_numpy()]


def build_contribution_tables(
    daily: pd.DataFrame,
    prices: pd.DataFrame,
    executed_regimes: pd.Series,
    *,
    annualization: int = 252,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return asset, regime/allocation, and reconciliation diagnostics."""
    required = {
        "date",
        "strategy",
        "net_return",
        "gross_asset_mix_return",
        *(f"invested_weight_{asset}" for asset in ASSETS),
    }
    missing = required.difference(daily.columns)
    if missing:
        raise ValueError(f"daily portfolio evidence is missing columns: {sorted(missing)}")
    if annualization <= 0:
        raise ValueError("annualization must be positive")

    panel = daily.copy()
    panel["date"] = pd.to_datetime(panel["date"], errors="raise")
    prices = prices.copy()
    prices.index = pd.DatetimeIndex(pd.to_datetime(prices.index, errors="raise")).astype("datetime64[ns]")
    returns = prices.loc[:, list(ASSETS)].pct_change(fill_method=None)
    executed_regimes = executed_regimes.copy()
    executed_regimes.index = pd.DatetimeIndex(pd.to_datetime(executed_regimes.index, errors="raise")).astype("datetime64[ns]")

    asset_rows: list[dict] = []
    regime_rows: list[dict] = []
    reconciliation_rows: list[dict] = []

    for strategy, raw_block in panel.groupby("strategy", sort=False):
        block = raw_block.sort_values("date").set_index("date")
        if block.index.duplicated().any():
            raise ValueError(f"duplicate daily rows for strategy {strategy}")
        asset_returns = returns.reindex(block.index)
        if asset_returns.isna().any(axis=None):
            raise ValueError(f"missing frozen asset return for strategy {strategy}")
        regime = executed_regimes.reindex(block.index)
        if regime.isna().any():
            raise ValueError(f"missing lagged executed regime for strategy {strategy}")

        weights = pd.DataFrame(
            {asset: block[f"invested_weight_{asset}"].astype(float) for asset in ASSETS},
            index=block.index,
        )
        asset_daily = weights * asset_returns
        reconstructed_gross = asset_daily.sum(axis=1)
        reported_gross = block["gross_asset_mix_return"].astype(float)
        if not np.allclose(reconstructed_gross.to_numpy(float), reported_gross.to_numpy(float), atol=2e-12, rtol=0.0):
            raise ValueError(f"asset contributions do not reproduce gross return for strategy {strategy}")
        net = block["net_return"].astype(float)
        cost_residual = net - reconstructed_gross

        for segment, (start, end) in SEGMENTS.items():
            idx = _segment_index(block.index, start, end)
            if len(idx) == 0:
                continue
            denom = float(len(idx))
            expected_ann_net = float(net.loc[idx].mean() * annualization)

            component_total = 0.0
            for asset in ASSETS:
                values = asset_daily.loc[idx, asset]
                contribution = float(values.sum() / denom * annualization)
                component_total += contribution
                asset_rows.append({
                    "strategy": strategy,
                    "segment": segment,
                    "component": asset,
                    "component_type": "asset",
                    "observations": int(len(idx)),
                    "mean_daily_contribution": float(values.mean()),
                    "annualized_arithmetic_contribution": contribution,
                })
            cost_values = cost_residual.loc[idx]
            cost_contribution = float(cost_values.sum() / denom * annualization)
            component_total += cost_contribution
            asset_rows.append({
                "strategy": strategy,
                "segment": segment,
                "component": "transaction_cost_residual",
                "component_type": "cost",
                "observations": int(len(idx)),
                "mean_daily_contribution": float(cost_values.mean()),
                "annualized_arithmetic_contribution": cost_contribution,
            })

            regime_total = 0.0
            segment_regime = regime.loc[idx]
            for regime_name in pd.unique(segment_regime):
                regime_idx = segment_regime.index[segment_regime.eq(regime_name)]
                n_regime = len(regime_idx)
                if n_regime == 0:
                    continue
                row = {
                    "strategy": strategy,
                    "segment": segment,
                    "executed_lagged_regime": str(regime_name),
                    "observations": int(n_regime),
                    "occupancy": float(n_regime / denom),
                }
                for asset in ASSETS:
                    row[f"average_invested_weight_{asset}"] = float(weights.loc[regime_idx, asset].mean())
                    row[f"annualized_{asset}_contribution"] = float(
                        asset_daily.loc[regime_idx, asset].sum() / denom * annualization
                    )
                row["annualized_cost_contribution"] = float(
                    cost_residual.loc[regime_idx].sum() / denom * annualization
                )
                row["annualized_net_return_contribution"] = float(
                    net.loc[regime_idx].sum() / denom * annualization
                )
                row["conditional_annualized_net_return"] = float(net.loc[regime_idx].mean() * annualization)
                regime_total += row["annualized_net_return_contribution"]
                regime_rows.append(row)

            component_error = float(component_total - expected_ann_net)
            regime_error = float(regime_total - expected_ann_net)
            if abs(component_error) > 2e-12 or abs(regime_error) > 2e-12:
                raise RuntimeError(
                    f"contribution reconciliation failed for {strategy}/{segment}: "
                    f"asset_error={component_error}, regime_error={regime_error}"
                )
            reconciliation_rows.append({
                "strategy": strategy,
                "segment": segment,
                "observations": int(len(idx)),
                "annualized_arithmetic_net_return": expected_ann_net,
                "asset_plus_cost_contribution_sum": float(component_total),
                "regime_contribution_sum": float(regime_total),
                "asset_reconciliation_error": component_error,
                "regime_reconciliation_error": regime_error,
            })

    return (
        pd.DataFrame(asset_rows),
        pd.DataFrame(regime_rows),
        pd.DataFrame(reconciliation_rows),
    )


def run(phase_dir: Path, phase_prefix: str) -> dict:
    if phase_prefix not in {"phase-b", "phase-c"}:
        raise ValueError("phase-prefix must be phase-b or phase-c")
    daily_path = phase_dir / f"{phase_prefix}-daily.csv"
    if not daily_path.exists():
        raise FileNotFoundError(daily_path)

    daily = pd.read_csv(daily_path)
    prices, price_manifest = load_frozen_prices("2007-01-01", None)
    history = map_regimes_to_outcome_calendar(prices, load_frozen_transitions())
    executed_regimes = history["core_regime"].shift(1)
    asset, regime, reconciliation = build_contribution_tables(daily, prices, executed_regimes)

    asset_path = phase_dir / f"{phase_prefix}-asset-contribution.csv"
    regime_path = phase_dir / f"{phase_prefix}-regime-allocation-contribution.csv"
    reconciliation_path = phase_dir / f"{phase_prefix}-contribution-reconciliation.csv"
    asset.to_csv(asset_path, index=False)
    regime.to_csv(regime_path, index=False)
    reconciliation.to_csv(reconciliation_path, index=False)

    result = {
        "phase_prefix": phase_prefix,
        "price_source_mode": price_manifest.get("source_mode"),
        "price_snapshot_csv_sha256": price_manifest.get("snapshot_csv_sha256"),
        "asset_contribution_rows": int(len(asset)),
        "regime_contribution_rows": int(len(regime)),
        "reconciliation_rows": int(len(reconciliation)),
        "max_abs_asset_reconciliation_error": float(reconciliation["asset_reconciliation_error"].abs().max()),
        "max_abs_regime_reconciliation_error": float(reconciliation["regime_reconciliation_error"].abs().max()),
        "contribution_semantics": "annualized arithmetic contribution; asset components plus transaction-cost residual reconcile exactly to net arithmetic return",
        "regime_semantics": "executed_lagged_regime is prior-bar V6.6 core regime available for the current return row",
    }
    (phase_dir / f"{phase_prefix}-contribution-manifest.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Issue #64 portfolio contribution diagnostics")
    parser.add_argument("--phase-dir", type=Path, required=True)
    parser.add_argument("--phase-prefix", choices=["phase-b", "phase-c"], required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.phase_dir, args.phase_prefix), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
