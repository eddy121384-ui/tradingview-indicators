#!/usr/bin/env python3
"""Issue #171 — cross-layer recovery divergence autopsy (frozen evaluator).

Frozen implementation of the Issue #171 contract: reconstruct the frozen
Deep-History (#160/#167 rule) and exact-V6.6 (#169 rule) recovery layers,
classify cross-layer events over common months with the frozen +/-3M window,
decompose divergence into state-vs-trajectory causes with deterministic
labels, quantify Growth-vs-Inflation contribution, profile lead/lag, and
attribute Deep-History components. Pure standard library (no numpy/pandas).

SIGNAL ONLY: inputs are the frozen DH monthly CSV (macro scores, incl.
G1-G5/I1-I5) and the frozen #133 snapshot (date/GPI/IPI). Asset-return files
are never opened. No thresholds, lookbacks, windows, weights, or labels
herein may be altered; any redesign belongs in a new issue.
"""

from __future__ import annotations

import base64
import csv
import gzip
import hashlib
import json
import math
import sys

# ---------------------------------------------------------------- frozen ----
STATE_HI = 10.0
MATCH_WINDOW = 3
DH_CSV_SHA256 = "42516418ec8d1ce981d1b4bc05e2ae86809d6acbf5de63dccbad515db507dcfc"
SNAPSHOT_SHA256 = "1d03923503e7fe82a69b033897484c48aa646279ecf70164d090ed62a5a70719"
GROWTH_COMPS = ("g1", "g2", "g3", "g4", "g5")
INFL_COMPS = ("i1", "i2", "i3", "i4", "i5")

NAN = float("nan")


def is_fin(x) -> bool:
    return x is not None and not (isinstance(x, float) and math.isnan(x))


def sgn_nz(x):
    if not is_fin(x) or x == 0.0:
        return "na"
    return 1 if x > 0 else -1


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


def mo_diff(a: str, b: str) -> int:
    return (int(b[:4]) - int(a[:4])) * 12 + (int(b[5:7]) - int(a[5:7]))


def median(xs):
    s = sorted(xs)
    m = len(s) >> 1
    return s[m] if len(s) % 2 else (s[m - 1] + s[m]) / 2.0


def mean(xs):
    return sum(xs) / len(xs)


# ------------------------------------------------------------------ inputs ----
def load_dh_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    out = {}
    for r in rows:
        rec = {}
        for k in ("growth_dh", "inflation_dh") + GROWTH_COMPS + INFL_COMPS:
            rec[k] = float(r[k]) if r[k] != "" else NAN
        out[r["date"]] = rec
    return out


def load_snapshot_b64(path):
    with open(path, encoding="ascii") as f:
        raw = gzip.decompress(base64.b64decode("".join(f.read().split())))
    digest = hashlib.sha256(raw).hexdigest()
    if digest != SNAPSHOT_SHA256:
        raise SystemExit(f"snapshot SHA256 mismatch: {digest}")
    rows = []
    for line in raw.decode("utf-8").splitlines()[1:]:
        if not line.strip():
            continue
        d, g, i, r = line.split(",")
        rows.append({"date": d[:7] + "-01", "gpi": float(g), "ipi": float(i),
                     "regime": int(r), "month_end": d})
    return rows


# ------------------------------------------------------------------ layers ----
def build_layer(months, get_g, get_i):
    val = {m: (get_g(m), get_i(m)) for m in months}
    st = []
    for m in months:
        G, I = val[m]
        elig = is_fin(G) and is_fin(I) and G <= STATE_HI and I <= STATE_HI
        pm = shift_month(m, -3)
        if pm in val:
            G0, I0 = val[pm]
            d3g = G - G0 if is_fin(G) and is_fin(G0) else NAN
            d3i = I - I0 if is_fin(I) and is_fin(I0) else NAN
        else:
            d3g = d3i = NAN
        st.append({"m": m, "G": G, "I": I, "elig": elig, "d3G": d3g, "d3I": d3i,
                   "qual": elig and is_fin(d3g) and is_fin(d3i) and d3g > 0 and d3i > 0})
    episodes, cur = [], None
    for i, s in enumerate(st):
        if s["elig"]:
            if cur is None:
                cur = {"idx": []}
            cur["idx"].append(i)
        elif cur is not None:
            episodes.append(cur)
            cur = None
    if cur is not None:
        episodes.append(cur)
    triggers = []
    for ei, e in enumerate(episodes):
        for i in e["idx"]:
            if st[i]["qual"]:
                triggers.append({"ep": ei, "idx": i, "date": st[i]["m"]})
                e["trigger"] = i
                break
    return st, episodes, triggers


# --------------------------------------------------------------- classify ----
def classify(dh_trig, ex_trig):
    pairs = []
    for d in dh_trig:
        for e in ex_trig:
            lag = abs(mo_diff(d["date"], e["date"]))
            if lag <= MATCH_WINDOW:
                pairs.append((lag, d["date"], e["date"]))
    pairs.sort(key=lambda p: (p[0], p[1], p[2]))
    used_d, used_e, matched = set(), set(), []
    for lag, dd, ee in pairs:
        if dd in used_d or ee in used_e:
            continue
        used_d.add(dd)
        used_e.add(ee)
        signed = mo_diff(dd, ee)
        matched.append({"dh": dd, "exact": ee, "lag": lag, "signed": signed,
                        "first": "DH" if signed > 0 else ("EXACT" if signed < 0 else "same")})
    dh_only = [t for t in dh_trig if t["date"] not in used_d]
    ex_only = [t for t in ex_trig if t["date"] not in used_e]
    return matched, dh_only, ex_only


# --------------------------------------------------------------- decompose ----
def attribute_label(state_mm, grow_mm, infl_mm):
    gm = grow_mm is True
    im = infl_mm is True
    if not state_mm and not gm and not im:
        return "timing_only"
    if state_mm and not gm and not im:
        return "state_only"
    if not state_mm and gm and not im:
        return "growth_trajectory_only"
    if not state_mm and not gm and im:
        return "inflation_trajectory_only"
    if not state_mm and gm and im:
        return "both_trajectories"
    if state_mm and gm and not im:
        return "state_plus_growth"
    if state_mm and not gm and im:
        return "state_plus_inflation"
    if state_mm and gm and im:
        return "state_plus_both"
    return "timing_only"  # unreachable; keeps the function total


def decompose_event(kind, dh_date, ex_date, dh_at, ex_at):
    if kind == "MATCHED":
        m0 = dh_date if mo_diff(dh_date, ex_date) <= 0 else ex_date
    else:
        m0 = dh_date or ex_date
    A, B = dh_at(m0), ex_at(m0)
    state_mm = A["elig"] != B["elig"]
    ga, gb = sgn_nz(A["d3G"]), sgn_nz(B["d3G"])
    ia, ib = sgn_nz(A["d3I"]), sgn_nz(B["d3I"])
    grow_mm = "na" if ga == "na" or gb == "na" else (ga != gb)
    infl_mm = "na" if ia == "na" or ib == "na" else (ia != ib)
    na = grow_mm == "na" or infl_mm == "na"
    label = attribute_label(state_mm, grow_mm, infl_mm)
    stale = kind != "MATCHED" and not state_mm and grow_mm is False and infl_mm is False
    return {"m0": m0, "dh_elig": A["elig"], "ex_elig": B["elig"],
            "G_DH": A["G"], "G_EX": B["G"], "I_DH": A["I"], "I_EX": B["I"],
            "d3G_DH": A["d3G"], "d3G_EX": B["d3G"],
            "d3I_DH": A["d3I"], "d3I_EX": B["d3I"],
            "grow_mm": grow_mm, "infl_mm": infl_mm, "na": na,
            "label": label, "stale": stale}


def axis_involved(dh_val, ex_val, traj_mm, thresh=STATE_HI):
    se = None if not is_fin(dh_val) or not is_fin(ex_val) \
        else ((dh_val <= thresh) != (ex_val <= thresh))
    if se is None or traj_mm == "na":
        return "na"
    return se or traj_mm


def decide_verdict(growth_frac, infl_frac, determinate_frac):
    if determinate_frac < 2.0 / 3.0:
        return "cross_layer_divergence_insufficient_component_evidence"
    if growth_frac >= 0.60 and infl_frac < 0.40:
        return "cross_layer_divergence_growth_dominant"
    if infl_frac >= 0.60 and growth_frac < 0.40:
        return "cross_layer_divergence_inflation_dominant"
    return "cross_layer_divergence_joint_and_rotating"


# ---------------------------------------------------------------- lead/lag ----
def consecutive_grid(value_map, lo, hi):
    grid, mo = [], lo
    while mo <= hi:
        v = value_map.get(mo, NAN)
        grid.append((mo, v))
        mo = shift_month(mo, 1)
    return grid


def positive_d3_onsets(grid):
    d3 = []
    for i, (d, v) in enumerate(grid):
        if i >= 3 and is_fin(v) and is_fin(grid[i - 3][1]):
            d3.append((d, v - grid[i - 3][1]))
        else:
            d3.append((d, NAN))
    out = []
    for i in range(1, len(grid)):
        a, b = d3[i - 1][1], d3[i][1]
        if is_fin(a) and is_fin(b) and b > 0 and a <= 0:
            out.append(grid[i][0])
    return out


def nearest_profile(dh_onsets, ex_onsets):
    prof = []
    for d in dh_onsets:
        best, bd = None, 10 ** 9
        for e in ex_onsets:
            lag = mo_diff(d, e)
            if abs(lag) < abs(bd):
                bd, best = lag, e
        prof.append({"dh": d, "ex": best, "lag": bd})
    lags = [p["lag"] for p in prof]
    return {"n": len(prof),
            "dh_first": sum(1 for l in lags if l > 0),
            "same": sum(1 for l in lags if l == 0),
            "ex_first": sum(1 for l in lags if l < 0),
            "median": median(lags), "mean": mean(lags), "lags": lags}


# ------------------------------------------------------------------- main ----
def main(dh_csv, snap_b64, out_dir):
    import os
    with open(dh_csv, "rb") as f:
        digest = hashlib.sha256(f.read().decode("utf-8").replace("\r\n", "\n").encode()).hexdigest()
    if digest != DH_CSV_SHA256:
        raise SystemExit(f"DH CSV SHA256 mismatch: {digest}")
    dh = load_dh_csv(dh_csv)
    snap = load_snapshot_b64(snap_b64)

    dh_months = sorted(dh)
    ex_months = sorted({r["date"] for r in snap})
    dh_st, dh_eps, dh_trig = build_layer(
        dh_months, lambda m: dh[m]["growth_dh"], lambda m: dh[m]["inflation_dh"])
    ex_map = {r["date"]: r for r in snap}
    ex_st, ex_eps, ex_trig = build_layer(
        ex_months, lambda m: ex_map[m]["gpi"], lambda m: ex_map[m]["ipi"])

    common = sorted(m for m in ex_months
                    if m in dh and is_fin(dh[m]["growth_dh"]) and is_fin(dh[m]["inflation_dh"]))
    dh_c = [t for t in dh_trig if t["date"] in common]
    dh_pre = [t for t in dh_trig if t["date"] not in common]
    matched, dh_only, ex_only = classify(
        [{"date": t["date"]} for t in dh_c], [{"date": t["date"]} for t in ex_trig])

    def dh_at(mo):
        r = dh.get(mo)
        if r is None:
            return {"elig": False, "G": NAN, "I": NAN, "d3G": NAN, "d3I": NAN}
        G, I = r["growth_dh"], r["inflation_dh"]
        pr = dh.get(shift_month(mo, -3))
        d3 = lambda a, b: (a - b) if is_fin(a) and pr is not None and is_fin(b) else NAN
        return {"elig": is_fin(G) and is_fin(I) and G <= STATE_HI and I <= STATE_HI,
                "G": G, "I": I,
                "d3G": d3(G, pr["growth_dh"] if pr else NAN),
                "d3I": d3(I, pr["inflation_dh"] if pr else NAN)}

    def ex_at(mo):
        r = ex_map.get(mo)
        if r is None:
            return {"elig": False, "G": NAN, "I": NAN, "d3G": NAN, "d3I": NAN}
        i = ex_months.index(mo)
        out = {"elig": r["gpi"] <= STATE_HI and r["ipi"] <= STATE_HI,
               "G": r["gpi"], "I": r["ipi"], "d3G": NAN, "d3I": NAN}
        if i >= 3:
            p = ex_map[ex_months[i - 3]]
            out["d3G"] = r["gpi"] - p["gpi"]
            out["d3I"] = r["ipi"] - p["ipi"]
        return out

    events = []
    for m in matched:
        events.append(("MATCHED", m["dh"], m["exact"], m["signed"],
                       abs(mo_diff(m["dh"], m["exact"])),
                       "DH" if m["signed"] > 0 else ("EXACT" if m["signed"] < 0 else "same")))
    for t in dh_only:
        events.append(("DH_ONLY", t["date"], None, None, None, None))
    for t in ex_only:
        events.append(("EXACT_ONLY", None, t["date"], None, None, None))
    events.sort(key=lambda e: min(x for x in (e[1], e[2]) if x is not None))
    rows = []
    for n, (kind, dd, ee, lag, abslag, first) in enumerate(events, 1):
        dec = decompose_event(kind, dd, ee, dh_at, ex_at)
        rows.append({"id": f"E{n:03d}", "kind": kind, "dh": dd, "exact": ee,
                     "lag": lag, "abslag": abslag, "first": first, **dec})

    div = [r for r in rows if r["kind"] != "MATCHED"]

    def invol(r, axis):
        DV, EV = (r["G_DH"], r["G_EX"]) if axis == "G" else (r["I_DH"], r["I_EX"])
        return axis_involved(DV, EV, r["grow_mm"] if axis == "G" else r["infl_mm"])

    det = [r for r in div if invol(r, "G") != "na" and invol(r, "I") != "na"]
    g_n = sum(1 for r in det if invol(r, "G") is True)
    i_n = sum(1 for r in det if invol(r, "I") is True)
    b_n = sum(1 for r in det if invol(r, "G") is True and invol(r, "I") is True)
    growth_frac = g_n / len(det) if det else float("nan")
    infl_frac = i_n / len(det) if det else float("nan")
    det_frac = len(det) / len(div) if div else float("nan")
    verdict = decide_verdict(growth_frac, infl_frac, det_frac)

    dh_g = {m: dh[m]["growth_dh"] for m in dh_months}
    dh_i = {m: dh[m]["inflation_dh"] for m in dh_months}
    ex_g = {r["date"]: r["gpi"] for r in snap}
    ex_i = {r["date"]: r["ipi"] for r in snap}
    LL = {
        "growth_common": nearest_profile(
            [d for d in positive_d3_onsets(consecutive_grid(dh_g, "1966-01-01", "2026-09-01"))
             if d >= "1994-05-01"],
            positive_d3_onsets(consecutive_grid(ex_g, "1994-05-01", "2026-08-01"))),
        "inflation_common": nearest_profile(
            [d for d in positive_d3_onsets(consecutive_grid(dh_i, "1966-01-01", "2026-09-01"))
             if d >= "1994-05-01"],
            positive_d3_onsets(consecutive_grid(ex_i, "1994-05-01", "2026-08-01"))),
        "convention": "lag = exact_onset - dh_onset; positive = DH first; nearest EX onset, no window",
    }
    trig_lags = [m["signed"] for m in matched]
    LL["trigger"] = {"n": len(trig_lags), "lags": trig_lags,
                     "dh_first": sum(1 for l in trig_lags if l > 0),
                     "same": sum(1 for l in trig_lags if l == 0),
                     "ex_first": sum(1 for l in trig_lags if l < 0),
                     "median": median(trig_lags) if trig_lags else None,
                     "mean": mean(trig_lags) if trig_lags else None}

    def comp_at(mo):
        r = dh.get(mo)
        if r is None:
            return None
        out = {}
        for k in GROWTH_COMPS + INFL_COMPS:
            v = r[k]
            p1 = dh.get(shift_month(mo, -1), {})
            p3 = dh.get(shift_month(mo, -3), {})
            v1 = p1.get(k, NAN)
            v3 = p3.get(k, NAN)
            out[k] = {"score": v,
                      "d1": (v - v1) if is_fin(v) and is_fin(v1) else NAN,
                      "d3": (v - v3) if is_fin(v) and is_fin(v3) else NAN}
        return out

    os.makedirs(out_dir, exist_ok=True)

    def f4(x):
        if x is None or (isinstance(x, float) and math.isnan(x)):
            return ""
        return round(float(x), 4) if isinstance(x, float) else x

    with open(os.path.join(out_dir, "divergence-events.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["event_id", "event_class", "dh_trigger_date", "exact_trigger_date",
                    "lag_mo", "abs_lag", "first_layer", "dh_state_flag", "exact_state_flag",
                    "growth_dh", "gpi", "inflation_dh", "ipi",
                    "d3growth_dh", "d3gpi", "d3inflation_dh", "d3ipi",
                    "growth_sign_agreement", "inflation_sign_agreement",
                    "divergence_attribution", "stale_note", "na_note"])
        for r in rows:
            ga = "na" if r["grow_mm"] == "na" else ("disagree" if r["grow_mm"] else "agree")
            ia = "na" if r["infl_mm"] == "na" else ("disagree" if r["infl_mm"] else "agree")
            w.writerow([r["id"], r["kind"], r["dh"] or "", r["exact"] or "",
                        r["lag"] if r["lag"] is not None else "",
                        r["abslag"] if r["abslag"] is not None else "",
                        r["first"] or "", r["dh_elig"], r["ex_elig"],
                        f4(r["G_DH"]), f4(r["G_EX"]), f4(r["I_DH"]), f4(r["I_EX"]),
                        f4(r["d3G_DH"]), f4(r["d3G_EX"]), f4(r["d3I_DH"]), f4(r["d3I_EX"]),
                        ga, ia, r["label"],
                        "stale-coincidence" if r["stale"] else "",
                        "axis-na-present" if r["na"] else ""])

    def ds_str(mo, k, n):
        c = comp_at(mo)
        if c is None:
            return "na"
        v = c[k]["d3"] if n == 3 else c[k]["d1"]
        if not is_fin(v):
            return "na"
        return "+" if v > 0 else ("-" if v < 0 else "0")

    with open(os.path.join(out_dir, "growth-axis-attribution.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["event_id", "class", "ref_month", "growth_dh", "gpi",
                    "d3growth_dh", "d3gpi", "growth_agree"] +
                   [k + "_d3sign" for k in GROWTH_COMPS] + ["g_top_driver"])
        for r in rows:
            ref = {"MATCHED": r["dh"] if mo_diff(r["dh"], r["exact"]) <= 0 else r["exact"],
                   "DH_ONLY": r["dh"], "EXACT_ONLY": r["exact"]}[r["kind"]]
            signs = [ds_str(ref, k, 3) for k in GROWTH_COMPS]
            tot = sum(c[k]["d3"] for k in GROWTH_COMPS
                      for c in [comp_at(ref)] if c is not None and is_fin(c[k]["d3"])) / 5.0 \
                if comp_at(ref) is not None and all(is_fin(comp_at(ref)[k]["d3"]) for k in GROWTH_COMPS) else NAN
            top, best = "", -1.0
            for k in GROWTH_COMPS:
                c = comp_at(ref)
                v = c[k]["d3"] if c else NAN
                if not is_fin(v) or not is_fin(tot) or tot == 0:
                    continue
                sh = (v / 5.0) / tot
                if (tot > 0 and sh > 0 or tot < 0 and sh < 0) and abs(sh) > best:
                    best, top = abs(sh), k
            ga = "na" if r["grow_mm"] == "na" else ("disagree" if r["grow_mm"] else "agree")
            w.writerow([r["id"], r["kind"], ref, f4(r["G_DH"]), f4(r["G_EX"]),
                        f4(r["d3G_DH"]), f4(r["d3G_EX"]), ga] + signs + [top])

    with open(os.path.join(out_dir, "inflation-axis-attribution.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["event_id", "class", "ref_month", "inflation_dh", "ipi",
                    "d3inflation_dh", "d3ipi", "infl_agree"] +
                   [k + "_d3sign" for k in INFL_COMPS] + ["i_top_driver"])
        for r in rows:
            ref = {"MATCHED": r["dh"] if mo_diff(r["dh"], r["exact"]) <= 0 else r["exact"],
                   "DH_ONLY": r["dh"], "EXACT_ONLY": r["exact"]}[r["kind"]]
            signs = [ds_str(ref, k, 3) for k in INFL_COMPS]
            tot = sum(c[k]["d3"] for k in INFL_COMPS
                      for c in [comp_at(ref)] if c is not None and is_fin(c[k]["d3"])) / 5.0 \
                if comp_at(ref) is not None and all(is_fin(comp_at(ref)[k]["d3"]) for k in INFL_COMPS) else NAN
            top, best = "", -1.0
            for k in INFL_COMPS:
                c = comp_at(ref)
                v = c[k]["d3"] if c else NAN
                if not is_fin(v) or not is_fin(tot) or tot == 0:
                    continue
                sh = (v / 5.0) / tot
                if (tot > 0 and sh > 0 or tot < 0 and sh < 0) and abs(sh) > best:
                    best, top = abs(sh), k
            ia = "na" if r["infl_mm"] == "na" else ("disagree" if r["infl_mm"] else "agree")
            w.writerow([r["id"], r["kind"], ref, f4(r["I_DH"]), f4(r["I_EX"]),
                        f4(r["d3I_DH"]), f4(r["d3I_EX"]), ia] + signs + [top])

    with open(os.path.join(out_dir, "divergence-components.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["event", "class", "side", "at_month", "component", "score",
                    "d1", "d3", "d3_sign", "share_of_composite_d3"])
        for r in rows:
            mos = ([r["dh"], r["exact"]] if r["kind"] == "MATCHED"
                   else [r["dh"] or r["exact"]])
            for mo in dict.fromkeys(m for m in mos if m):
                for side, keys in (("G", GROWTH_COMPS), ("I", INFL_COMPS)):
                    c = comp_at(mo)
                    tot = sum(c[k]["d3"] for k in keys) / 5.0 \
                        if c is not None and all(is_fin(c[k]["d3"]) for k in keys) else NAN
                    for k in keys:
                        v = c[k] if c else {"score": NAN, "d1": NAN, "d3": NAN}
                        w.writerow([r["id"], r["kind"], side, mo, k,
                                    f4(v["score"]), f4(v["d1"]), f4(v["d3"]),
                                    "" if not is_fin(v["d3"]) or v["d3"] == 0 else ("+" if v["d3"] > 0 else "-"),
                                    "" if not is_fin(v["d3"]) or not is_fin(tot) or tot == 0
                                    else round((v["d3"] / 5.0) / tot, 4)])

    with open(os.path.join(out_dir, "lead-lag-summary.json"), "w", encoding="utf-8") as f:
        json.dump(LL, f, indent=1)

    with open(os.path.join(out_dir, "divergence-summary.json"), "w", encoding="utf-8") as f:
        json.dump({
            "issue": 171, "dh_triggers_n": len(dh_trig_all(dh)),
            "common_months_n": len(common),
            "matched_n": len(matched), "dh_only_n": len(dh_only), "ex_only_n": len(ex_only),
            "dominance": {"divergent_n": len(div), "determinate_n": len(det),
                          "growth_frac": growth_frac, "infl_frac": infl_frac,
                          "both_frac": b_n / len(det) if det else None},
            "lead_lag": LL, "verdict": verdict,
            "exact_components": "unavailable",
            "outcome_data_loaded": False, "production_authorized": False,
        }, f, indent=1)
    print(json.dumps({"events": len(rows), "verdict": verdict}, indent=1))


def dh_trig_all(dh_months, dh):
    _, _, trig = build_layer(
        dh_months, lambda m: dh[m]["growth_dh"], lambda m: dh[m]["inflation_dh"])
    return trig


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit("usage: issue_171_divergence_autopsy.py <dh.csv> <snapshot.b64> <out_dir>")
    main(*sys.argv[1:4])
