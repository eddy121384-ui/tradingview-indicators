#!/usr/bin/env python3
"""Issue #184 — frozen specificity primitives (stdlib only).

Mirrors the frozen #182/#183 overlay math verbatim. Pure functions only;
no file I/O, no returns, no optimization. Tested by
test_issue_184_specificity.py and the Node mirror.
"""
import math

ORDER = ["sp500", "nasdaq", "russell", "treasury2y", "treasury10y",
         "longtreasury", "gold", "oil"]
EQ = ["sp500", "nasdaq", "russell"]
SCAP = {"sp500": 35, "nasdaq": 20, "russell": 15, "treasury2y": 15,
        "treasury10y": 25, "longtreasury": 15, "gold": 12, "oil": 8}
CASH_MIN = 2.0
CASH_MAX = 60.0
BUDGET = 5.0
COST = 0.0002

# Frozen exposure reduction (Issue #184 prereg section 4, weights-only).
D_PP = 3.051724137931045


def overlay_w(base, signal, budget=BUDGET):
    """Frozen #182 overlayW verbatim. base: dict with EQ sleeves + 'cash'."""
    w = dict(base)
    eq = [s for s in EQ if w.get(s, 0) > 0]
    E = sum(w[s] for s in eq)
    if signal == "risk-on":
        head = sum(SCAP[s] - w[s] for s in eq)
        add = min(budget, max(0.0, w["cash"] - CASH_MIN), CASH_MAX - E, head)
        add = max(0.0, add)
        if E > 0 and add > 0:
            for s in eq:
                take = min((add * w[s]) / E, SCAP[s] - w[s])
                w[s] += take
                w["cash"] -= take
    elif signal == "risk-off":
        cut = min(budget, E)
        if E > 0 and cut > 0:
            for s in eq:
                w[s] -= (cut * w[s]) / E
            w["cash"] += cut
    return w


def constant_w(base, d=D_PP):
    """Frozen #184 C control: constant Equity->Cash cut, pro-rata, zeros kept."""
    w = dict(base)
    eq = [s for s in EQ if w.get(s, 0) > 0]
    E = sum(w[s] for s in eq)
    cut = min(d, E)
    if E > 0 and cut > 0:
        for s in eq:
            w[s] -= (cut * w[s]) / E
        w["cash"] += cut
    return w


def shift_signals(sigs, k):
    """Frozen D construction: month i gets S[(i-k) mod N]."""
    n = len(sigs)
    return [sigs[(i - k) % n] for i in range(n)]


def downside_vol(rs):
    v = [x for x in rs if isinstance(x, float) or isinstance(x, int)]
    v = [x for x in v if x == x and abs(x) != float("inf")]
    if not v:
        return float("nan")
    return math.sqrt(sum(min(x, 0) ** 2 for x in v) / len(v)) * math.sqrt(12)


def metrics(R, C):
    """Verbatim #183 metrics(R, cash). Returns dict with n, cagr, vol_ann,
    cash_excess_ann, sharpe_like, maxdd, worst_month, pos_frac, downside_vol."""
    idx = [i for i in range(len(R))
           if isinstance(R[i], (int, float)) and isinstance(C[i], (int, float))
           and math.isfinite(R[i]) and math.isfinite(C[i])]
    Rs = [R[i] for i in idx]
    Cs = [C[i] for i in idx]
    n = len(Rs)
    if not n:
        return {"n": 0}
    mm = sum(Rs) / n
    sd = math.sqrt(sum((x - mm) ** 2 for x in Rs) / n)
    comp = 1.0
    for x in Rs:
        comp *= 1 + x
    compC = 1.0
    for x in Cs:
        compC *= 1 + x
    ex = [Rs[i] - Cs[i] for i in range(n)]
    em = sum(ex) / n
    esd = math.sqrt(sum((x - em) ** 2 for x in ex) / n)
    peak, dd, cum = 1.0, 0.0, 1.0
    for r in Rs:
        cum *= 1 + r
        peak = max(peak, cum)
        dd = min(dd, cum / peak - 1)
    return {
        "n": n,
        "cagr": comp ** (12 / n) - 1,
        "vol_ann": sd * math.sqrt(12),
        "cash_excess_ann": (comp / compC) ** (12 / n) - 1,
        "sharpe_like": (em * 12) / (esd * math.sqrt(12)) if esd > 0 else float("nan"),
        "maxdd": dd,
        "worst_month": min(Rs),
        "pos_frac": sum(1 for r in Rs if r > 0) / n,
        "downside_vol": downside_vol(Rs),
    }


def turnover_ann(stream):
    """stream: list of weight dicts in panel order. First month 0."""
    keys = ORDER + ["cash"]
    tot, prev = 0.0, None
    for w in stream:
        if prev is not None:
            tot += sum(abs(w[k] - prev[k]) for k in keys) / 2 / 100
        prev = dict(w)
    n = len(stream)
    return tot / n * 12 if n else float("nan")


def rank_higher(value, placebos):
    """Percentile rank for higher-better: 100 * #(D <= B) / N."""
    if not placebos:
        return float("nan")
    return 100.0 * sum(1 for d in placebos if d <= value) / len(placebos)


def rank_lower(value, placebos):
    """Percentile rank for lower-better: 100 * #(D >= B) / N."""
    if not placebos:
        return float("nan")
    return 100.0 * sum(1 for d in placebos if d >= value) / len(placebos)


def specificity_verdict(s1, s2, s3, s3partial, s4, s5):
    """Frozen prereg section 8 decision tree. Returns exactly one verdict."""
    if s1 and s2 and s3 and s4 and s5:
        return "v66_overlay_specific_information_supported"
    if (not s1) or (not s4) or (not s5):
        return "v66_overlay_not_supported_after_controls"
    if s1 and s2 and s4 and s5 and (not s3):
        return "v66_overlay_risk_control_supported_but_timing_not_specific"
    if s1 and s4 and s5 and (s2 or s3partial):
        return "v66_overlay_specificity_suggestive"
    return "v66_overlay_not_supported_after_controls"
