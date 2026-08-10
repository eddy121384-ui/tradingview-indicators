#!/usr/bin/env python3
"""Compare TradingView Issue #55 parity export against the Python mirror.

The intended input is TradingView's chart-data CSV exported from an EURUSD 1D
chart while the generated Issue #55 parity Pine is attached. The comparator
feeds the *same TradingView OHLC rows* into Python, removing cross-vendor feed
mismatch from the implementation-parity question.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from .price_only_core import compute_price_only
except ImportError:
    from price_only_core import compute_price_only  # type: ignore


TV_TO_PY = {
    "PARITY speed_rank": "speed_rank",
    "PARITY accel_rank": "accel_rank",
    "PARITY dist_rank": "dist_rank",
    "PARITY heat_up": "heat_up",
    "PARITY panic_heat_dn": "panic_heat_dn",
    "PARITY maturity_up": "maturity_up",
    "PARITY maturity_dn": "maturity_dn",
    "PARITY range_score": "range_score",
    "PARITY downside_exhaustion": "downside_exhaustion",
    "PARITY upside_exhaustion": "upside_exhaustion",
    "PARITY support_holding": "support_holding",
    "PARITY resistance_holding": "resistance_holding",
    "PARITY markup_extension": "markup_extension_score",
    "PARITY markdown_extension": "markdown_extension_score",
    "PARITY markup_continuation": "markup_continuation_score",
    "PARITY markdown_continuation": "markdown_continuation_score",
    "PARITY acc_gate_pct": "acc_gate",
    "PARITY markup_gate_pct": "markup_gate",
    "PARITY reacc_gate_pct": "reacc_gate",
    "PARITY dist_gate_pct": "dist_gate",
    "PARITY markdown_gate_pct": "markdown_gate",
    "PARITY redist_gate_pct": "redist_gate",
    "PARITY prob_acc": "prob_acc",
    "PARITY prob_markup": "prob_markup",
    "PARITY prob_reacc": "prob_reacc",
    "PARITY prob_dist": "prob_dist",
    "PARITY prob_markdown": "prob_markdown",
    "PARITY prob_redist": "prob_redist",
    "PARITY top_value": "top_value",
    "PARITY top_gap": "top_gap",
    "PARITY evidence_strength": "evidence_strength",
    "PARITY top_id": "top_id",
    "PARITY candidate_display_id": "candidate_display_id",
    "PARITY formal_id": "formal_id",
}

# Pine plots gates as percentages while Python stores [0,1] gates.
PERCENT_GATE_FIELDS = {
    "acc_gate",
    "markup_gate",
    "reacc_gate",
    "dist_gate",
    "markdown_gate",
    "redist_gate",
}
ID_FIELDS = {"top_id", "candidate_display_id", "formal_id"}
CORE_FIELDS = [
    "prob_acc",
    "prob_markup",
    "prob_reacc",
    "prob_dist",
    "prob_markdown",
    "prob_redist",
    "top_gap",
    "evidence_strength",
]


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(name).lower()).strip()


def find_column(columns, wanted: str) -> str:
    wanted_norm = _norm(wanted)
    exact = [column for column in columns if _norm(column) == wanted_norm]
    if len(exact) == 1:
        return exact[0]
    suffix = [column for column in columns if _norm(column).endswith(wanted_norm)]
    if len(suffix) == 1:
        return suffix[0]
    contains = [column for column in columns if wanted_norm in _norm(column)]
    if len(contains) == 1:
        return contains[0]
    raise ValueError(f"could not uniquely locate column {wanted!r}; matches={contains or suffix or exact}")


def load_tv_csv(path: Path) -> tuple[pd.DataFrame, dict[str, str]]:
    frame = pd.read_csv(path)
    columns = list(frame.columns)
    mapping: dict[str, str] = {}
    for canonical in ("open", "high", "low", "close"):
        mapping[canonical] = find_column(columns, canonical)
    for tv_name in TV_TO_PY:
        mapping[tv_name] = find_column(columns, tv_name)

    date_column = None
    for candidate in ("time", "date", "datetime"):
        try:
            date_column = find_column(columns, candidate)
            break
        except ValueError:
            pass
    if date_column is not None:
        mapping["date"] = date_column

    normalized = pd.DataFrame()
    if date_column is not None:
        normalized["date"] = frame[date_column]
    for canonical in ("open", "high", "low", "close"):
        normalized[canonical] = pd.to_numeric(frame[mapping[canonical]], errors="coerce")
    return normalized, mapping


def compare(path: Path) -> dict:
    raw = pd.read_csv(path)
    ohlc, mapping = load_tv_csv(path)
    py = compute_price_only(ohlc)

    comparisons: dict[str, dict] = {}
    common_mask = np.ones(len(raw), dtype=bool)
    for tv_name, py_name in TV_TO_PY.items():
        tv_values = pd.to_numeric(raw[mapping[tv_name]], errors="coerce").to_numpy(float)
        py_values = pd.to_numeric(py[py_name], errors="coerce").to_numpy(float)
        if py_name in PERCENT_GATE_FIELDS:
            py_values = py_values * 100.0
        valid = np.isfinite(tv_values) & np.isfinite(py_values)
        common_mask &= valid
        count = int(valid.sum())
        if count == 0:
            comparisons[py_name] = {"comparable_rows": 0}
            continue
        diff = np.abs(tv_values[valid] - py_values[valid])
        entry = {
            "comparable_rows": count,
            "max_abs_error": float(diff.max()),
            "mean_abs_error": float(diff.mean()),
            "p99_abs_error": float(np.quantile(diff, 0.99)),
        }
        if py_name in ID_FIELDS:
            entry["agreement_rate"] = float(np.mean(np.rint(tv_values[valid]).astype(int) == np.rint(py_values[valid]).astype(int)))
        comparisons[py_name] = entry

    # Evaluation begins only when all parity fields are finite in both engines.
    common_indices = np.flatnonzero(common_mask)
    first_common = int(common_indices[0]) if len(common_indices) else None
    last_common = int(common_indices[-1]) if len(common_indices) else None

    formal = comparisons.get("formal_id", {})
    candidate = comparisons.get("candidate_display_id", {})
    core_p99 = [comparisons[field].get("p99_abs_error", np.inf) for field in CORE_FIELDS]

    # Predeclared engineering gate. This is not an economic-performance gate.
    acceptance = {
        "formal_stage_agreement_at_least_99_5pct": formal.get("agreement_rate", 0.0) >= 0.995,
        "candidate_stage_agreement_at_least_99pct": candidate.get("agreement_rate", 0.0) >= 0.99,
        "core_continuous_fields_p99_error_at_most_0_50_points": bool(core_p99) and max(core_p99) <= 0.50,
    }
    acceptance["pass"] = all(acceptance.values())

    report = {
        "source_csv": str(path),
        "rows": int(len(raw)),
        "first_all-fields-comparable_row_index": first_common,
        "last_all-fields-comparable_row_index": last_common,
        "column_mapping": mapping,
        "comparisons": comparisons,
        "acceptance": acceptance,
        "notes": [
            "Stage weights are relative scores, not statistical probabilities.",
            "The comparator uses TradingView OHLC as Python input, so feed mismatch is removed from this parity test.",
            "If parity fails, fix implementation semantics before any OOS utility analysis.",
        ],
    }
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare TradingView Wyckoff parity CSV to Python mirror")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = compare(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report["acceptance"], indent=2))
    if not report["acceptance"]["pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
