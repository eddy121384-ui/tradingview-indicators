#!/usr/bin/env python3
"""Canonical v0.6 macro-regime mapping selected in Issue #57 Phase C.

The six Wyckoff stage scores remain available as substructure diagnostics. The
canonical product/research regime is four-state:

1 Accumulation family = Accumulation + Re-accumulation
2 Markup
3 Distribution family = Distribution + Re-distribution
4 Markdown

This module contains no predictive tuning and no PnL logic.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


SIX_TO_FOUR = {0: 0, 1: 1, 2: 2, 3: 1, 4: 3, 5: 4, 6: 3}
FOUR_STATE_NAMES = {
    0: "Neutral",
    1: "Accumulation family",
    2: "Markup",
    3: "Distribution family",
    4: "Markdown",
}


def map_six_id_to_four(values: np.ndarray | pd.Series) -> np.ndarray:
    arr = np.asarray(values, dtype=int)
    out = np.zeros_like(arr, dtype=int)
    for source, target in SIX_TO_FOUR.items():
        out[arr == source] = target
    unknown = ~np.isin(arr, list(SIX_TO_FOUR))
    if np.any(unknown):
        raise ValueError(f"unknown six-state ids: {sorted(set(arr[unknown].tolist()))}")
    return out


def aggregate_six_weights_to_four(outputs: pd.DataFrame) -> pd.DataFrame:
    """Aggregate six normalized stage weights into the four canonical regimes."""

    required = (
        "prob_acc",
        "prob_markup",
        "prob_reacc",
        "prob_dist",
        "prob_markdown",
        "prob_redist",
    )
    missing = [column for column in required if column not in outputs.columns]
    if missing:
        raise ValueError(f"missing six-state weights: {missing}")

    result = pd.DataFrame(index=outputs.index)
    result["regime_accumulation_family"] = outputs["prob_acc"] + outputs["prob_reacc"]
    result["regime_markup"] = outputs["prob_markup"]
    result["regime_distribution_family"] = outputs["prob_dist"] + outputs["prob_redist"]
    result["regime_markdown"] = outputs["prob_markdown"]
    return result


def attach_canonical_four_state(outputs: pd.DataFrame) -> pd.DataFrame:
    """Attach canonical IDs and four-state weights while retaining six-state fields."""

    if "formal_id" not in outputs.columns or "candidate_display_id" not in outputs.columns:
        raise ValueError("outputs must contain formal_id and candidate_display_id")
    result = outputs.copy()
    result["canonical_formal_id"] = map_six_id_to_four(result["formal_id"].fillna(0).to_numpy(int))
    result["canonical_candidate_display_id"] = map_six_id_to_four(
        result["candidate_display_id"].fillna(0).to_numpy(int)
    )
    weights = aggregate_six_weights_to_four(result)
    for column in weights.columns:
        result[column] = weights[column]
    return result
