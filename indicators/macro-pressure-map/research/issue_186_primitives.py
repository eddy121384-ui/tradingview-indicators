#!/usr/bin/env python3
"""Issue #186 — frozen turning-lag primitives (stdlib only, pure functions).

Mirrors the prereg verbatim. Tested by test_issue_186_primitives.py and the
Node mirror. No file I/O, no network, no optimization.
"""

THRESH_20 = 0.20
THRESH_10 = 0.10
MOVE_PP = 5.0
MOVE_PP_SENS = 10.0
WINDOW = 12
ALREADY_DEFENSIVE = 27.5
ALREADY_EXPOSED = 52.5


def extract_bears(months, closes, thresh=THRESH_20):
    """Deterministic peak/trough extractor (prereg section 4).

    months: ordered month keys (YYYY-MM). closes: aligned floats.
    Returns list of dicts {peak_i, trough_i, rec_i or None, severity,
    censored}. Non-overlapping; resume at recovery month.
    """
    n = len(months)
    events = []
    i = 0
    # running peak from current search start
    while i < n:
        # find running peak: max close in [i, ...) tracked incrementally
        peak_i = i
        peak_p = closes[i]
        j = i + 1
        found = None
        while j < n:
            if closes[j] > peak_p:
                peak_p = closes[j]
                peak_i = j
            elif closes[j] <= (1 - thresh) * peak_p:
                # confirm: trough = min in [peak_i, recovery)
                # find recovery: first k>j with close >= peak_p
                rec = None
                for k in range(j + 1, n):
                    if closes[k] > peak_p:
                        # earliest peak month on ties handled by strict >
                        pass
                    if closes[k] >= peak_p:
                        rec = k
                        break
                if rec is None:
                    seg = closes[peak_i:]
                    trel = min(range(len(seg)), key=lambda t: seg[t])
                    events.append({"peak_i": peak_i, "trough_i": peak_i + trel,
                                   "rec_i": None, "severity": seg[trel] / peak_p - 1,
                                   "censored": True})
                    return events
                seg = closes[peak_i:rec]
                trel = min(range(len(seg)), key=lambda t: seg[t])
                # earliest peak on ties: first index attaining max in [i, rec)
                pre = closes[i:rec]
                pmax = max(pre)
                peak_rel = next(t for t in range(len(pre)) if pre[t] == pmax)
                peak_i2 = i + peak_rel
                seg2 = closes[peak_i2:rec]
                trel2 = min(range(len(seg2)), key=lambda t: seg2[t])
                events.append({"peak_i": peak_i2, "trough_i": peak_i2 + trel2,
                               "rec_i": rec, "severity": seg2[trel2] / closes[peak_i2] - 1,
                               "censored": False})
                found = rec
                break
            j += 1
        if found is None:
            break
        i = found  # resume AT recovery month (months <= recovery excluded)
        # advance at least one step to avoid re-trigger on same peak
        i += 1
    return events


def month_diff(a, b):
    """Calendar months b - a for YYYY-MM strings (b later => positive)."""
    return (int(b[:4]) - int(a[:4])) * 12 + (int(b[5:7]) - int(a[5:7]))


def match_peak(T, emonths, E, thresh=MOVE_PP):
    """Prereg section 6 peak matching. emonths: E_t timeline month keys
    (YYYY-MM-01 or YYYY-MM); E: aligned equity targets (pp units).
    Returns (label, lag_or_None, action_month_or_None)."""
    idx = {m[:7]: i for i, m in enumerate(emonths)}
    if T not in idx:
        return ("censored_edge", None, None)
    ti = idx[T]
    dE = [0.0] + [E[i] - E[i - 1] for i in range(1, len(E))]
    # pre-window candidates [T-12, T]
    best = None
    for m in range(max(1, ti - WINDOW), ti + 1):
        if dE[m] <= -thresh and E[ti] <= E[m - 1] - thresh:
            best = m
    if best is not None:
        return ("early_protection", month_diff(T, emonths[best][:7]), emonths[best])
    for m in range(ti + 1, min(len(E), ti + 1 + WINDOW)):
        if dE[m] <= -thresh:
            return ("late_protection", month_diff(T, emonths[m][:7]), emonths[m])
    if E[ti] <= ALREADY_DEFENSIVE:
        return ("already_defensive", None, None)
    if ti < WINDOW or ti + WINDOW >= len(E):
        return ("censored_edge", None, None)
    return ("no_action", None, None)


def match_trough(T, emonths, E, thresh=MOVE_PP):
    idx = {m[:7]: i for i, m in enumerate(emonths)}
    if T not in idx:
        return ("censored_edge", None, None)
    ti = idx[T]
    dE = [0.0] + [E[i] - E[i - 1] for i in range(1, len(E))]
    best = None
    for m in range(max(1, ti - WINDOW), ti + 1):
        if m > 0 and dE[m] >= thresh and E[ti] >= E[m - 1] + thresh:
            best = m
    if best is not None:
        return ("early_re-risk", month_diff(T, emonths[best][:7]), emonths[best])
    for m in range(ti + 1, min(len(E), ti + 1 + WINDOW)):
        if dE[m] >= thresh:
            return ("late_re-risk", month_diff(T, emonths[m][:7]), emonths[m])
    if E[ti] >= ALREADY_EXPOSED:
        return ("already_exposed", None, None)
    if ti < WINDOW or ti + WINDOW >= len(E):
        return ("censored_edge", None, None)
    return ("no_action", None, None)


def drawdown_before_action(p_peak, p_action, p_trough):
    denom = p_peak - p_trough
    if denom == 0:
        return float("nan")
    return (p_peak - p_action) / denom


def rebound_fraction(p_action, p_trough, p_ref):
    denom = p_ref - p_trough
    if denom == 0:
        return float("nan")
    return (p_action - p_trough) / denom


def median(xs):
    v = sorted(x for x in xs if x == x)
    if not v:
        return float("nan")
    n = len(v)
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2


def pct(xs, q):
    v = sorted(x for x in xs if x == x)
    if not v:
        return float("nan")
    pos = q / 100 * (len(v) - 1)
    lo, hi = int(pos), min(int(pos) + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (pos - lo)


def turning_verdict(med_peak_lag, med_trough_lag, med_dd_before, n_events):
    """Prereg section 11 decision tree (all inputs post-computation)."""
    if n_events < 4:
        return "deep_history_timing_not_assessable"
    late = (med_peak_lag >= 4) or (med_trough_lag >= 6) or (med_dd_before >= 0.60)
    ok = (med_peak_lag <= 2) and (med_trough_lag <= 4)
    if late and not ok:
        # mixed iff one side acceptable while the other is late
        peak_ok, trough_ok = med_peak_lag <= 2, med_trough_lag <= 4
        if peak_ok != trough_ok:
            return "deep_history_timing_mixed_by_cycle"
        return "deep_history_timing_materially_late"
    if ok:
        return "deep_history_timing_acceptable_with_limitations"
    return "deep_history_timing_mixed_by_cycle"
