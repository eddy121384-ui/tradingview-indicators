#!/usr/bin/env python3
"""Post-hoc attribution diagnostics for Issue #64 Phase B.

This is deliberately NOT part of the preregistered primary benchmark set. It
asks whether the Reflation strategy's improvement can be explained by its higher
average realized equity exposure rather than regime timing itself.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

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
MATCH_TOLERANCE = 1e-9


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


def mean_invested_weights(frame: pd.DataFrame) -> dict[str, float]:
    """Return realized average invested weights, not target-template averages."""
    if frame.empty:
        raise ValueError("cannot average an empty invested-weight panel")
    result = {
        asset: float(frame[f"invested_weight_{asset}"].mean()) for asset in ASSETS
    }
    values = np.asarray([result[a] for a in ASSETS], dtype=float)
    if not np.isfinite(values).all() or not np.isclose(values.sum(), 1.0, atol=1e-9):
        raise ValueError("invalid realized average invested weights")
    return result


def _weights_from_logits(theta: np.ndarray) -> dict[str, float]:
    """Map two free logits plus a GLD reference logit to positive simplex weights."""
    z = np.asarray([float(theta[0]), float(theta[1]), 0.0], dtype=float)
    z -= np.max(z)
    values = np.exp(z)
    values /= values.sum()
    return {asset: float(value) for asset, value in zip(ASSETS, values)}


def _logits_from_weights(weights: dict[str, float]) -> np.ndarray:
    values = np.asarray([float(weights[a]) for a in ASSETS], dtype=float)
    if not np.isfinite(values).all() or (values <= 0.0).any():
        raise ValueError("solver seed weights must be finite and strictly positive")
    values /= values.sum()
    return np.log(values[:2] / values[2])


def solve_static_target_for_realized_average(
    returns: pd.DataFrame,
    desired_average: dict[str, float],
    *,
    cost_bps: float,
    name: str,
) -> tuple[dict[str, float], pd.DataFrame, dict]:
    """Solve a fixed monthly-rebalanced target that matches realized mean exposure.

    This is intentionally post-hoc and noncausal: the target is solved using the
    realized return path and the strategy's realized average invested weights.
    It is an attribution control, not an investable benchmark.
    """
    if returns.empty:
        raise ValueError("cannot solve exposure match on empty returns")
    desired = np.asarray([float(desired_average[a]) for a in ASSETS], dtype=float)
    if not np.isfinite(desired).all() or (desired <= 0.0).any():
        raise ValueError("desired realized weights must be finite and positive")
    desired /= desired.sum()
    desired_dict = {asset: float(value) for asset, value in zip(ASSETS, desired)}
    monthly = month_start_mask(returns.index)

    def simulate_theta(theta: np.ndarray) -> tuple[dict[str, float], pd.DataFrame, np.ndarray]:
        weights = _weights_from_logits(theta)
        targets = weights_series(weights, returns.index)
        sim = simulate_portfolio(
            returns,
            targets,
            monthly,
            cost_bps=cost_bps,
            name=name,
        )
        actual = np.asarray(
            [float(sim[f"invested_weight_{asset}"].mean()) for asset in ASSETS],
            dtype=float,
        )
        return weights, sim, actual

    def residual(theta: np.ndarray) -> np.ndarray:
        _, _, actual = simulate_theta(theta)
        return actual[:2] - desired[:2]

    fit = least_squares(
        residual,
        _logits_from_weights(desired_dict),
        xtol=1e-13,
        ftol=1e-13,
        gtol=1e-13,
        max_nfev=100,
    )
    if not fit.success:
        raise RuntimeError(f"realized exposure match failed: {fit.message}")
    weights, sim, actual = simulate_theta(fit.x)
    mismatch = actual - desired
    max_abs = float(np.max(np.abs(mismatch)))
    if max_abs > MATCH_TOLERANCE:
        raise AssertionError(
            f"realized exposure control mismatch {max_abs} exceeds {MATCH_TOLERANCE}"
        )
    metadata = {
        "target_weights": weights,
        "desired_average_invested_weights": desired_dict,
        "control_average_invested_weights": {
            asset: float(value) for asset, value in zip(ASSETS, actual)
        },
        "invested_weight_mismatch": {
            asset: float(value) for asset, value in zip(ASSETS, mismatch)
        },
        "max_abs_invested_weight_mismatch": max_abs,
        "solver_nfev": int(fit.nfev),
    }
    return weights, sim, metadata


def build_realized_exposure_matched_controls(
    daily: pd.DataFrame,
    returns: pd.DataFrame,
    *,
    cost_bps: float,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Build full-history and era-piecewise realized-exposure matched controls."""
    strategy = (
        daily.loc[daily["strategy"].eq("v66_reflation_override")]
        .set_index("date")
        .sort_index()
    )
    if not strategy.index.equals(returns.index):
        raise ValueError("strategy daily panel and reconstructed returns must align")

    pre_mask = strategy.index <= DEVELOPMENT_END
    post_mask = strategy.index >= POST_START
    if not pre_mask.any() or not post_mask.any():
        raise RuntimeError("both temporal segments are required for exposure matching")

    full_desired = mean_invested_weights(strategy)
    pre_desired = mean_invested_weights(strategy.loc[pre_mask])
    post_desired = mean_invested_weights(strategy.loc[post_mask])

    full_weights, full_sim, full_meta = solve_static_target_for_realized_average(
        returns,
        full_desired,
        cost_bps=cost_bps,
        name="posthoc_full_realized_exposure_match",
    )
    pre_weights, _, pre_meta = solve_static_target_for_realized_average(
        returns.loc[pre_mask],
        pre_desired,
        cost_bps=cost_bps,
        name="posthoc_pre2020_realized_exposure_match_solver",
    )
    post_weights, _, post_meta = solve_static_target_for_realized_average(
        returns.loc[post_mask],
        post_desired,
        cost_bps=cost_bps,
        name="posthoc_post2019_realized_exposure_match_solver",
    )

    era_targets = weights_series(pre_weights, returns.index)
    era_targets.loc[post_mask, list(ASSETS)] = np.asarray(
        [post_weights[a] for a in ASSETS], dtype=float
    )
    target_changed = era_targets.ne(era_targets.shift(1)).any(axis=1)
    era_rebalance = (month_start_mask(returns.index) | target_changed).astype(bool)
    era_sim = simulate_portfolio(
        returns,
        era_targets,
        era_rebalance,
        cost_bps=cost_bps,
        name="posthoc_era_realized_exposure_match",
    )

    era_actual_pre = mean_invested_weights(era_sim.loc[pre_mask])
    era_actual_post = mean_invested_weights(era_sim.loc[post_mask])
    pre_mismatch = {
        asset: float(era_actual_pre[asset] - pre_desired[asset]) for asset in ASSETS
    }
    post_mismatch = {
        asset: float(era_actual_post[asset] - post_desired[asset]) for asset in ASSETS
    }
    pre_max = max(abs(value) for value in pre_mismatch.values())
    post_max = max(abs(value) for value in post_mismatch.values())
    if pre_max > MATCH_TOLERANCE or post_max > MATCH_TOLERANCE:
        raise AssertionError(
            f"piecewise realized exposure mismatch pre={pre_max} post={post_max}"
        )

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


def delta_metrics(strategy_metrics: dict, control_metrics: dict) -> dict:
    metrics = ["CAGR", "annualized_return", "annualized_volatility", "Sharpe", "maximum_drawdown", "Calmar"]
    return {f"delta_{metric}": float(strategy_metrics[metric] - control_metrics[metric]) for metric in metrics}


def _numeric_control_metrics(metrics: dict) -> dict:
    return {
        f"control_{key}": value
        for key, value in metrics.items()
        if isinstance(value, (int, float, np.integer, np.floating))
    }


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
    full_sim, era_sim, match_meta = build_realized_exposure_matched_controls(
        daily,
        returns,
        cost_bps=cost_bps,
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
            "control": "posthoc_full_realized_exposure_match",
            **_numeric_control_metrics(full_control),
            **delta_metrics(full_strategy, full_control),
            **{
                f"strategy_avg_invested_{a}": match_meta["full"]["desired_average_invested_weights"][a]
                for a in ASSETS
            },
            **{
                f"control_avg_invested_{a}": match_meta["full"]["control_average_invested_weights"][a]
                for a in ASSETS
            },
            "max_abs_invested_weight_mismatch": match_meta["full"]["max_abs_invested_weight_mismatch"],
        },
        {
            "segment": "development_pre2020",
            "control": "posthoc_era_realized_exposure_match",
            **_numeric_control_metrics(pre_control),
            **delta_metrics(pre_strategy, pre_control),
            **{
                f"strategy_avg_invested_{a}": match_meta["development_pre2020"]["desired_average_invested_weights"][a]
                for a in ASSETS
            },
            **{
                f"control_avg_invested_{a}": match_meta["development_pre2020"]["piecewise_control_average_invested_weights"][a]
                for a in ASSETS
            },
            "max_abs_invested_weight_mismatch": match_meta["development_pre2020"]["piecewise_max_abs_invested_weight_mismatch"],
        },
        {
            "segment": "post2019_reused_exploratory",
            "control": "posthoc_era_realized_exposure_match",
            **_numeric_control_metrics(post_control),
            **delta_metrics(post_strategy, post_control),
            **{
                f"strategy_avg_invested_{a}": match_meta["post2019_reused_exploratory"]["desired_average_invested_weights"][a]
                for a in ASSETS
            },
            **{
                f"control_avg_invested_{a}": match_meta["post2019_reused_exploratory"]["piecewise_control_average_invested_weights"][a]
                for a in ASSETS
            },
            "max_abs_invested_weight_mismatch": match_meta["post2019_reused_exploratory"]["piecewise_max_abs_invested_weight_mismatch"],
        },
    ]
    pd.DataFrame(rows).to_csv(phase_b_dir / "phase-b-posthoc-exposure-match.csv", index=False)

    result = {
        "schema_version": 2,
        "issue": 64,
        "phase": "B-posthoc-attribution",
        "preregistered_primary_result_modified": False,
        "purpose": "separate regime timing from differences in realized average invested exposure",
        "causal_investable_benchmark": False,
        "reason_noncausal": "control target weights are solved post-hoc against the strategy's realized average invested weights and the realized asset-return path over the full period or temporal segment",
        "asset_return_reconstruction_max_abs_residual": residual,
        "reflation_fraction_full_history": float(status.mean()),
        "matching": match_meta,
        "comparison_rows": rows,
        "interpretation_boundary": "This diagnostic is post-hoc attribution only. It cannot upgrade the reused-history Phase B result to confirmatory evidence and must not be used to tune the preregistered strategy."
    }
    (phase_b_dir / "phase-b-posthoc-exposure-match.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Issue #64 Phase B realized-exposure attribution diagnostic")
    parser.add_argument("--phase-b-dir", type=Path, required=True)
    args = parser.parse_args()
    result = run_diagnostics(args.phase_b_dir)
    print(json.dumps({
        "matching": result["matching"],
        "comparison_rows": result["comparison_rows"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
