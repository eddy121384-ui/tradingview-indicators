#!/usr/bin/env python3
"""Issue #178 — frozen weight-policy primitives.

Frozen implementation of:
  indicators/macro-pressure-map/research/issue-178-weight-policy-prereg.md

Pure standard library. The Node executors implement the same frozen logic
for file generation; every primitive below was cross-checked through the
executed Node mirror (no Python runtime on this machine).
"""

from __future__ import annotations

# ------------------------------------------------ frozen §1 ----
BASELINE = {
    "sp500": 25.0, "nasdaq": 12.0, "russell": 8.0,
    "treasury2y": 8.0, "treasury10y": 14.0, "longtreasury": 8.0,
    "gold": 6.0, "oil": 4.0,
}
FAMILY = {
    "sp500": "equity", "nasdaq": "equity", "russell": "equity",
    "treasury2y": "rates", "treasury10y": "rates", "longtreasury": "rates",
    "gold": "real", "oil": "real",
}

# ------------------------------------------------ frozen §2 ----
MULT = {"0": 0.0, "Low": 0.5, "Neutral": 1.0, "High": 1.75}

# ------------------------------------------------ frozen §3 ----
SLEEVE_CAP = {
    "sp500": 35.0, "nasdaq": 20.0, "russell": 15.0,
    "treasury2y": 15.0, "treasury10y": 25.0, "longtreasury": 15.0,
    "gold": 12.0, "oil": 8.0,
}
FAMILY_CAP = {"equity": 60.0, "rates": 50.0, "real": 15.0}
CASH_MIN = 2.0
CASH_MAX = 60.0
CASH_MIN_BY_BIAS = {"low": 5.0, "neutral": 10.0, "high": 20.0}


# ------------------------------------------------ frozen §5 ----
def state_weights(tiers, available, cash_bias):
    """Deterministic tier→weight mapping (percent units, unrounded).

    tiers: sleeve -> 0/Low/Neutral/High (tier-0 raw = 0).
    available: set of non-cash sleeves with genuine returns this month.
    cash_bias: low/neutral/high.
    Returns (weights dict incl. cash, cap_bind list).
    """
    binds = []
    raw = {s: BASELINE[s] * MULT[t] for s, t in tiers.items()
           if s in available and MULT[t] > 0.0}
    for s in list(raw):
        if raw[s] > SLEEVE_CAP[s]:
            binds.append("sleeve:%s" % s)
            raw[s] = SLEEVE_CAP[s]
    famsum = {}
    for s, w in raw.items():
        famsum[FAMILY[s]] = famsum.get(FAMILY[s], 0.0) + w
    for fam, cap in FAMILY_CAP.items():
        if famsum.get(fam, 0.0) > cap:
            binds.append("family:%s" % fam)
            scale = cap / famsum[fam]
            for s in [x for x in raw if FAMILY[x] == fam]:
                raw[s] *= scale
    s_total = sum(raw.values())
    min_c = CASH_MIN_BY_BIAS[cash_bias]
    cash_raw = 100.0 - s_total
    if cash_raw < min_c:
        k = (100.0 - min_c) / s_total if s_total > 0 else 0.0
        for s in raw:
            raw[s] *= k
        cash = min_c
    elif cash_raw > CASH_MAX:
        k = (100.0 - CASH_MAX) / s_total if s_total > 0 else 0.0
        for s in raw:
            raw[s] *= k
        cash = CASH_MAX
    else:
        cash = cash_raw
    if cash < CASH_MIN:
        cash = CASH_MIN
    for s in list(raw):
        if raw[s] > SLEEVE_CAP[s]:
            binds.append("resleeve:%s" % s)
            cash += raw[s] - SLEEVE_CAP[s]
            raw[s] = SLEEVE_CAP[s]
    out = {s: 0.0 for s in BASELINE}
    out.update(raw)
    out["cash"] = cash
    return out, binds


def round_largest_remainder(weights, zeros):
    """Round to 2 decimals; rows total exactly 100.00; tier-0 stay 0.00."""
    floored = {}
    for s, w in weights.items():
        if s in zeros:
            floored[s] = 0.0
        else:
            floored[s] = __import__("math").floor(w * 100.0) / 100.0
    short = round(100.0 - sum(floored.values()), 2)
    cents = int(round(short * 100.0))
    if cents > 0:
        fracs = sorted(((weights[s] * 100.0 - floored[s] * 100.0, s)
                        for s in weights if s not in zeros),
                       reverse=True)
        for i in range(cents):
            floored[fracs[i % len(fracs)][1]] += 0.01
    return {s: round(v, 2) for s, v in floored.items()}


# ------------------------------------------------ frozen §6 ----
def confirm_state(state_hist):
    """B-2 confirmation: newest state must repeat twice, else hold previous.

    state_hist: list of consecutive monthly states ending at m-1.
    Returns confirmed state for allocation.
    """
    if len(state_hist) >= 2 and state_hist[-1] == state_hist[-2]:
        return state_hist[-1]
    if len(state_hist) >= 2:
        return state_hist[-2]
    return state_hist[-1]


# ------------------------------------------------ frozen §9 ----
def perf_stats(rets, cash_rets):
    """Unconditional performance metrics (decimal monthly series)."""
    import math
    n = len(rets)
    mean_m = sum(rets) / n
    var = sum((r - mean_m) ** 2 for r in rets) / n
    vol_a = math.sqrt(var) * math.sqrt(12.0)
    cagr = (1.0 + compound(rets)) ** (12.0 / n) - 1.0 if n else float("nan")
    ex = [r - c for r, c in zip(rets, cash_rets)]
    ex_m = sum(ex) / n
    ex_v = sum((e - ex_m) ** 2 for e in ex) / n
    sharpe_like = (ex_m * 12.0) / (math.sqrt(ex_v) * math.sqrt(12.0)) \
        if ex_v > 0 else float("nan")
    peak, maxdd = 1.0, 0.0
    cum = 1.0
    for r in rets:
        cum *= 1.0 + r
        peak = max(peak, cum)
        maxdd = min(maxdd, cum / peak - 1.0)
    return {
        "n": n, "cagr": cagr, "vol_ann": vol_a,
        "cash_excess_ann": (1.0 + compound(rets)) / (1.0 + compound(cash_rets)) - 1.0
        if n else float("nan"),
        "sharpe_like": sharpe_like, "maxdd": maxdd,
        "worst_month": min(rets),
        "pos_frac": sum(1 for r in rets if r > 0) / n,
    }


def compound(rs):
    p = 1.0
    for r in rs:
        p *= 1.0 + r
    return p - 1.0
