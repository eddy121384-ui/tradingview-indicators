#!/usr/bin/env python3
"""Post-hoc episode concentration diagnostics for Issue #64 Phase B.

This diagnostic does not alter the preregistered Reflation strategy. It asks
whether timing attribution versus an era realized-exposure-matched control is
broadly distributed or concentrated in a few Reflation episodes.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from asset_allocation_phase_b_diagnostics import (
    build_realized_exposure_matched_controls,
    lagged_reflation_status,
    reconstruct_asset_returns,
)

DEVELOPMENT_END = pd.Timestamp("2019-12-31")
POST_START = pd.Timestamp("2020-01-01")


def reflation_episode_table(status: pd.Series, active_log: pd.Series) -> pd.DataFrame:
    """Summarize contiguous True-status episodes on an aligned index."""
    if not status.index.equals(active_log.index):
        raise ValueError("status and active_log must share one index")
    if status.empty:
        return pd.DataFrame(columns=["start", "end", "days", "active_log_return"])
    groups = status.astype(bool).ne(status.astype(bool).shift(1)).cumsum()
    rows: list[dict] = []
    for _, block in status.astype(bool).groupby(groups):
        if not bool(block.iloc[0]):
            continue
        contribution = float(active_log.loc[block.index].sum())
        rows.append({
            "start": block.index[0],
            "end": block.index[-1],
            "days": int(len(block)),
            "active_log_return": contribution,
        })
    return pd.DataFrame(rows)


def concentration_summary(
    label: str,
    status: pd.Series,
    active_log: pd.Series,
) -> tuple[dict, pd.DataFrame]:
    episodes = reflation_episode_table(status, active_log)
    total = float(active_log.sum())
    reflation_total = float(active_log.loc[status.astype(bool)].sum())
    non_reflation_total = float(active_log.loc[~status.astype(bool)].sum())
    positive = episodes.loc[episodes["active_log_return"] > 0.0].sort_values(
        "active_log_return", ascending=False
    )
    positive_sum = float(positive["active_log_return"].sum()) if not positive.empty else 0.0
    largest = float(positive.iloc[0]["active_log_return"]) if not positive.empty else 0.0

    def share(k: int) -> float:
        if positive_sum <= 0.0:
            return np.nan
        return float(positive.head(k)["active_log_return"].sum() / positive_sum)

    largest_row = positive.iloc[0] if not positive.empty else None
    summary = {
        "segment": label,
        "total_active_log_return": total,
        "reflation_day_active_log_return": reflation_total,
        "non_reflation_day_active_log_return": non_reflation_total,
        "reflation_episodes": int(len(episodes)),
        "positive_reflation_episodes": int(len(positive)),
        "positive_episode_fraction": float(len(positive) / len(episodes)) if len(episodes) else np.nan,
        "sum_positive_reflation_episode_active_log": positive_sum,
        "largest_positive_episode_active_log": largest,
        "largest_positive_episode_start": (
            largest_row["start"].date().isoformat() if largest_row is not None else None
        ),
        "largest_positive_episode_end": (
            largest_row["end"].date().isoformat() if largest_row is not None else None
        ),
        "largest_positive_episode_days": int(largest_row["days"]) if largest_row is not None else 0,
        "top1_share_of_positive_episode_contribution": share(1),
        "top3_share_of_positive_episode_contribution": share(3),
        "top5_share_of_positive_episode_contribution": share(5),
        "active_log_after_removing_largest_positive_reflation_episode": total - largest,
    }
    episodes = episodes.copy()
    episodes.insert(0, "segment", label)
    return summary, episodes


def run_diagnostics(phase_b_dir: Path) -> dict:
    daily = pd.read_csv(phase_b_dir / "phase-b-daily.csv", parse_dates=["date"])
    manifest = json.loads((phase_b_dir / "phase-b-manifest.json").read_text(encoding="utf-8"))
    returns, residual = reconstruct_asset_returns(daily)
    if residual > 1e-10:
        raise AssertionError(f"asset-return reconstruction residual too large: {residual}")

    index = returns.index
    status = lagged_reflation_status(index)
    _, control, match_meta = build_realized_exposure_matched_controls(
        daily,
        returns,
        cost_bps=float(manifest["primary_cost_bps"]),
    )
    strategy = (
        daily.loc[daily["strategy"].eq("v66_reflation_override")]
        .set_index("date")
        .sort_index()
    )
    if not strategy.index.equals(control.index):
        raise AssertionError("strategy and exposure-matched control indices differ")
    active_log = np.log1p(strategy["net_return"].astype(float)) - np.log1p(
        control["net_return"].astype(float)
    )

    masks = {
        "full_reused_history": pd.Series(True, index=index),
        "development_pre2020": pd.Series(index <= DEVELOPMENT_END, index=index),
        "post2019_reused_exploratory": pd.Series(index >= POST_START, index=index),
    }
    summaries: list[dict] = []
    episode_frames: list[pd.DataFrame] = []
    for label, mask in masks.items():
        sub_status = status.loc[mask.to_numpy()]
        sub_active = active_log.loc[mask.to_numpy()]
        summary, episodes = concentration_summary(label, sub_status, sub_active)
        summaries.append(summary)
        if label != "full_reused_history":
            episode_frames.append(episodes)

    pd.DataFrame(summaries).to_csv(
        phase_b_dir / "phase-b-posthoc-timing-concentration-summary.csv", index=False
    )
    pd.concat(episode_frames, ignore_index=True).to_csv(
        phase_b_dir / "phase-b-posthoc-reflation-episodes.csv", index=False,
        date_format="%Y-%m-%d",
    )

    result = {
        "schema_version": 2,
        "issue": 64,
        "phase": "B-posthoc-timing-concentration",
        "preregistered_primary_result_modified": False,
        "purpose": "measure whether Reflation timing attribution is broad or dominated by a small number of episodes",
        "causal_investable_benchmark": False,
        "control": "posthoc era realized-exposure-matched allocation",
        "asset_return_reconstruction_max_abs_residual": residual,
        "realized_exposure_matching": match_meta,
        "summary_rows": summaries,
        "interpretation_boundary": "Post-hoc attribution only. Episode concentration cannot upgrade reused-history evidence to confirmation and must not be used to retune the strategy."
    }
    (phase_b_dir / "phase-b-posthoc-timing-concentration.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Issue #64 Phase B episode concentration diagnostic")
    parser.add_argument("--phase-b-dir", type=Path, required=True)
    args = parser.parse_args()
    result = run_diagnostics(args.phase_b_dir)
    print(json.dumps({"summary_rows": result["summary_rows"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
