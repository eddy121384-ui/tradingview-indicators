#!/usr/bin/env python3
"""Issue #160 — Deep-History Growth/Inflation v0.1 builder + overlap validation.

Frozen implementation of:
  indicators/macro-pressure-map/research/issue-160-deep-history-v01-prereg.md

Pure standard library (no numpy/pandas) so the frozen record runs anywhere.
Ports: the executed Node mirror implements the same frozen formulas; results
reported in the finding were produced before any redesign window.

Pipeline (post-prereg only):
  1. Read raw MCP fetch JSON: {TICKER: {desc, unit, count, data: "YYYY-MM-DD:value,..."}}.
     The JSON is the verbatim TradingView Official MCP payload
     (mcp-tv-get-economic-data, date_from=1960-01-01); per-ticker SHA256 hashes
     of the compact strings are recorded, never re-fetched here.
  2. Build the 10 frozen roles and the frozen 60-month pressure scores.
  3. Write the monthly CSV (all union months; NaN composites where the
     all-5-finite rule fails).
  4. Load ONLY date/GPI/IPI/regime from the frozen Issue #133 snapshot after
     verifying its SHA256. Never load asset-return panels (there are none in
     the snapshot; no other outcome file may be added).
  5. Compute ONLY the preregistered metrics, apply ALL 12 gates exactly,
     write the overlap JSON. No rescue, no retuning.

Firewall: outcome_data_loaded=false, production_authorized=false.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import sys

# ---------------------------------------------------------------- frozen ----
LOOKBACK = 60
SMA_FAST = 3
SMA_SLOW = 12
W_LEVEL = 0.5
W_MOM = 0.3
W_DIR = 0.2
STATE_LO = -10.0
STATE_HI = 10.0
EXACT_WINDOW_START = "2007-01-01"
SNAPSHOT_SHA256 = "1d03923503e7fe82a69b033897484c48aa646279ecf70164d090ed62a5a70719"
R7_LABEL = "Slowdown / Disinflation"

T_G1 = "ECONOMICS:USIPYY"
T_G2 = "ECONOMICS:USUR"
T_BP = "ECONOMICS:USBP"
T_DPI = "ECONOMICS:USDPI"
T_PCEPI = "ECONOMICS:USPCEPI"
T_G5 = "ECONOMICS:USMNO"
T_I1 = "ECONOMICS:USIRYY"
T_I2 = "ECONOMICS:USCPCEPIAC"
T_I3 = "ECONOMICS:USPPIYY"
T_I4 = "ECONOMICS:USWG"
T_I5 = "ECONOMICS:USEI"

NAN = float("nan")


def is_fin(x) -> bool:
    return x is not None and not (isinstance(x, float) and math.isnan(x))


# ------------------------------------------------------------ primitives ----
def mean_sd_biased(vals):
    n = len(vals)
    mean = sum(vals) / n
    var = sum((v - mean) ** 2 for v in vals) / n
    return mean, math.sqrt(var)


def last_valid(xs, i, k):
    out = []
    j = i
    while j >= 0 and len(out) < k:
        if is_fin(xs[j]):
            out.append(xs[j])
        j -= 1
    return out


def sma_last(xs, i, k):
    w = last_valid(xs, i, k)
    if len(w) < k:
        return NAN
    return sum(w) / k


def pressure_score(xs, lookback=LOOKBACK, sma_fast=SMA_FAST, sma_slow=SMA_SLOW):
    """Frozen monthly pressure score (prereg section 2).

    Absolute 1M/3M changes (never percentage ROC on rate series), 0.6/0.4
    momentum blend, biased rolling sds, tanh direction, 0.5/0.3/0.2 blend,
    100*tanh(raw/2). Positional lags; a missing neighbor yields missing
    momentum (no interpolation). Rolling windows skip missing values and use
    only months <= t (no future data).
    """
    n = len(xs)
    mom = [NAN] * n
    for i in range(n):
        if not is_fin(xs[i]):
            continue
        d1 = xs[i] - xs[i - 1] if i - 1 >= 0 and is_fin(xs[i - 1]) else NAN
        d3 = xs[i] - xs[i - 3] if i - 3 >= 0 and is_fin(xs[i - 3]) else NAN
        if is_fin(d1) and is_fin(d3):
            mom[i] = 0.6 * d1 + 0.4 * (d3 / 3.0)
    out = [NAN] * n
    for i in range(n):
        if not is_fin(xs[i]) or not is_fin(mom[i]):
            continue
        lv = last_valid(xs, i, lookback)
        mv = last_valid(mom, i, lookback)
        if len(lv) < lookback or len(mv) < lookback:
            continue
        mL, sL = mean_sd_biased(lv)
        mM, sM = mean_sd_biased(mv)
        if sL == 0.0 or sM == 0.0:
            continue
        s3 = sma_last(xs, i, sma_fast)
        s12 = sma_last(xs, i, sma_slow)
        if not is_fin(s3) or not is_fin(s12):
            continue
        lz = (xs[i] - mL) / sL
        mz = (mom[i] - mM) / sM
        direction = math.tanh((s3 - s12) / sL)
        raw = W_LEVEL * lz + W_MOM * mz + W_DIR * direction
        out[i] = 100.0 * math.tanh(raw / 2.0)
    return out


def shift_month(mo: str, d: int) -> str:
    y, m = int(mo[:4]), int(mo[5:7])
    m += d
    while m < 1:
        m += 12
        y -= 1
    while m > 12:
        m -= 12
        y += 1
    return f"{y:04d}-{m:02d}-01"


def parse_compact(data: str):
    months, vals = [], []
    for kv in data.split(","):
        d, v = kv.split(":")
        months.append(d)
        vals.append(float(v))
    return months, vals


# ------------------------------------------------------------------ build ----
def build_roles(raw: dict):
    """Return (months, X) with the 10 frozen economically-signed role series."""
    maps = {}
    for t, e in raw.items():
        months, vals = parse_compact(e["data"])
        maps[t] = dict(zip(months, vals))
    months = sorted({m for mp in maps.values() for m in mp})

    def get(t, mo):
        v = maps[t].get(mo)
        return NAN if v is None else v

    X = {k: [] for k in ("G1", "G2", "G3", "G4", "G5", "I1", "I2", "I3", "I4", "I5")}
    for mo in months:
        X["G1"].append(get(T_G1, mo))
        X["G2"].append(get(T_G2, mo))
        bp, bp12 = get(T_BP, mo), maps[T_BP].get(shift_month(mo, -12))
        X["G3"].append(NAN if not is_fin(bp) or bp12 is None or bp12 == 0 else 100.0 * (bp - bp12) / bp12)
        num, den = get(T_DPI, mo), get(T_PCEPI, mo)
        num12, den12 = maps[T_DPI].get(shift_month(mo, -12)), maps[T_PCEPI].get(shift_month(mo, -12))
        r = num / den if is_fin(num) and is_fin(den) and den != 0 else NAN
        r12 = num12 / den12 if num12 is not None and den12 is not None and den12 != 0 else NAN
        X["G4"].append(NAN if not is_fin(r) or not is_fin(r12) or r12 == 0 else 100.0 * (r - r12) / r12)
        X["G5"].append(get(T_G5, mo))
        X["I1"].append(get(T_I1, mo))
        X["I2"].append(get(T_I2, mo))
        X["I3"].append(get(T_I3, mo))
        X["I4"].append(get(T_I4, mo))
        X["I5"].append(get(T_I5, mo))
    return months, X


def build_monthly(raw: dict):
    months, X = build_roles(raw)
    S = {k: pressure_score(v) for k, v in X.items()}
    S["G2"] = [-v if is_fin(v) else NAN for v in S["G2"]]  # frozen G2 inversion
    rows = []
    for i, mo in enumerate(months):
        g = [S[k][i] for k in ("G1", "G2", "G3", "G4", "G5")]
        f = [S[k][i] for k in ("I1", "I2", "I3", "I4", "I5")]
        G = sum(g) / 5.0 if all(is_fin(v) for v in g) else NAN
        I = sum(f) / 5.0 if all(is_fin(v) for v in f) else NAN
        rows.append((mo, G, I, g, f))
    return rows


# ----------------------------------------------------------------- metrics ----
def pearson(a, b):
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    s = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    sa = sum((x - ma) ** 2 for x in a)
    sb = sum((y - mb) ** 2 for y in b)
    return s / math.sqrt(sa * sb)


def ranks(v):
    order = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r


def spearman(a, b):
    return pearson(ranks(a), ranks(b))


def sgn(x):
    return 1 if x > 0 else (-1 if x < 0 else 0)


def direction_agreement(a, b):
    agree = n = 0
    for i in range(1, len(a)):
        da, db = a[i] - a[i - 1], b[i] - b[i - 1]
        n += 1
        if sgn(da) == sgn(db):
            agree += 1
    return agree / n if n else NAN


def axis_state(s):
    if s < STATE_LO:
        return -1
    if s > STATE_HI:
        return 1
    return 0


def state_agreement(a, b):
    return sum(1 for x, y in zip(a, b) if axis_state(x) == axis_state(y)) / len(a)


def core_regime(g, i):
    """Verbatim port of v6_6_core.core_regime (thresholds +/-10)."""
    gp, gn = g > 10.0, g < -10.0
    ip, inn = i > 10.0, i < -10.0
    if gp and inn:
        return "Goldilocks / Disinflationary Expansion"
    if gp and not ip and not inn:
        return "Benign Expansion / Stable Inflation"
    if gp and ip:
        return "Reflation / Inflation Rising"
    if not gp and not gn and inn:
        return "Disinflationary Drift"
    if not gp and not gn and not ip and not inn:
        return "Neutral / Range-bound Macro"
    if not gp and not gn and ip:
        return "Inflation Pressure without Growth Confirmation"
    if gn and inn:
        return R7_LABEL
    if gn and not ip and not inn:
        return "Growth Slowdown / Stable Inflation"
    return "Stagflation Pressure"


def axis_turns(vals):
    """Frozen Issue #136 turn rule: dX_t > 0 and dX_{t-1} <= 0, no magnitude gate."""
    t = [False] * len(vals)
    for i in range(2, len(vals)):
        d = vals[i] - vals[i - 1]
        dp = vals[i - 1] - vals[i - 2]
        if math.isnan(d) or math.isnan(dp):
            continue
        t[i] = d > 0 and dp <= 0
    return t


def first_triggers(grid):
    """grid: list of dicts(date, g, i, r7) on consecutive calendar months.

    Frozen R7_ASYNC_TURN: r7 at t, axis turns within {t, t-1, t-2} on both
    axes; first trigger per contiguous R7 episode only.
    """
    tg = axis_turns([r["g"] for r in grid])
    ti = axis_turns([r["i"] for r in grid])
    out = []
    k = 0
    while k < len(grid):
        if not grid[k]["r7"]:
            k += 1
            continue
        j = k
        while j < len(grid) and grid[j]["r7"]:
            j += 1
        for t in range(k, j):
            g_hit = any(u >= 0 and tg[u] for u in (t - 2, t - 1, t))
            i_hit = any(u >= 0 and ti[u] for u in (t - 2, t - 1, t))
            if g_hit and i_hit:
                out.append(grid[t]["date"])
                break
        k = j
    return out


def month_diff(a, b):
    return (int(b[:4]) - int(a[:4])) * 12 + (int(b[5:7]) - int(a[5:7]))


def greedy_match(ref, pred, tol=3):
    used, matched, lags = set(), 0, []
    for r in sorted(ref):
        best, best_lag = None, 10**9
        for p in sorted(pred):
            if p in used:
                continue
            lag = abs(month_diff(r, p))
            if lag <= tol and lag < best_lag:
                best, best_lag = p, lag
        if best is not None:
            used.add(best)
            matched += 1
            lags.append(best_lag)
    lags.sort()
    if lags:
        mid = len(lags) // 2
        med = float(lags[mid]) if len(lags) % 2 else (lags[mid - 1] + lags[mid]) / 2.0
    else:
        med = NAN
    return matched, med


def evaluate_overlap(dh_rows, snap_rows):
    """dh_rows: (date, G, I); snap_rows: dicts(date, gpi, ipi, regime).

    Returns (overlap_list, metrics, v_trig, d_trig).
    """
    dh_full = {d: (G, I) for d, G, I in dh_rows if is_fin(G) and is_fin(I)}
    ov = []
    for s in snap_rows:
        if s["date"] < EXACT_WINDOW_START:
            continue
        key = s["date"][:7]
        hit = [d for d in dh_full if d[:7] == key]
        if not hit:
            continue
        G, I = dh_full[hit[0]]
        ov.append({"date": s["date"], "gpi": s["gpi"], "ipi": s["ipi"],
                   "regime": s["regime"], "G": G, "I": I})
    G = [r["G"] for r in ov]
    P = [r["gpi"] for r in ov]
    FI = [r["I"] for r in ov]
    Q = [r["ipi"] for r in ov]
    m = {
        "n": len(ov),
        "growth_pearson": pearson(G, P),
        "growth_spearman": spearman(G, P),
        "infl_pearson": pearson(FI, Q),
        "infl_spearman": spearman(FI, Q),
        "growth_dir": direction_agreement(G, P),
        "infl_dir": direction_agreement(FI, Q),
        "growth_state3": state_agreement(G, P),
        "infl_state3": state_agreement(FI, Q),
        "regime3x3": sum(1 for r in ov if axis_state(r["G"]) == axis_state(r["gpi"])
                         and axis_state(r["I"]) == axis_state(r["ipi"])) / len(ov),
    }
    ref_r7 = {r["date"] for r in ov if r["regime"] == 7}
    pred_r7 = {r["date"] for r in ov if core_regime(r["G"], r["I"]) == R7_LABEL}
    tp = len(ref_r7 & pred_r7)
    m.update({"r7_ref_n": len(ref_r7), "r7_pred_n": len(pred_r7), "r7_tp": tp,
              "r7_precision": tp / len(pred_r7) if pred_r7 else NAN,
              "r7_recall": tp / len(ref_r7) if ref_r7 else NAN})
    v_grid = [{"date": s["date"], "g": s["gpi"], "i": s["ipi"], "r7": s["regime"] == 7}
              for s in snap_rows]
    d_all = [{"date": d, "g": Gv, "i": Iv,
              "r7": core_regime(Gv, Iv) == R7_LABEL} for d, Gv, Iv in dh_rows]
    ov_months = {r["date"][:7] for r in ov}
    v_trig = sorted(t for t in first_triggers(v_grid) if t[:7] in ov_months)
    d_trig = sorted(t for t in first_triggers(d_all) if t[:7] in ov_months)
    matched, med = greedy_match(v_trig, d_trig)
    prec = matched / len(d_trig) if d_trig else NAN
    rec = matched / len(v_trig) if v_trig else NAN
    f1 = (2 * prec * rec / (prec + rec)) if is_fin(prec) and is_fin(rec) and (prec + rec) > 0 else NAN
    m.update({"trig_ref_n": len(v_trig), "trig_pred_n": len(d_trig),
              "trig_matched": matched, "trig_precision": prec, "trig_recall": rec,
              "trig_f1": f1,
              "trig_count_ratio": len(d_trig) / len(v_trig) if v_trig else NAN,
              "trig_median_lag": med})
    for nm, a, b in (("2008-2016", "2008-01-01", "2016-12-31"),
                     ("2017-2019", "2017-01-01", "2019-12-31"),
                     ("2020-2022", "2020-01-01", "2022-12-31"),
                     ("2023-2026-08", "2023-01-01", "2026-08-31")):
        s = [r for r in ov if a <= r["date"] <= b]
        ag = sum(1 for r in s if axis_state(r["G"]) == axis_state(r["gpi"])
                 and axis_state(r["I"]) == axis_state(r["ipi"]))
        m["sub_" + nm] = ag / len(s) if s else NAN
        m["sub_" + nm + "_n"] = len(s)
    gates = [
        m["n"] >= 180,
        m["growth_spearman"] >= 0.50,
        m["infl_spearman"] >= 0.50,
        m["growth_dir"] >= 0.60,
        m["infl_dir"] >= 0.60,
        m["regime3x3"] >= 0.55,
        m["r7_precision"] >= 0.60,
        m["r7_recall"] >= 0.60,
        m["trig_f1"] >= 0.60,
        is_fin(m["trig_count_ratio"]) and 0.50 <= m["trig_count_ratio"] <= 2.00,
        is_fin(m["trig_median_lag"]) and m["trig_median_lag"] <= 2,
        all(m["sub_" + nm] >= 0.45 for nm in ("2008-2016", "2017-2019", "2020-2022", "2023-2026-08")),
    ]
    m["gates"] = gates
    if not gates[0]:
        m["verdict"] = "deep_history_v01_overlap_inconclusive_sample"
    elif all(gates):
        m["verdict"] = "deep_history_v01_overlap_passed"
    else:
        m["verdict"] = "deep_history_v01_overlap_failed"
    return ov, m, v_trig, d_trig


# ------------------------------------------------------------------- main ----
def main(raw_path, snapshot_path, out_monthly, out_overlap):
    with open(raw_path, encoding="utf-8") as f:
        raw = json.load(f)
    with open(snapshot_path, "rb") as f:
        snap_bytes = f.read()
    digest = hashlib.sha256(snap_bytes).hexdigest()
    if digest != SNAPSHOT_SHA256:
        raise SystemExit(f"snapshot SHA256 mismatch: {digest}")
    text = snap_bytes.decode("utf-8").splitlines()
    header = text[0].split(",")
    if header != ["date", "gpi", "ipi", "regime"]:
        raise SystemExit(f"unexpected snapshot header: {header}")
    snap_rows = []
    for line in text[1:]:
        if not line.strip():
            continue
        d, g, i, r = line.split(",")
        snap_rows.append({"date": d, "gpi": float(g), "ipi": float(i), "regime": int(r)})
    gaps = [f"{a['date']}->{b['date']}" for a, b in zip(snap_rows, snap_rows[1:])
            if month_diff(a["date"], b["date"]) != 1]

    rows = build_monthly(raw)
    with open(out_monthly, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "growth_dh", "inflation_dh",
                    "g1", "g2", "g3", "g4", "g5", "i1", "i2", "i3", "i4", "i5"])
        for mo, G, I, g, fc in rows:
            w.writerow([mo,
                        "" if math.isnan(G) else repr(G),
                        "" if math.isnan(I) else repr(I)]
                       + [("" if math.isnan(v) else repr(v)) for v in g]
                       + [("" if math.isnan(v) else repr(v)) for v in fc])

    ov, m, v_trig, d_trig = evaluate_overlap(
        [(mo, G, I) for mo, G, I, _, _ in rows], snap_rows)
    payload = {
        "issue": 160,
        "prereg": "indicators/macro-pressure-map/research/issue-160-deep-history-v01-prereg.md",
        "snapshot_sha256": SNAPSHOT_SHA256,
        "snapshot_rows": len(snap_rows),
        "snapshot_gaps": gaps,
        "overlap_first": ov[0]["date"],
        "overlap_last": ov[-1]["date"],
        "metrics": m,
        "v66_triggers": v_trig,
        "dh_triggers": d_trig,
        "outcome_data_loaded": False,
        "production_authorized": False,
        "sample_note": "repeated robustness validation; NOT an untouched holdout",
    }
    with open(out_overlap, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1)
    print(json.dumps({"metrics": m, "verdict": m["verdict"]}, indent=1))


if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit("usage: issue_160_deep_history_v01.py <raw.json> <snapshot.csv> <out_monthly.csv> <out_overlap.json>")
    main(*sys.argv[1:5])
