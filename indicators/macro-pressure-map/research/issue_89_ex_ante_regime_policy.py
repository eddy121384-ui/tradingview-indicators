#!/usr/bin/env python3
"""Issue #89: ex-ante V6.6 regime allocation policy versus static portfolios.

The policy matrix is read from a preregistered contract and is never inferred
from asset returns. V6.6 supplies only the frozen state classification.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from asset_allocation_phase_a import ASSETS, REGIMES
from asset_allocation_phase_a_frozen import load_frozen_transitions, map_regimes_to_outcome_calendar
from asset_allocation_phase_b import (
    causal_inverse_vol_targets,
    month_start_mask,
    portfolio_metrics,
    simulate_portfolio,
    summarize_strategies,
    template_change_mask,
    weights_series,
)
from asset_allocation_contribution_diagnostics import build_contribution_tables
from issue_64_outcome_snapshot import load_frozen_prices

HERE = Path(__file__).resolve().parent
DEFAULT_CONTRACT = HERE / "decisions" / "issue-89-preregistered-policy.json"
STRATEGY = "v66_ex_ante_regime_policy"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_weights(weights: dict[str, float], name: str) -> None:
    if set(weights) != set(ASSETS):
        raise ValueError(f"{name} must define exactly {ASSETS}")
    values = np.asarray([float(weights[a]) for a in ASSETS], dtype=float)
    if not np.isfinite(values).all() or (values < 0.0).any():
        raise ValueError(f"{name} contains invalid weights")
    if not np.isclose(values.sum(), 1.0, atol=1e-12):
        raise ValueError(f"{name} weights must sum to one")


def load_contract(path: Path = DEFAULT_CONTRACT) -> dict:
    contract = json.loads(path.read_text(encoding="utf-8"))
    if contract.get("issue") != 89:
        raise ValueError("unexpected Issue #89 contract identity")
    if contract.get("frozen_before_issue_89_portfolio_results_viewed") is not True:
        raise ValueError("Issue #89 policy must be frozen before results")
    if contract.get("return_fitted_weight_selection_allowed") is not False:
        raise ValueError("Issue #89 may not fit policy weights to returns")
    if contract.get("weight_tuning_after_results_allowed") is not False:
        raise ValueError("Issue #89 may not tune policy weights after results")
    if contract.get("production_v66_parameters_modified") is not False:
        raise ValueError("Issue #89 may not modify V6.6")
    matrix = contract["policy"]["matrix"]
    if set(matrix) != set(REGIMES):
        raise ValueError("Issue #89 policy matrix must define every frozen V6.6 regime exactly once")
    for regime, weights in matrix.items():
        validate_weights(weights, regime)
    for name in ("fixed_60_40", "fixed_equal_weight", "fixed_neutral_40_40_20"):
        validate_weights(contract["benchmarks"][name]["weights"], name)
    return contract


def build_policy_targets(regimes: pd.Series, contract: dict) -> tuple[pd.DataFrame, pd.Series]:
    """Map yesterday's frozen regime to today's preregistered target."""
    lagged = regimes.shift(1)
    matrix = contract["policy"]["matrix"]
    data = pd.DataFrame(np.nan, index=regimes.index, columns=list(ASSETS), dtype=float)
    for regime in REGIMES:
        mask = lagged.eq(regime)
        row = np.asarray([float(matrix[regime][asset]) for asset in ASSETS], dtype=float)
        data.loc[mask, list(ASSETS)] = row
    template = lagged.astype("object")
    template.loc[lagged.isna()] = pd.NA
    known = lagged.notna()
    if known.any() and data.loc[known].isna().any(axis=None):
        missing = sorted(set(lagged.loc[known].astype(str)).difference(matrix))
        raise ValueError(f"unmapped V6.6 regimes: {missing}")
    return data, template


def determine_eval_index(
    prices: pd.DataFrame,
    regimes: pd.Series,
    contract: dict,
) -> tuple[pd.DatetimeIndex, pd.DataFrame]:
    cutoff = pd.Timestamp(contract["comparison_window"]["end"])
    prices = prices.loc[prices.index <= cutoff].copy()
    regimes = regimes.reindex(prices.index)
    returns_all = prices.pct_change(fill_method=None)
    lagged_regime = regimes.shift(1)
    lookback = int(contract["benchmarks"]["causal_inverse_volatility"]["lookback_trading_rows"])
    inv = causal_inverse_vol_targets(returns_all, lookback)
    valid = (
        returns_all.notna().all(axis=1)
        & lagged_regime.notna()
        & inv.notna().all(axis=1)
    )
    valid_dates = valid.index[valid]
    if valid_dates.empty:
        raise RuntimeError("no common Issue #89 evaluation start")
    start = valid_dates[0]
    index = prices.index[(prices.index >= start) & (prices.index <= cutoff)]
    if not returns_all.loc[index].notna().all(axis=None):
        raise RuntimeError("non-finite common asset returns inside Issue #89 window")
    if not lagged_regime.loc[index].notna().all():
        raise RuntimeError("missing lagged regime inside Issue #89 window")
    if not inv.loc[index].notna().all(axis=None):
        raise RuntimeError("missing inverse-vol target inside Issue #89 window")
    return index, returns_all


def build_targets(
    eval_index: pd.DatetimeIndex,
    regimes: pd.Series,
    returns_all: pd.DataFrame,
    contract: dict,
) -> tuple[dict[str, pd.DataFrame], dict[str, pd.Series], pd.Series]:
    policy_targets, template = build_policy_targets(regimes, contract)
    policy_targets = policy_targets.loc[eval_index]
    template = template.loc[eval_index]
    monthly = month_start_mask(eval_index)
    event = template_change_mask(template)
    targets = {
        STRATEGY: policy_targets,
        "fixed_60_40": weights_series(contract["benchmarks"]["fixed_60_40"]["weights"], eval_index),
        "fixed_equal_weight": weights_series(contract["benchmarks"]["fixed_equal_weight"]["weights"], eval_index),
        "fixed_neutral_40_40_20": weights_series(contract["benchmarks"]["fixed_neutral_40_40_20"]["weights"], eval_index),
    }
    lookback = int(contract["benchmarks"]["causal_inverse_volatility"]["lookback_trading_rows"])
    targets["causal_inverse_volatility"] = causal_inverse_vol_targets(returns_all, lookback).loc[eval_index]
    rebalance = {
        STRATEGY: (monthly | event).astype(bool),
        "fixed_60_40": monthly,
        "fixed_equal_weight": monthly,
        "fixed_neutral_40_40_20": monthly,
        "causal_inverse_volatility": monthly,
    }
    return targets, rebalance, template


def run_issue_89(start: str, output_dir: Path) -> dict:
    contract = load_contract()
    prices, price_manifest = load_frozen_prices(start, None)
    expected = contract["outcome_snapshot"]
    if price_manifest["snapshot_csv_sha256"] != expected["csv_sha256"]:
        raise RuntimeError("Issue #89 frozen outcome CSV SHA drifted")
    if price_manifest["snapshot_archive_sha256"] != expected["archive_sha256"]:
        raise RuntimeError("Issue #89 frozen outcome archive SHA drifted")

    history = map_regimes_to_outcome_calendar(prices, load_frozen_transitions())
    regimes = history["core_regime"]
    eval_index, returns_all = determine_eval_index(prices, regimes, contract)
    returns = returns_all.loc[eval_index, list(ASSETS)]
    targets, rebalance, template = build_targets(eval_index, regimes, returns_all, contract)

    cost = float(contract["transaction_cost"]["primary_bps_per_one_way_turnover"])
    simulations = {
        name: simulate_portfolio(returns, targets[name], rebalance[name], cost_bps=cost, name=name)
        for name in targets
    }
    annualization = int(contract["metrics"]["annualization_trading_rows"])
    summary = summarize_strategies(simulations, annualization)

    sensitivity_rows: list[dict] = []
    costs = sorted(set(float(x) for x in contract["transaction_cost"]["sensitivity_bps_per_one_way_turnover"]))
    for sensitivity_cost in costs:
        for name in targets:
            sim = simulate_portfolio(
                returns,
                targets[name],
                rebalance[name],
                cost_bps=sensitivity_cost,
                name=name,
            )
            sensitivity_rows.append({
                "cost_bps": sensitivity_cost,
                "strategy": name,
                **portfolio_metrics(sim, annualization=annualization),
            })
    sensitivity = pd.DataFrame(sensitivity_rows)

    output_dir.mkdir(parents=True, exist_ok=True)
    daily = pd.concat([sim.reset_index() for sim in simulations.values()], ignore_index=True)
    daily.to_csv(output_dir / "issue-89-daily.csv", index=False, date_format="%Y-%m-%d")
    summary.to_csv(output_dir / "issue-89-summary.csv", index=False)
    sensitivity.to_csv(output_dir / "issue-89-cost-sensitivity.csv", index=False)

    executed_regimes = regimes.shift(1)
    asset, regime_contrib, reconciliation = build_contribution_tables(
        daily,
        prices,
        executed_regimes,
        annualization=annualization,
    )
    asset.to_csv(output_dir / "issue-89-asset-contribution.csv", index=False)
    regime_contrib.to_csv(output_dir / "issue-89-regime-allocation-contribution.csv", index=False)
    reconciliation.to_csv(output_dir / "issue-89-contribution-reconciliation.csv", index=False)

    policy_days = template.value_counts().reindex(REGIMES, fill_value=0)
    transition_count = int(template.ne(template.shift(1)).iloc[1:].sum())
    manifest = {
        "schema_version": 1,
        "issue": 89,
        "purpose": "evaluate a preregistered non-return-fitted V6.6 economic regime allocation policy",
        "contract_path": str(DEFAULT_CONTRACT.relative_to(HERE)),
        "contract_sha256": sha256_file(DEFAULT_CONTRACT),
        "contract_frozen_before_results": True,
        "return_fitted_weight_selection": False,
        "weight_tuning_after_results": False,
        "price_source_mode": price_manifest["source_mode"],
        "price_snapshot_csv_sha256": price_manifest["snapshot_csv_sha256"],
        "price_snapshot_archive_sha256": price_manifest["snapshot_archive_sha256"],
        "evaluation_first_date": eval_index.min().date().isoformat(),
        "evaluation_last_date": eval_index.max().date().isoformat(),
        "evaluation_rows": int(len(eval_index)),
        "primary_cost_bps": cost,
        "policy_transition_count": transition_count,
        "policy_regime_target_days": {regime: int(policy_days.loc[regime]) for regime in REGIMES},
        "v66_parameters_modified": False,
        "durable_verdict_committed": False,
        "interpretation_boundary": "reused historical validation; results cannot be called untouched OOS or production validation",
    }
    (output_dir / "issue-89-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    full = summary.loc[summary["segment"].eq("full_reused_history")]
    report = [
        "# Issue #89 — ex-ante V6.6 regime allocation policy",
        "",
        f"Evaluation: {manifest['evaluation_first_date']} through {manifest['evaluation_last_date']} ({manifest['evaluation_rows']} rows).",
        f"Primary cost: {cost:.1f} bps per 100% one-way turnover.",
        "",
        "The allocation matrix was fixed before viewing Issue #89 portfolio results and was not fitted to SPY/TLT/GLD returns.",
        "",
        "## Full-history summary",
        "",
    ]
    for _, row in full.iterrows():
        report.append(
            f"- {row['strategy']}: CAGR {row['CAGR']:.4%}; vol {row['annualized_volatility']:.4%}; "
            f"Sharpe {row['Sharpe']:.3f}; max DD {row['maximum_drawdown']:.4%}; "
            f"Calmar {row['Calmar']:.3f}; turnover {row['annualized_turnover']:.3f}x/year."
        )
    (output_dir / "issue-89-report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Issue #89 ex-ante regime allocation policy")
    parser.add_argument("--start", default="2007-01-01")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run_issue_89(args.start, args.output_dir), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
