#!/usr/bin/env python3
"""Counterfactual continuity sweep for Issue #57 Phase A.

This is a robustness diagnostic, not a return backtest.  It uses only the already
burned/development-era Issue #55 fixtures and moves one close infinitesimally
across a prior 50-bar structural extreme while keeping the rest of the prefix
fixed.  The purpose is to measure local output discontinuity, not profitability.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from generate_v06_price_only_core import load_v06_namespace
from pine_math import atr
from price_only_core import compute_price_only


HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
MANIFEST_PATH = DATA_DIR / "issue-55-static-fx-canonical-manifest.json"
PAIRS = ("EURUSD", "USDJPY", "GBPUSD", "AUDUSD")
PROBABILITY_COLUMNS = (
    "prob_acc",
    "prob_markup",
    "prob_reacc",
    "prob_dist",
    "prob_markdown",
    "prob_redist",
)


def _load_pair(pair: str) -> pd.DataFrame:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    frozen_rel = manifest["pairs"][pair]["frozen_file"]
    frame = pd.read_csv(DATA_DIR / frozen_rel)
    return frame.rename(columns={column: column.lower() for column in frame.columns})


def _atr_at(frame: pd.DataFrame, index: int) -> float:
    values = atr(
        frame["high"].to_numpy(float),
        frame["low"].to_numpy(float),
        frame["close"].to_numpy(float),
        20,
    )
    value = float(values[index])
    if not np.isfinite(value) or value <= 0.0:
        raise RuntimeError(f"ATR unavailable at index {index}")
    return value


def _counterfactual_pair(
    frame: pd.DataFrame,
    index: int,
    boundary: float,
    epsilon: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    prefix = frame.iloc[: index + 1].copy().reset_index(drop=True)
    below = prefix.copy()
    above = prefix.copy()

    open_value = float(prefix.loc[index, "open"])
    original_high = float(prefix.loc[index, "high"])
    original_low = float(prefix.loc[index, "low"])
    common_high = max(original_high, open_value, boundary + epsilon)
    common_low = min(original_low, open_value, boundary - epsilon)

    for variant in (below, above):
        variant.loc[index, "high"] = common_high
        variant.loc[index, "low"] = common_low

    below.loc[index, "close"] = boundary - epsilon
    above.loc[index, "close"] = boundary + epsilon
    return below, above


def _row(compute: Callable[[pd.DataFrame], pd.DataFrame], frame: pd.DataFrame) -> pd.Series:
    return compute(frame).iloc[-1]


def _probability_l1(left: pd.Series, right: pd.Series) -> float:
    a = np.nan_to_num(left[list(PROBABILITY_COLUMNS)].to_numpy(float), nan=0.0)
    b = np.nan_to_num(right[list(PROBABILITY_COLUMNS)].to_numpy(float), nan=0.0)
    return float(np.abs(a - b).sum())


def _dist_markdown_jump(left: pd.Series, right: pd.Series) -> float:
    values = []
    for name in ("prob_dist", "prob_markdown"):
        a = float(left[name]) if np.isfinite(left[name]) else 0.0
        b = float(right[name]) if np.isfinite(right[name]) else 0.0
        values.append(abs(a - b))
    return float(sum(values))


def _case(
    pair: str,
    side: str,
    frame: pd.DataFrame,
    index: int,
    v06_compute: Callable[[pd.DataFrame], pd.DataFrame],
) -> dict[str, object]:
    lookback = frame.iloc[index - 50 : index]
    if len(lookback) != 50:
        raise RuntimeError("Need exactly 50 prior observations")
    if side == "low":
        boundary = float(lookback["low"].min())
    elif side == "high":
        boundary = float(lookback["high"].max())
    else:
        raise ValueError(side)

    atr_value = _atr_at(frame, index)
    epsilon = atr_value * 1e-4
    below, above = _counterfactual_pair(frame, index, boundary, epsilon)

    v05_below = _row(compute_price_only, below)
    v05_above = _row(compute_price_only, above)
    v06_below = _row(v06_compute, below)
    v06_above = _row(v06_compute, above)

    if side == "low":
        soft_primitive_jump = abs(
            float(v06_above["no_break_low_score"]) - float(v06_below["no_break_low_score"])
        )
    else:
        soft_primitive_jump = abs(
            float(v06_above["no_break_high_score"]) - float(v06_below["no_break_high_score"])
        )

    date_value = frame.loc[index, "date"] if "date" in frame.columns else index
    return {
        "pair": pair,
        "side": side,
        "index": index,
        "date": str(date_value),
        "boundary": boundary,
        "atr20": atr_value,
        "epsilon": epsilon,
        "epsilon_atr": epsilon / atr_value,
        "v05_hard_primitive_jump": 100.0,
        "v06_soft_primitive_jump": soft_primitive_jump,
        "v05_probability_l1_jump": _probability_l1(v05_below, v05_above),
        "v06_probability_l1_jump": _probability_l1(v06_below, v06_above),
        "v05_dist_markdown_jump": _dist_markdown_jump(v05_below, v05_above),
        "v06_dist_markdown_jump": _dist_markdown_jump(v06_below, v06_above),
        "v05_top_id_below": int(v05_below["top_id"]),
        "v05_top_id_above": int(v05_above["top_id"]),
        "v06_top_id_below": int(v06_below["top_id"]),
        "v06_top_id_above": int(v06_above["top_id"]),
        "v05_candidate_below": int(v05_below["candidate_display_id"]),
        "v05_candidate_above": int(v05_above["candidate_display_id"]),
        "v06_candidate_below": int(v06_below["candidate_display_id"]),
        "v06_candidate_above": int(v06_above["candidate_display_id"]),
    }


def run_sweep(target_index: int = 1300) -> dict[str, object]:
    # 1300 lies strictly inside the old Development partition (0..1439).
    if not 800 <= target_index <= 1439:
        raise ValueError("target_index must stay inside warmed-up old Development data")

    namespace = load_v06_namespace()
    v06_compute = namespace["compute_price_only"]
    rows = []
    for pair in PAIRS:
        frame = _load_pair(pair)
        for side in ("low", "high"):
            rows.append(_case(pair, side, frame, target_index, v06_compute))

    hard_l1 = np.array([float(row["v05_probability_l1_jump"]) for row in rows])
    soft_l1 = np.array([float(row["v06_probability_l1_jump"]) for row in rows])
    hard_dm = np.array([float(row["v05_dist_markdown_jump"]) for row in rows])
    soft_dm = np.array([float(row["v06_dist_markdown_jump"]) for row in rows])
    primitive = np.array([float(row["v06_soft_primitive_jump"]) for row in rows])

    return {
        "scope": "Issue #55 Development-era frozen inputs only; structural counterfactual, not PnL",
        "target_index": target_index,
        "cases": rows,
        "summary": {
            "case_count": len(rows),
            "v05_hard_primitive_jump": 100.0,
            "median_v06_soft_primitive_jump": float(np.median(primitive)),
            "median_v05_probability_l1_jump": float(np.median(hard_l1)),
            "median_v06_probability_l1_jump": float(np.median(soft_l1)),
            "median_v05_dist_markdown_jump": float(np.median(hard_dm)),
            "median_v06_dist_markdown_jump": float(np.median(soft_dm)),
            "v06_probability_jump_lower_cases": int(np.sum(soft_l1 < hard_l1)),
            "v06_probability_jump_equal_cases": int(np.sum(np.isclose(soft_l1, hard_l1))),
            "v06_probability_jump_higher_cases": int(np.sum(soft_l1 > hard_l1)),
        },
    }


def main() -> None:
    print(json.dumps(run_sweep(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
