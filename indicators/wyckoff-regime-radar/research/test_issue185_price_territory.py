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
    NOVELTY_CLASS_HEAVILY_REVISITED,
    NOVELTY_CLASS_UNVISITED,
    PTMConfig,
    Probe,
    REFERENCE_BARS,
    VALIDITY_DEGRADED_DEGENERATE_REFERENCE,
    VALIDITY_DEGRADED_REFERENCE_COVERAGE,
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
from ptm_territory_fixtures import (
    Fixture,
    REQUIRED_SCENARIOS,
    adjusted_split,
    all_fixtures,
    box_reference,
    creeping_stall,
    crossed_but_not_closed,
    degenerate_history,
    degenerate_history_tick_fallback,
    fake_breakout,
    futures_roll,
    gappy_reference,
    healthy_retest,
    long_period_box,
    long_trend_unbounded_novelty,
    long_wick,
    missing_reference_bars,
    nonduplication_same_path_different_reference,
    nonduplication_same_reference_different_path,
    one_tick_breakout,
    post_breakout_stall,
    short_mirror_of,
    slow_trend,
    sparse_slow_box,
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


def test_scale_break_screen_is_a_prompt_not_a_gate():
    # A genuine -55% move is indistinguishable from a 2:1 split using price
    # alone; documented false positive, so the screen must never gate trading.
    from ptm_territory import scale_ratio_break

    assert scale_ratio_break(45.0, 100.0, 1.5) is True
    # ... and any split milder than the factor slips through: documented
    # false negative (a 3:2 split leaves 66.7, which sits on the boundary).
    assert scale_ratio_break(70.0, 100.0, 1.5) is False


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


def test_120_bar_window_is_insufficient_for_a_long_period_box():
    ep = run(long_period_box())
    o = obs_at_close(ep, 112.0)
    assert o.revisit_episodes is not None and o.revisit_episodes <= 1
    assert o.novelty is not None and o.novelty >= 0.5
    assert o.is_new_territory_claim is True
    assert o.occupancy is not None and o.occupancy < 0.2


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


def test_config_fingerprint_pins_every_free_choice():
    fp = PTMConfig().fingerprint()
    assert fp["reference_bars"] == 120
    assert fp["quantile_low"] == 0.10
    assert fp["quantile_high"] == 0.90
    assert fp["radius_divisor"] == 20.0
    assert fp["outer_multiplier"] == 2.0
    assert fp["acceptance_window"] == 3


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
