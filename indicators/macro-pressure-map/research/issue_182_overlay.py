#!/usr/bin/env python3
"""Issue #182 — frozen tactical-overlay primitives.

Frozen implementation of:
  indicators/macro-pressure-map/research/issue-182-v66-tactical-prereg.md

Pure standard library. The Node executors implement the same frozen logic
for file generation; every primitive below was cross-checked through the
executed Node mirror (no Python runtime on this machine).
"""

from __future__ import annotations

# ------------------------------------------------ frozen §3 ----
BUDGET = 5.0
EQUITY_SLEEVES = ("sp500", "nasdaq", "russell")
SLEEVE_CAP = {
    "sp500": 35.0, "nasdaq": 20.0, "russell": 15.0,
    "treasury2y": 15.0, "treasury10y": 25.0, "longtreasury": 15.0,
    "gold": 12.0, "oil": 8.0,
}
EQUITY_FAMILY_CAP = 60.0
CASH_FLOOR = 2.0


def classify(growth: str, inflation: str) -> str:
    """Frozen V6.6 tactical classification (risk-off precedence built in)."""
    if growth == "High" and inflation != "High":
        return "risk-on"
    if growth == "Low" or inflation == "High":
        return "risk-off"
    return "neutral"


def apply_overlay(struct_w, signal: str, budget: float = BUDGET):
    """Apply bounded Equity<->Cash overlay to frozen structural weights.

    struct_w: dict sleeve -> weight (percent units, sums to 100).
    Returns (new weights dict, blocked_amount).
    """
    w = dict(struct_w)
    eq = [s for s in EQUITY_SLEEVES if w.get(s, 0.0) > 0.0]
    e_sum = sum(w[s] for s in eq)
    blocked = 0.0
    if signal == "risk-on":
        headroom = [SLEEVE_CAP[s] - w[s] for s in eq]
        add = min(budget, max(0.0, w["cash"] - CASH_FLOOR),
                  EQUITY_FAMILY_CAP - e_sum, sum(headroom))
        add = max(0.0, add)
        if e_sum > 0 and add > 0:
            for s, h in zip(eq, headroom):
                share = add * w[s] / e_sum
                take = min(share, h)
                blocked += share - take
                w[s] += take
            w["cash"] -= (add - blocked)
    elif signal == "risk-off":
        cut = min(budget, e_sum)
        if e_sum > 0 and cut > 0:
            for s in eq:
                w[s] -= cut * w[s] / e_sum
            w["cash"] += cut
    return w, blocked


# ------------------------------------------------ frozen §8 ----
def decide(cagr_gap, sharpe_gap, maxdd_gap, incr_turnover, conc_top1,
           benefit_positive, worst_seg_gap, worst_state_gap):
    """Frozen gate evaluation. Gaps = C minus A (pp units, MaxDD in pp)."""
    g1 = cagr_gap >= -0.50
    g2 = sharpe_gap >= -0.05
    g3 = maxdd_gap >= -3.0
    g4 = incr_turnover <= 40.0
    g5 = True if not benefit_positive else conc_top1 <= 0.60
    g6 = worst_seg_gap >= -1.0
    g7 = worst_state_gap >= -3.0
    gates = {"g1_cagr": g1, "g2_sharpe": g2, "g3_maxdd": g3,
             "g4_turnover": g4, "g5_concentration": g5,
             "g6_segment": g6, "g7_state": g7}
    fails = sum(1 for v in gates.values() if not v)
    if fails == 0:
        verdict = "v66_tactical_overlay_candidate_supported"
    elif (cagr_gap > 0 and g3 and g7 and fails <= 2):
        verdict = "v66_tactical_overlay_candidate_suggestive"
    else:
        verdict = "v66_tactical_overlay_not_supported"
    return verdict, gates
