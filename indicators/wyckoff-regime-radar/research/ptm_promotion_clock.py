"""Promotion clock for the frozen #78 exposure ladder (Issue #185, item 4).

Sophira's independent acceptance review (issue comment #6135232216, section 1)
found that ``issue-185-price-territory-integration-interface.md`` Case A/B
conflated two independent clocks: the parent model's *promotion* clock and the
PTM *observation* clock.  The old text said "probe at t0=120 and the benchmark
promotes at t+3=123", which is only correct when the breakout happens to occur
on the probe bar itself.

The frozen parent #78 workflow is:

    new formal Markup/Markdown
      -> 25% probe entered
      -> first usable post-entry B3 breakout
      -> observe the subsequent three completed bars P0..P2
      -> promotion to 100% becomes ELIGIBLE at the close of P2, i.e. B3 + 3

Promotion eligibility is therefore anchored on the **breakout**, not on the
probe.  ``eligible_promotion_t`` is ``B3_break_t + 3`` and equals ``probe_t0 + 3``
only in the coincident case.

SCOPE.  This module models TIMESTAMPS ONLY.  It does not implement, change, or
re-derive any trading rule of the parent model.  ``b3_break_t`` is an input the
parent model supplies, and nothing here decides when a breakout occurs or
whether one is "qualifying".  Nothing here reads market data and nothing here
carries an empirical claim.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Bars observed after the breakout before promotion may be considered (frozen).
CONFIRMATION_BARS = 3

PROMOTION_ELIGIBLE = "ELIGIBLE"
PROMOTION_NO_BREAKOUT = "NO_QUALIFYING_BREAKOUT"
PROMOTION_CONFIRMATION_FAILED = "CONFIRMATION_FAILED"

PTM_EARLIER = "EARLIER"
PTM_SAME_BAR = "SAME_BAR"
PTM_LATER = "LATER"
PTM_NOT_COMPARABLE = "NOT_COMPARABLE"


@dataclass(frozen=True)
class PromotionClock:
    """The six independent timestamps needed to compare PTM with the model.

    Every bar index refers to a **completed** bar.  An index of ``None`` means
    the event does not exist on this path (no qualifying breakout, failed
    confirmation, or no PTM reading), which is deliberately distinct from a
    numeric zero.
    """

    probe_t0: int
    """Bar of the 25% probe opportunity (from the parent model)."""

    b3_break_t: int | None
    """First usable post-entry B3 breakout (supplied by the parent model)."""

    b3_confirmation_t: int | None
    """Close of the third completed bar after the breakout: ``b3_break_t + 3``."""

    eligible_promotion_t: int | None
    """Earliest close at which the parent model's promotion may be satisfied.

    Identical to ``b3_confirmation_t`` under the frozen rule, and NOT
    ``probe_t0 + 3``.
    """

    ptm_observation_t: int | None
    """Close at which the PTM reading is observable (same-close signal)."""

    promotion_next_executable_t: int | None
    """First bar a promoted position could actually be traded: eligible + 1."""

    ptm_next_executable_t: int | None
    """First bar a PTM-conditioned action could actually be taken: obs + 1."""

    next_executable_t: int | None
    """First bar the COMBINED decision could be traded (max of the two above)."""

    probe_to_breakout_bars: int | None
    """``b3_break_t - probe_t0``: how long after the probe the breakout came."""

    probe_plus_three_naive_t: int
    """The timing the OLD integration text wrongly assumed.

    It is ``probe_t0 + confirmation_bars``, which equals the documented
    ``probe_t0 + 3`` exactly under the frozen ``CONFIRMATION_BARS = 3``.  The
    name is kept because the frozen contract is what the published review
    discusses; the parameterisation is stated in
    ``naive_probe_clock_basis`` so a non-default window cannot be misread.
    """

    naive_probe_clock_basis: str
    """Which formula produced ``probe_plus_three_naive_t`` (audit P3)."""

    naive_probe_clock_error_bars: int | None
    """``eligible_promotion_t - probe_plus_three_naive_t``.

    Positive means the old "probe + 3" text promoted too EARLY.  This is the
    size of the documented contract error, kept measurable.
    """

    promotion_status: str
    ptm_vs_eligibility: str
    ptm_extra_delay_bars: int | None
    """PTM's extra delay measured against the REAL eligibility bar.

    Zero whenever PTM evidence exists at or before promotion eligibility, i.e.
    whenever the indicator costs the model nothing.
    """


def build_promotion_clock(
    probe_t0: int,
    b3_break_t: int | None,
    ptm_observation_t: int | None = None,
    confirmation_passed: bool = True,
    confirmation_bars: int = CONFIRMATION_BARS,
) -> PromotionClock:
    """Build the corrected timing contract for one probe/breakout path.

    ``confirmation_passed=False`` models a breakout whose confirmation
    conditions failed: the breakout exists (so the clock can be inspected) but
    promotion never becomes eligible.

    Raises ``ValueError`` when the inputs violate the parent model's ordering
    contract (a breakout before the probe that establishes the position, or a
    non-positive confirmation window).  Those are caller-contract errors, so
    they are rejected rather than silently coerced.
    """
    if int(confirmation_bars) < 1:
        raise ValueError(
            f"confirmation_bars must be >= 1, got {confirmation_bars!r}"
        )
    if b3_break_t is not None and int(b3_break_t) < int(probe_t0):
        raise ValueError(
            f"b3_break_t ({b3_break_t}) precedes probe_t0 ({probe_t0}); the "
            "parent model cannot break out before the position exists"
        )

    probe_t0 = int(probe_t0)
    probe_plus_three = probe_t0 + int(confirmation_bars)

    if b3_break_t is None:
        status = PROMOTION_NO_BREAKOUT
        confirmation_t = None
        eligible_t = None
    elif not confirmation_passed:
        status = PROMOTION_CONFIRMATION_FAILED
        confirmation_t = int(b3_break_t) + int(confirmation_bars)
        eligible_t = None
    else:
        status = PROMOTION_ELIGIBLE
        confirmation_t = int(b3_break_t) + int(confirmation_bars)
        eligible_t = confirmation_t

    promotion_next_exec = None if eligible_t is None else eligible_t + 1
    ptm_next_exec = (
        None if ptm_observation_t is None else int(ptm_observation_t) + 1
    )
    if promotion_next_exec is None or ptm_next_exec is None:
        combined_next_exec = None
    else:
        combined_next_exec = max(promotion_next_exec, ptm_next_exec)

    if eligible_t is None or ptm_observation_t is None:
        vs = PTM_NOT_COMPARABLE
        extra: int | None = None
    else:
        ptm_t = int(ptm_observation_t)
        if ptm_t < eligible_t:
            vs = PTM_EARLIER
            extra = 0
        elif ptm_t == eligible_t:
            vs = PTM_SAME_BAR
            extra = 0
        else:
            vs = PTM_LATER
            extra = ptm_t - eligible_t

    return PromotionClock(
        probe_t0=probe_t0,
        b3_break_t=None if b3_break_t is None else int(b3_break_t),
        b3_confirmation_t=confirmation_t,
        eligible_promotion_t=eligible_t,
        ptm_observation_t=(
            None if ptm_observation_t is None else int(ptm_observation_t)
        ),
        promotion_next_executable_t=promotion_next_exec,
        ptm_next_executable_t=ptm_next_exec,
        next_executable_t=combined_next_exec,
        probe_to_breakout_bars=(
            None if b3_break_t is None else int(b3_break_t) - probe_t0
        ),
        probe_plus_three_naive_t=probe_plus_three,
        naive_probe_clock_basis=(
            f"probe_t0 + confirmation_bars ({probe_t0} + "
            f"{int(confirmation_bars)} = {probe_plus_three})"
        ),
        naive_probe_clock_error_bars=(
            None if eligible_t is None else eligible_t - probe_plus_three
        ),
        promotion_status=status,
        ptm_vs_eligibility=vs,
        ptm_extra_delay_bars=extra,
    )
