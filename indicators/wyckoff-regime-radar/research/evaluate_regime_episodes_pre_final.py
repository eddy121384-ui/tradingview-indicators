#!/usr/bin/env python3
"""Evaluate formal-state occupancy and episodes before final OOS for Issue #55.

Purpose: diagnose whether the six-stage formal state is meaningfully populated on
FX or collapses/sticks into a small subset of states. Development and
exploratory OOS only; final-OOS rows are never passed into the model.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from evaluate_regime_paths_pre_final import HORIZONS, future_metrics, load_frozen_pair
from price_only_core import STAGE_NAMES, PriceOnlyConfig, compute_price_only


ALLOWED_SPLITS = ("development", "exploratory_oos")
STAGES = tuple(range(1, 7))


def runs_in_split(formal: np.ndarray, start: int, end: int) -> list[dict]:
    runs: list[dict] = []
    i = start
    while i <= end:
        stage = int(formal[i])
        j = i
        while j + 1 <= end and int(formal[j + 1]) == stage:
            j += 1
        left_censored = i == start and i > 0 and int(formal[i - 1]) == stage
        # At the end of the pre-final array the next state is intentionally unknown.
        right_censored = j == end
        runs.append(
            {
                "stage": stage,
                "start_index": i,
                "end_index": j,
                "duration_rows": j - i + 1,
                "left_censored": left_censored,
                "right_censored": right_censored,
            }
        )
        i = j + 1
    return runs


def summarize_episode_entries(
    frame: pd.DataFrame,
    runs: list[dict],
    split_start: int,
    split_end: int,
) -> dict:
    output = {}
    metrics_by_horizon = {h: future_metrics(frame, h) for h in HORIZONS}
    for stage in STAGES:
        stage_runs = [run for run in runs if run["stage"] == stage]
        complete = [
            run
            for run in stage_runs
            if not run["left_censored"] and not run["right_censored"]
        ]
        durations = np.array([run["duration_rows"] for run in complete], dtype=float)
        stage_result = {
            "run_count_including_censored": len(stage_runs),
            "complete_episode_count": len(complete),
            "complete_duration_mean": float(np.mean(durations)) if len(durations) else None,
            "complete_duration_median": float(np.median(durations)) if len(durations) else None,
            "entry_forward_paths": {},
        }
        for horizon, metrics in metrics_by_horizon.items():
            entries = [
                run["start_index"]
                for run in stage_runs
                if run["start_index"] >= split_start
                and run["start_index"] + horizon <= split_end
                and np.isfinite(metrics["forward_return"][run["start_index"]])
            ]
            def avg(metric: str):
                vals = np.array([metrics[metric][idx] for idx in entries], dtype=float)
                vals = vals[np.isfinite(vals)]
                return float(np.mean(vals)) if len(vals) else None
            stage_result["entry_forward_paths"][str(horizon)] = {
                "episode_entry_count": len(entries),
                "forward_return_mean": avg("forward_return"),
                "mfe_mean": avg("mfe"),
                "mae_mean": avg("mae"),
                "realized_vol_mean": avg("realized_vol"),
            }
        output[str(stage)] = stage_result
    return output


def transition_matrix(runs: list[dict]) -> dict:
    counts = {str(stage): {str(other): 0 for other in STAGES} for stage in STAGES}
    for left, right in zip(runs, runs[1:]):
        a, b = int(left["stage"]), int(right["stage"])
        if a in STAGES and b in STAGES and a != b:
            counts[str(a)][str(b)] += 1
    return counts


def analyze_pair(frame: pd.DataFrame, meta: dict) -> dict:
    exp_end = int(meta["splits"]["exploratory_oos"]["end_index"])
    pre_final = frame.iloc[: exp_end + 1].copy().reset_index(drop=True)
    model = compute_price_only(pre_final, PriceOnlyConfig())
    formal = pd.to_numeric(model["formal_id"], errors="coerce").fillna(0).to_numpy(int)

    result = {
        "model_rows_computed": len(pre_final),
        "final_oos_rows_computed": 0,
        "splits": {},
    }
    for split_name in ALLOWED_SPLITS:
        split = meta["splits"][split_name]
        start, end = int(split["start_index"]), int(split["end_index"])
        values = formal[start : end + 1]
        counts = {str(stage): int(np.sum(values == stage)) for stage in range(0, 7)}
        shares = {str(stage): count / len(values) for stage, count in ((s, counts[str(s)]) for s in range(0, 7))}
        runs = runs_in_split(formal, start, end)
        populated = [stage for stage in STAGES if shares[str(stage)] >= 0.01]
        dominant_stage = max(range(0, 7), key=lambda stage: shares[str(stage)])
        result["splits"][split_name] = {
            "start_date": split["start_date"],
            "end_date": split["end_date"],
            "rows": len(values),
            "state_counts": counts,
            "state_shares": shares,
            "stages_with_at_least_1pct_share": populated,
            "populated_stage_count": len(populated),
            "dominant_state": dominant_stage,
            "dominant_state_share": shares[str(dominant_stage)],
            "episodes": summarize_episode_entries(pre_final, runs, start, end),
            "transitions": transition_matrix(runs),
        }
    return result


def build_report(manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("final_oos_status") != "SEALED_DO_NOT_EVALUATE":
        raise ValueError("refusing to run without final-OOS seal")
    pairs = {
        pair: analyze_pair(load_frozen_pair(manifest_path, meta), meta)
        for pair, meta in manifest["pairs"].items()
    }
    collapse_rows = []
    for pair, pair_report in pairs.items():
        for split_name in ALLOWED_SPLITS:
            split = pair_report["splits"][split_name]
            collapse_rows.append(
                {
                    "pair": pair,
                    "split": split_name,
                    "populated_stage_count": split["populated_stage_count"],
                    "dominant_state": split["dominant_state"],
                    "dominant_state_share": split["dominant_state_share"],
                    "markup_share": split["state_shares"]["2"],
                    "markdown_share": split["state_shares"]["5"],
                }
            )
    return {
        "schema_version": 1,
        "issue": 55,
        "status": "pre_final_formal_state_occupancy_episode_analysis",
        "stage_names": {str(stage): STAGE_NAMES[stage] for stage in range(0, 7)},
        "final_oos_status": "SEALED_NOT_COMPUTED",
        "pairs": pairs,
        "collapse_diagnostic": collapse_rows,
        "boundary": (
            "Development and exploratory OOS only. Formal-state occupancy, episodes and entry paths are descriptive; "
            "no final OOS and no trading-utility claim."
        ),
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# Issue #55 — Pre-final-OOS formal-state occupancy and episodes",
        "",
        "Final OOS remains **SEALED / NOT COMPUTED**.",
        "",
        "A stage counts as materially populated here if it occupies at least 1% of bars in that split.",
        "",
        "| Pair | Split | Populated stages | Dominant state | Dominant share | Markup share | Markdown share |",
        "|---|---|---:|---|---:|---:|---:|",
    ]
    for row in report["collapse_diagnostic"]:
        dominant = report["stage_names"][str(row["dominant_state"])]
        lines.append(
            f"| {row['pair']} | {row['split']} | {row['populated_stage_count']} | {dominant} | "
            f"{row['dominant_state_share'] * 100:.1f}% | {row['markup_share'] * 100:.1f}% | "
            f"{row['markdown_share'] * 100:.1f}% |"
        )

    lines.extend(["", "## Complete episode counts / median duration", ""])
    for pair, pair_report in report["pairs"].items():
        lines.append(f"### {pair}")
        lines.append("")
        lines.append("| Split | Stage | Episodes | Median bars |")
        lines.append("|---|---|---:|---:|")
        for split_name, split in pair_report["splits"].items():
            for stage in range(1, 7):
                ep = split["episodes"][str(stage)]
                med = "—" if ep["complete_duration_median"] is None else f"{ep['complete_duration_median']:.1f}"
                lines.append(
                    f"| {split_name} | {stage} {report['stage_names'][str(stage)]} | "
                    f"{ep['complete_episode_count']} | {med} |"
                )
        lines.append("")
    lines.append("Boundary: descriptive development + exploratory OOS only; no final OOS and no trading utility claim.")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    here = Path(__file__).resolve().parent
    parser.add_argument(
        "--manifest",
        type=Path,
        default=here / "data" / "issue-55-static-fx-canonical-manifest.json",
    )
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--md-output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_report(args.manifest)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.md_output:
        args.md_output.parent.mkdir(parents=True, exist_ok=True)
        args.md_output.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["collapse_diagnostic"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
