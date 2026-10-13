"""PTM v0.2 engineering-review tests (Issue #185).

Deterministic synthetic fixtures only.  No market data, no strategy return, no
production code, no OOS5.  Every assertion is grounded in the frozen v0.2
definition in ``ptm_territory.py`` or in a documented counterexample to it.
"""

from __future__ import annotations

import math
from dataclasses import replace

import numpy as np
import pytest

from ptm_territory import (
    ACCEPTANCE_WINDOW,
    ANCHOR_FIRST_PROBE_WINS,
    ANCHOR_REANCHOR_EACH_PROBE,
    Bar,
    COMPARABILITY_NO_COMPLETE_CYCLE,
    COMPARABILITY_OK,
    COMPARABILITY_REFERENCE_UNUSABLE,
    CYCLE_SWING_FRACTION,
    MAX_UNOBSERVED_GAP_FRACTION,
    MAX_W_OVER_SCALE,
    MIN_ENVELOPE_COVERED_FRACTION,
    MIN_REFERENCE_CYCLES,
    NOVELTY_CLASS_HEAVILY_REVISITED,
    NOVELTY_CLASS_UNVISITED,
    PTMConfig,
    Probe,
    REFERENCE_BARS,
    SCALE_STABLE,
    SCALE_UNKNOWN,
    SCALE_UNSTABLE,
    TOUCH_MIN_OVERLAP_FRACTION,
    TOUCH_RANGE_OVERLAP,
    VALIDITY_DEGRADED_DEGENERATE_REFERENCE,
    VALIDITY_DEGRADED_REFERENCE_ADEQUACY,
    VALIDITY_DEGRADED_REFERENCE_COVERAGE,
    VALIDITY_DEGRADED_SCALE_UNSTABLE,
    VALIDITY_OK,
    VALIDITY_UNKNOWN_INSUFFICIENT_HISTORY,
    VALIDITY_UNKNOWN_NONFINITE_QUERY,
    VALIDITY_UNKNOWN_NONFINITE_REFERENCE,
    VALIDITY_UNKNOWN_ZERO_BAND_WIDTH,
    build_reference,
    evaluate_episode,
    evaluate_stream,
    reference_gap_diagnostics,
)
from ptm_promotion_clock import (
    CONFIRMATION_BARS,
    PROMOTION_CONFIRMATION_FAILED,
    PROMOTION_ELIGIBLE,
    PROMOTION_NO_BREAKOUT,
    PTM_EARLIER,
    PTM_LATER,
    PTM_NOT_COMPARABLE,
    PTM_SAME_BAR,
    build_promotion_clock,
)
from ptm_territory_fixtures import (
    Fixture,
    PHASE2_SCENARIOS,
    REQUIRED_SCENARIOS,
    adjusted_split,
    all_fixtures,
    box_reference,
    creeping_stall,
    crossed_but_not_closed,
    degenerate_history,
    degenerate_history_tick_fallback,
    envelope_coverage_only,
    envelope_gap_only,
    fake_breakout,
    futures_roll,
    gappy_reference,
    healthy_retest,
    long_period_box,
    long_trend_unbounded_novelty,
    long_wick,
    low_level_scale_break_false_alarm,
    missing_reference_bars,
    negative_level_series,
    nonduplication_same_path_different_reference,
    nonduplication_same_reference_different_path,
    one_tick_breakout,
    one_way_reference_genuine_trend,
    post_breakout_stall,
    short_mirror_of,
    slow_trend,
    sparse_slow_box,
    translated_to_zero_scale,
    true_trend,
    unadjusted_split,
    volatility_regime_shift,
    wide_box_traversal,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def run(fixture: Fixture, config: PTMConfig | None = None):
    return evaluate_episode(
        fixture.bars, fixture.probe_index, fixture.direction, config or fixture.config
    )


def obs_at_close(ep, close: float, occurrence: int = 0, tol: float = 1e-9):
    hits = [o for o in ep.observations if abs(o.close - close) <= tol]
    assert hits, f"close {close} never observed; closes={[o.close for o in ep.observations]}"
    return hits[occurrence]


def structural_escape_bar(fixture: Fixture, ep) -> int | None:
    """First post-anchor bar whose range traded beyond the frozen envelope."""
    ref_high = ep.reference.max_high
    ref_low = ep.reference.min_low
    for i in range(fixture.probe_index, len(fixture.bars)):
        bar = fixture.bars[i]
        if fixture.direction > 0 and bar.high > ref_high:
            return i
        if fixture.direction < 0 and bar.low < ref_low:
            return i
    return None


def er(closes) -> float:
    closes = list(closes)
    denom = sum(abs(b - a) for a, b in zip(closes, closes[1:]))
    if denom == 0.0:
        return 0.0
    return abs(closes[-1] - closes[0]) / denom


# ===========================================================================
# 1. Frozen reference + causal construction
# ===========================================================================


def test_reference_is_exactly_the_120_completed_pre_probe_bars():
    fx = true_trend()
    ep = run(fx)
    ref = ep.reference
    assert ref.anchor_index == fx.probe_index == 120
    assert REFERENCE_BARS == 120
    assert len(ref.closes) == 120
    expected = [b.close for b in fx.bars[0:120]]
    assert list(ref.closes) == pytest.approx(expected)
    assert ref.max_high == pytest.approx(120.0)
    assert ref.min_low == pytest.approx(100.0)
    assert ref.validity == VALIDITY_OK


def test_radius_is_the_frozen_quantile_formula():
    ep = run(true_trend())
    closes = np.asarray(ep.reference.closes, dtype=float)
    expected_w = (
        np.quantile(closes, 0.90, method="linear")
        - np.quantile(closes, 0.10, method="linear")
    ) / 20.0
    assert ep.reference.w == pytest.approx(expected_w)
    assert ep.reference.w == pytest.approx(0.8)


def test_bands_are_query_centred_and_outer_is_twice_inner():
    ep = run(true_trend())
    for o in ep.observations:
        w = o.w
        assert o.inner_low == pytest.approx(o.close - w)
        assert o.inner_high == pytest.approx(o.close + w)
        assert o.outer_low == pytest.approx(o.close - 2 * w)
        assert o.outer_high == pytest.approx(o.close + 2 * w)


# ===========================================================================
# 2. Reproduction of the published v0.2 readouts (independent fixture)
# ===========================================================================


@pytest.mark.parametrize("close", [118.0, 119.0, 120.01])
def test_published_wide_box_readout(close):
    ep = run(wide_box_traversal())
    o = obs_at_close(ep, close)
    assert o.revisit_episodes == 6
    assert o.novelty == pytest.approx(1.0 / 7.0, rel=1e-12)
    assert o.novelty_class == NOVELTY_CLASS_HEAVILY_REVISITED
    assert o.is_new_territory_claim is False


def test_published_fake_breakout_readout():
    ep = run(fake_breakout())
    o = obs_at_close(ep, 116.0)
    assert o.revisit_episodes == 12
    assert o.novelty == pytest.approx(1.0 / 13.0, rel=1e-12)


def test_published_escape_readout():
    ep = run(true_trend())
    o = obs_at_close(ep, 121.6)
    assert o.revisit_episodes == 0
    assert o.novelty == pytest.approx(1.0)
    assert o.novelty_class == NOVELTY_CLASS_UNVISITED
    assert o.is_new_territory_claim is True


def test_reproduction_is_independent_not_a_claims_of_original_fixture():
    # The published numbers came from an unavailable original fixture.  This
    # test only pins that OUR independent fixture is the one that reproduces
    # them; it is not evidence about any market.
    ep = run(wide_box_traversal())
    assert len(ep.reference.closes) == 120
    assert obs_at_close(ep, 118.0).revisit_episodes == 6


# ===========================================================================
# 3. Scenario 1-2: wide box vs true trend
# ===========================================================================


def test_wide_box_never_claims_new_territory():
    ep = run(wide_box_traversal())
    assert ep.first_new_territory_bar is None
    assert all(not o.is_new_territory_claim for o in ep.observations)


def test_true_trend_first_recognition_has_zero_latency():
    fx = true_trend()
    ep = run(fx)
    escape = structural_escape_bar(fx, ep)
    first = ep.first_new_territory_bar
    assert escape is not None and first is not None
    assert first == escape, (
        f"first new-territory claim at {first}, structural escape at {escape}"
    )
    assert ep.first_unvisited_bar == escape


def test_revisit_and_occupancy_are_reported_separately():
    ep = run(wide_box_traversal())
    o = obs_at_close(ep, 118.0)
    assert o.revisit_episodes is not None and o.occupancy is not None
    assert o.occupancy == pytest.approx(24.0 / 120.0)
    # Low revisit count with non-trivial occupancy is a distinct signature.
    lp = run(long_period_box())
    o2 = obs_at_close(lp, 112.0)
    assert o2.revisit_episodes <= 1
    assert o2.occupancy is not None and o2.occupancy > 0.0


# ===========================================================================
# 4. Scenario 3-4: fake breakout and healthy retest
# ===========================================================================


def test_fake_breakout_degrades_immediately():
    ep = run(fake_breakout())
    assert obs_at_close(ep, 121.6).novelty == pytest.approx(1.0)
    assert obs_at_close(ep, 120.0).novelty == pytest.approx(1.0 / 7.0)
    assert obs_at_close(ep, 118.0).novelty == pytest.approx(1.0 / 7.0)
    assert obs_at_close(ep, 116.0).novelty == pytest.approx(1.0 / 13.0)
    first_claim = ep.first_new_territory_bar
    assert first_claim is not None
    # Deterioration is visible within three completed closes of the escape.
    assert all(
        o.is_new_territory_claim is False
        for o in ep.observations
        if o.bar_index > first_claim + 2
    )


def test_healthy_retest_weakens_then_recovers():
    ep = run(healthy_retest())
    retest = obs_at_close(ep, 118.0, occurrence=1)
    assert retest.revisit_episodes == 6
    assert retest.novelty == pytest.approx(1.0 / 7.0)
    # The trace legitimately lags rejection: it still carries the preceding
    # escape closers, which is exactly why current novelty is reported too.
    assert retest.acceptance_trace > retest.novelty
    assert retest.acceptance_trace == pytest.approx((1.0 + 1.0 / 7.0 + 1.0 / 7.0) / 3.0)
    tail = [o for o in ep.observations if o.bar_index >= retest.bar_index]
    assert tail[-1].novelty == pytest.approx(1.0)
    assert tail[-1].acceptance_trace == pytest.approx(1.0)
    # The trace climbs back rather than hard-resetting.
    seen = [o.acceptance_trace for o in tail]
    assert seen[-1] >= seen[0]
    assert min(seen) == pytest.approx(1.0 / 7.0)


# ===========================================================================
# 5. Scenario 5: one-tick breakout has no discontinuity
# ===========================================================================


def test_one_tick_breakout_has_no_signal_discontinuity():
    ep = run(one_tick_breakout())
    closes = [119.99, 120.0, 120.01, 120.02]
    R = [obs_at_close(ep, c).revisit_episodes for c in closes]
    N = [obs_at_close(ep, c).novelty for c in closes]
    F = [obs_at_close(ep, c).frontier_progress for c in closes]
    assert R == [6, 6, 6, 6]
    assert len(set(round(x, 12) for x in N)) == 1
    assert F[0] < 0.0 < F[3]
    assert max(abs(F[i + 1] - F[i]) for i in range(3)) < 0.05
    # Not a Donchian gate: nothing claims new territory one tick above the high.
    assert all(not obs_at_close(ep, c).is_new_territory_claim for c in closes)


# ===========================================================================
# 6. Scenario 6: post-breakout stagnation
# ===========================================================================


def test_post_breakout_stall_pins_novelty_at_one():
    ep = run(post_breakout_stall())
    last = ep.observations[-1]
    assert last.novelty == pytest.approx(1.0)
    assert last.revisit_episodes == 0
    assert last.novelty_class == NOVELTY_CLASS_UNVISITED
    assert last.bars_since_significant_progress >= 10
    assert last.stall_flag is True
    assert last.is_new_territory_claim is True  # the defect, stated plainly


def test_creeping_stall_defeats_naive_frontier_age():
    ep = run(creeping_stall())
    last = ep.observations[-1]
    assert last.days_since_best_frontier == 0        # every bar a tiny new high
    assert last.range_3_w is not None and last.range_3_w < 0.1
    assert last.stall_flag is True                   # amplitude diagnostic works
    assert last.novelty == pytest.approx(1.0)


def test_slow_trend_is_not_penalised_for_speed():
    ep = run(slow_trend())
    first = ep.first_new_territory_bar
    assert first is not None
    o = ep.observations[first - ep.anchor_index]
    assert o.revisit_episodes == 0
    assert o.progress_amplitude_3_w is not None and o.progress_amplitude_3_w < 3.0
    assert o.stall_flag is False


# ===========================================================================
# 7. Frozen-reference unbounded novelty (known defect)
# ===========================================================================


def test_long_trend_novelty_never_decays():
    fx = long_trend_unbounded_novelty()
    ep = run(fx)
    last = ep.observations[-1]
    assert last.bar_index - ep.anchor_index == 249
    assert last.novelty == pytest.approx(1.0)
    assert last.revisit_episodes == 0
    assert last.days_since_best_frontier == 0
    assert last.is_new_territory_claim is True


# ===========================================================================
# 8. Scenario 8: short mirror symmetry
# ===========================================================================


@pytest.mark.parametrize("factory", [true_trend, wide_box_traversal])
def test_short_mirror_is_exact(factory):
    long_fx = factory()
    long_ep = run(long_fx)
    short_fx = short_mirror_of(long_fx)
    short_ep = run(short_fx)
    assert len(long_ep.observations) == len(short_ep.observations)
    for a, b in zip(long_ep.observations, short_ep.observations):
        assert a.revisit_episodes == b.revisit_episodes
        assert a.occupancy == pytest.approx(b.occupancy)
        assert a.longest_inner_run == b.longest_inner_run
        assert a.novelty == pytest.approx(b.novelty)
        assert a.novelty_class == b.novelty_class
        assert a.frontier_progress == pytest.approx(b.frontier_progress)
        assert a.is_new_territory_claim == b.is_new_territory_claim
    assert long_ep.first_new_territory_bar == short_ep.first_new_territory_bar


# ===========================================================================
# 9. Scenario 9: data integrity, split / roll / gaps
# ===========================================================================


def test_missing_reference_bars_degrade_and_fail_closed():
    fx = missing_reference_bars()
    ep = run(fx)
    assert ep.reference.validity == VALIDITY_DEGRADED_REFERENCE_COVERAGE
    assert ep.reference.coverage == pytest.approx(112.0 / 120.0)
    assert ep.reference.n_valid == 112
    # Numbers still exist for diagnosis ...
    assert all(o.novelty is not None for o in ep.observations)
    # ... but nothing may claim genuinely new territory.
    assert all(not o.is_new_territory_claim for o in ep.observations)
    assert ep.first_new_territory_bar is None


def test_consistent_split_adjustment_is_affine_invariant():
    a = run(true_trend())
    b = run(adjusted_split())
    for x, y in zip(a.observations, b.observations):
        assert x.revisit_episodes == y.revisit_episodes
        assert x.occupancy == pytest.approx(y.occupancy)
        assert x.novelty == pytest.approx(y.novelty)
        assert x.novelty_class == y.novelty_class
        assert x.frontier_progress == pytest.approx(y.frontier_progress)


def test_affine_price_unit_change_is_invariant():
    fx = true_trend()
    scale, offset = 3.0, 7.0
    bars = [
        replace(
            b,
            open=b.open * scale + offset,
            high=b.high * scale + offset,
            low=b.low * scale + offset,
            close=b.close * scale + offset,
        )
        for b in fx.bars
    ]
    ep_a = run(fx)
    ep_b = evaluate_episode(bars, fx.probe_index, fx.direction, fx.config)
    for x, y in zip(ep_a.observations, ep_b.observations):
        assert x.revisit_episodes == y.revisit_episodes
        assert x.occupancy == pytest.approx(y.occupancy)
        assert x.novelty == pytest.approx(y.novelty)
        assert x.frontier_progress == pytest.approx(y.frontier_progress)


def test_unadjusted_split_is_screened():
    ep = run(unadjusted_split())
    post = [o for o in ep.observations if o.bar_index >= ep.anchor_index]
    assert post, "episode produced no post-anchor observations"
    assert all(o.suspect_scale_break for o in post)
    # The screen latches: once a unit discontinuity is observed, the frozen
    # reference is no longer trusted for the rest of the episode.
    assert post[0].suspect_scale_break is True
    # Without the screen the frozen math would have announced fresh territory.
    assert obs_at_close(ep, 60.8).revisit_episodes == 0


def test_futures_roll_is_screened():
    ep = run(futures_roll())
    assert all(o.suspect_scale_break for o in ep.observations)


def test_scale_break_screen_is_reflection_symmetric():
    # Regression: keying the latch on the level vs the reference median made a
    # sustained +60% trend keep its new-territory claims while the mirrored
    # -37.5% trend had them suppressed, because a price ratio is not invariant
    # under arithmetic reflection.  A split/roll is an overnight re-basing, so
    # only the one-bar jump may latch.
    fx = long_trend_unbounded_novelty()
    m = 200.0
    mirrored = [
        Bar(open=m - b.open, high=m - b.low, low=m - b.high, close=m - b.close,
            valid=b.valid, label=b.label)
        for b in fx.bars
    ]
    up = evaluate_episode(fx.bars, fx.probe_index, 1, fx.config)
    dn = evaluate_episode(mirrored, fx.probe_index, -1, fx.config)
    assert [o.is_new_territory_claim for o in up.observations] == \
        [o.is_new_territory_claim for o in dn.observations]
    assert [o.suspect_scale_break for o in up.observations] == \
        [o.suspect_scale_break for o in dn.observations]
    assert all(not o.suspect_scale_break for o in up.observations)
    assert any(o.is_new_territory_claim for o in up.observations)
    # the drift ratio is still surfaced, just not gated on
    assert any(o.drift_scale_warning for o in dn.observations)


def test_scale_break_screen_is_multiplicative_not_affine():
    # Known, documented limitation.  A split or roll is a MULTIPLICATIVE
    # re-basing, which is what the screen detects, so the screen is invariant
    # under price inversion but NOT under arithmetic reflection.  A halved
    # path latches; the reflected path is a x1.485 one-bar jump, which sits
    # just inside the 1.5 band and does not.  The consequence is unequal
    # treatment of an equally large one-bar rally, and it is recorded here
    # rather than hidden: see the finding doc defect register D8.
    from ptm_territory import scale_ratio_break

    assert scale_ratio_break(51.5, 100.0, 1.5) is True
    assert scale_ratio_break(148.5, 100.0, 1.5) is False
    # ... but the screen IS symmetric in the reciprocal sense: a 2.5x re-basing
    # and a 0.4x re-basing are both caught by the same factor.
    assert scale_ratio_break(250.0, 100.0, 2.0) is True
    assert scale_ratio_break(40.0, 100.0, 2.0) is True
    assert scale_ratio_break(194.0, 100.0, 2.0) is False
    assert scale_ratio_break(51.5, 100.0, 2.0) is False


def test_scale_break_screen_is_a_prompt_not_a_gate():
    # A genuine -55% move is indistinguishable from a 2:1 split using price
    # alone; documented false positive, so the screen must never gate trading.
    from ptm_territory import scale_ratio_break

    assert scale_ratio_break(45.0, 100.0, 1.5) is True
    # ... and any split milder than the factor slips through: documented
    # false negative (a 3:2 split leaves 66.7, which sits on the boundary).
    assert scale_ratio_break(70.0, 100.0, 1.5) is False


def test_latched_scale_break_blocks_new_territory_claims():
    # A suspect price unit must not be reported as brand-new territory, even
    # though the numbers stay available for diagnostics.
    for fx in (unadjusted_split(), futures_roll()):
        ep = run(fx)
        assert any(o.suspect_scale_break for o in ep.observations), fx.name
        assert all(not o.is_new_territory_claim for o in ep.observations), fx.name
        # the numbers themselves are still published for diagnosis
        assert all(o.novelty is not None for o in ep.observations), fx.name


def test_inclusive_touch_counts_an_exact_band_edge():
    # v0.2 is inclusive: high >= P-w and low <= P+w.  At close 115.20 with
    # w = 0.8 the inner high is exactly 116.00, and 12 reference bars have
    # low == 116.00.  A strict (> 0) overlap test silently drops them.
    ep = run(wide_box_traversal())
    o = obs_at_close(ep, 115.2)
    assert o.inner_high == pytest.approx(116.0)
    assert o.occupancy == pytest.approx(0.20)
    assert o.revisit_episodes == 12


def test_a_price_equal_to_every_reference_bar_is_visited():
    # All 120 reference bars sit exactly at 100.0.  Under a strict overlap
    # test the query price 100.0 is reported as UNVISITED (novelty 1.0) even
    # though every bar is exactly there.
    ep = run(degenerate_history_tick_fallback())
    o = obs_at_close(ep, 100.0)
    assert o.w == pytest.approx(0.01)
    assert o.revisit_episodes == 1
    assert o.novelty == pytest.approx(0.5)
    assert o.novelty_class == "SPARSE"
    assert o.is_new_territory_claim is False


def test_exact_band_edge_cannot_create_a_false_claim():
    # Two reference bars touch the inner band only at its exact lower edge
    # (high == P-w).  The inclusive predicate counts them; a strict one would
    # report R = 0 and emit a false new-territory claim.
    ref = (
        [Bar(open=100.0, high=100.0, low=100.0, close=100.0) for _ in range(58)]
        + [Bar(open=100.0, high=117.0, low=100.0, close=117.0)]
        + [Bar(open=100.0, high=103.0, low=100.0, close=103.0)]
        + [Bar(open=100.0, high=117.0, low=100.0, close=117.0)]
        + [Bar(open=120.0, high=120.0, low=120.0, close=120.0) for _ in range(59)]
    )
    probe = Bar(open=120.0, high=118.0, low=118.0, close=118.0)
    ep = evaluate_episode(ref + [probe], 120, 1)
    o = ep.observations[0]
    assert o.w == pytest.approx(1.0)
    assert o.inner_low == pytest.approx(117.0)
    assert o.revisit_episodes == 2
    assert o.novelty == pytest.approx(1.0 / 3.0)
    assert o.is_new_territory_claim is False


def test_anchor_past_end_of_data_is_unknown():
    bars = [Bar(open=100.0, high=100.0 + (i % 5), low=99.0, close=100.0 + (i % 5))
            for i in range(120)]
    for anchor in (121, 123, 400):
        ref = build_reference(bars, anchor, 1)
        assert ref.validity == VALIDITY_UNKNOWN_INSUFFICIENT_HISTORY, anchor
        assert ref.w is None
        assert ref.is_usable is False


def test_lowered_min_reference_coverage_cannot_reopen_a_claim():
    # coverage < 1.0 must block the claim independently of the config knob.
    ep = evaluate_episode(missing_reference_bars().bars, 120, 1,
                          PTMConfig(min_reference_coverage=0.0))
    assert ep.reference.coverage < 1.0
    assert ep.reference.allows_new_territory_claim is False
    assert all(not o.is_new_territory_claim for o in ep.observations)


def test_no_cross_bar_path_is_inferred():
    ep = run(gappy_reference())
    o = obs_at_close(ep, 110.0)
    # v0.1 close-only would also say "unvisited"; the point is that the design
    # makes no claim about the unobserved path between 100 and 120.
    assert o.revisit_episodes == 0
    diag = reference_gap_diagnostics(ep.reference)
    assert diag["max_close_gap_w"] > 10.0
    assert diag["envelope_covered_fraction"] < 0.05


def _v01_close_only_episodes(ref, p: float, w: float, outer_mult=2.0) -> int:
    """Historical CLOSE-only episode count: the rejected v0.1 semantics."""
    episodes = 0
    armed = True
    for i, ok in enumerate(ref.valid_mask):
        if not ok:
            continue
        c = ref.closes[i]
        if abs(c - p) <= w:
            if armed:
                episodes += 1
                armed = False
        elif abs(c - p) > outer_mult * w:
            armed = True
    return episodes


def test_ohlc_range_touch_fixes_the_v01_close_only_aliasing():
    # Reference closes are only 100/110/120, but the bar ranges span every
    # leg, so 118 was traversed 30 times without ever being a close.
    ep = run(crossed_but_not_closed())
    ref = ep.reference
    assert set(round(c, 6) for c in ref.closes) == {100.0, 110.0, 120.0}
    o = obs_at_close(ep, 118.0)
    assert o.revisit_episodes == 30
    assert o.novelty == pytest.approx(1.0 / 31.0)

    close_only = _v01_close_only_episodes(ref, 118.0, ref.w)
    assert close_only == 0, "the v0.1 close-only semantics must be reproduced here"
    assert 1.0 / (1.0 + close_only) == pytest.approx(1.0), (
        "v0.1 would have announced novelty 1.0 for heavily traversed territory"
    )
    assert o.novelty < 0.05


def test_dense_reference_has_full_envelope_coverage():
    ep = run(true_trend())
    diag = reference_gap_diagnostics(ep.reference)
    assert diag["envelope_covered_fraction"] == pytest.approx(1.0)
    assert diag["max_close_gap_w"] == pytest.approx(2.5)


# ===========================================================================
# 10. Fail-closed validity
# ===========================================================================


def test_degenerate_history_fails_closed():
    ep = run(degenerate_history())
    assert ep.reference.validity == VALIDITY_UNKNOWN_ZERO_BAND_WIDTH
    assert ep.reference.w is None
    for o in ep.observations:
        assert o.novelty is None
        assert o.revisit_episodes is None
        assert o.is_new_territory_claim is False


def test_degenerate_tick_fallback_produces_numbers_but_blocks_claims():
    ep = run(degenerate_history_tick_fallback())
    assert ep.reference.validity == VALIDITY_DEGRADED_DEGENERATE_REFERENCE
    assert ep.reference.degenerate is True
    assert ep.reference.w == pytest.approx(0.01)
    assert ep.observations[-1].novelty is not None
    assert all(not o.is_new_territory_claim for o in ep.observations)


def test_insufficient_history_is_unknown():
    fx = true_trend()
    bars = fx.bars[100:]
    ref = build_reference(bars, 5, 1, fx.config)
    assert ref.validity == VALIDITY_UNKNOWN_INSUFFICIENT_HISTORY
    assert ref.is_usable is False


# ===========================================================================
# 11. Scenario 10: future-append invariance (no lookahead)
# ===========================================================================


INVARIANCE_FIXTURES = [
    wide_box_traversal,
    true_trend,
    fake_breakout,
    healthy_retest,
    slow_trend,
    long_period_box,
]


@pytest.mark.parametrize("factory", INVARIANCE_FIXTURES)
def test_future_append_invariance(factory):
    fx = factory()
    full = run(fx)
    n = len(fx.bars)
    for cut in (fx.probe_index + 1, fx.probe_index + 5, fx.probe_index + 15, n - 1):
        if cut <= fx.probe_index:
            continue
        prefix_ep = evaluate_episode(fx.bars[:cut], fx.probe_index, fx.direction, fx.config)
        keep = cut - fx.probe_index
        assert prefix_ep.observations == full.observations[:keep], (
            f"{fx.name}: appending future bars changed history at cut={cut}"
        )


def test_reference_does_not_slide_over_the_episode():
    ep = run(long_trend_unbounded_novelty())
    assert all(o.anchor_index == 120 for o in ep.observations)
    refs = {o.w for o in ep.observations}
    assert len(refs) == 1


# ===========================================================================
# 12. First-close responsiveness and acceptance maturity
# ===========================================================================


def test_signal_exists_at_the_first_known_close():
    fx = true_trend()
    ep = run(fx)
    first = ep.observations[0]
    assert first.bar_index == fx.probe_index
    assert first.novelty is not None
    assert first.evidence_bars == 1
    assert first.acceptance_trace == pytest.approx(first.novelty)


def test_acceptance_trace_uses_at_most_three_closes():
    ep = run(healthy_retest())
    novelty = [o.novelty for o in ep.observations]
    for i, o in enumerate(ep.observations):
        lo = max(0, i - (ACCEPTANCE_WINDOW - 1))
        expected = sum(novelty[lo: i + 1]) / (i - lo + 1)
        assert o.acceptance_trace == pytest.approx(expected)
        assert o.evidence_bars == min(ACCEPTANCE_WINDOW, i + 1)


def test_observable_at_close_and_actionable_next_bar():
    for fx in all_fixtures():
        ep = run(fx)
        for o in ep.observations:
            assert o.observable_at_bar == o.bar_index
            assert o.actionable_at_bar == o.bar_index + 1


# ===========================================================================
# 13. Overlapping probes and anchor management
# ===========================================================================


def test_default_anchor_policy_keeps_one_frozen_reference():
    fx = wide_box_traversal()
    probes = [Probe(fx.probe_index, 1), Probe(fx.probe_index + 5, 1),
              Probe(fx.probe_index + 10, 1), Probe(fx.probe_index + 15, 1)]
    episodes = evaluate_stream(fx.bars, probes, fx.config, ANCHOR_FIRST_PROBE_WINS)
    assert len(episodes) == 1
    assert episodes[0].anchor_index == fx.probe_index
    assert episodes[0].reprobe_indices == [
        fx.probe_index + 5, fx.probe_index + 10, fx.probe_index + 15
    ]


def test_reanchor_each_probe_resets_maturity_and_changes_the_answer():
    fx = wide_box_traversal()
    probes = [Probe(fx.probe_index + k, 1) for k in (0, 5, 10, 15)]
    first = evaluate_stream(fx.bars, probes, fx.config, ANCHOR_FIRST_PROBE_WINS)
    each = evaluate_stream(fx.bars, probes, fx.config, ANCHOR_REANCHOR_EACH_PROBE)
    assert len(each) == 4
    for ep in each:
        assert ep.observations[0].evidence_bars == 1
        assert ep.anchor_index in [p.index for p in probes]
    # At one and the same bar the default keeps the accumulated evidence
    # maturity while naive re-anchoring restarts it at 1.
    target = fx.probe_index + 15
    a = first[0].observations[target - first[0].anchor_index]
    b = each[-1].observations[0]
    assert (a.anchor_index, a.evidence_bars) == (fx.probe_index, 3)
    assert (b.anchor_index, b.evidence_bars) == (target, 1)
    assert first[0].reprobe_indices == [fx.probe_index + 5, fx.probe_index + 10, target]


# ===========================================================================
# 14. Honest representation of the irreducible first-breakout ambiguity
# ===========================================================================


def test_true_and_fake_breakout_are_identical_through_the_first_escape():
    t_ep = run(true_trend())
    f_ep = run(fake_breakout())
    escape = f_ep.first_new_territory_bar
    assert escape is not None
    shared = [o for o in f_ep.observations if o.bar_index <= escape]
    assert len(shared) > 1
    for a, b in zip(t_ep.observations, shared):
        if a.bar_index > escape:
            break
        assert a == b, f"divergence before the escape at bar {a.bar_index}"
    # ... and they diverge only after the shared close.
    assert t_ep.observations[len(shared) - 1] == f_ep.observations[len(shared) - 1]
    assert t_ep.observations[-1].novelty != f_ep.observations[-1].novelty


# ===========================================================================
# 15. Engineering counterexamples to the frozen design
# ===========================================================================


def test_revisit_count_depends_on_observation_density():
    fast = obs_at_close(run(wide_box_traversal()), 118.0)
    slow = obs_at_close(run(sparse_slow_box()), 118.0)
    assert fast.revisit_episodes == 6
    assert slow.revisit_episodes == 3
    assert slow.novelty == pytest.approx(0.25)
    assert slow.novelty > fast.novelty  # same box, "more novel" only because slower
    # A2 adds the speed-invariant view alongside the frozen values.  Raw R and
    # N differ by ~1.7x here; episodes-per-cycle differs by well under 1.3x.
    assert fast.comparability_status == COMPARABILITY_OK
    assert slow.comparability_status == COMPARABILITY_OK
    assert fast.reference_cycle_count == pytest.approx(6.0)
    assert slow.reference_cycle_count == pytest.approx(3.0)
    assert fast.episodes_per_cycle == pytest.approx(1.0)
    assert slow.episodes_per_cycle == pytest.approx(1.0)
    ratio_raw = slow.revisit_episodes / fast.revisit_episodes
    ratio_a2 = slow.episodes_per_cycle / fast.episodes_per_cycle
    assert abs(math.log(ratio_a2)) < abs(math.log(ratio_raw))


def test_long_period_box_is_reported_as_insufficient_evidence_not_new_territory():
    """A1 closes the blocking wide-box false release.

    Before A1 this fixture produced ``R=1, N=0.5, claim=True`` *inside* a
    long-established box -- exactly the failure the indicator exists to avoid.
    The frozen 120-bar window is one slow one-way segment 105 -> 118, so it
    contains no complete round trip.  The honest output is "this window is not
    evidence of a repeated region", so no claim may be emitted anywhere.
    """
    ep = run(long_period_box())
    ref = ep.reference
    o = obs_at_close(ep, 112.0)
    # The raw v0.2 numbers are untouched and still LOOK novel ...
    assert o.revisit_episodes is not None and o.revisit_episodes <= 1
    assert o.novelty is not None and o.novelty >= 0.5
    assert o.occupancy is not None and o.occupancy < 0.2
    # ... but the window holds no complete round trip, so A1 fires.
    assert ref.swing_legs == 1
    assert ref.reference_cycle_count == pytest.approx(0.5)
    assert ref.reference_adequacy_ok is False
    assert ref.validity == VALIDITY_DEGRADED_REFERENCE_ADEQUACY
    assert ref.allows_new_territory_claim is False
    assert any("complete round trips" in r for r in ref.validity_reasons)
    # A1 is the ONLY guard that catches this fixture: coverage, envelope
    # observation and scale are all healthy, which is why the defect survived.
    assert ref.coverage == pytest.approx(1.0)
    assert ref.envelope_covered_fraction == pytest.approx(1.0)
    assert ref.scale_state == SCALE_STABLE
    # No observation in the whole episode may claim new territory.
    assert all(not x.is_new_territory_claim for x in ep.observations)
    # A2 must still report "unmeasurable", never a fabricated number.
    assert o.comparability_status == COMPARABILITY_NO_COMPLETE_CYCLE
    assert o.episodes_per_cycle is None
    assert o.revisit_density is not None


def test_long_wick_overstates_occupancy_and_masks_novelty():
    wick_ep = run(long_wick())
    o = obs_at_close(wick_ep, 135.0)
    assert o.revisit_episodes == 1
    assert o.novelty == pytest.approx(0.5)
    assert o.occupancy == pytest.approx(1.0 / 120.0)

    clean = run(true_trend())
    # A clean reference has no bar anywhere near 135.
    assert max(clean.reference.highs) == pytest.approx(120.0)
    assert obs_at_close(clean, 121.6).revisit_episodes == 0


def test_volatility_regime_shift_inflates_the_zone_radius():
    clean = run(wide_box_traversal())
    shifted = run(volatility_regime_shift())
    assert clean.reference.w == pytest.approx(0.8)
    assert shifted.reference.w > 10.0
    o = obs_at_close(shifted, 118.0)
    assert o.occupancy is not None and o.occupancy > 0.7
    assert o.revisit_episodes is not None and o.revisit_episodes < clean.reference.n_valid
    assert o.novelty != pytest.approx(1.0 / 7.0)


def test_long_wick_did_not_get_screened_as_a_scale_break():
    ep = run(long_wick())
    assert all(not o.suspect_scale_break for o in ep.observations)


# ===========================================================================
# 16. Construct-level non-duplication checks
# ===========================================================================


def test_same_recent_path_different_reference_gives_different_novelty():
    a, b = nonduplication_same_path_different_reference()
    ea, eb = run(a), run(b)
    er_a = er([a.post[0].open] + [x.close for x in a.post[:20]])
    er_b = er([b.post[0].open] + [x.close for x in b.post[:20]])
    assert er_a == pytest.approx(er_b) == pytest.approx(1.0)
    assert ea.observations[-1].novelty == pytest.approx(1.0 / 7.0)
    assert eb.observations[-1].novelty == pytest.approx(1.0)
    assert ea.observations[-1].novelty != eb.observations[-1].novelty


def test_same_reference_different_path_gives_same_novelty_different_er():
    a, b = nonduplication_same_reference_different_path()
    ea, eb = run(a), run(b)
    assert ea.observations[-1].close == pytest.approx(eb.observations[-1].close)
    assert ea.observations[-1].novelty == pytest.approx(eb.observations[-1].novelty)
    er_a = er([a.reference[-1].close] + [x.close for x in a.post[:20]])
    er_b = er([b.reference[-1].close] + [x.close for x in b.post[:20]])
    assert er_a == pytest.approx(1.0)
    assert er_b < 0.5
    assert er_a != pytest.approx(er_b)


# ===========================================================================
# 17. Contract / coverage guards
# ===========================================================================


def test_forward_mutation_cannot_change_an_earlier_observation():
    # Stronger than truncation: replace every bar strictly AFTER t with
    # garbage while keeping the series length.  If any forward read existed,
    # the observation at t would move.
    checked = 0
    for fx in all_fixtures():
        full = evaluate_episode(fx.bars, fx.probe_index, fx.direction, fx.config)
        for t in range(fx.probe_index, len(fx.bars), 3):
            mut = list(fx.bars)
            for i in range(t + 1, len(mut)):
                mut[i] = Bar(open=1e9, high=1e9, low=1e9, close=1e9,
                             valid=mut[i].valid, label=mut[i].label)
            got = evaluate_episode(mut, fx.probe_index, fx.direction, fx.config)
            assert got.observations[t - fx.probe_index] == \
                full.observations[t - fx.probe_index], (fx.name, t)
            checked += 1
    assert checked > 200


def test_config_fingerprint_pins_every_free_choice():
    fp = PTMConfig().fingerprint()
    assert fp["reference_bars"] == 120
    assert fp["quantile_low"] == 0.10
    assert fp["quantile_high"] == 0.90
    assert fp["radius_divisor"] == 20.0
    assert fp["outer_multiplier"] == 2.0
    assert fp["acceptance_window"] == 3
    # A fingerprint is only useful if a changed free choice actually changes
    # it AND changes output; otherwise it is a decorative echo of constants.
    base = PTMConfig()
    fx = wide_box_traversal()
    base_obs = evaluate_episode(fx.bars, fx.probe_index, fx.direction, base)
    for knob, value in (("reference_bars", 60), ("radius_divisor", 5.0),
                        ("quantile_high", 0.75), ("outer_multiplier", 1.0)):
        variant = PTMConfig(**{knob: value})
        assert variant.fingerprint() != base.fingerprint(), knob
        alt = evaluate_episode(fx.bars, fx.probe_index, fx.direction, variant)
        assert alt.observations != base_obs.observations, knob


def test_required_scenario_names_are_actually_implemented():
    names = {fx.name for fx in all_fixtures()}
    assert "wide_box_traversal" in names
    assert "true_trend" in names
    assert "fake_breakout" in names
    assert "healthy_retest" in names
    assert "one_tick_breakout" in names
    assert "post_breakout_stall" in names
    assert "slow_trend" in names
    assert "true_trend__short_mirror" in names
    assert "wide_box_traversal__short_mirror" in names
    assert "missing_reference_bars" in names
    assert len(REQUIRED_SCENARIOS) == 10


def test_all_fixtures_are_deterministic():
    for factory in (wide_box_traversal, true_trend, fake_breakout, slow_trend):
        assert factory().bars == factory().bars


def test_no_observation_reads_a_future_bar():
    # Rebuilding the episode from a truncated series must reproduce every
    # earlier observation bit-for-bit; that is the operational no-lookahead bar.
    fx = fake_breakout()
    full = run(fx)
    for cut in range(fx.probe_index + 1, len(fx.bars)):
        part = evaluate_episode(fx.bars[:cut], fx.probe_index, fx.direction, fx.config)
        assert part.observations == full.observations[: cut - fx.probe_index]


def test_box_reference_shape_matches_the_documented_six_sweeps():
    ref = box_reference()
    assert len(ref) == 120
    assert sum(1 for b in ref if b.close == pytest.approx(120.0)) == 6
    assert sum(1 for b in ref if b.close == pytest.approx(100.0)) == 6
    assert math.isclose(max(b.high for b in ref), 120.0)
    assert math.isclose(min(b.low for b in ref), 100.0)


# ---------------------------------------------------------------------------
# Fail-closed hardening: non-finite input and caller-contract violations
# ---------------------------------------------------------------------------


def _good_reference_bars() -> list[Bar]:
    out = []
    prev = 100.0
    for i in range(120):
        c = 100.0 + (i % 20)
        out.append(Bar(open=prev, high=max(prev, c), low=min(prev, c), close=c))
        prev = c
    return out


def test_nonfinite_query_close_fails_closed():
    # A NaN query close makes every band comparison compare against NaN; a
    # naive implementation silently registers spurious touches there.
    bars = _good_reference_bars()
    nan_bar = bars[-1]
    bad = Bar(open=nan_bar.close, high=nan_bar.close, low=nan_bar.close,
              close=float("nan"))
    ep = evaluate_episode(bars + [bad], 120, 1)
    o = ep.observations[0]
    assert o.validity == VALIDITY_UNKNOWN_NONFINITE_QUERY
    assert o.novelty is None
    assert o.occupancy is None
    assert o.revisit_episodes is None
    assert o.novelty_class is None
    assert o.frontier_progress is None
    assert o.is_new_territory_claim is False


def test_nonfinite_query_high_fails_closed():
    bars = _good_reference_bars()
    bad = Bar(open=100.0, high=float("inf"), low=100.0, close=110.0)
    ep = evaluate_episode(bars + [bad], 120, 1)
    assert ep.observations[0].novelty is None
    assert ep.observations[0].is_new_territory_claim is False


def test_nonfinite_reference_high_fails_closed():
    bars = _good_reference_bars()
    bars[60] = Bar(open=100.0, high=float("nan"), low=100.0, close=110.0)
    ep = evaluate_episode(bars + [Bar(open=120.0, high=125.0, low=119.0, close=124.0)],
                          120, 1)
    assert ep.reference.validity == VALIDITY_UNKNOWN_NONFINITE_REFERENCE
    assert ep.reference.is_usable is False
    assert ep.reference.w is None
    assert ep.observations[0].novelty is None
    assert ep.observations[0].is_new_territory_claim is False


def test_all_invalid_reference_is_unknown_not_ok():
    bars = [Bar(open=100.0, high=100.0, low=100.0, close=100.0, valid=False)
            for _ in range(120)]
    ep = evaluate_episode(bars + _good_reference_bars()[:3], 120, 1)
    assert ep.reference.validity == VALIDITY_UNKNOWN_INSUFFICIENT_HISTORY
    assert ep.reference.is_usable is False
    assert ep.observations[0].novelty is None
    assert ep.observations[0].is_new_territory_claim is False


def test_short_reference_window_is_unknown():
    bars = _good_reference_bars()
    for anchor in (0, 1, 60, 119):
        ref = build_reference(bars, anchor, 1)
        assert ref.validity == VALIDITY_UNKNOWN_INSUFFICIENT_HISTORY, anchor
        assert ref.is_usable is False
        assert ref.w is None


@pytest.mark.parametrize("bad_direction", [0, 2, -2, 7])
def test_invalid_direction_is_rejected_not_silently_defaulted(bad_direction):
    # The side is a caller contract, not market data: silently coercing an
    # invalid direction to +1 would return a plausible long-side answer.
    bars = _good_reference_bars() + _good_reference_bars()[:3]
    with pytest.raises(ValueError):
        build_reference(bars, 120, bad_direction)
    with pytest.raises(ValueError):
        evaluate_episode(bars, 120, bad_direction)


# ===========================================================================
# 17. A1 -- reference adequacy (is the window evidence of a repeated region?)
# ===========================================================================


def test_a1_thresholds_are_declared_pre_outcome_and_in_the_fingerprint():
    """The safety thresholds must be frozen constants, not tuned numbers."""
    assert CYCLE_SWING_FRACTION == 0.5
    assert MIN_REFERENCE_CYCLES == 1.0
    assert MIN_ENVELOPE_COVERED_FRACTION == 0.5
    assert MAX_UNOBSERVED_GAP_FRACTION == 0.25
    fp = PTMConfig().fingerprint()
    for key in ("cycle_swing_fraction", "min_reference_cycles",
                "min_envelope_covered_fraction", "max_unobserved_gap_fraction",
                "max_w_over_scale"):
        assert key in fp, key


def test_a1_cycle_count_matches_the_known_box_geometry():
    # The 6-sweep 100-120 box has 12 confirmed swing legs => 6 round trips; the
    # 3-sweep box => 3; the one-way long_period_box window => half a leg.
    assert run(wide_box_traversal()).reference.reference_cycle_count == pytest.approx(6.0)
    assert run(sparse_slow_box()).reference.reference_cycle_count == pytest.approx(3.0)
    assert run(long_period_box()).reference.reference_cycle_count == pytest.approx(0.5)
    assert run(wide_box_traversal()).reference.swing_legs == 12


@pytest.mark.parametrize("factory", [long_period_box,
                                     one_way_reference_genuine_trend,
                                     nonduplication_same_path_different_reference])
def test_a1_guards_without_a_complete_round_trip(factory):
    if factory is nonduplication_same_path_different_reference:
        _a, fx = factory()
    else:
        fx = factory()
    ref = run(fx).reference
    assert ref.reference_adequacy_ok is False
    assert ref.validity == VALIDITY_DEGRADED_REFERENCE_ADEQUACY
    assert ref.allows_new_territory_claim is False
    assert any("complete round trips" in r for r in ref.validity_reasons)


def test_a1_does_not_block_genuine_trends_whose_window_contains_cycles():
    """The guard must not cost us the real trends (Sophira's core requirement)."""
    for factory in (true_trend, slow_trend, healthy_retest,
                    long_trend_unbounded_novelty):
        ep = run(factory())
        assert ep.reference.validity == VALIDITY_OK, factory.__name__
        assert ep.reference.reference_adequacy_ok is True, factory.__name__
        assert ep.first_new_territory_bar is not None, factory.__name__


def test_a1_false_suppression_of_a_real_trend_is_measured_not_hidden():
    """The honest cost of A1: a genuine trend behind a one-way window is blocked.

    This is a REPORTED limitation, not a bug to be papered over.  The window
    contains no round trip, so the indicator cannot claim; it returns
    insufficient evidence instead of guessing.
    """
    fx = one_way_reference_genuine_trend()
    ep = run(fx)
    assert ep.reference.validity == VALIDITY_DEGRADED_REFERENCE_ADEQUACY
    assert all(not o.is_new_territory_claim for o in ep.observations)
    # The price path really did escape and keep going; the raw v0.2 numbers
    # show it, which is exactly why the guard is the only thing stopping a
    # claim here and why the suppression must be reported.
    last = ep.observations[-1]
    assert last.close == pytest.approx(160.0)
    assert last.frontier_progress is not None and last.frontier_progress > 0
    assert last.novelty_class == NOVELTY_CLASS_UNVISITED


def test_a1_is_the_only_guard_that_catches_the_long_period_box():
    """Coverage, envelope and scale are all healthy there; cycles are not."""
    for factory in (long_period_box, one_way_reference_genuine_trend):
        ref = run(factory()).reference
        assert ref.coverage == pytest.approx(1.0)
        assert ref.envelope_covered_fraction == pytest.approx(1.0)
        assert ref.max_unobserved_gap_fraction == pytest.approx(0.0)
        assert ref.scale_state == SCALE_STABLE
        assert ref.reference_adequacy_ok is False


def test_a1_is_the_single_point_of_control_for_the_long_period_box_claim():
    """Lowering ONLY the cycle guard reopens the claim, proving causality."""
    fx = long_period_box()
    blocked = run(fx)
    assert all(not o.is_new_territory_claim for o in blocked.observations)
    reopened = run(fx, PTMConfig(min_reference_cycles=0.0))
    assert any(o.is_new_territory_claim for o in reopened.observations)
    # ... and nothing else about the observation changes.
    assert reopened.observations[0].revisit_episodes == \
        blocked.observations[0].revisit_episodes


def test_phase2_guard_switch_defaults_on_and_only_lifts_the_gate():
    """The comparison switch is never the default and must not move R/O/N."""
    assert PTMConfig().apply_phase2_guards is True
    assert PTMConfig().fingerprint()["apply_phase2_guards"] is True
    fx = long_period_box()
    fixed = run(fx)
    legacy = run(fx, replace(fx.config, apply_phase2_guards=False))
    # Diagnostics are unchanged; only the gate is lifted.
    assert [o.revisit_episodes for o in legacy.observations] == \
        [o.revisit_episodes for o in fixed.observations]
    assert [o.novelty for o in legacy.observations] == \
        [o.novelty for o in fixed.observations]
    assert [o.comparability_status for o in legacy.observations] == \
        [o.comparability_status for o in fixed.observations]
    # The diagnostics stay truthful even when the gate is lifted ...
    assert legacy.reference.reference_adequacy_ok is False
    assert legacy.reference.guards_enforced is False
    # ... and the pre-patch label/behaviour is reproduced exactly.
    assert legacy.reference.validity == VALIDITY_OK
    assert legacy.reference.allows_new_territory_claim is True
    assert any(o.is_new_territory_claim for o in legacy.observations)
    assert all(not o.is_new_territory_claim for o in fixed.observations)


def test_a1_unobserved_gap_guard_catches_a_sparse_download():
    ref = run(gappy_reference()).reference
    assert ref.envelope_covered_fraction < MIN_ENVELOPE_COVERED_FRACTION
    assert ref.max_unobserved_gap_fraction > MAX_UNOBSERVED_GAP_FRACTION
    assert ref.reference_adequacy_ok is False
    assert ref.allows_new_territory_claim is False


def test_a1_close_to_close_gap_is_a_diagnostic_and_must_not_gate():
    """A range-spanning reference legitimately has big close jumps.

    ``crossed_but_not_closed`` teleports 100 <-> 120 between closes while its
    bar ranges cover every price in between, so gating on close gaps would
    falsely reject a fully observed reference.
    """
    ref = run(crossed_but_not_closed()).reference
    diag = reference_gap_diagnostics(ref)
    assert diag["max_close_gap_w"] >= 10.0          # big close jumps
    assert diag["max_unobserved_gap_fraction"] == pytest.approx(0.0)
    assert ref.envelope_covered_fraction == pytest.approx(1.0)
    assert ref.reference_adequacy_ok is True        # not falsely rejected


def test_a1_gap_diagnostics_agree_with_the_reference_fields():
    for fx in all_fixtures():
        ref = run(fx).reference
        diag = reference_gap_diagnostics(ref)
        if ref.w is None or ref.n_valid == 0:
            assert diag["envelope_covered_fraction"] is None, fx.name
            continue
        assert diag["envelope_covered_fraction"] == pytest.approx(
            ref.envelope_covered_fraction), fx.name
        assert diag["max_unobserved_gap_fraction"] == pytest.approx(
            ref.max_unobserved_gap_fraction), fx.name
        assert diag["max_unobserved_gap_w"] == pytest.approx(
            ref.max_unobserved_gap_w), fx.name


def test_a1_invalid_reference_bars_never_create_swing_legs():
    """Missing bars must not be interpolated into a fake round trip."""
    fx = missing_reference_bars()
    ref = run(fx).reference
    assert ref.validity == VALIDITY_DEGRADED_REFERENCE_COVERAGE
    assert ref.n_valid == 112
    # The box geometry is still visible through the gaps, so cycles survive;
    # the coverage guard is what blocks the claim here.
    assert ref.reference_cycle_count is not None
    assert ref.reference_adequacy_ok is True
    assert ref.allows_new_territory_claim is False


def test_a1_cycle_count_is_reflection_invariant():
    for factory in (true_trend, wide_box_traversal, long_period_box, sparse_slow_box):
        fx = factory()
        mirror = short_mirror_of(fx)
        a = run(fx).reference
        b = run(mirror).reference
        assert a.reference_cycle_count == b.reference_cycle_count, factory.__name__
        assert a.swing_legs == b.swing_legs, factory.__name__
        assert a.reference_adequacy_ok == b.reference_adequacy_ok, factory.__name__


# ===========================================================================
# 18. A2 -- market-speed-invariant revisit comparability
# ===========================================================================


def test_a2_reports_alongside_and_does_not_replace_r_or_n():
    for fx in all_fixtures():
        for o in run(fx).observations:
            if o.revisit_episodes is None:
                assert o.episodes_per_cycle is None
                assert o.revisit_density is None
                continue
            assert o.novelty == pytest.approx(1.0 / (1.0 + o.revisit_episodes))
            if o.comparability_status == COMPARABILITY_OK:
                cycles = o.reference_cycle_count
                assert cycles is not None and cycles >= 1.0
                assert o.episodes_per_cycle == pytest.approx(
                    o.revisit_episodes / cycles)
            else:
                assert o.episodes_per_cycle is None


def test_a2_speed_comparability_improves_on_raw_revisit_count():
    """Same box, 6 fast sweeps vs 3 slow sweeps.

    Raw R differs by 2x and N by 1.67x purely because of market speed.  The
    per-cycle rate is the speed-invariant view A2 adds.
    """
    fast = obs_at_close(run(wide_box_traversal()), 118.0)
    slow = obs_at_close(run(sparse_slow_box()), 118.0)
    assert fast.revisit_episodes == 6 and slow.revisit_episodes == 3
    raw_gap = abs(math.log(slow.revisit_episodes / fast.revisit_episodes))
    a2_gap = abs(math.log(slow.episodes_per_cycle / fast.episodes_per_cycle))
    assert a2_gap < raw_gap
    assert fast.episodes_per_cycle == pytest.approx(1.0)
    assert slow.episodes_per_cycle == pytest.approx(1.0)


def test_a2_zero_revisits_is_a_measured_zero_not_an_unmeasurable_none():
    """R == 0 is a real observation; only "no cycle" makes A2 unmeasurable."""
    ep = run(true_trend())
    first_clean = next(o for o in ep.observations if o.revisit_episodes == 0)
    assert first_clean.comparability_status == COMPARABILITY_OK
    assert first_clean.episodes_per_cycle == pytest.approx(0.0)
    assert first_clean.revisit_density == pytest.approx(0.0)


def test_a2_no_complete_cycle_is_explicitly_not_comparable():
    o = obs_at_close(run(long_period_box()), 112.0)
    assert o.comparability_status == COMPARABILITY_NO_COMPLETE_CYCLE
    assert o.episodes_per_cycle is None
    # The per-bar density is still computable; only the per-cycle rate is not.
    assert o.revisit_density is not None


def test_a2_unusable_reference_is_distinguished_from_no_cycle():
    ep = run(degenerate_history())
    o = ep.observations[0]
    assert o.revisit_episodes is None
    assert o.comparability_status == COMPARABILITY_REFERENCE_UNUSABLE
    assert o.episodes_per_cycle is None
    assert o.revisit_density is None


def test_a2_revisit_density_uses_the_valid_reference_bar_count():
    ref = run(missing_reference_bars()).reference
    o = run(missing_reference_bars()).observations[0]
    assert o.revisit_episodes is not None
    assert o.revisit_density == pytest.approx(
        o.revisit_episodes / float(ref.n_valid))


def test_a2_does_not_change_any_claim_decision():
    """A2 is descriptive: the claim predicate must be exactly the v0.2 rule."""
    for fx in all_fixtures():
        ep = run(fx)
        for o in ep.observations:
            expected = bool(
                o.novelty_class in (NOVELTY_CLASS_UNVISITED,
                                    "SPARSE")
                and ep.reference.allows_new_territory_claim
                and not o.suspect_scale_break
            )
            assert o.is_new_territory_claim == expected, (fx.name, o.bar_index)


# ===========================================================================
# 19. A3 -- price-scale stability
# ===========================================================================


def test_a3_threshold_equals_the_one_hundred_percent_interdecile_rule():
    # w = span / 20, so w/scale <= 0.05  <=>  span <= 100% of the price level.
    assert MAX_W_OVER_SCALE == 0.05
    assert MAX_W_OVER_SCALE * 20.0 == pytest.approx(1.0)


def test_a3_flags_the_volatility_regime_shift():
    ref = run(volatility_regime_shift()).reference
    assert ref.w_over_scale is not None and ref.w_over_scale > MAX_W_OVER_SCALE
    assert ref.scale_state == SCALE_UNSTABLE
    assert ref.scale_stable is False
    assert ref.validity == VALIDITY_DEGRADED_SCALE_UNSTABLE
    assert ref.allows_new_territory_claim is False
    assert any("w/scale" in r for r in ref.validity_reasons)


def test_a3_healthy_references_are_stable():
    for factory in (wide_box_traversal, true_trend, slow_trend, sparse_slow_box,
                    long_period_box, crossed_but_not_closed, long_wick):
        ref = run(factory()).reference
        assert ref.scale_state == SCALE_STABLE, factory.__name__
        assert ref.scale_stable is True, factory.__name__


def test_a3_zero_reference_level_fails_closed_without_dividing_by_zero():
    """Zero price level => no valid denominator => SCALE_UNKNOWN, no claim."""
    ref = run(translated_to_zero_scale()).reference
    assert ref.median_close == pytest.approx(0.0)
    assert ref.scale_reference is None
    assert ref.w_over_scale is None
    assert ref.scale_state == SCALE_UNKNOWN
    assert ref.scale_stable is False
    assert ref.validity == VALIDITY_DEGRADED_SCALE_UNSTABLE
    assert ref.allows_new_territory_claim is False
    assert run(translated_to_zero_scale()).observations[0].scale_state == SCALE_UNKNOWN


def test_a3_uses_absolute_median_so_negative_levels_stay_valid():
    ref = run(negative_level_series()).reference
    assert ref.median_close is not None and ref.median_close < 0.0
    assert ref.scale_reference == pytest.approx(abs(ref.median_close))
    assert ref.w_over_scale is not None and ref.w_over_scale > 0.0
    assert ref.scale_state == SCALE_STABLE
    assert ref.allows_new_territory_claim is True


def test_a3_negative_level_series_matches_its_positive_twin():
    """Territory arithmetic is translation invariant; only the ratio moves."""
    base = run(true_trend())
    shifted = run(negative_level_series())
    for a, b in zip(base.observations, shifted.observations):
        assert a.revisit_episodes == b.revisit_episodes
        assert a.occupancy == pytest.approx(b.occupancy)
        assert a.novelty == pytest.approx(b.novelty)
        assert a.is_new_territory_claim == b.is_new_territory_claim
    assert base.first_new_territory_bar == shifted.first_new_territory_bar


def test_a3_ratio_is_invariant_under_a_multiplicative_rescale():
    base = run(true_trend()).reference
    scaled = run(adjusted_split()).reference
    assert scaled.w_over_scale == pytest.approx(base.w_over_scale)
    assert scaled.scale_state == base.scale_state


def test_a3_ratio_is_not_translation_invariant_and_that_is_documented():
    """A level-relative ratio cannot be translation invariant.

    It is scale (multiplicative) invariant but not shift invariant: the
    denominator is the reference price level, so shifting the series towards
    zero raises the ratio until it fails closed.  Pinned so it cannot change
    silently.
    """
    base = run(true_trend()).reference
    near_zero = run(translated_to_zero_scale()).reference
    # true_trend median is 110; shifted by -200 it is exactly -90.
    negative = run(negative_level_series()).reference
    assert negative.median_close == pytest.approx(-90.0)
    assert base.w_over_scale == pytest.approx(base.w / 110.0)
    assert negative.w_over_scale == pytest.approx(base.w / 90.0)
    assert negative.w_over_scale != pytest.approx(base.w_over_scale)
    assert near_zero.w_over_scale is None
    assert base.scale_state != near_zero.scale_state


def test_a3_low_level_false_alarm_of_the_one_bar_screen_is_reported():
    """D10: the frozen one-bar scale-break screen is level-dependent.

    A fixed absolute 3.0 move is 2.4% at level 123 but 43% at level -7, so the
    screen latches near zero and suppresses claims whose R/O/N are identical to
    the positive-level path.  A3 itself is fine here (SCALE_STABLE); the
    suppression comes from the pre-existing frozen screen, and it is reported
    rather than hidden behind the negative-level fixture.
    """
    positive = run(true_trend())
    low = run(low_level_scale_break_false_alarm())
    assert low.reference.scale_state == SCALE_STABLE
    assert low.reference.allows_new_territory_claim is True
    # Identical territory arithmetic on both paths ...
    assert [o.revisit_episodes for o in low.observations] == \
        [o.revisit_episodes for o in positive.observations]
    # ... and the same first evidence bar ...
    assert positive.first_new_territory_bar == low.first_new_territory_bar == 127
    # ... but the screen latches on the low-level path only, and every bar it
    # latches on loses the claim the positive-level path keeps.
    assert any(o.suspect_scale_break for o in low.observations)
    assert not any(o.suspect_scale_break for o in positive.observations)
    pos_claims = [o.bar_index for o in positive.observations if o.is_new_territory_claim]
    low_claims = [o.bar_index for o in low.observations if o.is_new_territory_claim]
    assert len(low_claims) < len(pos_claims)
    suppressed = [o.bar_index for o in low.observations
                  if o.suspect_scale_break and not o.is_new_territory_claim]
    assert suppressed == [b for b in pos_claims if b not in low_claims]


def test_a3_guard_outcome_is_reflection_symmetric():
    for factory in (true_trend, wide_box_traversal, long_period_box, long_wick):
        fx = factory()
        mirror = short_mirror_of(fx)
        a, b = run(fx).reference, run(mirror).reference
        assert a.scale_state == b.scale_state, factory.__name__
        assert a.allows_new_territory_claim == b.allows_new_territory_claim


def test_a3_unstable_scale_blocks_every_claim_in_the_episode():
    ep = run(volatility_regime_shift())
    assert all(not o.is_new_territory_claim for o in ep.observations)


# ===========================================================================
# 20. Promotion clock -- the corrected timing contract (Sophira review s.1)
# ===========================================================================


def test_breakout_ten_bars_after_the_probe_promotes_at_breakout_plus_three():
    c = build_promotion_clock(probe_t0=120, b3_break_t=130, ptm_observation_t=130)
    assert c.b3_break_t == 130
    assert c.b3_confirmation_t == 133
    assert c.eligible_promotion_t == 133
    assert c.probe_to_breakout_bars == 10
    assert c.promotion_status == PROMOTION_ELIGIBLE


def test_probe_plus_three_is_not_the_promotion_time():
    """The contract error Sophira found, made measurable."""
    c = build_promotion_clock(probe_t0=120, b3_break_t=130)
    assert c.probe_plus_three_naive_t == 123
    assert c.eligible_promotion_t == 133
    # The old text would have promoted 10 bars too early.
    assert c.naive_probe_clock_error_bars == 10


def test_coincident_breakout_makes_the_naive_error_zero():
    c = build_promotion_clock(probe_t0=120, b3_break_t=120)
    assert c.eligible_promotion_t == 123
    assert c.naive_probe_clock_error_bars == 0


def test_no_qualifying_breakout_yields_no_promotion_eligibility():
    c = build_promotion_clock(probe_t0=120, b3_break_t=None, ptm_observation_t=140)
    assert c.promotion_status == PROMOTION_NO_BREAKOUT
    assert c.b3_confirmation_t is None
    assert c.eligible_promotion_t is None
    assert c.promotion_next_executable_t is None
    assert c.ptm_vs_eligibility == PTM_NOT_COMPARABLE
    assert c.ptm_extra_delay_bars is None
    # The PTM evidence still exists and is still actionable; there is simply no
    # promotion to compare it against.
    assert c.ptm_observation_t == 140
    assert c.ptm_next_executable_t == 141


def test_failed_confirmation_yields_no_promotion_eligibility():
    c = build_promotion_clock(probe_t0=120, b3_break_t=130,
                              confirmation_passed=False)
    assert c.promotion_status == PROMOTION_CONFIRMATION_FAILED
    assert c.b3_break_t == 130
    assert c.b3_confirmation_t == 133
    assert c.eligible_promotion_t is None
    assert c.ptm_extra_delay_bars is None


def test_ptm_earlier_than_eligibility_costs_the_model_zero_bars():
    c = build_promotion_clock(probe_t0=120, b3_break_t=130, ptm_observation_t=128)
    assert c.ptm_vs_eligibility == PTM_EARLIER
    assert c.ptm_extra_delay_bars == 0


def test_ptm_on_the_eligibility_bar_costs_zero_bars():
    c = build_promotion_clock(probe_t0=120, b3_break_t=130, ptm_observation_t=133)
    assert c.ptm_vs_eligibility == PTM_SAME_BAR
    assert c.ptm_extra_delay_bars == 0


def test_ptm_later_than_eligibility_is_measured_against_real_promotion():
    """Not against probe+3, which would report a fictional 12-bar delay."""
    c = build_promotion_clock(probe_t0=120, b3_break_t=130, ptm_observation_t=135)
    assert c.ptm_vs_eligibility == PTM_LATER
    assert c.ptm_extra_delay_bars == 2
    assert c.ptm_observation_t - c.probe_plus_three_naive_t == 12


def test_next_executable_is_the_later_of_the_two_independent_clocks():
    c = build_promotion_clock(probe_t0=120, b3_break_t=130, ptm_observation_t=135)
    assert c.promotion_next_executable_t == 134
    assert c.ptm_next_executable_t == 136
    assert c.next_executable_t == 136
    early = build_promotion_clock(probe_t0=120, b3_break_t=130, ptm_observation_t=125)
    assert early.next_executable_t == 134


def test_confirmation_window_is_the_frozen_three_bars():
    assert CONFIRMATION_BARS == 3
    c = build_promotion_clock(probe_t0=0, b3_break_t=0)
    assert c.eligible_promotion_t == 3


def test_breakout_before_the_probe_is_rejected_not_coerced():
    with pytest.raises(ValueError):
        build_promotion_clock(probe_t0=120, b3_break_t=119)


@pytest.mark.parametrize("bad_window", [0, -1, -3])
def test_non_positive_confirmation_window_is_rejected(bad_window):
    with pytest.raises(ValueError):
        build_promotion_clock(probe_t0=120, b3_break_t=130,
                              confirmation_bars=bad_window)


def test_promotion_clock_reads_no_market_data_and_is_deterministic():
    a = build_promotion_clock(probe_t0=120, b3_break_t=130, ptm_observation_t=135)
    b = build_promotion_clock(probe_t0=120, b3_break_t=130, ptm_observation_t=135)
    assert a == b


# ===========================================================================
# 21. Re-verification of the standing limits A4-A7
# ===========================================================================


def test_a4_the_secondary_touch_variant_cannot_mitigate_an_enclosing_wick():
    """A4 remains OPEN: the variant does not fix the long-wick case.

    A bar whose range fully encloses the query band overlaps 100% of it, so no
    ``min_touch_fraction`` can exclude it.  This is reported, not assumed away.
    """
    fx = long_wick()
    default = obs_at_close(run(fx), 135.0).revisit_episodes
    assert default == 1
    for frac in (0.25, 0.5, 0.75, 1.0):
        cfg = PTMConfig(touch_mode=TOUCH_MIN_OVERLAP_FRACTION,
                        min_touch_fraction=frac)
        ep = evaluate_episode(fx.bars, fx.probe_index, fx.direction, cfg)
        assert obs_at_close(ep, 135.0).revisit_episodes == default, frac


def test_a4_secondary_touch_variant_is_monotone_and_has_an_effect():
    changed = 0
    for fx in all_fixtures():
        counts = []
        for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
            cfg = PTMConfig(touch_mode=TOUCH_MIN_OVERLAP_FRACTION,
                            min_touch_fraction=frac)
            ep = evaluate_episode(fx.bars, fx.probe_index, fx.direction, cfg)
            counts.append(ep.observations[0].revisit_episodes)
        present = [c for c in counts if c is not None]
        for a, b in zip(present, present[1:]):
            assert a >= b, (fx.name, counts)
        if len(set(present)) > 1:
            changed += 1
    assert changed > 0, "the challenger touch mode never changed any count"


def test_a4_zero_overlap_fraction_is_exactly_the_inclusive_default():
    for factory in (true_trend, wide_box_traversal, long_wick):
        fx = factory()
        base = run(fx).observations
        cfg = PTMConfig(touch_mode=TOUCH_MIN_OVERLAP_FRACTION, min_touch_fraction=0.0)
        alt = evaluate_episode(fx.bars, fx.probe_index, fx.direction, cfg).observations
        assert [o.revisit_episodes for o in alt] == \
            [o.revisit_episodes for o in base]


def test_a5_first_probe_wins_freezes_one_reference_for_overlapping_probes():
    fx = wide_box_traversal()
    bars = fx.bars
    probes = [Probe(index=120, direction=1), Probe(index=124, direction=1),
              Probe(index=128, direction=1)]
    episodes = evaluate_stream(bars, probes, fx.config, ANCHOR_FIRST_PROBE_WINS)
    assert len(episodes) == 1
    assert episodes[0].anchor_index == 120
    assert episodes[0].reprobe_indices == [124, 128]


def test_a5_staleness_cap_opens_a_new_episode_after_the_window_is_stale():
    fx = wide_box_traversal()
    bars = fx.bars
    probes = [Probe(index=120, direction=1), Probe(index=120 + 120, direction=1)]
    episodes = evaluate_stream(bars, probes, fx.config, ANCHOR_FIRST_PROBE_WINS)
    assert len(episodes) == 2
    assert [e.anchor_index for e in episodes] == [120, 240]


def test_a5_anchor_policy_is_in_the_frozen_fingerprint():
    """A5: the anchor policy must be part of the frozen fingerprint.

    Regression found in phase 2: it was previously only a bare argument to
    ``evaluate_stream``, so a caller could switch to the defective re-anchor
    policy without the frozen fingerprint changing at all.
    """
    fp = PTMConfig().fingerprint()
    assert fp["anchor_policy"] == ANCHOR_FIRST_PROBE_WINS
    assert fp["anchor_policy"] == PTMConfig().anchor_policy
    changed = replace(PTMConfig(), anchor_policy=ANCHOR_REANCHOR_EACH_PROBE)
    assert changed.fingerprint()["anchor_policy"] == ANCHOR_REANCHOR_EACH_PROBE
    assert changed.fingerprint() != PTMConfig().fingerprint()

    fx = wide_box_traversal()
    probes = [Probe(index=120, direction=1), Probe(index=124, direction=1)]
    # No explicit argument means "use the config".
    assert len(evaluate_stream(fx.bars, probes, fx.config)) == 1
    assert len(evaluate_stream(fx.bars, probes, fx.config,
                               ANCHOR_FIRST_PROBE_WINS)) == 1
    assert len(evaluate_stream(fx.bars, probes, fx.config,
                               ANCHOR_REANCHOR_EACH_PROBE)) == 2
    # The defective policy is expressible for the counterexample, and recorded.
    from_config = evaluate_stream(
        fx.bars, probes,
        replace(fx.config, anchor_policy=ANCHOR_REANCHOR_EACH_PROBE))
    assert len(from_config) == 2


@pytest.mark.parametrize("bad", ["", "reanchor", "FIRST_PROBE_WINS", "x"])
def test_a5_unknown_anchor_policy_is_rejected(bad):
    fx = wide_box_traversal()
    with pytest.raises(ValueError):
        evaluate_stream(fx.bars, [Probe(index=120, direction=1)], fx.config, bad)


def test_a5_reanchor_each_probe_is_the_documented_defect_not_the_default():
    fx = wide_box_traversal()
    probes = [Probe(index=120, direction=1), Probe(index=124, direction=1)]
    default = evaluate_stream(fx.bars, probes, fx.config, ANCHOR_FIRST_PROBE_WINS)
    naive = evaluate_stream(fx.bars, probes, fx.config, ANCHOR_REANCHOR_EACH_PROBE)
    assert len(default) == 1
    assert len(naive) == 2  # re-anchoring resets evidence maturity
    assert PTMConfig().fingerprint()  # default config is first_probe_wins


def test_a6_stagnation_is_independent_and_never_enters_the_claim():
    for fx in all_fixtures():
        ep = run(fx)
        for o in ep.observations:
            recomputed = bool(
                o.novelty_class in (NOVELTY_CLASS_UNVISITED, "SPARSE")
                and ep.reference.allows_new_territory_claim
                and not o.suspect_scale_break
            )
            assert o.is_new_territory_claim == recomputed, (fx.name, o.bar_index)
    # A stall can coexist with a claim and a claim can coexist without a stall,
    # so the two are demonstrably not fused.
    stall = run(post_breakout_stall())
    assert any(o.stall_flag for o in stall.observations)
    assert any(o.is_new_territory_claim for o in stall.observations)


def test_a7_inclusive_band_edges_and_scale_break_can_never_create_a_claim():
    for fx in all_fixtures():
        ep = run(fx)
        for o in ep.observations:
            if o.suspect_scale_break:
                assert o.is_new_territory_claim is False, (fx.name, o.bar_index)
    for factory in (unadjusted_split, futures_roll):
        ep = run(factory())
        assert all(not o.is_new_territory_claim for o in ep.observations)
        assert any(o.suspect_scale_break for o in ep.observations)


def test_a7_unadjusted_split_and_roll_never_claim_new_territory():
    for factory in (unadjusted_split, futures_roll):
        ep = run(factory())
        assert all(not o.is_new_territory_claim for o in ep.observations), \
            factory.__name__


def test_a7_signal_is_same_close_observable_and_next_bar_actionable():
    """No fixed waiting period may be introduced by the phase-2 guards."""
    for fx in all_fixtures():
        for o in run(fx).observations:
            assert o.observable_at_bar == o.bar_index, fx.name
            assert o.actionable_at_bar == o.bar_index + 1, fx.name


def test_a7_no_phase2_guard_changed_the_causality_of_any_observation():
    for factory in (true_trend, long_period_box, gappy_reference,
                    volatility_regime_shift, missing_reference_bars):
        fx = factory()
        full = run(fx)
        for cut in range(fx.probe_index + 1, len(fx.bars)):
            part = evaluate_episode(fx.bars[:cut], fx.probe_index,
                                    fx.direction, fx.config)
            assert part.observations == full.observations[: cut - fx.probe_index], \
                (fx.name, cut)


def test_a7_all_phase2_guards_are_reflection_symmetric():
    for factory in (true_trend, wide_box_traversal, long_period_box,
                    sparse_slow_box, one_way_reference_genuine_trend,
                    volatility_regime_shift, long_wick):
        fx = factory()
        a = run(fx)
        b = run(short_mirror_of(fx))
        ra, rb = a.reference, b.reference
        assert ra.reference_cycle_count == rb.reference_cycle_count, factory.__name__
        assert ra.reference_adequacy_ok == rb.reference_adequacy_ok, factory.__name__
        assert ra.scale_state == rb.scale_state, factory.__name__
        assert ra.allows_new_territory_claim == rb.allows_new_territory_claim, \
            factory.__name__
        for x, y in zip(a.observations, b.observations):
            assert x.revisit_episodes == y.revisit_episodes, factory.__name__
            assert x.occupancy == pytest.approx(y.occupancy), factory.__name__
            assert x.novelty == pytest.approx(y.novelty), factory.__name__
            assert x.is_new_territory_claim == y.is_new_territory_claim, \
                factory.__name__


# ===========================================================================
# 22. Phase-2 scenario matrix (Sophira review s.2 and the issue's item 6)
# ===========================================================================


def test_phase2_comparison_numbers_are_pinned():
    """Pin the v0.2-vs-fixed claim counts quoted in the finding doc §6.E.

    These are the numbers the review reports. If the guards or the fixtures
    change, the documentation must be updated deliberately, not silently.
    """
    expected = {
        "wide_box_traversal": (0, 0),
        "long_period_box": (12, 0),
        "sparse_slow_box": (0, 0),
        "true_trend": (4, 4),
        "slow_trend": (19, 19),
        "long_trend_unbounded_novelty": (167, 167),
        "healthy_retest": (7, 7),
        "fake_breakout": (1, 1),
        "volatility_regime_shift": (0, 0),
        "gappy_reference": (3, 0),
        "one_way_reference_genuine_trend": (8, 0),
        "unadjusted_split": (0, 0),
        "futures_roll": (0, 0),
        "translated_to_zero_scale": (0, 0),
        "negative_level_series": (4, 4),
        "low_level_scale_break_false_alarm": (2, 2),
        "long_wick": (5, 5),
        "crossed_but_not_closed": (1, 1),
    }
    by_name = {f.name: f for f in all_fixtures()}
    for name, (v02, fixed) in sorted(expected.items()):
        fx = by_name[name]
        legacy = run(fx, replace(fx.config, apply_phase2_guards=False))
        now = run(fx)
        got = (sum(1 for o in legacy.observations if o.is_new_territory_claim),
               sum(1 for o in now.observations if o.is_new_territory_claim))
        assert got == (v02, fixed), (name, got)


def test_phase2_scenario_names_are_all_implemented():
    names = {fx.name for fx in all_fixtures()}
    for name in PHASE2_SCENARIOS:
        assert name in names, name
    assert len(REQUIRED_SCENARIOS) == 10
    assert len(PHASE2_SCENARIOS) >= 8


def test_phase2_scenario_1_no_false_new_territory_inside_a_large_box():
    for factory in (wide_box_traversal, long_period_box):
        ep = run(factory())
        assert all(not o.is_new_territory_claim for o in ep.observations), \
            factory.__name__


def test_phase2_scenario_2_long_period_box_is_insufficient_evidence():
    ref = run(long_period_box()).reference
    assert ref.validity == VALIDITY_DEGRADED_REFERENCE_ADEQUACY
    assert "insufficient" not in ref.validity  # stated as DEGRADED, not disguised
    assert ref.n_valid == 120  # usable numbers, no claim


def test_phase2_scenario_3_genuine_trends_are_not_wholly_blocked():
    for factory in (true_trend, slow_trend, healthy_retest):
        ep = run(factory())
        assert ep.first_new_territory_bar is not None, factory.__name__
        assert ep.reference.validity == VALIDITY_OK, factory.__name__


def test_phase2_scenario_4_slow_trend_is_identified_promptly():
    """Latency is measured from the structural escape, not from the anchor."""
    fx = slow_trend()
    ep = run(fx)
    escape = structural_escape_bar(fx, ep)
    assert escape is not None
    assert ep.first_new_territory_bar is not None
    assert ep.first_new_territory_bar - escape <= 1


def test_phase2_scenario_5_a_fake_breakout_is_reflected_immediately():
    ep = run(fake_breakout())
    # It may claim on the escape close (it cannot know the future), but the
    # moment price is back inside the visited region the claim must be gone.
    back_inside = obs_at_close(ep, 116.0)
    assert back_inside.revisit_episodes is not None and back_inside.revisit_episodes > 1
    assert back_inside.is_new_territory_claim is False


def test_phase2_scenario_6_a_healthy_retest_does_not_kill_the_signal():
    ep = run(healthy_retest())
    claims = [o.bar_index for o in ep.observations if o.is_new_territory_claim]
    assert claims
    retest = obs_at_close(ep, 118.0)
    assert retest.is_new_territory_claim is False  # back in old territory
    later = [o for o in ep.observations if o.bar_index > retest.bar_index
             and o.is_new_territory_claim]
    assert later, "the signal never returned after the retest"


def test_phase2_scenario_7_long_and_short_are_symmetric():
    for factory in (true_trend, wide_box_traversal, long_period_box):
        fx = factory()
        a, b = run(fx), run(short_mirror_of(fx))
        assert a.first_new_territory_bar == b.first_new_territory_bar, \
            factory.__name__


def test_phase2_scenario_8_no_extra_fixed_waiting_period_was_introduced():
    """Every guard is a reference-level gate, never a time delay."""
    for fx in all_fixtures():
        ep = run(fx)
        first = ep.first_new_territory_bar
        if first is None:
            continue
        base = ep.observations[0]
        assert base.observable_at_bar == base.bar_index
        # The earliest possible claim bar is the first observable bar, so a
        # guard cannot have inserted a fixed number of waiting bars.
        assert first >= ep.anchor_index
        assert all(o.actionable_at_bar == o.bar_index + 1 for o in ep.observations)


# ---------------------------------------------------------------------------
# 23. Phase-2 adversarial-audit hardening
# ---------------------------------------------------------------------------
#
# An independent phase-2 audit mutated the guards to find which ones were not
# actually pinned by the suite.  Four mutants survived the 151-test suite:
#     M1  drop ``reference_adequacy_ok`` from the claim gate
#     M9  drop ``scale_stable`` from the claim gate
#     M10 disable the A1 largest-unobserved-gap reason
#     M11 disable the A1 envelope-coverage reason
# and it found a P1 FAIL-OPEN: a bar with ``low=-1e308, high=+1e308`` made the
# derived envelope non-finite, ``inf/inf`` became NaN, ``nan < 0.5`` is False,
# and a claim was emitted with a NaN coverage diagnostic.  The tests below pin
# every one of those findings.


def test_audit_a1_gap_guard_blocks_in_isolation():
    """Only the gap reason may block ``envelope_gap_only``; cycles/coverage pass."""
    ep = run(envelope_gap_only())
    ref = ep.reference
    assert ref.reference_cycle_count >= MIN_REFERENCE_CYCLES
    assert ref.envelope_covered_fraction >= MIN_ENVELOPE_COVERED_FRACTION
    assert ref.max_unobserved_gap_fraction > MAX_UNOBSERVED_GAP_FRACTION
    assert ref.reference_adequacy_ok is False
    assert ref.validity == VALIDITY_DEGRADED_REFERENCE_ADEQUACY
    assert len(ref.validity_reasons) == 1
    assert "unobserved price gap" in ref.validity_reasons[0]
    assert ep.first_new_territory_bar is None


def test_audit_a1_coverage_guard_blocks_in_isolation():
    """Only the coverage reason may block ``envelope_coverage_only``."""
    ep = run(envelope_coverage_only())
    ref = ep.reference
    assert ref.reference_cycle_count >= MIN_REFERENCE_CYCLES
    assert ref.max_unobserved_gap_fraction <= MAX_UNOBSERVED_GAP_FRACTION
    assert ref.envelope_covered_fraction < MIN_ENVELOPE_COVERED_FRACTION
    assert ref.reference_adequacy_ok is False
    assert ref.validity == VALIDITY_DEGRADED_REFERENCE_ADEQUACY
    assert len(ref.validity_reasons) == 1
    assert "envelope fraction" in ref.validity_reasons[0]
    assert ep.first_new_territory_bar is None


def test_audit_a1_gap_reason_is_load_bearing():
    """Mutant M10: removing only the gap threshold must reopen the claim."""
    fx = envelope_gap_only()
    lifted = replace(fx.config, max_unobserved_gap_fraction=1.0)
    ep = run(fx, lifted)
    assert ep.reference.max_unobserved_gap_fraction > MAX_UNOBSERVED_GAP_FRACTION
    assert ep.reference.reference_adequacy_ok is True
    assert ep.reference.validity == VALIDITY_OK
    assert ep.first_new_territory_bar is not None


def test_audit_a1_coverage_reason_is_load_bearing():
    """Mutant M11: removing only the coverage threshold must reopen the claim."""
    fx = envelope_coverage_only()
    lifted = replace(fx.config, min_envelope_covered_fraction=0.0)
    ep = run(fx, lifted)
    assert ep.reference.envelope_covered_fraction < MIN_ENVELOPE_COVERED_FRACTION
    assert ep.reference.reference_adequacy_ok is True
    assert ep.reference.validity == VALIDITY_OK
    assert ep.first_new_territory_bar is not None


def test_audit_non_finite_bar_range_fails_closed_not_open():
    """P1: a non-finite derived envelope must block, never emit a NaN claim.

    ``low=-1e308, high=+1e308`` are both FINITE, so the reference-level
    finiteness check passes, but the span overflows to ``inf``.  ``inf/inf`` is
    NaN and ``nan < 0.5`` is ``False``, so before the fix both A1 envelope
    sub-guards silently passed and a claim was emitted carrying
    ``envelope_covered_fraction = nan``.
    """
    base = wide_box_traversal()
    poisoned = replace(base.reference[0], low=-1e308, high=1e308)
    fx = replace(base, reference=[poisoned] + list(base.reference[1:]))
    ep = run(fx)
    ref = ep.reference
    assert ref.reference_adequacy_ok is False
    assert ref.validity == VALIDITY_DEGRADED_REFERENCE_ADEQUACY
    assert ep.first_new_territory_bar is None
    assert math.isfinite(ref.envelope_covered_fraction)
    assert math.isfinite(ref.max_unobserved_gap_fraction)
    assert ref.envelope_covered_fraction == 0.0
    assert ref.max_unobserved_gap_fraction == 1.0
    diag = reference_gap_diagnostics(ref)
    for key, value in diag.items():
        assert value is None or math.isfinite(value), key
    # The poisoned bar must never produce a NaN claim anywhere in the stream.
    for o in ep.observations:
        assert not o.is_new_territory_claim
        if o.envelope_covered_fraction is not None:
            assert math.isfinite(o.envelope_covered_fraction)
        if o.max_unobserved_gap_fraction is not None:
            assert math.isfinite(o.max_unobserved_gap_fraction)


def test_audit_inverted_bar_range_fails_closed():
    """``high < low`` is a data error: it must not be silently ignorable."""
    base = wide_box_traversal()
    poisoned = replace(base.reference[0], low=130.0, high=120.0)
    fx = replace(base, reference=[poisoned] + list(base.reference[1:]))
    ep = run(fx)
    assert ep.reference.reference_adequacy_ok is False
    assert ep.first_new_territory_bar is None


def test_audit_claim_gate_requires_adequacy_and_scale_even_at_validity_ok():
    """Pin mutants M1/M9: the belt-and-braces conjuncts must stay load-bearing.

    Under the current validity mapping ``validity == OK`` cannot coexist with a
    failed guard, so no fixture reaches these conjuncts.  That makes them easy
    to delete without any test noticing, so their behaviour is pinned directly
    on the predicate.
    """
    base = run(true_trend()).reference
    assert base.allows_new_territory_claim is True
    assert replace(
        base, guards_enforced=True, validity=VALIDITY_OK,
        reference_adequacy_ok=False,
    ).allows_new_territory_claim is False
    assert replace(
        base, guards_enforced=True, validity=VALIDITY_OK, scale_stable=False,
    ).allows_new_territory_claim is False
    # With the comparison switch off both must yield to the v0.2 gate, which is
    # the whole point of the switch existing.
    assert replace(
        base, guards_enforced=False, validity=VALIDITY_OK,
        reference_adequacy_ok=False, scale_stable=False,
    ).allows_new_territory_claim is True


@pytest.mark.parametrize("kwargs", [
    {"radius_divisor": 0.0},
    {"radius_divisor": -1.0},
    {"radius_divisor": float("nan")},
    {"radius_divisor": float("inf")},
    {"acceptance_window": 0},
    {"acceptance_window": -1},
    {"acceptance_window": 2.5},
    {"reference_bars": 0},
    {"max_episode_bars": 0},
    {"outer_multiplier": 0.0},
    {"quantile_low": 0.5, "quantile_high": 0.5},
    {"quantile_low": 0.9, "quantile_high": 0.1},
    {"quantile_low": -0.1},
    {"quantile_high": 1.1},
    {"min_reference_coverage": 1.5},
    {"min_envelope_covered_fraction": -0.1},
    {"max_unobserved_gap_fraction": 2.0},
    {"min_touch_fraction": 1.5},
    {"min_reference_cycles": -0.5},
    {"min_reference_cycles": float("nan")},
    {"cycle_swing_fraction": 0.0},
    {"max_w_over_scale": 0.0},
    {"max_w_over_scale": float("inf")},
    {"suspect_scale_break_factor": 1.0},
    {"suspect_scale_break_factor": 0.5},
    {"tick": 0.0},
    {"tick": -1.0},
    {"touch_mode": "nonsense"},
    {"zero_width_policy": "nonsense"},
    {"anchor_policy": "nonsense"},
])
def test_audit_config_rejects_values_that_crash_or_redefine(kwargs):
    with pytest.raises(ValueError):
        PTMConfig(**kwargs)


def test_audit_acceptance_window_one_uses_only_the_current_close():
    """``[-(1-1):]`` is ``[-0:]``, i.e. the whole history -- a real bug.

    An acceptance window of one bar must mean "the current close only", not
    "the average of every close seen so far".  The non-vacuity assertion at the
    end matters: the buggy slice would have averaged the whole history, which
    can only differ from the current close if the novelty actually varies.
    """
    fx = true_trend()
    ep = run(fx, replace(fx.config, acceptance_window=1))
    novelties = [o.novelty for o in ep.observations if o.novelty is not None]
    assert len(novelties) > 2, "fixture must yield a real novelty history"
    assert len(set(novelties)) > 1, "novelty must vary, or the test is vacuous"
    checked = 0
    for o in ep.observations:
        if o.novelty is None:
            assert o.acceptance_trace is None
            continue
        checked += 1
        assert math.isclose(o.acceptance_trace, o.novelty, rel_tol=1e-12), (
            o.bar_index, o.acceptance_trace, o.novelty)
    assert checked == len(novelties)


def test_audit_default_config_is_valid_and_unchanged():
    """The hardening must not move any frozen default."""
    cfg = PTMConfig()
    assert cfg.radius_divisor > 0
    assert cfg.acceptance_window == ACCEPTANCE_WINDOW == 3
    assert cfg.reference_bars == REFERENCE_BARS
    assert cfg.cycle_swing_fraction == CYCLE_SWING_FRACTION
    assert cfg.min_reference_cycles == MIN_REFERENCE_CYCLES
    assert cfg.min_envelope_covered_fraction == MIN_ENVELOPE_COVERED_FRACTION
    assert cfg.max_unobserved_gap_fraction == MAX_UNOBSERVED_GAP_FRACTION
    assert cfg.max_w_over_scale == MAX_W_OVER_SCALE
    assert cfg.apply_phase2_guards is True
