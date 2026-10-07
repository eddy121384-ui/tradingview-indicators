#!/usr/bin/env python3
"""Issue #176 — frozen backbone-hardening primitives.

Frozen implementation of:
  indicators/macro-pressure-map/research/issue-176-allocation-backbone-prereg.md

Pure standard library (no numpy/pandas). Node executors implement the same
frozen formulas for fetching; every numeric vector was cross-checked through
the executed Node mirror (no Python runtime on this machine).

Firewall: no macro x asset join here; no state-conditioned computation here.
Unconditional builders + comparison metrics only.
"""

from __future__ import annotations

import math

NAN = float("nan")


def is_fin(x) -> bool:
    return x is not None and not (isinstance(x, float) and math.isnan(x))


# --------------------------------------------------- hardened builders ----
def sp500_tr_recon(price_prev, price_curr, shiller_div_curr):
    """Frozen S&P TR reconstruction (prereg §3.1).

    price_prev/curr: Yahoo ^GSPC DAILY month-end closes (month-end timing).
    shiller_div_curr: Shiller monthly Dividend level for month t (annual-rate
      cash dividends; interpolated intra-year by Shiller).
    r = price_return + (D_t / 12) / P_{t-1}.
    """
    if not is_fin(price_prev) or not is_fin(price_curr) or price_prev == 0:
        return NAN
    if not is_fin(shiller_div_curr):
        return NAN
    return price_curr / price_prev - 1.0 + (shiller_div_curr / 12.0) / price_prev


def oil_investable(front_prev, front_curr, tb3ms_prev_pct):
    """Frozen oil investable return (prereg §3.4).

    excess from Yahoo CL=F continuous front-month month-end closes;
    collateral from FRED TB3MS_{t-1} / 1200 (same frozen Cash accrual).
    r = (1 + excess) * (1 + collateral) - 1.
    """
    if not is_fin(front_prev) or not is_fin(front_curr) or front_prev == 0:
        return NAN
    if not is_fin(tb3ms_prev_pct):
        return NAN
    excess = front_curr / front_prev - 1.0
    collat = tb3ms_prev_pct / 1200.0
    return (1.0 + excess) * (1.0 + collat) - 1.0


def dividend_wedge(tr_prev, tr_curr, price_prev, price_curr):
    """Monthly TR-minus-price wedge (implied dividend accrual)."""
    if not all(is_fin(v) for v in (tr_prev, tr_curr, price_prev, price_curr)):
        return NAN
    if tr_prev == 0 or price_prev == 0:
        return NAN
    return (tr_curr / tr_prev - 1.0) - (price_curr / price_prev - 1.0)


# --------------------------------------------------- comparison metrics ----
def mean(xs):
    v = [x for x in xs if is_fin(x)]
    if not v:
        return NAN
    return sum(v) / len(v)


def biased_sd(xs):
    v = [x for x in xs if is_fin(x)]
    if not v:
        return NAN
    m = sum(v) / len(v)
    return math.sqrt(sum((x - m) ** 2 for x in v) / len(v))


def pearson(a, b):
    pairs = [(x, y) for x, y in zip(a, b) if is_fin(x) and is_fin(y)]
    if len(pairs) < 3:
        return NAN
    ma = sum(x for x, _ in pairs) / len(pairs)
    mb = sum(y for _, y in pairs) / len(pairs)
    cov = sum((x - ma) * (y - mb) for x, y in pairs)
    va = sum((x - ma) ** 2 for x, _ in pairs)
    vb = sum((y - mb) ** 2 for _, y in pairs)
    if va == 0 or vb == 0:
        return NAN
    return cov / math.sqrt(va * vb)


def mae(a, b):
    pairs = [(x, y) for x, y in zip(a, b) if is_fin(x) and is_fin(y)]
    if not pairs:
        return NAN
    return sum(abs(x - y) for x, y in pairs) / len(pairs)


def compound(rs):
    p = 1.0
    for r in rs:
        if not is_fin(r):
            return NAN
        p *= 1.0 + r
    return p - 1.0


def largest_disagreements(dates, old, new, k=10):
    rows = [(d, o, n, n - o) for d, o, n in zip(dates, old, new)
            if is_fin(o) and is_fin(n)]
    rows.sort(key=lambda r: abs(r[3]), reverse=True)
    return rows[:k]
