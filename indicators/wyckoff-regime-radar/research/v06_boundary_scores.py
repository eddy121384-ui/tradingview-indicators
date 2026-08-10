#!/usr/bin/env python3
"""Continuous boundary primitives for Wyckoff Regime Radar v0.6 Phase A.

These functions intentionally change only the binary no-break tests identified in
Issue #55.  They do not add predictive inputs and they are not calibrated to PnL.
"""

from __future__ import annotations

import numpy as np


SOFT_BOUNDARY_WIDTH_ATR = 0.25


def _safe_scale(atr_values: np.ndarray | float) -> np.ndarray:
    atr_arr = np.asarray(atr_values, dtype=float)
    return np.where(np.isfinite(atr_arr) & (atr_arr > 0.0), atr_arr, np.nan)


def _clamp_score(values: np.ndarray) -> np.ndarray:
    return np.clip(values, 0.0, 100.0)


def soft_no_break_low_score(
    close: np.ndarray | float,
    previous_low: np.ndarray | float,
    atr_values: np.ndarray | float,
    width_atr: float = SOFT_BOUNDARY_WIDTH_ATR,
) -> np.ndarray:
    """Return a continuous score for holding above a previous structural low.

    Score geometry is deliberately simple and symmetric:
    - previous_low - width_atr*ATR -> 0
    - previous_low                 -> 50
    - previous_low + width_atr*ATR -> 100

    Values outside the transition band saturate at 0/100.
    """

    if width_atr <= 0.0:
        raise ValueError("width_atr must be positive")
    close_arr = np.asarray(close, dtype=float)
    boundary = np.asarray(previous_low, dtype=float)
    scale = _safe_scale(atr_values) * width_atr
    score = 50.0 + 50.0 * ((close_arr - boundary) / scale)
    return _clamp_score(score)


def soft_no_break_high_score(
    close: np.ndarray | float,
    previous_high: np.ndarray | float,
    atr_values: np.ndarray | float,
    width_atr: float = SOFT_BOUNDARY_WIDTH_ATR,
) -> np.ndarray:
    """Mirror-symmetric score for holding below a previous structural high."""

    if width_atr <= 0.0:
        raise ValueError("width_atr must be positive")
    close_arr = np.asarray(close, dtype=float)
    boundary = np.asarray(previous_high, dtype=float)
    scale = _safe_scale(atr_values) * width_atr
    score = 50.0 + 50.0 * ((boundary - close_arr) / scale)
    return _clamp_score(score)
