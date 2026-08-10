#!/usr/bin/env python3
"""Audit whether any four-state v0.6 strength measure deserves 'confidence'.

Development derives Low/Medium/High cut points per pair and canonical Formal
state. Those cut points are applied unchanged to the already-observed Exploratory
and burned Final segments. This is calibration development evidence, not a fresh
independent validation and not a PnL test.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from diagnose_v06_boundary_sensitivity import PAIRS, _load_pair
from diagnose_v06_state_cardinality import HORIZONS
from generate_v06_phase_b_core import load_phase_b_namespace
from v06_live_window import live_window
from v06_state_mapping import attach_canonical_four_state


HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "data" / "issue-55-static-fx-canonical-manifest.json"
CANONICAL_WEIGHT_COLUMNS = (
    "regime_accumulation_family",
    "regime_markup",
    "regime_distribution_family",
    "regime_markdown",
)
STRENGTH_FIELDS = (
    "canonical_formal_support",
    "canonical_formal_margin",
    "canonical_concentration",
)
DIRECTIONAL_STATES = {2: 1.0, 4: -1.0}
MIN_DEV_N = 30
MIN_BIN_N = 10


def add_strength_fields(outputs: pd.DataFrame) -> pd.DataFrame:
    result = attach_canonical_four_state(outputs)
    weights = result[list(CANONICAL_WEIGHT_COLUMNS)].to_numpy(float)
    formal = result["canonical_formal_id"].to_numpy(int)

    support = np.full(len(result), np.nan, dtype=float)
    margin = np.full(len(result), np.nan, dtype=float)
    concentration = np.full(len(result), np.nan, dtype=float)

    for index in range(len(result)):
        row = weights[index]
        if not np.isfinite(row).all() or np.nansum(row) <= 0.0:
            continue
        probs = np.clip(row / np.nansum(row), 0.0, 1.0)
        positive = probs[probs > 0.0]
        entropy = -float(np.sum(positive * np.log(positive)))
        concentration[index] = (1.0 - entropy / np.log(4.0)) * 100.0

        state = int(formal[index])
        if state <= 0:
            continue
        state_index = state - 1
        own = float(row[state_index])
        others = np.delete(row, state_index)
        support[index] = own
        margin[index] = own - float(np.max(others))

    result["canonical_formal_support"] = support
    result["canonical_formal_margin"] = margin
    result["canonical_concentration"] = concentration
    return result


def _split_bounds(meta: dict[str, Any], live_start: int) -> dict[str, tuple[int, int]]:
    result: dict[str, tuple[int, int]] = {}
    for name in ("development", "exploratory_oos", "final_oos"):
        split = meta["splits"][name]
        start = max(int(split["start_index"]), live_start)
        end = int(split["end_index"])
        if start <= end:
            result[name] = (start, end)
    return result


def _cutpoints(values: np.ndarray) -> tuple[float, float] | None:
    finite = values[np.isfinite(values)]
    if len(finite) < MIN_DEV_N:
        return None
    q1, q2 = np.quantile(finite, [1.0 / 3.0, 2.0 / 3.0])
    if not np.isfinite(q1) or not np.isfinite(q2) or q1 >= q2:
        return None
    return float(q1), float(q2)


def _bin(values: np.ndarray, cuts: tuple[float, float]) -> np.ndarray:
    q1, q2 = cuts
    out = np.full(len(values), -1, dtype=int)
    finite = np.isfinite(values)
    out[finite & (values <= q1)] = 0
    out[finite & (values > q1) & (values <= q2)] = 1
    out[finite & (values > q2)] = 2
    return out


def _forward_return(close: np.ndarray, horizon: int) -> np.ndarray:
    out = np.full(len(close), np.nan, dtype=float)
    if horizon <= 0 or horizon >= len(close):
        return out
    valid = (close[:-horizon] > 0.0) & np.isfinite(close[:-horizon]) & np.isfinite(close[horizon:])
    values = np.full(len(close) - horizon, np.nan, dtype=float)
    values[valid] = close[horizon:][valid] / close[:-horizon][valid] - 1.0
    out[:-horizon] = values
    return out


def _retention(formal: np.ndarray, horizon: int) -> np.ndarray:
    out = np.full(len(formal), np.nan, dtype=float)
    if horizon <= 0 or horizon >= len(formal):
        return out
    current = formal[:-horizon]
    future = formal[horizon:]
    valid = (current > 0) & (future >= 0)
    values = np.full(len(current), np.nan, dtype=float)
    values[valid] = (current[valid] == future[valid]).astype(float)
    out[:-horizon] = values
    return out


def _bin_means(values: np.ndarray, bins: np.ndarray, mask: np.ndarray) -> dict[str, Any]:
    names = ("low", "medium", "high")
    counts: dict[str, int] = {}
    means: dict[str, float | None] = {}
    for index, name in enumerate(names):
        selected = values[mask & (bins == index) & np.isfinite(values)]
        counts[name] = int(len(selected))
        means[name] = float(np.mean(selected)) if len(selected) >= MIN_BIN_N else None
    low = means["low"]
    med = means["medium"]
    high = means["high"]
    comparable = low is not None and high is not None
    all_bins = comparable and med is not None
    return {
        "counts": counts,
        "means": means,
        "high_minus_low": (high - low) if comparable else None,
        "high_better_than_low": (high > low) if comparable else None,
        "monotonic_low_medium_high": (low <= med <= high) if all_bins else None,
    }


def analyze_pair(pair: str, frame: pd.DataFrame, outputs: pd.DataFrame, meta: dict[str, Any]) -> dict[str, Any]:
    enriched = add_strength_fields(outputs)
    _, live_meta = live_window(enriched)
    live_start = int(live_meta["live_start_index"])
    bounds = _split_bounds(meta, live_start)
    canonical = enriched["canonical_formal_id"].to_numpy(int)
    close = frame["close"].to_numpy(float)

    cuts: dict[str, dict[str, tuple[float, float] | None]] = {field: {} for field in STRENGTH_FIELDS}
    dev_start, dev_end = bounds["development"]
    for field in STRENGTH_FIELDS:
        values = enriched[field].to_numpy(float)
        for state in range(1, 5):
            mask = np.zeros(len(values), dtype=bool)
            mask[dev_start : dev_end + 1] = True
            mask &= canonical == state
            cuts[field][str(state)] = _cutpoints(values[mask])

    segment_results: dict[str, Any] = {}
    for segment in ("exploratory_oos", "final_oos"):
        start, end = bounds[segment]
        segment_results[segment] = {}
        for field in STRENGTH_FIELDS:
            values = enriched[field].to_numpy(float)
            field_rows: list[dict[str, Any]] = []
            for state in range(1, 5):
                state_cuts = cuts[field][str(state)]
                if state_cuts is None:
                    continue
                bins = _bin(values, state_cuts)
                for horizon in HORIZONS:
                    origin_end = end - horizon
                    if origin_end < start:
                        continue
                    origin = np.zeros(len(values), dtype=bool)
                    origin[start : origin_end + 1] = True
                    state_mask = origin & (canonical == state)
                    retention = _retention(canonical, horizon)
                    retention_result = _bin_means(retention, bins, state_mask)

                    directional_result = None
                    if state in DIRECTIONAL_STATES:
                        aligned = _forward_return(close, horizon) * DIRECTIONAL_STATES[state]
                        directional_result = _bin_means(aligned, bins, state_mask)

                    field_rows.append(
                        {
                            "state": state,
                            "horizon": horizon,
                            "cutpoints": list(state_cuts),
                            "retention": retention_result,
                            "directional_aligned_return": directional_result,
                        }
                    )
            segment_results[segment][field] = field_rows

    return {"pair": pair, "live_start": live_start, "cutpoints": cuts, "segments": segment_results}


def _aggregate(pairs: list[dict[str, Any]], segment: str, field: str, outcome: str) -> dict[str, Any]:
    comparable = 0
    high_better = 0
    monotonic_comparable = 0
    monotonic = 0
    high_low_values: list[float] = []
    for pair in pairs:
        for row in pair["segments"][segment][field]:
            result = row[outcome]
            if result is None:
                continue
            if result["high_better_than_low"] is not None:
                comparable += 1
                high_better += int(result["high_better_than_low"])
                high_low_values.append(float(result["high_minus_low"]))
            if result["monotonic_low_medium_high"] is not None:
                monotonic_comparable += 1
                monotonic += int(result["monotonic_low_medium_high"])
    return {
        "comparable_cases": comparable,
        "high_better_cases": high_better,
        "high_better_rate": high_better / comparable if comparable else None,
        "median_high_minus_low": float(np.median(high_low_values)) if high_low_values else None,
        "monotonic_comparable_cases": monotonic_comparable,
        "monotonic_cases": monotonic,
        "monotonic_rate": monotonic / monotonic_comparable if monotonic_comparable else None,
    }


def run_strength_audit() -> dict[str, Any]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    compute = load_phase_b_namespace()["compute_price_only"]
    pairs: list[dict[str, Any]] = []
    for pair in PAIRS:
        frame = _load_pair(pair)
        pairs.append(analyze_pair(pair, frame, compute(frame), manifest["pairs"][pair]))

    summary: dict[str, Any] = {}
    for segment in ("exploratory_oos", "final_oos"):
        summary[segment] = {}
        for field in STRENGTH_FIELDS:
            summary[segment][field] = {
                "formal_retention": _aggregate(pairs, segment, field, "retention"),
                "directional_aligned_return": _aggregate(
                    pairs, segment, field, "directional_aligned_return"
                ),
            }

    return {
        "issue": 57,
        "phase": "D-four-state-strength",
        "scope": (
            "Development-derived per-pair/per-state terciles applied unchanged to already-observed Exploratory and "
            "burned Final segments. Internal calibration-development evidence only; no PnL and no independent validation."
        ),
        "fields": {
            "canonical_formal_support": "weight assigned to the currently confirmed four-state Formal regime",
            "canonical_formal_margin": "Formal weight minus the strongest competing four-state weight",
            "canonical_concentration": "100 * (1 - normalized entropy) across four canonical weights",
        },
        "pairs": pairs,
        "summary": summary,
    }


def main() -> None:
    print(json.dumps(run_strength_audit(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
