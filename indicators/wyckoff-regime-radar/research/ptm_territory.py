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
        )

    @property
    def allows_new_territory_claim(self) -> bool:
        """Fail closed: only a fully valid, complete reference may claim.

        ``coverage >= 1.0`` is required independently of
        ``min_reference_coverage`` so that lowering that knob cannot reopen a
        claim on a partial reference window.
        """
        return self.validity == VALIDITY_OK and self.coverage >= 1.0


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
            detail = (
                f"zero inter-quantile spread; explicit tick fallback "
                f"w=tick={config.tick} used (degenerate reference, claims blocked)"
            )
            return FrozenReference(
                anchor_index=anchor_index,
                direction=int(np.sign(direction)) or 1,
                n_bars=len(window),
                n_valid=n_valid,
                coverage=coverage,
                q_low=q_low,
                q_high=q_high,
                w=w,
                max_high=float(np.max(highs)),
                min_low=float(np.min(lows)),
                max_close=float(np.max(closes)),
                min_close=float(np.min(closes)),
                median_close=float(np.median(closes)),
                degenerate=True,
                validity=VALIDITY_DEGRADED_DEGENERATE_REFERENCE,
                validity_detail=detail,
                closes=tuple(float(x) for x in all_closes),
                highs=tuple(float(x) for x in all_highs),
                lows=tuple(float(x) for x in all_lows),
                opens=tuple(float(x) for x in all_opens),
                valid_mask=tuple(bool(x) for x in valid_mask),
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

    if coverage < config.min_reference_coverage:
        validity = VALIDITY_DEGRADED_REFERENCE_COVERAGE
        detail = (
            f"coverage {coverage:.4f} < required "
            f"{config.min_reference_coverage:.4f} ({n_valid}/{k})"
        )

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
        median_close=float(np.median(closes)),
        degenerate=degenerate,
        validity=validity,
        validity_detail=detail,
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
    """
    if ref.w is None or ref.n_valid == 0:
        return {
            "max_close_gap_w": None,
            "median_close_gap_w": None,
            "envelope_covered_fraction": None,
        }

    w = float(ref.w)
    gaps: list[float] = []
    prev: float | None = None
    intervals: list[list[float]] = []
    for i, ok in enumerate(ref.valid_mask):
        if not ok:
            continue
        if prev is not None:
            gaps.append(abs(ref.closes[i] - prev))
        prev = ref.closes[i]
        intervals.append([ref.lows[i], ref.highs[i]])

    intervals.sort()
    merged: list[list[float]] = []
    for lo, hi in intervals:
        if merged and lo <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], hi)
        else:
            merged.append([lo, hi])
    covered = sum(hi - lo for lo, hi in merged)
    envelope = merged[-1][1] - merged[0][0] if merged else 0.0

    return {
        "max_close_gap_w": (max(gaps) / w) if gaps else 0.0,
        "median_close_gap_w": (float(np.median(gaps)) / w) if gaps else 0.0,
        "envelope_covered_fraction": (covered / envelope) if envelope > 0 else 1.0,
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
        hist = list(novelty_history)[-(config.acceptance_window - 1):]
        trace = hist + [novelty]
        acceptance = float(sum(trace) / len(trace))
    else:
        acceptance = novelty

    base.update(
        revisit_episodes=episodes,
        occupancy=occupancy,
        longest_inner_run=longest,
        novelty=novelty,
        novelty_class=nclass,
        acceptance_trace=acceptance if acceptance is not None else novelty,        frontier_progress=frontier,
        frontier_progress_close=frontier_close,
        days_since_best_frontier=days_since,
        frontier_change_3=(frontier - _frontier_at(bars, ref, max(ref.anchor_index, t - 3), config)),
        progress_3_w=progress_signed,
        progress_amplitude_3_w=progress_amp,
        range_3_w=range_3,
        bars_since_significant_progress=bars_since_progress,
        stall_flag=stall,
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
    anchor_policy: str = ANCHOR_FIRST_PROBE_WINS,
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
    """
    config = config or PTMConfig()
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
