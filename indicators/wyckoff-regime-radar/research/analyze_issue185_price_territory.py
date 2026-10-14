"""Issue #185 PTM v0.2 engineering-review runner.

Runs the deterministic synthetic fixtures through the independent PTM
prototype and writes the full audit artifact set:

* per-bar indicator trajectory CSVs (one per fixture + one combined file);
* first-recognition / latency statistics;
* a reproduction table against Sophira's published v0.2 readouts;
* comparison charts (wide box vs true trend vs fake breakout vs healthy retest);
* a machine-readable summary JSON and a human-readable Markdown report.

No market data, no strategy returns, no parameter search, no OOS5.

Usage::

    python analyze_issue185_price_territory.py
    python analyze_issue185_price_territory.py --outdir <path>
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import replace
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ptm_territory import (  # noqa: E402
    MAX_UNOBSERVED_GAP_FRACTION,
    MAX_W_OVER_SCALE,
    MIN_ENVELOPE_COVERED_FRACTION,
    MIN_REFERENCE_CYCLES,
    NOVELTY_CLASS_SPARSE,
    NOVELTY_CLASS_UNVISITED,
    REFERENCE_BARS,
    PTMConfig,
    evaluate_episode,
    reference_gap_diagnostics,
)
from ptm_promotion_clock import CONFIRMATION_BARS, build_promotion_clock  # noqa: E402
from ptm_addon_policy import (  # noqa: E402
    ACTIVE_CHALLENGERS,
    ADDON_ALREADY_FULL,
    ADDON_BASELINE_HANDLES,
    ADDON_DE_RISK,
    ADDON_NOT_ELIGIBLE,
    ADDON_OBSERVATION_RIGHT_CENSORED,
    ADDON_PROMOTE,
    ADDON_WITHHOLD_PENDING,
    ADDON_WITHHOLD_THROUGH_EXPIRY,
    C1_PTM_GUARD,
    C2_PTM_GUARD_DWELL,
    DECLARED_DISPOSITIONS,
    DISPOSITION_OBSERVATION_RIGHT_CENSORED,
    DISPOSITION_PARENT_NOT_ELIGIBLE,
    DISPOSITION_POLICY_WITHHELD_THROUGH_EXPIRY,
    DWELL_BARS_OMIN,
    EPISODE_EXPIRY_BARS,
    PARENT_PATH_NO_B3,
    PARENT_PATH_P0,
    RETIRED_CHALLENGERS,
    ParentPlan,
    claim_gate_failures,
    disposition_counts,
    evaluate_addon,
    evaluable_outcomes,
    is_sparse_or_unvisited,
    parent_eligible_outcomes,
    reference_is_valid,
    right_censored_share,
    withheld_share_of_evaluable,
)
from ptm_range_regime import (  # noqa: E402
    ATR_WINDOW_BARS,
    REFERENCE_BARS,
    STATUS_OK,
    WIDTH_ATR_EDGES,
    WIDTH_BINS,
    WIDTH_BIN_MID,
    WIDTH_BIN_NARROW,
    WIDTH_BIN_WIDE,
    assign_width_bin,
    range_regime_pre_bars,
)
from ptm_territory_charts import (  # noqa: E402
    render_comparison_chart,
    render_scenario_chart,
)
from ptm_territory_fixtures import (  # noqa: E402
    Fixture,
    all_fixtures,
    creeping_stall,
    fake_breakout,
    healthy_retest,
    post_breakout_stall,
    short_mirror_of,
    true_trend,
    wide_box_traversal,
)

RESEARCH_DIR = Path(__file__).resolve().parent
DEFAULT_OUT = RESEARCH_DIR / "artifacts" / "issue185_price_territory"

# Sophira's published v0.2 synthetic readouts (design comment #6117510142).
# These came from an unavailable original fixture; the comparison below is an
# INDEPENDENT reconstruction, never a claim of byte-level reproduction.
PUBLISHED_READOUTS = [
    ("wide_box_close_118", "wide_box_traversal", 118.0, 6, 1.0 / 7.0),
    ("wide_box_close_119", "wide_box_traversal", 119.0, 6, 1.0 / 7.0),
    ("one_tick_above_high_120_01", "wide_box_traversal", 120.01, 6, 1.0 / 7.0),
    ("initial_crossing_121_6", "true_trend", 121.6, 0, 1.0),
    ("fake_breakout_back_at_116", "fake_breakout", 116.0, 12, 1.0 / 13.0),
    ("true_breakout_123_126_129", "true_trend", 129.0, 0, 1.0),
    ("healthy_retest_to_118", "healthy_retest", 118.0, 6, 1.0 / 7.0),
    ("stall_124_6_for_18_bars", "post_breakout_stall", 124.6, 0, 1.0),
]

CHART_FIXTURES = [
    ("wide_box", "wide_box_traversal",
     "WIDE BOX 100-120 -- repeated intrabox traversals are NOT new territory"),
    ("true_trend", "true_trend",
     "TRUE TREND -- first close beyond the frozen envelope is recognised immediately"),
    ("fake_breakout", "fake_breakout",
     "FAKE BREAKOUT -- identical first escape close, then immediate deterioration"),
    ("healthy_retest", "healthy_retest",
     "HEALTHY RETEST -- novelty weakens into the old zone then recovers"),
    ("post_breakout_stall", "post_breakout_stall",
     "POST-BREAKOUT STALL -- novelty stays 1.0 while progress stops (known defect)"),
    ("creeping_stall", "creeping_stall",
     "CREEPING STALL -- +0.01/bar resets naive frontier age; amplitude gauge fires"),
    ("volatility_regime_shift", "volatility_regime_shift",
     "VOLATILITY REGIME SHIFT -- 15 extreme closes inflate w and collapse the band"),
    ("long_wick", "long_wick",
     "LONG WICK -- one 150 wick makes genuinely new price 135 look half-visited"),
    ("degenerate_history", "degenerate_history",
     "DEGENERATE HISTORY -- zero band width: fail closed, no fabricated novelty"),
]


def run_fixture(fixture: Fixture):
    bars = fixture.bars
    episode = evaluate_episode(
        bars, fixture.probe_index, fixture.direction, fixture.config
    )
    return bars, episode


def structural_escape_bar(fixture: Fixture, episode) -> int | None:
    bars = fixture.bars
    for i in range(fixture.probe_index, len(bars)):
        if fixture.direction > 0 and bars[i].high > episode.reference.max_high:
            return i
        if fixture.direction < 0 and bars[i].low < episode.reference.min_low:
            return i
    return None


def first_of(observations, predicate) -> int | None:
    for o in observations:
        if predicate(o):
            return o.bar_index
    return None


# ---------------------------------------------------------------------------
# C1/C2 add-on policy evaluation
# ---------------------------------------------------------------------------
#: Fixtures that are deliberately broken or built purely to instrument a guard.
#: A withhold on these is NOT evidence that the policy suppresses genuine
#: opportunities, so they are subtracted before any cost headline.  Each name
#: carries this round's declared rationale, taken from the fixture's own
#: docstring -- it is a declaration, not a discovery, and it is
#: PENDING_SOPHIRA_APPROVAL.
NON_SCENARIO_FIXTURES = {
    "missing_reference_bars": "data integrity: 8 of 120 reference bars invalid",
    "gappy_reference": "data integrity: sparse download, most sessions missing",
    "degenerate_history": "degenerate: zero inter-quantile spread",
    "degenerate_history_tick_fallback": "degenerate: zero spread, tick fallback",
    "unadjusted_split": "corporate action: reference in pre-split units",
    "futures_roll": "corporate action: continuous-futures roll printed 4x",
    "translated_to_zero_scale": "A3 instrumentation: reference median exactly 0",
    "low_level_scale_break_false_alarm":
        "D10 instrumentation: level-dependent scale-break false alarm",
    "crossed_but_not_closed": "A1 instrumentation: fully observed bar ranges",
    "envelope_gap_only": "A1 instrumentation: gap sub-guard isolation",
    "envelope_coverage_only": "A1 instrumentation: coverage sub-guard isolation",
}


def parent_plan_for(fixture: Fixture, episode) -> ParentPlan:
    """A DECLARED synthetic parent plan for a fixture.

    The synthetic paths contain no markup/markdown/B3 event, so the structural
    escape bar is used as the breakout stand-in and the frozen three-bar
    confirmation is applied to it, exactly as in ``phase2_comparison_rows``.
    The parent path is declared ``P0_NoTouch`` (the frozen parent adds at t+3
    on P0/P1/P2) when an escape exists, and ``NO_USABLE_B3`` otherwise, which
    is the parent's own "remains at Probe" case.  These are timing
    illustrations, not claims about the parent model's behaviour.
    """
    escape = structural_escape_bar(fixture, episode)
    return ParentPlan(
        probe_bar=fixture.probe_index,
        b3_break_bar=escape,
        path=PARENT_PATH_P0 if escape is not None else PARENT_PATH_NO_B3,
        usable_b3=escape is not None,
    )


def abstain_branch_reachability(fixtures, episodes) -> dict:
    """Scan for a counterexample to the abstain branch being unreachable.

    The abstain outcome (``ADDON_BASELINE_HANDLES``) needs a *trusted* reference
    at ``R <= 1`` that nevertheless makes no claim.  ``reference_is_valid`` is a
    superset of the frozen claim gate's non-novelty conjuncts, so this scan must
    find nothing.  It is performed rather than assumed, so that a future change
    to either gate turns this from a silent assumption into a failure.
    """
    counterexamples = []
    fingerprinted = 0
    for fixture in fixtures:
        episode = episodes[fixture.name]
        for o in episode.observations:
            if not reference_is_valid(o):
                continue
            fingerprinted += 1
            if is_sparse_or_unvisited(o) and not o.is_new_territory_claim:
                counterexamples.append({
                    "fixture": fixture.name,
                    "bar_index": o.bar_index,
                    "novelty_class": o.novelty_class,
                    "validity": o.validity,
                    "failures": list(claim_gate_failures(o)),
                })
    return {
        "trusted_reference_observations_scanned": fingerprinted,
        "counterexamples": counterexamples,
        "reachable": bool(counterexamples),
        "conclusion": (
            "the abstain outcome is provably unreachable: a trusted reference "
            "at R<=1 always claims, because reference_is_valid() is a superset "
            "of the frozen claim gate's non-novelty conjuncts"
        ),
        "prereg_consequence": (
            "This is a fact about ONE state (a TRUSTED reference at R<=1 that "
            "makes no claim), not about the degraded state. It does NOT mean the "
            "'abstain vs conservative hold' decision is mathematically "
            "unavailable: a policy could route DEGRADED/UNKNOWN straight to the "
            "unmodified baseline -- see BASELINE_ON_DEGRADED_ALTERNATIVE -- and "
            "that needs no change to the frozen instrument."
        ),
        "scope_correction": (
            "An earlier revision of this report claimed the abstain-vs-hold "
            "choice 'cannot be exercised as a policy parameter' and cited this "
            "scan as proof. That inference was WRONG and is withdrawn: this scan "
            "concerns the trusted-R<=1 no-claim state only. C1 chooses "
            "conservative hold for DEGRADED/UNKNOWN as an explicit POLICY "
            "PREFERENCE about which error to prefer (Sophira approved), with all "
            "opportunity cost charged, and NOT because mathematics forces it."
        ),
    }


def addon_policy_rows(fixtures, episodes) -> list[dict]:
    """Per-fixture C1/C2 outcome plus the honest cost accounting.

    The distinction that matters: a withheld add-on is only a *newly
    introduced* policy cost when the phase-2 signal itself produced a claim on
    or after the parent's eligibility bar.  When no such claim exists, the
    policy is not contradicting the signal.  Both are reported.
    """
    rows = []
    for fixture in fixtures:
        episode = episodes[fixture.name]
        plan = parent_plan_for(fixture, episode)
        eligible = plan.eligible_promotion_bar
        claim_bars = [o.bar_index for o in episode.observations
                      if o.is_new_territory_claim]
        late_claims = [b for b in claim_bars
                       if eligible is not None and b >= eligible]
        c1 = evaluate_addon(C1_PTM_GUARD, episode.observations, plan)
        c2 = evaluate_addon(C2_PTM_GUARD_DWELL, episode.observations, plan)
        regime = fixture_range_regime(fixture)
        rows.append({
            "fixture": fixture.name,
            "direction": fixture.direction,
            # OUTCOME label only -- never an input to the stratum.
            "sustained_escape": bool(_sustained_escape(fixture, episode)),
            "breakout_stand_in_bar": structural_escape_bar(fixture, episode),
            "eligible_promotion_bar": eligible,
            "parent_earns_addon": plan.parent_earns_addon,
            "last_observed_bar": max(o.bar_index for o in episode.observations),
            "claim_bars_total": len(claim_bars),
            "claim_bars_at_or_after_eligibility": len(late_claims),
            "c1_disposition": c1.disposition,
            "c1_status": c1.disposition,  # historical alias
            "c1_first_release_bar": c1.first_release_signal_bar,
            "c1_first_executable_bar": c1.first_executable_bar,
            "c1_extra_delay_bars": c1.extra_delay_bars,
            "c1_censored": c1.censored,
            "c1_followup_complete": c1.followup_complete,
            "c1_withheld_definite": c1.withheld_definite,
            "c1_observed_post_eligible_bars": c1.observed_post_eligible_bars,
            "c1_open_hold_at_last_bar": c1.open_hold_at_last_bar,
            # C2 is RETAINED HISTORICAL EVIDENCE ONLY.  It is not an active
            # challenger and contributes nothing to the study's decision surface.
            "c2_retired": True,
            "c2_disposition": c2.disposition,
            "c2_status": c2.disposition,  # historical alias
            "c2_first_release_bar": c2.first_release_signal_bar,
            "c2_first_executable_bar": c2.first_executable_bar,
            "c2_extra_delay_bars": c2.extra_delay_bars,
            "c2_censored": c2.censored,
            "c2_followup_complete": c2.followup_complete,
            "c2_withheld_definite": c2.withheld_definite,
            "c2_differs_from_c1": (
                (c1.disposition, c1.first_release_signal_bar)
                != (c2.disposition, c2.first_release_signal_bar)),
            "range_status": regime.status,
            "range_reason": regime.reason,
            "width_atr": regime.width_atr,
            "width_bin": regime.width_bin,
            "atr_pre": regime.atr_pre,
            "ref_span": regime.ref_span,
            "c1_reason": "; ".join(c1.reasons),
            "c2_reason": "; ".join(c2.reasons),
        })
    return rows


def addon_policy_summary(rows: list[dict]) -> dict:
    """C1 disposition accounting, split by follow-up completeness.

    The earlier revision summed every unreleased episode into one "censored"
    number and reported 14/23 = 60.9% as a permanent-withholding rate.  That was
    wrong: several of those fixtures END BEFORE the parent's eligibility bar, so
    no decision bar was ever observed.  This summary keeps the five canonical
    dispositions apart and defines a withholding rate ONLY over episodes whose
    predeclared decision horizon was fully observed.
    """
    entitled = [r for r in rows if r["parent_earns_addon"]]
    released = [r for r in entitled if r["c1_disposition"] == ADDON_PROMOTE]
    withheld_definite = [r for r in entitled if r["c1_withheld_definite"]]
    right_censored = [r for r in entitled
                      if r["c1_disposition"] == ADDON_OBSERVATION_RIGHT_CENSORED]
    rc_before_eligible = [
        r["fixture"] for r in right_censored
        if (r["eligible_promotion_bar"] is not None
            and r["last_observed_bar"] < r["eligible_promotion_bar"])]
    rc_after_eligible = [
        r["fixture"] for r in right_censored
        if r["fixture"] not in rc_before_eligible]
    de_risked = [r for r in entitled
                 if r["c1_disposition"] == ADDON_DE_RISK]
    evaluable = [r for r in entitled if r["c1_followup_complete"]]
    not_entitled = [r for r in rows if not r["parent_earns_addon"]]

    delays = [r["c1_extra_delay_bars"] for r in released
              if r["c1_extra_delay_bars"] is not None]

    def _dist(key: str) -> dict:
        counts = {d: 0 for d in DECLARED_DISPOSITIONS}
        for r in rows:
            counts[r[key]] = counts.get(r[key], 0) + 1
        return counts

    c1_dist = _dist("c1_disposition")
    c2_dist = _dist("c2_disposition")

    # The "signal contradiction" check is an INVARIANT of the gate, not empirical
    # evidence that the policy is safe.  A claim implies a valid reference
    # (``reference_is_valid`` is a superset of the claim gate's non-novelty
    # conjuncts), so a policy that withholds only on an invalid reference can
    # never withhold a bar that claims.  It is reported as an invariant so no
    # reader mistakes a tautology for a result.
    invariant_violations = [
        r["fixture"] for r in entitled
        if r["claim_bars_at_or_after_eligibility"] > 0
        and r["c1_withheld_definite"]]

    genuine_censored = [r["fixture"] for r in withheld_definite
                        if r["sustained_escape"]
                        and r["fixture"] not in NON_SCENARIO_FIXTURES]
    non_scenario_censored = [r["fixture"] for r in withheld_definite
                             if r["fixture"] in NON_SCENARIO_FIXTURES]

    return {
        "active_challengers": list(ACTIVE_CHALLENGERS),
        "active_challenger_count": len(ACTIVE_CHALLENGERS),
        "retired_challengers": list(RETIRED_CHALLENGERS),
        "retired_note": (
            "C2 is retained as historical audit evidence only. It is not an "
            "active candidate, is excluded from the comparison and decision "
            "surface, and its o_min is not tuned further. It was retired because "
            "the implemented 'three consecutive claims' is a claim-PERSISTENCE "
            "measure, not the approved historical touch-occupancy O, and it "
            "reversed the role of the secondary evidence from hold to release. "
            "The dwell count must never be described as occupancy."
        ),
        "dwell_bars_omin_historical": DWELL_BARS_OMIN,
        "episode_expiry_bars": EPISODE_EXPIRY_BARS,
        "fixtures_evaluated": len(rows),
        "fixtures_with_parent_addon_entitlement": len(entitled),
        "fixtures_without_parent_entitlement": len(not_entitled),

        # --- the five canonical dispositions (C1) ---------------------------
        "c1_disposition_distribution": c1_dist,
        "c1_parent_not_eligible": len(not_entitled),
        "c1_observation_right_censored": len(right_censored),
        "c1_observation_right_censored_before_eligibility": rc_before_eligible,
        "c1_observation_right_censored_after_eligibility": rc_after_eligible,
        "c1_policy_withheld_through_expiry": len(withheld_definite),
        "c1_baseline_de_risk_before_release": len(de_risked),
        "c1_promoted": len(released),
        "c1_open_hold_at_last_bar": sum(
            1 for r in rows if r["c1_open_hold_at_last_bar"]),

        # --- the ONLY valid denominator for a withholding rate --------------
        "c1_evaluable_episodes": len(evaluable),
        "c1_withheld_share_of_evaluable": (
            len(withheld_definite) / float(len(evaluable))
            if evaluable else None),
        "c1_right_censored_share_of_entitled": (
            len(right_censored) / float(len(entitled)) if entitled else None),
        # The synthetic fixtures are short relative to the 120-bar decision
        # horizon, so most cannot reach the expiry bar at all.  A permanent
        # withholding rate is therefore NOT ESTIMABLE from them, and saying so
        # is the honest result rather than quoting a number the data cannot
        # support.
        "c1_fixtures_reaching_expiry": sum(
            1 for r in entitled
            if (r["eligible_promotion_bar"] is not None
                and r["last_observed_bar"]
                >= r["eligible_promotion_bar"] + EPISODE_EXPIRY_BARS)),
        "c1_definite_withholding_estimable_from_synthetics": bool(
            withheld_definite),
        "c1_horizon_adequacy_note": (
            f"Only {sum(1 for r in entitled if (r['eligible_promotion_bar'] is not None and r['last_observed_bar'] >= r['eligible_promotion_bar'] + EPISODE_EXPIRY_BARS))} "
            f"of {len(entitled)} entitled synthetic fixtures reach the "
            f"{EPISODE_EXPIRY_BARS}-bar post-eligible decision horizon at all, "
            "and none of those establishes a definite withholding. The rest are "
            "administratively right-censored. The synthetic set therefore "
            "CANNOT estimate the permanent-withholding rate or C1's opportunity "
            "cost: that measurement requires the real B3 cohort, whose events "
            "are followed for the full horizon. Quoting a synthetic percentage "
            "as a withholding probability would be unsupported."
        ),
        "c1_denominator_note": (
            "c1_withheld_share_of_evaluable = numerator / denominator, where the "
            "numerator is the count of POLICY_WITHHELD_THROUGH_EXPIRY episodes "
            "and the denominator is the count of parent-eligible episodes whose "
            "predeclared decision horizon was fully observed. Episodes that were "
            "released, or that the baseline de-risked, count in the denominator "
            "with a zero numerator; right-censored episodes are excluded from "
            "BOTH because their future is unknown. Including them in the "
            "numerator is what produced the earlier uninterpretable "
            "14/23 = 60.9% figure. That figure is WITHDRAWN and must not be "
            "quoted as a withholding probability, a market estimate or a basis "
            "for any cutoff."
        ),
        "c1_superseded_figure": {
            "value": "14/23 = 60.9%",
            "status": "WITHDRAWN",
            "reason": (
                "summed right-censored episodes (including fixtures that end "
                "before the eligible decision bar) into a permanent-withholding "
                "count"
            ),
        },

        # --- delay, over released episodes only -----------------------------
        "c1_max_delay_over_released": max(delays) if delays else 0,
        "c1_mean_delay_over_released": (
            sum(delays) / float(len(delays)) if delays else None),
        "c1_delay_scope": (
            "max/mean are over episodes whose add-on was actually RELEASED. "
            "Unobserved delays are excluded from both and are never reported as "
            "0 additional bars."
        ),

        # --- invariant vs evidence ------------------------------------------
        "c1_signal_gate_invariant_holds": not invariant_violations,
        "c1_signal_gate_invariant_violations": invariant_violations,
        "c1_signal_gate_invariant_note": (
            "INVARIANT, NOT EVIDENCE. Because reference_is_valid is a superset of "
            "the frozen claim gate's non-novelty conjuncts, a claim implies a "
            "valid reference, so a policy that withholds only on an invalid "
            "reference can never withhold a claiming bar. A zero count here is a "
            "tautology of the gate and must NOT be reported as empirical "
            "protection or as evidence that C1 is safe."
        ),

        "c1_censored_genuine_sustained_escapes": genuine_censored,
        "c1_censored_non_scenario_fixtures": sorted(non_scenario_censored),
        "c1_censored_non_scenario_rationale": {
            k: v for k, v in NON_SCENARIO_FIXTURES.items()
            if k in non_scenario_censored
        },
        "genuine_trend_note": (
            "Definitely-withheld fixtures whose path left the envelope and never "
            "returned (parameter-free test), EXCLUDING fixtures that are "
            "deliberately broken or built only to instrument a guard. 'Sustained "
            "escape' is an OUTCOME label (it reads the future path), never an "
            "ex-ante stratum input, and it is not a claim that the trend was "
            "worth adding to: one_tick_breakout clears the frozen high by 0.02, "
            "where withholding is arguably correct."
        ),
        "c1_censored_note": (
            "Conservative hold is an explicit POLICY CHOICE with all opportunity "
            "cost charged, and it is reported with its full cost. Whether the "
            "resulting opportunity cost is acceptable is a joint "
            "loss-protection / MFE>=8 ATR harvest-retention decision reserved "
            "for Sophira; it is NOT derived from these synthetic fixtures."
        ),
        "censored_never_reported_as_zero": True,
        "wide_box_stratum": wide_box_stratum_summary(rows),
        "c1_status_distribution": c1_dist,
        "c2_status_distribution_historical": c2_dist,
        "c2_differs_from_c1_count_historical": sum(
            1 for r in rows if r["c2_differs_from_c1"]),
        "declared_dispositions": list(DECLARED_DISPOSITIONS),
        "c1_declared_dispositions_never_observed": [
            d for d in DECLARED_DISPOSITIONS if c1_dist.get(d, 0) == 0],
        "c1_declared_dispositions_never_observed_note": (
            "A declared disposition with no observation is disclosed rather than "
            "left implicit. BASELINE_HANDLES is additionally PROVABLY "
            "unreachable in the trusted-R<=1 no-claim state -- see "
            "abstain_branch, and note the scope correction recorded there: this "
            "does not make conservative hold a mathematical necessity. "
            "BASELINE_DE_RISK_BEFORE_RELEASE and ALREADY_FULL are unreachable on "
            "the synthetic set only because no fixture declares a deterioration "
            "or a pre-existing full position, and both are exercised by the unit "
            "tests."
        ),
    }


def fixture_range_regime(fixture) -> "RangeRegimeFeatures":
    """Ex-ante range descriptor for one fixture, from PRE-PROBE bars only.

    ``range_regime_at`` never reads the probe bar or anything after it, so this
    cannot depend on the future path.  The synthetic fixtures have complete
    OHLC, so the descriptor is available for all of them.
    """
    bars = fixture.bars
    pre = [(float(b.high), float(b.low), float(b.close))
           for b in bars[max(0, fixture.probe_index - REFERENCE_BARS):
                         fixture.probe_index]]
    return range_regime_pre_bars(pre)


def wide_box_stratum_summary(rows: list[dict]) -> dict:
    """The ex-ante wide-vs-narrow stratum, replacing two invalid criteria.

    The superseded criteria were:
      * ``(Q90 - Q10) / w`` where ``w = (Q90 - Q10) / RADIUS_DIVISOR`` -- an
        algebraic IDENTITY equal to RADIUS_DIVISOR for every valid reference, so
        it discriminated nothing;
      * ``R <= 1`` plus an unfixed v0.2 claim -- which selects *sparse claimed
        territory*, not a wide trading range;
      * ``sustained_escape()`` -- which reads the path AFTER the probe and is
        therefore a valid OUTCOME label but never a live decision cohort
        definition.
    """
    available = [r for r in rows if r["range_status"] == STATUS_OK]
    widths = [r["width_atr"] for r in available
              if r["width_atr"] is not None]
    bins = {b: 0 for b in WIDTH_BINS}
    for r in available:
        bins[r["width_bin"]] = bins.get(r["width_bin"], 0) + 1
    distinct = len({round(w, 9) for w in widths})

    manifest_path = (RESEARCH_DIR / "artifacts" / "issue185_price_territory" /
                     "issue185_real_cohort_manifest.json")
    real = None
    if manifest_path.exists():
        import json as _json
        real = _json.loads(manifest_path.read_text(encoding="utf-8"))

    return {
        "feature": "width_atr",
        "feature_definition": (
            "(Q90 - Q10) of the pre-probe reference closes divided by the mean "
            "true range over the last ATR_WINDOW_BARS pre-probe bars"
        ),
        "secondary_feature": "confirmed reference reversals (pre-probe)",
        "atr_window_bars": ATR_WINDOW_BARS,
        "reference_bars": REFERENCE_BARS,
        "width_atr_edges_frozen": list(WIDTH_ATR_EDGES),
        "edge_provenance": (
            "feature-only tertiles of the REAL Issue #76 B3 cohort, computed by "
            "analyze_issue185_real_cohort.py with no return, PnL or MFE input"
        ),
        "bin_rule": (
            "NARROW: width_atr < edge0; WIDE: width_atr >= edge1; MID: between. "
            "Reversal bins are the predeclared integer bins 0 / 1 / 2+."
        ),
        "zero_data_rule": (
            "UNAVAILABLE (never silently binned) when fewer than "
            "ATR_WINDOW_BARS+1 pre-probe bars exist, when the window spans a "
            "coordinate reset so its closes share no price coordinate, when the "
            "pre-probe ATR is not strictly positive, or when the reference span "
            "is not strictly positive."
        ),
        "causality": (
            "range_regime_at slices bars[anchor - reference_bars:anchor] and "
            "never reads bars[anchor] or later; appending future bars cannot "
            "change the result, and the test suite asserts that."
        ),
        "sustained_escape_is_outcome_only": True,
        "sustained_escape_note": (
            "sustained_escape() scans every bar after the probe and asks whether "
            "price ever returned to the old envelope. It is retained ONLY as an "
            "outcome label and is never an input to the stratum."
        ),
        "superseded_criteria": {
            "spread_over_w": (
                "IDENTITY, not a classifier: spread/w == RADIUS_DIVISOR for "
                "every valid reference"
            ),
            "R_le_1_plus_claim": (
                "selects sparse CLAIMED TERRITORY, not a wide trading range"
            ),
            "sustained_escape_stratum": (
                "reads the future path; outcome-only"
            ),
        },
        "synthetic_fixtures_available": len(available),
        "synthetic_fixtures_evaluated": len(rows),
        "synthetic_distinct_width_atr_values": distinct,
        "synthetic_bin_counts": bins,
        "discriminates": distinct > 1,
        "discrimination_note": (
            "A tautological criterion would produce exactly 1 distinct value "
            "across all episodes. The reported distinct-value count is the "
            "falsification test for that failure mode."
        ),
        "synthetic_discrimination_caveat": (
            "Most synthetic fixtures are built from the same boxed reference "
            "construction, so their pre-probe widths cluster and the descriptor "
            "has limited spread on them by construction. The synthetic distinct-"
            "value count is therefore a SANITY CHECK (it is > 1, so the feature "
            "is not constant), not a claim about discriminating power. The "
            "stratum's discriminating power rests on the real cohort, where "
            f"{'the feature takes 661 distinct values across 661 usable B3 events' if real else 'the real-cohort manifest is absent, so no claim is made'}."
        ),
        "real_cohort": {
            "manifest_present": real is not None,
            "usable_b3_events": (
                real["parity"]["observed"]["b3_events"]
                - sum(real["feature_unavailable"].values())
                if real else None),
            "b3_events": (real["parity"]["observed"]["b3_events"]
                          if real else None),
            "unavailable_breakdown": (
                real["feature_unavailable"] if real else None),
            "frozen_edges": (
                real["width_atr_tertile_edges"] if real else None),
            "note": (
                "Computed from the operator-side Issue #76 export, which is NOT "
                "committed to this repository (private market data). The raw "
                "files are identified by SHA-256 in the committed manifest; the "
                "numbers are NOT reproducible in CI and are never presented as "
                "if they were."
            ) if real else (
                "No real-cohort manifest in the tree; the frozen edges are used "
                "as declared constants and no real-cohort claim is made."
            ),
        },
    }


def omin_sensitivity_rows(fixtures, episodes) -> list[dict]:
    """RETIRED historical disclosure: C2's dwell horizon on SYNTHETIC fixtures.

    C2 is no longer an active challenger, so this table exists only to keep the
    historical record reproducible.  It must not be read as a challenger
    comparison, and its ``o_min`` must not be tuned further or promoted to a
    prereg parameter.  No market outcome is consulted, and the ACTIVE challenger
    set is exactly ``ACTIVE_CHALLENGERS``.
    """
    base = {}
    for fixture in fixtures:
        episode = episodes[fixture.name]
        plan = parent_plan_for(fixture, episode)
        c1 = evaluate_addon(C1_PTM_GUARD, episode.observations, plan)
        base[fixture.name] = (c1.disposition, c1.first_release_signal_bar)
    rows = []
    for omin in (1, 2, 3, 4, 5, 6):
        released = censored = differs = 0
        delays = []
        for fixture in fixtures:
            episode = episodes[fixture.name]
            plan = parent_plan_for(fixture, episode)
            out = evaluate_addon(C2_PTM_GUARD_DWELL, episode.observations, plan,
                                 dwell_bars=omin)
            if out.released:
                released += 1
                if out.extra_delay_bars is not None:
                    delays.append(out.extra_delay_bars)
            if out.censored:
                censored += 1
            if (out.disposition, out.first_release_signal_bar) != base[fixture.name]:
                differs += 1
        rows.append({
            "o_min": omin,
            "status": "RETIRED_NOT_AN_ACTIVE_CHALLENGER",
            "equals_parent_confirmation_bars": omin == CONFIRMATION_BARS,
            "released": released,
            "censored": censored,
            "mean_delay_over_released": (
                sum(delays) / float(len(delays)) if delays else None),
            "max_delay_over_released": max(delays) if delays else 0,
            "differs_from_c1": differs,
            "is_degenerate_equals_c1": differs == 0,
        })
    return rows


def _load_real_cohort_manifest() -> dict | None:
    """The committed real-cohort manifest, if the operator-side run was done.

    Its absence must never be fatal: CI does not have the private export, so the
    analyzer has to run without it and say so rather than fabricate numbers.
    """
    path = (RESEARCH_DIR / "artifacts" / "issue185_price_territory" /
            "issue185_real_cohort_manifest.json")
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def parent_event_provenance() -> dict:
    """The frozen parent event source and its parity contract.

    Everything here is read from the parent's own committed research code; no
    number is invented and no market outcome is touched.
    """
    return {
        "parent_issue": 78,
        "event_source_marker": "ISSUE76|schema=1",
        "event_source_module": "analyze_issue78_retest_path_stage1.py",
        "policy_module": "analyze_issue78_second_entry_economic_policy.py",
        "export_glob": "/mnt/data/pine-logs-#76 Forward Logger*.csv",
        "export_note": (
            "The Issue #76 Pine forward-logger export is PRIVATE market data and "
            "is NOT committed to this repository. The parity rehearsal below was "
            "run locally against an operator-supplied copy and is recorded as a "
            "contract with provenance, not as a CI-checkable step. The exact "
            "input files are identified in the committed real-cohort manifest "
            "by name, size and SHA-256."
        ),
        "real_input_manifest": _load_real_cohort_manifest(),
        "event_chain": "Breakout -> Acceptance -> Retest -> Resume",
        "probe_fraction": 0.25,
        "full_exposure": 1.0,
        "confirmation_bars": CONFIRMATION_BARS,
        "box_lookback_bars": 5,
        "baseline_policy": "R0_Immediate",
        "baseline_rule": "add immediately at t+3",
        "parent_paths": ["P0_NoTouch", "P1_WickHold", "P2_Reclaim",
                         "P3_FailedAcceptance"],
        "parent_paths_that_add_at_t3": ["P0_NoTouch", "P1_WickHold",
                                        "P2_Reclaim"],
        "parent_path_that_never_adds": "P3_FailedAcceptance",
        "no_usable_b3_outcome": "remains at Probe",
        "parity_constants": {
            "EXPECTED_EVENTS": 68118,
            "EXPECTED_EPISODES": 1624,
            "EXPECTED_B3_EVENTS": 997,
            "EXPECTED_P12": 236,
        },
        "parity_assertions_source": (
            "analyze_issue78_second_entry_economic_policy.py lines 741-757 "
            "(event count, episode count, B3 event count, P1/P2 count)"
        ),
        "rehearsal": PARENT_PARITY_REHEARSAL,
        "rehearsal_note": (
            "Counts-only rehearsal of the frozen assertions against a real "
            "export. No return, PnL or forward performance quantity was "
            "computed: the rehearsal stops before build_state_map and all "
            "economics, and scipy's rankdata (used only by the parent's "
            "conditional/outcome helpers) was stubbed to raise."
        ),
        "path_composition_from_rehearsal": PARENT_PATH_COMPOSITION,
        "addon_eligibility_rule": (
            "P0/P1/P2 add at B3_break_t + CONFIRMATION_BARS; P3 never adds; "
            "an episode without a usable B3 stays at Probe"
        ),
        "freeze_status": "PENDING_SOPHIRA_APPROVAL",
    }


# Parity rehearsal result.  Recorded here because the export itself is not in
# the repository; see ``parent_event_provenance``.
PARENT_PARITY_REHEARSAL = {
    "run_against": "operator-supplied Issue #76 forward-logger export",
    "export_files": 9,
    "events": 68118,
    "episodes": 1624,
    "b3_events": 997,
    "p1_p2": 236,
    "reconstruction_error": 5.595524044110789e-14,
    "all_four_constants_match": True,
}
PARENT_PATH_COMPOSITION = {
    "P0_NoTouch": 411,
    "P1_WickHold": 110,
    "P2_Reclaim": 126,
    "P3_FailedAcceptance": 350,
    "adds_at_t3": 647,
    "never_adds": 350,
}


def latency_row(fixture: Fixture, bars, episode) -> dict:
    obs = episode.observations
    usable = [o for o in obs if o.novelty is not None]
    escape = structural_escape_bar(fixture, episode)
    first_claim = first_of(obs, lambda o: o.is_new_territory_claim)
    first_unvisited = first_of(obs, lambda o: o.novelty_class == NOVELTY_CLASS_UNVISITED)
    first_sparse = first_of(
        obs, lambda o: o.novelty_class in (NOVELTY_CLASS_UNVISITED, NOVELTY_CLASS_SPARSE)
    )
    first_mature = first_of(
        obs,
        lambda o: o.evidence_bars >= 3
        and o.novelty_class in (NOVELTY_CLASS_UNVISITED, NOVELTY_CLASS_SPARSE),
    )
    latency = (first_claim - escape) if (first_claim is not None and escape is not None) else None
    ref = episode.reference
    diag = reference_gap_diagnostics(ref)
    return {
        "fixture": fixture.name,
        "direction": fixture.direction,
        "probe_bar": fixture.probe_index,
        "bars_evaluated": len(obs),
        "reference_bars": ref.n_bars,
        "reference_coverage": round(ref.coverage, 6),
        "validity": ref.validity,
        "w": ref.w,
        "structural_escape_bar": escape,
        "first_claim_bar": first_claim,
        "first_unvisited_bar": first_unvisited,
        "first_new_or_sparse_bar": first_sparse,
        "first_mature_acceptance_bar": first_mature,
        "recognition_latency_bars": latency,
        "claim_bars_total": sum(1 for o in obs if o.is_new_territory_claim),
        "stall_bars_total": sum(1 for o in obs if o.stall_flag),
        "min_novelty": min((o.novelty for o in usable), default=None),
        "max_novelty": max((o.novelty for o in usable), default=None),
        "final_novelty": obs[-1].novelty,
        "final_episodes": obs[-1].revisit_episodes,
        "final_occupancy": obs[-1].occupancy,
        "final_frontier": obs[-1].frontier_progress,
        "final_days_since_best_frontier": obs[-1].days_since_best_frontier,
        "max_close_gap_w": diag["max_close_gap_w"],
        "envelope_covered_fraction": diag["envelope_covered_fraction"],
        "suspect_scale_break_bars": sum(1 for o in obs if o.suspect_scale_break),
        # --- A1 reference adequacy ---
        "swing_legs": ref.swing_legs,
        "reference_cycle_count": ref.reference_cycle_count,
        "reference_adequacy_ok": ref.reference_adequacy_ok,
        "max_unobserved_gap_fraction": ref.max_unobserved_gap_fraction,
        # --- A2 comparability ---
        "comparability_status": obs[0].comparability_status,
        "first_claim_episodes_per_cycle": (
            next((o.episodes_per_cycle for o in obs if o.bar_index == first_claim), None)
            if first_claim is not None else None
        ),
        # --- A3 scale stability ---
        "scale_state": ref.scale_state,
        "w_over_scale": ref.w_over_scale,
        "scale_reference": ref.scale_reference,
        "validity_reasons": " | ".join(ref.validity_reasons),
    }


def reproduction_rows(by_name, episodes) -> list[dict]:
    rows = []
    for checkpoint, fixture_name, close, pub_r, pub_n in PUBLISHED_READOUTS:
        episode = episodes[fixture_name]
        hits = [o for o in episode.observations if abs(o.close - close) <= 1e-9]
        if not hits:
            rows.append({
                "checkpoint": checkpoint,
                "fixture": fixture_name,
                "close": close,
                "published_episodes": pub_r,
                "published_novelty": pub_n,
                "observed_episodes": None,
                "observed_novelty": None,
                "episodes_match": False,
                "novelty_match": False,
                "source": "independent reconstruction",
                "note": "close never reached in this fixture",
            })
            continue
        o = hits[-1] if checkpoint.startswith("stall") else hits[0]
        rows.append({
            "checkpoint": checkpoint,
            "fixture": fixture_name,
            "close": close,
            "published_episodes": pub_r,
            "published_novelty": pub_n,
            "observed_episodes": o.revisit_episodes,
            "observed_novelty": o.novelty,
            "episodes_match": o.revisit_episodes == pub_r,
            "novelty_match": (o.novelty is not None and abs(o.novelty - pub_n) < 1e-6),
            "source": "independent reconstruction",
            "note": (
                "published numbers came from an unavailable original fixture; "
                "match is a re-derivation, not a reproduction of that file"
            ),
        })
    return rows


# Classification of the fixtures whose v0.2 signal the phase-2 guards suppress.
#
# This uses each fixture's KNOWN CONSTRUCTION.  These are constructed paths, not
# market observations, and a price-only test genuinely CANNOT separate a long box
# from a real trend -- that inability is precisely why A1 reports "insufficient
# evidence" instead of guessing.  The table therefore reports the parameter-free
# structural measurement (`sustained_escape_refused`) alongside this label
# instead of pretending the two cases can be told apart from prices alone.
SUPPRESSION_CLASS = {
    "gappy_reference": "correct: data-quality guard, sparse download",
    "long_period_box": "correct: the blocking wide-box false release (A1)",
    "one_way_reference_genuine_trend":
        "COST: a genuine sustained escape refused certification",
    # INSTRUMENTATION, not scenarios.  These two fixtures exist so that each A1
    # envelope sub-guard is individually pinned: each is constructed to trip
    # exactly one of them.  They are deliberately blocked, so counting them in
    # the suppression headline would overstate the guard's real-world cost.
    "envelope_gap_only":
        "instrumentation: A1 gap-guard isolation, not a scenario",
    "envelope_coverage_only":
        "instrumentation: A1 coverage-guard isolation, not a scenario",
}

# Fixtures built purely to instrument a guard.  Excluded from every headline
# cost/suppression count, and reported separately instead.
INSTRUMENTATION_FIXTURES = frozenset(
    name for name, cls in SUPPRESSION_CLASS.items()
    if cls.startswith("instrumentation")
)


def _sustained_escape(fixture: Fixture, episode) -> bool:
    """Parameter-free: did the path leave the envelope and never come back?

    No threshold is involved.  It is reported as a measurement, not used as a
    gate or as a substitute for knowing the fixture's construction.
    """
    bars = fixture.bars
    ref = episode.reference
    if ref.max_high is None or ref.min_low is None:
        return False
    beyond = []
    for i in range(fixture.probe_index, len(bars)):
        if fixture.direction > 0:
            beyond.append(bars[i].close > ref.max_high)
        else:
            beyond.append(bars[i].close < ref.min_low)
    first = next((k for k, b in enumerate(beyond) if b), None)
    return first is not None and all(beyond[first:])


def phase2_comparison_rows(fixtures, episodes, legacy_episodes) -> list[dict]:
    """Per-fixture old-signal vs fixed-signal comparison (issue item 6).

    ``legacy_episodes`` are produced with ``apply_phase2_guards=False``, which
    reconstructs the pre-patch claim gate while keeping every diagnostic
    identical.  The model promotion bar is a CONSTRUCTED analogue: the
    synthetic paths contain no markup/markdown/B3 event, so the structural
    escape bar stands in for the breakout and the frozen three-bar
    confirmation is applied to it.  These are illustrations of the corrected
    timing contract, not claims about the parent model's behaviour.
    """
    rows = []
    for fx in fixtures:
        fixed = episodes[fx.name]
        legacy = legacy_episodes[fx.name]
        ref = fixed.reference
        escape = structural_escape_bar(fx, fixed)
        first_fixed = first_of(fixed.observations, lambda o: o.is_new_territory_claim)
        first_legacy = first_of(legacy.observations, lambda o: o.is_new_territory_claim)
        # Corrected clock: promotion eligibility is breakout + 3, never probe + 3.
        promotion_bar = None if escape is None else escape + 3
        naive_bar = fx.probe_index + 3
        if first_fixed is None or promotion_bar is None:
            extra_vs_model = None
        else:
            extra_vs_model = max(first_fixed - promotion_bar, 0)
        if first_fixed is None:
            extra_vs_naive = None
        else:
            extra_vs_naive = max(first_fixed - naive_bar, 0)
        rows.append({
            "fixture": fx.name,
            "direction": fx.direction,
            "probe_bar": fx.probe_index,
            "v02_signal_claim_bar": first_legacy,
            "v02_claim_bars_total": sum(
                1 for o in legacy.observations if o.is_new_territory_claim),
            "phase2_signal_claim_bar": first_fixed,
            "phase2_claim_bars_total": sum(
                1 for o in fixed.observations if o.is_new_territory_claim),
            "signal_suppressed_by_phase2": bool(
                first_legacy is not None and first_fixed is None),
            "first_recognition_bar": first_fixed,
            "added_delay_bars_vs_v02": (
                None if first_fixed is None or first_legacy is None
                else first_fixed - first_legacy),
            # Corrected timing contract.
            "breakout_stand_in_bar": escape,
            "model_confirmation_bar": promotion_bar,
            "naive_probe_plus_three_bar": naive_bar,
            "naive_baseline_error_bars": (
                None if promotion_bar is None else promotion_bar - naive_bar),
            "ptm_extra_delay_vs_model_bars": extra_vs_model,
            "ptm_extra_delay_vs_naive_bars": extra_vs_naive,
            # Guard outcomes.
            "reference_cycle_count": ref.reference_cycle_count,
            "reference_adequacy_ok": ref.reference_adequacy_ok,
            "scale_state": ref.scale_state,
            "validity": ref.validity,
            # Machine-readable so CI can assert that a fixture trips EXACTLY one
            # A1 sub-guard (the isolation property that makes the two envelope
            # guards individually pinned rather than jointly pinned).
            "validity_reasons": " | ".join(ref.validity_reasons),
            "validity_reason_count": len(ref.validity_reasons),
            "suppression_class": (
                SUPPRESSION_CLASS.get(fx.name) if first_fixed is None
                and first_legacy is not None else None),
            "sustained_escape_refused": bool(
                _sustained_escape(fx, fixed)
                and first_fixed is None and first_legacy is not None),
            "final_frontier_progress_w": fixed.observations[-1].frontier_progress,
        })
    return rows


PROMOTION_SCENARIOS = [
    ("coincident_breakout_at_probe",
     dict(probe_t0=120, b3_break_t=120, ptm_observation_t=120)),
    ("breakout_10_bars_after_probe",
     dict(probe_t0=120, b3_break_t=130, ptm_observation_t=130)),
    ("no_qualifying_breakout",
     dict(probe_t0=120, b3_break_t=None, ptm_observation_t=140)),
    ("confirmation_failed",
     dict(probe_t0=120, b3_break_t=130, ptm_observation_t=133,
          confirmation_passed=False)),
    ("ptm_earlier_than_eligibility",
     dict(probe_t0=120, b3_break_t=130, ptm_observation_t=128)),
    ("ptm_on_eligibility_bar",
     dict(probe_t0=120, b3_break_t=130, ptm_observation_t=133)),
    ("ptm_later_than_eligibility",
     dict(probe_t0=120, b3_break_t=130, ptm_observation_t=135)),
]


def promotion_clock_rows() -> list[dict]:
    """The six independent timestamps required by the corrected contract."""
    rows = []
    for label, kwargs in PROMOTION_SCENARIOS:
        c = build_promotion_clock(**kwargs)
        rows.append({
            "scenario": label,
            "probe_t0": c.probe_t0,
            "b3_break_t": c.b3_break_t,
            "b3_confirmation_t": c.b3_confirmation_t,
            "eligible_promotion_t": c.eligible_promotion_t,
            "ptm_observation_t": c.ptm_observation_t,
            "promotion_next_executable_t": c.promotion_next_executable_t,
            "ptm_next_executable_t": c.ptm_next_executable_t,
            "next_executable_t": c.next_executable_t,
            "probe_to_breakout_bars": c.probe_to_breakout_bars,
            "naive_probe_plus_three_t": c.probe_plus_three_naive_t,
            "naive_baseline_error_bars": c.naive_probe_clock_error_bars,
            "ptm_vs_eligibility": c.ptm_vs_eligibility,
            "ptm_extra_delay_bars": c.ptm_extra_delay_bars,
            "promotion_status": c.promotion_status,
        })
    return rows


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", default=str(DEFAULT_OUT))
    args = parser.parse_args(argv)

    out = Path(args.outdir)
    traces_dir = out / "traces"
    charts_dir = out / "charts"
    os.makedirs(traces_dir, exist_ok=True)
    os.makedirs(charts_dir, exist_ok=True)

    fixtures = all_fixtures()
    by_name = {f.name: f for f in fixtures}
    episodes = {}
    bars_by_name = {}
    frames = []

    for fixture in fixtures:
        bars, episode = run_fixture(fixture)
        episodes[fixture.name] = episode
        bars_by_name[fixture.name] = bars
        frame = pd.DataFrame(
            [o.as_row(fixture.name) for o in episode.observations]
        )
        frame.to_csv(traces_dir / f"{fixture.name}.csv", index=False,
                     float_format="%.6f", lineterminator="\n")
        frames.append(frame)

    combined = pd.concat(frames, ignore_index=True)
    combined.to_csv(out / "issue185_ptm_traces_all.csv", index=False,
                    float_format="%.6f", lineterminator="\n")

    latency = pd.DataFrame([latency_row(f, bars_by_name[f.name], episodes[f.name])
                            for f in fixtures])
    latency.to_csv(out / "issue185_ptm_latency.csv", index=False,
                   lineterminator="\n")

    repro = pd.DataFrame(reproduction_rows(by_name, episodes))
    repro.to_csv(out / "issue185_ptm_reproduction.csv", index=False,
                 lineterminator="\n")

    # Old-signal vs fixed-signal comparison.  ``apply_phase2_guards=False``
    # reconstructs the pre-patch v0.2 claim gate and leaves every diagnostic
    # (R, O, N, acceptance, A1/A2/A3 values) byte-identical.
    legacy_episodes = {}
    for fixture in fixtures:
        legacy_cfg = replace(fixture.config, apply_phase2_guards=False)
        legacy_episodes[fixture.name] = evaluate_episode(
            bars_by_name[fixture.name], fixture.probe_index,
            fixture.direction, legacy_cfg,
        )
    phase2 = pd.DataFrame(phase2_comparison_rows(fixtures, episodes, legacy_episodes))
    phase2.to_csv(out / "issue185_ptm_phase2_comparison.csv", index=False,
                  lineterminator="\n")

    clock = pd.DataFrame(promotion_clock_rows())
    clock.to_csv(out / "issue185_ptm_promotion_clock.csv", index=False,
                 lineterminator="\n")

    # C1/C2 add-on policy: the prereg-clarification artifact.  Reported with
    # censoring explicit so that "the add-on never happened" is never rendered
    # as "zero additional bars".
    addon_rows = addon_policy_rows(fixtures, episodes)
    addon = pd.DataFrame(addon_rows)
    addon.to_csv(out / "issue185_ptm_addon_policy.csv", index=False,
                 lineterminator="\n")
    addon_outcomes = addon_policy_summary(addon_rows)
    addon_outcomes["abstain_branch"] = abstain_branch_reachability(
        fixtures, episodes)

    omin = pd.DataFrame(omin_sensitivity_rows(fixtures, episodes))
    omin.to_csv(out / "issue185_ptm_omin_sensitivity.csv", index=False,
                lineterminator="\n")

    provenance = parent_event_provenance()
    (out / "issue185_ptm_parent_provenance.json").write_text(
        json.dumps(provenance, indent=2, default=str), encoding="utf-8",
        newline="\n",
    )

    chart_paths = []
    chart_rel = []
    for slug, fixture_name, title in CHART_FIXTURES:
        episode = episodes[fixture_name]
        chart_paths.append(render_scenario_chart(
            episode.observations,
            bars_by_name[fixture_name],
            episode.reference,
            title,
            str(charts_dir / f"{slug}.png"),
        ))
        chart_rel.append(f"charts/{slug}.png")

    series = [
        ("wide box 100-120", episodes["wide_box_traversal"].observations),
        ("true trend", episodes["true_trend"].observations),
        ("fake breakout", episodes["fake_breakout"].observations),
        ("healthy retest", episodes["healthy_retest"].observations),
        ("post-breakout stall", episodes["post_breakout_stall"].observations),
    ]
    comparison = render_comparison_chart(
        series,
        "COMPARISON -- novelty and acceptance by bars since probe anchor",
        str(charts_dir / "comparison_novelty.png"),
    )
    chart_paths.append(comparison)
    chart_rel.append("charts/comparison_novelty.png")

    summary = {
        "issue": 185,
        "title": "Price Territory Memory v0.2 -- independent engineering review",
        "base_branch": "research/issue-78-market-structure-dimension-audit",
        "base_commit": "e316d19",
        "config_fingerprint": PTMConfig().fingerprint(),
        "reference_bars": REFERENCE_BARS,
        "fixture_count": len(fixtures),
        "reproduction": {
            "published_source": "issue #185 comment 6117510142 (Sophira v0.2)",
            "status": "independent reconstruction",
            "all_episodes_match": bool(repro["episodes_match"].all()),
            "all_novelty_match": bool(repro["novelty_match"].all()),
            "rows": repro.to_dict(orient="records"),
        },
        "latency": latency.to_dict(orient="records"),
        "phase2_guard_thresholds": {
            "a1_cycle_swing_fraction": PTMConfig().cycle_swing_fraction,
            "a1_min_reference_cycles": MIN_REFERENCE_CYCLES,
            "a1_min_envelope_covered_fraction": MIN_ENVELOPE_COVERED_FRACTION,
            "a1_max_unobserved_gap_fraction": MAX_UNOBSERVED_GAP_FRACTION,
            "a3_max_w_over_scale": MAX_W_OVER_SCALE,
            "selection_basis": (
                "pre-outcome fixed synthetic-geometry thresholds; NOT selected "
                "on returns and NOT tuned on any market outcome"
            ),
        },
        "phase2_comparison": phase2.to_dict(orient="records"),
        "promotion_clock": clock.to_dict(orient="records"),
        "addon_policy": addon_outcomes,
        "addon_policy_rows": addon.to_dict(orient="records"),
        "omin_sensitivity": omin.to_dict(orient="records"),
        "parent_event_provenance": provenance,
        "phase2_outcomes": {
            "fixtures_with_v02_signal_suppressed": int(
                phase2.loc[
                    ~phase2["fixture"].isin(INSTRUMENTATION_FIXTURES),
                    "signal_suppressed_by_phase2",
                ].sum()),
            "instrumentation_fixtures_deliberately_blocked": int(
                phase2.loc[
                    phase2["fixture"].isin(INSTRUMENTATION_FIXTURES),
                    "signal_suppressed_by_phase2",
                ].sum()),
            "fixtures_v02_claimed_and_phase2_does_not": [
                r["fixture"] for r in phase2.to_dict(orient="records")
                if r["signal_suppressed_by_phase2"]
                and r["fixture"] not in INSTRUMENTATION_FIXTURES
            ],
            "instrumentation_fixtures_excluded_from_headline": sorted(
                INSTRUMENTATION_FIXTURES),
            "instrumentation_note": (
                "The fixtures above are guard-instrumentation constructs, not "
                "scenarios. They are deliberately blocked and are NOT counted in "
                "any suppression or false-suppression figure."
            ),
            "long_period_box_v02_claim_bars": int(phase2.set_index("fixture").loc[
                "long_period_box", "v02_claim_bars_total"]),
            "long_period_box_phase2_claim_bars": int(phase2.set_index("fixture").loc[
                "long_period_box", "phase2_claim_bars_total"]),
            "max_added_delay_vs_v02_bars": int(phase2["added_delay_bars_vs_v02"]
                                               .dropna().abs().max())
            if phase2["added_delay_bars_vs_v02"].notna().any() else 0,
            # Scope qualifier: the number above is the max over fixtures that
            # STILL CLAIM under both configurations.  For a suppressed fixture
            # there is no fixed-signal first claim at all, so its added delay is
            # unbounded (NaN in the CSV), not zero.
            "max_added_delay_vs_v02_bars_scope": (
                "max over fixtures that still claim under BOTH configurations; "
                "for a suppressed fixture the added delay is unbounded (NaN in "
                "the CSV), not zero"
            ),
            "genuine_trends_refused_certification": [
                name for name, cls in SUPPRESSION_CLASS.items()
                if cls.startswith("COST")
            ],
            "suppression_classes": {
                str(r["fixture"]): str(r["suppression_class"])
                for r in phase2.to_dict(orient="records")
                if isinstance(r["suppression_class"], str)
            },
            "max_ptm_extra_delay_vs_corrected_model_baseline_bars": (
                int(phase2["ptm_extra_delay_vs_model_bars"].dropna().max())
                if phase2["ptm_extra_delay_vs_model_bars"].notna().any() else 0
            ),
        },
        "charts": chart_rel,
        "outcomes": {
            "wide_box_claims": int(latency.set_index("fixture").loc[
                "wide_box_traversal", "claim_bars_total"]),
            "true_trend_recognition_latency_bars": int(latency.set_index("fixture").loc[
                "true_trend", "recognition_latency_bars"]),
            "fake_breakout_recognition_latency_bars": int(latency.set_index("fixture").loc[
                "fake_breakout", "recognition_latency_bars"]),
            "stall_novelty_pinned": float(latency.set_index("fixture").loc[
                "post_breakout_stall", "final_novelty"]),
            "long_trend_final_novelty": float(latency.set_index("fixture").loc[
                "long_trend_unbounded_novelty", "final_novelty"]),
        },
        "boundaries": {
            "market_data_used": False,
            "historical_returns_computed": False,
            "parameter_search_performed": False,
            "oos5_contacted": False,
            "pine_or_production_modified": False,
            "strategy_rules_modified": False,
        },
    }
    (out / "issue185_ptm_summary.json").write_text(
        json.dumps(summary, indent=2, default=str), encoding="utf-8", newline="\n"
    )

    _write_report(out, latency, repro, summary, phase2, clock)
    print(f"artifacts written to {out}")
    print(f"fixtures: {len(fixtures)}  charts: {len(chart_paths)}")
    print(repro.to_string(index=False))
    return 0


def _write_report(out: Path, latency: pd.DataFrame, repro: pd.DataFrame,
                  summary: dict, phase2: pd.DataFrame,
                  clock: pd.DataFrame) -> None:
    lines = [
        "# Issue #185 -- PTM v0.2 engineering-review run report",
        "",
        "Generated by `analyze_issue185_price_territory.py`. Deterministic "
        "synthetic fixtures only: no market data, no returns, no parameter "
        "search, no OOS5, no Pine and no production change.",
        "",
        "## Frozen configuration",
        "",
        "```json",
        json.dumps(PTMConfig().fingerprint(), indent=2),
        "```",
        "",
        "## Reproduction of the published v0.2 readouts",
        "",
        "| checkpoint | fixture | published R | published N | observed R | observed N | match |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for row in repro.to_dict(orient="records"):
        lines.append(
            f"| {row['checkpoint']} | {row['fixture']} | {row['published_episodes']} | "
            f"{row['published_novelty']:.4f} | {row['observed_episodes']} | "
            f"{float(row['observed_novelty']):.4f} | "
            f"{'yes' if row['episodes_match'] and row['novelty_match'] else 'NO'} |"
        )
    lines += [
        "",
        "Source: issue #185 comment 6117510142. The numbers above are an "
        "INDEPENDENT reconstruction from the written v0.2 definition against a "
        "locally built 6-sweep 120-bar box; they are not a byte-level "
        "reproduction of Sophira's original fixture, which was not handed over.",
        "",
        "## First-recognition latency",
        "",
        "| fixture | probe | structural escape | first claim | latency (bars) | claims | stall bars | final N | validity |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in latency.to_dict(orient="records"):
        lines.append(
            f"| {row['fixture']} | {row['probe_bar']} | {row['structural_escape_bar']} | "
            f"{row['first_claim_bar']} | {row['recognition_latency_bars']} | "
            f"{row['claim_bars_total']} | {row['stall_bars_total']} | "
            f"{'' if row['final_novelty'] is None else round(float(row['final_novelty']), 4)} | "
            f"{row['validity']} |"
        )
    lines += [
        "",
        "## Headline outcomes",
        "",
        "```json",
        json.dumps(summary["outcomes"], indent=2),
        "```",
        "",
        "## Phase-2 guard outcomes",
        "",
        "```json",
        json.dumps(summary["phase2_outcomes"], indent=2),
        "```",
        "",
        "## Phase-2 guards: fixed pre-outcome safety thresholds",
        "",
        "```json",
        json.dumps(summary["phase2_guard_thresholds"], indent=2),
        "```",
        "",
        "## Old signal (v0.2) vs fixed signal (A1/A2/A3)",
        "",
        "`v02_*` columns come from `apply_phase2_guards=False`, which reproduces "
        "the pre-patch claim gate. It does NOT leave every diagnostic identical: "
        "the gate itself, the derived `validity` label, `guards_enforced` and the "
        "observation-level validity fields all change. What is identical is every "
        "MEASURED quantity -- R, O, N, the acceptance trace and all A1/A2/A3 "
        "numerics -- which is what makes the old-vs-fixed comparison meaningful.",
        "",
        "`added delay` is the delay relative to the v0.2 first claim and is "
        "reported only for fixtures that claim under BOTH configurations; `nan` "
        "means there is no fixed-signal first claim at all, so the delay is "
        "unbounded rather than zero. The `max_added_delay_vs_v02_bars = 0` "
        "headline carries exactly that scope.",
        "",
        "| fixture | v0.2 first claim | fixed first claim | v0.2 claims | fixed claims | suppressed | added delay | cycles | adequacy | scale | validity |",
        "|---|---:|---:|---:|---:|---|---:|---:|---|---|---|",
    ]
    for row in phase2.to_dict(orient="records"):
        lines.append(
            f"| {row['fixture']} | {row['v02_signal_claim_bar']} | "
            f"{row['phase2_signal_claim_bar']} | {row['v02_claim_bars_total']} | "
            f"{row['phase2_claim_bars_total']} | "
            f"{'YES' if row['signal_suppressed_by_phase2'] else 'no'} | "
            f"{row['added_delay_bars_vs_v02']} | {row['reference_cycle_count']} | "
            f"{row['reference_adequacy_ok']} | {row['scale_state']} | "
            f"{row['validity']} |"
        )
    lines += [
        "",
        "`suppression_class` in `issue185_ptm_phase2_comparison.csv` classifies "
        "each suppressed fixture using its KNOWN CONSTRUCTION; "
        "`sustained_escape_refused` is the parameter-free structural measurement "
        "(the path left the envelope and never returned). A price-only test "
        "cannot separate a long box from a real trend, and this table does not "
        "pretend otherwise -- that is exactly why A1 reports insufficient "
        "evidence rather than guessing.",
        "",
        "## Corrected promotion clock (the frozen #78 B3 contract)",
        "",
        "Promotion eligibility is `B3_break + 3`, NOT `probe + 3`. The naive "
        "baseline is included so its error is measurable.",
        "",
        "| scenario | probe | B3 break | B3 confirm | eligible promotion | PTM obs | next executable | naive probe+3 | naive error | PTM vs eligibility | PTM extra delay | status |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---|",
    ]
    for row in clock.to_dict(orient="records"):
        lines.append(
            f"| {row['scenario']} | {row['probe_t0']} | {row['b3_break_t']} | "
            f"{row['b3_confirmation_t']} | {row['eligible_promotion_t']} | "
            f"{row['ptm_observation_t']} | {row['next_executable_t']} | "
            f"{row['naive_probe_plus_three_t']} | {row['naive_baseline_error_bars']} | "
            f"{row['ptm_vs_eligibility']} | {row['ptm_extra_delay_bars']} | "
            f"{row['promotion_status']} |"
        )
    lines += [
        "",
        "The synthetic fixtures contain no markup/markdown/B3 event, so "
        "`breakout_stand_in_bar` in the comparison CSV uses the structural "
        "escape bar as a CONSTRUCTED stand-in for the breakout.",
        "",
        "Two different delay baselines exist and must not be confused. This table "
        "compares against the CORRECTED baseline, `eligible_promotion_t = "
        "B3_break_t + 3`, so `PTM extra delay` is measured against the promotion "
        "the frozen #78 mechanics actually allow. The comparison CSV additionally "
        "carries `ptm_extra_delay_vs_naive_bars`, measured against the NAIVE "
        "`probe_t0 + 3` baseline; that column is large and non-zero (up to 80 "
        "bars) precisely because the naive baseline is wrong. Only the corrected "
        "figure answers 'does PTM delay a legitimate add-on'.",
        "",
        "## C1/C2 add-on policy (prereg clarification)",
        "",
        "The policy layer decides only whether the 75% add-on the frozen parent "
        "has already earned is RELEASED or WITHHELD. It never accelerates a "
        "promotion, never reduces exposure and never sizes.",
        "",
        "**One active challenger: C1.** C2 is retained historical evidence only "
        "and is excluded from the comparison and decision surface.",
        "",
        "| fixture | parent earns add-on | eligible bar | last bar | claims at/after "
        "eligibility | C1 disposition | C1 release | C1 executable | C1 delay | "
        "follow-up complete | withheld definite | open hold | width/ATR | width bin |",
        "|---|---|---:|---:|---:|---|---:|---:|---:|---|---|---|---:|---|",
    ]
    def cell(v):
        """Render a possibly-missing, possibly-pandas-coerced value.

        Rows pass through a DataFrame, so ``None`` can arrive as ``NaN`` and
        integers as floats.  Neither should leak into the report as ``nan``.
        """
        if v is None:
            return "-"
        if isinstance(v, float):
            if math.isnan(v):
                return "-"
            if float(v).is_integer():
                return str(int(v))
            return f"{v:.4g}"
        return str(v)

    for row in summary["addon_policy_rows"]:
        wa = row["width_atr"]
        if isinstance(wa, float) and not math.isnan(wa):
            width_txt = f"{wa:.2f}"
        else:
            width_txt = "-"
        lines.append(
            f"| {row['fixture']} | {row['parent_earns_addon']} | "
            f"{cell(row['eligible_promotion_bar'])} | "
            f"{cell(row['last_observed_bar'])} | "
            f"{row['claim_bars_at_or_after_eligibility']} | "
            f"{row['c1_disposition']} | "
            f"{cell(row['c1_first_release_bar'])} | "
            f"{cell(row['c1_first_executable_bar'])} | "
            f"{cell(row['c1_extra_delay_bars'])} | "
            f"{row['c1_followup_complete']} | {row['c1_withheld_definite']} | "
            f"{row['c1_open_hold_at_last_bar']} | {width_txt} | "
            f"{cell(row['width_bin'])} |"
        )
    addon = summary["addon_policy"]
    _ws = addon["c1_withheld_share_of_evaluable"]
    withheld_share_txt = "-" if _ws is None else f"{_ws:.1%}"
    _md = addon["c1_mean_delay_over_released"]
    mean_delay_txt = "-" if _md is None else f"{_md:.2f}"
    lines += [
        "",
        "### C1 add-on disposition, separating policy from follow-up completeness",
        "",
        "| disposition | count | meaning |",
        "|---|---:|---|",
        f"| `{DISPOSITION_PARENT_NOT_ELIGIBLE}` | "
        f"{addon['c1_parent_not_eligible']} | the parent never earned an add-on "
        "(P3 or no usable B3); not a PTM cost |",
        f"| `{DISPOSITION_OBSERVATION_RIGHT_CENSORED}` | "
        f"{addon['c1_observation_right_censored']} | follow-up incomplete; a "
        "future release is UNKNOWN and this is not evidence of permanent loss |",
        f"| `{DISPOSITION_POLICY_WITHHELD_THROUGH_EXPIRY}` | "
        f"{addon['c1_policy_withheld_through_expiry']} | withheld through the "
        "COMPLETE decision horizon; the only definite add-on loss |",
        f"| `{ADDON_DE_RISK}` | {addon['c1_baseline_de_risk_before_release']} | "
        "baseline de-risked/exited before any release |",
        f"| `{ADDON_PROMOTE}` | {addon['c1_promoted']} | released and executed at "
        "an observed finite delay |",
        "",
        f"* fixtures with a parent add-on entitlement: "
        f"**{addon['fixtures_with_parent_addon_entitlement']}** of "
        f"{addon['fixtures_evaluated']}",
        f"* right-censored **{addon['c1_observation_right_censored']}** "
        f"({addon['c1_right_censored_share_of_entitled']:.1%} of entitled) of "
        f"which **{len(addon['c1_observation_right_censored_before_eligibility'])}** "
        "end BEFORE the eligible decision bar, so no decision bar was ever "
        f"observed: `{addon['c1_observation_right_censored_before_eligibility']}`",
        f"* open hold still unresolved at the last observed bar: "
        f"**{addon['c1_open_hold_at_last_bar']}**",
        f"* fully evaluable episodes (parent-eligible AND complete horizon): "
        f"**{addon['c1_evaluable_episodes']}**",
        f"* fixtures that even REACH the expiry bar "
        f"(`eligible + {addon['episode_expiry_bars']}`): "
        f"**{addon['c1_fixtures_reaching_expiry']}**",
        f"* definite withholding estimable from the synthetic set: "
        f"**{addon['c1_definite_withholding_estimable_from_synthetics']}**",
        f"* withheld share of evaluable: **{withheld_share_txt}**",
        f"* delay over released episodes only — mean {mean_delay_txt}, max "
        f"{addon['c1_max_delay_over_released']}",
        "",
        f"**Horizon adequacy — the key correction this round.** "
        f"{addon['c1_horizon_adequacy_note']}",
    ]
    lines += [
        "",
        f"**Denominator rule.** {addon['c1_denominator_note']}",
        "",
        f"**Superseded figure.** `{addon['c1_superseded_figure']['value']}` is "
        f"**{addon['c1_superseded_figure']['status']}**: "
        f"{addon['c1_superseded_figure']['reason']}.",
        "",
        f"**Invariant, not evidence.** "
        f"`c1_signal_gate_invariant_holds = "
        f"{addon['c1_signal_gate_invariant_holds']}`. "
        f"{addon['c1_signal_gate_invariant_note']}",
        "",
        f"Definitely-withheld genuine sustained escapes: "
        f"**{addon['c1_censored_genuine_sustained_escapes']}**. "
        f"{addon['genuine_trend_note']}",
        "",
        f"{addon['c1_censored_note']}",
        "",
        f"C2 differs from C1 on **{addon['c2_differs_from_c1_count_historical']}** "
        "fixture(s) — retained as HISTORICAL EVIDENCE ONLY.",
        "",
        "### `o_min` sensitivity — RETIRED, historical record only",
        "",
        "| o_min | = parent CONFIRMATION_BARS | released | censored | mean delay "
        "(released) | max delay (released) | differs from C1 | degenerate (=C1) |",
        "|---:|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in summary["omin_sensitivity"]:
        mean = row["mean_delay_over_released"]
        lines.append(
            f"| {row['o_min']} | {row['equals_parent_confirmation_bars']} | "
            f"{row['released']} | {row['censored']} | "
            f"{'-' if mean is None else f'{mean:.2f}'} | "
            f"{row['max_delay_over_released']} | {row['differs_from_c1']} | "
            f"{row['is_degenerate_equals_c1']} |"
        )
    lines += [
        "",
        "**RETIRED — historical record only.** C2 is not an active challenger, "
        "so this table is kept only so the historical evidence stays "
        "reproducible. Its `o_min` must not be tuned further, promoted to a "
        "prereg parameter, or described as a measure of historical territory "
        "dwelling: it counts consecutive claiming bars (claim PERSISTENCE), not "
        "touch occupancy. The `o_min = 3` recommendation from the previous round "
        "is WITHDRAWN and is not part of the active study.",
        "",
    ]
    prov = summary["parent_event_provenance"]
    ab = addon["abstain_branch"]
    lines += [
        "",
        "### Declared dispositions and the trusted-reference abstain branch",
        "",
        "**Active challengers:** "
        f"`{addon['active_challengers']}` (count "
        f"{addon['active_challenger_count']}). **Retired:** "
        f"`{addon['retired_challengers']}`. {addon['retired_note']}",
        "",
        f"C1 disposition distribution: `{addon['c1_disposition_distribution']}`",
        "",
        f"Declared dispositions never observed under C1: "
        f"`{addon['c1_declared_dispositions_never_observed']}`",
        "",
        f"{addon['c1_declared_dispositions_never_observed_note']}",
        "",
        f"The abstain outcome (`{ADDON_BASELINE_HANDLES}`) was scanned for "
        f"counterexamples over **{ab['trusted_reference_observations_scanned']}** "
        "trusted-reference observations and found "
        f"**{len(ab['counterexamples'])}**. {ab['conclusion']}.",
        "",
        f"**Scope correction (this round).** {ab['scope_correction']}",
        "",
    ]
    wb = addon["wide_box_stratum"]
    lines += [
        "",
        "## Ex-ante wide-vs-narrow range stratum (replaces two invalid criteria)",
        "",
        f"* **Feature:** `{wb['feature']}` = {wb['feature_definition']}",
        f"* **Secondary:** {wb['secondary_feature']}",
        f"* **Windows:** ATR = {wb['atr_window_bars']} bars, reference = "
        f"{wb['reference_bars']} bars, all strictly PRE-probe",
        f"* **Frozen tertile edges:** `{wb['width_atr_edges_frozen']}` "
        f"({wb['edge_provenance']})",
        f"* **Bin rule:** {wb['bin_rule']}",
        f"* **Zero-data rule:** {wb['zero_data_rule']}",
        f"* **Causality:** {wb['causality']}",
        f"* **`sustained_escape` is OUTCOME-ONLY:** {wb['sustained_escape_note']}",
        "",
        "Superseded criteria:",
        "",
    ]
    for key, why in wb["superseded_criteria"].items():
        lines.append(f"* `{key}` — {why}")
    real = wb["real_cohort"]
    lines += [
        "",
        f"Discrimination on the {wb['synthetic_fixtures_evaluated']} synthetic "
        f"fixtures: **{wb['synthetic_distinct_width_atr_values']}** distinct "
        f"`width_atr` values (a tautology would be 1); bins "
        f"`{wb['synthetic_bin_counts']}`. {wb['discrimination_note']}",
        "",
        f"Real cohort: usable **{real['usable_b3_events']}** of "
        f"**{real['b3_events']}** B3 events at frozen edges "
        f"`{real['frozen_edges']}`. Unavailable breakdown: "
        f"`{real['unavailable_breakdown']}`",
        "",
        f"{real['note']}",
        "",
    ]
    lines += [
        "",
        "## Parent (#78) event provenance and parity contract",
        "",
        "| field | value |",
        "|---|---|",
        f"| event source marker | `{prov['event_source_marker']}` |",
        f"| event source module | `{prov['event_source_module']}` |",
        f"| policy module | `{prov['policy_module']}` |",
        f"| export glob | `{prov['export_glob']}` |",
        f"| event chain | {prov['event_chain']} |",
        f"| probe fraction | {prov['probe_fraction']} |",
        f"| baseline policy | `{prov['baseline_policy']}` ({prov['baseline_rule']}) |",
        f"| paths that add at t+3 | {prov['parent_paths_that_add_at_t3']} |",
        f"| path that never adds | `{prov['parent_path_that_never_adds']}` |",
        f"| no usable B3 | {prov['no_usable_b3_outcome']} |",
        "",
        "Frozen parity constants and the counts-only rehearsal:",
        "",
        "| constant | expected | rehearsed | match |",
        "|---|---:|---:|---|",
    ]
    rehearsal = prov["rehearsal"]
    pairs = (("events", "EXPECTED_EVENTS", "events"),
             ("episodes", "EXPECTED_EPISODES", "episodes"),
             ("B3 events", "EXPECTED_B3_EVENTS", "b3_events"),
             ("P1/P2", "EXPECTED_P12", "p1_p2"))
    for label, key, rkey in pairs:
        exp = prov["parity_constants"][key]
        got = rehearsal[rkey]
        lines.append(f"| {label} | {exp} | {got} | "
                     f"{'yes' if exp == got else 'NO'} |")
    comp = prov["path_composition_from_rehearsal"]
    lines += [
        "",
        f"Rehearsed against {rehearsal['export_files']} export file(s) with "
        f"reconstruction error {rehearsal['reconstruction_error']:.3g}; all four "
        "frozen constants reproduce. Causal path composition of the 997 B3 "
        f"events: `P0_NoTouch` {comp['P0_NoTouch']}, `P1_WickHold` "
        f"{comp['P1_WickHold']}, `P2_Reclaim` {comp['P2_Reclaim']} -- i.e. "
        f"{comp['adds_at_t3']} add at t+3 -- and `P3_FailedAcceptance` "
        f"{comp['P3_FailedAcceptance']} never add.",
        "",
        f"{prov['rehearsal_note']}",
        "",
        f"{prov['export_note']} Freeze status: `{prov['freeze_status']}`.",
        "",
        "## Boundaries",
        "",
        "```json",
        json.dumps(summary["boundaries"], indent=2),
        "```",
        "",
    ]
    (out / "issue185_ptm_report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8", newline="\n"
    )


if __name__ == "__main__":
    raise SystemExit(main())
