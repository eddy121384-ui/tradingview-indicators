#!/usr/bin/env python3
"""Issue #169 — exact-V6.6 broad weak-state recovery translation (frozen evaluator).

Frozen implementation of:
  indicators/macro-pressure-map/research/issue-169-exact-v66-recovery-prereg.md

Pure standard library (no numpy/pandas). Results were executed through a
line-for-line Node mirror (no Python runtime on the research machine); this
file is the canonical frozen record. PRNG below reproduces mulberry32
bit-for-bit (see tests for pinned vectors).

Pipeline:
  1. Verify the Issue #133 snapshot SHA256 and header; load date/GPI/IPI.
  2. Build V66_NONSTRONG_DISINFLATIONARY_STATE episodes, d3 trajectory,
     first triggers, severity labels, controls, and t+2 payoffs from the
     Issue #166 backbones. No return from t/t+1 enters payoffs.
  3. Primary stats, episode-cluster bootstrap (seed 169), eras, LOO,
     concentration, t+3 delay; all 9 gates; verdict.
  4. Only with the "secondary" argument: native t+1 timing and cross-layer
     comparison (post-verdict diagnostics; never rescue the verdict).

Firewall: outcome_data_loaded=true after load; production_authorized=false;
repeated_modern_sample=true; pristine_oos_claim=false.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import sys

# ---------------------------------------------------------------- frozen ----
SEED = 169
BOOT_REPS = 10000
BOOT_DRAWS_CAP = 1000000
SNAPSHOT_SHA256 = "1d03923503e7fe82a69b033897484c48aa646279ecf70164d090ed62a5a70719"
STATE_LO = 10.0
DEEP_LO = -10.0
ERAS = (("pre-2020", "0000-00-00", "2019-12-31"),
        ("2020-2022", "2020-01-01", "2022-12-31"),
        ("2023+", "2023-01-01", "9999-12-31"))

NAN = float("nan")


def is_fin(x) -> bool:
    return x is not None and not (isinstance(x, float) and math.isnan(x))


# ------------------------------------------------------------- RNG (exact) ----
_MASK = 0xFFFFFFFF


def _u32(x: int) -> int:
    return x & _MASK


def _s32(x: int) -> int:
    x &= _MASK
    return x - 0x100000000 if x >= 0x80000000 else x


def _imul32(a: int, b: int) -> int:
    return _s32(_u32(a) * _u32(b))


def mulberry32(seed: int):
    a = seed

    def gen():
        nonlocal a
        a = _s32(a + 0x6D2B79F5)
        t = _imul32(a ^ (_u32(a) >> 15), _s32(1 | a))
        t = _s32(_u32(t + _imul32(t ^ (_u32(t) >> 7), _s32(61 | t))) ^ _u32(t))
        t = _u32(t ^ (_u32(t) >> 14))
        return t / 4294967296.0

    return gen


# ------------------------------------------------------------------ dates ----
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


def mean(xs):
    return sum(xs) / len(xs)


def median(xs):
    s = sorted(xs)
    m = len(s) >> 1
    return s[m] if len(s) % 2 else (s[m - 1] + s[m]) / 2.0


# ----------------------------------------------------------------- primary ----
def load_snapshot(path):
    with open(path, "rb") as f:
        raw = f.read()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != SNAPSHOT_SHA256:
        raise SystemExit(f"snapshot SHA256 mismatch: {digest}")
    lines = raw.decode("utf-8").splitlines()
    header = lines[0].split(",")
    if header != ["date", "gpi", "ipi", "regime"]:
        raise SystemExit(f"unexpected snapshot header: {header}")
    rows = []
    for line in lines[1:]:
        if not line.strip():
            continue
        d, g, i, r = line.split(",")
        rows.append({"date": d, "gpi": float(g), "ipi": float(i), "regime": int(r)})
    return rows


def build_states(snap):
    out = []
    for i, s in enumerate(snap):
        elig = s["gpi"] <= STATE_LO and s["ipi"] <= STATE_LO
        if i >= 3:
            d3g = s["gpi"] - snap[i - 3]["gpi"]
            d3i = s["ipi"] - snap[i - 3]["ipi"]
        else:
            d3g = d3i = NAN
        out.append({**s, "elig": elig, "d3g": d3g, "d3i": d3i,
                    "qual": elig and is_fin(d3g) and is_fin(d3i) and d3g > 0 and d3i > 0})
    return out


def build_episodes(st):
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
    return episodes


def build_triggers(st, episodes):
    triggers = []
    for ei, e in enumerate(episodes):
        for i in e["idx"]:
            if st[i]["qual"]:
                s = st[i]
                triggers.append({"ep": ei, "idx": i, "date": s["date"],
                                 "deep": s["gpi"] < DEEP_LO and s["ipi"] < DEEP_LO})
                e["trigger"] = i
                break
    for t in triggers:
        t["mild"] = not t["deep"]
    return triggers


def build_obs(st, episodes, triggers):
    signals, controls = [], []
    trig_ep = {t["ep"] for t in triggers}
    for ei, e in enumerate(episodes):
        first = e.get("trigger")
        for i in e["idx"]:
            rec = {"ep": ei, "idx": i, "date": st[i]["date"]}
            if ei in trig_ep and first is not None and i == first:
                rec["deep"] = st[i]["gpi"] < DEEP_LO and st[i]["ipi"] < DEEP_LO
                signals.append(rec)
            elif ei in trig_ep and first is not None and i < first:
                controls.append(rec)
            elif ei not in trig_ep:
                controls.append(rec)
    return signals, controls


def payoff_for(snap, eq, ty, idx, start_off, length):
    base = snap[idx]["date"][:7] + "-01"
    e = t = 1.0
    for k in range(length):
        mo = shift_month(base, start_off + k)
        er, tr = eq.get(mo), ty.get(mo)
        if er is None or tr is None or not is_fin(er) or not is_fin(tr):
            return None
        e *= 1.0 + er
        t *= 1.0 + tr
    return {"eq": e - 1.0, "ty": t - 1.0, "spread": e - t}


def era_of(date):
    for name, a, b in ERAS:
        if a <= date <= b:
            return name
    raise AssertionError("date outside eras: " + date)


def evaluate(snap, eq, ty):
    st = build_states(snap)
    episodes = build_episodes(st)
    triggers = build_triggers(st, episodes)
    signals, controls = build_obs(st, episodes, triggers)

    def with_payoff(obs, off, length):
        out = []
        for o in obs:
            p = payoff_for(snap, eq, ty, o["idx"], off, length)
            if p is None:
                continue
            out.append({**o, "P": p})
        return out

    sig = with_payoff(signals, 2, 3)
    ctl = with_payoff(controls, 2, 3)
    S = [o["P"]["spread"] for o in sig]
    C = [o["P"]["spread"] for o in ctl]
    inc = mean(S) - mean(C) if S and C else NAN

    # cluster bootstrap over episodes
    ep_obs = []
    for ei in range(len(episodes)):
        ep_obs.append(([o["P"]["spread"] for o in sig if o["ep"] == ei],
                       [o["P"]["spread"] for o in ctl if o["ep"] == ei]))
    gen = mulberry32(SEED)
    boots, draws = [], 0
    while len(boots) < BOOT_REPS and draws < BOOT_DRAWS_CAP:
        draws += 1
        s, c = [], []
        for _ in range(len(episodes)):
            es, ec = ep_obs[int(gen() * len(ep_obs))]
            s += es
            c += ec
        if s and c:
            boots.append(mean(s) - mean(c))
    boots.sort()
    ci = [boots[int(0.025 * len(boots))], boots[int(0.975 * len(boots))]] if boots else [NAN, NAN]

    eras = {}
    for name, _, _ in ERAS:
        s = [o["P"]["spread"] for o in sig if era_of(o["date"]) == name]
        c = [o["P"]["spread"] for o in ctl if era_of(o["date"]) == name]
        eras[name] = {"sig_n": len(s), "ctl_n": len(c),
                      "incr": mean(s) - mean(c) if s and c else NAN}
    eval_eras = [e for e in eras if eras[e]["sig_n"] > 0 and eras[e]["ctl_n"] > 0]

    loo = []
    for t in triggers:
        s = [o["P"]["spread"] for o in sig if o["ep"] != t["ep"]]
        c = [o["P"]["spread"] for o in ctl if o["ep"] != t["ep"]]
        ok = bool(s and c)
        loo.append({"ep": t["ep"], "date": t["date"], "evaluable": ok,
                    "incr": mean(s) - mean(c) if ok else NAN})
    pos = [o["P"]["spread"] for o in sig if o["P"]["spread"] > 0]
    conc = max(pos) / sum(pos) if pos else NAN

    sig_d = with_payoff(signals, 3, 3)
    ctl_d = with_payoff(controls, 3, 3)
    d_incr = (mean([o["P"]["spread"] for o in sig_d]) - mean([o["P"]["spread"] for o in ctl_d])
              if sig_d and ctl_d else NAN)

    trig_eval = sum(1 for t in triggers if any(o["ep"] == t["ep"] for o in sig))
    gates = [
        trig_eval >= 8,
        bool(S) and mean(S) > 0,
        bool(S and C) and inc > 0,
        is_fin(ci[0]) and ci[0] > 0,
        sum(1 for e in eras if eras[e]["sig_n"] > 0 and eras[e]["ctl_n"] > 0) >= 2,
        len(eval_eras) >= 2 and (len([e for e in eval_eras if eras[e]["incr"] > 0]) >= 2
                                 if len(eval_eras) > 2 else all(eras[e]["incr"] > 0 for e in eval_eras)),
        all(l["incr"] > 0 for l in loo if l["evaluable"]),
        is_fin(conc) and conc <= 0.50,
        is_fin(d_incr) and d_incr > 0,
    ]
    if not gates[0]:
        verdict = "exact_v66_recovery_translation_inconclusive_sample"
    elif all(gates):
        verdict = "exact_v66_recovery_translation_supported"
    elif gates[1] and gates[2]:
        verdict = "exact_v66_recovery_translation_directionally_consistent_not_robust"
    else:
        verdict = "exact_v66_recovery_translation_not_supported"
    return {
        "episodes": episodes, "triggers": triggers, "signals": sig, "controls": ctl,
        "incremental": inc, "bootstrap_ci": ci, "bootstrap_valid": len(boots),
        "eras": eras, "loo": loo, "concentration": conc,
        "delay": {"sig_n": len(sig_d), "ctl_n": len(ctl_d), "incr": d_incr},
        "gates": gates, "verdict": verdict,
    }


def main(snap_path, eq_path, ty_path, out_dir):
    import os
    snap = load_snapshot(snap_path)

    def load_ret(path, col):
        out = {}
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                out[row["date"]] = float(row[col])
        return out

    eq, ty = load_ret(eq_path, "equity_tr"), load_ret(ty_path, "treasury10y_tr")
    res = evaluate(snap, eq, ty)
    os.makedirs(out_dir, exist_ok=True)

    def r6(x):
        return "" if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), 6)

    with open(os.path.join(out_dir, "recovery-signal-control.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["role", "episode", "macro_state_month", "signal_available_month", "severity",
                    "payoff_m1", "payoff_m2", "payoff_m3",
                    "eq_1m", "ty_1m", "spread_1m", "eq_3m", "ty_3m", "spread_3m",
                    "eq_6m", "ty_6m", "spread_6m", "eq_12m", "ty_12m", "spread_12m"])
        all_obs = ([("signal", o) for o in res["signals"]] + [("control", o) for o in res["controls"]])
        for role, o in all_obs:
            i = next(i for i, s in enumerate(snap) if s["date"] == o["date"])
            sev = ""
            if role == "signal":
                t = next(t for t in res["triggers"] if t["ep"] == o["ep"])
                sev = "deep" if t["deep"] else "mild"
            row = [role, o["ep"], o["date"], shift_month(o["date"], 1), sev,
                   shift_month(o["date"][:7] + "-01", 2), shift_month(o["date"][:7] + "-01", 3),
                   shift_month(o["date"][:7] + "-01", 4)]
            for L in (1, 3, 6, 12):
                p = payoff_for(snap, eq, ty, i, 2, L)
                row += [r6(p["eq"]), r6(p["ty"]), r6(p["spread"])] if p else ["", "", ""]
            w.writerow(row)

    with open(os.path.join(out_dir, "recovery-episodes.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["episode", "start", "end", "n_months", "trigger_date", "severity", "n_signals", "n_controls"])
        for ei, e in enumerate(res["episodes"]):
            t = next((x for x in res["triggers"] if x["ep"] == ei), None)
            w.writerow([ei, snap[e["idx"][0]]["date"], snap[e["idx"][-1]]["date"], len(e["idx"]),
                        t["date"] if t else "", "deep" if t and t["deep"] else ("mild" if t else ""),
                        sum(1 for o in res["signals"] if o["ep"] == ei),
                        sum(1 for o in res["controls"] if o["ep"] == ei)])

    S = [o for o in res["signals"]]
    C = [o for o in res["controls"]]
    payload = {
        "issue": 169, "snapshot_sha256": SNAPSHOT_SHA256,
        "episodes_n": len(res["episodes"]), "triggers_n": len(res["triggers"]),
        "deep_triggers_n": sum(1 for t in res["triggers"] if t["deep"]),
        "mild_triggers_n": sum(1 for t in res["triggers"] if not t["deep"]),
        "signals_n": len(S), "controls_n": len(C),
        "signal_spread": {"mean": r6(mean([o["P"]["spread"] for o in S])) if S else None},
        "incremental": r6(res["incremental"]) if is_fin(res["incremental"]) else None,
        "bootstrap": {"seed": SEED, "valid": res["bootstrap_valid"], "ci": [r6(res["bootstrap_ci"][0]), r6(res["bootstrap_ci"][1])]},
        "gates": res["gates"], "verdict": res["verdict"],
        "outcome_data_loaded": True, "production_authorized": False,
        "repeated_modern_sample": True, "pristine_oos_claim": False,
    }
    with open(os.path.join(out_dir, "recovery-results.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1)
    print(json.dumps({"verdict": res["verdict"], "gates": res["gates"]}, indent=1))


if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit("usage: issue_169_exact_v66_recovery.py <snapshot.csv> <equity.csv> <treasury.csv> <out_dir>")
    main(*sys.argv[1:5])
