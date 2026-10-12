#!/usr/bin/env python3
"""Issue #188 — frozen edge-attribution primitives (stdlib only, pure).

Mirrors the prereg verbatim. Tested by test_issue_188_primitives.py + Node
mirror. No file I/O, no network, no optimization.
"""
import math

COST_ETF = 0.0002


def _fin(x):
    return isinstance(x, (int, float)) and math.isfinite(x)


def drawdowns(rets):
    """Per-month drawdown fractions (<=0) on valid months; NaN skipped."""
    v = [x for x in rets if _fin(x)]
    out, peak, cum = [], 1.0, 1.0
    for r in v:
        cum *= 1 + r
        peak = max(peak, cum)
        out.append(cum / peak - 1)
    return out


def ulcer_index(rets):
    dd = drawdowns(rets)
    if not dd:
        return float("nan")
    return 100.0 * math.sqrt(sum(d * d for d in dd) / len(dd))


def upi(cagr, cash_cagr, ulcer):
    if not _fin(ulcer) or ulcer == 0:
        return None
    return (cagr - cash_cagr) * 100.0 / ulcer


def cdar95(rets):
    dd = [d for d in drawdowns(rets) if _fin(d)]
    if len(dd) < 20:
        return None
    s = sorted(dd)
    cut = s[max(0, math.ceil(0.05 * len(s)) - 1)]
    tail = [d for d in dd if d <= cut]
    return -100.0 * sum(tail) / len(tail)


def worst_rolling_12m(rets):
    v = [x for x in rets if _fin(x)]
    if len(v) < 12:
        return None
    worst = None
    for i in range(len(v) - 11):
        w = v[i:i + 12]
        c = 1.0
        for r in w:
            c *= 1 + r
        if worst is None or c - 1 < worst:
            worst = c - 1
    return worst


def underwater_duration(rets):
    v = [x for x in rets if _fin(x)]
    best, cur, peak, cum = 0, 0, 1.0, 1.0
    for r in v:
        cum *= 1 + r
        if cum >= peak:
            peak = cum
            cur = 0
        else:
            cur += 1
            best = max(best, cur)
    censored = cur > 0
    return {"months": best, "censored": censored}


def favorable_percentile(value, placebos):
    """100*(#{strictly worse} + 0.5*#{ties})/N. Caller orients higher-better.
    For lower-better metrics pass negated values."""
    n = len(placebos)
    if not n or not _fin(value):
        return float("nan")
    worse = sum(1 for d in placebos if _fin(d) and d < value)
    ties = sum(1 for d in placebos if _fin(d) and d == value)
    return 100.0 * (worse + 0.5 * ties) / n


def mulberry32(seed):
    state = seed & 0xFFFFFFFF

    def rnd():
        nonlocal state
        state = (state + 0x6D2B79F5) & 0xFFFFFFFF
        t = state
        t = ((t ^ (t >> 15)) * (t | 1)) & 0xFFFFFFFF
        t ^= t + (((t ^ (t >> 7)) * (t | 61)) & 0xFFFFFFFF)
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296.0

    return rnd


def bootstrap_cagr_diff_ci(dh, ctrl, block=24, reps=5000, seed=188):
    """Circular block bootstrap on paired series; per-replicate own-compounding
    CAGR diff (applied-month annualization). Returns (lo5, hi95)."""
    n = len(dh)
    rnd = mulberry32(seed)
    diffs = []
    nb = math.ceil(n / block)
    for _ in range(reps):
        idx = []
        for _ in range(nb):
            s = int(rnd() * n)
            idx.extend((s + k) % n for k in range(block))
        idx = idx[:n]
        cd, cc = 1.0, 1.0
        for i in idx:
            cd *= 1 + dh[i]
            cc *= 1 + ctrl[i]
        diffs.append((cd ** (12 / n) - 1) - (cc ** (12 / n) - 1))
    diffs.sort()
    return (diffs[int(0.05 * reps)], diffs[int(0.95 * reps)])


def shapley_2factor(a, b, c, aprime):
    """Returns (policy_effect, avail_effect, interaction) in input units."""
    pe = 0.5 * ((a - c) + (aprime - b))
    ae = 0.5 * ((a - aprime) + (c - b))
    it = (a - aprime) - (c - b)
    return (pe, ae, it)


def apply_verdict(flags):
    """Prereg section 8 tree. flags: assessable(bool), g1..g8(bool)."""
    if not flags["assessable"]:
        return "deep_history_evidence_mixed_or_inconclusive"
    g = [flags[f"G{i}"] for i in range(1, 9)]
    if all(g):
        return "deep_history_macro_information_supported"
    if flags["G1"] and not flags["G4"]:
        return "deep_history_reducible_to_simpler_defense"
    if not flags["G6"] or not flags["G7"]:
        return "deep_history_exposure_or_availability_explained"
    return "deep_history_evidence_mixed_or_inconclusive"
