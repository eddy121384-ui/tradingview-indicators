#!/usr/bin/env python3
"""Post-hoc attribution diagnostics for Issue #64 Phase B.

This is deliberately NOT part of the preregistered primary benchmark set. It
asks whether the Reflation strategy's improvement can be explained by its higher
average target equity exposure rather than regime timing itself.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from asset_allocation_phase_a import ASSETS
from asset_allocation_phase_a_frozen import load_frozen_transitions
from asset_allocation_phase_b import (
    month_start_mask,
    portfolio_metrics,
    segment_sim,
    simulate_portfolio,
    weights_series,
)

REFLATION_REGIME_ID = 3
DEVELOPMENT_END = pd.Timestamp("2019-12-31")
POST_START = pd.Timestamp("2020-01-01")
FIXED_BENCHMARKS = ("fixed_60_40", "fixed_equal_weight", "fixed_neutral_40_40_20")


def reconstruct_asset_returns(daily: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    """Recover asset returns from three independent fixed-benchmark equations."""
    blocks = {
        name: daily.loc[daily["strategy"].eq(name)].set_index("date").sort_index()
        for name in FIXED_BENCHMARKS
    }
    index = blocks[FIXED_BENCHMARKS[0]].index
    if any(not index.equals(blocks[name].index) for name in FIXED_BENCHMARKS[1:]):
        raise ValueError("fixed benchmark daily panels do not share one index")

    rows: list[np.ndarray] = []
    max_residual = 0.0
    for date in index:
        matrix = np.asarray([
            [
                float(blocks[name].loc[date, f"invested_weight_{asset}"])
                for asset in ASSETS
            ]
            for name in FIXED_BENCHMARKS
        ])
        gross = np.asarray([
            float(blocks[name].loc[date, "gross_asset_mix_return"])
            for name in FIXED_BENCHMARKS
        ])
        if not np.isfinite(matrix).all() or not np.isfinite(gross).all():
            raise ValueError(f"non-finite benchmark equation on {date}")
        if abs(np.linalg.det(matrix)) < 1e-12:
            raise ValueError(f"singular benchmark exposure matrix on {date}")
        solved = np.linalg.solve(matrix, gross)
        residual = np.max(np.abs(matrix @ solved - gross))
        max_residual = max(max_residual, float(residual))
        rows.append(solved)

    return pd.DataFrame(rows, index=index, columns=list(ASSETS)), max_residual


def _as_ns_index(values: pd.Index | pd.Series) -> pd.DatetimeIndex:
    """Normalize timestamps to ns precision before pandas merge_asof."""
    parsed = pd.to_datetime(values, errors="raise")
    if isinstance(parsed, pd.Series):
        parsed = pd.DatetimeIndex(parsed.to_numpy())
    else:
        parsed = pd.DatetimeIndex(parsed)
    return parsed.astype("datetime64[ns]")


def lagged_reflation_status(index: pd.DatetimeIndex) -> pd.Series:
    """Map frozen transitions robustly across pandas datetime precisions."""
    original_index = pd.DatetimeIndex(index)
    lookup_dates = _as_ns_index(original_index)
    transitions = load_frozen_transitions().sort_values("start_date").copy()
    transitions["start_date"] = _as_ns_index(transitions["start_date"])
    lookup = pd.DataFrame({"date": lookup_dates})
    mapped = pd.merge_asof(
        lookup,
        transitions,
        left_on="date",
        right_on="start_date",
        direction="backward",
        allow_exact_matches=True,
    )
    regimes = pd.Series(mapped["regime_id"].to_numpy(), index=original_index)
    return regimes.shift(1).eq(REFLATION_REGIME_ID).fillna(False).astype(bool)


def matched_weights(reflation_fraction: float) -> dict[str, float]:
    """Match the average TARGET exposure implied by 40/40/20 -> 60/20/20."""
    if not 0.0 <= reflation_fraction <= 1.0:
        raise ValueError("reflation_fraction must be in [0, 1]")
    shift = 0.20 * float(reflation_fraction)
    return {"SPY": 0.40 + shift, "TLT": 0.40 - shift, "GLD": 0.20}


def piecewise_era_matched_targets(index: pd.DatetimeIndex, status: pd.Series) -> tuple[pd.DataFrame, dict]:
    pre_mask = index <= DEVELOPMENT_END
    post_mask = index >= POST_START
    pre_fraction = float(status.loc[pre_mask].mean()) if pre_mask.any() else np.nan
    post_fraction = float(status.loc[post_mask].mean()) if post_mask.any() else np.nan
    if not np.isfinite(pre_fraction) or not np.isfinite(post_fraction):
        raise RuntimeError("both temporal segments are required for era-matched diagnostic")
    pre = matched_weights(pre_fraction)
    post = matched_weights(post_fraction)
    targets = weights_series(pre, index)
    targets.loc[post_mask, list(ASSETS)] = np.asarray([post[a] for a in ASSETS], dtype=float)
    meta = {
        "development_reflation_fraction": pre_fraction,
        "development_weights": pre,
        "post2019_reflation_fraction": post_fraction,
        "post2019_weights": post,
    }
    return targets, meta


def delta_metrics(strategy_metrics: dict, control_metrics: dict) -> dict:
    metrics = ["CAGR", "annualized_return", "annualized_volatility", "Sharpe", "maximum_drawdown", "Calmar"]
    return {f"delta_{metric}": float(strategy_metrics[metric] - control_metrics[metric]) for metric in metrics}


def run_diagnostics(phase_b_dir: Path) -> dict:
    daily_path = phase_b_dir / "phase-b-daily.csv"
    summary_path = phase_b_dir / "phase-b-summary.csv"
    manifest_path = phase_b_dir / "phase-b-manifest.json"
    daily = pd.read_csv(daily_path, parse_dates=["date"])
    summary = pd.read_csv(summary_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    returns, residual = reconstruct_asset_returns(daily)
    if residual > 1e-10:
        raise AssertionError(f"asset-return reconstruction residual too large: {residual}")
    index = returns.index
    status = lagged_reflation_status(index)
    observed_days = int(status.sum())
    if observed_days != int(manifest["reflation_target_days"]):
        raise AssertionError(
            f"reconstructed Reflation target days {observed_days} != manifest {manifest['reflation_target_days']}"
        )

    annualization = 252
    cost_bps = float(manifest["primary_cost_bps"])
    monthly = month_start_mask(index)

    full_fraction = float(status.mean())
    full_weights = matched_weights(full_fraction)
    full_targets = weights_series(full_weights, index)
    full_sim = simulate_portfolio(
        returns,
        full_targets,
        monthly,
        cost_bps=cost_bps,
        name="posthoc_full_frequency_exposure_match",
    )

    era_targets, era_meta = piecewise_era_matched_targets(index, status)
    target_changed = era_targets.ne(era_targets.shift(1)).any(axis=1)
    era_rebalance = (monthly | target_changed).astype(bool)
    era_sim = simulate_portfolio(
        returns,
        era_targets,
        era_rebalance,
        cost_bps=cost_bps,
        name="posthoc_era_frequency_exposure_match",
    )

    strategy_rows = summary.loc[summary["strategy"].eq("v66_reflation_override")].set_index("segment")
    full_strategy = strategy_rows.loc["full_reused_history"].to_dict()
    pre_strategy = strategy_rows.loc["development_pre2020"].to_dict()
    post_strategy = strategy_rows.loc["post2019_reused_exploratory"].to_dict()

    full_control = portfolio_metrics(full_sim, annualization=annualization)
    pre_control = portfolio_metrics(segment_sim(era_sim, None, "2019-12-31"), annualization=annualization)
    post_control = portfolio_metrics(segment_sim(era_sim, "2020-01-01", None), annualization=annualization)

    rows = [
        {
            "segment": "full_reused_history",
            "control": "posthoc_full_frequency_exposure_match",
            "reflation_fraction": full_fraction,
            **{f"control_{k}": v for k, v in full_control.items() if isinstance(v, (int, float, np.integer, np.floating))},
            **delta_metrics(full_strategy, full_control),
        },
        {
            "segment": "development_pre2020",
            "control": "posthoc_era_frequency_exposure_match",
            "reflation_fraction": era_meta["development_reflation_fraction"],
            **{f"control_{k}": v for k, v in pre_control.items() if isinstance(v, (int, float, np.integer, np.floating))},
            **delta_metrics(pre_strategy, pre_control),
        },
        {
            "segment": "post2019_reused_exploratory",
            "control": "posthoc_era_frequency_exposure_match",
            "reflation_fraction": era_meta["post2019_reflation_fraction"],
            **{f"control_{k}": v for k, v in post_control.items() if isinstance(v, (int, float, np.integer, np.floating))},
            **delta_metrics(post_strategy, post_control),
        },
    ]
    comparison = pd.DataFrame(rows)
    comparison.to_csv(phase_b_dir / "phase-b-posthoc-exposure-match.csv", index=False)

    result = {
        "schema_version": 1,
        "issue": 64,
        "phase": "B-posthoc-attribution",
        "preregistered_primary_result_modified": False,
        "purpose": "separate regime timing from the strategy's higher average target equity exposure",
        "causal_investable_benchmark": False,
        "reason_noncausal": "matched weights use realized Reflation occupancy over the evaluated full period or temporal segment",
        "asset_return_reconstruction_max_abs_residual": residual,
        "full_reflation_fraction": full_fraction,
        "full_matched_weights": full_weights,
        **era_meta,
        "comparison_rows": rows,
        "interpretation_boundary": "This diagnostic is post-hoc attribution only. It cannot upgrade the reused-history Phase B result to confirmatory evidence and must not be used to tune the preregistered strategy."
    }
    (phase_b_dir / "phase-b-posthoc-exposure-match.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Issue #64 Phase B exposure-matched attribution diagnostic")
    parser.add_argument("--phase-b-dir", type=Path, required=True)
    args = parser.parse_args()
    result = run_diagnostics(args.phase_b_dir)
    print(json.dumps({
        "full_reflation_fraction": result["full_reflation_fraction"],
        "full_matched_weights": result["full_matched_weights"],
        "comparison_rows": result["comparison_rows"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
