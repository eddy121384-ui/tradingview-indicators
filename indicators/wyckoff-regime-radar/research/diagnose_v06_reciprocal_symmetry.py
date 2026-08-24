#!/usr/bin/env python3
"""Issue #61 reciprocal / bull-bear symmetry audit.

This diagnostic uses the frozen Issue #55 FX fixtures and the frozen Issue #57
v0.6 Phase-B price-only classifier. It constructs reciprocal OHLC quotes and
measures where bull/bear mirror symmetry breaks. No PnL is used.
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

HERE = Path(__file__).resolve().parent
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
    ("recent_range_break_up_strength", "recent_range_break_dn_strength"),
    ("recent_range_break_dn_strength", "recent_range_break_up_strength"),
    ("range_cont_up", "range_cont_dn"),
    ("range_cont_dn", "range_cont_up"),
    ("breakout_score", "explicit_breakdown_score"),
    ("explicit_breakdown_score", "breakout_score"),
    ("breakout_gate", "explicit_breakdown_gate"),
    ("explicit_breakdown_gate", "breakout_gate"),
    ("range_cont_up_gate", "range_cont_dn_gate"),
    ("range_cont_dn_gate", "range_cont_up_gate"),
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
    required = ("open", "high", "low", "close")
    for column in required:
        values = pd.to_numeric(frame[column], errors="raise").to_numpy(float)
        if np.any(~np.isfinite(values)) or np.any(values <= 0.0):
            raise ValueError(f"{column}: reciprocal transform requires finite positive prices")
    o = pd.to_numeric(frame["open"], errors="raise").to_numpy(float)
    h = pd.to_numeric(frame["high"], errors="raise").to_numpy(float)
    l = pd.to_numeric(frame["low"], errors="raise").to_numpy(float)
    c = pd.to_numeric(frame["close"], errors="raise").to_numpy(float)
    out["open"] = 1.0 / o
    out["high"] = 1.0 / l
    out["low"] = 1.0 / h
    out["close"] = 1.0 / c
    return out


def model_output(frame: pd.DataFrame) -> tuple[dict[str, Any], Any]:
    namespace = load_phase_b_namespace()
    config_type = namespace["PriceOnlyConfig"]
    compute = namespace["compute_price_only"]
    config = config_type()
    return compute(frame.copy(), config), config


def as_bool(model: dict[str, Any], key: str) -> np.ndarray:
    return pd.to_numeric(model[key], errors="coerce").fillna(0.0).to_numpy(float) > 0.5


def as_float(model: dict[str, Any], key: str) -> np.ndarray:
    return pd.to_numeric(model[key], errors="coerce").to_numpy(float)


def as_int(model: dict[str, Any], key: str) -> np.ndarray:
    return pd.to_numeric(model[key], errors="coerce").fillna(0).to_numpy(int)


def boolean_agreement(left: np.ndarray, right: np.ndarray, warmup: int) -> dict[str, float | int]:
    a = left[warmup:]
    b = right[warmup:]
    matches = a == b
    union = a | b
    intersection = a & b
    return {
        "bars": int(len(a)),
        "agreement": float(np.mean(matches)) if len(a) else 1.0,
        "left_true": int(np.sum(a)),
        "right_true": int(np.sum(b)),
        "both_true": int(np.sum(intersection)),
        "either_true": int(np.sum(union)),
        "jaccard": float(np.sum(intersection) / np.sum(union)) if np.any(union) else 1.0,
        "mismatch_bars": int(np.sum(~matches)),
    }


def numeric_agreement(left: np.ndarray, right: np.ndarray, warmup: int) -> dict[str, float | int | None]:
    a = left[warmup:]
    b = right[warmup:]
    valid = np.isfinite(a) & np.isfinite(b)
    if not np.any(valid):
        return {"valid_bars": 0, "mae": None, "median_abs_error": None, "max_abs_error": None, "within_1e-9": None, "within_1e-6": None}
    diff = np.abs(a[valid] - b[valid])
    return {
        "valid_bars": int(np.sum(valid)),
        "mae": float(np.mean(diff)),
        "median_abs_error": float(np.median(diff)),
        "max_abs_error": float(np.max(diff)),
        "within_1e-9": float(np.mean(diff <= 1e-9)),
        "within_1e-6": float(np.mean(diff <= 1e-6)),
    }


def mirrored_stage_agreement(original: np.ndarray, reciprocal: np.ndarray, warmup: int) -> dict[str, Any]:
    a = original[warmup:]
    b = reciprocal[warmup:]
    expected = STAGE_MIRROR[np.clip(a, 0, 6)]
    matches = expected == b
    matrix: dict[str, dict[str, int]] = {}
    for orig_stage in range(7):
        indices = np.flatnonzero(a == orig_stage)
        counts = {str(stage): int(np.sum(b[indices] == stage)) for stage in range(7)} if len(indices) else {str(stage): 0 for stage in range(7)}
        matrix[str(orig_stage)] = counts
    return {
        "bars": int(len(a)),
        "agreement": float(np.mean(matches)) if len(a) else 1.0,
        "mismatch_bars": int(np.sum(~matches)),
        "confusion_original_to_reciprocal": matrix,
    }


def lifecycle_v2(model: dict[str, Any], config: Any, warmup: int) -> dict[str, np.ndarray]:
    formal = as_int(model, "formal_id")
    up = as_bool(model, "range_break_up")
    down = as_bool(model, "range_break_dn")
    high_break = as_float(model, "range_high_break")
    low_break = as_float(model, "range_low_break")
    close = as_float(model, "close") if "close" in model else None
    if close is None:
        raise KeyError("model output does not expose close")

    n = len(formal)
    pos_series = np.zeros(n, dtype=int)
    entry_long = np.zeros(n, dtype=bool)
    entry_short = np.zeros(n, dtype=bool)
    early_fail_long = np.zeros(n, dtype=bool)
    early_fail_short = np.zeros(n, dtype=bool)
    opposite_exit_long = np.zeros(n, dtype=bool)
    opposite_exit_short = np.zeros(n, dtype=bool)

    pos = 0
    armed_dir = 0
    armed_at = -1
    armed_level = np.nan
    entry_level = np.nan
    entry_age = -1
    confirm_bars = int(config.confirm_bars)

    for i in range(n):
        if i < warmup:
            pos_series[i] = 0
            continue
        stage = int(formal[i])
        before = pos
        closed_this_bar = False

        if pos == 1 and stage in (4, 5, 6):
            pos = 0
            opposite_exit_long[i] = True
            closed_this_bar = True
            entry_level = np.nan
            entry_age = -1
            armed_dir = 0
            armed_at = -1
            armed_level = np.nan
        elif pos == -1 and stage in (1, 2, 3):
            pos = 0
            opposite_exit_short[i] = True
            closed_this_bar = True
            entry_level = np.nan
            entry_age = -1
            armed_dir = 0
            armed_at = -1
            armed_level = np.nan

        was_holding = before == pos and pos != 0
        if was_holding and np.isfinite(entry_level):
            entry_age += 1
            if entry_age <= confirm_bars:
                invalidated = (pos == 1 and close[i] <= entry_level) or (pos == -1 and close[i] >= entry_level)
                if invalidated:
                    if pos == 1:
                        early_fail_long[i] = True
                    else:
                        early_fail_short[i] = True
                    pos = 0
                    closed_this_bar = True
                    entry_level = np.nan
                    entry_age = -1
                    armed_dir = 0
                    armed_at = -1
                    armed_level = np.nan
            else:
                entry_level = np.nan
                entry_age = -1

        if pos == 0 and not closed_this_bar and armed_dir != 0:
            age = i - armed_at
            target = 2 if armed_dir == 1 else 5
            precursor = 1 if armed_dir == 1 else 4
            if age <= confirm_bars and stage == target:
                pos = armed_dir
                entry_level = armed_level
                entry_age = 0
                if pos == 1:
                    entry_long[i] = True
                else:
                    entry_short[i] = True
                armed_dir = 0
                armed_at = -1
                armed_level = np.nan
            elif age > confirm_bars or stage not in (precursor, target):
                armed_dir = 0
                armed_at = -1
                armed_level = np.nan

        if pos == 0 and not closed_this_bar and armed_dir == 0:
            prev_stage = int(formal[i - 1]) if i > 0 else 0
            direct_long = bool(up[i]) and stage == 2 and prev_stage == 1
            direct_short = bool(down[i]) and stage == 5 and prev_stage == 4
            if direct_long:
                pos = 1
                entry_level = high_break[i]
                entry_age = 0
                entry_long[i] = True
            elif direct_short:
                pos = -1
                entry_level = low_break[i]
                entry_age = 0
                entry_short[i] = True
            elif bool(up[i]) and stage == 1:
                armed_dir = 1
                armed_at = i
                armed_level = high_break[i]
            elif bool(down[i]) and stage == 4:
                armed_dir = -1
                armed_at = i
                armed_level = low_break[i]

        pos_series[i] = pos

    return {
        "position": pos_series,
        "entry_long": entry_long,
        "entry_short": entry_short,
        "early_fail_long": early_fail_long,
        "early_fail_short": early_fail_short,
        "opposite_exit_long": opposite_exit_long,
        "opposite_exit_short": opposite_exit_short,
    }


def analyze_pair(frame: pd.DataFrame) -> dict[str, Any]:
    original, config = model_output(frame)
    reciprocal, reciprocal_config = model_output(reciprocal_ohlc(frame))
    warmup = int(config.rank_len - 1)
    if int(reciprocal_config.rank_len - 1) != warmup:
        raise RuntimeError("reciprocal config warm-up mismatch")

    formal = mirrored_stage_agreement(as_int(original, "formal_id"), as_int(reciprocal, "formal_id"), warmup)
    candidate_display = mirrored_stage_agreement(as_int(original, "candidate_display_id"), as_int(reciprocal, "candidate_display_id"), warmup)

    bool_rows: dict[str, Any] = {}
    for left_key, right_key in BOOL_PAIRS:
        if left_key in original and right_key in reciprocal:
            bool_rows[f"{left_key}__to_reciprocal__{right_key}"] = boolean_agreement(as_bool(original, left_key), as_bool(reciprocal, right_key), warmup)

    numeric_rows: dict[str, Any] = {}
    for left_key, right_key in NUMERIC_PAIRS:
        if left_key in original and right_key in reciprocal:
            numeric_rows[f"{left_key}__to_reciprocal__{right_key}"] = numeric_agreement(as_float(original, left_key), as_float(reciprocal, right_key), warmup)

    lifecycle_original = lifecycle_v2(original, config, warmup)
    lifecycle_reciprocal = lifecycle_v2(reciprocal, reciprocal_config, warmup)
    position = lifecycle_original["position"][warmup:]
    reciprocal_position = lifecycle_reciprocal["position"][warmup:]
    pos_matches = reciprocal_position == -position
    lifecycle: dict[str, Any] = {
        "position_mirror_agreement": float(np.mean(pos_matches)) if len(pos_matches) else 1.0,
        "position_mismatch_bars": int(np.sum(~pos_matches)),
    }
    pulse_pairs = (
        ("entry_long", "entry_short"),
        ("entry_short", "entry_long"),
        ("early_fail_long", "early_fail_short"),
        ("early_fail_short", "early_fail_long"),
        ("opposite_exit_long", "opposite_exit_short"),
        ("opposite_exit_short", "opposite_exit_long"),
    )
    for left_key, right_key in pulse_pairs:
        lifecycle[f"{left_key}__to_reciprocal__{right_key}"] = boolean_agreement(lifecycle_original[left_key], lifecycle_reciprocal[right_key], warmup)

    return {
        "rows": int(len(frame)),
        "start_date": str(pd.Timestamp(frame["date"].iloc[0]).date()),
        "end_date": str(pd.Timestamp(frame["date"].iloc[-1]).date()),
        "warmup_bars": warmup,
        "formal_stage_mirror": formal,
        "candidate_display_stage_mirror": candidate_display,
        "boolean_event_mirrors": bool_rows,
        "numeric_score_mirrors": numeric_rows,
        "lifecycle_mirror": lifecycle,
    }


def aggregate_pair_metric(pairs: dict[str, Any], path: tuple[str, ...], key: str) -> float:
    values: list[float] = []
    for pair in pairs.values():
        node: Any = pair
        for element in path:
            node = node[element]
        values.append(float(node[key]))
    return float(np.mean(values)) if values else float("nan")


def build_report() -> dict[str, Any]:
    pair_results = {pair: analyze_pair(frame) for pair, frame in load_frozen_pairs().items()}
    raw_up_key = "range_break_up__to_reciprocal__range_break_dn"
    raw_dn_key = "range_break_dn__to_reciprocal__range_break_up"
    ma_up_key = "ma_cross_up__to_reciprocal__ma_cross_dn"
    ma_dn_key = "ma_cross_dn__to_reciprocal__ma_cross_up"
    aggregate = {
        "pair_count": len(pair_results),
        "mean_formal_stage_mirror_agreement": aggregate_pair_metric(pair_results, ("formal_stage_mirror",), "agreement"),
        "mean_candidate_display_mirror_agreement": aggregate_pair_metric(pair_results, ("candidate_display_stage_mirror",), "agreement"),
        "mean_raw_range_break_up_to_down_agreement": aggregate_pair_metric(pair_results, ("boolean_event_mirrors", raw_up_key), "agreement"),
        "mean_raw_range_break_down_to_up_agreement": aggregate_pair_metric(pair_results, ("boolean_event_mirrors", raw_dn_key), "agreement"),
        "mean_ma_cross_up_to_down_agreement": aggregate_pair_metric(pair_results, ("boolean_event_mirrors", ma_up_key), "agreement"),
        "mean_ma_cross_down_to_up_agreement": aggregate_pair_metric(pair_results, ("boolean_event_mirrors", ma_dn_key), "agreement"),
        "mean_lifecycle_position_mirror_agreement": float(np.mean([pair["lifecycle_mirror"]["position_mirror_agreement"] for pair in pair_results.values()])),
    }
    return {
        "schema_version": 1,
        "issue": 61,
        "status": "RECIPROCAL_SYMMETRY_AUDIT_REUSED_DATA_NO_PNL",
        "engine": "Issue #57 frozen v0.6 Phase-B price-only core + Issue #61 human-review lifecycle v2 semantics",
        "reciprocal_transform": {"open": "1/open", "high": "1/low", "low": "1/high", "close": "1/close"},
        "known_source_level_asymmetries": [
            "breakout range evidence scale: upside 0.70 vs downside 0.85",
            "recent range gate scale: upside 0.85 vs downside 0.90",
            "downside MA breakdown evidence has panic_heat_dn/structure_weak qualifiers unlike the upside MA path",
        ],
        "pairs": pair_results,
        "aggregate": aggregate,
        "boundary": "Diagnostic only. Reused frozen FX fixtures. No PnL, no repair, no threshold tuning.",
    }


def pct(value: float) -> str:
    return f"{100.0 * value:.2f}%"


def render_markdown(report: dict[str, Any]) -> str:
    agg = report["aggregate"]
    lines = [
        "# Issue #61 — v0.6 reciprocal / bull-bear symmetry audit",
        "",
        "**Diagnostic only; reused data; no PnL.**",
        "",
        "## Aggregate mirror agreement",
        "",
        "| Layer | Mean bar/event agreement |",
        "|---|---:|",
        f"| Raw range break: up → reciprocal down | {pct(agg['mean_raw_range_break_up_to_down_agreement'])} |",
        f"| Raw range break: down → reciprocal up | {pct(agg['mean_raw_range_break_down_to_up_agreement'])} |",
        f"| MA cross: up → reciprocal down | {pct(agg['mean_ma_cross_up_to_down_agreement'])} |",
        f"| MA cross: down → reciprocal up | {pct(agg['mean_ma_cross_down_to_up_agreement'])} |",
        f"| Candidate-display stage mirror | {pct(agg['mean_candidate_display_mirror_agreement'])} |",
        f"| Formal-stage mirror | {pct(agg['mean_formal_stage_mirror_agreement'])} |",
        f"| Human-review lifecycle position mirror | {pct(agg['mean_lifecycle_position_mirror_agreement'])} |",
        "",
        "## Known source-level asymmetries (not repaired here)",
        "",
    ]
    for item in report["known_source_level_asymmetries"]:
        lines.append(f"- {item}")
    lines += ["", "## Per pair", "", "| Pair | Formal mirror | Candidate mirror | Range up→down | Range down→up | MA up→down | MA down→up | Lifecycle position mirror |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    raw_up_key = "range_break_up__to_reciprocal__range_break_dn"
    raw_dn_key = "range_break_dn__to_reciprocal__range_break_up"
    ma_up_key = "ma_cross_up__to_reciprocal__ma_cross_dn"
    ma_dn_key = "ma_cross_dn__to_reciprocal__ma_cross_up"
    for pair, row in report["pairs"].items():
        b = row["boolean_event_mirrors"]
        lines.append(
            f"| {pair} | {pct(row['formal_stage_mirror']['agreement'])} | {pct(row['candidate_display_stage_mirror']['agreement'])} | "
            f"{pct(b[raw_up_key]['agreement'])} | {pct(b[raw_dn_key]['agreement'])} | {pct(b[ma_up_key]['agreement'])} | {pct(b[ma_dn_key]['agreement'])} | "
            f"{pct(row['lifecycle_mirror']['position_mirror_agreement'])} |"
        )
    lines += [
        "",
        "## Interpretation rule",
        "",
        "- If raw range breaks mirror closely but later layers do not, the asymmetry is introduced by price representation and/or classifier logic rather than the market path itself.",
        "- This audit does not decide how to repair any asymmetry and does not use performance to select a repair.",
    ]
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit v0.6 reciprocal bull/bear symmetry")
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_report()
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.markdown.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["aggregate"], indent=2))


if __name__ == "__main__":
    main()
