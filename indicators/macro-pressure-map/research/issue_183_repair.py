#!/usr/bin/env python3
"""Issue #183 — frozen repair primitives.

Frozen implementation of:
  indicators/macro-pressure-map/research/issue-183-lineage-repair-spec.md

Pure standard library. The Node replay implements the same frozen logic; every
primitive below was cross-checked BOTH through the executed Node mirror and
through `python -m unittest test_issue_183_repair` (bundled CPython 3.12).
"""

from __future__ import annotations

import math

NAN = float("nan")

# ------------------------------------------------ frozen §2 ----
TOL = 1e-9
ZERO_CELLS = {
    ("G_Low/I_Low", "oil"),
    ("G_Neutral/I_High", "russell"),
    ("G_High/I_Low", "gold"),
}
SLEEVE_CAP = {
    "sp500": 35.0, "nasdaq": 20.0, "russell": 15.0,
    "treasury2y": 15.0, "treasury10y": 25.0, "longtreasury": 15.0,
    "gold": 12.0, "oil": 8.0,
}
FAMILY = {
    "sp500": "equity", "nasdaq": "equity", "russell": "equity",
    "treasury2y": "rates", "treasury10y": "rates", "longtreasury": "rates",
    "gold": "real", "oil": "real",
}
FAMILY_CAP = {"equity": 60.0, "rates": 50.0, "real": 15.0}


def is_fin(x) -> bool:
    return x is not None and not (isinstance(x, float) and math.isnan(x))


def assert_matrix_row(state: str, weights: dict) -> list:
    """Frozen §2 integrity asserts for one matrix row. Returns error list."""
    errs = []
    tot = sum(weights.values())
    if abs(tot - 100.0) > TOL:
        errs.append("sum %s = %r" % (state, tot))
    if tot > 100.0 + TOL:
        errs.append("gross>100 %s" % state)
    for s, w in weights.items():
        if w < -TOL:
            errs.append("negative %s %s" % (state, s))
        if s in SLEEVE_CAP and w > SLEEVE_CAP[s] + TOL:
            errs.append("sleeve-cap %s %s" % (state, s))
        if (state, s) in ZERO_CELLS and abs(w) > TOL:
            errs.append("zero-cell %s %s" % (state, s))
    for fam, cap in FAMILY_CAP.items():
        fsum = sum(w for s, w in weights.items() if FAMILY.get(s) == fam)
        if fsum > cap + TOL:
            errs.append("family-cap %s %s" % (state, fam))
    if weights.get("cash", NAN) < 2.0 - TOL:
        errs.append("cash-min %s" % state)
    if weights.get("cash", NAN) > 60.0 + TOL:
        errs.append("cash-max %s" % state)
    return errs


# ------------------------------------------------ frozen §4 ----
def decide_178(rel_cagr_gap, maxdd_gap, turnover_gap):
    """Comparative-revalidation mapping for corrected #178 (spec §4)."""
    if rel_cagr_gap is None or maxdd_gap is None or turnover_gap is None:
        return "state_weight_policy_candidate_revalidated_with_limitations"
    if maxdd_gap < -10.0:
        return "state_weight_policy_candidate_invalidated_by_repair"
    if abs(rel_cagr_gap) <= 1.0 and maxdd_gap >= -3.0 and abs(turnover_gap) <= 5.0:
        return "state_weight_policy_candidate_revalidated"
    return "state_weight_policy_candidate_revalidated_with_limitations"


def decide_180(fails: int, semantic_unresolved: bool, te: float) -> str:
    if fails == 0:
        return "tradable_implementation_revalidated"
    if fails <= 2 and not semantic_unresolved and te <= 4.0:
        return "tradable_implementation_revalidated_with_limitations"
    return "tradable_implementation_invalidated_by_repair"


def decide_182(cagr_gap, sharpe_gap, maxdd_gap, incr_turnover,
               conc_top1, benefit_positive, worst_seg, worst_state):
    """Original #182 gate mapping, reused verbatim."""
    g1 = cagr_gap >= -0.50
    g2 = sharpe_gap >= -0.05
    g3 = maxdd_gap >= -3.0
    g4 = incr_turnover <= 40.0
    g5 = True if not benefit_positive else conc_top1 <= 0.60
    g6 = worst_seg >= -1.0
    g7 = worst_state >= -3.0
    gates = {"g1_cagr": g1, "g2_sharpe": g2, "g3_maxdd": g3,
             "g4_turnover": g4, "g5_concentration": g5,
             "g6_segment": g6, "g7_state": g7}
    fails = sum(1 for v in gates.values() if not v)
    if fails == 0:
        verdict = "v66_tactical_overlay_candidate_supported"
    elif cagr_gap > 0 and g3 and g7 and fails <= 2:
        verdict = "v66_tactical_overlay_candidate_suggestive"
    else:
        verdict = "v66_tactical_overlay_not_supported"
    return verdict, gates
