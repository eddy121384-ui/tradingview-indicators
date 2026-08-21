#!/usr/bin/env python3
"""Issue #61 pre-PnL audit of existing rangeScore as a trend-consolidation substate.

Literal Formal/Candidate Stage 3/6 are structurally absent. This diagnostic does
not invent a new indicator or tune a threshold. It reuses the model's existing
range-gate boundaries: rangeScore 35 starts the existing gate, 70 fills it.
Counts, durations and subsequent fresh-break timing only; no price returns.
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

RANGE_GATE_START = 35.0
RANGE_GATE_FULL = 70.0
BREAK_CHECKPOINTS = (0, 1, 3, 5, 20)


def extract_runs(mask: np.ndarray) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    start: int | None = None
    for i, value in enumerate(mask.astype(bool)):
        if value and start is None:
            start = i
        elif not value and start is not None:
            runs.append((start, i - 1))
            start = None
    if start is not None:
        runs.append((start, len(mask) - 1))
    return runs


def fresh_break_lag_after_run(
    run_end: int,
    position: np.ndarray,
    fresh_break: np.ndarray,
    direction: int,
    horizon: int = 20,
) -> int | None:
    end = min(len(position) - 1, run_end + horizon)
    for i in range(run_end, end + 1):
        if int(position[i]) != direction:
            return None
        if bool(fresh_break[i]):
            return i - run_end
    return None


def summarize_level(
    position: np.ndarray,
    formal: np.ndarray,
    range_score: np.ndarray,
    fresh_break: np.ndarray,
    direction: int,
    matching_formal_stage: int,
    threshold: float,
) -> dict[str, object]:
    held = position == direction
    active = held & np.isfinite(range_score) & (range_score >= threshold)
    active_inside_matching_formal = active & (formal == matching_formal_stage)
    runs = extract_runs(active)
    lags = [fresh_break_lag_after_run(end, position, fresh_break, direction) for _, end in runs]
    finite_lags = [lag for lag in lags if lag is not None]
    durations = [end - start + 1 for start, end in runs]
    return {
        "threshold": threshold,
        "held_bars": int(np.sum(held)),
        "range_active_bars": int(np.sum(active)),
        "range_active_share_of_held": None if not np.any(held) else float(np.sum(active) / np.sum(held)),
        "range_active_inside_matching_formal_bars": int(np.sum(active_inside_matching_formal)),
        "runs": int(len(runs)),
        "median_run_bars": None if not durations else float(np.median(durations)),
        "max_run_bars": None if not durations else int(max(durations)),
        "runs_with_same_direction_fresh_break_by": {
            str(checkpoint): int(sum(lag is not None and lag <= checkpoint for lag in lags))
            for checkpoint in BREAK_CHECKPOINTS
        },
        "runs_without_same_direction_break_within_20": int(sum(lag is None for lag in lags)),
        "median_fresh_break_lag_if_matched": None if not finite_lags else float(np.median(finite_lags)),
    }


def analyze_pair(frame: pd.DataFrame) -> dict[str, object]:
    ns = load_phase_b_namespace()
    config_type = ns["PriceOnlyConfig"]
    compute_price_only = ns["compute_price_only"]
    config = config_type()
    model = compute_price_only(frame.copy(), config)

    formal = pd.to_numeric(model["formal_id"], errors="coerce").fillna(0).to_numpy(int)
    range_score = pd.to_numeric(model["range_score"], errors="coerce").to_numpy(float)
    fresh_up = pd.to_numeric(model["range_break_up"], errors="coerce").fillna(0).to_numpy(float) > 0.5
    fresh_down = pd.to_numeric(model["range_break_dn"], errors="coerce").fillna(0).to_numpy(float) > 0.5
    warmup = int(config.rank_len - 1)
    signal, _ = stage_lifecycle_signal(
        formal, fresh_up, fresh_down, warmup=warmup, confirm_bars=int(config.confirm_bars)
    )

    return {
        "rows": int(len(frame)),
        "warmup_bars": warmup,
        "long": {
            "range_gate_start": summarize_level(signal, formal, range_score, fresh_up, 1, 2, RANGE_GATE_START),
            "range_gate_full": summarize_level(signal, formal, range_score, fresh_up, 1, 2, RANGE_GATE_FULL),
        },
        "short": {
            "range_gate_start": summarize_level(signal, formal, range_score, fresh_down, -1, 5, RANGE_GATE_START),
            "range_gate_full": summarize_level(signal, formal, range_score, fresh_down, -1, 5, RANGE_GATE_FULL),
        },
    }


def aggregate_level(pairs: dict[str, dict[str, object]], side: str, level: str) -> dict[str, object]:
    rows = [pair[side][level] for pair in pairs.values()]  # type: ignore[index]
    held = int(sum(int(row["held_bars"]) for row in rows))
    active = int(sum(int(row["range_active_bars"]) for row in rows))
    durations = [float(row["median_run_bars"]) for row in rows if row["median_run_bars"] is not None]
    return {
        "threshold": float(rows[0]["threshold"]) if rows else None,
        "held_bars": held,
        "range_active_bars": active,
        "range_active_share_of_held": None if held == 0 else active / held,
        "range_active_inside_matching_formal_bars": int(sum(int(row["range_active_inside_matching_formal_bars"]) for row in rows)),
        "runs": int(sum(int(row["runs"]) for row in rows)),
        "pairs_with_any_runs": int(sum(int(row["runs"]) > 0 for row in rows)),
        "median_pair_median_run_bars": None if not durations else float(np.median(durations)),
        "runs_with_same_direction_fresh_break_by": {
            str(checkpoint): int(sum(int(row["runs_with_same_direction_fresh_break_by"][str(checkpoint)]) for row in rows))  # type: ignore[index]
            for checkpoint in BREAK_CHECKPOINTS
        },
        "runs_without_same_direction_break_within_20": int(sum(int(row["runs_without_same_direction_break_within_20"]) for row in rows)),
    }


def build_report() -> dict[str, object]:
    pairs = {pair: analyze_pair(frame) for pair, frame in load_frozen_pairs().items()}
    aggregate: dict[str, object] = {"pair_count": len(pairs)}
    for side in ("long", "short"):
        aggregate[side] = {
            level: aggregate_level(pairs, side, level)
            for level in ("range_gate_start", "range_gate_full")
        }
    return {
        "schema_version": 1,
        "issue": 61,
        "status": "PRE_PNL_RANGE_SUBSTATE_AUDIT",
        "existing_thresholds": {"range_gate_start": RANGE_GATE_START, "range_gate_full": RANGE_GATE_FULL},
        "break_checkpoints": list(BREAK_CHECKPOINTS),
        "pairs": pairs,
        "aggregate": aggregate,
        "boundary": "Existing rangeScore boundaries only; counts/durations/fresh-break timing only. No PnL or threshold selection from returns.",
    }


def pct(value: float | None) -> str:
    return "—" if value is None else f"{100.0 * value:.2f}%"


def render_markdown(report: dict[str, object]) -> str:
    agg = report["aggregate"]  # type: ignore[index]
    lines = [
        "# Issue #61 — Existing rangeScore as Trend Consolidation substate",
        "",
        "**Pre-PnL structural audit only.**",
        "",
        "The existing v0.6 range gate starts at `rangeScore = 35` and is fully active at `70`. Both are reported as inherited model semantics; neither is selected from returns.",
        "",
        "## Aggregate",
        "",
        "| Side | Existing level | Held bars | Active bars | Share held | Inside matching Formal trend | Runs | Pairs | Break same/end bar | by +3 | by +5 | by +20 | No break +20 |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for side, label in (("long", "Long"), ("short", "Short")):
        for level in ("range_gate_start", "range_gate_full"):
            row = agg[side][level]
            b = row["runs_with_same_direction_fresh_break_by"]
            lines.append(
                f"| {label} | {level} (≥{row['threshold']:.0f}) | {row['held_bars']} | {row['range_active_bars']} | {pct(row['range_active_share_of_held'])} | "
                f"{row['range_active_inside_matching_formal_bars']} | {row['runs']} | {row['pairs_with_any_runs']}/{agg['pair_count']} | "
                f"{b['0']} | {b['3']} | {b['5']} | {b['20']} | {row['runs_without_same_direction_break_within_20']} |"
            )

    lines += ["", "## Per pair — range gate start (≥35)", "", "| Pair | Long active share | Long runs | Long break +20 | Short active share | Short runs | Short break +20 |", "|---|---:|---:|---:|---:|---:|---:|"]
    for pair, result in report["pairs"].items():  # type: ignore[index]
        long = result["long"]["range_gate_start"]
        short = result["short"]["range_gate_start"]
        lines.append(
            f"| {pair} | {pct(long['range_active_share_of_held'])} | {long['runs']} | {long['runs_with_same_direction_fresh_break_by']['20']} | "
            f"{pct(short['range_active_share_of_held'])} | {short['runs']} | {short['runs_with_same_direction_fresh_break_by']['20']} |"
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
