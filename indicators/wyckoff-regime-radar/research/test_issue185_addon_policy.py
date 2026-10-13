"""Deterministic tests for the C1/C2 add-on policy and the parent parity contract.

Scope: the prereg-clarification patch only (issue #185, P0.2/P0.3/P0.4 and the
P0.1 formula pin).  No market data, no returns, no OOS3/4/5, no Pine.

The eight scenarios the prereg review asked to be covered deterministically:

1. withhold then successful release
2. withhold then parent deterioration
3. data suddenly becomes DEGRADED
4. the R = 2..4 middle band
5. permanent absence of release evidence
6. PTM episode expiry
7. no parent add-on entitlement at all
8. long/short symmetry and no future leak

The single most important invariant under test: **a withheld add-on is never
reported as "0 additional bars"**.  It is censored, and its delay is unbounded.
"""
from __future__ import annotations

import math
from dataclasses import replace

import pytest

import ptm_territory_fixtures as fixtures_module
from analyze_issue185_price_territory import parent_event_provenance
from ptm_addon_policy import (
    ADDON_ALREADY_FULL,
    ADDON_BASELINE_HANDLES,
    ADDON_DE_RISK,
    ADDON_NOT_ELIGIBLE,
    ADDON_PROMOTE,
    ADDON_WITHHOLD_CENSORED,
    ADDON_WITHHOLD_PENDING,
    C1_PTM_GUARD,
    C2_PTM_GUARD_DWELL,
    CHALLENGER_POLICIES,
    DWELL_BARS_OMIN,
    EPISODE_EXPIRY_BARS,
    PARENT_PATH_NO_B3,
    PARENT_PATH_P0,
    PARENT_PATH_P3,
    ParentPlan,
    claim_gate_failures,
    evaluate_addon,
    is_sparse_or_unvisited,
    next_executable_bar,
    reference_is_valid,
)
from ptm_promotion_clock import CONFIRMATION_BARS
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
        "claim_bars_total": 1,
        "claim_bars_at_or_after_eligibility": 1,
        "c1_status": ADDON_PROMOTE,
        "c1_first_release_bar": 113,
        "c1_first_executable_bar": 114,
        "c1_extra_delay_bars": 0,
        "c1_censored": False,
        "c1_missed_addon": False,
        "c2_status": ADDON_PROMOTE,
        "c2_first_release_bar": 113,
        "c2_first_executable_bar": 114,
        "c2_extra_delay_bars": 0,
        "c2_censored": False,
        "c2_missed_addon": False,
        "policies_differ": False,
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
    assert out.status == ADDON_PROMOTE
    assert out.first_release_signal_bar is not None
    assert out.first_executable_bar == out.first_release_signal_bar + 1
    # The decision cannot be taken before the parent has finished confirming.
    assert out.first_release_signal_bar >= 133


def test_a3_no_release_before_eligibility_even_with_claims_from_the_breakout():
    # Claims start at the breakout (110) and continue; the release is still
    # gated at B3 + 3 = 113.
    observations = [obs(b) for b in range(110, 125)]
    out = evaluate_addon(C1_PTM_GUARD, observations, plan(probe=100, b3=110))
    assert out.status == ADDON_PROMOTE
    assert out.first_release_signal_bar == 113
    assert out.first_executable_bar == 114
    assert out.extra_delay_bars == 0


# ===========================================================================
# B. The eight required scenarios
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
    assert out.status == ADDON_PROMOTE
    assert out.first_release_signal_bar == 115
    assert out.first_executable_bar == 116
    # Held for 2 bars past the parent's own timing: 116 - 114 = 2.
    assert out.extra_delay_bars == 2
    assert not out.censored and not out.missed_addon
    held = [d for d in out.trail if d.status == ADDON_WITHHOLD_PENDING]
    assert len(held) == 2
    assert all("conservative hold" in d.reason for d in held)


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
    assert out.status == ADDON_DE_RISK
    assert not out.released
    assert out.first_release_signal_bar is None
    assert out.first_executable_bar is None
    assert out.censored and out.missed_addon
    assert out.extra_delay_bars is None, (
        "a censored outcome must not report a numeric delay"
    )
    assert any("never promotes" in r for r in out.reasons)


def test_b3_data_suddenly_becomes_degraded_and_never_recovers():
    observations = [
        obs(113, claim=True, band=NOVELTY_CLASS_SPARSE, episodes=1),
    ] + [
        obs(b, claim=False, validity=VALIDITY_DEGRADED_SCALE_UNSTABLE,
            scale=False, band=NOVELTY_CLASS_SPARSE, episodes=1,
            scale_state="SCALE_UNSTABLE")
        for b in range(114, 116)
    ]
    observations = [obs(113, claim=True, band=NOVELTY_CLASS_SPARSE,
                        episodes=1)] + observations[1:]
    out = evaluate_addon(C1_PTM_GUARD, observations, plan(probe=100, b3=110))
    # The one trusted claim at 113 is enough for C1 to release; the later
    # degradation cannot retroactively unmake it.
    assert out.status == ADDON_PROMOTE
    assert out.first_release_signal_bar == 113

    # Now the degraded state arrives BEFORE any trusted claim: never releases.
    degraded = [
        obs(b, claim=False, validity=VALIDITY_DEGRADED_SCALE_UNSTABLE,
            scale=False, band=NOVELTY_CLASS_SPARSE, episodes=1,
            scale_state="SCALE_UNSTABLE")
        for b in range(113, 116)
    ]
    out2 = evaluate_addon(C1_PTM_GUARD, degraded, plan(probe=100, b3=110))
    assert out2.status == ADDON_WITHHOLD_CENSORED
    assert out2.censored and out2.missed_addon
    assert out2.extra_delay_bars is None
    reasons = " ".join(d.reason for d in out2.trail)
    assert "scale_state=SCALE_UNSTABLE" in reasons


def test_b4_middle_band_r2_to_r4_is_withheld_and_named_in_the_reason():
    observations = [
        obs(b, claim=False, band=NOVELTY_CLASS_REVISITED, episodes=3)
        for b in range(113, 120)
    ]
    out = evaluate_addon(C1_PTM_GUARD, observations, plan(probe=100, b3=110))
    assert out.status == ADDON_WITHHOLD_CENSORED
    assert out.censored
    assert out.extra_delay_bars is None
    assert any(f"novelty_class={NOVELTY_CLASS_REVISITED}" in d.reason
               or "R>=2" in d.reason for d in out.trail)
    # The gate names the revisit band as the blocker.
    assert f"novelty_class={NOVELTY_CLASS_REVISITED}" in claim_gate_failures(
        observations[0])


def test_b5_permanent_absence_of_release_evidence_is_censored_not_zero():
    """The invariant this whole patch exists to protect."""
    observations = [
        obs(b, claim=False, band=NOVELTY_CLASS_HEAVILY_REVISITED, episodes=7)
        for b in range(113, 200)
    ]
    out = evaluate_addon(C1_PTM_GUARD, observations, plan(probe=100, b3=110))
    assert out.status == ADDON_WITHHOLD_CENSORED
    assert out.censored and out.missed_addon
    assert out.first_executable_bar is None
    assert out.extra_delay_bars is None, (
        "a permanently withheld add-on must be censored, never 0 bars"
    )
    row = out.as_row()
    assert row["extra_delay_bars"] is None
    assert row["extra_delay_bars_is_censored"] is True
    assert "unbounded" in row["reasons"]


def test_b6_episode_expiry_does_not_auto_promote():
    expiry = EPISODE_EXPIRY_BARS
    last = 113 + expiry
    observations = [
        obs(b, claim=False, band=NOVELTY_CLASS_HEAVILY_REVISITED, episodes=7)
        for b in range(110 + 1, last + 1)
    ]
    out = evaluate_addon(C1_PTM_GUARD, observations, plan(probe=100, b3=110))
    assert out.status == ADDON_WITHHOLD_CENSORED
    assert not out.released
    assert out.final_bar == last
    assert f"expired at bar {last}" in " ".join(out.reasons)
    # Expiry is not confirmation: nothing after the expiry bar changes it.
    longer = observations + [
        obs(b, claim=True, band=NOVELTY_CLASS_UNVISITED, episodes=0)
        for b in range(last + 1, last + 4)
    ]
    out2 = evaluate_addon(C1_PTM_GUARD, longer, plan(probe=100, b3=110))
    assert out2.status == ADDON_WITHHOLD_CENSORED


def test_b7_no_parent_entitlement_is_not_charged_to_ptm():
    observations = [obs(b, claim=False) for b in range(120, 130)]

    p3 = plan(probe=100, b3=110, path=PARENT_PATH_P3)
    out_p3 = evaluate_addon(C1_PTM_GUARD, observations, p3)
    assert out_p3.status == ADDON_NOT_ELIGIBLE
    assert out_p3.eligible_promotion_bar is None
    assert out_p3.extra_delay_bars is None
    assert out_p3.missed_addon is False, "PTM withheld nothing here"
    assert out_p3.censored is False

    no_b3 = plan(probe=100, b3=None, path=PARENT_PATH_NO_B3, usable=False)
    out_no = evaluate_addon(C1_PTM_GUARD, observations, no_b3)
    assert out_no.status == ADDON_NOT_ELIGIBLE
    assert out_no.missed_addon is False


def test_b8_long_short_symmetry():
    """A short mirror must produce the same decision, bar for bar."""
    long_fx = true_trend()
    short_fx = fixtures_module.short_mirror_of(long_fx)
    decisions = []
    for fx in (long_fx, short_fx):
        episode = evaluate_episode(fx.bars, fx.probe_index, fx.direction,
                                   fx.config)
        observations = [o for o in episode.observations if o.novelty is not None]
        p = ParentPlan(probe_bar=fx.probe_index, b3_break_bar=120,
                       path=PARENT_PATH_P0)
        decisions.append(evaluate_addon(C1_PTM_GUARD, observations, p))
    a, b = decisions
    assert a.status == b.status
    assert a.first_release_signal_bar == b.first_release_signal_bar
    assert a.first_executable_bar == b.first_executable_bar
    assert a.extra_delay_bars == b.extra_delay_bars


def test_b9_no_future_leak_release_bar_is_prefix_stable():
    """Truncating the series must not move a release that already happened."""
    long_fx = true_trend()
    episode = evaluate_episode(long_fx.bars, long_fx.probe_index,
                               long_fx.direction, long_fx.config)
    observations = list(episode.observations)
    p = ParentPlan(probe_bar=long_fx.probe_index, b3_break_bar=120,
                   path=PARENT_PATH_P0)
    full = evaluate_addon(C1_PTM_GUARD, observations, p)
    assert full.status == ADDON_PROMOTE
    release = full.first_release_signal_bar
    release_idx = next(i for i, o in enumerate(observations)
                       if o.bar_index == release)

    # Any prefix that still contains the release bar must reproduce it exactly.
    for cut in range(release_idx, len(observations)):
        prefix = observations[:cut + 1]
        got = evaluate_addon(C1_PTM_GUARD, prefix, p)
        assert got.status == full.status, (cut, got.status)
        assert got.first_release_signal_bar == release, cut
        assert got.first_executable_bar == full.first_executable_bar, cut
        assert got.extra_delay_bars == full.extra_delay_bars, cut

    # Any prefix that stops before the release must NOT claim a release.
    for cut in range(0, release_idx):
        prefix = observations[:cut + 1]
        got = evaluate_addon(C1_PTM_GUARD, prefix, p)
        assert not got.released, (cut, got.status)


# ===========================================================================
# C. Safety properties of the policy
# ===========================================================================
def test_c1_three_challengers_are_rejected():
    observations = [obs(113)]
    with pytest.raises(ValueError, match="no third challenger"):
        evaluate_addon("C3_SOMETHING_NEW", observations,
                       plan(probe=100, b3=110))
    assert len(CHALLENGER_POLICIES) == 2
    assert CHALLENGER_POLICIES == (C1_PTM_GUARD, C2_PTM_GUARD_DWELL)


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
    assert out.status == ADDON_ALREADY_FULL
    assert out.extra_delay_bars == 0
    assert not out.censored


def test_c5_dwell_counts_the_parents_own_acceptance_window():
    """C2 dwell is measured over B3+1..B3+3, so the parent horizon is reused."""
    assert DWELL_BARS_OMIN == CONFIRMATION_BARS
    assert EPISODE_EXPIRY_BARS == PTMConfig().reference_bars
    # A claim on every acceptance bar releases at the eligibility bar.
    observations = [obs(b) for b in range(111, 120)]
    out = evaluate_addon(C2_PTM_GUARD_DWELL, observations,
                         plan(probe=100, b3=110))
    assert out.status == ADDON_PROMOTE
    assert out.first_release_signal_bar == 113
    assert out.extra_delay_bars == 0

    # A claim appearing only at the eligibility bar does not satisfy o_min=3.
    only_last = [
        obs(111, claim=False, band=NOVELTY_CLASS_SPARSE, episodes=1),
        obs(112, claim=False, band=NOVELTY_CLASS_SPARSE, episodes=1),
        obs(113, claim=True, band=NOVELTY_CLASS_SPARSE, episodes=1),
    ]
    out2 = evaluate_addon(C2_PTM_GUARD_DWELL, only_last,
                          plan(probe=100, b3=110))
    assert out2.status == ADDON_WITHHOLD_CENSORED
    # C1 still releases on the same input, which is why C2 is a distinct
    # challenger rather than a duplicate.
    out3 = evaluate_addon(C1_PTM_GUARD, only_last, plan(probe=100, b3=110))
    assert out3.status == ADDON_PROMOTE
    assert out3.first_release_signal_bar == 113


def test_c6_on_the_synthetic_set_c1_never_contradicts_the_signal():
    """Every C1 withhold must coincide with the absence of a claim."""
    from analyze_issue185_price_territory import addon_policy_rows
    episodes = {}
    fixtures = list(all_fixtures())
    for fx in fixtures:
        episodes[fx.name] = evaluate_episode(fx.bars, fx.probe_index,
                                             fx.direction, fx.config)
    rows = addon_policy_rows(fixtures, episodes)
    offenders = [r["fixture"] for r in rows
                 if r["parent_earns_addon"]
                 and r["c1_censored"]
                 and r["claim_bars_at_or_after_eligibility"] > 0]
    assert offenders == [], (
        "C1 withheld a fixture that had a claim at/after eligibility: "
        f"{offenders}"
    )
    assert any(r["c1_censored"] for r in rows), (
        "no fixture is withheld, so this invariant is vacuous"
    )


def test_c7_long_period_box_addon_is_withheld():
    """The blocking wide-box false release must also lose its add-on."""
    fx = long_period_box()
    episode = evaluate_episode(fx.bars, fx.probe_index, fx.direction, fx.config)
    p = ParentPlan(probe_bar=fx.probe_index, b3_break_bar=120,
                   path=PARENT_PATH_P0)
    for policy in CHALLENGER_POLICIES:
        out = evaluate_addon(policy, episode.observations, p)
        assert out.status == ADDON_WITHHOLD_CENSORED, policy
        assert not out.released, policy
        assert out.extra_delay_bars is None, policy


def test_c8_abstain_branch_is_provably_unreachable():
    """The 'abstain / baseline handles' outcome cannot occur.

    Its precondition is a trusted reference at R <= 1 that makes no claim.
    ``reference_is_valid`` conjoins exactly the claim gate's non-novelty
    conjuncts, so at R <= 1 the claim must be True.  This is what makes the
    review's "abstain vs conservative hold" choice non-exercisable rather than
    merely untested.
    """
    from ptm_addon_policy import ADDON_BASELINE_HANDLES  # noqa: F401
    from analyze_issue185_price_territory import (
        abstain_branch_reachability, addon_policy_rows)

    trust = obs(113, claim=False, band=NOVELTY_CLASS_SPARSE, episodes=1)
    # A trusted reference at R <= 1 always carries the claim.
    assert reference_is_valid(trust)
    assert is_sparse_or_unvisited(trust)
    # The only way to make the reference untrusted is to break one of its own
    # conjuncts, which is also a claim-gate conjunct -- so the precondition
    # cannot be satisfied.  Demonstrate it on every synthetic observation.
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
    assert "PENDING_SOPHIRA_APPROVAL" in scan["prereg_consequence"]

    # And per-observation: trusted + R<=1 implies the claim.
    for fx in fixtures:
        for o in episodes[fx.name].observations:
            if reference_is_valid(o) and is_sparse_or_unvisited(o):
                assert o.is_new_territory_claim, (fx.name, o.bar_index)

    # The evaluation itself never yields the abstain status.
    statuses = {r["c1_status"] for r in addon_policy_rows(fixtures, episodes)}
    assert "BASELINE_HANDLES" not in statuses, statuses


def test_c9_declared_statuses_are_enumerated_not_implied():
    """Every declared outcome is listed, and the unobserved ones are named."""
    from analyze_issue185_price_territory import addon_policy_summary
    rows = [
        _row(fixture="a"),
    ]
    s = addon_policy_summary(rows)
    assert len(s["declared_statuses"]) == 7
    assert s["c1_status_distribution"] == {"PROMOTE": 1}
    never = s["c1_declared_statuses_never_observed"]
    assert "WITHHOLD_CENSORED" in never
    assert "BASELINE_HANDLES" in never
    assert "provably unreachable" in s[
        "c1_declared_statuses_never_observed_note"].lower()


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
    assert prov["freeze_status"] == "PENDING_SOPHIRA_APPROVAL"
    # The rehearsal is a contract, recorded because the export is not committed.
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


def test_e3_addon_policy_summary_reports_censoring_explicitly():
    from analyze_issue185_price_territory import addon_policy_summary
    rows = [
        _row(fixture="a"),
        _row(fixture="b", c1_status=ADDON_WITHHOLD_CENSORED,
             c2_status=ADDON_WITHHOLD_CENSORED, c1_censored=True,
             c1_missed_addon=True, claim_bars_at_or_after_eligibility=0,
             c1_first_release_bar=None, c1_first_executable_bar=None,
             c1_extra_delay_bars=None, c2_first_release_bar=None,
             c2_first_executable_bar=None, c2_extra_delay_bars=None,
             c2_censored=True, sustained_escape=True),
        _row(fixture="c", parent_earns_addon=False,
             c1_status=ADDON_NOT_ELIGIBLE, c2_status=ADDON_NOT_ELIGIBLE,
             c1_first_release_bar=None, c1_first_executable_bar=None,
             c1_extra_delay_bars=None, c2_first_release_bar=None,
             c2_first_executable_bar=None, c2_extra_delay_bars=None,
             claim_bars_at_or_after_eligibility=0),
    ]
    s = addon_policy_summary(rows)
    assert s["fixtures_with_parent_addon_entitlement"] == 2
    assert s["fixtures_without_parent_entitlement"] == 1
    assert s["c1_released"] == 1 and s["c1_censored"] == 1
    assert s["c1_censored_share_of_entitled"] == 0.5
    # The censored row is excluded from the delay statistics entirely.
    assert s["c1_max_delay_over_released"] == 0
    assert s["c1_mean_delay_over_released"] == 0.0
    assert "unbounded" in s["c1_delay_scope"]
    assert s["censored_never_reported_as_zero"] is True


def test_e4_every_fixture_is_classified_for_the_cost_headline():
    """No fixture may silently fall outside the declared classification."""
    from analyze_issue185_price_territory import NON_SCENARIO_FIXTURES
    names = {fx.name for fx in all_fixtures()}
    unknown = set(NON_SCENARIO_FIXTURES) - names
    assert unknown == set(), f"declared but non-existent fixtures: {unknown}"
    assert all(v.strip() for v in NON_SCENARIO_FIXTURES.values())
