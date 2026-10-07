#!/usr/bin/env python3
"""Issue #177 — frozen policy-translation primitives.

Frozen implementation of:
  indicators/macro-pressure-map/research/issue-177-state-allocation-policy-prereg.md

Pure standard library (no numpy/pandas). The Node builder implements the same
frozen rules for file generation; the primitives below are exercised directly by
`test_issue_177_policy.py` under the bundled Python runtime, and independently
re-implemented by the executed Node acceptance suite
`test_issue_177_matrix.mjs` (which does not import this module).
"""

from __future__ import annotations

import math

NAN = float("nan")

TIERS = ("0", "Low", "Neutral", "High")
POINTS = {"High": 2, "Neutral": 1, "Low": 0, "0": -1}


def is_fin(x) -> bool:
    return x is not None and not (isinstance(x, float) and math.isnan(x))


# ------------------------------------------------------- frozen §3 ----
def baseline_tier(evidence: str, mean_excess):
    """Non-cash baseline tier from frozen evidence (before zero upgrade)."""
    if evidence == "historically_favored":
        return "High"
    if evidence == "historically_unfavorable":
        return "Low"
    if evidence == "mixed":
        if not is_fin(mean_excess):
            return "Low"
        return "Neutral" if mean_excess >= 0 else "Low"
    if evidence == "insufficient_sample":
        return "Neutral"
    raise ValueError("unknown evidence: %r" % (evidence,))


# ------------------------------------------------------- frozen §4 ----
def zero_rule_b(evidence, mean_ex, ep_hit, p10_ex, worst_ep, p_material,
                ex_worst_mean_ex) -> bool:
    """Path-B zero test on current hardened evidence (all inputs required)."""
    if evidence != "historically_unfavorable":
        return False
    if not (is_fin(mean_ex) and mean_ex < 0):
        return False
    if not (is_fin(ep_hit) and ep_hit <= 0.40):
        return False
    tail = ((is_fin(p10_ex) and p10_ex <= -0.04)
            or (is_fin(worst_ep) and worst_ep <= -0.15)
            or (is_fin(p_material) and p_material >= 0.10))
    if not tail:
        return False
    return bool(is_fin(ex_worst_mean_ex) and ex_worst_mean_ex < 0)


def apply_zero(baseline: str, flag_a: bool, rule_b: bool):
    """Upgrade Low->0 only via frozen zero rule; returns (tier, reason)."""
    if baseline == "Low" and (flag_a or rule_b):
        return "0", ("A" if flag_a else "B")
    return baseline, ""


# ------------------------------------------------------- frozen §5 ----
LIMITED_ELIGIBILITY = {"eligible_with_limitation"}
LIMITED_VERDICTS = {"hardened_with_limitation",
                    "unresolved_keep_issue174_semantics"}


def confidence(eligibility: str, hardening_verdict: str | None) -> str:
    if eligibility in LIMITED_ELIGIBILITY:
        return "limited"
    if hardening_verdict in LIMITED_VERDICTS:
        return "limited"
    return "full"


# ------------------------------------------------------- frozen §7 ----
def cash_bias(opportunity_score: int) -> str:
    if opportunity_score <= 3:
        return "high"
    if opportunity_score <= 8:
        return "neutral"
    return "low"


def opportunity_score(tiers) -> int:
    return sum(POINTS[t] for t in tiers)
