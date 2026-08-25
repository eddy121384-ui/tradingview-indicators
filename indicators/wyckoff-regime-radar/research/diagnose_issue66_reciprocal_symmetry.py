#!/usr/bin/env python3
"""Issue #66 Phase-A reciprocal symmetry decomposition.

This diagnostic reproduces the frozen v0.6 Phase-B price-only classifier on the
already-burned four-FX fixtures and on their reciprocal OHLC quotations. It is
strictly an engineering/semantic audit: no PnL, return, Sharpe, drawdown, trade
count, win rate, or strategy statistic is computed.

The required stage mirror is 0<->0, 1<->4, 2<->5, 3<->6.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from generate_v06_phase_b_core import load_phase_b_namespace

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "data" / "issue-55-static-fx-canonical-manifest.json"
STAGE_MIRROR = np.array([0, 4, 5, 6, 1, 2, 3], dtype=int)

EVENT_PAIRS: dict[str, tuple[tuple[str, str], ...]] = {
    "raw_price_range": (
        ("range_break_up", "range_break_dn"),
        ("range_break_dn", "range_break_up"),
    ),
    "ma_representation": (
        ("ma_cross_up", "ma_cross_dn"),
        ("ma_cross_dn", "ma_cross_up"),
    ),
    "directional_modes": (
        ("breakout_mode_up", "breakdown_mode_dn"),
        ("breakdown_mode_dn", "breakout_mode_up"),
    ),
}

NUMERIC_PAIRS: dict[str, tuple[tuple[str, str], ...]] = {
    "representation": (
        ("heat_up", "panic_heat_dn"),
        ("panic_heat_dn", "heat_up"),
        ("maturity_up", "maturity_dn"),
        ("maturity_dn", "maturity_up"),
        ("end_risk_up", "end_risk_dn"),
        ("end_risk_dn", "end_risk_up"),
    ),
    "boundary_primitives": (
        ("no_break_low_score", "no_break_high_score"),
        ("no_break_high_score", "no_break_low_score"),
        ("above_prev_range_score", "below_prev_range_score"),
        ("below_prev_range_score", "above_prev_range_score"),
        ("sustained_above_score", "sustained_below_score"),
        ("sustained_below_score", "sustained_above_score"),
        ("range_break_up_strength", "range_break_dn_strength"),
        ("range_break_dn_strength", "range_break_up_strength"),
    ),
    "directional_evidence": (
        ("downside_exhaustion", "upside_exhaustion"),
        ("upside_exhaustion", "downside_exhaustion"),
        ("support_holding", "resistance_holding"),
        ("resistance_holding", "support_holding"),
        ("range_cont_up", "range_cont_dn"),
        ("range_cont_dn", "range_cont_up"),
        ("breakout_score", "explicit_breakdown_score"),
        ("explicit_breakdown_score", "breakout_score"),
        ("breakout_gate", "explicit_breakdown_gate"),
        ("explicit_breakdown_gate", "breakout_gate"),
        ("markup_extension_score", "markdown_extension_score"),
        ("markdown_extension_score", "markup_extension_score"),
        ("markup_continuation_score", "markdown_continuation_score"),
        ("markdown_continuation_score", "markup_continuation_score"),
        ("breakout_markup_gate", "breakdown_markdown_gate"),
        ("breakdown_markdown_gate", "breakout_markup_gate"),
        ("markup_cont_gate", "markdown_cont_gate"),
        ("markdown_cont_gate", "markup_cont_gate"),
    ),
    "stage_raw": (
        ("acc_raw", "dist_raw"),
        ("dist_raw", "acc_raw"),
        ("markup_raw", "markdown_raw"),
        ("markdown_raw", "markup_raw"),
        ("reacc_raw", "redist_raw"),
        ("redist_raw", "reacc_raw"),
    ),
    "stage_gates": (
        ("acc_gate", "dist_gate"),
        ("dist_gate", "acc_gate"),
        ("markup_gate", "markdown_gate"),
        ("markdown_gate", "markup_gate"),
        ("reacc_gate", "redist_gate"),
        ("redist_gate", "reacc_gate"),
    ),
    "effective_weights": (
        ("acc_eff", "dist_eff"),
        ("dist_eff", "acc_eff"),
        ("markup_eff", "markdown_eff"),
        ("markdown_eff", "markup_eff"),
        ("reacc_eff", "redist_eff"),
        ("redist_eff", "reacc_eff"),
    ),
    "probability_weights": (
        ("prob_acc", "prob_dist"),
        ("prob_dist", "prob_acc"),
        ("prob_markup", "prob_markdown"),
        ("prob_markdown", "prob_markup"),
        ("prob_reacc", "prob_redist"),
        ("prob_redist", "prob_reacc"),
    ),
}

SELF_NUMERIC = ("evidence_strength", "top_value", "top_gap")
SELF_BOOLEAN = ("candidate_conflict", "chaos", "coexist", "weak_candidate", "strong_candidate", "fast_switch")

STAGE_VECTOR_LEFT = ("acc_raw", "markup_raw", "reacc_raw", "dist_raw", "markdown_raw", "redist_raw")
STAGE_VECTOR_GATE = ("acc_gate", "markup_gate", "reacc_gate", "dist_gate", "markdown_gate", "redist_gate")
STAGE_VECTOR_EFFECTIVE = ("acc_eff", "markup_eff", "reacc_eff", "dist_eff", "markdown_eff", "redist_eff")
STAGE_VECTOR_PROB = ("prob_acc", "prob_markup", "prob_reacc", "prob_dist", "prob_markdown", "prob_redist")
STAGE_VECTOR_MIRRORED = (3, 4, 5, 0, 1, 2)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_frozen_pairs() -> dict[str, pd.DataFrame]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    pairs: dict[str, pd.DataFrame] = {}
    for pair, meta in manifest["pairs"].items():
        path = MANIFEST.parent / meta["frozen_file"]
        actual = sha256_file(path)
        expected = str(meta["frozen_sha256"])
        if actual != expected:
            raise RuntimeError(f"{pair}: frozen SHA mismatch: {actual} != {expected}")
        frame = pd.read_csv(path)
        frame["date"] = pd.to_datetime(frame["date"], errors="raise")
        pairs[pair] = frame.reset_index(drop=True)
    return pairs


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


def vector_mirror_metrics(model: pd.DataFrame, inverse: pd.DataFrame, columns: tuple[str, ...], warmup: int) -> dict[str, float | int | None]:
    left = np.column_stack([arr_float(model, column) for column in columns])[warmup:]
    right_raw = np.column_stack([arr_float(inverse, column) for column in columns])[warmup:]
    right = right_raw[:, STAGE_VECTOR_MIRRORED]
    valid = np.isfinite(left) & np.isfinite(right)
    if not np.any(valid):
        return {"valid_values": 0, "mae": None, "median_abs_error": None, "max_abs_error": None, "within_1e6": None}
    diff = np.abs(left[valid] - right[valid])
    return {
        "valid_values": int(np.sum(valid)),
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


def transition_metrics(original: np.ndarray, inverse: np.ndarray, warmup: int) -> dict[str, float | int]:
    start = max(1, warmup)
    a_prev = original[start - 1 : -1]
    a_curr = original[start:]
    b_prev = inverse[start - 1 : -1]
    b_curr = inverse[start:]
    expected_prev = STAGE_MIRROR[np.clip(a_prev, 0, 6)]
    expected_curr = STAGE_MIRROR[np.clip(a_curr, 0, 6)]
    pair_match = (expected_prev == b_prev) & (expected_curr == b_curr)
    a_change = a_curr != a_prev
    b_change = b_curr != b_prev
    event = boolean_metrics(a_change, b_change, warmup=0)
    return {
        "transition_pair_mirror_agreement": float(np.mean(pair_match)) if len(pair_match) else 1.0,
        "transition_pair_mismatch_bars": int(np.sum(~pair_match)),
        "change_event_jaccard": float(event["event_jaccard"]),
        "change_event_bar_agreement": float(event["bar_agreement"]),
    }


def analyze_pair(frame: pd.DataFrame) -> dict[str, Any]:
    inverse_frame = reciprocal_ohlc(frame)
    model, config = compute(frame)
    inverse, _ = compute(inverse_frame)
    warmup = int(config.rank_len - 1)

    event_layers: dict[str, Any] = {}
    for layer, pairs in EVENT_PAIRS.items():
        event_layers[layer] = {
            f"{left}__to_inverse__{right}": boolean_metrics(arr_bool(model, left), arr_bool(inverse, right), warmup)
            for left, right in pairs
        }

    numeric_layers: dict[str, Any] = {}
    for layer, pairs in NUMERIC_PAIRS.items():
        metrics: dict[str, Any] = {}
        for left, right in pairs:
            if left in model.columns and right in inverse.columns:
                metrics[f"{left}__to_inverse__{right}"] = numeric_metrics(arr_float(model, left), arr_float(inverse, right), warmup)
        numeric_layers[layer] = metrics

    scalar_invariants = {
        key: numeric_metrics(arr_float(model, key), arr_float(inverse, key), warmup)
        for key in SELF_NUMERIC
    }
    boolean_invariants = {
        key: boolean_metrics(arr_bool(model, key), arr_bool(inverse, key), warmup)
        for key in SELF_BOOLEAN
    }

    candidate = arr_int(model, "candidate_display_id")
    inverse_candidate = arr_int(inverse, "candidate_display_id")
    formal = arr_int(model, "formal_id")
    inverse_formal = arr_int(inverse, "formal_id")

    return {
        "rows": int(len(frame)),
        "start_date": str(pd.Timestamp(frame["date"].iloc[0]).date()),
        "end_date": str(pd.Timestamp(frame["date"].iloc[-1]).date()),
        "warmup_bars": warmup,
        "event_layers": event_layers,
        "numeric_layers": numeric_layers,
        "scalar_invariants": scalar_invariants,
        "boolean_invariants": boolean_invariants,
        "stage_vector_mirrors": {
            "raw": vector_mirror_metrics(model, inverse, STAGE_VECTOR_LEFT, warmup),
            "gates": vector_mirror_metrics(model, inverse, STAGE_VECTOR_GATE, warmup),
            "effective": vector_mirror_metrics(model, inverse, STAGE_VECTOR_EFFECTIVE, warmup),
            "probabilities": vector_mirror_metrics(model, inverse, STAGE_VECTOR_PROB, warmup),
        },
        "candidate_display_stage": stage_metrics(candidate, inverse_candidate, warmup),
        "formal_stage": stage_metrics(formal, inverse_formal, warmup),
        "candidate_transition": transition_metrics(candidate, inverse_candidate, warmup),
        "formal_transition": transition_metrics(formal, inverse_formal, warmup),
    }


def mean_path(pairs: dict[str, Any], *keys: str) -> float:
    values: list[float] = []
    for row in pairs.values():
        node: Any = row
        for key in keys:
            node = node[key]
        values.append(float(node))
    return float(np.mean(values))


def mean_event(pairs: dict[str, Any], layer: str, key: str, metric: str) -> float:
    return float(np.mean([row["event_layers"][layer][key][metric] for row in pairs.values()]))


def build_report() -> dict[str, Any]:
    pairs = {name: analyze_pair(frame) for name, frame in load_frozen_pairs().items()}
    aggregate = {
        "pair_count": len(pairs),
        "range_up_to_inverse_down_jaccard": mean_event(pairs, "raw_price_range", "range_break_up__to_inverse__range_break_dn", "event_jaccard"),
        "range_down_to_inverse_up_jaccard": mean_event(pairs, "raw_price_range", "range_break_dn__to_inverse__range_break_up", "event_jaccard"),
        "ma_up_to_inverse_down_jaccard": mean_event(pairs, "ma_representation", "ma_cross_up__to_inverse__ma_cross_dn", "event_jaccard"),
        "ma_down_to_inverse_up_jaccard": mean_event(pairs, "ma_representation", "ma_cross_dn__to_inverse__ma_cross_up", "event_jaccard"),
        "breakout_mode_up_to_inverse_down_jaccard": mean_event(pairs, "directional_modes", "breakout_mode_up__to_inverse__breakdown_mode_dn", "event_jaccard"),
        "breakdown_mode_down_to_inverse_up_jaccard": mean_event(pairs, "directional_modes", "breakdown_mode_dn__to_inverse__breakout_mode_up", "event_jaccard"),
        "candidate_display_mirror_agreement": mean_path(pairs, "candidate_display_stage", "mirror_agreement"),
        "formal_stage_mirror_agreement": mean_path(pairs, "formal_stage", "mirror_agreement"),
        "candidate_transition_pair_mirror_agreement": mean_path(pairs, "candidate_transition", "transition_pair_mirror_agreement"),
        "formal_transition_pair_mirror_agreement": mean_path(pairs, "formal_transition", "transition_pair_mirror_agreement"),
        "raw_stage_vector_mae": mean_path(pairs, "stage_vector_mirrors", "raw", "mae"),
        "stage_gate_vector_mae": mean_path(pairs, "stage_vector_mirrors", "gates", "mae"),
        "effective_stage_vector_mae": mean_path(pairs, "stage_vector_mirrors", "effective", "mae"),
        "probability_stage_vector_mae": mean_path(pairs, "stage_vector_mirrors", "probabilities", "mae"),
    }
    return {
        "schema_version": 1,
        "issue": 66,
        "phase": "A",
        "status": "RECIPROCAL_SYMMETRY_DECOMPOSITION_REUSED_DATA_NO_PNL",
        "engine": "frozen v0.6 Phase-B price-only core mechanically derived from frozen v0.5.2.1",
        "research_boundary": "Engineering/semantic symmetry audit only. No strategy or profitability statistic is computed.",
        "aggregate": aggregate,
        "pairs": pairs,
    }


def pct(value: float) -> str:
    return f"{value * 100.0:.2f}%"


def fmt(value: float | int | None, digits: int = 6) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, int):
        return str(value)
    return f"{value:.{digits}f}"


def render_markdown(report: dict[str, Any]) -> str:
    a = report["aggregate"]
    lines = [
        "# Issue #66 Phase A — Reciprocal Symmetry Decomposition",
        "",
        "Status: **reused frozen data / no PnL**",
        "",
        "This report reruns the frozen v0.6 Phase-B price-only classifier on each canonical FX fixture and its reciprocal OHLC quotation. It measures semantic/inversion symmetry only.",
        "",
        "## Baseline reproduction",
        "",
        "| Layer | Reciprocal metric |",
        "|---|---:|",
        f"| Raw range break up → inverse down | Jaccard {pct(a['range_up_to_inverse_down_jaccard'])} |",
        f"| Raw range break down → inverse up | Jaccard {pct(a['range_down_to_inverse_up_jaccard'])} |",
        f"| MA cross up → inverse down | Jaccard {pct(a['ma_up_to_inverse_down_jaccard'])} |",
        f"| MA cross down → inverse up | Jaccard {pct(a['ma_down_to_inverse_up_jaccard'])} |",
        f"| Breakout mode up → inverse breakdown | Jaccard {pct(a['breakout_mode_up_to_inverse_down_jaccard'])} |",
        f"| Breakdown mode down → inverse breakout | Jaccard {pct(a['breakdown_mode_down_to_inverse_up_jaccard'])} |",
        f"| Candidate-display stage | mirror {pct(a['candidate_display_mirror_agreement'])} |",
        f"| Formal stage | mirror {pct(a['formal_stage_mirror_agreement'])} |",
        "",
        "## Six-stage vector decomposition",
        "",
        "Lower MAE is more symmetric. Raw/effective/probability values are on 0–100-like scales; gates are on 0–1.",
        "",
        "| Layer | Mean reciprocal MAE |",
        "|---|---:|",
        f"| Raw stage scores | {fmt(a['raw_stage_vector_mae'])} |",
        f"| Stage gates | {fmt(a['stage_gate_vector_mae'])} |",
        f"| Effective stage weights | {fmt(a['effective_stage_vector_mae'])} |",
        f"| Stage probabilities | {fmt(a['probability_stage_vector_mae'])} |",
        "",
        "## Persistence / transitions",
        "",
        f"Candidate transition-pair mirror agreement: **{pct(a['candidate_transition_pair_mirror_agreement'])}**  ",
        f"Formal transition-pair mirror agreement: **{pct(a['formal_transition_pair_mirror_agreement'])}**",
        "",
        "## Per pair",
        "",
        "| Pair | Range U→D | MA U→D | Candidate | Formal | Formal transition | Prob-vector MAE |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, row in report["pairs"].items():
        events = row["event_layers"]
        lines.append(
            f"| {name} | {pct(events['raw_price_range']['range_break_up__to_inverse__range_break_dn']['event_jaccard'])} | "
            f"{pct(events['ma_representation']['ma_cross_up__to_inverse__ma_cross_dn']['event_jaccard'])} | "
            f"{pct(row['candidate_display_stage']['mirror_agreement'])} | {pct(row['formal_stage']['mirror_agreement'])} | "
            f"{pct(row['formal_transition']['transition_pair_mirror_agreement'])} | "
            f"{fmt(row['stage_vector_mirrors']['probabilities']['mae'])} |"
        )
    lines += [
        "",
        "## Interpretation boundary",
        "",
        "This phase does not choose or repair any formula. The decomposition is evidence for Phase B ordering only. In particular, arithmetic moving-average / ATR representation can break reciprocal symmetry upstream of explicitly unequal bull/bear constants, while the raw range-break event itself remains exactly mirrored on the frozen fixtures.",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Issue #66 Phase-A reciprocal symmetry decomposition")
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_report()
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.markdown.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["aggregate"], indent=2))


if __name__ == "__main__":
    main()
