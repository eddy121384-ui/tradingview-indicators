#!/usr/bin/env python3
"""Issue #61 pre-PnL audit: Candidate Stage 3/6 while base lifecycle holds.

Formal Stage 3/6 proved almost absent. This diagnostic asks whether the existing
v0.6 candidate layer nevertheless surfaces Re-accumulation / Redistribution
inside an active Formal trend. Counts/durations only; no price outcome.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from diagnose_stage_lifecycle_break_timing import load_frozen_pairs
from diagnose_stage_lifecycle_consolidation_occupancy import run_lengths
from evaluate_stage_lifecycle_base import stage_lifecycle_signal
from generate_v06_phase_b_core import load_phase_b_namespace


def summarize_candidate(
    position: np.ndarray,
    formal: np.ndarray,
    candidate: np.ndarray,
    direction: int,
    trend_stage: int,
    consolidation_stage: int,
) -> dict[str, object]:
    held = position == direction
    candidate_consolidation = held & (candidate == consolidation_stage)
    candidate_inside_formal_trend = candidate_consolidation & (formal == trend_stage)
    held_bars = int(np.sum(held))
    bars = int(np.sum(candidate_consolidation))
    runs = run_lengths(candidate_consolidation)

    onsets = 0
    from_matching_formal_trend = 0
    for i in range(1, len(candidate_consolidation)):
        if candidate_consolidation[i] and not candidate_consolidation[i - 1]:
            onsets += 1
            if int(formal[i]) == trend_stage:
                from_matching_formal_trend += 1

    return {
        "held_bars": held_bars,
        "candidate_consolidation_bars": bars,
        "candidate_consolidation_share_of_held": None if held_bars == 0 else bars / held_bars,
        "candidate_inside_matching_formal_trend_bars": int(np.sum(candidate_inside_formal_trend)),
        "candidate_runs": int(len(runs)),
        "median_candidate_run_bars": None if not runs else float(np.median(runs)),
        "max_candidate_run_bars": None if not runs else int(max(runs)),
        "candidate_onsets": onsets,
        "candidate_onsets_while_formal_trend": from_matching_formal_trend,
    }


def analyze_pair(frame: pd.DataFrame) -> dict[str, object]:
    ns = load_phase_b_namespace()
    config_type = ns["PriceOnlyConfig"]
    compute_price_only = ns["compute_price_only"]
    config = config_type()
    model = compute_price_only(frame.copy(), config)

    formal = pd.to_numeric(model["formal_id"], errors="coerce").fillna(0).to_numpy(int)
    candidate = pd.to_numeric(model["candidate_display_id"], errors="coerce").fillna(0).to_numpy(int)
    fresh_up = pd.to_numeric(model["range_break_up"], errors="coerce").fillna(0).to_numpy(float) > 0.5
    fresh_down = pd.to_numeric(model["range_break_dn"], errors="coerce").fillna(0).to_numpy(float) > 0.5
    warmup = int(config.rank_len - 1)
    signal, _ = stage_lifecycle_signal(
        formal, fresh_up, fresh_down, warmup=warmup, confirm_bars=int(config.confirm_bars)
    )

    return {
        "rows": int(len(frame)),
        "warmup_bars": warmup,
        "long_candidate_stage3": summarize_candidate(signal, formal, candidate, 1, 2, 3),
        "short_candidate_stage6": summarize_candidate(signal, formal, candidate, -1, 5, 6),
    }


def aggregate_side(pairs: dict[str, dict[str, object]], key: str) -> dict[str, object]:
    rows = [pair[key] for pair in pairs.values()]  # type: ignore[index]
    held = int(sum(int(row["held_bars"]) for row in rows))
    bars = int(sum(int(row["candidate_consolidation_bars"]) for row in rows))
    run_medians = [float(row["median_candidate_run_bars"]) for row in rows if row["median_candidate_run_bars"] is not None]
    return {
        "held_bars": held,
        "candidate_consolidation_bars": bars,
        "candidate_consolidation_share_of_held": None if held == 0 else bars / held,
        "candidate_inside_matching_formal_trend_bars": int(sum(int(row["candidate_inside_matching_formal_trend_bars"]) for row in rows)),
        "candidate_runs": int(sum(int(row["candidate_runs"]) for row in rows)),
        "candidate_onsets": int(sum(int(row["candidate_onsets"]) for row in rows)),
        "candidate_onsets_while_formal_trend": int(sum(int(row["candidate_onsets_while_formal_trend"]) for row in rows)),
        "pairs_with_any_candidate_consolidation": int(sum(int(row["candidate_consolidation_bars"]) > 0 for row in rows)),
        "median_pair_median_candidate_run_bars": None if not run_medians else float(np.median(run_medians)),
    }


def build_report() -> dict[str, object]:
    pairs = {pair: analyze_pair(frame) for pair, frame in load_frozen_pairs().items()}
    return {
        "schema_version": 1,
        "issue": 61,
        "status": "PRE_PNL_CANDIDATE_CONSOLIDATION_AUDIT",
        "candidate_field": "candidate_display_id",
        "pairs": pairs,
        "aggregate": {
            "pair_count": len(pairs),
            "long_candidate_stage3": aggregate_side(pairs, "long_candidate_stage3"),
            "short_candidate_stage6": aggregate_side(pairs, "short_candidate_stage6"),
        },
        "boundary": "Counts/durations only. No PnL. Candidate layer is existing v0.6 semantics; no new threshold is introduced.",
    }


def pct(value: float | None) -> str:
    return "—" if value is None else f"{100.0 * value:.2f}%"


def render_markdown(report: dict[str, object]) -> str:
    agg = report["aggregate"]  # type: ignore[index]
    lines = [
        "# Issue #61 — Candidate Stage 3 / 6 consolidation audit",
        "",
        "**Counts/durations only. No price outcomes.**",
        "",
        "Formal Stage 3/6 were nearly absent in the base lifecycle. This audit checks whether the existing `candidate_display_id` layer surfaces those consolidation semantics while Formal remains in the matching trend stage.",
        "",
        "## Aggregate",
        "",
        "| State | Held bars | Candidate bars | Share held | Bars inside matching Formal trend | Runs | Onsets | Onsets while Formal trend | Pairs with any | Median pair run |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for key, label in (("long_candidate_stage3", "Long / Candidate Stage 3"), ("short_candidate_stage6", "Short / Candidate Stage 6")):
        row = agg[key]
        lines.append(
            f"| {label} | {row['held_bars']} | {row['candidate_consolidation_bars']} | {pct(row['candidate_consolidation_share_of_held'])} | "
            f"{row['candidate_inside_matching_formal_trend_bars']} | {row['candidate_runs']} | {row['candidate_onsets']} | "
            f"{row['candidate_onsets_while_formal_trend']} | {row['pairs_with_any_candidate_consolidation']}/{agg['pair_count']} | "
            f"{row['median_pair_median_candidate_run_bars'] if row['median_pair_median_candidate_run_bars'] is not None else '—'} |"
        )

    lines += ["", "## Per pair", "", "| Pair | Long held | Cand3 bars | Cand3 share | Cand3 runs | Short held | Cand6 bars | Cand6 share | Cand6 runs |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for pair, result in report["pairs"].items():  # type: ignore[index]
        long = result["long_candidate_stage3"]
        short = result["short_candidate_stage6"]
        lines.append(
            f"| {pair} | {long['held_bars']} | {long['candidate_consolidation_bars']} | {pct(long['candidate_consolidation_share_of_held'])} | {long['candidate_runs']} | "
            f"{short['held_bars']} | {short['candidate_consolidation_bars']} | {pct(short['candidate_consolidation_share_of_held'])} | {short['candidate_runs']} |"
        )
    lines += ["", "## Boundary", "", str(report["boundary"]), ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--md-output", type=Path, required=True)
    args = parser.parse_args()
    report = build_report()
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.md_output.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["aggregate"], indent=2))


if __name__ == "__main__":
    main()
