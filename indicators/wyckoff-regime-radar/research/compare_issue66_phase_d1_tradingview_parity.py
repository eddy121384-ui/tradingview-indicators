#!/usr/bin/env python3
"""Compare TradingView Issue #66 C-2 parity export against the C-2 Python reference.

The comparator feeds the exact TradingView OHLC rows back into the accepted C-2
Python loader. This removes cross-vendor feed differences from the parity test.
A failure is an implementation-semantic finding only; it does not authorize
classifier tuning.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from .generate_issue66_phase_c2_stage14_conflict_core import load_phase_c2_namespace
except ImportError:
    from generate_issue66_phase_c2_stage14_conflict_core import load_phase_c2_namespace  # type: ignore


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
    "PARITY markup_extension_score": "markup_extension_score",
    "PARITY markdown_extension_score": "markdown_extension_score",
    "PARITY markup_continuation_score": "markup_continuation_score",
    "PARITY markdown_continuation_score": "markdown_continuation_score",
    "PARITY acc_gate": "acc_gate",
    "PARITY markup_gate": "markup_gate",
    "PARITY reacc_gate": "reacc_gate",
    "PARITY dist_gate": "dist_gate",
    "PARITY markdown_gate": "markdown_gate",
    "PARITY redist_gate": "redist_gate",
    "PARITY prob_acc": "prob_acc",
    "PARITY prob_markup": "prob_markup",
    "PARITY prob_reacc": "prob_reacc",
    "PARITY prob_dist": "prob_dist",
    "PARITY prob_markdown": "prob_markdown",
    "PARITY prob_redist": "prob_redist",
    "PARITY top_id": "top_id",
    "PARITY top_value": "top_value",
    "PARITY top_gap": "top_gap",
    "PARITY evidence_strength": "evidence_strength",
    "PARITY candidate_display_id": "candidate_display_id",
    "PARITY formal_id": "formal_id",
    "PARITY stale_pressure_bars": "stale_pressure_bars",
    "PARITY stale_pressure_reason": "stale_pressure_reason",
}

PERCENT_GATE_FIELDS = {
    "acc_gate",
    "markup_gate",
    "reacc_gate",
    "dist_gate",
    "markdown_gate",
    "redist_gate",
}
ID_FIELDS = {
    "top_id",
    "candidate_display_id",
    "formal_id",
    "stale_pressure_bars",
    "stale_pressure_reason",
}
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


def compute_c2(ohlc: pd.DataFrame) -> pd.DataFrame:
    namespace = load_phase_c2_namespace()
    compute = namespace["compute_price_only"]
    return compute(ohlc)  # type: ignore[operator]


def compare(path: Path) -> dict:
    raw = pd.read_csv(path)
    ohlc, mapping = load_tv_csv(path)
    py = compute_c2(ohlc)

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
            entry["agreement_rate"] = float(
                np.mean(np.rint(tv_values[valid]).astype(int) == np.rint(py_values[valid]).astype(int))
            )
        comparisons[py_name] = entry

    common_indices = np.flatnonzero(common_mask)
    first_common = int(common_indices[0]) if len(common_indices) else None
    last_common = int(common_indices[-1]) if len(common_indices) else None

    formal = comparisons.get("formal_id", {})
    candidate = comparisons.get("candidate_display_id", {})
    core_p99 = [comparisons[field].get("p99_abs_error", np.inf) for field in CORE_FIELDS]
    acceptance = {
        "formal_stage_agreement_at_least_99_5pct": formal.get("agreement_rate", 0.0) >= 0.995,
        "candidate_stage_agreement_at_least_99pct": candidate.get("agreement_rate", 0.0) >= 0.99,
        "core_continuous_fields_p99_error_at_most_0_50_points": bool(core_p99) and max(core_p99) <= 0.50,
    }
    acceptance["pass"] = all(acceptance.values())

    return {
        "issue": 66,
        "phase": "D-1",
        "reference": "accepted C-2 price-only Python core",
        "source_csv": str(path),
        "rows": int(len(raw)),
        "first_all_fields_comparable_row_index": first_common,
        "last_all_fields_comparable_row_index": last_common,
        "column_mapping": mapping,
        "comparisons": comparisons,
        "acceptance": acceptance,
        "notes": [
            "TradingView OHLC is reused as Python input to remove feed mismatch.",
            "This is an implementation-parity gate, not an economic-performance gate.",
            "Parity failures authorize implementation-semantic fixes only; C-2 classifier formulas and thresholds remain frozen.",
        ],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Compare Issue #66 C-2 TradingView parity CSV to Python")
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    report = compare(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report["acceptance"], indent=2))
    if not report["acceptance"]["pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
