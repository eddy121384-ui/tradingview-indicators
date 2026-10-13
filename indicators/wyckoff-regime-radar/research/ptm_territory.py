"""Price Territory Memory (PTM) v0.2 -- independent engineering prototype.

Issue: eddy121384-ui/tradingview-indicators#185
Design authority: Sophira PTM design proposal v0.1 (#6117440344) and the
v0.2 synthetic design review (#6117510142).  v0.2 supersedes the v0.1
**close-only** historical territory-touch calculation with a frozen
**OHLC bar-range** touch calculation.

This module is an INDEPENDENT engineering implementation written from the
issue text.  It is not a byte-level reproduction of Sophira's prototype and
it carries no empirical claim.  It contains:

* a frozen, causal reference builder (120 completed pre-probe OHLC bars);
* zone radius ``w = (Q90(close_ref) - Q10(close_ref)) / 20``;
* query-centred fuzzy inner band ``[P-w, P+w]`` and outer band ``[P-2w, P+2w]``;
* historical revisit *episodes* ``R`` (arming / re-arming on the outer band);
* historical touch *occupancy* ``O`` (share of reference bars touching the
  inner band) -- reported separately from ``R``, never fused into one score;
* immediately observable novelty ``N = 1 / (1 + R)``;
* acceptance trace over at most the last 3 post-anchor known closes with
  explicit evidence maturity, live from the first known close;
* signed frontier progress versus the frozen historical extreme (context
  only, NOT a required breakout gate);
* separate stagnation diagnostics (the stagnation problem is explicitly
  NOT solved by this design);
* fail-closed data-validity states, so no "new territory" claim is emitted
  without a valid price scale and a valid reference.

Hard boundaries honoured here: no Pine, no production code, no strategy
sizing rule, no historical outcome study, no OOS5 contact.

Design-frozen constants are module level and are echoed into every result so
that an artifact can never be silently re-interpreted under a different
configuration.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable, Sequence

import numpy as np

# ---------------------------------------------------------------------------
# Design-frozen constants (candidates from the design note, NOT tuned values)
# ---------------------------------------------------------------------------

REFERENCE_BARS = 120
QUANTILE_LOW = 0.10
QUANTILE_HIGH = 0.90
RADIUS_DIVISOR = 20.0
OUTER_BAND_MULTIPLIER = 2.0
ACCEPTANCE_WINDOW = 3

# Descriptive stagnation-diagnostic constants.  These are NOT trading
# thresholds and they are NOT validated; see KNOWN_DEFECTS in the finding doc.
STALL_RANGE_FRACTION_W = 0.5
STALL_PROGRESS_FRACTION_W = 0.5
STALL_MIN_BARS = 10

# Descriptive suspect-scale-break screen (split / futures roll / unit change).
# 1.5 only catches gross unit discontinuities; see the finding doc for the
# documented false positive and false negative.
SUSPECT_SCALE_BREAK_FACTOR = 1.5

# ---------------------------------------------------------------------------
# A1 -- reference adequacy guards (pre-outcome fixed safety thresholds)
# ---------------------------------------------------------------------------
#
# These are SAFETY thresholds, not trading thresholds.  They answer one
# question only: "does the frozen 120-bar window actually contain evidence of
# a repeated price region, or could it be one leg of a much longer structure
# that this window cannot see?"  They were fixed BEFORE any market-outcome
# work, and they are NOT selected on returns.  Derivation basis (synthetic
# geometry only, see the finding doc section 6.F):
#
# * A confirmed swing must traverse at least half of the inter-decile close
#   span, so 1-cent noise cannot manufacture a "round trip".
# * At least one complete out-and-back (two confirmed swings) must be present.
# * At least half of the envelope must have been observed as occupied, and no
#   single unobserved hole may exceed a quarter of the envelope.  A sparse
#   download and a rolled/teleporting series both fail here.
#
# NOTE the standing limitation: 120 bars cannot reveal what happened before
# bar 0 of the window.  These guards can only report "insufficient evidence";
# they never claim that the longer history WAS a box.
CYCLE_SWING_FRACTION = 0.5
MIN_REFERENCE_CYCLES = 1.0
MIN_ENVELOPE_COVERED_FRACTION = 0.5
MAX_UNOBSERVED_GAP_FRACTION = 0.25

# ---------------------------------------------------------------------------
# A3 -- price-scale stability guard (pre-outcome fixed safety threshold)
# ---------------------------------------------------------------------------
#
# ``w`` is measured in price units, so a reference window that mixes price
# scales (a regime spike, an unadjusted split, a contract roll, a unit change)
# can produce a band far wider than the instrument's real price quantum.
# ``w / |reference scale|`` makes that ratio dimensionless and comparable
# across instruments quoting in different units.
#
# MAX_W_OVER_SCALE = 0.05 is exactly equivalent to "the inter-decile close
# range must not exceed 100% of the reference price level", because
# ``w = span / RADIUS_DIVISOR`` and ``20 * 0.05 = 1.0``.
MAX_W_OVER_SCALE = 0.05

# Descriptive novelty taxonomy.  Purely a reporting label; no trading meaning.
NOVELTY_CLASS_UNVISITED = "UNVISITED"
NOVELTY_CLASS_SPARSE = "SPARSE"
NOVELTY_CLASS_REVISITED = "REVISITED"
NOVELTY_CLASS_HEAVILY_REVISITED = "HEAVILY_REVISITED"

# Data-validity states.
VALIDITY_OK = "OK"
VALIDITY_UNKNOWN_INSUFFICIENT_HISTORY = "UNKNOWN_INSUFFICIENT_HISTORY"
VALIDITY_UNKNOWN_ZERO_BAND_WIDTH = "UNKNOWN_ZERO_BAND_WIDTH"
VALIDITY_UNKNOWN_NONFINITE_REFERENCE = "UNKNOWN_NONFINITE_REFERENCE"
VALIDITY_UNKNOWN_NONFINITE_QUERY = "UNKNOWN_NONFINITE_QUERY"
VALIDITY_DEGRADED_REFERENCE_COVERAGE = "DEGRADED_REFERENCE_COVERAGE"
VALIDITY_DEGRADED_DEGENERATE_REFERENCE = "DEGRADED_DEGENERATE_REFERENCE"
VALIDITY_DEGRADED_REFERENCE_ADEQUACY = "DEGRADED_REFERENCE_ADEQUACY"
VALIDITY_DEGRADED_SCALE_UNSTABLE = "DEGRADED_SCALE_UNSTABLE"

# A3 scale state, surfaced as its own named state (not only via ``validity``).
SCALE_STABLE = "SCALE_STABLE"
SCALE_UNSTABLE = "SCALE_UNSTABLE"
SCALE_UNKNOWN = "SCALE_UNKNOWN"

# A2 comparability status.  This exists so "zero complete round trips" and
# "reference unusable" can never be silently confused with the legitimate
# observation "the band was revisited zero times".
COMPARABILITY_OK = "COMPARABLE"
COMPARABILITY_NO_COMPLETE_CYCLE = "NO_COMPLETE_CYCLE"
COMPARABILITY_REFERENCE_UNUSABLE = "REFERENCE_UNUSABLE"

# Touch semantics.
TOUCH_RANGE_OVERLAP = "range_overlap"          # v0.2 default
TOUCH_MIN_OVERLAP_FRACTION = "min_overlap_fraction"  # challenger, not default
TOUCH_BODY_OVERLAP = "body_overlap"            # challenger, not default

# Zero-width policies.
ZERO_WIDTH_FAIL_CLOSED = "fail_closed"         # default
ZERO_WIDTH_TICK_FALLBACK = "tick_fallback"     # explicit opt-in only

# Anchor policies.
ANCHOR_FIRST_PROBE_WINS = "first_probe_wins"   # default
ANCHOR_REANCHOR_EACH_PROBE = "reanchor_each_probe"  # documented defective


# ---------------------------------------------------------------------------
# Input containers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Bar:
    """One completed OHLC bar.

    ``valid=False`` marks a bar the data layer knows to be missing/absent.
    Invalid bars never contribute touches and lower reference coverage.
    ``label`` is for CSV readability only and never enters any calculation.
    """

    open: float
    high: float
    low: float
    close: float
    valid: bool = True
    label: str = ""


@dataclass(frozen=True)
class PTMConfig:
    """Every free choice of the prototype, explicitly parameterised."""

    reference_bars: int = REFERENCE_BARS
    quantile_low: float = QUANTILE_LOW
    quantile_high: float = QUANTILE_HIGH
    radius_divisor: float = RADIUS_DIVISOR
    outer_multiplier: float = OUTER_BAND_MULTIPLIER
    acceptance_window: int = ACCEPTANCE_WINDOW
    tick: float | None = None
    zero_width_policy: str = ZERO_WIDTH_FAIL_CLOSED
    touch_mode: str = TOUCH_RANGE_OVERLAP
    min_touch_fraction: float = 0.0
    min_reference_coverage: float = 1.0
    max_episode_bars: int = REFERENCE_BARS
    suspect_scale_break_factor: float = SUSPECT_SCALE_BREAK_FACTOR
    # A1 reference-adequacy safety guards (pre-outcome fixed; see constants).
    cycle_swing_fraction: float = CYCLE_SWING_FRACTION
    min_reference_cycles: float = MIN_REFERENCE_CYCLES
    min_envelope_covered_fraction: float = MIN_ENVELOPE_COVERED_FRACTION
    max_unobserved_gap_fraction: float = MAX_UNOBSERVED_GAP_FRACTION
    # A5 anchor policy.  Frozen, in the fingerprint, and validated by
    # ``evaluate_stream``; re-anchoring every probe is the documented defect.
    anchor_policy: str = ANCHOR_FIRST_PROBE_WINS
    # A3 scale-stability safety guard (pre-outcome fixed).
    max_w_over_scale: float = MAX_W_OVER_SCALE
    # COMPARISON SWITCH, not a tuning parameter.  ``True`` (the only value any
    # real observation may use) applies the A1/A3 guards to the claim gate.
    # ``False`` reconstructs the pre-patch v0.2 claim behaviour so the runner
    # can print an old-vs-fixed table per fixture.  All diagnostics are still
    # computed and reported when it is False; only the gate is lifted.  A test
    # pins this default and pins that lifting it reproduces the old defect.
    apply_phase2_guards: bool = True

    def __post_init__(self) -> None:
        """Reject configurations that can only crash or change the definition.

        These are caller errors, not market conditions, so they fail loudly at
        construction rather than deep inside the geometry.  Two real ones found
        by the phase-2 adversarial audit: ``radius_divisor=0`` raised a bare
        ``ZeroDivisionError``, and ``acceptance_window=0`` silently redefined
        the acceptance trace (``[-(0-1):]`` is ``[-0:]``, the whole history).
        A guard that fails open because its knob was mistyped is worse than a
        crash.
        """
        def _positive(name: str, value) -> None:
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ValueError(f"{name} must be a number, got {value!r}")
            if not math.isfinite(float(value)) or float(value) <= 0.0:
                raise ValueError(
                    f"{name} must be a positive finite number, got {value!r}")

        def _unit(name: str, value) -> None:
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise ValueError(f"{name} must be a number, got {value!r}")
            if not math.isfinite(float(value)) or not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{name} must be within [0, 1], got {value!r}")

        def _positive_int(name: str, value) -> None:
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise ValueError(f"{name} must be a positive integer, got {value!r}")

        _positive_int("reference_bars", self.reference_bars)
        _positive_int("acceptance_window", self.acceptance_window)
        _positive_int("max_episode_bars", self.max_episode_bars)
        _positive("radius_divisor", self.radius_divisor)
        _positive("outer_multiplier", self.outer_multiplier)
        _positive("cycle_swing_fraction", self.cycle_swing_fraction)
        _positive("max_w_over_scale", self.max_w_over_scale)
        if self.tick is not None:
            _positive("tick", self.tick)
        _positive("suspect_scale_break_factor", self.suspect_scale_break_factor)
        if float(self.suspect_scale_break_factor) <= 1.0:
            raise ValueError(
                "suspect_scale_break_factor must exceed 1.0, got "
                f"{self.suspect_scale_break_factor!r}")
        _unit("quantile_low", self.quantile_low)
        _unit("quantile_high", self.quantile_high)
        if not float(self.quantile_low) < float(self.quantile_high):
            raise ValueError(
                f"quantile_low ({self.quantile_low!r}) must be below "
                f"quantile_high ({self.quantile_high!r})")
        for name in ("min_touch_fraction", "min_reference_coverage",
                     "min_envelope_covered_fraction",
                     "max_unobserved_gap_fraction"):
            _unit(name, getattr(self, name))
        if not (isinstance(self.min_reference_cycles, (int, float))
                and not isinstance(self.min_reference_cycles, bool)
                and math.isfinite(float(self.min_reference_cycles))
                and float(self.min_reference_cycles) >= 0.0):
            raise ValueError(
                f"min_reference_cycles must be a non-negative number, got "
                f"{self.min_reference_cycles!r}")
        for name, allowed in (
            ("touch_mode", (TOUCH_RANGE_OVERLAP, TOUCH_MIN_OVERLAP_FRACTION)),
            ("zero_width_policy", (ZERO_WIDTH_FAIL_CLOSED,
                                   ZERO_WIDTH_TICK_FALLBACK)),
            ("anchor_policy", (ANCHOR_FIRST_PROBE_WINS,
                               ANCHOR_REANCHOR_EACH_PROBE)),
        ):
            if getattr(self, name) not in allowed:
                raise ValueError(f"unknown {name}: {getattr(self, name)!r}")

    def fingerprint(self) -> dict:
        return {
            "reference_bars": self.reference_bars,
            "quantile_low": self.quantile_low,
            "quantile_high": self.quantile_high,
            "radius_divisor": self.radius_divisor,
            "outer_multiplier": self.outer_multiplier,
            "acceptance_window": self.acceptance_window,
            "tick": self.tick,
            "zero_width_policy": self.zero_width_policy,
            "touch_mode": self.touch_mode,
            "min_touch_fraction": self.min_touch_fraction,
            "min_reference_coverage": self.min_reference_coverage,
            "max_episode_bars": self.max_episode_bars,
            "suspect_scale_break_factor": self.suspect_scale_break_factor,
            "cycle_swing_fraction": self.cycle_swing_fraction,
            "min_reference_cycles": self.min_reference_cycles,
            "min_envelope_covered_fraction": self.min_envelope_covered_fraction,
            "max_unobserved_gap_fraction": self.max_unobserved_gap_fraction,
            "max_w_over_scale": self.max_w_over_scale,
            "anchor_policy": self.anchor_policy,
            "apply_phase2_guards": self.apply_phase2_guards,
        }


@dataclass(frozen=True)
class Probe:
    """A probe opportunity produced by the inherited model, never by PTM."""

    index: int
    direction: int  # +1 long, -1 short


# ---------------------------------------------------------------------------
# Frozen reference
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FrozenReference:
    anchor_index: int
    direction: int
    n_bars: int
    n_valid: int
    coverage: float
    q_low: float | None
    q_high: float | None
    w: float | None
    max_high: float | None
    min_low: float | None
    max_close: float | None
    min_close: float | None
    median_close: float | None
    degenerate: bool
    validity: str
    validity_detail: str
    # A1 reference-adequacy diagnostics (None when the window has no numerics).
    swing_legs: int | None = None
    reference_cycle_count: float | None = None
    envelope_covered_fraction: float | None = None
    max_unobserved_gap_fraction: float | None = None
    max_unobserved_gap_w: float | None = None
    # A3 scale-stability diagnostics.
    scale_reference: float | None = None
    w_over_scale: float | None = None
    scale_state: str = SCALE_UNKNOWN
    # Guard outcomes, kept separate from ``validity`` so the claim gate can be
    # asserted directly instead of inferred from a string mapping.
    reference_adequacy_ok: bool = False
    scale_stable: bool = False
    guards_enforced: bool = True
    validity_reasons: tuple = ()
    closes: tuple = field(repr=False, default=())
    highs: tuple = field(repr=False, default=())
    lows: tuple = field(repr=False, default=())
    opens: tuple = field(repr=False, default=())
    valid_mask: tuple = field(repr=False, default=())

    @property
    def is_usable(self) -> bool:
        """True when numeric territory outputs may be computed at all."""
        return self.validity in (
            VALIDITY_OK,
            VALIDITY_DEGRADED_REFERENCE_COVERAGE,
            VALIDITY_DEGRADED_DEGENERATE_REFERENCE,
            VALIDITY_DEGRADED_REFERENCE_ADEQUACY,
            VALIDITY_DEGRADED_SCALE_UNSTABLE,
        )

    @property
    def allows_new_territory_claim(self) -> bool:
        """Fail closed: only a fully adequate, stable, complete reference claims.

        ``coverage >= 1.0`` is required independently of
        ``min_reference_coverage`` so that lowering that knob cannot reopen a
        claim on a partial reference window.  ``reference_adequacy_ok`` and
        ``scale_stable`` are asserted here as well as through ``validity`` so
        that a future change to the validity mapping cannot silently reopen a
        claim on a reference that failed an A1/A3 guard.

        ``guards_enforced`` is False only in the runner's documented
        old-vs-fixed comparison mode; every real observation has it True.
        """
        gate = self.validity == VALIDITY_OK and self.coverage >= 1.0
        if self.guards_enforced:
            gate = gate and self.reference_adequacy_ok and self.scale_stable
        return gate


def _swing_legs(closes: Sequence[float], valid_mask: Sequence[bool],
                threshold: float) -> int:
    """Count confirmed swing legs on the valid closes; each leg ends at a
    confirmed reversal.

    A leg is confirmed only when price retraces at least ``threshold`` from the
    running extreme, so sub-quantum noise cannot manufacture a "round trip".
    The count is the number of confirmed REVERSALS, which is also the number of
    completed legs -- a monotone window with no reversal returns 0, not 1.  It
    is a deliberately conservative *lower* bound, and because
    ``reference_cycle_count = legs / 2.0`` a single confirmed leg is only half a
    round trip, which is why ``MIN_REFERENCE_CYCLES = 1.0`` requires two.
    """
    pts = [float(c) for c, ok in zip(closes, valid_mask) if ok]
    if len(pts) < 2 or not (threshold > 0.0):
        return 0
    legs = 0
    hi = lo = pts[0]
    direction = 0  # 0 unknown, +1 rising, -1 falling
    for c in pts[1:]:
        if c > hi:
            hi = c
        if c < lo:
            lo = c
        if direction >= 0 and (hi - c) >= threshold:
            legs += 1
            direction = -1
            lo = hi = c
        elif direction <= 0 and (c - lo) >= threshold:
            legs += 1
            direction = 1
            lo = hi = c
    return legs


def _envelope_geometry(lows: Sequence[float], highs: Sequence[float],
                       valid_mask: Sequence[bool]) -> tuple[float, float, float, bool]:
    """Return ``(envelope, covered, largest_unobserved_gap, unusable)`` in price units.

    Bars are treated as their observed ``[low, high]`` range only.  The
    unobserved gap is measured between *merged observed ranges*, never between
    consecutive closes: a reference whose bars span whole legs legitimately has
    large close-to-close jumps while observing every price in between, so a
    close-gap test would falsely reject it.

    ``unusable`` is ``True`` when the geometry cannot be trusted, and the caller
    must then fail CLOSED.  This is not hypothetical: two finite bounds of
    opposite sign at the double limit (``low = -1e308``, ``high = +1e308``)
    produce a non-finite span, and ``inf / inf`` is ``nan`` -- and ``nan < 0.5``
    is ``False``, so a naive coverage test silently PASSES.  A NaN diagnostic
    must never be able to open a claim gate, so non-finite or inverted bar
    ranges, and any non-finite derived quantity, are rejected outright.  A bar
    whose range cannot be represented could have covered any price at all, so
    the envelope is genuinely unknown, not merely large.
    """
    intervals: list[tuple[float, float]] = []
    unusable = False
    for i in range(len(valid_mask)):
        if not valid_mask[i]:
            continue
        lo, hi = float(lows[i]), float(highs[i])
        if not (math.isfinite(lo) and math.isfinite(hi)) or hi < lo:
            unusable = True
            continue
        intervals.append((lo, hi))
    intervals.sort()
    merged: list[list[float]] = []
    for lo, hi in intervals:
        if merged and lo <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], hi)
        else:
            merged.append([lo, hi])
    if not merged:
        return 0.0, 0.0, 0.0, True
    envelope = merged[-1][1] - merged[0][0]
    covered = sum(hi - lo for lo, hi in merged)
    gaps = [merged[i + 1][0] - merged[i][1] for i in range(len(merged) - 1)]
    biggest_gap = max(gaps) if gaps else 0.0
    if not (math.isfinite(envelope) and math.isfinite(covered)
            and math.isfinite(biggest_gap)):
        return 0.0, 0.0, 0.0, True
    return envelope, covered, biggest_gap, unusable


def _adequacy_diagnostics(
    closes: Sequence[float],
    lows: Sequence[float],
    highs: Sequence[float],
    valid_mask: Sequence[bool],
    span: float,
    w: float,
    config: PTMConfig,
) -> dict:
    """A1: does this window contain evidence of a repeated price region?"""
    legs = _swing_legs(closes, valid_mask, config.cycle_swing_fraction * span)
    cycles = legs / 2.0
    envelope, covered, biggest_gap, unusable = _envelope_geometry(
        lows, highs, valid_mask)
    if unusable:
        # Fail closed and report zeros rather than a NaN that no comparison
        # can fail on.  The explicit reason below blocks the claim.
        envc, gap_fraction, gap_w = 0.0, 1.0, 0.0
    else:
        envc = (covered / envelope) if envelope > 0 else 1.0
        gap_w = (biggest_gap / w) if w > 0 else None
        gap_fraction = (biggest_gap / envelope) if envelope > 0 else 0.0

    reasons: list[str] = []
    if cycles < config.min_reference_cycles:
        reasons.append(
            f"complete round trips {cycles:.1f} < required "
            f"{config.min_reference_cycles:.1f} "
            f"({legs} confirmed swings over span {span:.4g})"
        )
    if unusable:
        reasons.append(
            "reference bar ranges are non-finite or inverted, so the observed "
            "price envelope is unmeasurable; coverage treated as 0"
        )
    if envc < config.min_envelope_covered_fraction:
        reasons.append(
            f"observed envelope fraction {envc:.4f} < required "
            f"{config.min_envelope_covered_fraction:.4f}"
        )
    if gap_fraction > config.max_unobserved_gap_fraction:
        reasons.append(
            f"largest unobserved price gap {gap_fraction:.4f} of envelope > "
            f"allowed {config.max_unobserved_gap_fraction:.4f}"
        )
    return {
        "swing_legs": legs,
        "reference_cycle_count": cycles,
        "envelope_covered_fraction": envc,
        "max_unobserved_gap_fraction": gap_fraction,
        "max_unobserved_gap_w": gap_w,
        "reference_adequacy_ok": not reasons,
        "reasons": reasons,
    }


def _scale_diagnostics(median_close: float | None, w: float,
                       config: PTMConfig) -> dict:
    """A3: is ``w`` a plausible price quantum for this instrument's scale?

    The denominator is ``|median reference close|``.  ``abs`` keeps the ratio
    meaningful for series quoted on a negative level (negative yields) and
    makes it identical for a short-side mirror.  A zero or non-finite
    denominator yields ``w_over_scale = None`` and is treated as NOT stable:
    an unmeasurable scale must never be reported as a stable one, and it must
    never be divided by.
    """
    scale = None
    if median_close is not None and math.isfinite(float(median_close)):
        candidate = abs(float(median_close))
        if candidate > 0.0:
            scale = candidate
    if scale is None:
        return {
            "scale_reference": None,
            "w_over_scale": None,
            "scale_state": SCALE_UNKNOWN,
            "scale_stable": False,
            "reasons": [
                "reference scale reference (|median close|) is zero or "
                "non-finite; ratio undefined, treated as unstable"
            ],
        }
    ratio = w / scale
    stable = math.isfinite(ratio) and ratio <= config.max_w_over_scale
    reasons: list[str] = []
    if not stable:
        reasons.append(
            f"w/scale {ratio:.5f} > allowed {config.max_w_over_scale:.5f} "
            f"(w={w:.6g}, |median close|={scale:.6g})"
        )
    return {
        "scale_reference": scale,
        "w_over_scale": ratio,
        "scale_state": SCALE_STABLE if stable else SCALE_UNSTABLE,
        "scale_stable": stable,
        "reasons": reasons,
    }


def build_reference(
    bars: Sequence[Bar],
    anchor_index: int,
    direction: int,
    config: PTMConfig | None = None,
) -> FrozenReference:
    """Freeze the ``config.reference_bars`` completed bars preceding the anchor.

    The reference is causal: it uses exactly ``bars[anchor - k : anchor]`` and
    nothing at or after ``anchor``.  It never slides afterwards.
    """
    config = config or PTMConfig()
    if int(direction) not in (-1, 1):
        raise ValueError(
            f"direction must be +1 (long) or -1 (short), got {direction!r}; "
            "the side is a caller contract, not market data, so it is rejected "
            "rather than silently defaulted"
        )
    k = int(config.reference_bars)
    start = anchor_index - k
    window_len = max(min(anchor_index, len(bars)) - max(start, 0), 0)
    if start < 0 or window_len < k:
        # Covers both "not enough history before the anchor" and "the anchor
        # itself is past the end of the data", which would otherwise silently
        # freeze a truncated window and report a misleading DEGRADED state.
        return FrozenReference(
            anchor_index=anchor_index,
            direction=int(np.sign(direction)) or 1,
            n_bars=window_len,
            n_valid=0,
            coverage=0.0,
            q_low=None,
            q_high=None,
            w=None,
            max_high=None,
            min_low=None,
            max_close=None,
            min_close=None,
            median_close=None,
            degenerate=False,
            validity=VALIDITY_UNKNOWN_INSUFFICIENT_HISTORY,
            validity_detail=(
                f"need {k} completed bars ending at anchor {anchor_index}, "
                f"only {window_len} available"
            ),
        )

    window = list(bars[start:anchor_index])
    valid_mask = [bool(b.valid) for b in window]
    n_valid = int(sum(valid_mask))
    coverage = n_valid / float(k) if k else 0.0

    valid_bars = [b for b, ok in zip(window, valid_mask) if ok]
    if n_valid == 0:
        return FrozenReference(
            anchor_index=anchor_index,
            direction=int(np.sign(direction)) or 1,
            n_bars=len(window),
            n_valid=0,
            coverage=0.0,
            q_low=None,
            q_high=None,
            w=None,
            max_high=None,
            min_low=None,
            max_close=None,
            min_close=None,
            median_close=None,
            degenerate=False,
            validity=VALIDITY_UNKNOWN_INSUFFICIENT_HISTORY,
            validity_detail="reference window contains no valid bars",
        )

    # Full-window arrays (invalid bars included) so that every positional index
    # in the reference stays aligned with ``valid_mask``; invalid entries never
    # contribute to any statistic.
    all_closes = np.asarray([b.close for b in window], dtype=float)
    all_highs = np.asarray([b.high for b in window], dtype=float)
    all_lows = np.asarray([b.low for b in window], dtype=float)
    all_opens = np.asarray([b.open for b in window], dtype=float)

    closes = np.asarray([b.close for b in valid_bars], dtype=float)
    highs = np.asarray([b.high for b in valid_bars], dtype=float)
    lows = np.asarray([b.low for b in valid_bars], dtype=float)

    q_low = float(np.quantile(closes, config.quantile_low, method="linear"))
    q_high = float(np.quantile(closes, config.quantile_high, method="linear"))
    spread = q_high - q_low
    w = spread / float(config.radius_divisor)

    degenerate = False
    tick_fallback = False
    validity = VALIDITY_OK
    detail = f"{n_valid}/{k} valid reference bars"

    if not math.isfinite(w) or w <= 0.0:
        if (
            config.zero_width_policy == ZERO_WIDTH_TICK_FALLBACK
            and config.tick is not None
            and config.tick > 0.0
        ):
            w = float(config.tick)
            degenerate = True
            tick_fallback = True
            detail = (
                f"zero inter-quantile spread; explicit tick fallback "
                f"w=tick={config.tick} used (degenerate reference, claims blocked)"
            )
        else:
            return FrozenReference(
                anchor_index=anchor_index,
                direction=int(np.sign(direction)) or 1,
                n_bars=len(window),
                n_valid=n_valid,
                coverage=coverage,
                q_low=q_low,
                q_high=q_high,
                w=None,
                max_high=float(np.max(highs)),
                min_low=float(np.min(lows)),
                max_close=float(np.max(closes)),
                min_close=float(np.min(closes)),
                median_close=float(np.median(closes)),
                degenerate=True,
                validity=VALIDITY_UNKNOWN_ZERO_BAND_WIDTH,
                validity_detail=(
                    f"Q{config.quantile_high:.2f}-Q{config.quantile_low:.2f} spread "
                    f"= {spread} gives non-positive radius; no valid price quantum"
                ),
            )

    range_stats = (
        float(np.max(highs)),
        float(np.min(lows)),
        float(np.max(closes)),
        float(np.min(closes)),
    )
    if not all(math.isfinite(v) for v in range_stats):
        return FrozenReference(
            anchor_index=anchor_index,
            direction=int(np.sign(direction)) or 1,
            n_bars=len(window),
            n_valid=n_valid,
            coverage=coverage,
            q_low=q_low,
            q_high=q_high,
            w=None,
            max_high=None,
            min_low=None,
            max_close=None,
            min_close=None,
            median_close=None,
            degenerate=False,
            validity=VALIDITY_UNKNOWN_NONFINITE_REFERENCE,
            validity_detail=(
                "reference window contains non-finite OHLC values; fail closed"
            ),
        )

    # ------------------------------------------------------------------
    # A1 / A3 guards and validity precedence.
    #
    # Precedence (documented; ``validity_reasons`` lists EVERY triggered reason
    # so nothing is hidden behind the winning label):
    #   1 DEGRADED_DEGENERATE_REFERENCE   explicit tick fallback
    #   2 DEGRADED_SCALE_UNSTABLE         A3
    #   3 DEGRADED_REFERENCE_ADEQUACY     A1
    #   4 DEGRADED_REFERENCE_COVERAGE
    #   5 OK
    # Every DEGRADED state still reports the numeric diagnostics but cannot
    # emit a new-territory claim.
    # ------------------------------------------------------------------
    median_close = float(np.median(closes))
    adequacy = _adequacy_diagnostics(
        all_closes, all_lows, all_highs, valid_mask, spread, float(w), config
    )
    scale = _scale_diagnostics(median_close, float(w), config)

    validity_reasons: list[str] = []
    if tick_fallback:
        validity_reasons.append(detail)
    if not scale["scale_stable"]:
        validity_reasons.extend(scale["reasons"])
    if not adequacy["reference_adequacy_ok"]:
        validity_reasons.extend(adequacy["reasons"])
    if coverage < config.min_reference_coverage:
        validity_reasons.append(
            f"coverage {coverage:.4f} < required "
            f"{config.min_reference_coverage:.4f} ({n_valid}/{k})"
        )

    if tick_fallback:
        validity = VALIDITY_DEGRADED_DEGENERATE_REFERENCE
    elif config.apply_phase2_guards and not scale["scale_stable"]:
        validity = VALIDITY_DEGRADED_SCALE_UNSTABLE
    elif config.apply_phase2_guards and not adequacy["reference_adequacy_ok"]:
        validity = VALIDITY_DEGRADED_REFERENCE_ADEQUACY
    elif coverage < config.min_reference_coverage:
        validity = VALIDITY_DEGRADED_REFERENCE_COVERAGE
    else:
        validity = VALIDITY_OK

    return FrozenReference(
        anchor_index=anchor_index,
        direction=int(np.sign(direction)) or 1,
        n_bars=len(window),
        n_valid=n_valid,
        coverage=coverage,
        q_low=q_low,
        q_high=q_high,
        w=float(w),
        max_high=float(np.max(highs)),
        min_low=float(np.min(lows)),
        max_close=float(np.max(closes)),
        min_close=float(np.min(closes)),
        median_close=median_close,
        degenerate=degenerate,
        validity=validity,
        validity_detail=(
            "; ".join(validity_reasons) if validity_reasons else detail
        ),
        swing_legs=adequacy["swing_legs"],
        reference_cycle_count=adequacy["reference_cycle_count"],
        envelope_covered_fraction=adequacy["envelope_covered_fraction"],
        max_unobserved_gap_fraction=adequacy["max_unobserved_gap_fraction"],
        max_unobserved_gap_w=adequacy["max_unobserved_gap_w"],
        scale_reference=scale["scale_reference"],
        w_over_scale=scale["w_over_scale"],
        scale_state=scale["scale_state"],
        reference_adequacy_ok=adequacy["reference_adequacy_ok"],
        scale_stable=scale["scale_stable"],
        guards_enforced=bool(config.apply_phase2_guards),
        validity_reasons=tuple(validity_reasons),
        closes=tuple(float(x) for x in all_closes),
        highs=tuple(float(x) for x in all_highs),
        lows=tuple(float(x) for x in all_lows),
        opens=tuple(float(x) for x in all_opens),
        valid_mask=tuple(bool(x) for x in valid_mask),
    )


# ---------------------------------------------------------------------------
# Reference density diagnostics (descriptive only -- NOT part of R, O or N)
# ---------------------------------------------------------------------------


def reference_gap_diagnostics(ref: FrozenReference) -> dict:
    """Expose how densely the frozen reference actually samples its envelope.

    ``R``, ``O`` and ``N`` are deliberately NOT modified by these numbers.  The
    engineering review needs them because a sparse or rolled reference can make
    ``N`` overstate novelty while every published v0.2 formula still evaluates
    exactly as specified.  A gappy daily download therefore cannot be caught by
    the frozen v0.2 math alone; it has to be surfaced separately.

    Two different gap notions are reported on purpose:

    * ``max_close_gap_w`` -- close-to-close jump.  DIAGNOSTIC ONLY.  A
      reference whose bars span whole legs (e.g. ``crossed_but_not_closed``)
      has large close jumps while observing every price in between, so this
      must never gate a claim.
    * ``max_unobserved_gap_w`` / ``max_unobserved_gap_fraction`` -- the
      largest price interval inside the envelope that NO bar range covers.
      This is the quantity the A1 guard gates on.
    """
    if ref.w is None or ref.n_valid == 0:
        return {
            "max_close_gap_w": None,
            "median_close_gap_w": None,
            "envelope_covered_fraction": None,
            "max_unobserved_gap_w": None,
            "max_unobserved_gap_fraction": None,
        }

    w = float(ref.w)
    gaps: list[float] = []
    prev: float | None = None
    for i, ok in enumerate(ref.valid_mask):
        if not ok:
            continue
        if prev is not None:
            gaps.append(abs(ref.closes[i] - prev))
        prev = ref.closes[i]

    envelope, covered, biggest_gap, unusable = _envelope_geometry(
        ref.lows, ref.highs, ref.valid_mask
    )
    if unusable:
        # Never report a NaN here: it must be impossible for a NaN diagnostic
        # to be read as "passes the threshold".  See _envelope_geometry.
        return {
            "max_close_gap_w": (max(gaps) / w) if gaps else 0.0,
            "median_close_gap_w": (float(np.median(gaps)) / w) if gaps else 0.0,
            "envelope_covered_fraction": 0.0,
            "max_unobserved_gap_w": 0.0,
            "max_unobserved_gap_fraction": 1.0,
        }

    return {
        "max_close_gap_w": (max(gaps) / w) if gaps else 0.0,
        "median_close_gap_w": (float(np.median(gaps)) / w) if gaps else 0.0,
        "envelope_covered_fraction": (covered / envelope) if envelope > 0 else 1.0,
        "max_unobserved_gap_w": (biggest_gap / w) if w > 0 else None,
        "max_unobserved_gap_fraction": (
            (biggest_gap / envelope) if envelope > 0 else 0.0
        ),
    }


# ---------------------------------------------------------------------------
# Per-bar observation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TerritoryObservation:
    """One completed-close PTM observation.  Actionable no earlier than t+1."""

    bar_index: int
    anchor_index: int
    direction: int
    label: str
    close: float
    high: float
    low: float
    w: float | None
    inner_low: float | None
    inner_high: float | None
    outer_low: float | None
    outer_high: float | None
    revisit_episodes: int | None
    occupancy: float | None
    longest_inner_run: int | None
    novelty: float | None
    novelty_class: str | None
    acceptance_trace: float | None
    evidence_bars: int
    frontier_progress: float | None
    frontier_progress_close: float | None
    days_since_best_frontier: int | None
    frontier_change_3: float | None
    progress_3_w: float | None
    progress_amplitude_3_w: float | None
    range_3_w: float | None
    bars_since_significant_progress: int | None
    stall_flag: bool | None
    is_new_territory_claim: bool
    suspect_scale_break: bool
    drift_scale_warning: bool
    reference_coverage: float
    degenerate_reference: bool
    validity: str
    validity_detail: str
    # --- A1: reference adequacy (is the window evidence of a repeated region?) ---
    swing_legs: int | None
    reference_cycle_count: float | None
    envelope_covered_fraction: float | None
    max_unobserved_gap_fraction: float | None
    max_unobserved_gap_w: float | None
    reference_adequacy_ok: bool
    # --- A2: scale comparability (speed-invariant revisit description) ---
    episodes_per_cycle: float | None
    revisit_density: float | None
    comparability_status: str
    # --- A3: scale stability (is w a plausible price quantum?) ---
    scale_reference: float | None
    w_over_scale: float | None
    scale_state: str
    scale_stable: bool
    observable_at_bar: int
    actionable_at_bar: int

    def as_row(self, fixture: str = "") -> dict:
        d = {
            "fixture": fixture,
        }
        d.update(self.__dict__)
        return d


def _touch_flags(
    ref: FrozenReference, inner_low: float, inner_high: float, config: PTMConfig
) -> list[bool]:
    """Historical inner-band touch per reference bar, under the chosen mode."""
    band = inner_high - inner_low
    min_overlap = float(config.min_touch_fraction) * band
    flags: list[bool] = []
    for i in range(len(ref.closes)):
        if not ref.valid_mask[i]:
            flags.append(False)
            continue
        if config.touch_mode == TOUCH_BODY_OVERLAP:
            lo = min(ref.opens[i], ref.closes[i])
            hi = max(ref.opens[i], ref.closes[i])
        else:
            lo = ref.lows[i]
            hi = ref.highs[i]
        overlap = min(hi, inner_high) - max(lo, inner_low)
        if config.touch_mode == TOUCH_MIN_OVERLAP_FRACTION:
            flags.append(overlap >= min_overlap)
        else:
            # The v0.2 predicate is INCLUSIVE: high >= P-w and low <= P+w.
            # At tick-aligned prices w is often an exact multiple of the price
            # quantum, so a strict (>0) test would drop real band-edge touches
            # and could report a price equal to every reference bar as
            # "never visited".  Inclusive matches the written definition.
            flags.append(overlap >= 0.0)
    return flags


def _count_episodes(touch: Sequence[bool], ref: FrozenReference,
                    outer_low: float, outer_high: float) -> tuple[int, int]:
    """Count arming-gated revisit episodes and the longest uninterrupted run.

    A bar that is entirely outside the outer band re-arms the counter.  A bar
    that is neither touching the inner band nor fully outside the outer band
    leaves the armed state unchanged, so tiny in/out oscillations at the band
    edge cannot inflate the count.
    """
    episodes = 0
    armed = True
    run = 0
    longest = 0
    for i in range(len(ref.closes)):
        if not ref.valid_mask[i]:
            continue
        if touch[i]:
            run += 1
            longest = max(longest, run)
            if armed:
                episodes += 1
                armed = False
        else:
            run = 0
            fully_outside = ref.lows[i] > outer_high or ref.highs[i] < outer_low
            if fully_outside:
                armed = True
    return episodes, longest


def _novelty_class(episodes: int | None) -> str | None:
    if episodes is None:
        return None
    if episodes <= 0:
        return NOVELTY_CLASS_UNVISITED
    if episodes == 1:
        return NOVELTY_CLASS_SPARSE
    if episodes <= 4:
        return NOVELTY_CLASS_REVISITED
    return NOVELTY_CLASS_HEAVILY_REVISITED


def scale_ratio_break(a: float, b: float, factor: float) -> bool:
    """True when ``a`` and ``b`` cannot be the same price unit.

    Sign flips always count as a break.  Otherwise the absolute ratio must stay
    inside ``[1/factor, factor]``.  This is a data-quality prompt, NOT a gate:
    it cannot tell a split from a genuine large move.  See the finding doc for
    the false-positive (a real -50% crash) and false-negative (a 3:2 split)
    cases.
    """
    if a == 0.0 or b == 0.0:
        return a != b
    if (a > 0.0) != (b > 0.0):
        return True
    ratio = abs(a) / abs(b)
    return ratio > factor or ratio < 1.0 / factor


def observe(
    bars: Sequence[Bar],
    ref: FrozenReference,
    t: int,
    config: PTMConfig | None = None,
    novelty_history: Sequence[float] | None = None,
    best_frontier: float | None = None,
    best_frontier_age: int | None = None,
    last_significant_progress_t: int | None = None,
    scale_break_latched: bool = False,
) -> TerritoryObservation:
    """Compute one PTM observation from a frozen reference and bars up to ``t``.

    Causality: only ``bars[ref.anchor_index : t + 1]`` plus the frozen
    reference are read.  Nothing at a later index can influence this result.
    """
    config = config or PTMConfig()
    bar = bars[t]
    direction = ref.direction

    base = dict(
        bar_index=t,
        anchor_index=ref.anchor_index,
        direction=direction,
        label=bar.label,
        close=float(bar.close),
        high=float(bar.high),
        low=float(bar.low),
        w=ref.w,
        inner_low=None,
        inner_high=None,
        outer_low=None,
        outer_high=None,
        revisit_episodes=None,
        occupancy=None,
        longest_inner_run=None,
        novelty=None,
        novelty_class=None,
        acceptance_trace=None,
        evidence_bars=min(config.acceptance_window, max(t - ref.anchor_index + 1, 0)),
        frontier_progress=None,
        frontier_progress_close=None,
        days_since_best_frontier=None,
        frontier_change_3=None,
        progress_3_w=None,
        progress_amplitude_3_w=None,
        range_3_w=None,
        bars_since_significant_progress=None,
        stall_flag=None,
        is_new_territory_claim=False,
        suspect_scale_break=False,
        drift_scale_warning=False,
        reference_coverage=ref.coverage,
        degenerate_reference=ref.degenerate,
        validity=ref.validity,
        validity_detail=ref.validity_detail,
        swing_legs=ref.swing_legs,
        reference_cycle_count=ref.reference_cycle_count,
        envelope_covered_fraction=ref.envelope_covered_fraction,
        max_unobserved_gap_fraction=ref.max_unobserved_gap_fraction,
        max_unobserved_gap_w=ref.max_unobserved_gap_w,
        reference_adequacy_ok=ref.reference_adequacy_ok,
        episodes_per_cycle=None,
        revisit_density=None,
        comparability_status=COMPARABILITY_REFERENCE_UNUSABLE,
        scale_reference=ref.scale_reference,
        w_over_scale=ref.w_over_scale,
        scale_state=ref.scale_state,
        scale_stable=ref.scale_stable,
        observable_at_bar=t,
        actionable_at_bar=t + 1,
    )

    if not ref.is_usable or ref.w is None:
        return TerritoryObservation(**base)

    p = float(bar.close)
    if not (
        math.isfinite(p)
        and math.isfinite(float(bar.high))
        and math.isfinite(float(bar.low))
    ):
        # A NaN query close would make every band comparison compare against
        # NaN and silently register spurious touches, so it must fail closed
        # instead of returning a plausible-looking novelty.
        base.update(
            validity=VALIDITY_UNKNOWN_NONFINITE_QUERY,
            validity_detail="non-finite query OHLC; fail closed",
        )
        return TerritoryObservation(**base)
    w = float(ref.w)
    inner_low, inner_high = p - w, p + w
    outer_low, outer_high = p - config.outer_multiplier * w, p + config.outer_multiplier * w
    base.update(inner_low=inner_low, inner_high=inner_high,
                outer_low=outer_low, outer_high=outer_high)

    touch = _touch_flags(ref, inner_low, inner_high, config)
    episodes, longest = _count_episodes(touch, ref, outer_low, outer_high)
    occupancy = (sum(touch) / float(ref.n_valid)) if ref.n_valid else None
    novelty = 1.0 / (1.0 + episodes)
    nclass = _novelty_class(episodes)

    # --- A2: market-speed-invariant revisit comparability ------------------
    # ``revisit_density`` is revisits per valid reference bar: a real rate, so
    # "revisited zero times" is the legitimate value 0.0, never None.
    # ``episodes_per_cycle`` divides by the number of complete round trips the
    # window actually contains, which is the quantity that removes the raw
    # market-speed dependence of R.  Neither number replaces R or N, and
    # neither is used to change the claim: they are reported alongside the
    # frozen v0.2 values so a later frozen research run can compare like with
    # like.  A window with no complete round trip yields None (unmeasurable),
    # which is deliberately distinct from 0.0 (measured zero).
    cycles = ref.reference_cycle_count
    if ref.n_valid > 0:
        base["revisit_density"] = episodes / float(ref.n_valid)
    if cycles is not None and cycles >= 1.0:
        base["episodes_per_cycle"] = episodes / cycles
        base["comparability_status"] = COMPARABILITY_OK
    else:
        base["episodes_per_cycle"] = None
        base["comparability_status"] = COMPARABILITY_NO_COMPLETE_CYCLE

    if direction > 0:
        frontier = (p - ref.max_high) / w
        frontier_close = (p - ref.max_close) / w
    else:
        frontier = (ref.min_low - p) / w
        frontier_close = (ref.min_close - p) / w

    # Causal running best frontier and its age, driven by the caller's state
    # but recomputable from history alone (see evaluate_episode).
    if best_frontier is None:
        run_best = frontier
        days_since = 0
    else:
        if frontier > best_frontier:
            run_best = frontier
            days_since = 0
        else:
            run_best = best_frontier
            days_since = (best_frontier_age or 0) + 1

    prev_idx = max(ref.anchor_index, t - 3)
    prev_close = float(bars[prev_idx].close)
    progress_signed = direction * (p - prev_close) / w
    progress_amp = abs(p - prev_close) / w
    window = bars[max(ref.anchor_index, t - 2): t + 1]
    range_3 = (max(b.high for b in window) - min(b.low for b in window)) / w

    if last_significant_progress_t is None:
        last_significant_progress_t = ref.anchor_index
    if abs(p - float(bars[t - 1].close)) / w >= STALL_PROGRESS_FRACTION_W and t > ref.anchor_index:
        last_significant_progress_t = t
    elif t == ref.anchor_index:
        last_significant_progress_t = t
    bars_since_progress = t - last_significant_progress_t

    novelty_fresh = nclass in (NOVELTY_CLASS_UNVISITED, NOVELTY_CLASS_SPARSE)
    stall = bool(
        novelty_fresh
        and (bars_since_progress >= STALL_MIN_BARS or days_since >= STALL_MIN_BARS)
        and range_3 < STALL_RANGE_FRACTION_W
    )

    median_ref = float(ref.median_close) if ref.median_close is not None else 0.0
    prev_close = float(bars[t - 1].close) if t > 0 else p
    # A split or a futures roll is an OVERNIGHT re-basing, so the latch keys on
    # the one-bar jump only.  Comparing the level against the reference median
    # instead would flag any sustained large move -- and because a ratio is not
    # invariant under arithmetic price reflection, that version silently
    # suppressed new-territory claims on long downtrends but not long uptrends
    # of the same size.  The drift comparison is reported, never gated on.
    instantaneous_break = scale_ratio_break(
        p, prev_close, config.suspect_scale_break_factor
    )
    drift_break = scale_ratio_break(p, median_ref, config.suspect_scale_break_factor)
    suspect = bool(scale_break_latched or instantaneous_break)

    acceptance = None
    if novelty_history is not None:
        # The trace must include the CURRENT completed close: the design
        # requires a signal on the first close, not after three or five bars.
        # Guard the slice: ``[-(1-1):]`` is ``[-0:]``, i.e. the WHOLE history,
        # which would silently average the entire episode instead of taking
        # just the current close.
        prior = (list(novelty_history)[-(config.acceptance_window - 1):]
                 if config.acceptance_window > 1 else [])
        trace = prior + [novelty]
        acceptance = float(sum(trace) / len(trace))
    else:
        acceptance = novelty

    base.update(
        revisit_episodes=episodes,
        occupancy=occupancy,
        longest_inner_run=longest,
        novelty=novelty,
        novelty_class=nclass,
        acceptance_trace=acceptance if acceptance is not None else novelty,
        frontier_progress=frontier,
        frontier_progress_close=frontier_close,
        days_since_best_frontier=days_since,
        frontier_change_3=(frontier - _frontier_at(bars, ref, max(ref.anchor_index, t - 3), config)),
        progress_3_w=progress_signed,
        progress_amplitude_3_w=progress_amp,
        range_3_w=range_3,
        bars_since_significant_progress=bars_since_progress,
        stall_flag=stall,
        # Fail-closed claim gate.  ``allows_new_territory_claim`` now requires a
        # complete (coverage 1.0), ADEQUATE (A1) and SCALE-STABLE (A3)
        # reference as well as a validity of OK; ``suspect`` still suppresses.
        is_new_territory_claim=bool(
            novelty_fresh and ref.allows_new_territory_claim and not suspect
        ),
        suspect_scale_break=suspect,
        drift_scale_warning=bool(drift_break),
    )
    return TerritoryObservation(**base)


def _frontier_at(bars: Sequence[Bar], ref: FrozenReference, t: int,
                 config: PTMConfig) -> float:
    p = float(bars[t].close)
    w = float(ref.w)
    if ref.direction > 0:
        return (p - ref.max_high) / w
    return (ref.min_low - p) / w


# ---------------------------------------------------------------------------
# Episode evaluation
# ---------------------------------------------------------------------------


@dataclass
class Episode:
    anchor_index: int
    direction: int
    observations: list[TerritoryObservation]
    reference: FrozenReference
    reprobe_indices: list[int] = field(default_factory=list)
    closed_at: int | None = None

    @property
    def first_new_territory_bar(self) -> int | None:
        for obs in self.observations:
            if obs.is_new_territory_claim:
                return obs.bar_index
        return None

    @property
    def first_unvisited_bar(self) -> int | None:
        for obs in self.observations:
            if obs.novelty_class == NOVELTY_CLASS_UNVISITED:
                return obs.bar_index
        return None


def evaluate_episode(
    bars: Sequence[Bar],
    anchor_index: int,
    direction: int,
    config: PTMConfig | None = None,
) -> Episode:
    """Evaluate one anchored PTM episode over every completed bar >= anchor."""
    config = config or PTMConfig()
    ref = build_reference(bars, anchor_index, direction, config)

    observations: list[TerritoryObservation] = []
    novelty_history: list[float] = []
    best_frontier: float | None = None
    best_age: int | None = None
    last_progress_t: int | None = anchor_index
    scale_break_latched = False

    for t in range(anchor_index, len(bars)):
        obs = observe(
            bars,
            ref,
            t,
            config,
            novelty_history=novelty_history,
            best_frontier=best_frontier,
            best_frontier_age=best_age,
            last_significant_progress_t=last_progress_t,
            scale_break_latched=scale_break_latched,
        )
        observations.append(obs)
        if obs.suspect_scale_break:
            scale_break_latched = True
        if obs.novelty is not None:
            novelty_history.append(obs.novelty)
        if obs.frontier_progress is not None:
            if best_frontier is None or obs.frontier_progress > best_frontier:
                best_frontier = obs.frontier_progress
        if obs.days_since_best_frontier is not None:
            best_age = obs.days_since_best_frontier
        if obs.bars_since_significant_progress is not None:
            last_progress_t = t - obs.bars_since_significant_progress
    return Episode(
        anchor_index=anchor_index,
        direction=int(np.sign(direction)) or 1,
        observations=observations,
        reference=ref,
    )


def evaluate_stream(
    bars: Sequence[Bar],
    probes: Iterable[Probe],
    config: PTMConfig | None = None,
    anchor_policy: str | None = None,
) -> list[Episode]:
    """Group a probe stream into anchored episodes.

    ``first_probe_wins`` (default): the first probe of an episode freezes the
    reference.  Overlapping probes are attached to the open episode and do NOT
    re-freeze the reference and do NOT reset evidence maturity.  A new episode
    only opens when the previous one has run longer than ``max_episode_bars``
    (the reference window is then fully stale) or after the caller's probe
    arrives while no episode is open.

    ``reanchor_each_probe`` is kept only so the counterexample in the tests can
    demonstrate why naive re-anchoring is wrong.  It is NOT the default.

    ``anchor_policy`` defaults to ``None``, which means "use
    ``config.anchor_policy``".  Passing it explicitly is retained for the
    counterexample tests; the value is part of the config fingerprint, so a
    real run cannot change it without changing the frozen fingerprint.
    """
    config = config or PTMConfig()
    if anchor_policy is None:
        anchor_policy = config.anchor_policy
    if anchor_policy not in (ANCHOR_FIRST_PROBE_WINS, ANCHOR_REANCHOR_EACH_PROBE):
        raise ValueError(f"unknown anchor policy: {anchor_policy!r}")
    ordered = sorted(probes, key=lambda p: p.index)
    episodes: list[Episode] = []
    open_episode: Episode | None = None

    for probe in ordered:
        if open_episode is not None:
            age = probe.index - open_episode.anchor_index
            still_open = age < config.max_episode_bars
        else:
            still_open = False

        if anchor_policy == ANCHOR_REANCHOR_EACH_PROBE or not still_open:
            if open_episode is not None:
                open_episode.closed_at = probe.index
            open_episode = evaluate_episode(bars, probe.index, probe.direction, config)
            episodes.append(open_episode)
        else:
            open_episode.reprobe_indices.append(probe.index)

    if open_episode is not None and open_episode.closed_at is None:
        open_episode.closed_at = len(bars) - 1
    return episodes


# ---------------------------------------------------------------------------
# Convenience helpers used by the runner and the tests
# ---------------------------------------------------------------------------


def observations_as_rows(episode: Episode, fixture: str = "") -> list[dict]:
    return [obs.as_row(fixture) for obs in episode.observations]


def find_first_observation(observations: Sequence[TerritoryObservation],
                           predicate) -> int | None:
    for obs in observations:
        if predicate(obs):
            return obs.bar_index
    return None
