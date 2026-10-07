#!/usr/bin/env python3
"""Issue #174 — 9-sleeve macro asset outcome map: frozen backbone builders/metrics.

Frozen implementation of:
  indicators/macro-pressure-map/research/issue-174-nine-sleeve-map-prereg.md

Pure standard library (no numpy/pandas) so the frozen record runs anywhere.
Node executors (issue_174_build.mjs / issue_174_map.mjs) implement the same
frozen formulas for fetching; every numeric vector below was cross-checked
through the executed Node mirror (no Python runtime on this machine).

Firewall: no macro x asset join is performed here; no state-conditioned
return is computed here. This file defines builders + metric/classifier
primitives only. The Node map step performs the join AFTER the prereg commit.
"""

from __future__ import annotations

import math

# ------------------------------------------------------------ frozen ----
STATE_LO = -10.0
STATE_HI = 10.0

GROWTH_BANDS = ("Low", "Neutral", "High")
INFL_BANDS = ("Low", "Neutral", "High")

ERAS = (
    ("E1_pre_volcker", "1966-03-01", "1979-12-01"),
    ("E2_great_moderation", "1980-01-01", "2007-12-01"),
    ("E3_post_gfc_qe", "2008-01-01", "2019-12-01"),
    ("E4_post_2020", "2020-01-01", "2026-08-01"),
)

MATERIAL_MONTHLY_PP = -0.02
MATERIAL_EPISODE_PP = -0.05

NAN = float("nan")


def is_fin(x) -> bool:
    return x is not None and not (isinstance(x, float) and math.isnan(x))


# ---------------------------------------------------------------- state ----
def band(score: float) -> str:
    if not is_fin(score):
        return "NA"
    if score < STATE_LO:
        return "Low"
    if score > STATE_HI:
        return "High"
    return "Neutral"


def state_of(g, i) -> str:
    gb, ib = band(g), band(i)
    if gb == "NA" or ib == "NA":
        return "NA"
    return "G_%s/I_%s" % (gb, ib)


def era_of(month: str) -> str:
    for name, lo, hi in ERAS:
        if lo <= month <= hi:
            return name
    return "OUT"


# ------------------------------------------------------- return builders ----
def price_return(p_prev, p_curr):
    if not is_fin(p_prev) or not is_fin(p_curr) or p_prev == 0:
        return NAN
    return p_curr / p_prev - 1.0


def cash_monthly(tb3ms_prev_pct):
    """Frozen Cash: simple accrual from previous month FRED TB3MS (% p.a.)."""
    if not is_fin(tb3ms_prev_pct):
        return NAN
    return tb3ms_prev_pct / 1200.0


def synthetic_bond_monthly_return(y_t, y_next, years: int):
    """Frozen par-bond synthetic total return (S2/S20/S10 structure).

    - y_t, y_next: decimal p.a. (e.g. 0.05 = 5%).
    - years: integer maturity at initiation (2, 10, 20).
    - Face 100, annual coupon c=100*y_t, semiannual c/2, N=2*years flows.
    - Hold one month; reprice remaining years-1/12 flows at y_next with
      half-year compounding extended to fractional exponents; dirty price
      (accrual embedded, no double-counted coupon cash); roll monthly.
    """
    if not is_fin(y_t) or not is_fin(y_next) or y_t < 0 or y_next < 0:
        return NAN
    if years <= 0:
        return NAN
    n = 2 * years
    coupon = 100.0 * y_t / 2.0
    per = y_next / 2.0
    pv = 0.0
    for k in range(1, n + 1):
        tau_years = k / 2.0 - 1.0 / 12.0
        periods = 2.0 * tau_years  # half-year periods (fractional allowed)
        df = (1.0 + per) ** (-periods) if (1.0 + per) > 0 else NAN
        if not is_fin(df):
            return NAN
        cf = coupon + (100.0 if k == n else 0.0)
        pv += cf * df
    return pv / 100.0 - 1.0


# -------------------------------------------------------------- metrics ----
def mean(xs):
    v = [x for x in xs if is_fin(x)]
    if not v:
        return NAN
    return sum(v) / len(v)


def median(xs):
    v = sorted(x for x in xs if is_fin(x))
    if not v:
        return NAN
    n = len(v)
    mid = n // 2
    if n % 2 == 1:
        return v[mid]
    return (v[mid - 1] + v[mid]) / 2.0


def biased_sd(xs):
    v = [x for x in xs if is_fin(x)]
    if not v:
        return NAN
    m = sum(v) / len(v)
    var = sum((x - m) ** 2 for x in v) / len(v)
    return math.sqrt(var)


def downside_dev(xs):
    """Frozen downside vol input: sqrt(mean(min(r,0)^2)) monthly."""
    v = [x for x in xs if is_fin(x)]
    if not v:
        return NAN
    return math.sqrt(sum(min(x, 0.0) ** 2 for x in v) / len(v))


def percentile(xs, q: float):
    """Linear-interpolation percentile, q in [0,1]. Frozen tail = q=0.10."""
    v = sorted(x for x in xs if is_fin(x))
    if not v:
        return NAN
    if len(v) == 1:
        return v[0]
    pos = q * (len(v) - 1)
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return v[int(pos)]
    frac = pos - lo
    return v[lo] * (1.0 - frac) + v[hi] * frac


def p10(xs):
    return percentile(xs, 0.10)


def compound(rs):
    p = 1.0
    for r in rs:
        if not is_fin(r):
            return NAN
        p *= 1.0 + r
    return p - 1.0


def geometric_excess(rs_sleeve, rs_cash):
    rs = compound(rs_sleeve)
    rc = compound(rs_cash)
    if not is_fin(rs) or not is_fin(rc):
        return NAN
    return (1.0 + rs) / (1.0 + rc) - 1.0


def build_episodes(months, states):
    """Contiguous same-state episodes over calendar-ordered months.

    months: list of YYYY-MM-01 strings in calendar order (macro-valid only).
    states: parallel list of 3x3 state strings.
    Returns list of (start_idx, end_idx, state).
    A gap in calendar continuity breaks episodes (caller must only pass
    consecutive calendar months; any missing calendar month splits input).
    """
    eps = []
    if not months:
        return eps
    s, e = 0, 0
    for k in range(1, len(months)):
        if states[k] == states[s] and _cal_next(months[k - 1]) == months[k]:
            e = k
        else:
            eps.append((s, e, states[s]))
            s, e = k, k
    eps.append((s, e, states[s]))
    return eps


def _cal_next(mo: str) -> str:
    y, m = int(mo[:4]), int(mo[5:7])
    m += 1
    if m > 12:
        m = 1
        y += 1
    return "%04d-%02d-01" % (y, m)


# ------------------------------------------------------- classification ----
def classify_evidence(n_m, n_e, mean_ex, pos_m_frac, ep_hit, p10_ex, worst_m,
                      p_under, persistent_positive, persistent_negative):
    if n_m < 24 or n_e < 4:
        return "insufficient_sample"
    if (is_fin(mean_ex) and mean_ex > 0.001
            and is_fin(pos_m_frac) and pos_m_frac >= 0.55
            and is_fin(ep_hit) and ep_hit >= 0.60
            and is_fin(p10_ex) and p10_ex >= -0.04
            and is_fin(worst_m) and worst_m > -0.20
            and not persistent_negative):
        return "historically_favored"
    if (is_fin(mean_ex) and mean_ex < -0.0005
            and (is_fin(pos_m_frac) and pos_m_frac <= 0.45
                 or is_fin(ep_hit) and ep_hit <= 0.40)
            and (is_fin(p10_ex) and p10_ex <= -0.03
                 or is_fin(worst_m) and worst_m <= -0.10
                 or is_fin(p_under) and p_under >= 0.60)
            and not persistent_positive):
        return "historically_unfavorable"
    return "mixed"


def zero_candidate(eligible: str, evidence: str, n_m, n_e, ep_hit, mean_ex,
                   p10_ex, worst_ep, p_material_monthly,
                   persistent_positive, ex_worst_mean_ex) -> bool:
    if eligible not in ("eligible_primary", "eligible_with_limitation"):
        return False
    if evidence != "historically_unfavorable":
        return False
    if not (n_m >= 60 and n_e >= 6):
        return False
    if not (is_fin(ep_hit) and ep_hit <= 0.40):
        return False
    if not (is_fin(mean_ex) and mean_ex < 0):
        return False
    tail = ((is_fin(p10_ex) and p10_ex <= -0.04)
            or (is_fin(worst_ep) and worst_ep <= -0.15)
            or (is_fin(p_material_monthly) and p_material_monthly >= 0.10))
    if not tail:
        return False
    if persistent_positive:
        return False
    if not (is_fin(ex_worst_mean_ex) and ex_worst_mean_ex < 0):
        return False
    return True
