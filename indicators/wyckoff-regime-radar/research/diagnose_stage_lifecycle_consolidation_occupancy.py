#!/usr/bin/env python3
"""Issue #61 Phase-C pre-PnL audit of Stage 3/6 exposure occupancy.

Counts only.  This diagnostic determines whether Re-accumulation / Redistribution
occur often enough while the frozen base lifecycle is holding exposure to justify
later research on partial risk reduction.  No price outcome is computed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from diagnose_stage_lifecycle_break_timing import load_frozen_pairs
from evaluate_stage_lifecycle_base import stage_lifecycle_signal
from generate_v06_phase_b_core import load_phase_b_namespace


def run_lengths(mask: np.ndarray) -> list[int]:
    lengths: list[int] = []
    current = 0
    for value in mask.astype(bool):
        if value:
            current += 1
        elif current:
            lengths.append(current)
            current = 0
    if current:
        lengths.append(current)
    return lengths


def summarize_side(position: np.ndarray, formal: np.ndarray, direction: int, trend_stage: int, consolidation_stage: int) -> dict[str, object]:
    held = position == direction
    trend = held & (formal == trend_stage)
    consolidation = held & (formal == consolidation_stage)
    held_bars = int(np.sum(held))
    trend_bars = int(np.sum(trend))
    consolidation_bars = int(np.sum(consolidation))
    runs = run_lengths(consolidation)

    transitions_into_consolidation = 0
    from_trend = 0
    for i in range(1, len(formal)):
        if consolidation[i] and not consolidation[i - 1]:
            transitions_into_consolidation += 1
            if held[i - 1] and int(formal[i - 1]) == trend_stage:
                from_trend += 1

    return {
        "held_bars": held_bars,
        "trend_stage_bars": trend_bars,
        "consolidation_stage_bars": consolidation_bars,
        "consolidation_share_of_held": None if held_bars == 0 else consolidation_bars / held_bars,
        "consolidation_runs": int(len(runs)),
        "median_consolidation_run_bars": None if not runs else float(np.median(runs)),
        "max_consolidation_run_bars": None if not runs else int(max(runs)),
        "transitions_into_consolidation": transitions_into_consolidation,
        "transitions_from_trend_stage": from_trend,
    }


def analyze_pair(frame: pd.DataFrame) -> dict[str, object]:
    namespace = load_phase_b_namespace()
    config_type = namespace["PriceOnlyConfig"]
    compute_price_only = namespace["compute_price_only"]
    config = config_type()
    model = compute_price_only(frame.copy(), config)

    formal = pd.to_numeric(model["formal_id"], errors="coerce").fillna(0).to_numpy(int)
    fresh_up = pd.to_numeric(model["range_break_up"], errors="coerce").fillna(0).to_numpy(float) > 0.5
    fresh_down = pd.to_numeric(model["range_break_dn"], errors="coerce").fillna(0).to_numpy(float) > 0.5
    warmup = int(config.rank_len - 1)
    signal, events = stage_lifecycle_signal(
        formal,
        fresh_up,
        fresh_down,
        warmup=warmup,
        confirm_bars=int(config.confirm_bars),
    )

    return {
        "rows": int(len(frame)),
        "warmup_bars": warmup,
        "lifecycle_entries": int(events["bull_setup_confirmed_entries"] + events["bear_setup_confirmed_entries"] + events["bull_direct_stage2_break_entries"] + events["bear_direct_stage5_break_entries"]),
        "long": summarize_side(signal, formal, direction=1, trend_stage=2, consolidation_stage=3),
        "short": summarize_side(signal, formal, direction=-1, trend_stage=5, consolidation_stage=6),
    }


def aggregate_side(pairs: dict[str, dict[str, object]], side: str) -> dict[str, object]:
    rows = [pair[side] for pair in pairs.values()]  # type: ignore[index]
    held = sum(int(row["held_bars"]) for row in rows)
    consolidation = sum(int(row["consolidation_stage_bars"]) for row in rows)
    medians = [float(row["median_consolidation_run_bars"]) for row in rows if row["median_consolidation_run_bars"] is not None]
    return {
        "held_bars": held,
        "trend_stage_bars": int(sum(int(row["trend_stage_bars"]) for row in rows)),
        "consolidation_stage_bars": consolidation,
        "consolidation_share_of_held": None if held == 0 else consolidation / held,
        "consolidation_runs": int(sum(int(row["consolidation_runs"]) for row in rows)),
        "median_pair_median_consolidation_run_bars": None if not medians else float(np.median(medians)),
        "transitions_into_consolidation": int(sum(int(row["transitions_into_consolidation"]) for row in rows)),
        "transitions_from_trend_stage": int(sum(int(row["transitions_from_trend_stage"]) for row in rows)),
        "pairs_with_any_consolidation_exposure": int(sum(int(row["consolidation_stage_bars"]) > 0 for row in rows)),
    }


def build_report() -> dict[str, object]:
    pairs = {pair: analyze_pair(frame) for pair, frame in load_frozen_pairs().items()}
    return {
        "schema_version": 1,
        "issue": 61,
        "status": "PHASE_C_PRE_PNL_CONSOLIDATION_OCCUPANCY_AUDIT",
        "pairs": pairs,
        "aggregate": {
            "pair_count": len(pairs),
            "long_stage3": aggregate_side(pairs, "long"),
            "short_stage6": aggregate_side(pairs, "short"),
        },
        "boundary": "Counts and durations only. No return, Sharpe, drawdown, stop, target, or sizing outcome is computed.",
    }


def pct(value: float | None) -> str:
    return "—" if value is None else f"{100.0 * value:.2f}%"


def render_markdown(report: dict[str, object]) -> str:
    agg = report["aggregate"]  # type: ignore[index]
    lines = [
        "# Issue #61 — Phase C pre-PnL Stage 3 / 6 occupancy audit",
        "",
        "**Counts/durations only. No price outcomes.**",
        "",
        "Question: do Stage 3 / Stage 6 occur often enough while the frozen base lifecycle is actually holding exposure to justify a partial-risk-reduction rule?",
        "",
        "## Aggregate",
        "",
        "| State | Held bars | Consolidation bars | Share of held | Runs | Transitions into state | From trend stage | Pairs with any exposure | Median pair run bars |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for key, label in (("long_stage3", "Long / Stage 3"), ("short_stage6", "Short / Stage 6")):
        row = agg[key]
        lines.append(
            f"| {label} | {row['held_bars']} | {row['consolidation_stage_bars']} | {pct(row['consolidation_share_of_held'])} | "
            f"{row['consolidation_runs']} | {row['transitions_into_consolidation']} | {row['transitions_from_trend_stage']} | "
            f"{row['pairs_with_any_consolidation_exposure']}/{agg['pair_count']} | {row['median_pair_median_consolidation_run_bars'] if row['median_pair_median_consolidation_run_bars'] is not None else '—'} |"
        )

    lines += ["", "## Per pair", "", "| Pair | Long held | Stage3 bars | Stage3 share | Stage3 runs | Short held | Stage6 bars | Stage6 share | Stage6 runs |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for pair, result in report["pairs"].items():  # type: ignore[index]
        long = result["long"]
        short = result["short"]
        lines.append(
            f"| {pair} | {long['held_bars']} | {long['consolidation_stage_bars']} | {pct(long['consolidation_share_of_held'])} | {long['consolidation_runs']} | "
            f"{short['held_bars']} | {short['consolidation_stage_bars']} | {pct(short['consolidation_share_of_held'])} | {short['consolidation_runs']} |"
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
