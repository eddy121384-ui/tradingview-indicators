#!/usr/bin/env python3
"""Issue #185 -- C1/C2 add-on (second-entry) exposure policy.

This module is a *policy prototype*, not an indicator.  It decides one thing
only: whether the extra 75% of exposure that the frozen parent model has
already earned ("the add-on") is **released** or **withheld** because of PTM
territory evidence.  It never accelerates a promotion, never reduces exposure,
and never sizes a position.

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

Exactly two challenger policies are defined: ``C1_PTM_GUARD`` and
``C2_PTM_GUARD_DWELL``.  No third policy and no parameter grid belongs here.
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
# Policy identity.  Exactly two challengers; adding a third is out of scope.
# ---------------------------------------------------------------------------
C1_PTM_GUARD = "C1_PTM_GUARD"
C2_PTM_GUARD_DWELL = "C2_PTM_GUARD_DWELL"
CHALLENGER_POLICIES = (C1_PTM_GUARD, C2_PTM_GUARD_DWELL)

# ---------------------------------------------------------------------------
# Dwell horizon for C2 (``o_min``).  Design-derived, NOT outcome-derived.
#
# ``o_min`` counts bars of the PARENT'S OWN acceptance window -- the
# ``CONFIRMATION_BARS`` bars after the breakout, ``b3_break + 1 .. b3_break + 3``
# -- on which the new-territory claim held.  Fixing the window this way is the
# whole point: the parent has already paid for those three bars, so C2
# introduces no new timescale, and the window is fully observed by the time the
# parent's eligibility bar arrives (``P1/P2 is known at t+3`` in issue #78).
#
# Counting dwell only from the eligibility bar was tried first and REJECTED:
# on ``true_trend`` the claim run is exactly the acceptance window, so a
# post-eligibility count left 1 of 3 bars and C2 censored a genuine trend that
# C1 promotes at zero delay.  See the prereg draft.
#
# ``o_min = CONFIRMATION_BARS`` therefore means "the claim held on every bar of
# the acceptance window".  PENDING_SOPHIRA_APPROVAL.
# ---------------------------------------------------------------------------
DWELL_BARS_OMIN = CONFIRMATION_BARS  # 3

#: In-episode expiry, in completed bars after the parent's eligibility bar.
#: Tied to the frozen reference window so the two cannot drift apart.
EPISODE_EXPIRY_BARS = PTMConfig().reference_bars  # 120

# ---------------------------------------------------------------------------
# Outcomes.  ``CENSORED`` is the honest label for "the add-on never happened":
# its extra delay is unbounded, not zero.
# ---------------------------------------------------------------------------
ADDON_PROMOTE = "PROMOTE"
ADDON_WITHHOLD_PENDING = "WITHHOLD_PENDING"
ADDON_WITHHOLD_CENSORED = "WITHHOLD_CENSORED"
#: The "abstain / let the baseline handle it" outcome.
#:
#: PROVABLY UNREACHABLE against the frozen instrument.  Its precondition is
#: ``reference_is_valid(observation) and is_sparse_or_unvisited(observation)
#: and not observation.is_new_territory_claim``.  But ``reference_is_valid``
#: conjoins exactly the non-novelty conjuncts of the frozen claim gate
#: (``validity == OK``, ``coverage >= 1.0``, ``reference_adequacy_ok``,
#: ``scale_stable``, ``not suspect``) and is therefore a SUPERSET of
#: ``FrozenReference.allows_new_territory_claim`` for any value of
#: ``guards_enforced``.  With ``is_sparse_or_unvisited`` supplying
#: ``novelty_fresh``, ``is_new_territory_claim`` must be True, contradicting
#: the precondition.  The branch is kept as an explicit, auditable fallback and
#: is scanned for counterexamples by the analyzer and by
#: ``test_c8_abstain_branch_is_provably_unreachable``; it is never taken.
#:
#: Consequence for the prereg: "abstain" and "conservative hold" are NOT
#: distinct policies on the current instrument, so the choice between them
#: cannot be exercised as a parameter.  Genuine abstain semantics would require
#: weakening this gate below the claim gate -- an instrument change, not a
#: policy setting.
ADDON_BASELINE_HANDLES = "BASELINE_HANDLES"
ADDON_NOT_ELIGIBLE = "NOT_ELIGIBLE"
ADDON_DE_RISK = "DE_RISK_BASELINE"
ADDON_ALREADY_FULL = "ALREADY_FULL"

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
    """The whole-episode result of one challenger policy."""

    policy: str
    status: str
    parent_path: str
    eligible_promotion_bar: int | None
    first_release_signal_bar: int | None
    first_executable_bar: int | None
    #: Bars of extra delay versus the parent's own R0 timing.  ``None`` when
    #: the add-on never happened: the delay is then unbounded (censored), and
    #: reporting 0 here would be false.
    extra_delay_bars: int | None
    censored: bool
    missed_addon: bool
    final_bar: int | None
    reasons: tuple[str, ...] = ()
    trail: tuple[AddOnDecision, ...] = field(default=(), repr=False)

    @property
    def released(self) -> bool:
        return self.status == ADDON_PROMOTE

    def as_row(self) -> dict:
        return {
            "policy": self.policy,
            "status": self.status,
            "parent_path": self.parent_path,
            "eligible_promotion_bar": self.eligible_promotion_bar,
            "first_release_signal_bar": self.first_release_signal_bar,
            "first_executable_bar": self.first_executable_bar,
            "extra_delay_bars": self.extra_delay_bars,
            "extra_delay_bars_is_censored": self.censored,
            "missed_addon": self.missed_addon,
            "final_bar": self.final_bar,
            "reasons": "; ".join(self.reasons),
        }


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

    # --- Case: the parent never earned the add-on at all -------------------
    # The 75% was never going to be added, so PTM withheld nothing.  This must
    # NOT be recorded as a PTM delay; see ``missed_addon``.
    if eligible is None:
        reason = (
            PARENT_PATH_P3
            if plan.path == PARENT_PATH_P3
            else f"parent has no add-on entitlement (path={plan.path})"
        )
        op = by_bar.get(min(by_bar))
        record(last_bar, ADDON_NOT_ELIGIBLE, False, op, reason)
        return AddOnOutcome(
            policy=policy,
            status=ADDON_NOT_ELIGIBLE,
            parent_path=plan.path,
            eligible_promotion_bar=None,
            first_release_signal_bar=None,
            first_executable_bar=None,
            extra_delay_bars=None,
            censored=False,
            missed_addon=False,
            final_bar=last_bar,
            reasons=(reason,),
            trail=tuple(trail),
        )

    # --- Case: exposure was already at full before the decision ------------
    if plan.already_full_at is not None and plan.already_full_at <= eligible:
        reason = (
            f"exposure already full at bar {plan.already_full_at}; PTM has no "
            "effect on an executed add-on and never reduces exposure"
        )
        record(eligible, ADDON_ALREADY_FULL, False, by_bar.get(eligible), reason)
        return AddOnOutcome(
            policy=policy,
            status=ADDON_ALREADY_FULL,
            parent_path=plan.path,
            eligible_promotion_bar=eligible,
            first_release_signal_bar=None,
            first_executable_bar=None,
            extra_delay_bars=0,
            censored=False,
            missed_addon=False,
            final_bar=eligible,
            reasons=(reason,),
            trail=tuple(trail),
        )

    # --- Case: the parent deteriorates before release ----------------------
    # Deterioration invokes the inherited de-risk/exit handling.  It must never
    # be converted into a promotion, and never into "waiting paid off".
    if plan.deteriorated_at is not None and plan.deteriorated_at <= eligible:
        reason = (
            f"parent deteriorated at bar {plan.deteriorated_at} before "
            "release; baseline de-risk/exit handles this and deterioration "
            "never promotes"
        )
        record(eligible, ADDON_DE_RISK, False, by_bar.get(eligible), reason)
        return AddOnOutcome(
            policy=policy,
            status=ADDON_DE_RISK,
            parent_path=plan.path,
            eligible_promotion_bar=eligible,
            first_release_signal_bar=None,
            first_executable_bar=None,
            extra_delay_bars=None,
            censored=True,
            missed_addon=True,
            final_bar=eligible,
            reasons=(reason,),
            trail=tuple(trail),
        )

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
            return AddOnOutcome(
                policy=policy,
                status=ADDON_DE_RISK,
                parent_path=plan.path,
                eligible_promotion_bar=eligible,
                first_release_signal_bar=None,
                first_executable_bar=None,
                extra_delay_bars=None,
                censored=True,
                missed_addon=True,
                final_bar=t,
                reasons=(reason,),
                trail=tuple(trail),
            )

        if op is None:
            # No reading.  An absent observation is never evidence.
            dwell_run = 0
            if post_eligibility:
                record(t, ADDON_WITHHOLD_PENDING, False, None,
                       _absent_observation())
        elif not reference_is_valid(op):
            # DEGRADED / UNKNOWN: conservative hold.  The reference cannot say
            # whether this is old territory or new, so the add-on waits rather
            # than being treated as novel or as automatically benign.
            dwell_run = 0
            if post_eligibility:
                record(t, ADDON_WITHHOLD_PENDING, False, op,
                       "reference not trusted ("
                       + ", ".join(claim_gate_failures(op))
                       + "); conservative hold")
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
                return AddOnOutcome(
                    policy=policy,
                    status=ADDON_PROMOTE,
                    parent_path=plan.path,
                    eligible_promotion_bar=eligible,
                    first_release_signal_bar=t,
                    first_executable_bar=next_executable_bar(t),
                    extra_delay_bars=next_executable_bar(t)
                    - next_executable_bar(eligible),
                    censored=False,
                    missed_addon=False,
                    final_bar=t,
                    reasons=(reason,),
                    trail=tuple(trail),
                )
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
                    return AddOnOutcome(
                        policy=policy,
                        status=ADDON_BASELINE_HANDLES,
                        parent_path=plan.path,
                        eligible_promotion_bar=eligible,
                        first_release_signal_bar=t,
                        first_executable_bar=next_executable_bar(t),
                        extra_delay_bars=next_executable_bar(t)
                        - next_executable_bar(eligible),
                        censored=False,
                        missed_addon=False,
                        final_bar=t,
                        reasons=(reason,),
                        trail=tuple(trail),
                    )
                record(t, ADDON_WITHHOLD_PENDING, False, op,
                       f"trusted reference but {band_of(op)} (R>=2) cannot "
                       "certify new territory in this episode")
            else:
                record(t, ADDON_WITHHOLD_PENDING, False, op,
                       f"no claim yet in the acceptance window "
                       f"(band={band_of(op)})")

        if post_eligibility and t >= expiry_bar:
            reason = (
                f"episode expired at bar {t} ({expiry_bars} bars after "
                f"eligibility at {eligible}) with no release evidence; the "
                "add-on never happened, so its extra delay is unbounded "
                "(censored), not zero"
            )
            if saw_dwell_pending:
                reason += "; C2 dwell was never satisfied"
            record(t, ADDON_WITHHOLD_CENSORED, False, op, reason)
            return AddOnOutcome(
                policy=policy,
                status=ADDON_WITHHOLD_CENSORED,
                parent_path=plan.path,
                eligible_promotion_bar=eligible,
                first_release_signal_bar=None,
                first_executable_bar=None,
                extra_delay_bars=None,
                censored=True,
                missed_addon=True,
                final_bar=t,
                reasons=(reason,),
                trail=tuple(trail),
            )

    # Observations ran out inside the window without release evidence.
    reason = (
        f"no release evidence by the last observed bar {last_bar}; the add-on "
        "never happened and its extra delay is unbounded (censored), not zero"
    )
    record(last_bar, ADDON_WITHHOLD_CENSORED, False, by_bar.get(last_bar), reason)
    return AddOnOutcome(
        policy=policy,
        status=ADDON_WITHHOLD_CENSORED,
        parent_path=plan.path,
        eligible_promotion_bar=eligible,
        first_release_signal_bar=None,
        first_executable_bar=None,
        extra_delay_bars=None,
        censored=True,
        missed_addon=True,
        final_bar=last_bar,
        reasons=(reason,),
        trail=tuple(trail),
    )


def censored_share(outcomes: Sequence[AddOnOutcome]) -> float:
    """Share of outcomes whose extra delay is censored (unbounded).

    Reported next to any mean delay, because averaging a censored quantity as
    if it were zero is exactly the error the prereg must not make.
    """
    if not outcomes:
        raise ValueError("no outcomes")
    return sum(1 for o in outcomes if o.censored) / float(len(outcomes))


def mean_observed_delay(outcomes: Sequence[AddOnOutcome]) -> float | None:
    """Mean delay over outcomes that were actually observed (released).

    Returns None when nothing released, making "no data" distinct from "zero".
    """
    vals = [o.extra_delay_bars for o in outcomes
            if not o.censored and o.extra_delay_bars is not None]
    if not vals:
        return None
    return sum(vals) / float(len(vals))


def assert_finite_or_censored(outcome: AddOnOutcome) -> None:
    """Guard used by tests: a censored outcome must not report a delay."""
    if outcome.censored and outcome.extra_delay_bars is not None:
        raise AssertionError(
            f"censored outcome {outcome.status} reported "
            f"extra_delay_bars={outcome.extra_delay_bars}"
        )
    if not outcome.censored and outcome.extra_delay_bars is not None:
        if not math.isfinite(float(outcome.extra_delay_bars)):
            raise AssertionError("non-finite delay on an uncensored outcome")
