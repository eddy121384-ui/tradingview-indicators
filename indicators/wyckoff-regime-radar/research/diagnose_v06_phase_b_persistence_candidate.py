#!/usr/bin/env python3
"""Compare Phase-B stale-formal decay with the unchanged Phase-A state machine.

This is an internal timing/coverage diagnostic on burned Issue #55 history. It
contains no return or PnL evaluation and is not an independent OOS test.
"""

from __future__ import annotations

import json
from typing import Any

import numpy as np

from diagnose_v06_boundary_sensitivity import PAIRS, _load_pair
from diagnose_v06_state_persistence import analyze_outputs
from generate_v06_phase_b_core import load_phase_b_namespace
from generate_v06_price_only_core import load_v06_namespace


def _zero_run_stats(formal: np.ndarray) -> dict[str, float | int | None]:
    lengths: list[int] = []
    start: int | None = None
    for index, value in enumerate(formal):
        if value == 0 and start is None:
            start = index
        if start is not None and (value != 0 or index == len(formal) - 1):
            end = index if value == 0 and index == len(formal) - 1 else index - 1
            lengths.append(end - start + 1)
            start = None
    if not lengths:
        return {"count": 0, "median": None, "p90": None, "max": None}
    arr = np.asarray(lengths, dtype=float)
    return {
        "count": len(lengths),
        "median": float(np.median(arr)),
        "p90": float(np.percentile(arr, 90)),
        "max": int(np.max(arr)),
    }


def _transition_counts(formal: np.ndarray) -> dict[str, int]:
    direct_nonzero = 0
    into_zero = 0
    out_of_zero = 0
    for previous, current in zip(formal[:-1], formal[1:]):
        if previous == current:
            continue
        if previous != 0 and current != 0:
            direct_nonzero += 1
        elif previous != 0 and current == 0:
            into_zero += 1
        elif previous == 0 and current != 0:
            out_of_zero += 1
    return {
        "direct_nonzero_to_nonzero": direct_nonzero,
        "into_zero": into_zero,
        "out_of_zero": out_of_zero,
    }


def _analyze(outputs, *, phase_b: bool) -> dict[str, Any]:
    metrics = analyze_outputs(outputs)
    formal = outputs["formal_id"].fillna(0).to_numpy(int)
    metrics["formal_zero_run_bars"] = _zero_run_stats(formal)
    metrics["transition_types"] = _transition_counts(formal)
    if phase_b:
        reason = outputs["stale_pressure_reason"].fillna(0).to_numpy(int)
        clear_indices = np.where((formal[1:] == 0) & (formal[:-1] != 0))[0] + 1
        reasons = {"chaos": 0, "weak_challenger": 0, "coexist": 0, "other": 0}
        for index in clear_indices:
            value = int(reason[index])
            if value == 1:
                reasons["chaos"] += 1
            elif value == 2:
                reasons["weak_challenger"] += 1
            elif value == 3:
                reasons["coexist"] += 1
            else:
                reasons["other"] += 1
        metrics["clear_to_zero_reasons"] = reasons
    return metrics


def run_phase_b_candidate_comparison() -> dict[str, Any]:
    phase_a_compute = load_v06_namespace()["compute_price_only"]
    phase_b_compute = load_phase_b_namespace()["compute_price_only"]
    rows: list[dict[str, Any]] = []

    for pair in PAIRS:
        frame = _load_pair(pair)
        rows.append({"pair": pair, "engine": "phase_a", **_analyze(phase_a_compute(frame), phase_b=False)})
        rows.append({"pair": pair, "engine": "phase_b_candidate", **_analyze(phase_b_compute(frame), phase_b=True)})

    summary: dict[str, Any] = {}
    for engine in ("phase_a", "phase_b_candidate"):
        engine_rows = [row for row in rows if row["engine"] == engine]

        def med(path: tuple[str, ...]) -> float | None:
            values: list[float] = []
            for row in engine_rows:
                value: Any = row
                for key in path:
                    value = value[key]
                if value is not None:
                    values.append(float(value))
            return float(np.median(values)) if values else None

        summary[engine] = {
            "median_pair_formal_zero_share": med(("formal_zero_share",)),
            "median_pair_formal_carry_share": med(("formal_carry_without_strong_candidate_share",)),
            "median_pair_disagreement_share_candidate_bars": med(
                ("candidate_formal_disagreement_share_candidate_bars",)
            ),
            "median_pair_disagreement_run_p90_bars": med(
                ("candidate_formal_disagreement_run_bars", "p90")
            ),
            "median_pair_formal_carry_run_p90_bars": med(("formal_carry_run_bars", "p90")),
            "median_pair_adopted_switch_delay_bars": med(
                ("candidate_adoption", "adopted_delay_bars", "median")
            ),
            "median_pair_candidate_adoption_rate": med(("candidate_adoption", "adoption_rate")),
            "median_pair_formal_dwell_median_bars": med(("formal_dwell_bars_all_states", "median")),
            "median_pair_zero_run_median_bars": med(("formal_zero_run_bars", "median")),
            "median_pair_zero_run_p90_bars": med(("formal_zero_run_bars", "p90")),
            "total_one_bar_formal_flips": int(sum(int(row["one_bar_formal_flips"]) for row in engine_rows)),
            "total_formal_switches": int(sum(int(row["formal_switches"]) for row in engine_rows)),
            "total_direct_nonzero_switches": int(
                sum(int(row["transition_types"]["direct_nonzero_to_nonzero"]) for row in engine_rows)
            ),
            "total_into_zero_transitions": int(
                sum(int(row["transition_types"]["into_zero"]) for row in engine_rows)
            ),
        }
        if engine == "phase_b_candidate":
            summary[engine]["clear_to_zero_reasons"] = {
                key: int(sum(int(row["clear_to_zero_reasons"][key]) for row in engine_rows))
                for key in ("chaos", "weak_challenger", "coexist", "other")
            }

    return {
        "issue": 57,
        "phase": "B-candidate-comparison",
        "scope": "Burned Issue #55 FX history only; state-machine engineering comparison; no PnL/OOS claim.",
        "rule": (
            "Keep strong-candidate confirmation unchanged. Clear an existing Formal to neutral after confirm_bars "
            "of continuous chaos, weak opposing challenger, or coexistence pressure. Never promote weak candidates."
        ),
        "rows": rows,
        "summary": summary,
    }


def main() -> None:
    print(json.dumps(run_phase_b_candidate_comparison(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
