"""Deterministic synthetic OHLC fixtures for the PTM v0.2 engineering review.

Issue #185.  Every fixture is a pure function of a frozen constant list: no
randomness, no clock, no network, no market data.  These are *constructed*
paths, not observations of any instrument, and they carry no empirical claim.

Sophira's published v0.2 readouts (design comment #6117510142) came from an
artificial fixture that was not handed over with the issue text.  The
``wide_box_*`` fixtures below are an INDEPENDENT reconstruction from the
written definition; the finding document reports where they reproduce the
published pattern and explicitly does not claim bar-for-bar reproduction.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Sequence

from ptm_territory import (
    Bar,
    PTMConfig,
    ZERO_WIDTH_FAIL_CLOSED,
    ZERO_WIDTH_TICK_FALLBACK,
)

BOX_LO = 100.0
BOX_HI = 120.0
BOX_CYCLES = 6
BOX_BARS_PER_LEG = 10
BOX_REFERENCE_BARS = BOX_CYCLES * 2 * BOX_BARS_PER_LEG  # 120


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------


def make_bars(
    closes: Sequence[float],
    start_open: float | None = None,
    wick: float = 0.0,
    label_offset: int = 0,
    label_prefix: str = "b",
) -> list[Bar]:
    """Turn a close path into OHLC bars with no wicks unless ``wick`` > 0.

    ``open`` is the previous close, ``high = max(open, close) + wick`` and
    ``low = min(open, close) - wick``.  Deterministic and gap-honest: the bar
    range is exactly what the fixture says it is; no cross-bar path is implied.
    """
    bars: list[Bar] = []
    prev = float(start_open) if start_open is not None else float(closes[0])
    for i, c in enumerate(closes):
        c = float(c)
        o = prev
        h = max(o, c) + float(wick)
        l = min(o, c) - float(wick)
        bars.append(
            Bar(open=o, high=h, low=l, close=c, valid=True,
                label=f"{label_prefix}{label_offset + i}")
        )
        prev = c
    return bars


def relabel(bars: Sequence[Bar], prefix: str = "b") -> list[Bar]:
    return [replace(b, label=f"{prefix}{i}") for i, b in enumerate(bars)]


def box_reference_closes(
    cycles: int = BOX_CYCLES,
    bars_per_leg: int = BOX_BARS_PER_LEG,
    lo: float = BOX_LO,
    hi: float = BOX_HI,
) -> list[float]:
    """Closes of a symmetric ``lo``-``hi`` box: up-leg then down-leg, repeated.

    With the defaults this is exactly 120 closes = 6 full sweeps, each sweep
    taking 20 bars.  The peak close of every up-leg is exactly ``hi`` and the
    trough close of every down-leg is exactly ``lo``, so the frozen reference
    high is exactly 120.0 and the historical low is exactly 100.0.
    """
    closes: list[float] = []
    step = (hi - lo) / float(bars_per_leg)
    for _ in range(cycles):
        for i in range(1, bars_per_leg + 1):
            closes.append(lo + step * i)
        for i in range(1, bars_per_leg + 1):
            closes.append(hi - step * i)
    return closes


def box_reference(wicks: float = 0.0) -> list[Bar]:
    closes = box_reference_closes()
    return make_bars(closes, start_open=BOX_LO, wick=wicks, label_prefix="ref")


def ramp(start: float, end: float, n: int) -> list[float]:
    """``n`` linearly interpolated closes from just-after ``start`` to ``end``."""
    if n <= 0:
        return []
    return [start + (end - start) * (i + 1) / float(n) for i in range(n)]


@dataclass(frozen=True)
class Fixture:
    name: str
    description: str
    reference: list[Bar]
    post: list[Bar]
    probe_index: int
    direction: int
    config: PTMConfig

    @property
    def bars(self) -> list[Bar]:
        return relabel(list(self.reference) + list(self.post))

    @property
    def reference_end(self) -> int:
        return len(self.reference)

    @property
    def probe_offset(self) -> int:
        """Probe index relative to the first post-reference bar."""
        return self.probe_index - self.reference_end


def _fixture(
    name: str,
    description: str,
    post_closes: Sequence[float],
    *,
    reference: list[Bar] | None = None,
    direction: int = 1,
    config: PTMConfig | None = None,
    probe_index: int | None = None,
    wick: float = 0.0,
    start_open: float | None = None,
) -> Fixture:
    ref = list(reference) if reference is not None else box_reference()
    ref = relabel(ref, "b")
    post = make_bars(
        post_closes,
        start_open=(start_open if start_open is not None
                    else (ref[-1].close if ref else float(post_closes[0]))),
        wick=wick,
        label_prefix="b",
    )
    start = len(ref)
    post = [replace(b, label=f"b{start + i}") for i, b in enumerate(post)]
    idx = start if probe_index is None else probe_index
    return Fixture(
        name=name,
        description=description,
        reference=ref,
        post=post,
        probe_index=idx,
        direction=direction,
        config=config or PTMConfig(),
    )


# ---------------------------------------------------------------------------
# Required scenario 1-9 (long side)
# ---------------------------------------------------------------------------


def wide_box_traversal() -> Fixture:
    """Large 100-120 box; apparent strong rally to 118/119/120.01 inside it."""
    post: list[float] = []
    post += ramp(100.0, 118.0, 9)          # "strong" leg inside the box
    post += ramp(118.0, 100.0, 9)          # full return to the floor
    post += ramp(100.0, 119.0, 10)         # one bid higher, still inside
    post += ramp(119.0, 100.0, 10)
    post += ramp(100.0, 120.01, 11)        # one tick above the frozen high
    post += ramp(120.01, 116.0, 4)
    return _fixture(
        "wide_box_traversal",
        "120-bar 100-120 box (6 sweeps) then repeated intrabox traversals that "
        "look like a strong rally; ends one tick above the frozen high.",
        post,
    )


def true_trend() -> Fixture:
    """Price leaves the frozen envelope and keeps going 121 -> 129.

    The first eight post-anchor closes are byte-identical to ``fake_breakout``
    up to and including the first close beyond the frozen envelope (121.6).
    That shared prefix is deliberate: the design cannot know the future at
    that close, and the tests assert the two observations are identical there.
    """
    return _fixture(
        "true_trend",
        "Box reference then a monotone escape above the frozen high.",
        [103, 106, 109, 112, 115, 118, 120, 121.6, 123, 126, 129],
    )


def fake_breakout() -> Fixture:
    """Same first escape close as ``true_trend``, then immediate failure."""
    return _fixture(
        "fake_breakout",
        "Box reference then a breakout to 121.6 and an immediate slide back "
        "into the repeatedly visited region at 116.",
        [103, 106, 109, 112, 115, 118, 120, 121.6, 120, 118, 116],
    )


def healthy_retest() -> Fixture:
    """Escape, one retest into the old envelope, then continuation."""
    return _fixture(
        "healthy_retest",
        "Box reference then escape to 123-124, a retest to 118, then "
        "continuation to 127.",
        [103, 106, 109, 112, 115, 118, 121, 123, 124, 122, 120, 118, 119, 121, 124, 127],
    )


def one_tick_breakout() -> Fixture:
    """Only one minimum tick above the frozen high; no signal discontinuity."""
    return _fixture(
        "one_tick_breakout",
        "Approach the frozen high and step one tick (0.01) beyond it; the "
        "inner/outer fuzzy band must not create a hard discontinuity.",
        [110, 115, 117, 118, 119, 119.5, 119.9, 119.99, 120.0, 120.01, 120.02],
        config=PTMConfig(tick=0.01),
    )


def post_breakout_stall() -> Fixture:
    """Escape to 124.6 then 18 identical closes: novelty stays pinned at 1.0."""
    post = [103, 106, 109, 112, 115, 118, 121, 123, 124.6] + [124.6] * 18
    return _fixture(
        "post_breakout_stall",
        "Escapes to 124.6 and then goes completely flat for 18 bars -- the "
        "known 'high novelty without progress' failure mode.",
        post,
    )


def creeping_stall() -> Fixture:
    """Escape then 18 consecutive +0.01 ticks: naive frontier age resets daily."""
    post = [103, 106, 109, 112, 115, 118, 121, 123, 124.6]
    post += [124.6 + 0.01 * (i + 1) for i in range(18)]
    return _fixture(
        "creeping_stall",
        "Escapes and then creeps +0.01 per bar for 18 bars, resetting naive "
        "frontier age every day.  Progress amplitude must stay separate.",
        post,
    )


def slow_trend() -> Fixture:
    """A patient +0.5/bar advance; the indicator must not only reward spikes."""
    return _fixture(
        "slow_trend",
        "Box reference then a slow +0.5 per bar advance from 100 to 130.",
        [100.0 + 0.5 * (i + 1) for i in range(60)],
    )


def long_trend_unbounded_novelty() -> Fixture:
    """A very long one-way trend with a frozen reference: novelty never decays."""
    return _fixture(
        "long_trend_unbounded_novelty",
        "250-bar one-way advance; the frozen reference never slides, so "
        "novelty stays 1.0 forever regardless of how old the trend is.",
        [100.0 + 0.25 * (i + 1) for i in range(250)],
    )


# ---------------------------------------------------------------------------
# Short mirror
# ---------------------------------------------------------------------------


def mirror_bars(bars: Sequence[Bar], pivot: float) -> list[Bar]:
    """Reflect a bar series through a constant price pivot.

    long low/high become short high/low; this is the exact code-symmetry
    transform for a long-vs-short probe.
    """
    return [
        Bar(
            open=2.0 * pivot - b.open,
            high=2.0 * pivot - b.low,
            low=2.0 * pivot - b.high,
            close=2.0 * pivot - b.close,
            valid=b.valid,
            label=b.label,
        )
        for b in bars
    ]


def short_mirror_of(fixture: Fixture, pivot: float = 110.0) -> Fixture:
    return Fixture(
        name=f"{fixture.name}__short_mirror",
        description=f"Exact price-reflection mirror of {fixture.name} "
                    f"(pivot {pivot}), direction = short.",
        reference=mirror_bars(fixture.reference, pivot),
        post=mirror_bars(fixture.post, pivot),
        probe_index=fixture.probe_index,
        direction=-1,
        config=fixture.config,
    )


# ---------------------------------------------------------------------------
# Required scenario 9: data integrity
# ---------------------------------------------------------------------------


def missing_reference_bars(gap_every: int = 15) -> Fixture:
    """True trend with 8 of the 120 reference bars marked invalid (missing)."""
    ref = box_reference()
    ref = [replace(b, valid=False) if (i % gap_every == 14) else b for i, b in enumerate(ref)]
    return _fixture(
        "missing_reference_bars",
        "True-trend path whose 120-bar reference has 8 missing bars "
        "(coverage 112/120); must degrade, not silently claim new territory.",
        [103, 106, 109, 112, 115, 118, 120, 121.6, 123, 126, 129],
        reference=ref,
    )


def adjusted_split() -> Fixture:
    """Same path after a *consistent* 2:1 split adjustment (affine, must match)."""
    fx = true_trend()
    scale = 0.5
    return Fixture(
        name="adjusted_split",
        description="true_trend after a consistent 2:1 split adjustment "
                    "(all bars scaled by 0.5); outputs must be identical.",
        reference=[replace(b, open=b.open * scale, high=b.high * scale,
                           low=b.low * scale, close=b.close * scale)
                   for b in fx.reference],
        post=[replace(b, open=b.open * scale, high=b.high * scale,
                      low=b.low * scale, close=b.close * scale) for b in fx.post],
        probe_index=fx.probe_index,
        direction=fx.direction,
        config=fx.config,
    )


def unadjusted_split() -> Fixture:
    """Reference still in pre-split units while post-probe bars are post-split."""
    fx = true_trend()
    return Fixture(
        name="unadjusted_split",
        description="Reference in pre-split units (100-120) but post-probe bars "
                    "halved (50-65): an unadjusted split must be screened, not "
                    "reported as a brand-new territory.",
        reference=list(fx.reference),
        post=[replace(b, open=b.open * 0.5, high=b.high * 0.5,
                      low=b.low * 0.5, close=b.close * 0.5) for b in fx.post],
        probe_index=fx.probe_index,
        direction=fx.direction,
        config=fx.config,
    )


def futures_roll() -> Fixture:
    """Continuous-futures roll: the same trend printed 4x higher."""
    fx = true_trend()
    scale = 4.0
    return Fixture(
        name="futures_roll",
        description="Reference near 100-120, post-probe bars near 400-520 after "
                    "a contract roll; the roll must be screened.",
        reference=list(fx.reference),
        post=[replace(b, open=b.open * scale, high=b.high * scale,
                      low=b.low * scale, close=b.close * scale) for b in fx.post],
        probe_index=fx.probe_index,
        direction=fx.direction,
        config=fx.config,
    )


def gappy_reference() -> Fixture:
    """Sparse reference: closes teleport 100 <-> 120, bars cover only a point.

    This is the case where a *daily* download is missing most sessions.  The
    design must not infer the unobserved path (v0.1 bug), and the engineering
    review must expose that a gappy reference can OVERSTATE novelty.
    """
    closes: list[float] = []
    for i in range(120):
        closes.append(120.0 if i % 2 == 0 else 100.0)
    ref = [Bar(open=c, high=c + 0.01, low=c - 0.01, close=c, label=f"b{i}")
           for i, c in enumerate(closes)]
    return _fixture(
        "gappy_reference",
        "Sparse 120-bar reference teleporting between 100 and 120 with "
        "1-cent bars; the middle of the span was never observed as occupied.",
        [110.0, 115.0, 118.0, 121.0],
        reference=ref,
    )


def crossed_but_not_closed() -> Fixture:
    """The v0.1 aliasing case: price crosses 117/119 but never closes there.

    The reference closes only ever take the values 100, 110 and 120, while the
    bar ranges span the legs between them.  Close-only territory counting sees
    zero touches at 118 and would announce ``novelty = 1.0`` for a heavily
    traversed region -- exactly the bug v0.2 was created to fix.
    """
    closes: list[float] = []
    for _ in range(30):
        closes += [110.0, 120.0, 110.0, 100.0]
    ref = make_bars(closes, start_open=100.0, label_prefix="b")
    ref = relabel(ref, "b")
    assert len(ref) == 120
    return _fixture(
        "crossed_but_not_closed",
        "Reference whose closes are only 100/110/120 but whose bar ranges "
        "span every leg; 118 was traversed 30 times yet never closed.",
        [112.0, 115.0, 118.0, 119.0, 120.01],
        reference=ref,
    )


def degenerate_history() -> Fixture:
    """All reference closes identical: zero inter-quantile spread."""
    ref = [Bar(open=100.0, high=100.0, low=100.0, close=100.0, label=f"b{i}")
           for i in range(120)]
    return _fixture(
        "degenerate_history",
        "120 identical closes at 100 (zero width); must fail closed unless an "
        "explicit positive tick fallback is supplied.",
        [100.0, 101.0, 102.0, 103.0],
        reference=ref,
        config=PTMConfig(zero_width_policy=ZERO_WIDTH_FAIL_CLOSED),
    )


def degenerate_history_tick_fallback() -> Fixture:
    ref = [Bar(open=100.0, high=100.0, low=100.0, close=100.0, label=f"b{i}")
           for i in range(120)]
    return _fixture(
        "degenerate_history_tick_fallback",
        "Same degenerate history but with an explicit 0.01 tick fallback: "
        "numbers are produced, but no new-territory claim is allowed.",
        [100.0, 101.0, 102.0, 103.0],
        reference=ref,
        config=PTMConfig(zero_width_policy=ZERO_WIDTH_TICK_FALLBACK, tick=0.01),
    )


# ---------------------------------------------------------------------------
# Engineering-review counterexamples
# ---------------------------------------------------------------------------


def sparse_slow_box() -> Fixture:
    """The same 100-120 box traversed only 3 times in 120 bars."""
    ref = make_bars(
        box_reference_closes(cycles=3, bars_per_leg=20),
        start_open=BOX_LO,
        label_prefix="b",
    )
    ref = relabel(ref, "b")
    return _fixture(
        "sparse_slow_box",
        "Identical 100-120 box but each sweep takes 40 bars, so 120 bars holds "
        "only 3 sweeps -- revisit count is observation-density dependent.",
        ramp(100.0, 118.0, 9),
        reference=ref,
    )


def long_period_box() -> Fixture:
    """A long-established 90-130 box whose last 120 bars are one slow segment."""
    ref = make_bars(ramp(105.0, 118.0, 120), start_open=105.0, label_prefix="b")
    ref = relabel(ref, "b")
    return _fixture(
        "long_period_box",
        "Underlying regime is a long-established wide box, but the frozen 120 "
        "bars contain one slow one-way segment 105->118; price at 112 reports "
        "SPARSE even though the longer history is heavily occupied.",
        [119.0, 118.0, 117.0, 116.0, 114.0, 112.0, 110.0, 112.0, 114.0, 116.0, 118.0, 119.0],
        reference=ref,
    )


def long_wick() -> Fixture:
    """One reference bar carries a huge upper wick into genuinely new price."""
    ref = box_reference()
    ref = [replace(b, high=150.0) if i == 60 else b for i, b in enumerate(ref)]
    ref = relabel(ref, "b")
    return _fixture(
        "long_wick",
        "Box reference with ONE bar wicking to 150; price at 135 is genuinely "
        "new territory but the wick bar touches it, halving novelty.",
        [121.0, 125.0, 130.0, 135.0, 135.0],
        reference=ref,
    )


def volatility_regime_shift() -> Fixture:
    """Last 15 reference closes spike to 400: Q90 explodes, band collapses."""
    ref = box_reference()
    ref = [replace(b, open=400.0, high=400.0, low=400.0, close=400.0)
           if i >= 105 else b for i, b in enumerate(ref)]
    ref = relabel(ref, "b")
    return _fixture(
        "volatility_regime_shift",
        "Box reference whose final 15 bars print 400; Q90 of the frozen closes "
        "moves from 118 to 400, so w explodes and the inner band swallows the "
        "whole box.",
        ramp(100.0, 118.0, 9),
        reference=ref,
        start_open=100.0,
    )


# ---------------------------------------------------------------------------
# Construct-level non-duplication pairs
# ---------------------------------------------------------------------------


def nonduplication_same_path_different_reference() -> tuple[Fixture, Fixture]:
    """Identical post-anchor path, different frozen references.

    ER20 at the shared bar is identical because ER20 only looks at the last 20
    closes.  PTM novelty differs because it only looks at the frozen reference.
    """
    post = ramp(100.0, 118.0, 20)
    a = _fixture("nondup_ref_box", "Same path, reference = occupied 100-120 box.",
                 post)
    far = make_bars(ramp(200.0, 215.0, 120), start_open=200.0, label_prefix="b")
    far = relabel(far, "b")
    b = _fixture("nondup_ref_far", "Same path, reference = far-away 200-215 region.",
                 post, reference=far, start_open=100.0)
    return a, b


def nonduplication_same_reference_different_path() -> tuple[Fixture, Fixture]:
    """Identical frozen reference and identical final close, different path.

    Both arrive at 118 with 20 post-anchor bars, so PTM novelty is identical
    while ER20 differs.
    """
    smooth = ramp(100.0, 118.0, 20)
    choppy: list[float] = []
    hi, lo = 118.0, 100.0
    for i in range(20):
        hi_leg = i % 4 < 2
        frac = (i + 1) / 20.0
        choppy.append(lo + (hi - lo) * (frac if hi_leg else 1.0 - frac * 0.5))
    choppy[-1] = 118.0
    a = _fixture("nondup_path_smooth", "Smooth 20-bar arrival at 118.", smooth)
    b = _fixture("nondup_path_choppy", "Choppy 20-bar arrival at 118.", choppy)
    return a, b


# ---------------------------------------------------------------------------
# Registry used by the runner
# ---------------------------------------------------------------------------


def all_fixtures() -> list[Fixture]:
    fx: list[Fixture] = [
        wide_box_traversal(),
        true_trend(),
        fake_breakout(),
        healthy_retest(),
        one_tick_breakout(),
        post_breakout_stall(),
        creeping_stall(),
        slow_trend(),
        long_trend_unbounded_novelty(),
        short_mirror_of(true_trend()),
        short_mirror_of(wide_box_traversal()),
        missing_reference_bars(),
        adjusted_split(),
        unadjusted_split(),
        futures_roll(),
        gappy_reference(),
        crossed_but_not_closed(),
        degenerate_history(),
        degenerate_history_tick_fallback(),
        sparse_slow_box(),
        long_period_box(),
        long_wick(),
        volatility_regime_shift(),
        nonduplication_same_path_different_reference()[0],
        nonduplication_same_path_different_reference()[1],
        nonduplication_same_reference_different_path()[0],
        nonduplication_same_reference_different_path()[1],
    ]
    return fx


REQUIRED_SCENARIOS = [
    "wide_box_traversal",
    "true_trend",
    "fake_breakout",
    "healthy_retest",
    "one_tick_breakout",
    "post_breakout_stall",
    "slow_trend",
    "short_mirror_of_true_trend",
    "missing_reference_bars",
    "future_append_invariance",
]
