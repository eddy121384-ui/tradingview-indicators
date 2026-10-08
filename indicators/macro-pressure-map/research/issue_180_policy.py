#!/usr/bin/env python3
"""Issue #180 — frozen implementation primitives.

Frozen implementation of:
  indicators/macro-pressure-map/research/issue-180-implementation-prereg.md

Pure standard library. The Node executors implement the same frozen logic
for file generation; every primitive below was cross-checked through the
executed Node mirror (no Python runtime on this machine).
"""

from __future__ import annotations

import math

NAN = float("nan")

# ------------------------------------------------ frozen §4 ----
COST_RATE_PRIMARY = 0.0002
COST_RATE_ALT = 0.0010


def apply_cost(pre_cost_ret, oneway_turnover, rate=COST_RATE_PRIMARY):
    """post-cost month return (turnover in fraction units, e.g. 0.20)."""
    return pre_cost_ret - oneway_turnover * rate


# --------------------------------------- frozen §8 tracking ----
def track_stats(proxy, research):
    """Unconditional proxy-vs-research stats over common months."""
    pairs = [(p, r) for p, r in zip(proxy, research)
             if is_fin(p) and is_fin(r)]
    n = len(pairs)
    if n < 2:
        return {"n": n}
    diffs = [p - r for p, r in pairs]
    ma_p = sum(p for p, _ in pairs) / n
    ma_r = sum(r for _, r in pairs) / n
    cov = sum((p - ma_p) * (r - ma_r) for p, r in pairs)
    va = sum((p - ma_p) ** 2 for p, _ in pairs)
    vb = sum((r - ma_r) ** 2 for _, r in pairs)
    md = sum(diffs) / n
    te = math.sqrt(sum((d - md) ** 2 for d in diffs) / n) * math.sqrt(12.0)
    cp = compound([p for p, _ in pairs])
    cr = compound([r for _, r in pairs])
    return {
        "n": n,
        "corr": cov / math.sqrt(va * vb) if va > 0 and vb > 0 else NAN,
        "mean_diff_pp": md * 100.0,
        "ann_ret_diff_pp": ((1.0 + cp) / (1.0 + cr) - 1.0) * 100.0,
        "te_vol_pct": te * 100.0,
        "worst_diff_pp": min(diffs) * 100.0,
        "cum_ratio": (1.0 + cp) / (1.0 + cr),
    }


def is_fin(x) -> bool:
    return x is not None and not (isinstance(x, float) and math.isnan(x))


def compound(rs):
    p = 1.0
    for r in rs:
        p *= 1.0 + r
    return p - 1.0


def classify_impl(n, ann_ret_diff_pp, te_vol_pct, corr, mismatch_unresolved):
    """Frozen §8 classification thresholds."""
    if n < 60:
        return "implementation_not_ready"
    if (abs(ann_ret_diff_pp) <= 0.5 and te_vol_pct <= 1.5 and corr >= 0.99
            and not mismatch_unresolved):
        return "implementation_faithful"
    if corr >= 0.95 and te_vol_pct <= 4.0:
        return "implementation_acceptable_with_limitation"
    return "implementation_materially_different"


# --------------------------------------- frozen §9 decision ----
def decide(cagr_gap_pp, te_pct, maxdd_gap_pp, drag_pct, rank_kept,
           defensive_vol_worse_pp, semantic_unresolved, not_ready_big):
    """Frozen §9 pass/fail decision. Gaps in pp units (implementation − research)."""
    conds = {
        "cagr": abs(cagr_gap_pp) <= 1.0,
        "te": te_pct <= 2.5,
        "maxdd": maxdd_gap_pp >= -5.0,
        "drag": drag_pct <= 0.4,
        "rank": rank_kept,
        "defensive": defensive_vol_worse_pp <= 2.0,
    }
    fails = sum(1 for v in conds.values() if not v)
    if not_ready_big:
        return "tradable_implementation_not_ready", conds
    if fails == 0:
        return "tradable_implementation_candidate_complete", conds
    if fails <= 2 and not semantic_unresolved and te_pct <= 4.0:
        return "tradable_implementation_candidate_complete_with_limitations", conds
    return "tradable_implementation_not_ready", conds
