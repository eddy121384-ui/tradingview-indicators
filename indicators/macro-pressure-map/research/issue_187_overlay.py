#!/usr/bin/env python3
"""Issue #187 — frozen early-recovery overlay primitives (stdlib only, pure).

Mirrors the prereg verbatim. Tested by test_issue_187_overlay.py + Node mirror.
No file I/O, no network, no optimization.
"""
import math

ORDER = ["sp500", "nasdaq", "russell", "treasury2y", "treasury10y",
         "longtreasury", "gold", "oil"]
EQ = ["sp500", "nasdaq", "russell"]
SCAP = {"sp500": 35, "nasdaq": 20, "russell": 15, "treasury2y": 15,
        "treasury10y": 25, "longtreasury": 15, "gold": 12, "oil": 8}
CASH_MIN = 2.0
FAM_EQ_CAP = 60.0
BUDGET = 5.0
COST = 0.0002


def entry_signal(g2, g1, g0, i1, i0):
    """Prereg section 2. g2,g1,g0 = Growth t-2,t-1,t; i1,i0 = Infl t-1,t.
    All present (caller guarantees non-NaN). Returns bool."""
    return (g0 < -10.0
            and g0 > g1 > g2
            and i0 <= 10.0
            and (i0 - i1) <= 5.0)


def low_episodes(growth):
    """Raw Low episodes: maximal runs of idx with G < -10 (NaN breaks).
    growth: list of float|nan. Returns list of (start, end) inclusive."""
    eps, s = [], None
    for i, g in enumerate(growth):
        if isinstance(g, float) and math.isnan(g):
            if s is not None:
                eps.append((s, i - 1))
                s = None
            continue
        if g < -10.0:
            if s is None:
                s = i
        elif s is not None:
            eps.append((s, i - 1))
            s = None
    if s is not None:
        eps.append((s, len(growth) - 1))
    return eps


def size_overlay(base, requested=BUDGET):
    """Prereg section 4. Returns (w, added, blocked, reason)."""
    w = dict(base)
    eq = [s for s in EQ if w.get(s, 0) > 0]
    E = sum(w[s] for s in eq)
    head = sum(SCAP[s] - w[s] for s in eq)
    add = min(requested, max(0.0, w["cash"] - CASH_MIN), FAM_EQ_CAP - E, head)
    add = max(0.0, add)
    reason = "full" if abs(add - requested) < 1e-9 else (
        "cash_floor" if add == max(0.0, w["cash"] - CASH_MIN) else "cap_headroom")
    if E > 0 and add > 0:
        for s in eq:
            take = min((add * w[s]) / E, SCAP[s] - w[s])
            w[s] += take
            w["cash"] -= take
    return w, add, requested - add, reason


def exit_check(g1, g0, gm1, i0, im1, e_ref, e_now, e_prev, active_n):
    """Prereg section 5. NaN-safe (missing -> that exit does not fire).
    Returns list of firing exit letters (subset of A..E)."""
    fires = []
    if _fin(e_now) and _fin(e_ref) and e_now >= e_ref + 5 - 1e-9:
        fires.append("A")
    if (_fin(i0) and i0 > 10) or (_fin(i0) and _fin(im1) and i0 - im1 > 5):
        fires.append("B")
    if (_fin(g0) and _fin(g1) and _fin(gm1)
            and (g0 - g1) <= 0 and (g1 - gm1) <= 0):
        fires.append("C")
    if _fin(e_now) and _fin(e_prev) and e_now - e_prev <= -5 + 1e-9:
        fires.append("D")
    if active_n >= 6:
        fires.append("E")
    return fires


def _fin(x):
    return isinstance(x, (int, float)) and math.isfinite(x)


def downside_vol(rs):
    v = [x for x in rs if _fin(x)]
    if not v:
        return float("nan")
    return math.sqrt(sum(min(x, 0) ** 2 for x in v) / len(v)) * math.sqrt(12)


def metrics(R, C):
    idx = [i for i in range(len(R)) if _fin(R[i]) and _fin(C[i])]
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
    keys = ORDER + ["cash"]
    tot, prev = 0.0, None
    for w in stream:
        if prev is not None:
            tot += sum(abs(w[k] - prev[k]) for k in keys) / 2 / 100
        prev = dict(w)
    return tot / len(stream) * 12 if stream else float("nan")


def apply_gates(g):
    """Prereg section 12 tree. g: dict G1..G8 booleans + n_act + overlap_y.
    Returns verdict string."""
    if g["n_act"] < 3 or g["overlap_y"] < 10:
        return "early_recovery_equity_overlay_not_assessable"
    vals = [g[f"G{i}"] for i in range(1, 9)]
    if all(vals):
        return "early_recovery_equity_overlay_supported"
    fails = sum(1 for v in vals if not v)
    if g["G1"] and fails <= 2 and g["G2"] and g["G4"]:
        return "early_recovery_equity_overlay_suggestive_with_limitations"
    return "early_recovery_equity_overlay_not_supported"
