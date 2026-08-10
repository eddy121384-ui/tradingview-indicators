#!/usr/bin/env python3
"""Decompose v0.6 Formal carry bars for Issue #57 Phase B.

The first persistence audit showed that confirmation delay itself is short and
stable, while Formal often persists with no strong candidate. This diagnostic
separates that carry into chaos, weak challenger, weak same-state support,
coexistence, and neutral/no-candidate cases. No model rule or PnL is changed.
"""

from __future__ import annotations

import json
from typing import Any

import numpy as np

from diagnose_v06_boundary_sensitivity import PAIRS, _load_pair
from generate_v06_price_only_core import load_v06_namespace


FOLLOW_WINDOWS = (5, 10)


def _stats(values: list[int]) -> dict[str, float | int | None]:
    if not values:
        return {"count": 0, "median": None, "p90": None, "max": None}
    arr = np.asarray(values, dtype=float)
    return {
        "count": len(values),
        "median": float(np.median(arr)),
        "p90": float(np.percentile(arr, 90)),
        "max": int(np.max(arr)),
    }


def _categorize(outputs) -> tuple[np.ndarray, np.ndarray]:
    candidate = outputs["candidate_id"].fillna(0).to_numpy(int)
    display = outputs["candidate_display_id"].fillna(0).to_numpy(int)
    formal = outputs["formal_id"].fillna(0).to_numpy(int)
    chaos = outputs["chaos"].fillna(False).to_numpy(bool)
    coexist = outputs["coexist"].fillna(False).to_numpy(bool)

    carry = (formal != 0) & (candidate == 0)
    category = np.full(len(outputs), "not_carry", dtype=object)
    challenger = np.zeros(len(outputs), dtype=int)

    for index in np.where(carry)[0]:
        if chaos[index]:
            category[index] = "chaos"
        elif display[index] != 0 and display[index] != formal[index]:
            category[index] = "weak_challenger"
            challenger[index] = display[index]
        elif display[index] == formal[index] and display[index] != 0:
            category[index] = "weak_same_state"
        elif coexist[index]:
            category[index] = "coexist_no_display"
        else:
            category[index] = "neutral_no_candidate"
    return category, challenger


def _category_run_lengths(category: np.ndarray, name: str) -> list[int]:
    lengths: list[int] = []
    start: int | None = None
    for index, value in enumerate(category):
        if value == name and start is None:
            start = index
        if start is not None and (value != name or index == len(category) - 1):
            end = index if value == name and index == len(category) - 1 else index - 1
            lengths.append(end - start + 1)
            start = None
    return lengths


def _weak_challenger_runs(category: np.ndarray, challenger: np.ndarray) -> list[tuple[int, int, int]]:
    runs: list[tuple[int, int, int]] = []
    start: int | None = None
    stage = 0
    for index in range(len(category) + 1):
        is_weak = index < len(category) and category[index] == "weak_challenger"
        current_stage = int(challenger[index]) if is_weak else 0
        if start is None and is_weak:
            start = index
            stage = current_stage
            continue
        if start is not None and (not is_weak or current_stage != stage):
            runs.append((start, index - 1, stage))
            start = index if is_weak else None
            stage = current_stage if is_weak else 0
    return runs


def analyze_pair(outputs) -> dict[str, Any]:
    formal = outputs["formal_id"].fillna(0).to_numpy(int)
    candidate = outputs["candidate_id"].fillna(0).to_numpy(int)
    category, challenger = _categorize(outputs)
    carry_mask = category != "not_carry"
    carry_bars = int(np.sum(carry_mask))

    categories = (
        "chaos",
        "weak_challenger",
        "weak_same_state",
        "coexist_no_display",
        "neutral_no_candidate",
    )
    category_summary: dict[str, Any] = {}
    for name in categories:
        count = int(np.sum(category == name))
        category_summary[name] = {
            "bars": count,
            "share_of_all_bars": float(count / len(outputs)) if len(outputs) else None,
            "share_of_carry_bars": float(count / carry_bars) if carry_bars else None,
            "run_length_bars": _stats(_category_run_lengths(category, name)),
        }

    weak_runs = _weak_challenger_runs(category, challenger)
    follow: dict[str, Any] = {}
    for window in FOLLOW_WINDOWS:
        eligible = 0
        formal_adopt = 0
        strong_adopt = 0
        long_runs = 0
        long_formal_adopt = 0
        for start, end, stage in weak_runs:
            stop = min(len(outputs) - 1, end + window)
            if end >= len(outputs) - 1:
                continue
            eligible += 1
            future_formal = formal[end + 1 : stop + 1]
            future_candidate = candidate[end + 1 : stop + 1]
            adopted_formal = bool(np.any(future_formal == stage))
            adopted_strong = bool(np.any(future_candidate == stage))
            formal_adopt += int(adopted_formal)
            strong_adopt += int(adopted_strong)
            if end - start + 1 >= 2:
                long_runs += 1
                long_formal_adopt += int(adopted_formal)
        follow[str(window)] = {
            "eligible_runs": eligible,
            "formal_adoption_count": formal_adopt,
            "formal_adoption_rate": (formal_adopt / eligible) if eligible else None,
            "strong_candidate_emergence_count": strong_adopt,
            "strong_candidate_emergence_rate": (strong_adopt / eligible) if eligible else None,
            "runs_length_ge_2": long_runs,
            "formal_adoption_rate_length_ge_2": (
                long_formal_adopt / long_runs if long_runs else None
            ),
        }

    return {
        "bars": len(outputs),
        "formal_carry_bars": carry_bars,
        "formal_carry_share": float(carry_bars / len(outputs)) if len(outputs) else None,
        "categories": category_summary,
        "weak_challenger_runs": _stats([end - start + 1 for start, end, _ in weak_runs]),
        "weak_challenger_followthrough": follow,
    }


def run_carry_challenger_audit() -> dict[str, Any]:
    compute = load_v06_namespace()["compute_price_only"]
    rows: list[dict[str, Any]] = []
    for pair in PAIRS:
        outputs = compute(_load_pair(pair))
        rows.append({"pair": pair, **analyze_pair(outputs)})

    categories = (
        "chaos",
        "weak_challenger",
        "weak_same_state",
        "coexist_no_display",
        "neutral_no_candidate",
    )
    aggregate_categories: dict[str, Any] = {}
    total_carry = sum(int(row["formal_carry_bars"]) for row in rows)
    total_bars = sum(int(row["bars"]) for row in rows)
    for name in categories:
        bars = sum(int(row["categories"][name]["bars"]) for row in rows)
        aggregate_categories[name] = {
            "bars": bars,
            "share_of_all_bars": bars / total_bars if total_bars else None,
            "share_of_carry_bars": bars / total_carry if total_carry else None,
        }

    aggregate_follow: dict[str, Any] = {}
    for window in FOLLOW_WINDOWS:
        key = str(window)
        eligible = sum(int(row["weak_challenger_followthrough"][key]["eligible_runs"]) for row in rows)
        adopted = sum(int(row["weak_challenger_followthrough"][key]["formal_adoption_count"]) for row in rows)
        strong = sum(
            int(row["weak_challenger_followthrough"][key]["strong_candidate_emergence_count"])
            for row in rows
        )
        long_runs = sum(int(row["weak_challenger_followthrough"][key]["runs_length_ge_2"]) for row in rows)
        long_adopt_rates_weighted_num = sum(
            int(row["weak_challenger_followthrough"][key]["formal_adoption_rate_length_ge_2"] * row["weak_challenger_followthrough"][key]["runs_length_ge_2"])
            if row["weak_challenger_followthrough"][key]["formal_adoption_rate_length_ge_2"] is not None
            else 0
            for row in rows
        )
        aggregate_follow[key] = {
            "eligible_runs": eligible,
            "formal_adoption_rate": adopted / eligible if eligible else None,
            "strong_candidate_emergence_rate": strong / eligible if eligible else None,
            "runs_length_ge_2": long_runs,
            "formal_adoption_rate_length_ge_2": (
                long_adopt_rates_weighted_num / long_runs if long_runs else None
            ),
        }

    return {
        "issue": 57,
        "phase": "B-carry-decomposition",
        "scope": "Already-observed Issue #55 FX history only; internal state-machine diagnosis; no PnL.",
        "rows": rows,
        "aggregate": {
            "bars": total_bars,
            "formal_carry_bars": total_carry,
            "formal_carry_share": total_carry / total_bars if total_bars else None,
            "categories": aggregate_categories,
            "weak_challenger_followthrough": aggregate_follow,
        },
    }


def main() -> None:
    print(json.dumps(run_carry_challenger_audit(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
