"""Deterministic tests for the C1 add-on policy, the ex-ante range stratum and
the parent parity contract.

Scope: the C1-only prereg convergence round (issue #185).  No market data, no
returns, no OOS3/4/5, no Pine.

WHAT THIS FILE PINS
-------------------
1. The parent clock: a release is never executable before the parent has
   finished confirming (`B3_break + CONFIRMATION_BARS`).
2. The eight behavioural scenarios the earlier review required.
3. The corrected DISPOSITION TAXONOMY: an episode whose data ends before the
   decision horizon is complete is ``OBSERVATION_RIGHT_CENSORED`` -- the future
   is unknown -- and is never counted as a permanent add-on loss.
4. The ex-ante range descriptor: causal, discriminating, with explicit
   zero-data rules, and never derived from the future path.
5. The two withdrawn claims: the 14/23 = 60.9% "permanent censoring" figure and
   the zero "signal contradiction" as evidence.
6. The parent (#78) parity contract.

The single most important invariant under test: **an unobserved add-on delay is
never reported as "0 additional bars"**, and **only a complete follow-up horizon
can establish a permanent withholding**.
"""
from __future__ import annotations

import math
from dataclasses import replace

import pytest

import ptm_territory_fixtures as fixtures_module
from analyze_issue185_price_territory import (
    addon_policy_rows,
    addon_policy_summary,
    parent_event_provenance,
    parent_plan_for,
)
from ptm_addon_policy import (
    ACTIVE_CHALLENGERS,
    ADDON_ALREADY_FULL,
    ADDON_BASELINE_HANDLES,
    ADDON_DE_RISK,
    ADDON_NOT_ELIGIBLE,
    ADDON_OBSERVATION_RIGHT_CENSORED,
    ADDON_PROMOTE,
    ADDON_WITHHOLD_PENDING,
    ADDON_WITHHOLD_THROUGH_EXPIRY,
    BASELINE_ON_DEGRADED_ALTERNATIVE,
    C1_PTM_GUARD,
    C2_PTM_GUARD_DWELL,
    CANONICAL_DISPOSITIONS,
    CHALLENGER_POLICIES,
    DECLARED_DISPOSITIONS,
    DISPOSITION_OBSERVATION_RIGHT_CENSORED,
    DISPOSITION_PARENT_NOT_ELIGIBLE,
    DISPOSITION_POLICY_WITHHELD_THROUGH_EXPIRY,
    DISPOSITION_PROMOTED,
    DWELL_BARS_OMIN,
    EPISODE_EXPIRY_BARS,
    PARENT_PATH_NO_B3,
    PARENT_PATH_P0,
    PARENT_PATH_P3,
    RETIRED_CHALLENGERS,
    ParentPlan,
    assert_finite_or_censored,
    claim_gate_failures,
    evaluate_addon,
    evaluable_outcomes,
    is_sparse_or_unvisited,
    next_executable_bar,
    reference_is_valid,
    right_censored_share,
    withheld_share_of_evaluable,
)
from ptm_promotion_clock import CONFIRMATION_BARS
from ptm_range_regime import (
    ATR_WINDOW_BARS,
    REVERSAL_BIN_MANY,
    REVERSAL_BIN_NONE,
    REVERSAL_BIN_ONE,
    STATUS_OK,
    STATUS_UNAVAILABLE,
    WIDTH_ATR_EDGES,
    WIDTH_BIN_MID,
    WIDTH_BIN_NARROW,
    WIDTH_BIN_WIDE,
    assign_reversal_bin,
    assign_width_bin,
    range_regime_at,
    range_regime_pre_bars,
    true_range_bars,
)
from ptm_territory import (
    NOVELTY_CLASS_HEAVILY_REVISITED,
    NOVELTY_CLASS_REVISITED,
    NOVELTY_CLASS_SPARSE,
    NOVELTY_CLASS_UNVISITED,
    VALIDITY_DEGRADED_REFERENCE_ADEQUACY,
    VALIDITY_DEGRADED_SCALE_UNSTABLE,
    VALIDITY_OK,
    _swing_legs,
    build_reference,
    evaluate_episode,
    PTMConfig,
)
from ptm_territory_fixtures import all_fixtures, long_period_box, true_trend


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _base_observation():
    """A real observation, used as the template for synthetic overrides."""
    fx = true_trend()
    episode = evaluate_episode(fx.bars, fx.probe_index, fx.direction, fx.config)
    return episode.observations[0]


_BASE = _base_observation()


def obs(bar, *, claim=True, validity=VALIDITY_OK, adequacy=True, scale=True,
        band=NOVELTY_CLASS_UNVISITED, episodes=0, coverage=1.0, suspect=False,
        scale_state="SCALE_STABLE"):
    """A synthetic observation with only the policy-relevant fields varied."""
    return replace(
        _BASE,
        bar_index=bar,
        is_new_territory_claim=claim,
        validity=validity,
        reference_adequacy_ok=adequacy,
        scale_stable=scale,
        novelty_class=band,
        revisit_episodes=episodes,
        reference_coverage=coverage,
        suspect_scale_break=suspect,
        scale_state=scale_state,
    )


def plan(*, probe=100, b3=110, path=PARENT_PATH_P0, usable=True,
         deteriorated_at=None, already_full_at=None):
    return ParentPlan(probe_bar=probe, b3_break_bar=b3, path=path,
                      usable_b3=usable, deteriorated_at=deteriorated_at,
                      already_full_at=already_full_at)


def withheld_obs(bars):
    """A repeated, non-claiming HEAVILY_REVISITED reading (never certifies)."""
    return [obs(b, claim=False, band=NOVELTY_CLASS_HEAVILY_REVISITED,
                episodes=7) for b in bars]


def _row(**overrides):
    """One ``addon_policy_rows`` record, with the real column contract.

    Built from the function's own output shape so that a column added there does
    not silently disappear from these unit tests.
    """
    row = {
        "fixture": "x",
        "direction": "long",
        "sustained_escape": False,
        "breakout_stand_in_bar": 110,
        "eligible_promotion_bar": 113,
        "parent_earns_addon": True,
        "last_observed_bar": 113,
        "claim_bars_total": 1,
        "claim_bars_at_or_after_eligibility": 1,
        "c1_disposition": DISPOSITION_PROMOTED,
        "c1_status": DISPOSITION_PROMOTED,
        "c1_first_release_bar": 113,
        "c1_first_executable_bar": 114,
        "c1_extra_delay_bars": 0,
        "c1_censored": False,
        "c1_followup_complete": True,
        "c1_withheld_definite": False,
        "c1_observed_post_eligible_bars": 1,
        "c1_open_hold_at_last_bar": False,
        "c2_retired": True,
        "c2_disposition": DISPOSITION_PROMOTED,
        "c2_status": DISPOSITION_PROMOTED,
        "c2_first_release_bar": 113,
        "c2_first_executable_bar": 114,
        "c2_extra_delay_bars": 0,
        "c2_censored": False,
        "c2_followup_complete": True,
        "c2_withheld_definite": False,
        "c2_differs_from_c1": False,
        "range_status": STATUS_OK,
        "range_reason": "pre-probe range descriptor available",
        "width_atr": 9.0,
        "width_bin": WIDTH_BIN_MID,
        "atr_pre": 0.5,
        "ref_span": 4.5,
        "c1_reason": "affirmative new-territory claim on a trusted reference",
        "c2_reason": "affirmative new-territory claim on a trusted reference",
    }
    row.update(overrides)
    return row


# ===========================================================================
# A. Clock: release never happens before the parent's eligibility bar
# ===========================================================================
def test_a1_eligibility_is_b3_plus_confirmation_bars_not_probe_plus():
    p = plan(probe=120, b3=130)
    assert p.eligible_promotion_bar == 133
    assert p.eligible_promotion_bar == 130 + CONFIRMATION_BARS
    assert p.eligible_promotion_bar != 120 + CONFIRMATION_BARS


def test_a2_a_release_fills_no_earlier_than_the_bar_after_its_signal():
    assert next_executable_bar(133) == 134
    observations = [obs(b) for b in range(120, 140)]
    out = evaluate_addon(C1_PTM_GUARD, observations, plan(probe=120, b3=130))
    assert out.disposition == DISPOSITION_PROMOTED
    assert out.first_release_signal_bar is not None
    assert out.first_executable_bar == out.first_release_signal_bar + 1
    assert out.first_release_signal_bar >= 133


def test_a3_no_release_before_eligibility_even_with_claims_from_the_breakout():
    observations = [obs(b) for b in range(110, 125)]
    out = evaluate_addon(C1_PTM_GUARD, observations, plan(probe=100, b3=110))
    assert out.disposition == DISPOSITION_PROMOTED
    assert out.first_release_signal_bar == 113
    assert out.first_executable_bar == 114
    assert out.extra_delay_bars == 0


# ===========================================================================
# B. The eight required behavioural scenarios
# ===========================================================================
def test_b1_withhold_then_successful_release():
    """DEGRADED at eligibility, then a trusted claim later -> release."""
    observations = [
        obs(113, claim=False, validity=VALIDITY_DEGRADED_REFERENCE_ADEQUACY,
            adequacy=False, band=NOVELTY_CLASS_SPARSE, episodes=1),
        obs(114, claim=False, validity=VALIDITY_DEGRADED_REFERENCE_ADEQUACY,
            adequacy=False, band=NOVELTY_CLASS_SPARSE, episodes=1),
        obs(115, claim=True, band=NOVELTY_CLASS_SPARSE, episodes=1),
        obs(116, claim=True, band=NOVELTY_CLASS_SPARSE, episodes=1),
    ]
    out = evaluate_addon(C1_PTM_GUARD, observations, plan(probe=100, b3=110))
    assert out.disposition == DISPOSITION_PROMOTED
    assert out.first_release_signal_bar == 115
    assert out.first_executable_bar == 116
    assert out.extra_delay_bars == 2
    assert not out.censored and not out.withheld_definite
    held = [d for d in out.trail if d.status == ADDON_WITHHOLD_PENDING]
    assert len(held) == 2
    assert all("conservative hold" in d.reason for d in held)
    # The hold is labelled a POLICY CHOICE, not a mathematical necessity.
    assert all("policy choice" in d.reason for d in held)


def test_b2_deterioration_while_withheld_never_promotes():
    """The benchmark deteriorates before release: baseline handles, no promote."""
    observations = [
        obs(113, claim=False, validity=VALIDITY_DEGRADED_REFERENCE_ADEQUACY,
            adequacy=False, band=NOVELTY_CLASS_SPARSE, episodes=1),
        obs(114, claim=True, band=NOVELTY_CLASS_SPARSE, episodes=1),
        obs(115, claim=True, band=NOVELTY_CLASS_SPARSE, episodes=1),
    ]
    out = evaluate_addon(
        C1_PTM_GUARD, observations,
        plan(probe=100, b3=110, deteriorated_at=114))
    assert out.disposition == ADDON_DE_RISK
    assert not out.released
    assert out.first_release_signal_bar is None
    assert out.first_executable_bar is None
    assert out.extra_delay_bars is None, (
        "an unobserved delay must not be reported as a numeric value"
    )
    assert any("never promotes" in r for r in out.reasons)


def test_b2b_de_risk_is_not_a_ptm_withholding():
    """The baseline closed the position; PTM did not withhold, so it is not
    charged as a definite PTM add-on loss."""
    observations = [
        obs(113, claim=False, band=NOVELTY_CLASS_SPARSE, episodes=1),
        obs(114, claim=False, band=NOVELTY_CLASS_SPARSE, episodes=1),
    ]
    out = evaluate_addon(C1_PTM_GUARD, observations,
                         plan(probe=100, b3=110, deteriorated_at=113))
    assert out.disposition == ADDON_DE_RISK
    assert out.followup_complete is True
    assert out.withheld_definite is False
    assert out not in evaluable_outcomes([out])
    assert withheld_share_of_evaluable([out]) is None
    assert not out.withheld_definite


def test_b2c_competing_baseline_exit_never_dilutes_withholding_rate():
    """Only an actual PTM resolution enters the definite-hold denominator."""
    expiry = 113 + EPISODE_EXPIRY_BARS
    withheld = evaluate_addon(
        C1_PTM_GUARD, withheld_obs(range(111, expiry + 1)),
        plan(probe=100, b3=110))
    exited = evaluate_addon(
        C1_PTM_GUARD, withheld_obs(range(111, 116)),
        plan(probe=100, b3=110, deteriorated_at=113))
    assert withheld.disposition == DISPOSITION_POLICY_WITHHELD_THROUGH_EXPIRY
    assert exited.disposition == ADDON_DE_RISK
    assert evaluable_outcomes([withheld, exited]) == [withheld]
    assert withheld_share_of_evaluable([withheld, exited]) == 1.0


def test_b3_data_suddenly_becomes_degraded_and_never_recovers():
    observations = [
        obs(113, claim=True, band=NOVELTY_CLASS_SPARSE, episodes=1),
    ] + [
        obs(b, claim=False, validity=VALIDITY_DEGRADED_SCALE_UNSTABLE,
            scale=False, band=NOVELTY_CLASS_SPARSE, episodes=1,
            scale_state="SCALE_UNSTABLE")
        for b in range(114, 116)
    ]
    out = evaluate_addon(C1_PTM_GUARD, observations, plan(probe=100, b3=110))
    # The one trusted claim at 113 is enough for C1 to release; later
    # degradation cannot retroactively unmake it.
    assert out.disposition == DISPOSITION_PROMOTED
    assert out.first_release_signal_bar == 113

    # Degraded from the start, and the data ends well before the horizon:
    # a right-censored open hold, NOT a proven permanent withholding.
    degraded = [
        obs(b, claim=False, validity=VALIDITY_DEGRADED_SCALE_UNSTABLE,
            scale=False, band=NOVELTY_CLASS_SPARSE, episodes=1,
            scale_state="SCALE_UNSTABLE")
        for b in range(113, 116)
    ]
    out2 = evaluate_addon(C1_PTM_GUARD, degraded, plan(probe=100, b3=110))
    assert out2.disposition == DISPOSITION_OBSERVATION_RIGHT_CENSORED
    assert out2.censored and not out2.withheld_definite
    assert out2.followup_complete is False
    assert out2.open_hold_at_last_bar is True
    assert out2.extra_delay_bars is None
    reasons = " ".join(d.reason for d in out2.trail)
    assert "SCALE_UNSTABLE" in reasons


def test_b4_middle_band_r2_to_r4_is_withheld_and_named_in_the_reason():
    observations = [
        obs(b, claim=False, band=NOVELTY_CLASS_REVISITED, episodes=3)
        for b in range(113, 120)
    ]
    out = evaluate_addon(C1_PTM_GUARD, observations, plan(probe=100, b3=110))
    assert not out.released
    assert out.censored
    assert out.extra_delay_bars is None
    assert any(f"novelty_class={NOVELTY_CLASS_REVISITED}" in d.reason
               or "R>=2" in d.reason for d in out.trail)
    assert f"novelty_class={NOVELTY_CLASS_REVISITED}" in claim_gate_failures(
        observations[0])


def test_b5_withholding_through_complete_expiry_is_definite_not_zero():
    """The invariant this whole round exists to protect.

    Only a COMPLETE post-eligible horizon establishes a permanent withholding,
    and even then the delay is not reported as 0 bars.
    """
    last = 113 + EPISODE_EXPIRY_BARS
    observations = withheld_obs(range(111, last + 1))
    out = evaluate_addon(C1_PTM_GUARD, observations, plan(probe=100, b3=110))
    assert out.disposition == DISPOSITION_POLICY_WITHHELD_THROUGH_EXPIRY
    assert out.withheld_definite is True
    assert out.followup_complete is True
    assert out.first_executable_bar is None
    assert out.extra_delay_bars is None, (
        "a withheld add-on must never be reported as 0 bars of delay"
    )
    assert out.observed_post_eligible_bars >= EPISODE_EXPIRY_BARS
    row = out.as_row()
    assert row["extra_delay_bars"] is None
    assert row["extra_delay_bars_observed"] is False
    assert row["withheld_definite"] is True
    assert "complete decision horizon" in row["reasons"]
    # A definite withholding is a valid 1 in a withholding count.
    assert withheld_share_of_evaluable([out]) == 1.0


def test_b5b_sparse_or_gapped_observations_are_not_complete_withholdings():
    """An expiry index alone cannot prove 120 completed decision observations."""
    last = 113 + EPISODE_EXPIRY_BARS
    p = plan(probe=100, b3=110)
    complete = withheld_obs(range(111, last + 1))
    # A single missing interior bar must defeat a "complete" 120-bar claim.
    gap = [o for o in complete if o.bar_index != 150]
    out = evaluate_addon(C1_PTM_GUARD, gap, p)
    assert out.disposition == DISPOSITION_OBSERVATION_RIGHT_CENSORED
    assert out.followup_complete is False
    assert out.withheld_definite is False
    assert out.observed_post_eligible_bars == EPISODE_EXPIRY_BARS
    assert "1 missing decision-bar" in " ".join(out.reasons)
    assert withheld_share_of_evaluable([out]) is None

    # Two endpoints never imply that all the bars between were observed.
    sparse = withheld_obs([111, 113, last])
    out2 = evaluate_addon(C1_PTM_GUARD, sparse, p)
    assert out2.disposition == DISPOSITION_OBSERVATION_RIGHT_CENSORED
    assert out2.observed_post_eligible_bars == 2
    assert not out2.withheld_definite

    # A present (but untrusted) reading still counts as an observed bar;
    # the pre-existing complete-horizon test covers the contiguous case.


def test_b6_episode_expiry_does_not_auto_promote():
    expiry = EPISODE_EXPIRY_BARS
    last = 113 + expiry
    observations = withheld_obs(range(111, last + 1))
    out = evaluate_addon(C1_PTM_GUARD, observations, plan(probe=100, b3=110))
    assert out.disposition == DISPOSITION_POLICY_WITHHELD_THROUGH_EXPIRY
    assert not out.released
    assert out.final_bar == last
    assert f"bar {last}" in " ".join(out.reasons)
    # Expiry is not confirmation: nothing after the expiry bar changes it.
    longer = observations + [
        obs(b, claim=True, band=NOVELTY_CLASS_UNVISITED, episodes=0)
        for b in range(last + 1, last + 4)
    ]
    out2 = evaluate_addon(C1_PTM_GUARD, longer, plan(probe=100, b3=110))
    assert out2.disposition == DISPOSITION_POLICY_WITHHELD_THROUGH_EXPIRY


def test_b7_no_parent_entitlement_is_not_charged_to_ptm():
    observations = [obs(b, claim=False) for b in range(120, 130)]

    p3 = plan(probe=100, b3=110, path=PARENT_PATH_P3)
    out_p3 = evaluate_addon(C1_PTM_GUARD, observations, p3)
    assert out_p3.disposition == DISPOSITION_PARENT_NOT_ELIGIBLE
    assert out_p3.eligible_promotion_bar is None
    assert out_p3.extra_delay_bars is None
    assert out_p3.withheld_definite is False, "PTM withheld nothing here"
    assert out_p3.censored is False
    assert out_p3 not in evaluable_outcomes([out_p3])

    no_b3 = plan(probe=100, b3=None, path=PARENT_PATH_NO_B3, usable=False)
    out_no = evaluate_addon(C1_PTM_GUARD, observations, no_b3)
    assert out_no.disposition == DISPOSITION_PARENT_NOT_ELIGIBLE
    assert out_no.withheld_definite is False


def test_b8_long_short_symmetry():
    long_fx = true_trend()
    short_fx = fixtures_module.short_mirror_of(long_fx)
    decisions = []
    for fx in (long_fx, short_fx):
        episode = evaluate_episode(fx.bars, fx.probe_index, fx.direction,
                                   fx.config)
        p = ParentPlan(probe_bar=fx.probe_index, b3_break_bar=120,
                       path=PARENT_PATH_P0)
        decisions.append(evaluate_addon(C1_PTM_GUARD, episode.observations, p))
    a, b = decisions
    assert a.disposition == b.disposition
    assert a.first_release_signal_bar == b.first_release_signal_bar
    assert a.first_executable_bar == b.first_executable_bar
    assert a.extra_delay_bars == b.extra_delay_bars


def test_b9_no_future_leak_release_bar_is_prefix_stable():
    long_fx = true_trend()
    episode = evaluate_episode(long_fx.bars, long_fx.probe_index,
                               long_fx.direction, long_fx.config)
    observations = list(episode.observations)
    p = ParentPlan(probe_bar=long_fx.probe_index, b3_break_bar=120,
                   path=PARENT_PATH_P0)
    full = evaluate_addon(C1_PTM_GUARD, observations, p)
    assert full.disposition == DISPOSITION_PROMOTED
    release = full.first_release_signal_bar
    release_idx = next(i for i, o in enumerate(observations)
                       if o.bar_index == release)

    for cut in range(release_idx, len(observations)):
        got = evaluate_addon(C1_PTM_GUARD, observations[:cut + 1], p)
        assert got.disposition == full.disposition, (cut, got.disposition)
        assert got.first_release_signal_bar == release, cut

    for cut in range(0, release_idx):
        got = evaluate_addon(C1_PTM_GUARD, observations[:cut + 1], p)
        assert not got.released, (cut, got.disposition)


# ===========================================================================
# B'. Right-censoring vs permanent withholding (Sophira's S3 finding)
# ===========================================================================
@pytest.mark.parametrize("fixture_name", [
    "gappy_reference", "one_tick_breakout", "crossed_but_not_closed"])
def test_b10_named_counterexamples_are_right_censored_not_permanent(
        fixture_name):
    """The three fixtures Sophira named must not be counted as permanent losses.

    Each ends BEFORE the parent's eligibility bar, so no decision bar was ever
    observed: ``followup_complete=False``, ``withheld_definite=False``.
    """
    by_name = {fx.name: fx for fx in all_fixtures()}
    assert fixture_name in by_name, sorted(by_name)
    fx = by_name[fixture_name]
    episode = evaluate_episode(fx.bars, fx.probe_index, fx.direction, fx.config)
    p = parent_plan_for(fx, episode)
    out = evaluate_addon(C1_PTM_GUARD, episode.observations, p)
    assert out.disposition == DISPOSITION_OBSERVATION_RIGHT_CENSORED
    assert out.followup_complete is False
    assert out.withheld_definite is False
    assert out.extra_delay_bars is None
    # No decision bar was reached at all.
    last_bar = max(o.bar_index for o in episode.observations)
    assert out.eligible_promotion_bar is not None
    assert last_bar < out.eligible_promotion_bar
    assert out.open_hold_at_last_bar is False
    assert "BEFORE the parent's eligibility bar" in " ".join(out.reasons)


def test_b11_fixture_ending_before_eligibility_is_not_a_withholding_rate():
    """A truncated observation can never enter the withholding denominator."""
    before = [
        obs(b, claim=False, band=NOVELTY_CLASS_HEAVILY_REVISITED, episodes=7)
        for b in range(110, 112)  # ends at 111, eligibility is 113
    ]
    out = evaluate_addon(C1_PTM_GUARD, before, plan(probe=100, b3=110))
    assert out.disposition == DISPOSITION_OBSERVATION_RIGHT_CENSORED
    assert out.followup_complete is False
    assert out.withheld_definite is False
    assert out.observed_post_eligible_bars == 0
    # It is excluded from the evaluable denominator, so the rate is undefined
    # rather than 0% or 100%.
    assert evaluable_outcomes([out]) == []
    assert withheld_share_of_evaluable([out]) is None
    assert right_censored_share([out]) == 1.0


def test_b12_horizon_guard_rejects_a_definite_withholding_without_followup():
    """Encoding the invariant, not merely trusting call sites."""
    last = 113 + EPISODE_EXPIRY_BARS
    good = evaluate_addon(
        C1_PTM_GUARD, withheld_obs(range(111, last + 1)), plan(probe=100, b3=110))
    assert good.disposition == DISPOSITION_POLICY_WITHHELD_THROUGH_EXPIRY
    assert_finite_or_censored(good)
    # Forging a definite withholding on an incomplete horizon must be caught.
    forged = replace(good, followup_complete=False)
    with pytest.raises(AssertionError, match="complete follow-up horizon"):
        assert_finite_or_censored(forged)
    # A right-censored outcome with a complete horizon is contradictory.
    with pytest.raises(AssertionError, match="contradictory"):
        assert_finite_or_censored(replace(
            good, disposition=DISPOSITION_OBSERVATION_RIGHT_CENSORED))


def test_b13_synthetic_set_cannot_establish_a_definite_withholding():
    """The honest headline: the synthetic fixtures cannot measure this."""
    fixtures = list(all_fixtures())
    episodes = {fx.name: evaluate_episode(fx.bars, fx.probe_index,
                                          fx.direction, fx.config)
                for fx in fixtures}
    rows = addon_policy_rows(fixtures, episodes)
    s = addon_policy_summary(rows)
    assert s["c1_fixtures_reaching_expiry"] >= 1, (
        "no fixture reaches the horizon, so the horizon itself is unreachable "
        "on this set and the conclusion must be restated"
    )
    assert s["c1_fixtures_reaching_expiry"] < (
        s["fixtures_with_parent_addon_entitlement"]), (
        "every fixture reaches the horizon, so the right-censoring finding "
        "needs revisiting"
    )
    # Reaching the horizon is not the same as being withheld through it.
    assert s["c1_policy_withheld_through_expiry"] == 0
    assert s["c1_definite_withholding_estimable_from_synthetics"] is False
    assert s["c1_withheld_share_of_evaluable"] == 0.0
    note = s["c1_horizon_adequacy_note"]
    assert "CANNOT estimate" in note
    assert "right-censored" in note
    # And the superseded figure is explicitly withdrawn.
    assert s["c1_superseded_figure"]["status"] == "WITHDRAWN"
    assert "60.9%" in s["c1_superseded_figure"]["value"]


# ===========================================================================
# C. Safety properties of the policy
# ===========================================================================
def test_c1_only_one_active_challenger_and_c2_is_retired():
    with pytest.raises(ValueError, match="no third challenger"):
        evaluate_addon("C3_SOMETHING_NEW", [obs(113)], plan(probe=100, b3=110))
    assert ACTIVE_CHALLENGERS == (C1_PTM_GUARD,)
    assert RETIRED_CHALLENGERS == (C2_PTM_GUARD_DWELL,)
    assert CHALLENGER_POLICIES == (C1_PTM_GUARD, C2_PTM_GUARD_DWELL)
    # Acceptance is not endorsement: C2 stays runnable for historical evidence.
    out = evaluate_addon(C2_PTM_GUARD_DWELL, [obs(113)], plan(probe=100, b3=110))
    assert out.policy == C2_PTM_GUARD_DWELL


def test_c2_dwell_and_expiry_arguments_are_validated():
    observations = [obs(113)]
    with pytest.raises(ValueError, match="dwell_bars"):
        evaluate_addon(C2_PTM_GUARD_DWELL, observations,
                       plan(probe=100, b3=110), dwell_bars=0)
    with pytest.raises(ValueError, match="expiry_bars"):
        evaluate_addon(C1_PTM_GUARD, observations, plan(probe=100, b3=110),
                       expiry_bars=0)
    with pytest.raises(ValueError, match="no PTM observations"):
        evaluate_addon(C1_PTM_GUARD, [], plan(probe=100, b3=110))


def test_c3_parent_plan_rejects_inconsistent_inputs():
    with pytest.raises(ValueError, match="unknown parent path"):
        ParentPlan(probe_bar=100, b3_break_bar=110, path="P9_NOPE")
    with pytest.raises(ValueError, match="requires b3_break_bar"):
        ParentPlan(probe_bar=100, b3_break_bar=None, path=PARENT_PATH_P0)
    with pytest.raises(ValueError, match="precedes probe_bar"):
        ParentPlan(probe_bar=120, b3_break_bar=110, path=PARENT_PATH_P0)
    with pytest.raises(ValueError, match="must be None"):
        ParentPlan(probe_bar=100, b3_break_bar=110, path=PARENT_PATH_P0,
                   usable_b3=False)


def test_c4_already_full_is_neutral_and_ptm_never_reduces():
    observations = [obs(b) for b in range(113, 120)]
    out = evaluate_addon(C1_PTM_GUARD, observations,
                         plan(probe=100, b3=110, already_full_at=105))
    assert out.disposition == ADDON_ALREADY_FULL
    assert out.extra_delay_bars == 0
    assert not out.censored
    assert out.withheld_definite is False
    assert out not in evaluable_outcomes([out])
    assert withheld_share_of_evaluable([out]) is None


def test_c5_dwell_counts_the_parents_own_acceptance_window():
    """C2 dwell is measured over B3+1..B3+3, so the parent horizon is reused.

    HISTORICAL: C2 is retired.  This test is kept so the retained evidence stays
    reproducible, and it explicitly asserts that the dwell count is a
    claim-persistence count, never described as occupancy.
    """
    assert DWELL_BARS_OMIN == CONFIRMATION_BARS
    assert EPISODE_EXPIRY_BARS == PTMConfig().reference_bars
    observations = [obs(b) for b in range(111, 120)]
    out = evaluate_addon(C2_PTM_GUARD_DWELL, observations,
                         plan(probe=100, b3=110))
    assert out.disposition == DISPOSITION_PROMOTED
    assert out.first_release_signal_bar == 113
    assert out.extra_delay_bars == 0

    only_last = [
        obs(111, claim=False, band=NOVELTY_CLASS_SPARSE, episodes=1),
        obs(112, claim=False, band=NOVELTY_CLASS_SPARSE, episodes=1),
        obs(113, claim=True, band=NOVELTY_CLASS_SPARSE, episodes=1),
    ]
    out2 = evaluate_addon(C2_PTM_GUARD_DWELL, only_last,
                          plan(probe=100, b3=110))
    assert not out2.released
    out3 = evaluate_addon(C1_PTM_GUARD, only_last, plan(probe=100, b3=110))
    assert out3.disposition == DISPOSITION_PROMOTED
    assert out3.first_release_signal_bar == 113


def test_c6_signal_gate_check_is_an_invariant_not_evidence():
    """The zero "signal contradiction" count is a tautology of the gate."""
    fixtures = list(all_fixtures())
    episodes = {fx.name: evaluate_episode(fx.bars, fx.probe_index,
                                          fx.direction, fx.config)
                for fx in fixtures}
    rows = addon_policy_rows(fixtures, episodes)
    offenders = [r["fixture"] for r in rows
                 if r["parent_earns_addon"]
                 and r["claim_bars_at_or_after_eligibility"] > 0
                 and r["c1_withheld_definite"]]
    assert offenders == []
    s = addon_policy_summary(rows)
    assert s["c1_signal_gate_invariant_holds"] is True
    # It must be LABELLED as an invariant, never presented as protection.
    note = s["c1_signal_gate_invariant_note"].lower()
    assert "invariant, not evidence" in note
    assert "tautology" in note
    # The old evidence-style claim must be gone.
    assert "newly_introduced_suppression_count" not in s


def test_c7_long_period_box_addon_is_never_released():
    """The blocking wide-box false release must also lose its add-on."""
    fx = long_period_box()
    episode = evaluate_episode(fx.bars, fx.probe_index, fx.direction, fx.config)
    p = ParentPlan(probe_bar=fx.probe_index, b3_break_bar=120,
                   path=PARENT_PATH_P0)
    out = evaluate_addon(C1_PTM_GUARD, episode.observations, p)
    assert not out.released
    assert out.extra_delay_bars is None
    assert out.disposition in (
        DISPOSITION_POLICY_WITHHELD_THROUGH_EXPIRY,
        DISPOSITION_OBSERVATION_RIGHT_CENSORED)
    if out.followup_complete:
        assert out.withheld_definite is True
    else:
        assert out.withheld_definite is False


def test_c8_trusted_abstain_branch_is_unreachable_and_the_old_claim_is_withdrawn():
    """The state is unreachable; the inference drawn from it is withdrawn."""
    from analyze_issue185_price_territory import abstain_branch_reachability

    trust = obs(113, claim=False, band=NOVELTY_CLASS_SPARSE, episodes=1)
    assert reference_is_valid(trust)
    assert is_sparse_or_unvisited(trust)
    fixtures = list(all_fixtures())
    episodes = {fx.name: evaluate_episode(fx.bars, fx.probe_index,
                                          fx.direction, fx.config)
                for fx in fixtures}
    scan = abstain_branch_reachability(fixtures, episodes)
    assert scan["reachable"] is False, scan["counterexamples"]
    assert scan["counterexamples"] == []
    assert scan["trusted_reference_observations_scanned"] > 0, (
        "the scan is vacuous if it never inspects a trusted reference"
    )
    # The scope correction must be present, and must NOT repeat the wrong claim.
    assert "scope_correction" in scan
    assert "WRONG" in scan["scope_correction"]
    assert "BASELINE_ON_DEGRADED_ALTERNATIVE" in scan["prereg_consequence"]
    assert "cannot be exercised" not in scan["prereg_consequence"]

    for fx in fixtures:
        for o in episodes[fx.name].observations:
            if reference_is_valid(o) and is_sparse_or_unvisited(o):
                assert o.is_new_territory_claim, (fx.name, o.bar_index)

    # The evaluation never yields the trusted-abstain status.
    assert "BASELINE_HANDLES" not in {r["c1_disposition"] for r in
                                      addon_policy_rows(fixtures, episodes)}


def test_c8b_conservative_hold_is_documented_as_a_policy_choice():
    """Sophira's correction must be recorded in the code, not just the prose."""
    import ptm_addon_policy as m
    doc = m.__doc__ or ""
    assert "POLICY CHOICE, NOT A MATHEMATICAL NECESSITY" in doc
    assert "BASELINE_ON_DEGRADED_ALTERNATIVE" in doc
    assert m.BASELINE_ON_DEGRADED_ALTERNATIVE.startswith("ALT_")
    # It is documented, not registered as a challenger.
    assert m.BASELINE_ON_DEGRADED_ALTERNATIVE not in m.CHALLENGER_POLICIES
    assert len(m.ACTIVE_CHALLENGERS) == 1


def test_c9_declared_dispositions_are_enumerated_not_implied():
    rows = [_row(fixture="a")]
    s = addon_policy_summary(rows)
    assert len(s["declared_dispositions"]) == 7
    assert len(CANONICAL_DISPOSITIONS) == 5
    assert len(DECLARED_DISPOSITIONS) == 7
    assert s["c1_disposition_distribution"][DISPOSITION_PROMOTED] == 1
    never = s["c1_declared_dispositions_never_observed"]
    assert DISPOSITION_POLICY_WITHHELD_THROUGH_EXPIRY in never
    assert "BASELINE_HANDLES" in never
    assert "provably unreachable" in s[
        "c1_declared_dispositions_never_observed_note"].lower()


# ===========================================================================
# C'. Ex-ante wide-vs-narrow range stratum (Sophira's S2 finding)
# ===========================================================================
def _ramp_bars(n, *, lo=100.0, hi=110.0, atr=1.0, cycle=10):
    """Deterministic oscillating bars with a controlled range and ATR."""
    bars = []
    span = hi - lo
    for i in range(n):
        phase = (i % cycle) / float(cycle)
        c = lo + span * (0.5 + 0.5 * math.sin(2 * math.pi * phase))
        prev = bars[-1][2] if bars else c
        h = max(c, prev) + atr / 2.0
        l = min(c, prev) - atr / 2.0
        bars.append((h, l, c))
    return bars


def _sweep_bars(closes, tr):
    """Bars whose closes follow *closes* and whose per-bar range is *tr*."""
    bars = []
    for i, c in enumerate(closes):
        prev = closes[i - 1] if i else c
        bars.append((max(c, prev) + tr / 2.0, min(c, prev) - tr / 2.0, c))
    return bars


def test_f1_range_regime_is_causal_no_future_influence():
    """Appending arbitrary future bars must not change the descriptor."""
    anchor = 140
    bars = _ramp_bars(anchor + 1)
    base = range_regime_at(bars, anchor)
    assert base.status == STATUS_OK
    for future in (
        _ramp_bars(30, lo=50.0, hi=500.0, atr=20.0),
        [(1e6, 1e5, 5e5)] * 50,
        [(-1.0, -2.0, -1.5)] * 50,
    ):
        got = range_regime_at(bars + list(future), anchor)
        assert got == base, "the descriptor depends on the future path"


def test_f2_range_regime_ignores_the_anchor_bar_and_reads_only_the_past():
    anchor = 140
    bars = _ramp_bars(anchor + 1)
    base = range_regime_at(bars, anchor)
    # Mutating the anchor bar itself must change nothing: it is not read.
    mutated = list(bars)
    mutated[anchor] = (1e9, -1e9, 0.0)
    assert range_regime_at(mutated, anchor) == base


def test_f3_range_regime_zero_data_rules_are_explicit():
    # Too little history -> UNAVAILABLE, never silently binned.
    short = range_regime_pre_bars(_ramp_bars(ATR_WINDOW_BARS))
    assert short.status == STATUS_UNAVAILABLE
    assert short.width_bin is None
    assert "insufficient pre-probe history" in short.reason

    # A coordinate reset (NaN high/low) makes the window meaningless.
    gapped = _ramp_bars(ATR_WINDOW_BARS + 5)
    gapped[3] = (float("nan"), float("nan"), gapped[3][2])
    g = range_regime_pre_bars(gapped)
    assert g.status == STATUS_UNAVAILABLE
    assert g.width_bin is None
    assert "coordinate reset" in g.reason

    # Zero volatility -> UNAVAILABLE.
    flat = [(100.0, 100.0, 100.0)] * (ATR_WINDOW_BARS + 2)
    z = range_regime_pre_bars(flat)
    assert z.status == STATUS_UNAVAILABLE
    assert "span" in z.reason or "ATR" in z.reason

    # Non-finite close -> UNAVAILABLE.
    bad = _ramp_bars(ATR_WINDOW_BARS + 2)
    bad[1] = (bad[1][0], bad[1][1], float("inf"))
    nf = range_regime_pre_bars(bad)
    assert nf.status == STATUS_UNAVAILABLE

    # Every UNAVAILABLE result carries no bin and no number.
    for f in (short, g, z, nf):
        assert f.available is False
        assert f.width_atr is None and f.width_bin is None


def test_f3b_full_reference_gate_fails_closed_at_119_bars():
    """Formal live/historical descriptor must never use a shortened reference.

    Legacy synthetic diagnostics deliberately remain explicit partial-window
    illustrations, but the formal signal cannot silently use their window.
    """
    from ptm_range_regime import REFERENCE_BARS

    assert REFERENCE_BARS == 120
    for n in (0, 15, 60, 119):
        bars = _ramp_bars(n)
        formal = range_regime_pre_bars(bars, require_full_reference=True)
        assert formal.status == STATUS_UNAVAILABLE, n
        assert formal.width_atr is None and formal.width_bin is None
        assert "need exactly 120" in formal.reason
        assert formal.n_pre_bars == n

        # The real/full-series path must enforce the same rule by default.
        at_probe = range_regime_at(bars, n)
        assert at_probe.status == STATUS_UNAVAILABLE, n

    valid = _ramp_bars(REFERENCE_BARS)
    full = range_regime_pre_bars(valid, require_full_reference=True)
    assert full.status == STATUS_OK
    at_probe = range_regime_at(valid, REFERENCE_BARS)
    assert at_probe == full

    # A caller accidentally passing more than 120 must not silently change
    # the reference window. The full-series helper slices exactly 120.
    oversize = range_regime_pre_bars(
        _ramp_bars(REFERENCE_BARS + 1), require_full_reference=True)
    assert oversize.status == STATUS_UNAVAILABLE
    with pytest.raises(ValueError, match="frozen at 120"):
        range_regime_at(valid, REFERENCE_BARS, reference_bars=119)

    # A probe bar and any future data must not affect the exact past window.
    future = [(1e6, -1e6, 5e5)] * 20
    assert range_regime_at(valid + future, REFERENCE_BARS) == full


def test_f4_range_regime_discriminates_and_is_not_the_tautological_ratio():
    """`spread / w` was identically RADIUS_DIVISOR; the new feature varies."""
    cfg = PTMConfig()

    tight_closes = [10.0 + 0.1 * math.sin(2 * math.pi * i / 10.0)
                    for i in range(60)]
    wide_closes = [10.0 + 0.6 * i for i in range(60)]
    f_tight = range_regime_pre_bars(_sweep_bars(tight_closes, 0.05))
    f_wide = range_regime_pre_bars(_sweep_bars(wide_closes, 0.05))
    assert f_tight.status == STATUS_OK and f_wide.status == STATUS_OK
    assert f_wide.width_atr > f_tight.width_atr, (
        f_wide.width_atr, f_tight.width_atr)

    # The superseded criterion was constant for every valid reference.
    fx = true_trend()
    ref = build_reference(fx.bars, fx.probe_index, fx.direction, fx.config)
    span = ref.q_high - ref.q_low
    assert math.isclose(span / ref.w, cfg.radius_divisor, rel_tol=1e-9)
    assert cfg.radius_divisor == 20.0

    # Over the synthetic fixtures the new feature takes several distinct values.
    fixtures = list(all_fixtures())
    widths = set()
    for f in fixtures:
        pre = [(float(b.high), float(b.low), float(b.close))
               for b in f.bars[max(0, f.probe_index - 120):f.probe_index]]
        r = range_regime_pre_bars(pre)
        if r.status == STATUS_OK:
            widths.add(round(r.width_atr, 9))
    assert len(widths) > 1, "the new descriptor does not discriminate"


def test_f5_stratum_depends_only_on_the_pre_probe_window():
    """Two fixtures identical before the probe but different after must share a
    stratum: this is the test that `sustained_escape()` can never pass."""
    from ptm_territory_fixtures import _fixture

    reference = fixtures_module.box_reference()
    up = _fixture("probe_up", "post path escapes upward", [130.0, 140.0, 150.0],
                  reference=list(reference))
    down = _fixture("probe_down", "post path collapses", [80.0, 70.0, 60.0],
                    reference=list(reference))
    refs = []
    for f in (up, down):
        pre = [(float(b.high), float(b.low), float(b.close))
               for b in f.bars[max(0, f.probe_index - 120):f.probe_index]]
        refs.append(range_regime_pre_bars(pre))
    assert refs[0].width_atr == refs[1].width_atr
    assert refs[0].width_bin == refs[1].width_bin
    assert refs[0].width_bin is not None


def test_f6_stratum_summary_flags_the_superseded_criteria():
    fixtures = list(all_fixtures())
    episodes = {fx.name: evaluate_episode(fx.bars, fx.probe_index,
                                          fx.direction, fx.config)
                for fx in fixtures}
    rows = addon_policy_rows(fixtures, episodes)
    s = addon_policy_summary(rows)
    w = s["wide_box_stratum"]
    assert w["discriminates"] is True
    assert w["synthetic_distinct_width_atr_values"] > 1
    assert w["sustained_escape_is_outcome_only"] is True
    assert w["width_atr_edges_frozen"] == list(WIDTH_ATR_EDGES)
    assert "IDENTITY" in w["superseded_criteria"]["spread_over_w"]
    assert "sparse" in w["superseded_criteria"]["R_le_1_plus_claim"].lower()
    assert "outcome-only" in w["superseded_criteria"][
        "sustained_escape_stratum"]
    # Every row carries a stratum field, available or explicitly unavailable.
    for r in rows:
        assert r["range_status"] in (STATUS_OK, STATUS_UNAVAILABLE)
        if r["range_status"] == STATUS_UNAVAILABLE:
            assert r["width_bin"] is None and r["range_reason"]
        else:
            assert r["width_bin"] in (WIDTH_BIN_NARROW, WIDTH_BIN_MID,
                                      WIDTH_BIN_WIDE)


def test_f7_bin_assignment_is_predeclared_and_monotone():
    lo, hi = WIDTH_ATR_EDGES
    assert lo < hi
    assert assign_width_bin(lo - 0.001) == WIDTH_BIN_NARROW
    assert assign_width_bin(lo) == WIDTH_BIN_MID
    assert assign_width_bin(hi - 0.001) == WIDTH_BIN_MID
    assert assign_width_bin(hi) == WIDTH_BIN_WIDE
    with pytest.raises(ValueError):
        assign_width_bin(1.0, edges=(5.0, 1.0))
    # Reversal bins are integer bins: no tuned boundary.
    assert assign_reversal_bin(0) == REVERSAL_BIN_NONE
    assert assign_reversal_bin(1) == REVERSAL_BIN_ONE
    assert assign_reversal_bin(2) == REVERSAL_BIN_MANY
    assert assign_reversal_bin(99) == REVERSAL_BIN_MANY


def test_f8_true_range_definition_matches_the_standard():
    highs, lows, closes = [11.0, 12.0], [9.0, 11.5], [10.0, 11.8]
    tr = true_range_bars(highs, lows, closes)
    assert len(tr) == 1
    prev_c = closes[0]
    assert math.isclose(tr[0], max(highs[1] - lows[1], abs(highs[1] - prev_c),
                                    abs(lows[1] - prev_c)))
    with pytest.raises(ValueError):
        true_range_bars([1.0], [1.0, 2.0], [1.0])
    with pytest.raises(ValueError):
        range_regime_pre_bars(_ramp_bars(30), atr_window=1)


def test_f9_descriptor_is_quantised_for_cross_platform_stability():
    """Guards the artifact gate against a last-bit, cross-platform difference.

    The committed artifacts are byte-compared against a fresh run on a DIFFERENT
    operating system.  An unquantised mean of 14 true ranges differed by ~1e-14
    between the authoring machine and the CI runner, which failed the
    reproducibility gate for a reason unrelated to the study.  ``math.fsum``
    plus a fixed-decimal quantisation removes that failure class.
    """
    from ptm_range_regime import WIDTH_ATR_DECIMALS, quantise

    assert WIDTH_ATR_DECIMALS == 6
    # These are the two values that actually differed between Windows and the
    # Linux CI runner for `gappy_reference`.
    assert quantise(20.01000000000001) == 20.01
    assert quantise(20.009999999999998) == 20.01
    assert quantise(0.999500249875062) == 0.9995
    assert quantise(0.9995002498750626) == 0.9995

    closes = [10.0 + 0.6 * i for i in range(40)]
    base = _sweep_bars(closes, 0.05)
    f0 = range_regime_pre_bars(base)
    assert f0.status == STATUS_OK

    # Nudge one high by two ULP: far below the quantisation step, so neither
    # the stored value nor its bin may move.
    nudged = list(base)
    h, l, c = nudged[5]
    nudged[5] = (math.nextafter(math.nextafter(h, math.inf), math.inf), l, c)
    f1 = range_regime_pre_bars(nudged)
    assert f1.width_atr == f0.width_atr, (f0.width_atr, f1.width_atr)
    assert f1.atr_pre == f0.atr_pre, (f0.atr_pre, f1.atr_pre)
    assert f1.width_bin == f0.width_bin

    # Every stored float is already at the declared precision, and the bin is
    # derived from the quantised width so the two can never disagree.
    for f in (f0, f1):
        assert f.width_atr == round(f.width_atr, WIDTH_ATR_DECIMALS)
        assert f.atr_pre == round(f.atr_pre, WIDTH_ATR_DECIMALS)
        assert f.ref_span == round(f.ref_span, WIDTH_ATR_DECIMALS)
        assert f.width_bin == assign_width_bin(f.width_atr)


# ===========================================================================
# D. P0.1 -- the formula in the docs must equal the implemented one
# ===========================================================================
def test_d1_cycle_threshold_is_half_the_inter_decile_span_not_half_w():
    """The implemented leg threshold is ``0.5 * (Q90 - Q10)``, i.e. ``10 * w``.

    ``span = Q90 - Q10 = radius_divisor * w`` with ``radius_divisor = 20``, so
    the prereg's earlier ``0.5 * w`` prose was 20x smaller -- the more
    permissive (fail-open) direction.  ``volatility_regime_shift`` shows the
    difference: the implemented threshold credits 0.5 cycles, the prose reading
    would credit 5.5 and let the guard pass.
    """
    cfg = PTMConfig()
    assert cfg.radius_divisor == 20.0
    assert math.isclose(cfg.cycle_swing_fraction * cfg.radius_divisor, 10.0)

    seen_divergence = False
    for factory in (true_trend, long_period_box,
                    fixtures_module.volatility_regime_shift):
        fx = factory()
        ref = build_reference(fx.bars, fx.probe_index, fx.direction, fx.config)
        assert ref.q_low is not None and ref.w is not None
        span = ref.q_high - ref.q_low
        assert math.isclose(span, fx.config.radius_divisor * ref.w,
                            rel_tol=1e-9)
        closes, mask = list(ref.closes), list(ref.valid_mask)
        legs_span = _swing_legs(closes, mask,
                               fx.config.cycle_swing_fraction * span)
        legs_w = _swing_legs(closes, mask,
                             fx.config.cycle_swing_fraction * ref.w)
        assert legs_span / 2.0 == ref.reference_cycle_count, fx.name
        if legs_span != legs_w:
            seen_divergence = True
            assert legs_w / 2.0 != ref.reference_cycle_count, fx.name
    assert seen_divergence, (
        "no fixture separates 0.5*span from 0.5*w, so this pin is vacuous"
    )


# ===========================================================================
# E. Parent (#78) provenance contract
# ===========================================================================
def test_e1_parity_constants_in_the_parent_source_match_the_contract():
    """Pin the parent's own frozen constants by reading its source.

    The parent modules import ``scipy`` at module level (used only by their
    outcome helpers) and scipy is not a dependency of this repository, so the
    constants are read with ``ast`` rather than by importing.  This is what
    makes the provenance record a *checkable* contract instead of prose.
    """
    import ast
    from pathlib import Path

    here = Path(__file__).resolve().parent
    want = {
        "analyze_issue78_retest_path_stage1.py": {
            "MARKER": "ISSUE76|schema=1",
            "EXPECTED_EVENTS": 68118,
            "EXPECTED_EPISODES": 1624,
        },
        "analyze_issue78_second_entry_economic_policy.py": {
            "EXPECTED_EVENTS": 68118,
            "EXPECTED_EPISODES": 1624,
            "EXPECTED_B3_EVENTS": 997,
            "EXPECTED_P12": 236,
            "PROBE": 0.25,
            "FULL": 1.0,
        },
    }
    for filename, expected in want.items():
        path = here / filename
        assert path.is_file(), f"missing parent source {filename}"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        found = {}
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
                if isinstance(target, ast.Name):
                    try:
                        found[target.id] = ast.literal_eval(node.value)
                    except ValueError:
                        pass
        for key, value in expected.items():
            assert key in found, f"{filename} lost the frozen constant {key}"
            assert found[key] == value, (filename, key, found[key], value)

    prov = parent_event_provenance()
    assert prov["parity_constants"]["EXPECTED_EVENTS"] == 68118
    assert prov["parity_constants"]["EXPECTED_EPISODES"] == 1624
    assert prov["parity_constants"]["EXPECTED_B3_EVENTS"] == 997
    assert prov["parity_constants"]["EXPECTED_P12"] == 236


def test_e2_provenance_names_the_real_parent_contract():
    prov = parent_event_provenance()
    assert prov["event_source_marker"] == "ISSUE76|schema=1"
    assert prov["policy_module"] == "analyze_issue78_second_entry_economic_policy.py"
    assert prov["baseline_policy"] == "R0_Immediate"
    assert prov["confirmation_bars"] == CONFIRMATION_BARS == 3
    assert prov["probe_fraction"] == 0.25
    assert prov["parent_paths_that_add_at_t3"] == [
        "P0_NoTouch", "P1_WickHold", "P2_Reclaim"]
    assert prov["parent_path_that_never_adds"] == "P3_FailedAcceptance"
    assert prov["no_usable_b3_outcome"] == "remains at Probe"
    assert prov["rehearsal"]["all_four_constants_match"] is True
    assert prov["parity_constants"] == {
        "EXPECTED_EVENTS": 68118, "EXPECTED_EPISODES": 1624,
        "EXPECTED_B3_EVENTS": 997, "EXPECTED_P12": 236,
    }
    comp = prov["path_composition_from_rehearsal"]
    assert comp["adds_at_t3"] + comp["never_adds"] == 997
    assert (comp["P0_NoTouch"] + comp["P1_WickHold"] + comp["P2_Reclaim"]
            == comp["adds_at_t3"])
    assert comp["P1_WickHold"] + comp["P2_Reclaim"] == 236
    # The raw export is private and must be described as NOT committed.
    assert "NOT committed" in prov["export_note"]


def test_e3_real_cohort_manifest_is_optional_and_never_fabricated():
    """CI has no private export, so the manifest may be absent -- but if it is
    present it must be internally consistent."""
    prov = parent_event_provenance()
    m = prov["real_input_manifest"]
    if m is None:
        assert "NOT committed" in prov["export_note"]
        return
    assert m["feature_only"] is True
    assert m["outcomes_computed"] is False
    assert m["raw_data_committed"] is False
    # The committed v1 is an archival *partial-window-permissive* result;
    # a strict-120 re-freeze must advertise the new contract explicitly.
    assert m["schema"] in (
        "issue185-real-cohort-v1", "issue185-real-cohort-v2-strict120")
    if m["schema"] == "issue185-real-cohort-v1":
        assert m.get("strict_full_reference") is not True
    else:
        assert m["strict_full_reference"] is True
        assert m["reference_bars"] == 120
        assert m["atr_window_bars"] == 14
        summary = m["feature_summary"]
        assert summary["b3_events"] == 997
        assert summary["usable_width_atr"] == 661
        assert summary["unavailable"] == 336
        assert summary["short_reference_unavailable"] == 19
        assert summary["coordinate_reset_unavailable"] == 317
        assert summary["short_reference_accepted"] == 0
        assert summary["distinct_width_atr_values"] == 661
        assert summary["width_atr_tertile_edges"] == list(WIDTH_ATR_EDGES)
        assert summary["width_atr_bins"] == {
            "NARROW": 221, "MID": 219, "WIDE": 221}
        assert summary["usable_width_atr"] + summary["unavailable"] == (
            summary["b3_events"])
        assert sum(m["feature_unavailable"].values()) == (
            summary["unavailable"])
        assert sum(summary["width_atr_bins"].values()) == (
            summary["usable_width_atr"])
        assert len(m["manifest"]) == 9
        # Provenance: input content stays private; its manifest hashes are
        # public for replication. These nine fingerprints were matched 9/9.
        assert all(len(f["sha256"]) == 64 for f in m["manifest"])
    assert len(m["manifest"]) >= 1
    for f in m["manifest"]:
        assert len(f["sha256"]) == 64
        assert f["bytes"] > 0 and f["rows"] > 0
    assert m["parity"]["observed"]["b3_events"] == 997
    assert m["parity"]["observed"]["P12"] == 236
    assert m["parent_contract"]["marker"] == "ISSUE76|schema=1"
    assert m["parent_contract"]["probe"] == 0.25
    edges = m["width_atr_tertile_edges"]
    assert edges is not None and len(edges) == 2
    assert list(WIDTH_ATR_EDGES) == edges, (
        "the frozen edges in ptm_range_regime must equal the manifest's"
    )


def test_e4_addon_policy_summary_reports_dispositions_explicitly():
    rows = [
        _row(fixture="promoted"),
        _row(fixture="censored",
             c1_disposition=DISPOSITION_OBSERVATION_RIGHT_CENSORED,
             c1_status=DISPOSITION_OBSERVATION_RIGHT_CENSORED,
             c1_censored=True, c1_followup_complete=False,
             c1_withheld_definite=False, c1_open_hold_at_last_bar=True,
             claim_bars_at_or_after_eligibility=0, last_observed_bar=115,
             c1_first_release_bar=None, c1_first_executable_bar=None,
             c1_extra_delay_bars=None, sustained_escape=True),
        _row(fixture="not_eligible", parent_earns_addon=False,
             c1_disposition=DISPOSITION_PARENT_NOT_ELIGIBLE,
             c1_status=DISPOSITION_PARENT_NOT_ELIGIBLE,
             c1_first_release_bar=None, c1_first_executable_bar=None,
             c1_extra_delay_bars=None, claim_bars_at_or_after_eligibility=0),
    ]
    s = addon_policy_summary(rows)
    assert s["fixtures_with_parent_addon_entitlement"] == 2
    assert s["fixtures_without_parent_entitlement"] == 1
    assert s["c1_promoted"] == 1
    assert s["c1_observation_right_censored"] == 1
    assert s["c1_policy_withheld_through_expiry"] == 0
    assert s["c1_right_censored_share_of_entitled"] == 0.5
    # Only the promoted episode is evaluable, so the rate is 0% -- and the
    # right-censored episode NEVER enters that denominator.
    assert s["c1_evaluable_episodes"] == 1
    assert s["c1_withheld_share_of_evaluable"] == 0.0
    assert s["c1_max_delay_over_released"] == 0
    assert "unobserved delays are excluded" in s["c1_delay_scope"].lower()
    assert s["censored_never_reported_as_zero"] is True


def test_e5_every_fixture_is_classified_for_the_cost_headline():
    """No fixture may silently fall outside the declared classification."""
    from analyze_issue185_price_territory import NON_SCENARIO_FIXTURES
    names = {fx.name for fx in all_fixtures()}
    unknown = set(NON_SCENARIO_FIXTURES) - names
    assert unknown == set(), f"declared but non-existent fixtures: {unknown}"
    assert all(v.strip() for v in NON_SCENARIO_FIXTURES.values())
