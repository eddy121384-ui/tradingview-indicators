#!/usr/bin/env python3
"""Issue #185 -- C1 add-on (second-entry) exposure policy.

ACTIVE STUDY: ONE CHALLENGER (C1)
---------------------------------
The active empirical study compares exactly one challenger, ``C1_PTM_GUARD``,
against the two frozen benchmarks ``B0 = R0 Immediate`` and
``B1 = R0 + Warning-First``.  ``C2_PTM_GUARD_DWELL`` is RETIRED from the active
candidate set, the comparison surface and the prereg decision surface; its code
and tests are retained so the historical evidence stays reproducible.  No
substitute challenger, no harsher variant and no parameter sweep replaces it.

Why C2 was retired (Sophira final review, 2026-10-14): the approved C2 was
"PTM Guard + historical touch-occupancy", i.e. an additional HOLD condition
expressed as an occupancy proportion ``O`` in ``[0, 1]``.  What was implemented
was "three consecutive affirmative new-territory claims inside the parent's B3
acceptance window before RELEASE" -- a *claim-persistence* condition, not
historical dwelling, which additionally reverses the role of the secondary
evidence (a hold condition became a release condition) and silently changed the
unit from an occupancy proportion to a bar count.  That is a different
hypothesis, so it is not promoted into the study.

This module is a *policy prototype*, not an indicator.  It decides one thing
only: whether the extra 75% of exposure that the frozen parent model has
already earned ("the add-on") is **released** or **withheld** because of PTM
territory evidence.  It never accelerates a promotion, never reduces exposure,
and never sizes a position.

DISPOSITION vs FOLLOW-UP COMPLETENESS
-------------------------------------
A disposition must separate *what the policy did* from *how much data we have*.
An episode whose data ends before the predeclared decision horizon is complete
cannot establish either a permanent withholding or a missed earned add-on: the
future is unknown.  ``OBSERVATION_RIGHT_CENSORED`` exists for exactly that case
and is never counted as a permanent loss.

Parent clock (frozen in issue #78, not redefined here)
------------------------------------------------------
``analyze_issue78_second_entry_economic_policy.py`` states the parent contract:

* 25% Probe is taken before add-risk (``PROBE = 0.25``, ``FULL = 1.00``);
* the evidence chain is Breakout -> Acceptance -> Retest -> Resume;
* ``R0_Immediate`` -- the frozen baseline -- adds immediately at ``t+3``;
* ``P0_NoTouch`` / ``P1_WickHold`` / ``P2_Reclaim`` all add at ``t+3``;
* ``P3_FailedAcceptance`` never adds;
* "episodes without a usable B3 breakout remain at Probe".

So ``eligible_promotion_t = B3_break_t + 3`` and the fill cannot happen before
the next tradable bar::

    next_executable_t = max(eligible_promotion_t, PTM_observation_t) + 1

Why the guard is not "not ``HEAVILY_REVISITED``"
-----------------------------------------------
The frozen claim rule is ``is_new_territory_claim = novelty_fresh and
allows_new_territory_claim and not suspect``, and ``novelty_fresh`` is exactly
``novelty_class in (UNVISITED, SPARSE)``, i.e. ``R <= 1``.  Therefore:

* an *affirmative claim* can only ever be emitted while ``R <= 1``;
* once ``R >= 2`` the frozen rule can never certify new territory again in that
  episode, so "wait for a claim" is not a release path for the revisited bands;
* and on the ``long_period_box`` counterexample the written "only veto while
  HEAVILY_REVISITED" rule fails open, because that episode sits at ``R <= 1``
  and is blocked by reference *adequacy*, not by revisit count.

C1 and C2 therefore gate on the **full claim gate**, not on a revisit band.
The revisit band selects how much evidence is demanded, and the invalid
(``DEGRADED``/``UNKNOWN``) state always withholds rather than pretending the
territory is either novel or benign.

CONSERVATIVE HOLD IS A POLICY CHOICE, NOT A MATHEMATICAL NECESSITY
------------------------------------------------------------------
C1 withholds the earned add-on while the reference is ``DEGRADED`` or
``UNKNOWN``.  That is a deliberate research choice by Sophira, **not** the only
option the frozen mathematics allows.  An alternative design could route the
``DEGRADED``/``UNKNOWN`` state straight to the unmodified baseline so that R0's
own decision stands, and that alternative requires **no** change to A1-A7,
``R``/``O``/``N``, the thresholds or the B3 clock.  The choice is therefore a
policy preference about which error to prefer, and it must be reported with its
full opportunity cost.  (An earlier note in this repository claimed the choice
was mathematically unavailable; that claim was wrong and is withdrawn -- see
``BASELINE_ON_DEGRADED_ALTERNATIVE``.)

Note the separate, narrower fact: the ``BASELINE_HANDLES`` outcome for a
*trusted* reference at ``R <= 1`` with no claim is unreachable, because
``reference_is_valid`` implies the claim gate's non-novelty conjuncts.  That
fact says nothing about the ``DEGRADED``/``UNKNOWN`` routing choice above.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Mapping, Sequence

from ptm_promotion_clock import CONFIRMATION_BARS
from ptm_territory import (
    NOVELTY_CLASS_SPARSE,
    NOVELTY_CLASS_UNVISITED,
    PTMConfig,
    VALIDITY_OK,
    TerritoryObservation,
)

# ---------------------------------------------------------------------------
# Policy identity.  ONE active challenger; adding a third is out of scope.
# ---------------------------------------------------------------------------
C1_PTM_GUARD = "C1_PTM_GUARD"
C2_PTM_GUARD_DWELL = "C2_PTM_GUARD_DWELL"

#: The active prereg candidate set.  Exactly one challenger.  Adding a
#: substitute, a harsher C2 or a parameter variant is out of scope.
ACTIVE_CHALLENGERS = (C1_PTM_GUARD,)
#: Retired from the active study; kept only so the historical evidence and its
#: unit tests remain reproducible.  Never reported as a research candidate and
#: never counted in the candidate count.
RETIRED_CHALLENGERS = (C2_PTM_GUARD_DWELL,)
#: Everything ``evaluate_addon`` will accept.  Acceptance is NOT endorsement:
#: C2 is evaluated in the artifacts purely as retained historical evidence.
CHALLENGER_POLICIES = ACTIVE_CHALLENGERS + RETIRED_CHALLENGERS

#: The rejected alternative to C1's degraded handling, documented but NOT
#: implemented as a challenger and NOT part of the candidate count.
#:
#: Under this design a ``DEGRADED``/``UNKNOWN`` reference would release the hold
#: and let the unmodified baseline R0 decision stand, instead of holding
#: conservatively.  It needs no change to the frozen instrument, which is why
#: "conservative hold" is a preference about which error to prefer rather than a
#: mathematical consequence.  C1 does NOT take this route.
BASELINE_ON_DEGRADED_ALTERNATIVE = "ALT_BASELINE_ON_DEGRADED"

# ---------------------------------------------------------------------------
# Dwell horizon for C2 (``o_min``).  HISTORICAL ONLY.
#
# C2 is retired from the active study, so this number is no longer a research
# parameter and MUST NOT be tuned, replaced or re-justified.  It is kept beside
# the retained C2 code so the historical artifacts stay reproducible.
#
# IMPORTANT: ``o_min`` counts bars on which a novelty claim held inside the
# parent's acceptance window.  It is a claim-PERSISTENCE count, NOT a measure of
# historical territory dwelling, and it must never be described as occupancy.
# ---------------------------------------------------------------------------
DWELL_BARS_OMIN = CONFIRMATION_BARS  # 3

#: In-episode expiry, in completed bars after the parent's eligibility bar.
#: Tied to the frozen reference window so the two cannot drift apart.
EPISODE_EXPIRY_BARS = PTMConfig().reference_bars  # 120

# ---------------------------------------------------------------------------
# Add-on disposition.
#
# A disposition answers exactly one question: what happened to the parent's
# earned 75% add-on?  The five canonical dispositions are reported separately,
# and the distinction that was missing before is
# ``OBSERVATION_RIGHT_CENSORED``: when the data ends before the decision horizon
# is complete, the add-on's fate is UNKNOWN.  That is categorically different
# from a policy that positively withheld through a complete horizon, and the two
# must never be summed into one "censored" number.
# ---------------------------------------------------------------------------
#: The parent never earned an add-on (P3, or no usable B3).  Not a PTM cost.
DISPOSITION_PARENT_NOT_ELIGIBLE = "PARENT_NOT_ELIGIBLE"
#: Follow-up incomplete: the predeclared post-eligible horizon was not fully
#: observed, so a future release is unknown.  NOT evidence of permanent loss.
DISPOSITION_OBSERVATION_RIGHT_CENSORED = "OBSERVATION_RIGHT_CENSORED"
#: The policy positively withheld through the complete decision horizon with no
#: valid release.  This is the only disposition that establishes a permanent
#: add-on loss.
DISPOSITION_POLICY_WITHHELD_THROUGH_EXPIRY = "POLICY_WITHHELD_THROUGH_EXPIRY"
#: The baseline de-risked/exited before any release, so PTM never decided.
DISPOSITION_BASELINE_DE_RISK_BEFORE_RELEASE = "BASELINE_DE_RISK_BEFORE_RELEASE"
#: The add-on was released and executed at a finite, observed delay.
DISPOSITION_PROMOTED = "PROMOTED"
#: Supplementary, outside the five: already at full exposure before eligibility.
DISPOSITION_ALREADY_FULL = "ALREADY_FULL"
#: Supplementary: trusted reference at R<=1 with no claim. Provably unreachable
#: (see the module docstring); kept as an auditable fallback, never taken.
DISPOSITION_BASELINE_HANDLES = "BASELINE_HANDLES"

CANONICAL_DISPOSITIONS = (
    DISPOSITION_PARENT_NOT_ELIGIBLE,
    DISPOSITION_OBSERVATION_RIGHT_CENSORED,
    DISPOSITION_POLICY_WITHHELD_THROUGH_EXPIRY,
    DISPOSITION_BASELINE_DE_RISK_BEFORE_RELEASE,
    DISPOSITION_PROMOTED,
)
#: Canonical plus the two supplementary labels, so nothing is silently dropped
#: from an accounting table.
DECLARED_DISPOSITIONS = CANONICAL_DISPOSITIONS + (
    DISPOSITION_ALREADY_FULL,
    DISPOSITION_BASELINE_HANDLES,
)

# Per-bar audit-trail labels.  These are NOT dispositions: the trail records the
# state of each bar, while the disposition summarises the whole episode.
STATUS_WITHHOLD_PENDING = "WITHHOLD_PENDING"

# ---------------------------------------------------------------------------
# Back-compatible aliases.  These names predate the disposition taxonomy; each
# now maps to the canonical label with identical semantics where it existed, and
# ``ADDON_WITHHOLD_CENSORED`` is deliberately GONE because it conflated
# right-censoring with a definite withholding.
# ---------------------------------------------------------------------------
ADDON_PROMOTE = DISPOSITION_PROMOTED
ADDON_NOT_ELIGIBLE = DISPOSITION_PARENT_NOT_ELIGIBLE
ADDON_DE_RISK = DISPOSITION_BASELINE_DE_RISK_BEFORE_RELEASE
ADDON_ALREADY_FULL = DISPOSITION_ALREADY_FULL
ADDON_BASELINE_HANDLES = DISPOSITION_BASELINE_HANDLES
ADDON_WITHHOLD_PENDING = STATUS_WITHHOLD_PENDING
ADDON_OBSERVATION_RIGHT_CENSORED = DISPOSITION_OBSERVATION_RIGHT_CENSORED
ADDON_WITHHOLD_THROUGH_EXPIRY = DISPOSITION_POLICY_WITHHELD_THROUGH_EXPIRY

PARENT_PATH_P0 = "P0_NoTouch"
PARENT_PATH_P1 = "P1_WickHold"
PARENT_PATH_P2 = "P2_Reclaim"
PARENT_PATH_P3 = "P3_FailedAcceptance"
PARENT_PATH_NO_B3 = "NO_USABLE_B3"
PARENT_PATHS = (PARENT_PATH_P0, PARENT_PATH_P1, PARENT_PATH_P2, PARENT_PATH_P3,
                PARENT_PATH_NO_B3)
#: Paths on which the frozen parent adds at t+3.
PARENT_PATHS_THAT_ADD = (PARENT_PATH_P0, PARENT_PATH_P1, PARENT_PATH_P2)


@dataclass(frozen=True)
class ParentPlan:
    """The parent's own add-on entitlement for one episode.

    This is *input* to the policy.  The policy never recomputes or overrides
    the parent clock; it only decides whether the earned add-on is released.
    """

    probe_bar: int
    b3_break_bar: int | None
    path: str
    usable_b3: bool = True
    deteriorated_at: int | None = None
    already_full_at: int | None = None

    def __post_init__(self) -> None:
        if self.path not in PARENT_PATHS:
            raise ValueError(
                f"unknown parent path {self.path!r}; expected one of "
                f"{PARENT_PATHS}"
            )
        if self.usable_b3:
            if self.b3_break_bar is None:
                raise ValueError("usable_b3 requires b3_break_bar")
            if self.b3_break_bar < self.probe_bar:
                raise ValueError(
                    f"b3_break_bar {self.b3_break_bar} precedes probe_bar "
                    f"{self.probe_bar}"
                )
        elif self.b3_break_bar is not None:
            raise ValueError("b3_break_bar must be None when usable_b3 is False")

    @property
    def eligible_promotion_bar(self) -> int | None:
        """``B3_break_t + CONFIRMATION_BARS``; None when nothing was earned."""
        if not self.usable_b3 or self.b3_break_bar is None:
            return None
        if self.path == PARENT_PATH_P3:
            return None
        return int(self.b3_break_bar) + CONFIRMATION_BARS

    @property
    def parent_earns_addon(self) -> bool:
        return self.eligible_promotion_bar is not None


def next_executable_bar(signal_bar: int) -> int:
    """The first bar a decision taken on ``signal_bar`` can be filled on."""
    return int(signal_bar) + 1


def band_of(observation: TerritoryObservation) -> str:
    """The revisit band, taken from the frozen novelty classification."""
    return observation.novelty_class or "UNKNOWN"


def is_sparse_or_unvisited(observation: TerritoryObservation) -> bool:
    """``R <= 1``: the only band in which the frozen rule can claim."""
    return observation.novelty_class in (NOVELTY_CLASS_UNVISITED,
                                         NOVELTY_CLASS_SPARSE)


def claim_gate_failures(observation: TerritoryObservation) -> tuple[str, ...]:
    """Why the frozen claim gate is closed, one reason per open conjunct.

    Mirrors ``FrozenReference.allows_new_territory_claim`` plus the
    ``novelty_fresh`` and ``not suspect`` conjuncts of the claim rule, so a
    withheld add-on can always name the exact reason instead of being a bare
    boolean.
    """
    reasons: list[str] = []
    if observation.validity != VALIDITY_OK:
        reasons.append(f"validity={observation.validity}")
    if not (observation.reference_coverage >= 1.0):
        reasons.append(
            f"reference_coverage={observation.reference_coverage:.4f}<1.0"
        )
    if not observation.reference_adequacy_ok:
        reasons.append("reference_adequacy_failed")
    if not observation.scale_stable:
        reasons.append(f"scale_state={observation.scale_state}")
    if observation.suspect_scale_break:
        reasons.append("suspect_scale_break")
    if not is_sparse_or_unvisited(observation):
        reasons.append(f"novelty_class={band_of(observation)}")
    return tuple(reasons)


def reference_is_valid(observation: TerritoryObservation) -> bool:
    """True only for a fully trusted reference (A1 and A3 both passed)."""
    return bool(
        observation.validity == VALIDITY_OK
        and observation.reference_coverage >= 1.0
        and observation.reference_adequacy_ok
        and observation.scale_stable
        and not observation.suspect_scale_break
    )


@dataclass(frozen=True)
class AddOnDecision:
    """One bar's decision, kept for the audit trail."""

    bar_index: int
    status: str
    releases: bool
    claim: bool
    band: str
    revisit_episodes: int | None
    gate_failures: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class AddOnOutcome:
    """The whole-episode result of one challenger policy.

    ``disposition`` is the canonical label.  ``followup_complete`` says whether
    the predeclared post-eligible decision horizon was actually observed, and
    ``withheld_definite`` is True ONLY when the policy positively withheld
    through that complete horizon.  A right-censored episode has
    ``followup_complete=False``, ``withheld_definite=False`` and
    ``extra_delay_bars=None``: its future is unknown, not zero and not
    unbounded-by-proof.
    """

    policy: str
    disposition: str
    parent_path: str
    eligible_promotion_bar: int | None
    first_release_signal_bar: int | None
    first_executable_bar: int | None
    #: Bars of extra delay versus the parent's own R0 timing.  ``None`` whenever
    #: the delay was not observed: reporting 0 there would be false.
    extra_delay_bars: int | None
    #: The predeclared decision horizon ``eligible + expiry_bars`` was reached
    #: (or a terminal event closed the episode) before the data ran out.
    followup_complete: bool
    #: PTM positively withheld through the complete horizon.  Only this flag
    #: establishes a permanent add-on loss.
    withheld_definite: bool
    #: Completed bars observed at or after the eligibility bar.
    observed_post_eligible_bars: int
    #: An unreleased hold was still open when the data ran out.
    open_hold_at_last_bar: bool
    #: The horizon length this evaluation required, for the report.
    horizon_bars_required: int
    final_bar: int | None
    reasons: tuple[str, ...] = ()
    trail: tuple[AddOnDecision, ...] = field(default=(), repr=False)

    @property
    def released(self) -> bool:
        return self.disposition == DISPOSITION_PROMOTED

    @property
    def censored(self) -> bool:
        """A delay exists but was not observed.  Never average this in as zero.

        ``PARENT_NOT_ELIGIBLE`` and ``ALREADY_FULL`` are not censored: there was
        never a delay to observe, so they are neither observed nor censored.
        """
        if self.disposition in (DISPOSITION_PARENT_NOT_ELIGIBLE,
                               DISPOSITION_ALREADY_FULL):
            return False
        return self.extra_delay_bars is None

    @property
    def status(self) -> str:
        """Alias of ``disposition`` kept for the historical evidence readers."""
        return self.disposition

    def as_row(self) -> dict:
        return {
            "policy": self.policy,
            "disposition": self.disposition,
            "parent_path": self.parent_path,
            "eligible_promotion_bar": self.eligible_promotion_bar,
            "first_release_signal_bar": self.first_release_signal_bar,
            "first_executable_bar": self.first_executable_bar,
            "extra_delay_bars": self.extra_delay_bars,
            "extra_delay_bars_observed": not self.censored,
            "followup_complete": self.followup_complete,
            "withheld_definite": self.withheld_definite,
            "observed_post_eligible_bars": self.observed_post_eligible_bars,
            "open_hold_at_last_bar": self.open_hold_at_last_bar,
            "horizon_bars_required": self.horizon_bars_required,
            "final_bar": self.final_bar,
            "reasons": "; ".join(self.reasons),
        }


def _outcome(policy: str, disposition: str, plan: ParentPlan, *,
             eligible: int | None, release_bar: int | None = None,
             followup_complete: bool, withheld_definite: bool,
             observed_post_eligible_bars: int, open_hold_at_last_bar: bool,
             horizon_bars_required: int, final_bar: int | None,
             reason: str, trail: tuple) -> AddOnOutcome:
    """Single construction point, so no field can drift between branches."""
    if release_bar is not None:
        exec_bar = next_executable_bar(release_bar)
        delay = exec_bar - next_executable_bar(int(eligible))
    else:
        exec_bar = None
        delay = None
    return AddOnOutcome(
        policy=policy,
        disposition=disposition,
        parent_path=plan.path,
        eligible_promotion_bar=eligible,
        first_release_signal_bar=release_bar,
        first_executable_bar=exec_bar,
        extra_delay_bars=delay,
        followup_complete=followup_complete,
        withheld_definite=withheld_definite,
        observed_post_eligible_bars=observed_post_eligible_bars,
        open_hold_at_last_bar=open_hold_at_last_bar,
        horizon_bars_required=horizon_bars_required,
        final_bar=final_bar,
        reasons=(reason,),
        trail=trail,
    )


def _absent_observation(band: str = "UNKNOWN") -> str:
    return f"no PTM observation at or after the eligibility bar ({band})"


def evaluate_addon(
    policy: str,
    observations: Mapping[int, TerritoryObservation] | Sequence[TerritoryObservation],
    plan: ParentPlan,
    *,
    dwell_bars: int = DWELL_BARS_OMIN,
    expiry_bars: int = EPISODE_EXPIRY_BARS,
) -> AddOnOutcome:
    """Evaluate one challenger policy for one episode.

    Causality: the decision at bar ``t`` uses only the observation *at* ``t``
    (a completed close, itself observable at ``t``) and earlier decisions.  The
    earliest bar at which the resulting order can fill is ``t + 1``.
    """
    if policy not in CHALLENGER_POLICIES:
        raise ValueError(
            f"unknown policy {policy!r}; exactly {CHALLENGER_POLICIES} are "
            "preregistered, and no third challenger may be added"
        )
    if dwell_bars < 1:
        raise ValueError(f"dwell_bars must be >= 1, got {dwell_bars}")
    if expiry_bars < 1:
        raise ValueError(f"expiry_bars must be >= 1, got {expiry_bars}")

    if isinstance(observations, Mapping):
        by_bar = dict(observations)
    else:
        by_bar = {o.bar_index: o for o in observations}
    if not by_bar:
        raise ValueError("no PTM observations supplied")

    eligible = plan.eligible_promotion_bar
    last_bar = max(by_bar)
    trail: list[AddOnDecision] = []

    def record(bar: int, status: str, releases: bool, op, reason: str) -> None:
        trail.append(AddOnDecision(
            bar_index=bar,
            status=status,
            releases=releases,
            claim=bool(op.is_new_territory_claim) if op is not None else False,
            band=band_of(op) if op is not None else "UNKNOWN",
            revisit_episodes=op.revisit_episodes if op is not None else None,
            gate_failures=claim_gate_failures(op) if op is not None else (),
            reason=reason,
        ))

    def post_eligible_bars(upto: int) -> int:
        """Count ACTUAL observations, never inferred bars between two indexes."""
        return sum(1 for index in by_bar if eligible <= index <= upto)

    # --- Case: the parent never earned the add-on at all -------------------
    # The 75% was never going to be added, so PTM withheld nothing.  This is
    # not a PTM cost and not a PTM delay.
    if eligible is None:
        reason = (
            PARENT_PATH_P3
            if plan.path == PARENT_PATH_P3
            else f"parent has no add-on entitlement (path={plan.path})"
        )
        op = by_bar.get(min(by_bar))
        record(last_bar, ADDON_NOT_ELIGIBLE, False, op, reason)
        return _outcome(
            policy, DISPOSITION_PARENT_NOT_ELIGIBLE, plan, eligible=None,
            followup_complete=False, withheld_definite=False,
            observed_post_eligible_bars=0, open_hold_at_last_bar=False,
            horizon_bars_required=expiry_bars, final_bar=last_bar,
            reason=reason, trail=tuple(trail))

    # --- Case: exposure was already at full before the decision ------------
    if plan.already_full_at is not None and plan.already_full_at <= eligible:
        reason = (
            f"exposure already full at bar {plan.already_full_at}; PTM has no "
            "effect on an executed add-on and never reduces exposure"
        )
        record(eligible, ADDON_ALREADY_FULL, False, by_bar.get(eligible), reason)
        # Delay is genuinely 0 here: the parent's own add-on already happened,
        # so there is nothing for PTM to delay.
        return AddOnOutcome(
            policy=policy,
            disposition=DISPOSITION_ALREADY_FULL,
            parent_path=plan.path,
            eligible_promotion_bar=eligible,
            first_release_signal_bar=None,
            first_executable_bar=None,
            extra_delay_bars=0,
            followup_complete=False,
            withheld_definite=False,
            observed_post_eligible_bars=0,
            open_hold_at_last_bar=False,
            horizon_bars_required=expiry_bars,
            final_bar=eligible,
            reasons=(reason,),
            trail=tuple(trail),
        )

    # --- Case: the parent deteriorates before release ----------------------
    # Deterioration invokes the inherited de-risk/exit handling.  It must never
    # be converted into a promotion, and never into "waiting paid off".  PTM did
    # not withhold here -- the baseline closed the position -- so this is not a
    # definite PTM withholding.
    if plan.deteriorated_at is not None and plan.deteriorated_at <= eligible:
        reason = (
            f"parent deteriorated at bar {plan.deteriorated_at} before "
            "release; baseline de-risk/exit handles this and deterioration "
            "never promotes"
        )
        record(eligible, ADDON_DE_RISK, False, by_bar.get(eligible), reason)
        return _outcome(
            policy, DISPOSITION_BASELINE_DE_RISK_BEFORE_RELEASE, plan,
            eligible=eligible, followup_complete=True, withheld_definite=False,
            observed_post_eligible_bars=0, open_hold_at_last_bar=False,
            horizon_bars_required=expiry_bars, final_bar=eligible,
            reason=reason, trail=tuple(trail))

    # --- Walk the parent's own acceptance window, then the eligible bars ----
    # The window is ``b3_break + 1 .. b3_break + CONFIRMATION_BARS``; the last
    # bar of it IS the eligibility bar, so the whole window is observed before
    # any release can happen.  Dwell counts claims inside that window.
    if plan.usable_b3 and plan.b3_break_bar is not None:
        window_start = int(plan.b3_break_bar) + 1
    else:
        window_start = eligible
    walk_start = max(window_start, min(by_bar))

    dwell_run = 0
    #: Decision horizon: the first bar at which the policy episode is over.
    expiry_bar = eligible + expiry_bars
    saw_dwell_pending = False

    for t in range(walk_start, last_bar + 1):
        op = by_bar.get(t)
        post_eligibility = t >= eligible

        # Deterioration: stop and hand over to the baseline.  Never promotes.
        if plan.deteriorated_at is not None and t >= plan.deteriorated_at:
            reason = (
                f"parent deteriorated at bar {plan.deteriorated_at} before the "
                "add-on was released; the baseline's de-risk/exit handles this "
                "and deterioration never promotes"
            )
            record(t, ADDON_DE_RISK, False, op, reason)
            return _outcome(
                policy, DISPOSITION_BASELINE_DE_RISK_BEFORE_RELEASE, plan,
                eligible=eligible, followup_complete=True,
                withheld_definite=False,
                observed_post_eligible_bars=post_eligible_bars(t),
                open_hold_at_last_bar=False, horizon_bars_required=expiry_bars,
                final_bar=t, reason=reason, trail=tuple(trail))

        if op is None:
            # No reading.  An absent observation is never evidence.
            dwell_run = 0
            if post_eligibility:
                record(t, ADDON_WITHHOLD_PENDING, False, None,
                       _absent_observation())
        elif not reference_is_valid(op):
            # DEGRADED / UNKNOWN: conservative hold -- an explicit POLICY
            # CHOICE (see BASELINE_ON_DEGRADED_ALTERNATIVE), not a mathematical
            # necessity.  The reference cannot say whether this is old
            # territory or new, so the add-on waits rather than being treated as
            # novel or as automatically benign.
            dwell_run = 0
            if post_eligibility:
                record(t, ADDON_WITHHOLD_PENDING, False, op,
                       "reference not trusted ("
                       + ", ".join(claim_gate_failures(op))
                       + "); conservative hold (policy choice, not forced)")
        elif op.is_new_territory_claim:
            dwell_run += 1
            if not post_eligibility:
                record(t, ADDON_WITHHOLD_PENDING, False, op,
                       f"acceptance-window claim {dwell_run} "
                       "(before the parent's eligibility bar)")
            elif policy == C2_PTM_GUARD_DWELL and dwell_run < dwell_bars:
                saw_dwell_pending = True
                record(t, ADDON_WITHHOLD_PENDING, False, op,
                       f"dwell {dwell_run}/{dwell_bars} claim bars in the "
                       "acceptance window")
            else:
                reason = (
                    "affirmative new-territory claim on a trusted reference"
                    + (f"; claim held on {dwell_run}/{CONFIRMATION_BARS} "
                       f"acceptance-window bars (o_min={dwell_bars})"
                       if policy == C2_PTM_GUARD_DWELL else "")
                )
                record(t, ADDON_PROMOTE, True, op, reason)
                return _outcome(
                    policy, DISPOSITION_PROMOTED, plan, eligible=eligible,
                    release_bar=t, followup_complete=True,
                    withheld_definite=False,
                    observed_post_eligible_bars=post_eligible_bars(t),
                    open_hold_at_last_bar=False,
                    horizon_bars_required=expiry_bars, final_bar=t,
                    reason=reason, trail=tuple(trail))
        else:
            # Trusted reference, but no claim.
            dwell_run = 0
            if post_eligibility:
                if is_sparse_or_unvisited(op):
                    reason = (
                        "trusted reference with R<=1 and no territory "
                        "objection; PTM abstains and the baseline R0 decision "
                        "stands"
                    )
                    record(t, ADDON_BASELINE_HANDLES, True, op, reason)
                    return _outcome(
                        policy, DISPOSITION_BASELINE_HANDLES, plan,
                        eligible=eligible, release_bar=t,
                        followup_complete=True, withheld_definite=False,
                        observed_post_eligible_bars=post_eligible_bars(t),
                        open_hold_at_last_bar=False,
                        horizon_bars_required=expiry_bars, final_bar=t,
                        reason=reason, trail=tuple(trail))
                record(t, ADDON_WITHHOLD_PENDING, False, op,
                       f"trusted reference but {band_of(op)} (R>=2) cannot "
                       "certify new territory in this episode")
            else:
                record(t, ADDON_WITHHOLD_PENDING, False, op,
                       f"no claim yet in the acceptance window "
                       f"(band={band_of(op)})")

        if post_eligibility and t >= expiry_bar:
            # An indexed endpoint is not evidence that every intervening
            # decision bar was observed. Missing observations are different
            # from present-but-DEGRADED PTM readings; only the latter prove
            # that the conservative hold actually operated on that bar.
            missing = [
                idx for idx in range(eligible, expiry_bar + 1)
                if idx not in by_bar
            ]
            if missing:
                reason = (
                    f"{len(missing)} missing decision-bar observation(s) "
                    f"between eligibility {eligible} and expiry {expiry_bar}; "
                    "the horizon is administratively right-censored, not a "
                    "definite policy withholding"
                )
                record(t, ADDON_OBSERVATION_RIGHT_CENSORED, False, op, reason)
                return _outcome(
                    policy, DISPOSITION_OBSERVATION_RIGHT_CENSORED, plan,
                    eligible=eligible, followup_complete=False,
                    withheld_definite=False,
                    observed_post_eligible_bars=post_eligible_bars(t),
                    open_hold_at_last_bar=True,
                    horizon_bars_required=expiry_bars, final_bar=t,
                    reason=reason, trail=tuple(trail))
            reason = (
                f"policy withheld through the complete decision horizon: the "
                f"episode expired at bar {t} ({expiry_bars} bars after "
                f"eligibility at {eligible}) with no release evidence. This is "
                "a DEFINITE withholding over the declared horizon; the add-on "
                "may still occur later, so its extra delay is not zero and is "
                "not bounded by this horizon"
            )
            if saw_dwell_pending:
                reason += "; C2 dwell was never satisfied"
            record(t, ADDON_WITHHOLD_THROUGH_EXPIRY, False, op, reason)
            return _outcome(
                policy, DISPOSITION_POLICY_WITHHELD_THROUGH_EXPIRY, plan,
                eligible=eligible, followup_complete=True,
                withheld_definite=True,
                observed_post_eligible_bars=post_eligible_bars(t),
                open_hold_at_last_bar=False, horizon_bars_required=expiry_bars,
                final_bar=t, reason=reason, trail=tuple(trail))

    # --- Observations ran out before the decision horizon was complete -----
    # This is the case the earlier revision got wrong.  The add-on's fate is
    # UNKNOWN, not "never happened":
    #   * if the data ends before the eligibility bar, no decision bar was ever
    #     observed, so nothing about PTM's behaviour can be concluded at all;
    #   * if the data ends after it but before expiry, a hold was open and a
    #     future release is simply unobserved.
    # Neither counts as a permanent withholding or a missed earned add-on.
    if last_bar < eligible:
        reason = (
            f"data ends at bar {last_bar} BEFORE the parent's eligibility bar "
            f"{eligible}: no decision bar was ever observed, so the add-on's "
            "fate is unknown (administratively right-censored). This is not a "
            "permanent withholding and not a missed add-on"
        )
    else:
        reason = (
            f"data ends at bar {last_bar}, "
            f"{expiry_bar - last_bar} bar(s) before the decision horizon at "
            f"{expiry_bar}: a hold was still open, so a future release is "
            "unobserved (administratively right-censored). This is not a "
            "permanent withholding and not a missed add-on"
        )
    record(last_bar, ADDON_OBSERVATION_RIGHT_CENSORED, False,
           by_bar.get(last_bar), reason)
    return _outcome(
        policy, DISPOSITION_OBSERVATION_RIGHT_CENSORED, plan, eligible=eligible,
        followup_complete=False, withheld_definite=False,
        observed_post_eligible_bars=post_eligible_bars(last_bar),
        open_hold_at_last_bar=last_bar >= eligible,
        horizon_bars_required=expiry_bars, final_bar=last_bar,
        reason=reason, trail=tuple(trail))


def disposition_counts(outcomes: Sequence[AddOnOutcome]) -> dict:
    """Count every declared disposition, including the zero ones.

    A disposition that never occurs must still appear with a count of 0, so an
    accounting table can never hide a category by omission.
    """
    counts = {d: 0 for d in DECLARED_DISPOSITIONS}
    for o in outcomes:
        if o.disposition not in counts:
            raise AssertionError(
                f"undeclared disposition {o.disposition!r}; every outcome must "
                f"use one of {DECLARED_DISPOSITIONS}")
        counts[o.disposition] += 1
    counts["_total"] = len(outcomes)
    return counts


def parent_eligible_outcomes(outcomes: Sequence[AddOnOutcome]) -> list:
    """Outcomes where the parent actually earned the add-on.

    Only these can carry an add-on opportunity cost; ``PARENT_NOT_ELIGIBLE``
    episodes are excluded so a never-earned add-on is not charged to PTM.
    """
    return [o for o in outcomes
            if o.disposition != DISPOSITION_PARENT_NOT_ELIGIBLE]


def evaluable_outcomes(outcomes: Sequence[AddOnOutcome]) -> list:
    """Parent-eligible outcomes whose decision horizon was fully observed.

    This is the ONLY denominator on which a permanent-withholding rate is
    defined.  Right-censored episodes are excluded because their future is
    unknown, and including them is precisely what produced the earlier
    uninterpretable 14/23 figure.
    """
    return [o for o in parent_eligible_outcomes(outcomes)
            if o.followup_complete]


def withheld_share_of_evaluable(outcomes: Sequence[AddOnOutcome]) -> float | None:
    """Permanent withholding rate over fully observed, parent-eligible episodes.

    Returns ``None`` when nothing is evaluable, so "no evidence yet" stays
    distinct from "0% withheld".
    """
    ev = evaluable_outcomes(outcomes)
    if not ev:
        return None
    return sum(1 for o in ev if o.withheld_definite) / float(len(ev))


def right_censored_share(outcomes: Sequence[AddOnOutcome]) -> float | None:
    """Share of parent-eligible episodes whose follow-up was incomplete."""
    pe = parent_eligible_outcomes(outcomes)
    if not pe:
        return None
    return sum(1 for o in pe
               if o.disposition == DISPOSITION_OBSERVATION_RIGHT_CENSORED
               ) / float(len(pe))


def censored_share(outcomes: Sequence[AddOnOutcome]) -> float:
    """Share of outcomes whose extra delay was not observed.

    Retained for the historical evidence readers.  Reported next to any mean
    delay, because averaging an unobserved delay as if it were zero is exactly
    the error the prereg must not make.
    """
    if not outcomes:
        raise ValueError("no outcomes")
    return sum(1 for o in outcomes if o.censored) / float(len(outcomes))


def mean_observed_delay(outcomes: Sequence[AddOnOutcome]) -> float | None:
    """Mean delay over outcomes whose delay was actually observed (released).

    Returns None when nothing released, making "no data" distinct from "zero".
    """
    vals = [o.extra_delay_bars for o in outcomes
            if not o.censored and o.extra_delay_bars is not None]
    if not vals:
        return None
    return sum(vals) / float(len(vals))


def assert_finite_or_censored(outcome: AddOnOutcome) -> None:
    """Guard used by tests: an unobserved delay must not be reported as a value.

    Also enforces the disposition invariants that keep the accounting honest:
    a definite withholding must have a complete horizon, and a right-censored
    episode must never claim a definite withholding.
    """
    if outcome.censored and outcome.extra_delay_bars is not None:
        raise AssertionError(
            f"unobserved delay on {outcome.disposition} reported "
            f"extra_delay_bars={outcome.extra_delay_bars}"
        )
    if not outcome.censored and outcome.extra_delay_bars is not None:
        if not math.isfinite(float(outcome.extra_delay_bars)):
            raise AssertionError("non-finite delay on an observed outcome")
    if outcome.withheld_definite and not outcome.followup_complete:
        raise AssertionError(
            "withheld_definite requires a complete follow-up horizon; a "
            "truncated observation can never establish a permanent withholding"
        )
    if (outcome.disposition == DISPOSITION_OBSERVATION_RIGHT_CENSORED
            and outcome.followup_complete):
        raise AssertionError(
            "OBSERVATION_RIGHT_CENSORED is contradictory with a complete "
            "horizon"
        )
    if outcome.disposition == DISPOSITION_PROMOTED and outcome.censored:
        raise AssertionError("a promoted add-on must have an observed delay")
