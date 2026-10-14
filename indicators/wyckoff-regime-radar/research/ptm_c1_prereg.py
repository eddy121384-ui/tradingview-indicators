"""Issue #185 active C1-only preregistration utilities (NO market outcomes).

This module is deliberately separate from the historical C1/C2 phase-2
engineering artifact generator. The latter's truncated-fixture labels are
NOT an empirical permanent-suppression rate.

All stratification inputs precede the probe. All decisions use the already
frozen parent's B3+3 eligibility and PTM outputs. Nothing reads returns.
"""
from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

from ptm_addon_policy import (
    ADDON_ALREADY_FULL,
    ADDON_DE_RISK,
    ADDON_PROMOTE,
    C1_PTM_GUARD,
    EPISODE_EXPIRY_BARS,
    AddOnOutcome,
    ParentPlan,
    evaluate_addon,
)
from ptm_territory import Bar

ACTIVE_CHALLENGERS = (C1_PTM_GUARD,)  # C2 retained only in the legacy engineering archive.
PARENT_NOT_ELIGIBLE = "PARENT_NOT_ELIGIBLE"
RIGHT_CENSORED = "OBSERVATION_RIGHT_CENSORED"
WITHHELD_THROUGH_EXPIRY = "POLICY_WITHHELD_THROUGH_EXPIRY"
BASELINE_DE_RISK = "BASELINE_DE_RISK_BEFORE_RELEASE"
PROMOTED = "PROMOTED"
ALREADY_FULL = "ALREADY_FULL"

# PREdeclared descriptive geometry bins, never fitted to forward returns.
# Keep the continuous width/ATR value in reports; the bins are secondary.
ATR_WINDOW = 14
NARROW_ATR_UPPER = 4.0
WIDE_ATR_LOWER = 8.0
REFERENCE_BARS = 120


@dataclass(frozen=True)
class C1Disposition:
    status: str
    eligible_bar: int | None
    last_observed_bar: int | None
    expiry_bar: int | None
    completed_full_policy_horizon: bool
    established_policy_missed_addon: bool
    finite_delay_bars: int | None
    original_engineering_status: str


def classify_c1_disposition(
    plan: ParentPlan,
    observations: Sequence,
    result: AddOnOutcome | None = None,
    *,
    expiry_bars: int = EPISODE_EXPIRY_BARS,
) -> C1Disposition:
    """Separate administrative right-censoring from actual policy expiry.

    A fixture ending before eligibility cannot establish a missed add-on.
    Even a post-eligibility hold with <120 fully observed bars has UNKNOWN
    eventual release. Only a complete, unreleased policy horizon is called
    WITHHELD_THROUGH_EXPIRY. This is not a PnL or MFE claim.
    """
    if expiry_bars < 1:
        raise ValueError("expiry_bars must be positive")
    if not observations:
        raise ValueError("observations must be non-empty")
    if result is None:
        result = evaluate_addon(C1_PTM_GUARD, observations, plan, expiry_bars=expiry_bars)
    bars = {o.bar_index for o in observations}
    last = max(bars)
    eligible = plan.eligible_promotion_bar
    expiry = None if eligible is None else eligible + expiry_bars
    full_horizon = bool(
        eligible is not None
        and all(t in bars for t in range(eligible, expiry + 1))
    )
    if eligible is None:
        status = PARENT_NOT_ELIGIBLE
    elif result.status == ADDON_ALREADY_FULL:
        status = ALREADY_FULL
    elif result.status == ADDON_DE_RISK:
        status = BASELINE_DE_RISK
    elif result.status == ADDON_PROMOTE:
        status = PROMOTED
    elif full_horizon:
        status = WITHHELD_THROUGH_EXPIRY
    else:
        status = RIGHT_CENSORED
    return C1Disposition(
        status=status,
        eligible_bar=eligible,
        last_observed_bar=last,
        expiry_bar=expiry,
        completed_full_policy_horizon=full_horizon,
        established_policy_missed_addon=(status == WITHHELD_THROUGH_EXPIRY),
        finite_delay_bars=result.extra_delay_bars if status == PROMOTED else None,
        original_engineering_status=result.status,
    )


@dataclass(frozen=True)
class PreprobeRange:
    regime: str
    width_atr14: float | None
    reference_cycles: float | None
    reference_high_low_width: float | None
    atr14: float | None
    rationale: str


def preprobe_range_state(
    bars: Sequence[Bar],
    probe_bar: int,
    reference_cycles: float | None,
) -> PreprobeRange:
    """No post-probe access: full pre-probe reference, last 14 completed TRs.

    Classifier uses historical HIGH-LOW range / pre-probe ATR14 and independent
    historical reversals. It does not reuse the mathematical identity
    (Q90-Q10)/w=20. A future 'sustained_escape' is an OUTCOME, never a stratum.
    """
    ref = bars[max(0, probe_bar - REFERENCE_BARS):probe_bar]
    if len(ref) != REFERENCE_BARS or probe_bar < ATR_WINDOW + 1:
        return PreprobeRange("UNKNOWN", None, reference_cycles, None, None, "insufficient pre-probe history")
    if any(not b.valid or not all(math.isfinite(v) for v in
                                  (b.open, b.high, b.low, b.close)) or
           b.low > b.high or not b.low <= b.close <= b.high for b in ref):
        return PreprobeRange("UNKNOWN", None, reference_cycles, None, None, "invalid pre-probe OHLC")
    tr = []
    for i in range(probe_bar - ATR_WINDOW, probe_bar):
        b, prev = bars[i], bars[i - 1]
        if not prev.valid or not math.isfinite(prev.close):
            return PreprobeRange("UNKNOWN", None, reference_cycles, None, None, "invalid previous close")
        tr.append(max(b.high - b.low, abs(b.high - prev.close), abs(b.low - prev.close)))
    atr = sum(tr) / ATR_WINDOW
    width = max(b.high for b in ref) - min(b.low for b in ref)
    if not all(math.isfinite(v) for v in (atr, width)) or atr <= 0:
        return PreprobeRange("UNKNOWN", None, reference_cycles, width, atr, "zero/nonfinite ATR or width")
    ratio = width / atr
    if not math.isfinite(ratio):
        return PreprobeRange("UNKNOWN", None, reference_cycles, width, atr, "nonfinite normalized width")
    if ratio < NARROW_ATR_UPPER:
        label = "NARROW"
    elif ratio >= WIDE_ATR_LOWER and reference_cycles is not None and reference_cycles >= 1:
        label = "WIDE_ROTATING"
    elif ratio >= WIDE_ATR_LOWER:
        label = "WIDE_UNCONFIRMED_ROTATION"
    else:
        label = "MIDDLE"
    return PreprobeRange(
        label, ratio, reference_cycles, width, atr,
        "pre-probe high-low width / mean of last 14 completed true ranges; "
        "wide >=8 ATR14 and confirmed historical round trip >=1; "
        "narrow <4 ATR14; middle otherwise",
    )


def synthetic_c1_audit() -> dict:
    """Pre-outcome audit; historical synthetic scenarios, not a market estimate."""
    from analyze_issue185_price_territory import (
        NON_SCENARIO_FIXTURES, parent_plan_for, run_fixture,
    )
    from ptm_territory_fixtures import all_fixtures

    rows = []
    for fx in all_fixtures():
        _, episode = run_fixture(fx)
        plan = parent_plan_for(fx, episode)  # constructed B3, NOT a real #78 event.
        result = evaluate_addon(C1_PTM_GUARD, episode.observations, plan)
        disposition = classify_c1_disposition(plan, episode.observations, result)
        range_state = preprobe_range_state(fx.bars, fx.probe_index,
                                           episode.reference.reference_cycle_count)
        rows.append({
            "fixture": fx.name,
            "scenario_or_instrumentation": (
                "instrumentation" if fx.name in NON_SCENARIO_FIXTURES else "scenario"
            ),
            "range": asdict(range_state),
            "disposition": asdict(disposition),
        })
    counts = {status: sum(1 for r in rows if r["disposition"]["status"] == status)
              for status in (PARENT_NOT_ELIGIBLE, RIGHT_CENSORED,
                             WITHHELD_THROUGH_EXPIRY, BASELINE_DE_RISK,
                             PROMOTED, ALREADY_FULL)}
    return {
        "active_challengers": list(ACTIVE_CHALLENGERS),
        "fixtures": len(rows),
        "disposition_counts": counts,
        "warnings": [
            "NO forward returns/PnL/MFE computed",
            "All B3 timestamps for synthetic fixtures are constructed, not real parent events",
            "Administrative right-censoring does not prove permanent withholding",
            "C2 previous results remain historical engineering evidence, not active prereg",
            "Ex-post sustained_escape is not used to create the ex-ante range buckets",
        ],
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(synthetic_c1_audit(), indent=2, allow_nan=False))
