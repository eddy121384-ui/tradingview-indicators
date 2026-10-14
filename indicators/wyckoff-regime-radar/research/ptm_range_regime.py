#!/usr/bin/env python3
"""Issue #185 -- ex-ante (pre-decision) trading-range descriptor.

WHY THIS MODULE EXISTS
----------------------
The prereg previously stratified "wide box" episodes using ``spread / w`` where
``w = (Q90 - Q10) / RADIUS_DIVISOR``.  That ratio is identically
``RADIUS_DIVISOR`` (= 20) for every valid reference, so it discriminated
**nothing** -- it was an algebraic identity masquerading as a classifier.  The
rest of that criterion selected on ``R <= 1`` plus an unfixed v0.2 claim, which
describes *sparse claimed territory*, not a wide trading range.  And
``sustained_escape()`` in the analyzer reads the path AFTER the probe, so it is
a valid retrospective OUTCOME label and may never define a live decision cohort.

This module replaces both with a descriptor built ONLY from bars strictly before
the probe bar:

    width_atr = (Q90 - Q10) of the pre-probe reference closes
                ------------------------------------------------
                ATR over the last ``ATR_WINDOW_BARS`` pre-probe bars

    reversals = observed confirmed reference cycles in the same pre-probe window
                (supplied by the caller from the frozen reference construction)

``width_atr`` asks "how wide was the range this probe is emerging from, measured
in the instrument's own recent true range?".  A 4-ATR reference is a tight
consolidation; a 40-ATR reference is a large trading range.  The ratio is
scale-free, so it is comparable across yields, FX and equity indices.

UNITS, DENOMINATORS AND ZERO-DATA RULES
---------------------------------------
* Numerator: ``Q90 - Q10`` of the pre-probe **close** series, in the same price
  coordinate as the input bars.  This is the same span the frozen reference
  uses, so the descriptor and the reference cannot drift apart.
* Denominator: mean true range over the last ``ATR_WINDOW_BARS`` pre-probe bars,
  where true range is the usual ``max(h-l, |h-prev_c|, |l-prev_c|)``.
* ``ATR_WINDOW_BARS = 14`` is a conventional, predeclared window; it is a
  property of the DESCRIPTOR, not a tuned parameter.
* The descriptor is reported ``UNAVAILABLE`` -- never silently binned -- when:
    - fewer than ``ATR_WINDOW_BARS + 1`` pre-probe bars are available;
    - any input OHLC value is missing or non-finite;
    - the pre-probe ATR is not strictly positive;
    - the reference span is not strictly positive.
  An ``UNAVAILABLE`` episode has no stratum, and the report must show the count.

BIN BOUNDARIES
--------------
The width tertiles :data:`WIDTH_ATR_EDGES` were frozen from the **real** Issue
#76 B3 cohort using this feature ONLY -- no return, PnL or MFE was computed to
choose them (see ``analyze_issue185_real_cohort.py``).  Freezing boundaries on
the feature distribution is legitimate precisely because the feature is
backward-looking and outcome-free; freezing them on returns would not be.

CAUSALITY
---------
``range_regime_at`` slices ``bars[anchor_index - reference_bars:anchor_index]``
and never reads ``bars[anchor_index]`` or anything after it.  Appending arbitrary
future bars cannot change the result, and the test suite asserts exactly that.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from ptm_territory import PTMConfig

# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------
STATUS_OK = "OK"
STATUS_UNAVAILABLE = "UNAVAILABLE"

# ---------------------------------------------------------------------------
# Width bins.  ``WIDE`` is the "large trading range" stratum the study cares
# about; ``NARROW`` is the tight-consolidation comparison.
# ---------------------------------------------------------------------------
WIDTH_BIN_NARROW = "NARROW"
WIDTH_BIN_MID = "MID"
WIDTH_BIN_WIDE = "WIDE"
WIDTH_BINS = (WIDTH_BIN_NARROW, WIDTH_BIN_MID, WIDTH_BIN_WIDE)

# ---------------------------------------------------------------------------
# Reversal bins: an integer count, so the bins are predeclared by construction
# and cannot be tuned.
# ---------------------------------------------------------------------------
REVERSAL_BIN_NONE = "REV_0"
REVERSAL_BIN_ONE = "REV_1"
REVERSAL_BIN_MANY = "REV_2PLUS"
REVERSAL_BINS = (REVERSAL_BIN_NONE, REVERSAL_BIN_ONE, REVERSAL_BIN_MANY)

#: Conventional ATR lookback for the descriptor.  Predeclared, not tuned.
ATR_WINDOW_BARS = 14

#: Pre-probe reference length.  Tied to the frozen PTM reference window so the
#: description and the territory reference describe the same stretch of history.
REFERENCE_BARS = PTMConfig().reference_bars  # 120

#: FROZEN feature-only tertile edges for ``width_atr``, computed over the real
#: Issue #76 B3 cohort (661 of 997 events with a valid contiguous pre-probe
#: reference window) by ``analyze_issue185_real_cohort.py`` with NO outcome
#: information.  ``NARROW`` = below the first edge, ``WIDE`` = at/above the
#: second, ``MID`` = between.  Do not re-derive these from outcomes.
WIDTH_ATR_EDGES = (7.3677, 11.9931)


@dataclass(frozen=True)
class RangeRegimeFeatures:
    """One episode's pre-decision range description.  All fields backward-looking."""

    status: str
    reason: str
    width_atr: float | None
    reversals: int | None
    reversal_bin: str | None
    atr_pre: float | None
    ref_span: float | None
    n_pre_bars: int
    width_bin: str | None

    @property
    def available(self) -> bool:
        return self.status == STATUS_OK

    def as_row(self) -> dict:
        return {
            "range_status": self.status,
            "range_reason": self.reason,
            "width_atr": self.width_atr,
            "width_bin": self.width_bin,
            "reversals": self.reversals,
            "reversal_bin": self.reversal_bin,
            "atr_pre": self.atr_pre,
            "ref_span": self.ref_span,
            "n_pre_bars": self.n_pre_bars,
        }


def _unavailable(reason: str, *, n_pre_bars: int,
                 reversals: int | None = None) -> RangeRegimeFeatures:
    return RangeRegimeFeatures(
        status=STATUS_UNAVAILABLE, reason=reason, width_atr=None,
        reversals=reversals, reversal_bin=None, atr_pre=None, ref_span=None,
        n_pre_bars=n_pre_bars, width_bin=None)


def quantile(values: Sequence[float], q: float) -> float:
    """Linear-interpolation quantile.  No numpy dependency; deterministic."""
    s = sorted(values)
    if not s:
        raise ValueError("no values")
    if not 0.0 <= q <= 1.0:
        raise ValueError(f"q must be in [0, 1], got {q}")
    pos = q * (len(s) - 1)
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(s) - 1)
    frac = pos - lo
    return s[lo] * (1.0 - frac) + s[hi] * frac


def assign_width_bin(width_atr: float, edges: tuple = WIDTH_ATR_EDGES) -> str:
    """Map a width to its predeclared tertile bin."""
    if len(edges) != 2:
        raise ValueError(f"expected 2 tertile edges, got {len(edges)}")
    lo, hi = float(edges[0]), float(edges[1])
    if not lo <= hi:
        raise ValueError(f"edges must be non-decreasing, got {edges}")
    if width_atr < lo:
        return WIDTH_BIN_NARROW
    if width_atr >= hi:
        return WIDTH_BIN_WIDE
    return WIDTH_BIN_MID


def assign_reversal_bin(reversals: int) -> str:
    """Map a confirmed-cycle count to its predeclared integer bin."""
    if reversals < 0:
        raise ValueError(f"reversals must be >= 0, got {reversals}")
    if reversals == 0:
        return REVERSAL_BIN_NONE
    if reversals == 1:
        return REVERSAL_BIN_ONE
    return REVERSAL_BIN_MANY


def true_range_bars(highs: Sequence[float], lows: Sequence[float],
                    closes: Sequence[float]) -> list[float]:
    """Per-bar true range.  ``bars[0]`` has no predecessor, so it is skipped."""
    n = len(highs)
    if not (n == len(lows) == len(closes)):
        raise ValueError("high/low/close must be the same length")
    out = []
    for k in range(1, n):
        prev_c = closes[k - 1]
        out.append(max(highs[k] - lows[k], abs(highs[k] - prev_c),
                       abs(lows[k] - prev_c)))
    return out


def range_regime_pre_bars(
        pre_bars: Sequence[tuple[float, float, float]], *,
        atr_window: int = ATR_WINDOW_BARS,
        reference_cycle_count: int | None = None,
) -> RangeRegimeFeatures:
    """Descriptor from a bar window that is ALREADY strictly pre-probe.

    ``pre_bars`` items are ``(high, low, close)``.  The caller is responsible
    for having excluded the probe bar and everything after it; use
    :func:`range_regime_at` when starting from a full series.
    """
    if atr_window < 2:
        raise ValueError(f"atr_window must be >= 2, got {atr_window}")
    n = len(pre_bars)
    reversals = reference_cycle_count
    reversal_bin = (assign_reversal_bin(reversals)
                    if reversals is not None else None)

    if n < atr_window + 1:
        return _unavailable(
            f"insufficient pre-probe history: {n} bar(s), need at least "
            f"{atr_window + 1}", n_pre_bars=n, reversals=reversals)

    highs, lows, closes = [], [], []
    gaps = 0
    for bar in pre_bars:
        h, l, c = (float(bar[0]), float(bar[1]), float(bar[2]))
        if not math.isfinite(c):
            return _unavailable("non-finite pre-probe close", n_pre_bars=n,
                                reversals=reversals)
        if not (math.isfinite(h) and math.isfinite(l)):
            # The parent's reconstruct() marks the first bar of every contiguous
            # run with NaN high/low and RESETS the close coordinate to 0.  A
            # window containing such a bar mixes two price coordinates, so the
            # span and the ATR would both be meaningless.
            gaps += 1
        highs.append(h)
        lows.append(l)
        closes.append(c)

    if gaps:
        return _unavailable(
            f"pre-probe window spans {gaps} coordinate reset(s): the closes do "
            "not share one price coordinate, so neither the reference span nor "
            "the ATR is meaningful; a contiguous reference window is required",
            n_pre_bars=n, reversals=reversals)

    span = quantile(closes, 0.9) - quantile(closes, 0.1)
    if not span > 0.0:
        return _unavailable(
            f"degenerate pre-probe reference span ({span!r} <= 0)",
            n_pre_bars=n, reversals=reversals)

    atr = sum(true_range_bars(highs, lows, closes)[-atr_window:]) / float(atr_window)
    if not atr > 0.0:
        return _unavailable(f"non-positive pre-probe ATR ({atr!r})",
                            n_pre_bars=n, reversals=reversals)

    width_atr = span / atr
    if not math.isfinite(width_atr):
        return _unavailable("non-finite width_atr", n_pre_bars=n,
                            reversals=reversals)

    return RangeRegimeFeatures(
        status=STATUS_OK, reason="pre-probe range descriptor available",
        width_atr=width_atr, reversals=reversals, reversal_bin=reversal_bin,
        atr_pre=atr, ref_span=span, n_pre_bars=n,
        width_bin=assign_width_bin(width_atr))


def range_regime_at(
        bars: Sequence[tuple[float, float, float]], anchor_index: int, *,
        atr_window: int = ATR_WINDOW_BARS,
        reference_bars: int = REFERENCE_BARS,
        reference_cycle_count: int | None = None,
) -> RangeRegimeFeatures:
    """Descriptor for the probe at ``anchor_index``.

    Reads ``bars[anchor_index - reference_bars:anchor_index]`` and nothing else.
    ``bars[anchor_index]`` and every later bar are ignored, so the result cannot
    depend on the future path.
    """
    if anchor_index < 0:
        raise ValueError(f"anchor_index must be >= 0, got {anchor_index}")
    if reference_bars < 1:
        raise ValueError(f"reference_bars must be >= 1, got {reference_bars}")
    start = max(0, anchor_index - reference_bars)
    return range_regime_pre_bars(
        bars[start:anchor_index], atr_window=atr_window,
        reference_cycle_count=reference_cycle_count)
