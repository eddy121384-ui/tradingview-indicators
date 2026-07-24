#!/usr/bin/env python3
"""Diagnose SPY five-feature K=8 sensitivity to deterministic HMM restarts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.preprocessing import StandardScaler

import compare_feature_sets
import compare_state_counts
import train_hmm

K = 8
FEATURE_SET = "baseline_er_downside"
DEFAULT_CUTOFF = "2026-07-23"
BASELINE_RESTART_OFFSETS = tuple(compare_state_counts.RESTART_OFFSETS)
DEFAULT_RESTART_OFFSETS = tuple(range(9))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Diagnose SPY five-feature K=8 restart sensitivity"
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--date-column", default="Date")
    parser.add_argument("--open-column", default="Open")
    parser.add_argument("--high-column", default="High")
    parser.add_argument("--low-column", default="Low")
    parser.add_argument("--close-column", default="Close")
    parser.add_argument("--symbol", default="SPY")
    parser.add_argument("--timeframe", default="1D")
    parser.add_argument("--train-fraction", type=float, default=0.80)
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=list(compare_state_counts.DEFAULT_SEEDS),
    )
    parser.add_argument("--cutoff", default=DEFAULT_CUTOFF)
    parser.add_argument(
        "--restart-offsets",
        type=int,
        nargs="+",
        default=list(DEFAULT_RESTART_OFFSETS),
    )
    return parser.parse_args()


def validate_frozen_seed_groups(group_seeds: list[int]) -> None:
    expected = list(compare_state_counts.DEFAULT_SEEDS)
    if group_seeds != expected:
        rendered = ", ".join(str(seed) for seed in expected)
        raise ValueError(
            "restart-sensitivity diagnostic requires frozen seed groups "
            f"[{rendered}] in order"
        )


def validate_restart_offsets(group_seeds: list[int], offsets: list[int]) -> None:
    if len(set(offsets)) != len(offsets):
        raise ValueError("restart offsets must be unique")
    if any(offset < 0 for offset in offsets):
        raise ValueError("restart offsets must be non-negative")
    if not set(BASELINE_RESTART_OFFSETS).issubset(offsets):
        raise ValueError("expanded restart offsets must include the existing schedule")

    attempt_owners: dict[int, int] = {}
    for group_seed in group_seeds:
        for offset in offsets:
            attempt_seed = group_seed + offset
            owner = attempt_owners.get(attempt_seed)
            if owner is not None:
                raise ValueError(
                    "restart-attempt seed sets overlap: "
                    f"attempt seed {attempt_seed} belongs to groups {owner} and {group_seed}"
                )
            attempt_owners[attempt_seed] = group_seed


def select_best_attempt(
    successful: list[dict[str, Any]], allowed_offsets: tuple[int, ...] | list[int]
) -> dict[str, Any]:
    allowed = set(allowed_offsets)
    eligible = [row for row in successful if row["offset"] in allowed]
    if not eligible:
        raise RuntimeError("no successful fit exists in the requested restart schedule")
    return max(
        eligible,
        key=lambda row: (row["train_log_likelihood"], -row["attempt_seed"]),
    )


def decision_for_summaries(
    baseline: dict[str, Any],
    expanded: dict[str, Any],
    expanded_selections: list[dict[str, Any]],
) -> dict[str, Any]:
    baseline_rare_check = baseline["guardrails"]["checks"]["no_rare_oos_states"]
    if baseline_rare_check:
        raise RuntimeError(
            "the frozen input no longer reproduces the known baseline rare-state failure"
        )

    expanded_passes = bool(expanded["guardrails"]["passed"])
    selected_new_restart = any(
        row["offset"] not in BASELINE_RESTART_OFFSETS
        for row in expanded_selections
    )
    recovered = expanded_passes and selected_new_restart
    return {
        "outcome": (
            "restart_schedule_insufficient"
            if recovered
            else "structurally_unstable_k8"
        ),
        "baseline_failed_guardrails": list(baseline["guardrails"]["failed"]),
        "expanded_failed_guardrails": list(expanded["guardrails"]["failed"]),
        "expanded_selected_new_restart": selected_new_restart,
        "reason": (
            "The broader deterministic sweep selected at least one restart outside "
            "the existing three-attempt schedule and the resulting three-group K=8 "
            "candidate passed every unchanged guardrail."
            if recovered
            else "The broader deterministic sweep did not produce a stable three-group "
            "K=8 candidate that both passed every unchanged guardrail and depended on a "
            "new restart; the K=8 result remains structurally restart-sensitive."
        ),
    }


def fit_attempt(
    train_matrix: np.ndarray,
    full_matrix: np.ndarray,
    train_rows: int,
    group_seed: int,
    offset: int,
    observation_matrix: np.ndarray,
    dates: np.ndarray,
    closes: np.ndarray,
) -> dict[str, Any]:
    attempt_seed = group_seed + offset
    try:
        model = compare_state_counts.fit_candidate(train_matrix, K, attempt_seed)
    except RuntimeError as exc:
        return {
            "group_seed": group_seed,
            "offset": offset,
            "attempt_seed": attempt_seed,
            "status": "failed",
            "error": f"{type(exc).__name__}: {exc}",
        }

    train_log_likelihood = float(model.score(train_matrix))
    metrics = compare_state_counts.fit_metrics(
        model,
        full_matrix,
        train_rows,
        group_seed,
        observation_matrix=observation_matrix,
        dates=dates,
        events=[],
        closes=closes,
    )
    metrics["group_seed"] = group_seed
    metrics["selected_attempt_seed"] = attempt_seed
    metrics["restart_attempts"] = []
    return {
        "group_seed": group_seed,
        "offset": offset,
        "attempt_seed": attempt_seed,
        "status": "ok",
        "train_log_likelihood": train_log_likelihood,
        "iterations": int(model.monitor_.iter),
        "minimum_oos_occupancy": min(metrics["occupancy_oos"]),
        "rare_state_count_oos": metrics["rare_state_count_oos"],
        "occupancy_drift_l1": metrics["occupancy_drift_l1"],
        "train_oos_likelihood_drift": metrics["train_oos_likelihood_drift"],
        "minimum_pairwise_separation": metrics["minimum_pairwise_separation"],
        "model": model,
        "metrics": metrics,
    }


def public_attempt(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key not in {"model", "metrics"}}


def summarize_selection(
    group_results: list[dict[str, Any]], offsets: tuple[int, ...] | list[int]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    selections = [select_best_attempt(row["successful"], offsets) for row in group_results]
    summary = compare_state_counts.summarize_candidate(
        [row["model"] for row in selections],
        [row["metrics"] for row in selections],
    )
    selection_rows = [
        {
            "group_seed": row["group_seed"],
            "offset": row["offset"],
            "attempt_seed": row["attempt_seed"],
            "train_log_likelihood": row["train_log_likelihood"],
            "minimum_oos_occupancy": row["minimum_oos_occupancy"],
            "rare_state_count_oos": row["rare_state_count_oos"],
        }
        for row in selections
    ]
    return summary, selection_rows


def markdown_report(result: dict[str, Any]) -> str:
    decision = result["decision"]
    lines = [
        "# SPY five-feature K=8 restart-sensitivity decision",
        "",
        f"**Outcome:** `{decision['outcome']}`",
        f"**Cutoff:** {result['scope']['cutoff']}",
        "",
        decision["reason"],
        "",
        "| Group | Existing selected | Existing min OOS | Expanded selected | Expanded min OOS |",
        "|---:|---:|---:|---:|---:|",
    ]
    baseline = {row["group_seed"]: row for row in result["baseline"]["selections"]}
    expanded = {row["group_seed"]: row for row in result["expanded"]["selections"]}
    for group_seed in result["scope"]["seeds"]:
        left, right = baseline[group_seed], expanded[group_seed]
        lines.append(
            f"| {group_seed} | {left['attempt_seed']} | {left['minimum_oos_occupancy']:.4%} | "
            f"{right['attempt_seed']} | {right['minimum_oos_occupancy']:.4%} |"
        )

    lines += [
        "",
        f"Existing guardrails: {', '.join(result['baseline']['summary']['guardrails']['failed']) or 'pass'}",
        f"Expanded guardrails: {', '.join(result['expanded']['summary']['guardrails']['failed']) or 'pass'}",
        "",
        "## All deterministic attempts",
        "",
        "| Group | Offset | Seed | Status | Train LL | Min OOS occupancy | Rare OOS states |",
        "|---:|---:|---:|---|---:|---:|---:|",
    ]
    for group in result["groups"]:
        for attempt in group["attempts"]:
            if attempt["status"] != "ok":
                lines.append(
                    f"| {group['group_seed']} | {attempt['offset']} | {attempt['attempt_seed']} | failed | — | — | — |"
                )
                continue
            lines.append(
                f"| {group['group_seed']} | {attempt['offset']} | {attempt['attempt_seed']} | ok | "
                f"{attempt['train_log_likelihood']:.3f} | {attempt['minimum_oos_occupancy']:.4%} | "
                f"{attempt['rare_state_count_oos']} |"
            )
    lines += [
        "",
        "The expanded selection still uses the existing highest-train-likelihood rule within each seed group. Features, K, split, scaler, inference, alignment, diagnostics, guardrails, and the 2% rare-state threshold are unchanged.",
        "",
    ]
    return "\n".join(lines)


def compare(args: argparse.Namespace) -> dict[str, Any]:
    if args.symbol.upper() != "SPY" or args.timeframe.upper() != "1D":
        raise ValueError("restart-sensitivity diagnostic is restricted to SPY 1D")
    if not 0.50 <= args.train_fraction < 1.0:
        raise ValueError("train_fraction must be in [0.50, 1.0)")
    validate_frozen_seed_groups(args.seeds)
    compare_state_counts.validate_seed_groups(args.seeds)
    validate_restart_offsets(args.seeds, args.restart_offsets)

    raw = train_hmm.load_ohlc(args)
    matches = raw.index[raw["date"].dt.strftime("%Y-%m-%d") == args.cutoff].tolist()
    if not matches:
        raise ValueError(f"cutoff date is unavailable in input: {args.cutoff}")
    raw = raw.iloc[: matches[-1] + 1].reset_index(drop=True)

    config = train_hmm.FeatureConfig()
    baseline = train_hmm.calculate_features(raw, config)
    enriched = compare_feature_sets.add_path_features(baseline, raw)
    feature_names = list(compare_feature_sets.FEATURE_SETS[FEATURE_SET])
    train_rows = int(len(enriched) * args.train_fraction)
    if train_rows < 200 or len(enriched) - train_rows < 50:
        raise ValueError(
            "chronological split requires at least 200 training and 50 out-of-sample rows"
        )

    scaler = StandardScaler()
    train_matrix = scaler.fit_transform(enriched.loc[: train_rows - 1, feature_names])
    full_matrix = scaler.transform(enriched[feature_names])
    observation_matrix = enriched[feature_names].to_numpy(dtype=float)
    dates = enriched["date"].dt.tz_localize(None).to_numpy(dtype="datetime64[D]")
    closes = enriched["close"].to_numpy(dtype=float)

    group_results = []
    for group_seed in args.seeds:
        attempts = [
            fit_attempt(
                train_matrix,
                full_matrix,
                train_rows,
                group_seed,
                offset,
                observation_matrix,
                dates,
                closes,
            )
            for offset in args.restart_offsets
        ]
        successful = [row for row in attempts if row["status"] == "ok"]
        if not successful:
            raise RuntimeError(f"all expanded restart attempts failed for group {group_seed}")
        group_results.append(
            {
                "group_seed": group_seed,
                "attempts": attempts,
                "successful": successful,
            }
        )

    baseline_summary, baseline_selections = summarize_selection(
        group_results, BASELINE_RESTART_OFFSETS
    )
    expanded_summary, expanded_selections = summarize_selection(
        group_results, args.restart_offsets
    )
    decision = decision_for_summaries(
        baseline_summary, expanded_summary, expanded_selections
    )

    return compare_state_counts.strict_json(
        {
            "schema_version": 1,
            "scope": {
                "symbol": "SPY",
                "timeframe": "1D",
                "feature_set": FEATURE_SET,
                "k": K,
                "cutoff": args.cutoff,
                "seeds": args.seeds,
            },
            "method": {
                "train_fraction": args.train_fraction,
                "baseline_restart_offsets": list(BASELINE_RESTART_OFFSETS),
                "expanded_restart_offsets": args.restart_offsets,
                "selection": "highest finite converged train log likelihood per seed group",
                "rare_state_occupancy": compare_state_counts.RARE_STATE_THRESHOLD,
            },
            "sample": {
                "raw_rows_through_cutoff": len(raw),
                "usable_rows": len(enriched),
                "train_rows": train_rows,
                "oos_rows": len(enriched) - train_rows,
            },
            "groups": [
                {
                    "group_seed": row["group_seed"],
                    "attempts": [public_attempt(item) for item in row["attempts"]],
                }
                for row in group_results
            ],
            "baseline": {
                "selections": baseline_selections,
                "summary": baseline_summary,
            },
            "expanded": {
                "selections": expanded_selections,
                "summary": expanded_summary,
            },
            "decision": decision,
        }
    )


def main() -> int:
    args = parse_args()
    result = compare(args)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "k8-restart-sensitivity.json"
    report_path = args.output_dir / "k8-restart-sensitivity.md"
    json_path.write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    report_path.write_text(markdown_report(result), encoding="utf-8")
    print(f"decision: {result['decision']['outcome']}")
    print(f"wrote: {json_path}")
    print(f"wrote: {report_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
