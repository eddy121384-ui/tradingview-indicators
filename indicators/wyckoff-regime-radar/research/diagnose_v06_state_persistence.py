#!/usr/bin/env python3
"""Audit candidate -> formal-state persistence for Wyckoff v0.6 Phase B.

This module changes no model logic. It measures the existing frozen persistence
state machine on already-observed Issue #55 data so Phase B changes, if any, are
motivated by explicit timing pathology rather than backtest PnL.
"""

from __future__ import annotations

import json
from typing import Any, Callable

import numpy as np
import pandas as pd

from diagnose_v06_boundary_sensitivity import PAIRS, _load_pair
from generate_v06_price_only_core import load_v06_namespace
from price_only_core import STAGE_NAMES, compute_price_only


ENGINE_NAMES = ("v0.5.2.1", "v0.6-phase-a")


def _runs(values: np.ndarray, *, include_zero: bool = False) -> list[tuple[int, int, int]]:
    """Return inclusive contiguous runs as (start, end, value)."""

    arr = np.asarray(values, dtype=int)
    if len(arr) == 0:
        return []
    result: list[tuple[int, int, int]] = []
    start = 0
    for index in range(1, len(arr) + 1):
        if index == len(arr) or arr[index] != arr[start]:
            value = int(arr[start])
            if include_zero or value != 0:
                result.append((start, index - 1, value))
            start = index
    return result


def _condition_runs(mask: np.ndarray) -> list[int]:
    arr = np.asarray(mask, dtype=bool)
    lengths: list[int] = []
    start: int | None = None
    for index, value in enumerate(arr):
        if value and start is None:
            start = index
        if start is not None and (not value or index == len(arr) - 1):
            end = index if value and index == len(arr) - 1 else index - 1
            lengths.append(end - start + 1)
            start = None
    return lengths


def _stats(lengths: list[int]) -> dict[str, float | int | None]:
    if not lengths:
        return {"count": 0, "median": None, "p90": None, "max": None}
    values = np.asarray(lengths, dtype=float)
    return {
        "count": len(lengths),
        "median": float(np.median(values)),
        "p90": float(np.percentile(values, 90)),
        "max": int(np.max(values)),
    }


def _candidate_adoption(candidate: np.ndarray, formal: np.ndarray) -> dict[str, Any]:
    demand_runs = 0
    adopted_delays: list[int] = []
    unadopted_lengths: list[int] = []
    examples: list[dict[str, int]] = []

    for start, end, stage in _runs(candidate):
        if int(formal[start]) == stage:
            continue
        demand_runs += 1
        adoption = None
        for index in range(start, end + 1):
            if int(formal[index]) == stage:
                adoption = index
                break
        if adoption is None:
            length = end - start + 1
            unadopted_lengths.append(length)
            if len(examples) < 8:
                examples.append({"start": start, "end": end, "stage": stage, "length": length})
        else:
            adopted_delays.append(adoption - start)

    return {
        "switch_demand_candidate_runs": demand_runs,
        "adopted_runs": len(adopted_delays),
        "unadopted_runs": len(unadopted_lengths),
        "adoption_rate": (len(adopted_delays) / demand_runs) if demand_runs else None,
        "adopted_delay_bars": _stats(adopted_delays),
        "unadopted_run_length_bars": _stats(unadopted_lengths),
        "unadopted_examples": examples,
    }


def analyze_outputs(outputs: pd.DataFrame) -> dict[str, Any]:
    candidate = outputs["candidate_id"].fillna(0).to_numpy(int)
    candidate_display = outputs["candidate_display_id"].fillna(0).to_numpy(int)
    formal = outputs["formal_id"].fillna(0).to_numpy(int)
    n = len(outputs)

    strong_candidate = candidate != 0
    disagreement = strong_candidate & (candidate != formal)
    carry = (formal != 0) & (candidate == 0)
    weak_only = (candidate_display != 0) & (candidate == 0)

    formal_switches = int(np.sum(formal[1:] != formal[:-1])) if n > 1 else 0
    candidate_switches = int(np.sum(candidate[1:] != candidate[:-1])) if n > 1 else 0
    one_bar_flips = 0
    if n >= 3:
        one_bar_flips = int(np.sum((formal[1:-1] != formal[:-2]) & (formal[2:] == formal[:-2])))

    dwell_by_stage: dict[str, dict[str, float | int | None]] = {}
    all_dwell: list[int] = []
    for stage in range(1, 7):
        lengths = [end - start + 1 for start, end, value in _runs(formal) if value == stage]
        all_dwell.extend(lengths)
        dwell_by_stage[f"{stage}_{STAGE_NAMES[stage]}"] = _stats(lengths)

    disagreement_lengths = _condition_runs(disagreement)
    carry_lengths = _condition_runs(carry)
    weak_only_lengths = _condition_runs(weak_only)

    return {
        "bars": n,
        "formal_zero_share": float(np.mean(formal == 0)) if n else None,
        "strong_candidate_share": float(np.mean(strong_candidate)) if n else None,
        "weak_only_candidate_share": float(np.mean(weak_only)) if n else None,
        "candidate_formal_disagreement_share_all_bars": float(np.mean(disagreement)) if n else None,
        "candidate_formal_disagreement_share_candidate_bars": (
            float(np.sum(disagreement) / np.sum(strong_candidate)) if np.sum(strong_candidate) else None
        ),
        "formal_carry_without_strong_candidate_share": float(np.mean(carry)) if n else None,
        "candidate_formal_disagreement_run_bars": _stats(disagreement_lengths),
        "formal_carry_run_bars": _stats(carry_lengths),
        "weak_only_run_bars": _stats(weak_only_lengths),
        "formal_switches": formal_switches,
        "candidate_switches": candidate_switches,
        "one_bar_formal_flips": one_bar_flips,
        "one_bar_flip_per_formal_switch": (one_bar_flips / formal_switches) if formal_switches else None,
        "formal_dwell_bars_all_states": _stats(all_dwell),
        "formal_dwell_bars_by_stage": dwell_by_stage,
        "candidate_adoption": _candidate_adoption(candidate, formal),
    }


def _engine_outputs(
    compute: Callable[[pd.DataFrame], pd.DataFrame],
    frame: pd.DataFrame,
) -> pd.DataFrame:
    return compute(frame)


def run_persistence_audit() -> dict[str, Any]:
    v06_compute = load_v06_namespace()["compute_price_only"]
    engines: dict[str, Callable[[pd.DataFrame], pd.DataFrame]] = {
        "v0.5.2.1": compute_price_only,
        "v0.6-phase-a": v06_compute,
    }

    rows: list[dict[str, Any]] = []
    for pair in PAIRS:
        frame = _load_pair(pair)
        for engine_name, compute in engines.items():
            metrics = analyze_outputs(_engine_outputs(compute, frame))
            rows.append({"pair": pair, "engine": engine_name, **metrics})

    summary: dict[str, Any] = {}
    for engine_name in ENGINE_NAMES:
        engine_rows = [row for row in rows if row["engine"] == engine_name]

        def median_field(name: str) -> float | None:
            values = [float(row[name]) for row in engine_rows if row[name] is not None]
            return float(np.median(values)) if values else None

        disagreement_run_p90 = [
            float(row["candidate_formal_disagreement_run_bars"]["p90"])
            for row in engine_rows
            if row["candidate_formal_disagreement_run_bars"]["p90"] is not None
        ]
        carry_run_p90 = [
            float(row["formal_carry_run_bars"]["p90"])
            for row in engine_rows
            if row["formal_carry_run_bars"]["p90"] is not None
        ]
        adoption_delays = [
            float(row["candidate_adoption"]["adopted_delay_bars"]["median"])
            for row in engine_rows
            if row["candidate_adoption"]["adopted_delay_bars"]["median"] is not None
        ]
        adoption_rates = [
            float(row["candidate_adoption"]["adoption_rate"])
            for row in engine_rows
            if row["candidate_adoption"]["adoption_rate"] is not None
        ]
        dwell_medians = [
            float(row["formal_dwell_bars_all_states"]["median"])
            for row in engine_rows
            if row["formal_dwell_bars_all_states"]["median"] is not None
        ]
        summary[engine_name] = {
            "median_pair_disagreement_share_all_bars": median_field(
                "candidate_formal_disagreement_share_all_bars"
            ),
            "median_pair_disagreement_share_candidate_bars": median_field(
                "candidate_formal_disagreement_share_candidate_bars"
            ),
            "median_pair_formal_carry_share": median_field("formal_carry_without_strong_candidate_share"),
            "median_pair_disagreement_run_p90_bars": (
                float(np.median(disagreement_run_p90)) if disagreement_run_p90 else None
            ),
            "median_pair_formal_carry_run_p90_bars": (
                float(np.median(carry_run_p90)) if carry_run_p90 else None
            ),
            "median_pair_adopted_switch_delay_bars": (
                float(np.median(adoption_delays)) if adoption_delays else None
            ),
            "median_pair_candidate_adoption_rate": (
                float(np.median(adoption_rates)) if adoption_rates else None
            ),
            "median_pair_formal_dwell_median_bars": (
                float(np.median(dwell_medians)) if dwell_medians else None
            ),
            "total_one_bar_formal_flips": int(sum(int(row["one_bar_formal_flips"]) for row in engine_rows)),
            "total_formal_switches": int(sum(int(row["formal_switches"]) for row in engine_rows)),
        }

    return {
        "issue": 57,
        "phase": "B-audit",
        "scope": (
            "All Issue #55 frozen 2012-2022 FX bars are already-observed/burned and are used here only "
            "for persistence diagnosis. No PnL or independent OOS claim."
        ),
        "rows": rows,
        "summary": summary,
    }


def main() -> None:
    print(json.dumps(run_persistence_audit(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
