#!/usr/bin/env python3
"""Probe the untouched 20-bar breakout/breakdown boundary for Issue #57.

The v0.6 Phase-A changes currently soften the 50-bar structural no-break and
continuation boundaries. This diagnostic asks whether the separate 20-bar
breakout event still creates a material one-tick cliff.

No returns or PnL are evaluated here.
"""

from __future__ import annotations

import json

import numpy as np

from diagnose_v06_boundary_sensitivity import (
    PAIRS,
    PROBABILITY_COLUMNS,
    _atr_at,
    _counterfactual_pair,
    _load_pair,
    _row,
)
from generate_v06_price_only_core import load_v06_namespace
from price_only_core import compute_price_only


UP_PATH_FIELDS = (
    "range_break_up",
    "ma_cross_up",
    "recent_break_up",
    "breakout_mode_up",
    "range_cont_up",
    "breakout_score",
    "breakout_gate",
    "range_cont_up_gate",
    "markup_continuation_score",
    "breakout_markup_gate",
    "markup_cont_gate",
    "markup_gate",
    "prob_markup",
)
DOWN_PATH_FIELDS = (
    "range_break_dn",
    "ma_cross_dn",
    "recent_break_dn",
    "recent_range_break_dn",
    "breakdown_mode_dn",
    "range_cont_dn",
    "explicit_breakdown_score",
    "explicit_breakdown_gate",
    "range_cont_dn_gate",
    "markdown_continuation_score",
    "breakdown_markdown_gate",
    "markdown_cont_gate",
    "markdown_gate",
    "prob_markdown",
)


def _l1(left, right) -> float:
    a = np.nan_to_num(left[list(PROBABILITY_COLUMNS)].to_numpy(float), nan=0.0)
    b = np.nan_to_num(right[list(PROBABILITY_COLUMNS)].to_numpy(float), nan=0.0)
    return float(np.abs(a - b).sum())


def _path_pair(left, right, fields: tuple[str, ...]) -> dict[str, list[float | None]]:
    result: dict[str, list[float | None]] = {}
    for field in fields:
        pair: list[float | None] = []
        for row in (left, right):
            value = float(row[field])
            pair.append(value if np.isfinite(value) else None)
        result[field] = pair
    return result


def run_breakout20_sweep(target_index: int = 1300) -> dict[str, object]:
    if not 800 <= target_index <= 1439:
        raise ValueError("target_index must stay inside warmed-up old Development data")

    v06_compute = load_v06_namespace()["compute_price_only"]
    rows: list[dict[str, object]] = []

    for pair in PAIRS:
        frame = _load_pair(pair)
        atr_value = _atr_at(frame, target_index)
        epsilon = atr_value * 1e-4
        lookback20 = frame.iloc[target_index - 20 : target_index]
        lookback50 = frame.iloc[target_index - 50 : target_index]

        for side in ("low", "high"):
            if side == "high":
                boundary = float(lookback20["high"].max())
                boundary50 = float(lookback50["high"].max())
                event_field = "range_break_up"
                recent_field = "recent_break_up"
                continuation_field = "range_cont_up"
                path_fields = UP_PATH_FIELDS
            else:
                boundary = float(lookback20["low"].min())
                boundary50 = float(lookback50["low"].min())
                event_field = "range_break_dn"
                recent_field = "recent_break_dn"
                continuation_field = "range_cont_dn"
                path_fields = DOWN_PATH_FIELDS

            below, above = _counterfactual_pair(frame, target_index, boundary, epsilon)
            v05_below = _row(compute_price_only, below)
            v05_above = _row(compute_price_only, above)
            v06_below = _row(v06_compute, below)
            v06_above = _row(v06_compute, above)

            rows.append(
                {
                    "pair": pair,
                    "side": side,
                    "date": str(frame.loc[target_index, "date"]),
                    "atr20": atr_value,
                    "epsilon": epsilon,
                    "boundary20": boundary,
                    "boundary50": boundary50,
                    "distance_20_to_50_atr": abs(boundary - boundary50) / atr_value,
                    "event_below": float(v06_below[event_field]),
                    "event_above": float(v06_above[event_field]),
                    "recent_below": float(v06_below[recent_field]),
                    "recent_above": float(v06_above[recent_field]),
                    "continuation_below": float(v06_below[continuation_field]),
                    "continuation_above": float(v06_above[continuation_field]),
                    "v05_probability_l1_jump": _l1(v05_below, v05_above),
                    "v06_probability_l1_jump": _l1(v06_below, v06_above),
                    "v05_top": [int(v05_below["top_id"]), int(v05_above["top_id"])],
                    "v06_top": [int(v06_below["top_id"]), int(v06_above["top_id"])],
                    "v05_candidate": [
                        int(v05_below["candidate_display_id"]),
                        int(v05_above["candidate_display_id"]),
                    ],
                    "v06_candidate": [
                        int(v06_below["candidate_display_id"]),
                        int(v06_above["candidate_display_id"]),
                    ],
                    "v06_path": _path_pair(v06_below, v06_above, path_fields),
                }
            )

    toggled = [row for row in rows if row["event_below"] != row["event_above"]]
    isolated = [row for row in toggled if float(row["distance_20_to_50_atr"]) >= 0.25]
    worst = max(toggled, key=lambda row: float(row["v06_probability_l1_jump"])) if toggled else None
    return {
        "scope": "Issue #55 Development-era inputs only; 20-bar boundary counterfactual; no PnL",
        "target_index": target_index,
        "cases": rows,
        "worst_toggled_case": worst,
        "summary": {
            "case_count": len(rows),
            "event_toggle_cases": len(toggled),
            "event_toggle_isolated_from_50bar_band_cases": len(isolated),
            "median_v05_l1_all": float(np.median([row["v05_probability_l1_jump"] for row in rows])),
            "median_v06_l1_all": float(np.median([row["v06_probability_l1_jump"] for row in rows])),
            "median_v06_l1_toggled": (
                float(np.median([row["v06_probability_l1_jump"] for row in toggled])) if toggled else None
            ),
            "max_v06_l1_toggled": (
                float(max(row["v06_probability_l1_jump"] for row in toggled)) if toggled else None
            ),
        },
    }


def main() -> None:
    print(json.dumps(run_breakout20_sweep(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
