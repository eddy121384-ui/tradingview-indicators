#!/usr/bin/env python3
"""Engineering sweep of stale-Formal decay horizons for Issue #57 Phase B.

Candidates are exact multiples (1x/2x/3x) of the already-existing confirm_bars
horizon. No return or PnL is evaluated. The purpose is to compare stale-state
reduction against neutral churn before freezing a persistence rule.
"""

from __future__ import annotations

import json
from typing import Any

import numpy as np

from diagnose_v06_boundary_sensitivity import PAIRS, _load_pair
from diagnose_v06_phase_b_persistence_candidate import _analyze
from generate_v06_phase_b_core import load_phase_b_namespace
from generate_v06_price_only_core import load_v06_namespace
from price_only_core import PriceOnlyConfig


MULTIPLIERS = (1, 2, 3)


def simulate_stale_decay(outputs, multiplier: int):
    if multiplier <= 0:
        raise ValueError("multiplier must be positive")
    cfg = PriceOnlyConfig()
    out = outputs.copy()
    n = len(out)
    strong = out["strong_candidate"].fillna(False).to_numpy(bool)
    top_id = out["top_id"].fillna(0).to_numpy(int)
    fast_switch = out["fast_switch"].fillna(False).to_numpy(bool)
    display = out["candidate_display_id"].fillna(0).to_numpy(int)
    chaos = out["chaos"].fillna(False).to_numpy(bool)
    coexist = out["coexist"].fillna(False).to_numpy(bool)

    formal = np.zeros(n, dtype=int)
    candidate = np.zeros(n, dtype=int)
    candidate_bars_series = np.zeros(n, dtype=int)
    stale_bars_series = np.zeros(n, dtype=int)
    stale_reason_series = np.zeros(n, dtype=int)

    confirmed = 0
    current_candidate = 0
    candidate_bars = 0
    stale_bars = 0
    stale_limit = cfg.confirm_bars * multiplier

    for index in range(n):
        if strong[index]:
            stale_bars = 0
            stale_reason = 0
            raw_id = int(top_id[index])
            if raw_id == current_candidate:
                candidate_bars += 1
            else:
                current_candidate = raw_id
                candidate_bars = 1
            active_confirm = cfg.fast_switch_confirm_bars if fast_switch[index] else cfg.confirm_bars
            if candidate_bars >= active_confirm:
                confirmed = current_candidate
        else:
            current_candidate = 0
            candidate_bars = 0
            display_id = int(display[index])
            weak_challenger = confirmed != 0 and display_id != 0 and display_id != confirmed
            coexist_pressure = confirmed != 0 and bool(coexist[index]) and display_id == 0
            if bool(chaos[index]) and confirmed != 0:
                stale_reason = 1
            elif weak_challenger:
                stale_reason = 2
            elif coexist_pressure:
                stale_reason = 3
            else:
                stale_reason = 0

            if stale_reason != 0:
                stale_bars += 1
                if stale_bars >= stale_limit:
                    confirmed = 0
            else:
                stale_bars = 0

        formal[index] = confirmed
        candidate[index] = current_candidate
        candidate_bars_series[index] = candidate_bars
        stale_bars_series[index] = stale_bars
        stale_reason_series[index] = stale_reason

    out["formal_id"] = formal
    out["candidate_id"] = candidate
    out["candidate_bars"] = candidate_bars_series
    out["stale_pressure_bars"] = stale_bars_series
    out["stale_pressure_reason"] = stale_reason_series
    return out


def _summary(engine_rows: list[dict[str, Any]]) -> dict[str, Any]:
    def med(path: tuple[str, ...]) -> float | None:
        values: list[float] = []
        for row in engine_rows:
            value: Any = row
            for key in path:
                value = value[key]
            if value is not None:
                values.append(float(value))
        return float(np.median(values)) if values else None

    return {
        "median_pair_formal_zero_share": med(("formal_zero_share",)),
        "median_pair_formal_carry_share": med(("formal_carry_without_strong_candidate_share",)),
        "median_pair_disagreement_share_candidate_bars": med(
            ("candidate_formal_disagreement_share_candidate_bars",)
        ),
        "median_pair_carry_run_p90_bars": med(("formal_carry_run_bars", "p90")),
        "median_pair_disagreement_run_p90_bars": med(
            ("candidate_formal_disagreement_run_bars", "p90")
        ),
        "median_pair_formal_dwell_median_bars": med(("formal_dwell_bars_all_states", "median")),
        "median_pair_zero_run_median_bars": med(("formal_zero_run_bars", "median")),
        "median_pair_zero_run_p90_bars": med(("formal_zero_run_bars", "p90")),
        "total_one_bar_formal_flips": int(sum(int(row["one_bar_formal_flips"]) for row in engine_rows)),
        "total_formal_switches": int(sum(int(row["formal_switches"]) for row in engine_rows)),
        "total_into_zero_transitions": int(
            sum(int(row["transition_types"]["into_zero"]) for row in engine_rows)
        ),
    }


def run_decay_sweep() -> dict[str, Any]:
    phase_a_compute = load_v06_namespace()["compute_price_only"]
    phase_b_1x_compute = load_phase_b_namespace()["compute_price_only"]
    rows: list[dict[str, Any]] = []

    for pair in PAIRS:
        frame = _load_pair(pair)
        phase_a_outputs = phase_a_compute(frame)
        rows.append({"pair": pair, "engine": "phase_a", **_analyze(phase_a_outputs, phase_b=False)})

        for multiplier in MULTIPLIERS:
            simulated = simulate_stale_decay(phase_a_outputs, multiplier)
            if multiplier == 1:
                generated = phase_b_1x_compute(frame)
                if not np.array_equal(
                    simulated["formal_id"].to_numpy(int), generated["formal_id"].to_numpy(int)
                ):
                    raise RuntimeError(f"1x simulator does not match generated Phase-B core for {pair}")
            rows.append(
                {
                    "pair": pair,
                    "engine": f"stale_decay_{multiplier}x",
                    "multiplier": multiplier,
                    **_analyze(simulated, phase_b=True),
                }
            )

    summary: dict[str, Any] = {}
    for engine in ("phase_a",) + tuple(f"stale_decay_{m}x" for m in MULTIPLIERS):
        summary[engine] = _summary([row for row in rows if row["engine"] == engine])

    baseline = summary["phase_a"]
    for multiplier in MULTIPLIERS:
        key = f"stale_decay_{multiplier}x"
        row = summary[key]
        base_carry = float(baseline["median_pair_formal_carry_share"])
        new_carry = float(row["median_pair_formal_carry_share"])
        base_zero = float(baseline["median_pair_formal_zero_share"])
        new_zero = float(row["median_pair_formal_zero_share"])
        row["carry_reduction_relative"] = (base_carry - new_carry) / base_carry if base_carry else None
        row["formal_zero_increase_percentage_points"] = (new_zero - base_zero) * 100.0
        row["additional_into_zero_transitions"] = (
            int(row["total_into_zero_transitions"]) - int(baseline["total_into_zero_transitions"])
        )
        row["additional_formal_switches"] = int(row["total_formal_switches"]) - int(
            baseline["total_formal_switches"]
        )

    return {
        "issue": 57,
        "phase": "B-decay-horizon-sweep",
        "scope": "Burned Issue #55 history only; 1x/2x/3x confirm_bars engineering sensitivity; no PnL.",
        "confirm_bars": PriceOnlyConfig().confirm_bars,
        "multipliers": list(MULTIPLIERS),
        "rows": rows,
        "summary": summary,
    }


def main() -> None:
    print(json.dumps(run_decay_sweep(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
