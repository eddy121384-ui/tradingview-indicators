#!/usr/bin/env python3
"""Issue #61 reciprocal / bull-bear symmetry audit v2.

Runs the exact frozen v0.6 Phase-B classifier on each frozen FX fixture and on
its reciprocal OHLC quote. Reports structural-break, representation, score,
stage and current human-review lifecycle mirror agreement. No PnL is used.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from diagnose_stage_lifecycle_break_timing import load_frozen_pairs
from generate_v06_phase_b_core import load_phase_b_namespace

STAGE_MIRROR = np.array([0, 4, 5, 6, 1, 2, 3], dtype=int)
BOOL_PAIRS = (
    ("range_break_up", "range_break_dn"),
    ("range_break_dn", "range_break_up"),
    ("ma_cross_up", "ma_cross_dn"),
    ("ma_cross_dn", "ma_cross_up"),
    ("recent_break_up", "recent_break_dn"),
    ("recent_break_dn", "recent_break_up"),
    ("breakout_mode_up", "breakdown_mode_dn"),
    ("breakdown_mode_dn", "breakout_mode_up"),
)
NUMERIC_PAIRS = (
    ("no_break_low_score", "no_break_high_score"),
    ("no_break_high_score", "no_break_low_score"),
    ("above_prev_range_score", "below_prev_range_score"),
    ("below_prev_range_score", "above_prev_range_score"),
    ("sustained_above_score", "sustained_below_score"),
    ("sustained_below_score", "sustained_above_score"),
    ("range_break_up_strength", "range_break_dn_strength"),
    ("range_break_dn_strength", "range_break_up_strength"),
    ("range_cont_up", "range_cont_dn"),
    ("range_cont_dn", "range_cont_up"),
    ("breakout_score", "explicit_breakdown_score"),
    ("explicit_breakdown_score", "breakout_score"),
    ("breakout_gate", "explicit_breakdown_gate"),
    ("explicit_breakdown_gate", "breakout_gate"),
    ("markup_continuation_score", "markdown_continuation_score"),
    ("markdown_continuation_score", "markup_continuation_score"),
    ("breakout_markup_gate", "breakdown_markdown_gate"),
    ("breakdown_markdown_gate", "breakout_markup_gate"),
    ("markup_cont_gate", "markdown_cont_gate"),
    ("markdown_cont_gate", "markup_cont_gate"),
    ("markup_gate", "markdown_gate"),
    ("markdown_gate", "markup_gate"),
)


def reciprocal_ohlc(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    for column in ("open", "high", "low", "close"):
        values = pd.to_numeric(frame[column], errors="raise").to_numpy(float)
        if np.any(~np.isfinite(values)) or np.any(values <= 0.0):
            raise ValueError(f"{column}: reciprocal transform requires finite positive prices")
    o = frame["open"].to_numpy(float)
    h = frame["high"].to_numpy(float)
    l = frame["low"].to_numpy(float)
    c = frame["close"].to_numpy(float)
    out["open"] = 1.0 / o
    out["high"] = 1.0 / l
    out["low"] = 1.0 / h
    out["close"] = 1.0 / c
    return out


def compute(frame: pd.DataFrame) -> tuple[pd.DataFrame, Any]:
    ns = load_phase_b_namespace()
    config = ns["PriceOnlyConfig"]()
    return ns["compute_price_only"](frame.copy(), config), config


def arr_float(model: pd.DataFrame, key: str) -> np.ndarray:
    return pd.to_numeric(model[key], errors="coerce").to_numpy(float)


def arr_bool(model: pd.DataFrame, key: str) -> np.ndarray:
    return np.nan_to_num(arr_float(model, key), nan=0.0) > 0.5


def arr_int(model: pd.DataFrame, key: str) -> np.ndarray:
    return np.nan_to_num(arr_float(model, key), nan=0.0).astype(int)


def boolean_metrics(left: np.ndarray, right: np.ndarray, warmup: int) -> dict[str, float | int]:
    a = left[warmup:]
    b = right[warmup:]
    union = a | b
    both = a & b
    return {
        "bars": int(len(a)),
        "bar_agreement": float(np.mean(a == b)) if len(a) else 1.0,
        "left_true": int(np.sum(a)),
        "right_true": int(np.sum(b)),
        "both_true": int(np.sum(both)),
        "either_true": int(np.sum(union)),
        "event_jaccard": float(np.sum(both) / np.sum(union)) if np.any(union) else 1.0,
        "mismatch_bars": int(np.sum(a != b)),
    }


def numeric_metrics(left: np.ndarray, right: np.ndarray, warmup: int) -> dict[str, float | int | None]:
    a = left[warmup:]
    b = right[warmup:]
    valid = np.isfinite(a) & np.isfinite(b)
    if not np.any(valid):
        return {"valid_bars": 0, "mae": None, "median_abs_error": None, "max_abs_error": None, "within_1e6": None}
    diff = np.abs(a[valid] - b[valid])
    return {
        "valid_bars": int(np.sum(valid)),
        "mae": float(np.mean(diff)),
        "median_abs_error": float(np.median(diff)),
        "max_abs_error": float(np.max(diff)),
        "within_1e6": float(np.mean(diff <= 1e-6)),
    }


def stage_metrics(original: np.ndarray, inverse: np.ndarray, warmup: int) -> dict[str, Any]:
    a = original[warmup:]
    b = inverse[warmup:]
    expected = STAGE_MIRROR[np.clip(a, 0, 6)]
    matches = expected == b
    by_stage: dict[str, Any] = {}
    for stage in range(7):
        mask = a == stage
        by_stage[str(stage)] = {
            "bars": int(np.sum(mask)),
            "mirror_agreement": None if not np.any(mask) else float(np.mean(matches[mask])),
        }
    return {
        "bars": int(len(a)),
        "mirror_agreement": float(np.mean(matches)) if len(a) else 1.0,
        "mismatch_bars": int(np.sum(~matches)),
        "by_original_stage": by_stage,
    }


def lifecycle_v2(model: pd.DataFrame, close: np.ndarray, config: Any, warmup: int) -> dict[str, np.ndarray]:
    formal = arr_int(model, "formal_id")
    up = arr_bool(model, "range_break_up")
    down = arr_bool(model, "range_break_dn")
    high_break = arr_float(model, "range_high_break")
    low_break = arr_float(model, "range_low_break")
    n = len(formal)
    out = {
        "position": np.zeros(n, dtype=int),
        "entry_long": np.zeros(n, dtype=bool),
        "entry_short": np.zeros(n, dtype=bool),
        "early_fail_long": np.zeros(n, dtype=bool),
        "early_fail_short": np.zeros(n, dtype=bool),
        "opposite_exit_long": np.zeros(n, dtype=bool),
        "opposite_exit_short": np.zeros(n, dtype=bool),
    }
    pos = 0
    armed_dir = 0
    armed_at = -1
    armed_level = np.nan
    entry_level = np.nan
    entry_age = -1
    confirm = int(config.confirm_bars)

    for i in range(n):
        if i < warmup:
            continue
        stage = int(formal[i])
        before = pos
        closed = False

        if pos == 1 and stage in (4, 5, 6):
            pos = 0
            out["opposite_exit_long"][i] = True
            closed = True
        elif pos == -1 and stage in (1, 2, 3):
            pos = 0
            out["opposite_exit_short"][i] = True
            closed = True
        if closed:
            entry_level = np.nan
            entry_age = -1
            armed_dir = 0
            armed_at = -1
            armed_level = np.nan

        if before == pos and pos != 0 and np.isfinite(entry_level):
            entry_age += 1
            if entry_age <= confirm:
                invalid = (pos == 1 and close[i] <= entry_level) or (pos == -1 and close[i] >= entry_level)
                if invalid:
                    out["early_fail_long" if pos == 1 else "early_fail_short"][i] = True
                    pos = 0
                    closed = True
                    entry_level = np.nan
                    entry_age = -1
                    armed_dir = 0
                    armed_at = -1
                    armed_level = np.nan
            else:
                entry_level = np.nan
                entry_age = -1

        if pos == 0 and not closed and armed_dir != 0:
            age = i - armed_at
            target = 2 if armed_dir == 1 else 5
            precursor = 1 if armed_dir == 1 else 4
            if age <= confirm and stage == target:
                pos = armed_dir
                entry_level = armed_level
                entry_age = 0
                out["entry_long" if pos == 1 else "entry_short"][i] = True
                armed_dir = 0
                armed_at = -1
                armed_level = np.nan
            elif age > confirm or stage not in (precursor, target):
                armed_dir = 0
                armed_at = -1
                armed_level = np.nan

        if pos == 0 and not closed and armed_dir == 0:
            prev_stage = int(formal[i - 1]) if i > 0 else 0
            if bool(up[i]) and stage == 2 and prev_stage == 1:
                pos = 1
                entry_level = high_break[i]
                entry_age = 0
                out["entry_long"][i] = True
            elif bool(down[i]) and stage == 5 and prev_stage == 4:
                pos = -1
                entry_level = low_break[i]
                entry_age = 0
                out["entry_short"][i] = True
            elif bool(up[i]) and stage == 1:
                armed_dir = 1
                armed_at = i
                armed_level = high_break[i]
            elif bool(down[i]) and stage == 4:
                armed_dir = -1
                armed_at = i
                armed_level = low_break[i]

        out["position"][i] = pos
    return out


def analyze_pair(frame: pd.DataFrame) -> dict[str, Any]:
    inverse_frame = reciprocal_ohlc(frame)
    original, config = compute(frame)
    inverse, inverse_config = compute(inverse_frame)
    warmup = int(config.rank_len - 1)

    events: dict[str, Any] = {}
    for left, right in BOOL_PAIRS:
        events[f"{left}__to_inverse__{right}"] = boolean_metrics(arr_bool(original, left), arr_bool(inverse, right), warmup)

    scores: dict[str, Any] = {}
    for left, right in NUMERIC_PAIRS:
        if left in original.columns and right in inverse.columns:
            scores[f"{left}__to_inverse__{right}"] = numeric_metrics(arr_float(original, left), arr_float(inverse, right), warmup)

    original_life = lifecycle_v2(original, frame["close"].to_numpy(float), config, warmup)
    inverse_life = lifecycle_v2(inverse, inverse_frame["close"].to_numpy(float), inverse_config, warmup)
    p = original_life["position"][warmup:]
    q = inverse_life["position"][warmup:]
    lifecycle: dict[str, Any] = {
        "position_mirror_agreement": float(np.mean(q == -p)) if len(p) else 1.0,
        "position_mismatch_bars": int(np.sum(q != -p)),
    }
    for left, right in (
        ("entry_long", "entry_short"),
        ("entry_short", "entry_long"),
        ("early_fail_long", "early_fail_short"),
        ("early_fail_short", "early_fail_long"),
        ("opposite_exit_long", "opposite_exit_short"),
        ("opposite_exit_short", "opposite_exit_long"),
    ):
        lifecycle[f"{left}__to_inverse__{right}"] = boolean_metrics(original_life[left], inverse_life[right], warmup)

    return {
        "rows": int(len(frame)),
        "start_date": str(pd.Timestamp(frame["date"].iloc[0]).date()),
        "end_date": str(pd.Timestamp(frame["date"].iloc[-1]).date()),
        "warmup_bars": warmup,
        "formal_stage": stage_metrics(arr_int(original, "formal_id"), arr_int(inverse, "formal_id"), warmup),
        "candidate_display_stage": stage_metrics(arr_int(original, "candidate_display_id"), arr_int(inverse, "candidate_display_id"), warmup),
        "event_mirrors": events,
        "score_mirrors": scores,
        "lifecycle": lifecycle,
    }


def mean_path(pairs: dict[str, Any], *keys: str) -> float:
    vals: list[float] = []
    for row in pairs.values():
        node: Any = row
        for key in keys:
            node = node[key]
        vals.append(float(node))
    return float(np.mean(vals))


def build_report() -> dict[str, Any]:
    pairs = {name: analyze_pair(frame) for name, frame in load_frozen_pairs().items()}
    def mean_event(key: str, metric: str) -> float:
        return float(np.mean([row["event_mirrors"][key][metric] for row in pairs.values()]))
    agg = {
        "pair_count": len(pairs),
        "formal_stage_mirror_agreement": mean_path(pairs, "formal_stage", "mirror_agreement"),
        "candidate_display_mirror_agreement": mean_path(pairs, "candidate_display_stage", "mirror_agreement"),
        "lifecycle_position_mirror_agreement": mean_path(pairs, "lifecycle", "position_mirror_agreement"),
        "range_up_to_inverse_down_jaccard": mean_event("range_break_up__to_inverse__range_break_dn", "event_jaccard"),
        "range_down_to_inverse_up_jaccard": mean_event("range_break_dn__to_inverse__range_break_up", "event_jaccard"),
        "ma_up_to_inverse_down_jaccard": mean_event("ma_cross_up__to_inverse__ma_cross_dn", "event_jaccard"),
        "ma_down_to_inverse_up_jaccard": mean_event("ma_cross_dn__to_inverse__ma_cross_up", "event_jaccard"),
        "breakout_mode_up_to_inverse_down_jaccard": mean_event("breakout_mode_up__to_inverse__breakdown_mode_dn", "event_jaccard"),
        "breakdown_mode_down_to_inverse_up_jaccard": mean_event("breakdown_mode_dn__to_inverse__breakout_mode_up", "event_jaccard"),
    }
    return {
        "schema_version": 2,
        "issue": 61,
        "status": "RECIPROCAL_SYMMETRY_AUDIT_REUSED_DATA_NO_PNL",
        "engine": "frozen v0.6 Phase-B price-only core + Issue #61 human-review lifecycle v2",
        "known_source_level_asymmetries": [
            "upside breakout range-evidence scale 0.70 vs downside 0.85",
            "upside recent-range gate scale 0.85 vs downside 0.90",
            "downside MA breakdown evidence has panic_heat_dn/structure_weak qualifiers unlike upside MA path",
            "Stage-2 breakout gate and Stage-5 breakdown gate use non-isomorphic confirmation products",
        ],
        "aggregate": agg,
        "pairs": pairs,
        "boundary": "No PnL. No repair. Reused diagnostic data only.",
    }


def pct(v: float) -> str:
    return f"{100*v:.2f}%"


def render_markdown(report: dict[str, Any]) -> str:
    a = report["aggregate"]
    lines = [
        "# Issue #61 — v0.6 reciprocal / bull-bear symmetry audit",
        "",
        "**No PnL. Reused frozen FX data. Diagnostic only.**",
        "",
        "## Aggregate",
        "",
        "| Layer | Mirror metric |",
        "|---|---:|",
        f"| Raw range break up → inverse down | Jaccard {pct(a['range_up_to_inverse_down_jaccard'])} |",
        f"| Raw range break down → inverse up | Jaccard {pct(a['range_down_to_inverse_up_jaccard'])} |",
        f"| MA cross up → inverse down | Jaccard {pct(a['ma_up_to_inverse_down_jaccard'])} |",
        f"| MA cross down → inverse up | Jaccard {pct(a['ma_down_to_inverse_up_jaccard'])} |",
        f"| Breakout mode up → inverse breakdown mode | Jaccard {pct(a['breakout_mode_up_to_inverse_down_jaccard'])} |",
        f"| Breakdown mode down → inverse breakout mode | Jaccard {pct(a['breakdown_mode_down_to_inverse_up_jaccard'])} |",
        f"| Candidate-display stage | bar mirror {pct(a['candidate_display_mirror_agreement'])} |",
        f"| Formal stage | bar mirror {pct(a['formal_stage_mirror_agreement'])} |",
        f"| Human-review lifecycle position | bar mirror {pct(a['lifecycle_position_mirror_agreement'])} |",
        "",
        "## Known source-level asymmetries (not repaired in this audit)",
        "",
    ]
    lines += [f"- {item}" for item in report["known_source_level_asymmetries"]]
    lines += ["", "## Per pair", "", "| Pair | Range U→D Jaccard | Range D→U Jaccard | MA U→D Jaccard | MA D→U Jaccard | Candidate mirror | Formal mirror | Lifecycle mirror |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for name, row in report["pairs"].items():
        e = row["event_mirrors"]
        lines.append(
            f"| {name} | {pct(e['range_break_up__to_inverse__range_break_dn']['event_jaccard'])} | "
            f"{pct(e['range_break_dn__to_inverse__range_break_up']['event_jaccard'])} | "
            f"{pct(e['ma_cross_up__to_inverse__ma_cross_dn']['event_jaccard'])} | "
            f"{pct(e['ma_cross_dn__to_inverse__ma_cross_up']['event_jaccard'])} | "
            f"{pct(row['candidate_display_stage']['mirror_agreement'])} | {pct(row['formal_stage']['mirror_agreement'])} | "
            f"{pct(row['lifecycle']['position_mirror_agreement'])} |"
        )
    lines += [
        "",
        "## Reading the result",
        "",
        "If raw range-break Jaccard is near 100% but MA/score/state/lifecycle symmetry degrades later, the asymmetry is introduced by representation and classifier design rather than by changing the historical market path.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()
    report = build_report()
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.markdown.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["aggregate"], indent=2))


if __name__ == "__main__":
    main()
