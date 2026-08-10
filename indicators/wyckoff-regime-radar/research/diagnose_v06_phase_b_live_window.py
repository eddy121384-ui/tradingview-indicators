#!/usr/bin/env python3
"""Warm-up-excluded Phase-B persistence audit for Issue #57.

Earlier persistence reports intentionally preserved raw full-history diagnostics,
but their Neutral episode statistics include the long indicator warm-up. This
report starts at the first bar with a positive six-stage top weight and should be
used for the Phase-B engineering choice.
"""

from __future__ import annotations

import json
from typing import Any

import numpy as np

from diagnose_v06_boundary_sensitivity import PAIRS, _load_pair
from diagnose_v06_carry_challengers import analyze_pair
from diagnose_v06_phase_b_decay_sweep import MULTIPLIERS, _summary, simulate_stale_decay
from diagnose_v06_phase_b_persistence_candidate import _analyze
from generate_v06_price_only_core import load_v06_namespace
from price_only_core import PriceOnlyConfig
from v06_live_window import live_window


def _aggregate_carry(rows: list[dict[str, Any]]) -> dict[str, Any]:
    categories = (
        "chaos",
        "weak_challenger",
        "weak_same_state",
        "coexist_no_display",
        "neutral_no_candidate",
    )
    total_bars = sum(int(row["bars"]) for row in rows)
    total_carry = sum(int(row["formal_carry_bars"]) for row in rows)
    category_summary: dict[str, Any] = {}
    for name in categories:
        bars = sum(int(row["categories"][name]["bars"]) for row in rows)
        category_summary[name] = {
            "bars": bars,
            "share_of_all_live_bars": bars / total_bars if total_bars else None,
            "share_of_live_carry_bars": bars / total_carry if total_carry else None,
        }

    follow: dict[str, Any] = {}
    for window in ("5", "10"):
        eligible = sum(int(row["weak_challenger_followthrough"][window]["eligible_runs"]) for row in rows)
        formal_adopt = sum(
            int(row["weak_challenger_followthrough"][window]["formal_adoption_count"]) for row in rows
        )
        strong = sum(
            int(row["weak_challenger_followthrough"][window]["strong_candidate_emergence_count"])
            for row in rows
        )
        follow[window] = {
            "eligible_runs": eligible,
            "formal_adoption_rate": formal_adopt / eligible if eligible else None,
            "strong_candidate_emergence_rate": strong / eligible if eligible else None,
        }

    return {
        "live_bars": total_bars,
        "formal_carry_bars": total_carry,
        "formal_carry_share": total_carry / total_bars if total_bars else None,
        "categories": category_summary,
        "weak_challenger_followthrough": follow,
    }


def run_live_window_audit() -> dict[str, Any]:
    compute = load_v06_namespace()["compute_price_only"]
    persistence_rows: list[dict[str, Any]] = []
    carry_rows: list[dict[str, Any]] = []
    live_metadata: list[dict[str, Any]] = []

    for pair in PAIRS:
        full = compute(_load_pair(pair))
        live, meta = live_window(full)
        live_metadata.append({"pair": pair, **meta})
        persistence_rows.append({"pair": pair, "engine": "phase_a", **_analyze(live, phase_b=False)})
        carry_rows.append({"pair": pair, **analyze_pair(live)})

        for multiplier in MULTIPLIERS:
            simulated_full = simulate_stale_decay(full, multiplier)
            simulated_live, simulated_meta = live_window(simulated_full)
            if simulated_meta["live_start_index"] != meta["live_start_index"]:
                raise RuntimeError(f"live window moved under persistence-only simulation for {pair}")
            persistence_rows.append(
                {
                    "pair": pair,
                    "engine": f"stale_decay_{multiplier}x",
                    "multiplier": multiplier,
                    **_analyze(simulated_live, phase_b=True),
                }
            )

    summary: dict[str, Any] = {}
    engines = ("phase_a",) + tuple(f"stale_decay_{m}x" for m in MULTIPLIERS)
    for engine in engines:
        summary[engine] = _summary([row for row in persistence_rows if row["engine"] == engine])

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
        row["additional_formal_switches"] = int(row["total_formal_switches"]) - int(
            baseline["total_formal_switches"]
        )
        row["additional_into_zero_transitions"] = int(row["total_into_zero_transitions"]) - int(
            baseline["total_into_zero_transitions"]
        )

    return {
        "issue": 57,
        "phase": "B-live-window",
        "scope": (
            "Burned Issue #55 FX history only, trimmed to first top_value > 0 per pair. "
            "Engineering persistence comparison only; no PnL or independent OOS claim."
        ),
        "live_windows": live_metadata,
        "confirm_bars": PriceOnlyConfig().confirm_bars,
        "multipliers": list(MULTIPLIERS),
        "persistence_rows": persistence_rows,
        "carry_rows": carry_rows,
        "phase_a_carry_decomposition": _aggregate_carry(carry_rows),
        "summary": summary,
        "supersedes_for_phase_b_choice": [
            "issue-57-phase-b-persistence-audit.md neutral statistics",
            "issue-57-phase-b-decay-horizon-sweep.md neutral statistics",
        ],
    }


def main() -> None:
    print(json.dumps(run_live_window_audit(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
