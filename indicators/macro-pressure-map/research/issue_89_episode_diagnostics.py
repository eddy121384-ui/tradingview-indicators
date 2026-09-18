#!/usr/bin/env python3
"""Issue #89 episode concentration and leave-one-positive-episode-out diagnostic.

This module is governed by a secondary robustness preregistration created after
primary portfolio results were viewed but before episode-level results were
computed. It may diagnose concentration; it may not tune the primary policy.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from asset_allocation_phase_a import ASSETS
from asset_allocation_phase_a_frozen import load_frozen_transitions, map_regimes_to_outcome_calendar
from asset_allocation_phase_b import (
    month_start_mask,
    portfolio_metrics,
    segment_sim,
    simulate_portfolio,
    template_change_mask,
)
from asset_allocation_phase_b_diagnostics import (
    mean_invested_weights,
    solve_static_target_for_realized_average,
)
from issue_64_outcome_snapshot import load_frozen_prices
from issue_89_ex_ante_regime_policy import (
    STRATEGY,
    build_targets,
    determine_eval_index,
    load_contract,
)
from issue_89_exposure_diagnostics import build_controls

HERE = Path(__file__).resolve().parent
ROBUSTNESS_CONTRACT = HERE / "decisions" / "issue-89-episode-robustness-preregistered.json"


def load_robustness_contract(path: Path = ROBUSTNESS_CONTRACT) -> dict:
    contract = json.loads(path.read_text(encoding="utf-8"))
    if contract.get("issue") != 89:
        raise ValueError("unexpected Issue #89 robustness contract identity")
    if contract.get("primary_policy_modified") is not False:
        raise ValueError("episode robustness may not modify the primary policy")
    if contract.get("primary_portfolio_results_already_viewed") is not True:
        raise ValueError("robustness contract must disclose primary results were already viewed")
    if contract.get("frozen_before_issue_89_episode_results_viewed") is not True:
        raise ValueError("episode robustness semantics must be frozen before episode results")
    return contract


def contiguous_template_runs(template: pd.Series) -> list[dict]:
    if template.empty:
        return []
    if template.isna().any():
        raise ValueError("episode template cannot contain missing values")
    values = template.astype(str).to_numpy()
    runs: list[dict] = []
    start = 0
    for i in range(1, len(values) + 1):
        if i == len(values) or values[i] != values[start]:
            runs.append({
                "start_position": start,
                "end_position": i - 1,
                "regime": values[start],
                "start": template.index[start],
                "end": template.index[i - 1],
                "days": i - start,
            })
            start = i
    return runs


def eligible_episode_table(
    template: pd.Series,
    active_log: pd.Series,
    *,
    segment: str,
    start: pd.Timestamp | None,
    end: pd.Timestamp | None,
) -> pd.DataFrame:
    if not template.index.equals(active_log.index):
        raise ValueError("template and active log must share one index")
    rows: list[dict] = []
    for run in contiguous_template_runs(template):
        if start is not None and run["start"] < start:
            continue
        if end is not None and run["end"] > end:
            continue
        contribution = float(active_log.loc[run["start"]:run["end"]].sum())
        rows.append({
            "segment": segment,
            **run,
            "active_log_return": contribution,
        })
    return pd.DataFrame(rows)


def summarize_episodes(episodes: pd.DataFrame) -> dict:
    if episodes.empty:
        raise RuntimeError("no eligible Issue #89 episodes")
    positive = episodes.loc[episodes["active_log_return"] > 0.0].sort_values("active_log_return", ascending=False)
    negative = episodes.loc[episodes["active_log_return"] < 0.0].sort_values("active_log_return")
    if positive.empty:
        raise RuntimeError("no positive Issue #89 episode available for leaveout")
    if negative.empty:
        raise RuntimeError("no negative Issue #89 episode available for concentration report")
    positive_sum = float(positive["active_log_return"].sum())
    winner = positive.iloc[0]
    loser = negative.iloc[0]
    return {
        "episodes": int(len(episodes)),
        "positive_episodes": int(len(positive)),
        "negative_episodes": int(len(negative)),
        "sum_positive_episode_active_log": positive_sum,
        "largest_positive_episode": {
            "regime": str(winner["regime"]),
            "start": winner["start"].date().isoformat(),
            "end": winner["end"].date().isoformat(),
            "days": int(winner["days"]),
            "active_log_return": float(winner["active_log_return"]),
        },
        "largest_negative_episode": {
            "regime": str(loser["regime"]),
            "start": loser["start"].date().isoformat(),
            "end": loser["end"].date().isoformat(),
            "days": int(loser["days"]),
            "active_log_return": float(loser["active_log_return"]),
        },
        "top1_share_of_positive_episode_contribution": (
            float(winner["active_log_return"] / positive_sum) if positive_sum > 0.0 else np.nan
        ),
    }


def fresh_leaveout_control(
    leaveout: pd.DataFrame,
    returns: pd.DataFrame,
    *,
    start: pd.Timestamp | None,
    end: pd.Timestamp | None,
    cost_bps: float,
    name: str,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    start_str = None if start is None else start.date().isoformat()
    end_str = None if end is None else end.date().isoformat()
    leaveout_seg = segment_sim(leaveout, start_str, end_str)
    returns_seg = returns.loc[leaveout_seg.index]
    desired = mean_invested_weights(leaveout_seg)
    target, control, meta = solve_static_target_for_realized_average(
        returns_seg,
        desired,
        cost_bps=cost_bps,
        name=name,
    )
    return leaveout_seg, control, {
        **meta,
        "matching_basis": "leaveout realized average invested_weight_* exposure",
        "target_weights": target,
        "segment_start": start_str,
        "segment_end": end_str,
    }


def metric_delta(strategy: pd.DataFrame, control: pd.DataFrame) -> dict:
    left = portfolio_metrics(strategy, annualization=252)
    right = portfolio_metrics(control, annualization=252)
    return {
        "delta_CAGR": float(left["CAGR"] - right["CAGR"]),
        "delta_Sharpe": float(left["Sharpe"] - right["Sharpe"]),
        "delta_maximum_drawdown": float(left["maximum_drawdown"] - right["maximum_drawdown"]),
        "delta_Calmar": float(left["Calmar"] - right["Calmar"]),
    }


def run(evidence_dir: Path) -> dict:
    primary_contract = load_contract()
    robustness = load_robustness_contract()
    manifest = json.loads((evidence_dir / "issue-89-manifest.json").read_text(encoding="utf-8"))
    daily = pd.read_csv(evidence_dir / "issue-89-daily.csv", parse_dates=["date"])
    strategy = daily.loc[daily["strategy"].eq(STRATEGY)].set_index("date").sort_index()

    prices, _ = load_frozen_prices("2007-01-01", None)
    history = map_regimes_to_outcome_calendar(prices, load_frozen_transitions())
    regimes = history["core_regime"]
    eval_index, returns_all = determine_eval_index(prices, regimes, primary_contract)
    returns = returns_all.loc[eval_index, list(ASSETS)]
    targets, _, template = build_targets(eval_index, regimes, returns_all, primary_contract)
    if not strategy.index.equals(eval_index):
        raise AssertionError("Issue #89 episode strategy index drifted from evaluator index")

    cost_bps = float(manifest["primary_cost_bps"])
    full_control, era_control, matching = build_controls(strategy, returns, cost_bps=cost_bps)
    segments = {
        "full_reused_history": (None, None, full_control, matching["full"]["target_weights"]),
        "development_pre2020": (
            None,
            pd.Timestamp("2019-12-31"),
            era_control,
            matching["development_target_weights"],
        ),
        "post2019_reused_exploratory": (
            pd.Timestamp("2020-01-01"),
            None,
            era_control,
            matching["post2019_target_weights"],
        ),
    }

    all_episode_frames: list[pd.DataFrame] = []
    summaries: list[dict] = []
    for label, (start, end, original_control, replacement_weights) in segments.items():
        start_str = None if start is None else start.date().isoformat()
        end_str = None if end is None else end.date().isoformat()
        strategy_seg = segment_sim(strategy, start_str, end_str)
        control_seg = segment_sim(original_control, start_str, end_str)
        active_seg = np.log1p(strategy_seg["net_return"].astype(float)) - np.log1p(
            control_seg["net_return"].astype(float)
        )

        episodes = eligible_episode_table(
            template,
            active_seg.reindex(template.index).fillna(0.0),
            segment=label,
            start=start,
            end=end,
        )
        # eligible_episode_table receives a full-index active series. Runs outside
        # the segment are filtered before their contribution is read, so zeros
        # introduced outside the segment cannot affect eligible episode values.
        episode_summary = summarize_episodes(episodes)
        winner = episode_summary["largest_positive_episode"]

        modified_targets = targets[STRATEGY].copy()
        winner_start = pd.Timestamp(winner["start"])
        winner_end = pd.Timestamp(winner["end"])
        winner_mask = (modified_targets.index >= winner_start) & (modified_targets.index <= winner_end)
        replacement = np.asarray([float(replacement_weights[a]) for a in ASSETS], dtype=float)
        modified_targets.loc[winner_mask, list(ASSETS)] = replacement

        modified_template = template.astype("object").copy()
        modified_template.loc[winner_mask] = f"__leaveout_static__{label}"
        modified_rebalance = (
            month_start_mask(eval_index) | template_change_mask(modified_template)
        ).astype(bool)
        leaveout = simulate_portfolio(
            returns,
            modified_targets,
            modified_rebalance,
            cost_bps=cost_bps,
            name=f"issue89_leaveout_{label}",
        )

        leaveout_seg, leaveout_control, leaveout_meta = fresh_leaveout_control(
            leaveout,
            returns,
            start=start,
            end=end,
            cost_bps=cost_bps,
            name=f"issue89_leaveout_match_{label}",
        )
        tolerance = float(robustness["exposure_match_tolerance"])
        if float(leaveout_meta["max_abs_invested_weight_mismatch"]) > tolerance:
            raise AssertionError("Issue #89 leaveout exposure match exceeds robustness tolerance")

        normal_active_log = float(np.log1p(strategy_seg["net_return"]).sum() - np.log1p(control_seg["net_return"]).sum())
        leaveout_active_log = float(np.log1p(leaveout_seg["net_return"]).sum() - np.log1p(leaveout_control["net_return"]).sum())
        summary = {
            "segment": label,
            **episode_summary,
            "normal_active_log_return": normal_active_log,
            "active_log_after_removing_largest_positive_episode": leaveout_active_log,
            "normal_incremental": metric_delta(strategy_seg, control_seg),
            "incremental_after_leaveout": metric_delta(leaveout_seg, leaveout_control),
            "leaveout_realized_exposure_matching": leaveout_meta,
            "leaveout_method": robustness["leaveout_replacement"],
        }
        summaries.append(summary)
        all_episode_frames.append(episodes)

    pd.concat(all_episode_frames, ignore_index=True).to_csv(
        evidence_dir / "issue-89-episodes.csv",
        index=False,
        date_format="%Y-%m-%d",
    )
    result = {
        "schema_version": 1,
        "issue": 89,
        "purpose": "diagnose whether ex-ante policy switching attribution is concentrated in a few regime episodes",
        "primary_policy_modified": False,
        "secondary_robustness_contract": str(ROBUSTNESS_CONTRACT.relative_to(HERE)),
        "secondary_contract_frozen_before_episode_results": True,
        "summary_rows": summaries,
        "interpretation_boundary": robustness["interpretation_boundary"],
    }
    (evidence_dir / "issue-89-episode-robustness.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Issue #89 episode robustness")
    parser.add_argument("--evidence-dir", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.evidence_dir)
    print(json.dumps({"summary_rows": result["summary_rows"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
