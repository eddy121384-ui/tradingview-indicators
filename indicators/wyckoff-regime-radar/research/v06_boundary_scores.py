#!/usr/bin/env python3
"""Continuous boundary primitives for Wyckoff Regime Radar v0.6 Phase A.

These functions intentionally change only boundary-sensitive price primitives
identified by Issue #55 / Issue #57 diagnostics. They do not add predictive
inputs and they are not calibrated to PnL.
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


def soft_above_range_score(
    close: np.ndarray | float,
    previous_high: np.ndarray | float,
    atr_values: np.ndarray | float,
    width_atr: float = SOFT_BOUNDARY_WIDTH_ATR,
) -> np.ndarray:
    """Continuous strength for trading above a prior structural high.

    This is the exact mirror complement of ``soft_no_break_high_score``:
    the structural boundary maps to 50, and a full-width move above it maps
    to 100 rather than creating a boolean 0/1 edge.
    """

    return 100.0 - soft_no_break_high_score(close, previous_high, atr_values, width_atr)


def soft_below_range_score(
    close: np.ndarray | float,
    previous_low: np.ndarray | float,
    atr_values: np.ndarray | float,
    width_atr: float = SOFT_BOUNDARY_WIDTH_ATR,
) -> np.ndarray:
    """Mirror-symmetric strength for trading below a prior structural low."""

    return 100.0 - soft_no_break_low_score(close, previous_low, atr_values, width_atr)


def soft_break_above_score(
    close: np.ndarray | float,
    previous_high: np.ndarray | float,
    atr_values: np.ndarray | float,
    width_atr: float = SOFT_BOUNDARY_WIDTH_ATR,
) -> np.ndarray:
    """One-sided continuous breakout evidence above a prior high.

    Unlike ``soft_above_range_score``, this is event-like evidence: being at or
    below the boundary contributes zero. Evidence then ramps linearly to 100 at
    ``width_atr`` ATR above the boundary. This keeps the old notion that a
    breakout requires clearing the level while removing the one-tick 0/1 cliff.
    """

    if width_atr <= 0.0:
        raise ValueError("width_atr must be positive")
    close_arr = np.asarray(close, dtype=float)
    boundary = np.asarray(previous_high, dtype=float)
    scale = _safe_scale(atr_values) * width_atr
    return _clamp_score(100.0 * ((close_arr - boundary) / scale))


def soft_break_below_score(
    close: np.ndarray | float,
    previous_low: np.ndarray | float,
    atr_values: np.ndarray | float,
    width_atr: float = SOFT_BOUNDARY_WIDTH_ATR,
) -> np.ndarray:
    """Mirror-symmetric one-sided breakdown evidence below a prior low."""

    if width_atr <= 0.0:
        raise ValueError("width_atr must be positive")
    close_arr = np.asarray(close, dtype=float)
    boundary = np.asarray(previous_low, dtype=float)
    scale = _safe_scale(atr_values) * width_atr
    return _clamp_score(100.0 * ((boundary - close_arr) / scale))


def soft_hold_strength(values: np.ndarray, bars: int) -> np.ndarray:
    """Continuous N-bar persistence strength using the weakest bar in the run.

    A two-bar hold is therefore only as strong as the weaker of the current and
    prior soft boundary scores. This preserves the intended persistence concept
    without a boolean ``barssince`` cliff at the structural boundary.
    """

    if bars <= 0:
        raise ValueError("bars must be positive")
    arr = np.asarray(values, dtype=float)
    out = np.full(arr.shape, np.nan, dtype=float)
    if bars == 1:
        return arr.copy()
    for index in range(bars - 1, len(arr)):
        window = arr[index - bars + 1 : index + 1]
        if np.isfinite(window).all():
            out[index] = float(np.min(window))
    return out
