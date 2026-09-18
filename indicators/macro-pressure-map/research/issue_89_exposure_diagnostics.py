#!/usr/bin/env python3
"""Issue #89 realized-exposure-matched static attribution control."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from asset_allocation_phase_a import ASSETS
from asset_allocation_phase_b import month_start_mask, portfolio_metrics, segment_sim, simulate_portfolio, weights_series
from asset_allocation_phase_b_diagnostics import (
    MATCH_TOLERANCE,
    delta_metrics,
    mean_invested_weights,
    solve_static_target_for_realized_average,
)
from issue_64_outcome_snapshot import load_frozen_prices
from issue_89_ex_ante_regime_policy import DEFAULT_CONTRACT, STRATEGY, load_contract


def _numeric_control_metrics(metrics: dict) -> dict:
    return {
        f"control_{key}": value
        for key, value in metrics.items()
        if isinstance(value, (int, float, np.integer, np.floating))
    }


def build_controls(
    strategy: pd.DataFrame,
    returns: pd.DataFrame,
    *,
    cost_bps: float,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    if not strategy.index.equals(returns.index):
        raise ValueError("Issue #89 strategy and returns must share the exact index")
    pre_mask = strategy.index <= pd.Timestamp("2019-12-31")
    post_mask = strategy.index >= pd.Timestamp("2020-01-01")
    if not pre_mask.any() or not post_mask.any():
        raise RuntimeError("Issue #89 exposure attribution requires both eras")

    desired_full = mean_invested_weights(strategy)
    desired_pre = mean_invested_weights(strategy.loc[pre_mask])
    desired_post = mean_invested_weights(strategy.loc[post_mask])

    full_weights, full_sim, full_meta = solve_static_target_for_realized_average(
        returns,
        desired_full,
        cost_bps=cost_bps,
        name="issue89_full_realized_exposure_match",
    )
    pre_weights, _, pre_meta = solve_static_target_for_realized_average(
        returns.loc[pre_mask],
        desired_pre,
        cost_bps=cost_bps,
        name="issue89_pre2020_realized_exposure_match_solver",
    )
    post_weights, _, post_meta = solve_static_target_for_realized_average(
        returns.loc[post_mask],
        desired_post,
        cost_bps=cost_bps,
        name="issue89_post2019_realized_exposure_match_solver",
    )

    era_targets = weights_series(pre_weights, returns.index)
    era_targets.loc[post_mask, list(ASSETS)] = np.asarray([post_weights[a] for a in ASSETS], dtype=float)
    changed = era_targets.ne(era_targets.shift(1)).any(axis=1)
    era_rebalance = (month_start_mask(returns.index) | changed).astype(bool)
    era_sim = simulate_portfolio(
        returns,
        era_targets,
        era_rebalance,
        cost_bps=cost_bps,
        name="issue89_era_realized_exposure_match",
    )

    era_actual_pre = mean_invested_weights(era_sim.loc[pre_mask])
    era_actual_post = mean_invested_weights(era_sim.loc[post_mask])
    pre_mismatch = {a: float(era_actual_pre[a] - desired_pre[a]) for a in ASSETS}
    post_mismatch = {a: float(era_actual_post[a] - desired_post[a]) for a in ASSETS}
    pre_max = max(abs(v) for v in pre_mismatch.values())
    post_max = max(abs(v) for v in post_mismatch.values())
    if pre_max > MATCH_TOLERANCE or post_max > MATCH_TOLERANCE:
        raise AssertionError(f"Issue #89 era exposure mismatch pre={pre_max} post={post_max}")

    metadata = {
        "matching_basis": "realized average invested_weight_* exposure",
        "full": full_meta,
        "development_pre2020": {
            **pre_meta,
            "piecewise_control_average_invested_weights": era_actual_pre,
            "piecewise_invested_weight_mismatch": pre_mismatch,
            "piecewise_max_abs_invested_weight_mismatch": float(pre_max),
        },
        "post2019_reused_exploratory": {
            **post_meta,
            "piecewise_control_average_invested_weights": era_actual_post,
            "piecewise_invested_weight_mismatch": post_mismatch,
            "piecewise_max_abs_invested_weight_mismatch": float(post_max),
        },
        "full_target_weights": full_weights,
        "development_target_weights": pre_weights,
        "post2019_target_weights": post_weights,
    }
    return full_sim, era_sim, metadata


def run(evidence_dir: Path) -> dict:
    contract = load_contract(DEFAULT_CONTRACT)
    daily = pd.read_csv(evidence_dir / "issue-89-daily.csv", parse_dates=["date"])
    summary = pd.read_csv(evidence_dir / "issue-89-summary.csv")
    manifest = json.loads((evidence_dir / "issue-89-manifest.json").read_text(encoding="utf-8"))

    strategy = daily.loc[daily["strategy"].eq(STRATEGY)].set_index("date").sort_index()
    prices, price_manifest = load_frozen_prices("2007-01-01", None)
    if price_manifest["snapshot_csv_sha256"] != contract["outcome_snapshot"]["csv_sha256"]:
        raise RuntimeError("Issue #89 exposure diagnostic price SHA drifted")
    returns = prices.loc[:, list(ASSETS)].pct_change(fill_method=None).reindex(strategy.index)
    if returns.isna().any(axis=None):
        raise RuntimeError("Issue #89 exposure diagnostic has missing asset returns")

    cost = float(manifest["primary_cost_bps"])
    full_sim, era_sim, matching = build_controls(strategy, returns, cost_bps=cost)
    annualization = int(contract["metrics"]["annualization_trading_rows"])

    strategy_rows = summary.loc[summary["strategy"].eq(STRATEGY)].set_index("segment")
    controls = {
        "full_reused_history": portfolio_metrics(full_sim, annualization=annualization),
        "development_pre2020": portfolio_metrics(segment_sim(era_sim, None, "2019-12-31"), annualization=annualization),
        "post2019_reused_exploratory": portfolio_metrics(segment_sim(era_sim, "2020-01-01", None), annualization=annualization),
    }
    match_meta = {
        "full_reused_history": matching["full"],
        "development_pre2020": matching["development_pre2020"],
        "post2019_reused_exploratory": matching["post2019_reused_exploratory"],
    }
    rows = []
    for segment, control_metrics in controls.items():
        strategy_metrics = strategy_rows.loc[segment].to_dict()
        meta = match_meta[segment]
        if segment == "full_reused_history":
            desired = meta["desired_average_invested_weights"]
            actual = meta["control_average_invested_weights"]
            mismatch = meta["max_abs_invested_weight_mismatch"]
            control_name = "issue89_full_realized_exposure_match"
        else:
            desired = meta["desired_average_invested_weights"]
            actual = meta["piecewise_control_average_invested_weights"]
            mismatch = meta["piecewise_max_abs_invested_weight_mismatch"]
            control_name = "issue89_era_realized_exposure_match"
        rows.append({
            "segment": segment,
            "control": control_name,
            **_numeric_control_metrics(control_metrics),
            **delta_metrics(strategy_metrics, control_metrics),
            **{f"strategy_avg_invested_{a}": desired[a] for a in ASSETS},
            **{f"control_avg_invested_{a}": actual[a] for a in ASSETS},
            "max_abs_invested_weight_mismatch": float(mismatch),
        })

    comparison = pd.DataFrame(rows)
    comparison.to_csv(evidence_dir / "issue-89-exposure-match.csv", index=False)
    max_mismatch = float(comparison["max_abs_invested_weight_mismatch"].max())
    tolerance = float(contract["benchmarks"]["realized_exposure_matched_static_control"]["max_abs_invested_weight_mismatch"])
    if max_mismatch > tolerance:
        raise AssertionError(f"Issue #89 exposure mismatch {max_mismatch} exceeds {tolerance}")

    result = {
        "schema_version": 1,
        "issue": 89,
        "purpose": "separate long-run allocation-mix value from V6.6 regime-switching value",
        "causal_investable_benchmark": False,
        "matching": matching,
        "comparison_rows": rows,
        "max_abs_invested_weight_mismatch": max_mismatch,
        "required_max_abs_invested_weight_mismatch": tolerance,
        "interpretation_boundary": "post-hoc attribution control; favorable 60/40 comparison alone is not evidence of regime-switching value",
    }
    (evidence_dir / "issue-89-exposure-match.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Issue #89 realized-exposure attribution")
    parser.add_argument("--evidence-dir", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.evidence_dir)
    print(json.dumps({
        "max_abs_invested_weight_mismatch": result["max_abs_invested_weight_mismatch"],
        "comparison_rows": result["comparison_rows"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
