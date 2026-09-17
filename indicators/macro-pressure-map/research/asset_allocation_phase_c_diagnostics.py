#!/usr/bin/env python3
"""Post-hoc attribution and concentration diagnostics for Issue #64 Phase C."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

from asset_allocation_phase_a import ASSETS
from asset_allocation_phase_a_frozen import REGIME_ID_MAP, load_frozen_transitions
from asset_allocation_phase_b import (
    month_start_mask,
    portfolio_metrics,
    segment_sim,
    simulate_portfolio,
    template_change_mask,
)
from asset_allocation_phase_b_diagnostics import mean_invested_weights, reconstruct_asset_returns
from asset_allocation_phase_c import (
    REFLATION_REGIME,
    STAGFLATION_REGIME,
    build_three_state_targets,
    load_contract,
)

DEVELOPMENT_END = pd.Timestamp("2019-12-31")
POST_START = pd.Timestamp("2020-01-01")
MATCH_TOLERANCE = 1e-9


def lagged_regime_names(index: pd.DatetimeIndex) -> pd.Series:
    dates = pd.DatetimeIndex(pd.to_datetime(index, errors="raise")).astype("datetime64[ns]")
    transitions = load_frozen_transitions().copy()
    transitions["start_date"] = pd.DatetimeIndex(transitions["start_date"]).astype("datetime64[ns]")
    mapped = pd.merge_asof(
        pd.DataFrame({"date": dates}),
        transitions.sort_values("start_date"),
        left_on="date",
        right_on="start_date",
        direction="backward",
        allow_exact_matches=True,
    )
    names = pd.Series(mapped["regime_id"].map(REGIME_ID_MAP).to_numpy(), index=index, dtype="object")
    return names.shift(1)


def _control_targets_from_shift(
    template: pd.Series,
    neutral: dict[str, float],
    reflation: dict[str, float],
    theta: np.ndarray,
) -> pd.DataFrame:
    shift = np.asarray([float(theta[0]), float(theta[1]), -float(theta[0]) - float(theta[1])])
    neutral_v = np.asarray([float(neutral[a]) for a in ASSETS]) + shift
    reflation_v = np.asarray([float(reflation[a]) for a in ASSETS]) + shift
    if (neutral_v <= 0.0).any() or (reflation_v <= 0.0).any():
        raise ValueError("exposure-match shift produced non-positive control weights")
    data = np.tile(neutral_v, (len(template), 1))
    data[template.eq("reflation").to_numpy()] = reflation_v
    return pd.DataFrame(data, index=template.index, columns=list(ASSETS))


def solve_phase_b_preserving_exposure_match(
    returns: pd.DataFrame,
    phase_b_template: pd.Series,
    desired_average: dict[str, float],
    *,
    neutral: dict[str, float],
    reflation: dict[str, float],
    cost_bps: float,
    name: str,
) -> tuple[pd.DataFrame, dict]:
    """Match Phase C realized exposure while preserving Phase B Reflation timing.

    A constant zero-sum shift is applied to both the neutral and Reflation
    templates. This strips out average SPY/GLD/TLT exposure differences without
    granting the control any Stagflation timing information.
    """
    desired = np.asarray([float(desired_average[a]) for a in ASSETS], dtype=float)
    monthly = month_start_mask(returns.index)
    rebalance = (monthly | template_change_mask(phase_b_template)).astype(bool)

    def simulate_theta(theta: np.ndarray):
        targets = _control_targets_from_shift(phase_b_template, neutral, reflation, theta)
        sim = simulate_portfolio(returns, targets, rebalance, cost_bps=cost_bps, name=name)
        actual = np.asarray([sim[f"invested_weight_{a}"].mean() for a in ASSETS], dtype=float)
        return sim, actual

    def residual(theta: np.ndarray) -> np.ndarray:
        try:
            _, actual = simulate_theta(theta)
        except ValueError:
            return np.asarray([1.0, 1.0])
        return actual[:2] - desired[:2]

    fit = least_squares(
        residual,
        np.zeros(2),
        bounds=(np.asarray([-0.09, -0.09]), np.asarray([0.09, 0.09])),
        xtol=1e-13,
        ftol=1e-13,
        gtol=1e-13,
        max_nfev=100,
    )
    if not fit.success:
        raise RuntimeError(f"Phase C exposure-match solver failed: {fit.message}")
    sim, actual = simulate_theta(fit.x)
    mismatch = actual - desired
    max_abs = float(np.max(np.abs(mismatch)))
    if max_abs > MATCH_TOLERANCE:
        raise AssertionError(f"Phase C realized exposure mismatch {max_abs} exceeds {MATCH_TOLERANCE}")
    shift = {
        "SPY": float(fit.x[0]),
        "TLT": float(fit.x[1]),
        "GLD": float(-fit.x[0] - fit.x[1]),
    }
    return sim, {
        "constant_template_shift": shift,
        "desired_average_invested_weights": {a: float(v) for a, v in zip(ASSETS, desired)},
        "control_average_invested_weights": {a: float(v) for a, v in zip(ASSETS, actual)},
        "max_abs_invested_weight_mismatch": max_abs,
        "solver_nfev": int(fit.nfev),
        "interpretation": "post-hoc noncausal attribution control; Phase B Reflation timing is preserved and no Stagflation timing is provided",
    }


def metric_delta(lhs: dict, rhs: dict) -> dict:
    names = ["CAGR", "annualized_volatility", "Sharpe", "maximum_drawdown", "Calmar", "annualized_turnover"]
    return {f"delta_{name}": float(lhs[name] - rhs[name]) for name in names}


def contiguous_true_runs(mask: np.ndarray) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    start: int | None = None
    for i, value in enumerate(mask.astype(bool)):
        if value and start is None:
            start = i
        if start is not None and ((not value) or i == len(mask) - 1):
            end = i if value and i == len(mask) - 1 else i - 1
            runs.append((start, end))
            start = None
    return runs


def select_largest_stagflation_episode(
    phase_c_sim: pd.DataFrame,
    phase_b_sim: pd.DataFrame,
    stag_mask: np.ndarray,
    *,
    segment_start: pd.Timestamp | None,
    segment_end: pd.Timestamp | None,
) -> dict:
    index = phase_c_sim.index
    active_log = np.log1p(phase_c_sim["net_return"].to_numpy(float)) - np.log1p(phase_b_sim["net_return"].to_numpy(float))
    rows: list[dict] = []
    for start, end in contiguous_true_runs(stag_mask):
        start_date = index[start]
        end_date = index[end]
        if segment_start is not None and start_date < segment_start:
            continue
        if segment_end is not None and end_date > segment_end:
            continue
        contribution_end = min(end + 1, len(index) - 1)  # include exit/rebalance day
        contribution = float(active_log[start:contribution_end + 1].sum())
        rows.append({
            "start_position": start,
            "end_position": end,
            "start": start_date,
            "end": end_date,
            "active_log_contribution_including_exit_day": contribution,
        })
    if not rows:
        raise RuntimeError("no Stagflation episodes in requested segment")
    return max(rows, key=lambda row: row["active_log_contribution_including_exit_day"])


def run_diagnostics(phase_b_dir: Path, phase_c_dir: Path) -> dict:
    contract = load_contract()
    b_daily = pd.read_csv(phase_b_dir / "phase-b-daily.csv", parse_dates=["date"])
    c_daily = pd.read_csv(phase_c_dir / "phase-c-daily.csv", parse_dates=["date"])
    c_summary = pd.read_csv(phase_c_dir / "phase-c-summary.csv")
    c_manifest = json.loads((phase_c_dir / "phase-c-manifest.json").read_text(encoding="utf-8"))

    returns, residual = reconstruct_asset_returns(b_daily)
    if residual > 1e-10:
        raise AssertionError(f"asset-return reconstruction residual too large: {residual}")
    index = returns.index
    lagged_names = lagged_regime_names(index)
    neutral = contract["templates"]["neutral"]
    reflation = contract["templates"]["reflation"]
    stagflation = contract["templates"]["stagflation"]

    pb_targets, pb_template = build_three_state_targets(
        lagged_names.shift(-1), neutral=neutral, reflation=reflation, stagflation=stagflation,
        include_reflation=True, include_stagflation=False,
    )
    pc_targets, pc_template = build_three_state_targets(
        lagged_names.shift(-1), neutral=neutral, reflation=reflation, stagflation=stagflation,
        include_reflation=True, include_stagflation=True,
    )
    # build_three_state_targets performs its own one-row lag; shift(-1) supplies the
    # already-lagged names so the resulting templates align to the evaluation dates.
    pb_template.index = index
    pc_template.index = index
    pb_targets.index = index
    pc_targets.index = index

    monthly = month_start_mask(index)
    pb_rebalance = (monthly | template_change_mask(pb_template)).astype(bool)
    pc_rebalance = (monthly | template_change_mask(pc_template)).astype(bool)
    cost_bps = float(contract["primary_cost_bps"])
    pb_sim = simulate_portfolio(returns, pb_targets, pb_rebalance, cost_bps=cost_bps, name="phase_b_reflation_only")
    pc_sim = simulate_portfolio(returns, pc_targets, pc_rebalance, cost_bps=cost_bps, name="phase_c_combined")

    official_pb = c_daily.loc[c_daily["strategy"].eq("phase_b_reflation_only")].set_index("date").sort_index()
    official_pc = c_daily.loc[c_daily["strategy"].eq("phase_c_combined")].set_index("date").sort_index()
    if not index.equals(official_pb.index) or not index.equals(official_pc.index):
        raise ValueError("Phase C daily panels do not align to reconstructed returns")
    max_replay_error = max(
        float(np.max(np.abs(pb_sim["net_return"].to_numpy() - official_pb["net_return"].to_numpy()))),
        float(np.max(np.abs(pc_sim["net_return"].to_numpy() - official_pc["net_return"].to_numpy()))),
    )
    if max_replay_error > 1e-12:
        raise AssertionError(f"Phase C replay error too large: {max_replay_error}")

    segments = {
        "full_reused_history": (None, None),
        "development_pre2020": (None, DEVELOPMENT_END),
        "post2019_reused_exploratory": (POST_START, None),
    }
    exposure_rows: list[dict] = []
    exposure_json: dict[str, dict] = {}
    for segment, (start, end) in segments.items():
        mask = pd.Series(True, index=index)
        if start is not None:
            mask &= index >= start
        if end is not None:
            mask &= index <= end
        seg_returns = returns.loc[mask]
        seg_template = pb_template.loc[mask]
        seg_pc = official_pc.loc[mask]
        desired = mean_invested_weights(seg_pc)
        control, meta = solve_phase_b_preserving_exposure_match(
            seg_returns,
            seg_template,
            desired,
            neutral=neutral,
            reflation=reflation,
            cost_bps=cost_bps,
            name=f"phase_c_exposure_match_{segment}",
        )
        pc_metrics = portfolio_metrics(seg_pc, annualization=252)
        control_metrics = portfolio_metrics(control, annualization=252)
        delta = metric_delta(pc_metrics, control_metrics)
        exposure_json[segment] = {"match": meta, "timing_delta": delta}
        exposure_rows.append({"segment": segment, **meta["constant_template_shift"], **delta})

    stag_mask = pc_template.eq("stagflation").to_numpy()
    episode_results: dict[str, dict] = {}
    episode_rows: list[dict] = []
    for segment, (start, end) in {
        "development_pre2020": (None, DEVELOPMENT_END),
        "post2019_reused_exploratory": (POST_START, None),
    }.items():
        winner = select_largest_stagflation_episode(
            pc_sim,
            pb_sim,
            stag_mask,
            segment_start=start,
            segment_end=end,
        )
        modified_targets = pc_targets.copy()
        modified_template = pc_template.copy()
        s = int(winner["start_position"])
        e = int(winner["end_position"])
        modified_targets.iloc[s:e + 1] = pb_targets.iloc[s:e + 1].to_numpy(float)
        modified_template.iloc[s:e + 1] = pb_template.iloc[s:e + 1].to_numpy()
        modified_rebalance = (monthly | template_change_mask(modified_template)).astype(bool)
        leaveout = simulate_portfolio(
            returns,
            modified_targets,
            modified_rebalance,
            cost_bps=cost_bps,
            name=f"phase_c_leaveout_{segment}",
        )
        pb_seg = segment_sim(pb_sim, None if start is None else start.date().isoformat(), None if end is None else end.date().isoformat())
        pc_seg = segment_sim(pc_sim, None if start is None else start.date().isoformat(), None if end is None else end.date().isoformat())
        leave_seg = segment_sim(leaveout, None if start is None else start.date().isoformat(), None if end is None else end.date().isoformat())
        pb_metrics = portfolio_metrics(pb_seg, annualization=252)
        pc_metrics = portfolio_metrics(pc_seg, annualization=252)
        leave_metrics = portfolio_metrics(leave_seg, annualization=252)
        normal_delta = metric_delta(pc_metrics, pb_metrics)
        leave_delta = metric_delta(leave_metrics, pb_metrics)
        full_active_log = float(np.log1p(pc_seg["net_return"]).sum() - np.log1p(pb_seg["net_return"]).sum())
        leave_active_log = float(np.log1p(leave_seg["net_return"]).sum() - np.log1p(pb_seg["net_return"]).sum())
        record = {
            "largest_winning_episode_start": winner["start"].date().isoformat(),
            "largest_winning_episode_end": winner["end"].date().isoformat(),
            "screening_active_log_contribution_including_exit_day": float(winner["active_log_contribution_including_exit_day"]),
            "normal_active_log_return": full_active_log,
            "active_log_return_after_leaveout": leave_active_log,
            "normal_incremental": normal_delta,
            "incremental_after_leaveout": leave_delta,
        }
        episode_results[segment] = record
        episode_rows.append({
            "segment": segment,
            "episode_start": record["largest_winning_episode_start"],
            "episode_end": record["largest_winning_episode_end"],
            "normal_active_log_return": full_active_log,
            "active_log_after_leaveout": leave_active_log,
            **{f"normal_{k}": v for k, v in normal_delta.items()},
            **{f"leaveout_{k}": v for k, v in leave_delta.items()},
        })

    result = {
        "schema_version": 1,
        "issue": 64,
        "phase": "C",
        "diagnostic_role": "post-hoc attribution and concentration diagnostics required by preregistration",
        "evidence_status": contract["evidence_status"],
        "primary_cost_bps": cost_bps,
        "phase_c_replay_max_abs_net_return_error": max_replay_error,
        "exposure_match": exposure_json,
        "episode_concentration": episode_results,
        "interpretation_boundary": "These diagnostics are post-hoc on reused history and do not create untouched OOS evidence.",
    }
    (phase_c_dir / "phase-c-posthoc-diagnostics.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    pd.DataFrame(exposure_rows).to_csv(phase_c_dir / "phase-c-posthoc-exposure-match.csv", index=False)
    pd.DataFrame(episode_rows).to_csv(phase_c_dir / "phase-c-posthoc-episode-leaveout.csv", index=False)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Issue #64 Phase C post-hoc diagnostics")
    parser.add_argument("--phase-b-dir", type=Path, required=True)
    parser.add_argument("--phase-c-dir", type=Path, required=True)
    args = parser.parse_args()
    result = run_diagnostics(args.phase_b_dir, args.phase_c_dir)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
