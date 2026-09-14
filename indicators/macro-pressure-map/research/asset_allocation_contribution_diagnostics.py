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
import math
from pathlib import Path

import numpy as np
import pandas as pd

from asset_allocation_phase_a import ASSETS
from asset_allocation_phase_a_frozen import load_frozen_transitions, map_regimes_to_outcome_calendar
from issue_64_durable_validation import validate_phase_b_generated_evidence
from issue_64_outcome_snapshot import load_frozen_prices

HERE = Path(__file__).resolve().parent
PHASE_B_DECISION = HERE / "decisions" / "issue-64-phase-b.json"
PHASE_C_DECISION = HERE / "decisions" / "issue-64-phase-c.json"
FULL_SEGMENT = "full_reused_history"
PHASE_C_STRATEGY = "phase_c_combined"
PHASE_B_STRATEGY = "phase_b_reflation_only"
STAGFLATION_REGIME = "Stagflation Pressure"
REFLATION_REGIME = "Reflation / Inflation Rising"
SLOWDOWN_DISINFLATION_REGIME = "Slowdown / Disinflation"

SEGMENTS = {
    FULL_SEGMENT: (None, None),
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


def _single_row(table: pd.DataFrame, table_name: str, **filters: object) -> pd.Series:
    mask = pd.Series(True, index=table.index)
    for column, value in filters.items():
        if column not in table.columns:
            raise ValueError(f"{table_name} is missing required column {column}")
        mask &= table[column].eq(value)
    rows = table.loc[mask]
    if len(rows) != 1:
        raise ValueError(f"expected exactly one {table_name} row for {filters}, found {len(rows)}")
    return rows.iloc[0]


def _reject_nonfinite_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant is not allowed in durable Phase C decision: {value}")


def validate_phase_c_durable_contribution_audit(
    asset: pd.DataFrame,
    regime: pd.DataFrame,
    reconciliation: pd.DataFrame,
    decision: dict,
) -> dict:
    """Fail closed if verdict-bearing Phase C contribution values drift.

    Reconciliation alone is insufficient: internally consistent contribution
    tables could still change the historical attribution used by the durable
    `risk_management_value_only` interpretation. This validator binds the
    regenerated full-history contribution values to the committed decision.
    """
    if int(decision.get("schema_version", 0)) < 5:
        raise ValueError("Phase C decision schema must include durable contribution-value binding")
    binding = decision["regenerated_evidence_binding"]
    audit = decision["portfolio_contribution_audit"]
    expected_c = audit["full_history_phase_c_combined"]
    tolerance = float(binding["contribution_value_tolerance"])
    if not math.isfinite(tolerance) or tolerance <= 0.0:
        raise ValueError("contribution-value tolerance must be finite and positive")

    observed_errors: dict[str, float] = {}

    def check(name: str, actual: float, expected: float) -> None:
        actual_value = float(actual)
        expected_value = float(expected)
        if not math.isfinite(actual_value) or not math.isfinite(expected_value):
            raise ValueError(
                "non-finite durable contribution value: "
                f"check={name}, actual={actual_value}, expected={expected_value}"
            )
        error = abs(actual_value - expected_value)
        if not math.isfinite(error):
            raise ValueError(f"non-finite durable contribution error for {name}: {error}")
        observed_errors[name] = error

    full_recon = _single_row(
        reconciliation,
        "reconciliation",
        strategy=PHASE_C_STRATEGY,
        segment=FULL_SEGMENT,
    )
    check(
        "phase_c_annualized_arithmetic_net_return",
        full_recon["annualized_arithmetic_net_return"],
        expected_c["annualized_arithmetic_net_return"],
    )

    for asset_name in ASSETS:
        row = _single_row(
            asset,
            "asset contribution",
            strategy=PHASE_C_STRATEGY,
            segment=FULL_SEGMENT,
            component=asset_name,
        )
        check(
            f"phase_c_asset_{asset_name}",
            row["annualized_arithmetic_contribution"],
            expected_c["annualized_asset_contribution"][asset_name],
        )

    cost_row = _single_row(
        asset,
        "asset contribution",
        strategy=PHASE_C_STRATEGY,
        segment=FULL_SEGMENT,
        component="transaction_cost_residual",
    )
    check(
        "phase_c_transaction_cost_residual",
        cost_row["annualized_arithmetic_contribution"],
        expected_c["annualized_transaction_cost_residual"],
    )

    phase_c_stag = _single_row(
        regime,
        "regime contribution",
        strategy=PHASE_C_STRATEGY,
        segment=FULL_SEGMENT,
        executed_lagged_regime=STAGFLATION_REGIME,
    )
    for asset_name in ASSETS:
        check(
            f"phase_c_stagflation_average_weight_{asset_name}",
            phase_c_stag[f"average_invested_weight_{asset_name}"],
            expected_c["stagflation_realized_average_allocation"][asset_name],
        )
    check(
        "phase_c_stagflation_net_contribution",
        phase_c_stag["annualized_net_return_contribution"],
        expected_c["stagflation_annualized_net_return_contribution"],
    )

    phase_c_reflation = _single_row(
        regime,
        "regime contribution",
        strategy=PHASE_C_STRATEGY,
        segment=FULL_SEGMENT,
        executed_lagged_regime=REFLATION_REGIME,
    )
    check(
        "phase_c_reflation_net_contribution",
        phase_c_reflation["annualized_net_return_contribution"],
        expected_c["reflation_annualized_net_return_contribution"],
    )

    phase_c_slowdown = _single_row(
        regime,
        "regime contribution",
        strategy=PHASE_C_STRATEGY,
        segment=FULL_SEGMENT,
        executed_lagged_regime=SLOWDOWN_DISINFLATION_REGIME,
    )
    check(
        "phase_c_slowdown_disinflation_net_contribution",
        phase_c_slowdown["annualized_net_return_contribution"],
        expected_c["slowdown_disinflation_annualized_net_return_contribution"],
    )

    phase_b_stag = _single_row(
        regime,
        "regime contribution",
        strategy=PHASE_B_STRATEGY,
        segment=FULL_SEGMENT,
        executed_lagged_regime=STAGFLATION_REGIME,
    )
    phase_b_stag_value = float(phase_b_stag["annualized_net_return_contribution"])
    phase_c_stag_value = float(phase_c_stag["annualized_net_return_contribution"])
    check(
        "phase_b_stagflation_net_contribution",
        phase_b_stag_value,
        audit["full_history_phase_b_stagflation_regime_contribution"],
    )
    check(
        "stagflation_contribution_improvement_vs_phase_b",
        phase_c_stag_value - phase_b_stag_value,
        audit["stagflation_regime_contribution_improvement_vs_phase_b"],
    )

    worst_name, max_abs_error = max(observed_errors.items(), key=lambda item: item[1])
    if not math.isfinite(max_abs_error):
        raise ValueError(f"non-finite maximum durable contribution error: {max_abs_error}")
    if max_abs_error > tolerance:
        raise RuntimeError(
            "Phase C durable contribution audit drifted: "
            f"worst={worst_name}, error={max_abs_error}, tolerance={tolerance}"
        )
    return {
        "validated": True,
        "check_count": int(len(observed_errors)),
        "max_abs_error": float(max_abs_error),
        "worst_check": worst_name,
        "tolerance": tolerance,
    }


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
            for asset_name in ASSETS:
                values = asset_daily.loc[idx, asset_name]
                contribution_value = float(values.sum() / denom * annualization)
                component_total += contribution_value
                asset_rows.append({
                    "strategy": strategy,
                    "segment": segment,
                    "component": asset_name,
                    "component_type": "asset",
                    "observations": int(len(idx)),
                    "mean_daily_contribution": float(values.mean()),
                    "annualized_arithmetic_contribution": contribution_value,
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
                for asset_name in ASSETS:
                    row[f"average_invested_weight_{asset_name}"] = float(weights.loc[regime_idx, asset_name].mean())
                    row[f"annualized_{asset_name}_contribution"] = float(
                        asset_daily.loc[regime_idx, asset_name].sum() / denom * annualization
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

    durable_validation = None
    if phase_prefix == "phase-c":
        decision = json.loads(
            PHASE_C_DECISION.read_text(encoding="utf-8"),
            parse_constant=_reject_nonfinite_json_constant,
        )
        audit = decision["portfolio_contribution_audit"]
        if price_manifest.get("source_mode") != audit["price_source_mode"]:
            raise RuntimeError("Phase C contribution audit price-source mode drifted")
        if price_manifest.get("snapshot_csv_sha256") != audit["price_snapshot_csv_sha256"]:
            raise RuntimeError("Phase C contribution audit frozen-price SHA drifted")
        durable_validation = validate_phase_c_durable_contribution_audit(
            asset,
            regime,
            reconciliation,
            decision,
        )

    asset_path = phase_dir / f"{phase_prefix}-asset-contribution.csv"
    regime_path = phase_dir / f"{phase_prefix}-regime-allocation-contribution.csv"
    reconciliation_path = phase_dir / f"{phase_prefix}-contribution-reconciliation.csv"
    asset.to_csv(asset_path, index=False)
    regime.to_csv(regime_path, index=False)
    reconciliation.to_csv(reconciliation_path, index=False)

    if phase_prefix == "phase-b":
        durable_validation = validate_phase_b_generated_evidence(phase_dir, PHASE_B_DECISION)

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
    if durable_validation is not None:
        if phase_prefix == "phase-b":
            result["durable_phase_b_evidence_audit"] = durable_validation
        else:
            result["durable_contribution_audit"] = durable_validation
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
