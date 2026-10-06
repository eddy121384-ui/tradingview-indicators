#!/usr/bin/env python
"""Issue #167 frozen evaluator.

Deep-History 1966+ broad weak-state recovery x trajectory -- Equity vs 10Y Treasury.

Frozen by:
  research/issue-167-deep-history-recovery-outcomes-prereg.md
  (prereg commit b88ff35358215057d6bf3e0375fed560eb61322c)

This evaluator implements the preregistration EXACTLY. Nothing here may be tuned
after outcomes are seen. Standard library only (no pandas/numpy dependency), fully
deterministic, fixed bootstrap seed 19660101.

Run from indicators/macro-pressure-map/research/:

    python issue_167_deep_history_recovery_outcomes.py

Verified frozen inputs:
  macro CSV canonical git-blob SHA256 (LF blob, not CRLF worktree copy):
    42516418ec8d1ce981d1b4bc05e2ae86809d6acbf5de63dccbad515db507dcfc
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import statistics
import subprocess
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# Frozen constants (do not change after outcomes are seen)
# --------------------------------------------------------------------------

ISSUE = 167
SEED = 19660101
N_BOOTSTRAP = 10000
N_BOOTSTRAP_VALID_REQUIRED = 10000

MACRO_CSV = Path("generated/issue-160/deep-history-v01-monthly.csv")
MACRO_BLOB_SHA256 = "42516418ec8d1ce981d1b4bc05e2ae86809d6acbf5de63dccbad515db507dcfc"

EQUITY_CSV = Path("generated/issue-166/equity-monthly-total-returns.csv")
TREASURY_CSV = Path("generated/issue-166/treasury-monthly-total-returns.csv")
OUT_DIR = Path("generated/issue-167")

PRIMARY_THRESHOLD = 10.0        # G <= +10 AND I <= +10
DEEP_THRESHOLD = -10.0          # G < -10 AND I < -10
TRAJECTORY_LAG = 3              # d3 = x_t - x_(t-3)

WINDOW_START = "1966-01"
WINDOW_END = "2026-08"

ERAS = [
    ("1966-01", "1984-12", "1966-1984"),
    ("1985-01", "2004-12", "1985-2004"),
    ("2005-01", "2026-08", "2005-2026"),
]

PRIMARY_HORIZON = 3
DESCRIPTIVE_HORIZONS = [1, 3, 6, 12]

AVAIL_LAG = 1       # signal available = t+1
PAYOFF_LAG = 2      # first payoff month = t+2

FLAGS = {
    "outcome_data_loaded": True,
    "production_authorized": False,
    "revised_macro_history": True,
    "real_time_vintage_claim": False,
}


# --------------------------------------------------------------------------
# Month helpers
# --------------------------------------------------------------------------

def month_key(date_str: str) -> str:
    """'2026-08-01' -> '2026-08'."""
    return date_str[:7]


def add_months(m: str, k: int) -> str:
    y, mo = int(m[:4]), int(m[5:7])
    total = y * 12 + (mo - 1) + k
    return f"{total // 12:04d}-{total % 12 + 1:02d}"


def month_range(start: str, end: str):
    cur, out = start, []
    while cur <= end:
        out.append(cur)
        cur = add_months(cur, 1)
    return out


def month_index(m: str) -> int:
    return int(m[:4]) * 12 + (int(m[5:7]) - 1)


# --------------------------------------------------------------------------
# Frozen input loading + integrity
# --------------------------------------------------------------------------

def blob_sha256(path: Path) -> str:
    """Canonical LF blob hash; falls back to CRLF-normalized file bytes."""
    try:
        root = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                              capture_output=True, check=True, text=True).stdout.strip()
        rel = Path(path).resolve().relative_to(Path(root).resolve()).as_posix()
        out = subprocess.run(["git", "show", f"HEAD:{rel}"],
                             capture_output=True, check=True)
        return hashlib.sha256(out.stdout).hexdigest()
    except Exception:
        data = Path(path).read_bytes().replace(b"\r\n", b"\n")
        return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def load_macro(path: Path) -> dict:
    """Return {month: {'g':..,'i':..}} for months where BOTH axes are finite."""
    out = {}
    with path.open(newline="") as fh:
        for row in csv.DictReader(fh):
            m = month_key(row["date"])
            g, i = row["growth_dh"].strip(), row["inflation_dh"].strip()
            if g != "" and i != "":
                out[m] = {"g": float(g), "i": float(i)}
    return out


def load_returns(path: Path, column: str) -> dict:
    out = {}
    with path.open(newline="") as fh:
        for row in csv.DictReader(fh):
            v = row[column].strip()
            if v != "":
                out[month_key(row["date"])] = float(v)
    return out


# --------------------------------------------------------------------------
# Payoffs
# --------------------------------------------------------------------------

def compound(returns: dict, months: list) -> float | None:
    """Compounded total return over `months`, or None if any month is missing."""
    acc = 1.0
    for m in months:
        r = returns.get(m)
        if r is None:
            return None
        acc *= (1.0 + r)
    return acc - 1.0


def payoff_months(t: str, horizon: int, extra_delay: int = 0) -> list:
    """horizon completed monthly returns beginning at t+2 (+extra_delay)."""
    first = add_months(t, PAYOFF_LAG + extra_delay)
    return [add_months(first, k) for k in range(horizon)]


def spreads_for(eq: dict, tsy: dict, t: str, horizons: list, extra_delay: int = 0) -> dict:
    out = {}
    for h in horizons:
        ms = payoff_months(t, h, extra_delay)
        e = compound(eq, ms)
        b = compound(tsy, ms)
        out[h] = {
            "equity": e,
            "treasury": b,
            "spread": (None if (e is None or b is None) else e - b),
        }
    return out


# --------------------------------------------------------------------------
# Macro classification, episodes, signals, controls
# --------------------------------------------------------------------------

def classify(macro: dict, months: list) -> dict:
    """Per-month state / severity / trajectory flags (prereg sections 2,3,5)."""
    out = {}
    for m in months:
        g, i = macro[m]["g"], macro[m]["i"]
        primary = (g <= PRIMARY_THRESHOLD) and (i <= PRIMARY_THRESHOLD)
        deep = (g < DEEP_THRESHOLD) and (i < DEEP_THRESHOLD)
        base = month_index(m) - TRAJECTORY_LAG
        prev = f"{base // 12:04d}-{base % 12 + 1:02d}"
        d3g = d3i = None
        if prev in macro:
            d3g = g - macro[prev]["g"]
            d3i = i - macro[prev]["i"]
        traj_valid = d3g is not None and d3i is not None
        traj = traj_valid and d3g > 0 and d3i > 0
        out[m] = {
            "month": m, "g": g, "i": i,
            "primary_state": primary,
            "deep_dual_weak": deep,
            "mild_transition_weak": primary and not deep,
            "d3_growth": d3g, "d3_inflation": d3i,
            "trajectory_valid": traj_valid,
            "trajectory_positive": traj,
            "qualifying": primary and traj,
            "trajectory_quadrant": (
                None if not traj_valid else
                ("d3G>0/d3I>0" if (d3g > 0 and d3i > 0) else
                 "d3G>0/d3I<=0" if (d3g > 0) else
                 "d3G<=0/d3I>0" if (d3i > 0) else
                 "d3G<=0/d3I<=0")
            ),
        }
    return out


def build_episodes(state_flags: dict, months: list) -> list:
    """Contiguous CALENDAR months satisfying `state_flags` without a macro hole."""
    episodes, cur = [], []
    for m in months:
        if not state_flags[m]:
            if cur:
                episodes.append(cur)
                cur = []
            continue
        if cur and add_months(cur[-1], 1) != m:
            episodes.append(cur)
            cur = []
        cur.append(m)
    if cur:
        episodes.append(cur)
    return episodes


def primary_signals_controls(classified: dict, months: list) -> tuple:
    """Thin alias for the primary cohort (single implementation, prereg sections 2/6/7)."""
    return cohort_rows(classified, months, "primary")


def cohort_rows(classified: dict, months: list, cohort: str):
    """Cohort builder. cohort: 'primary' | 'high_inflation_slowdown'.

    Episodes are contiguous calendar months in the cohort state; only the FIRST
    qualifying month per episode is a signal, pre-trigger eligible months are
    controls, post-trigger months are excluded (prereg sections 6, 7).
    """
    if cohort == "primary":
        flags = {m: classified[m]["primary_state"] for m in months}
    else:
        flags = {
            m: (classified[m]["g"] <= PRIMARY_THRESHOLD
                and classified[m]["i"] > PRIMARY_THRESHOLD)
            for m in months
        }
    episodes = build_episodes(flags, months)
    quals = {m: flags[m] and classified[m]["trajectory_positive"] for m in months}
    rows, ep_rows = [], []
    for idx, ep in enumerate(episodes):
        eligible = [m for m in ep if classified[m]["trajectory_valid"]]
        trigger = next((m for m in ep if quals[m]), None)
        if trigger is not None:
            signals = [trigger]
            controls = [m for m in eligible if m < trigger]
        else:
            signals, controls = [], eligible
        for m in signals:
            rows.append({"cohort": cohort, "episode_id": idx, "role": "signal", "month": m})
        for m in controls:
            rows.append({"cohort": cohort, "episode_id": idx, "role": "control", "month": m})
        ep_rows.append({
            "cohort": cohort,
            "episode_id": idx,
            "start": ep[0], "end": ep[-1],
            "months": len(ep), "eligible_months": len(eligible),
            "trigger_month": trigger,
            "trigger_severity": (
                None if trigger is None else
                ("deep_dual_weak" if classified[trigger]["deep_dual_weak"]
                 else "mild_transition_weak")
            ),
            "n_signals": len(signals),
            "n_controls": len(controls),
            "post_trigger_excluded": (
                0 if trigger is None else sum(1 for m in ep if m > trigger)
            ),
        })
    return rows, ep_rows


# --------------------------------------------------------------------------
# Era helpers
# --------------------------------------------------------------------------

def era_of(m: str) -> str:
    for start, end, name in ERAS:
        if start <= m <= end:
            return name
    return "outside"


# --------------------------------------------------------------------------
# Statistics
# --------------------------------------------------------------------------

def mean(xs):
    xs = [x for x in xs if x is not None]
    return statistics.fmean(xs) if xs else None


def describe(xs: list) -> dict:
    xs = [x for x in xs if x is not None]
    if not xs:
        return {"n": 0, "mean": None, "median": None, "positive_fraction": None}
    return {
        "n": len(xs),
        "mean": statistics.fmean(xs),
        "median": statistics.median(xs),
        "positive_fraction": sum(1 for x in xs if x > 0) / len(xs),
    }


def incremental_mean(obs: list) -> float | None:
    """mean(signal spreads) - mean(control spreads)."""
    s = [o["spread"] for o in obs if o["role"] == "signal" and o["spread"] is not None]
    c = [o["spread"] for o in obs if o["role"] == "control" and o["spread"] is not None]
    if not s or not c:
        return None
    return statistics.fmean(s) - statistics.fmean(c)


def episode_cluster_bootstrap(obs: list, episodes_evaluable: list) -> dict:
    """Resample whole primary-state episodes; 10,000 VALID replications; seed 19660101."""
    by_ep = {}
    for o in obs:
        if o["spread"] is None:
            continue
        by_ep.setdefault(o["episode_id"], {"signal": [], "control": []})
        by_ep[o["episode_id"]][o["role"]].append(o["spread"])

    pool = [e for e in episodes_evaluable if e in by_ep]
    if not pool:
        return {"n_episodes": 0, "valid_replications": 0,
                "ci_lower": None, "ci_upper": None, "mean": None}

    rng = random.Random(SEED)
    draws, attempts, valid = [], 0, 0
    while valid < N_BOOTSTRAP_VALID_REQUIRED and attempts < N_BOOTSTRAP_VALID_REQUIRED * 200:
        attempts += 1
        n = len(pool)
        picks = [pool[rng.randrange(n)] for _ in range(n)]
        sig, ctl = [], []
        for e in picks:
            sig.extend(by_ep[e]["signal"])
            ctl.extend(by_ep[e]["control"])
        if not sig or not ctl:
            continue                                     # invalid -> reproduce
        draws.append(statistics.fmean(sig) - statistics.fmean(ctl))
        valid += 1

    if not draws:
        return {"n_episodes": len(pool), "valid_replications": 0,
                "ci_lower": None, "ci_upper": None, "mean": None}

    draws.sort()
    lo = draws[int(0.025 * len(draws))]
    hi = draws[int(0.975 * len(draws)) - 1]
    return {
        "n_episodes": len(pool),
        "valid_replications": valid,
        "ci_lower": lo, "ci_upper": hi,
        "mean": statistics.fmean(draws),
        "attempts": attempts,
    }


# --------------------------------------------------------------------------
# Gates + verdict
# --------------------------------------------------------------------------

def evaluate_gates(obs_primary: list, ep_rows: list, boot: dict,
                   primary_incremental, delayed_incremental) -> dict:
    # evaluable = observations with a usable primary 3M payoff
    ev = [o for o in obs_primary if o["spread"] is not None]
    n_trigger_ep = len({o["episode_id"] for o in ev if o["role"] == "signal"})

    sig = [o["spread"] for o in ev if o["role"] == "signal"]
    ctl = [o["spread"] for o in ev if o["role"] == "control"]

    # gate 5/6: eras
    per_era = {}
    for o in ev:
        per_era.setdefault(o["era"], {"signal": [], "control": []})[o["role"]].append(o["spread"])
    evaluable_eras = [e for e, d in per_era.items() if d["signal"] and d["control"]]
    era_increments = {
        e: statistics.fmean(per_era[e]["signal"]) - statistics.fmean(per_era[e]["control"])
        for e in evaluable_eras
    }
    positive_eras = [e for e, v in era_increments.items() if v > 0]

    if len(evaluable_eras) >= 3:
        gate6 = len(positive_eras) >= 2
    elif len(evaluable_eras) == 2:
        gate6 = len(positive_eras) == 2
    else:
        gate6 = False

    # gate 7: leave-one-trigger-episode-out (whole episode removed: signal + its controls)
    trigger_eps = sorted({o["episode_id"] for o in ev if o["role"] == "signal"})
    loo = {}
    for e in trigger_eps:
        sub = [o for o in ev if o["episode_id"] != e]
        v = incremental_mean(sub)
        if v is not None:
            loo[e] = v
    gate7 = bool(loo) and all(v > 0 for v in loo.values())

    # gate 8: strongest positive trigger episode share of total positive contribution
    contrib = {}
    for e in trigger_eps:
        contrib[e] = sum(o["spread"] for o in ev
                         if o["episode_id"] == e and o["role"] == "signal")
    total_positive = sum(v for v in contrib.values() if v > 0)
    strongest = max(contrib.values()) if contrib else None
    share = (strongest / total_positive) if (contrib and total_positive > 0) else None
    gate8 = share is not None and share <= 0.50

    gates = {
        "gate1_min_8_trigger_episodes": n_trigger_ep >= 8,
        "gate2_signal_mean_gt_0": bool(sig) and statistics.fmean(sig) > 0,
        "gate3_incremental_gt_0": primary_incremental is not None and primary_incremental > 0,
        "gate4_bootstrap_ci_lower_gt_0": boot["ci_lower"] is not None and boot["ci_lower"] > 0,
        "gate5_eras_with_both_ge_2": len(evaluable_eras) >= 2,
        "gate6_positive_eras": gate6,
        "gate7_all_loo_positive": gate7,
        "gate8_strongest_share_le_50pct": gate8,
        "gate9_delayed_positive": delayed_incremental is not None and delayed_incremental > 0,
    }
    detail = {
        "n_trigger_episodes_evaluable": n_trigger_ep,
        "n_signal_obs": len(sig), "n_control_obs": len(ctl),
        "evaluable_eras": evaluable_eras,
        "era_increments": era_increments,
        "positive_eras": positive_eras,
        "leave_one_out_increments": {str(k): v for k, v in loo.items()},
        "trigger_contributions": {str(k): v for k, v in contrib.items()},
        "strongest_positive_share": share,
        "delayed_incremental": delayed_incremental,
    }
    return gates, detail


def verdict_from(gates: dict, primary_incremental) -> str:
    if not gates["gate1_min_8_trigger_episodes"]:
        return "deep_history_recovery_outcome_inconclusive_sample"
    robustness = [gates[k] for k in (
        "gate4_bootstrap_ci_lower_gt_0", "gate5_eras_with_both_ge_2",
        "gate6_positive_eras", "gate7_all_loo_positive",
        "gate8_strongest_share_le_50pct", "gate9_delayed_positive",
    )]
    direction_ok = gates["gate2_signal_mean_gt_0"] and gates["gate3_incremental_gt_0"]
    if direction_ok and not all(robustness):
        return "deep_history_recovery_outcome_suggestive_not_robust"
    if all(gates.values()):
        return "deep_history_recovery_outcome_supported"
    return "deep_history_recovery_outcome_not_supported"


# --------------------------------------------------------------------------
# Output helpers
# --------------------------------------------------------------------------

def write_csv(path: Path, rows: list, columns: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--macro", default=str(MACRO_CSV))
    ap.add_argument("--equity", default=str(EQUITY_CSV))
    ap.add_argument("--treasury", default=str(TREASURY_CSV))
    ap.add_argument("--out", default=str(OUT_DIR))
    ap.add_argument("--skip-hash-check", action="store_true")
    args = ap.parse_args(argv)

    macro_path = Path(args.macro)
    got = blob_sha256(macro_path)
    if not args.skip_hash_check and got != MACRO_BLOB_SHA256:
        print(f"ABORT: frozen macro CSV hash mismatch.\n  expected {MACRO_BLOB_SHA256}\n  got      {got}",
              file=sys.stderr)
        return 2
    eq_sha, tsy_sha = file_sha256(Path(args.equity)), file_sha256(Path(args.treasury))

    macro = load_macro(macro_path)
    eq = load_returns(Path(args.equity), "equity_tr")
    tsy = load_returns(Path(args.treasury), "treasury10y_tr")

    months = [m for m in month_range(WINDOW_START, WINDOW_END) if m in macro]
    classified = classify(macro, months)

    rows, ep_rows = cohort_rows(classified, months, "primary")

    obs = []
    for r in rows:
        t = r["month"]
        c = classified[t]
        sp = spreads_for(eq, tsy, t, DESCRIPTIVE_HORIZONS)
        obs.append({
            "episode_id": r["episode_id"], "role": r["role"],
            "macro_state_month": t,
            "signal_available_month": add_months(t, AVAIL_LAG),
            "growth_dh": c["g"], "inflation_dh": c["i"],
            "d3_growth": c["d3_growth"], "d3_inflation": c["d3_inflation"],
            "episode_severity": ("deep_dual_weak" if c["deep_dual_weak"]
                                 else "mild_transition_weak"),
            "era": era_of(t),
            **{f"equity_{h}m": sp[h]["equity"] for h in DESCRIPTIVE_HORIZONS},
            **{f"treasury_{h}m": sp[h]["treasury"] for h in DESCRIPTIVE_HORIZONS},
            **{f"spread_{h}m": sp[h]["spread"] for h in DESCRIPTIVE_HORIZONS},
        })

    # primary comparison uses the frozen 3M horizon
    obs_primary = [dict(o, spread=o["spread_3m"]) for o in obs]

    primary_incremental = incremental_mean(obs_primary)
    episodes_evaluable = sorted({o["episode_id"] for o in obs_primary if o["spread_3m"] is not None})
    boot = episode_cluster_bootstrap(obs_primary, episodes_evaluable)

    # gate 9: one-additional-month implementation delay, same 3M horizon
    delayed = []
    for o in obs_primary:
        t = o["macro_state_month"]
        sp = spreads_for(eq, tsy, t, [PRIMARY_HORIZON], extra_delay=1)[PRIMARY_HORIZON]
        delayed.append(dict(o, spread=sp["spread"]))
    delayed_incremental = incremental_mean(delayed)

    gates, gate_detail = evaluate_gates(obs_primary, ep_rows, boot,
                                        primary_incremental, delayed_incremental)
    verdict = verdict_from(gates, primary_incremental)

    # ---- subgroup report (primary triggers by trigger-month severity) ----
    severity_rows = []
    for sev in ("deep_dual_weak", "mild_transition_weak"):
        sel = [o for o in obs_primary if o["role"] == "signal"
               and o["episode_severity"] == sev and o["spread"] is not None]
        d = describe([o["spread"] for o in sel])
        eras = {}
        for o in sel:
            eras[o["era"]] = eras.get(o["era"], 0) + 1
        severity_rows.append({
            "trigger_severity": sev, "n": d["n"], "mean": d["mean"],
            "median": d["median"], "positive_fraction": d["positive_fraction"],
            "equity_mean": mean([o["equity_3m"] for o in sel]),
            "treasury_mean": mean([o["treasury_3m"] for o in sel]),
            "eras": json.dumps(eras, sort_keys=True),
        })

    # ---- secondary high-inflation slowdown cohort (descriptive only) ----
    hi_rows, hi_eps = cohort_rows(classified, months, "high_inflation_slowdown")
    hi_obs = []
    for r in hi_rows:
        t = r["month"]
        c = classified[t]
        sp = spreads_for(eq, tsy, t, DESCRIPTIVE_HORIZONS)
        hi_obs.append({
            "episode_id": r["episode_id"], "role": r["role"],
            "macro_state_month": t,
            "signal_available_month": add_months(t, AVAIL_LAG),
            "growth_dh": c["g"], "inflation_dh": c["i"],
            "era": era_of(t),
            **{f"spread_{h}m": sp[h]["spread"] for h in DESCRIPTIVE_HORIZONS},
            **{f"equity_{h}m": sp[h]["equity"] for h in DESCRIPTIVE_HORIZONS},
            **{f"treasury_{h}m": sp[h]["treasury"] for h in DESCRIPTIVE_HORIZONS},
        })
    hi_report = []
    for h in DESCRIPTIVE_HORIZONS:
        for role in ("signal", "control"):
            sel = [o for o in hi_obs if o["role"] == role and o[f"spread_{h}m"] is not None]
            d = describe([o[f"spread_{h}m"] for o in sel])
            hi_report.append({
                "horizon_months": h, "role": role, "n": d["n"],
                "mean": d["mean"], "median": d["median"],
                "positive_fraction": d["positive_fraction"],
                "equity_mean": mean([o[f"equity_{h}m"] for o in sel]),
                "treasury_mean": mean([o[f"treasury_{h}m"] for o in sel]),
            })

    # ---- descriptive 3x3 map + trajectory quadrants (exploratory) ----
    def band(v, lo, hi):
        return "low" if v < lo else ("high" if v > hi else "neutral")
    map_rows = []
    for gl in ("low", "neutral", "high"):
        for il in ("low", "neutral", "high"):
            sel_m = [m for m in months
                     if band(classified[m]["g"], DEEP_THRESHOLD, PRIMARY_THRESHOLD) == gl
                     and band(classified[m]["i"], DEEP_THRESHOLD, PRIMARY_THRESHOLD) == il]
            flags = {m: (m in set(sel_m)) for m in months}
            eps = build_episodes(flags, months) if sel_m else []
            sp = [spreads_for(eq, tsy, m, [3])[3] for m in sel_m]
            d = describe([s["spread"] for s in sp])
            map_rows.append({
                "growth_band": gl, "inflation_band": il,
                "months": len(sel_m), "episodes": len(eps),
                "n_3m": d["n"], "mean_3m": d["mean"], "median_3m": d["median"],
                "positive_fraction_3m": d["positive_fraction"],
                "equity_3m_mean": mean([s["equity"] for s in sp]),
                "treasury_3m_mean": mean([s["treasury"] for s in sp]),
            })
    quad_rows = []
    for q in ("d3G>0/d3I>0", "d3G>0/d3I<=0", "d3G<=0/d3I>0", "d3G<=0/d3I<=0"):
        sel_m = [m for m in months if classified[m]["trajectory_quadrant"] == q]
        sp = [spreads_for(eq, tsy, m, [3])[3] for m in sel_m]
        d = describe([s["spread"] for s in sp])
        quad_rows.append({
            "trajectory_quadrant": q, "months": len(sel_m), "n_3m": d["n"],
            "mean_3m": d["mean"], "median_3m": d["median"],
            "positive_fraction_3m": d["positive_fraction"],
        })

    # trajectory quadrants INSIDE each of the 9 states (issue: report quadrants per state)
    state_quad_rows = []
    for gl in ("low", "neutral", "high"):
        for il in ("low", "neutral", "high"):
            for q in ("d3G>0/d3I>0", "d3G>0/d3I<=0", "d3G<=0/d3I>0", "d3G<=0/d3I<=0"):
                sel_m = [m for m in months
                         if band(classified[m]["g"], DEEP_THRESHOLD, PRIMARY_THRESHOLD) == gl
                         and band(classified[m]["i"], DEEP_THRESHOLD, PRIMARY_THRESHOLD) == il
                         and classified[m]["trajectory_quadrant"] == q]
                sp = [spreads_for(eq, tsy, m, [3])[3] for m in sel_m]
                d = describe([s["spread"] for s in sp])
                state_quad_rows.append({
                    "growth_band": gl, "inflation_band": il,
                    "trajectory_quadrant": q, "months": len(sel_m), "n_3m": d["n"],
                    "mean_3m": d["mean"], "median_3m": d["median"],
                    "positive_fraction_3m": d["positive_fraction"],
                })

    primary_desc = describe([o["spread_3m"] for o in obs_primary if o["role"] == "signal"])
    control_desc = describe([o["spread_3m"] for o in obs_primary if o["role"] == "control"])
    # explicit leg reporting (issue requires Equity_3M_TR, Treasury10Y_3M_TR and the spread)
    for desc, role in ((primary_desc, "signal"), (control_desc, "control")):
        sel = [o for o in obs_primary if o["role"] == role and o["spread_3m"] is not None]
        desc["equity_leg_mean"] = mean([o["equity_3m"] for o in sel])
        desc["equity_leg_median"] = (statistics.median([o["equity_3m"] for o in sel])
                                     if sel else None)
        desc["treasury_leg_mean"] = mean([o["treasury_3m"] for o in sel])
        desc["treasury_leg_median"] = (statistics.median([o["treasury_3m"] for o in sel])
                                       if sel else None)

    result = {
        "issue": ISSUE,
        "prereg": "issue-167-deep-history-recovery-outcomes-prereg.md",
        "prereg_commit": "b88ff35358215057d6bf3e0375fed560eb61322c",
        "branch": "research/issue-167-deep-history-recovery-outcomes",
        "verbose_status": verdict,
        "verdict": verdict,
        **FLAGS,
        "primary_state": "DH_NONSTRONG_DISINFLATIONARY_STATE (Growth_DH <= +10 AND Inflation_DH <= +10)",
        "trajectory": "d3Growth > 0 AND d3Inflation > 0 (lag 3); first qualifying month per episode only",
        "timing": {"macro_state_month": "t", "signal_available_month": "t+1", "first_payoff_month": "t+2"},
        "bootstrap": {"method": "primary-state-episode cluster bootstrap",
                      "seed": SEED, "requested_replications": N_BOOTSTRAP,
                      **boot},
        "inputs": {
            "macro_csv": str(MACRO_CSV), "macro_blob_sha256": got,
            "macro_blob_sha256_expected": MACRO_BLOB_SHA256,
            "macro_blob_sha256_ok": got == MACRO_BLOB_SHA256,
            "equity_csv": str(EQUITY_CSV), "equity_sha256": eq_sha,
            "treasury_csv": str(TREASURY_CSV), "treasury_sha256": tsy_sha,
            "macro_valid_months_in_window": len(months),
            "window": [WINDOW_START, WINDOW_END],
        },
        "primary_episodes_total": len(ep_rows),
        "primary_episodes_triggered": sum(1 for e in ep_rows if e["trigger_month"] is not None),
        "primary_observations": {
            "all_signals": sum(1 for o in obs_primary if o["role"] == "signal"),
            "all_controls": sum(1 for o in obs_primary if o["role"] == "control"),
            "signals_with_3m_payoff": primary_desc["n"],
            "controls_with_3m_payoff": control_desc["n"],
        },
        "signal_3m": primary_desc,
        "control_3m": control_desc,
        "incremental_mean_3m": primary_incremental,
        "incremental_mean_3m_delayed_t_plus_3": delayed_incremental,
        "gates": gates,
        "gate_detail": gate_detail,
        "severity_subgroups": severity_rows,
        "high_inflation_slowdown": hi_report,
        "high_inflation_slowdown_episodes": len(hi_eps),
        "descriptive_3x3_map": map_rows,
        "trajectory_quadrants": quad_rows,
        "descriptive_trajectory_quadrants_within_state": state_quad_rows,
    }

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "recovery-primary-result.json").write_text(
        json.dumps(result, indent=1, sort_keys=True), encoding="utf-8")

    write_csv(out / "recovery-signal-control.csv", obs, [
        "episode_id", "role", "macro_state_month", "signal_available_month",
        "growth_dh", "inflation_dh", "d3_growth", "d3_inflation",
        "episode_severity", "era",
        "equity_1m", "treasury_1m", "spread_1m",
        "equity_3m", "treasury_3m", "spread_3m",
        "equity_6m", "treasury_6m", "spread_6m",
        "equity_12m", "treasury_12m", "spread_12m",
    ])
    write_csv(out / "recovery-primary-episodes.csv", ep_rows, [
        "episode_id", "start", "end", "months", "eligible_months",
        "trigger_month", "trigger_severity", "n_signals", "n_controls",
        "post_trigger_excluded",
    ])
    write_csv(out / "recovery-severity-subgroups.csv", severity_rows, [
        "trigger_severity", "n", "mean", "median", "positive_fraction",
        "equity_mean", "treasury_mean", "eras",
    ])
    write_csv(out / "recovery-high-inflation-slowdown.csv", hi_report, [
        "horizon_months", "role", "n", "mean", "median", "positive_fraction",
        "equity_mean", "treasury_mean",
    ])
    write_csv(out / "recovery-descriptive-3x3-map.csv", map_rows, [
        "growth_band", "inflation_band", "months", "episodes", "n_3m",
        "mean_3m", "median_3m", "positive_fraction_3m",
        "equity_3m_mean", "treasury_3m_mean",
    ])
    write_csv(out / "recovery-trajectory-quadrants.csv", quad_rows, [
        "trajectory_quadrant", "months", "n_3m", "mean_3m", "median_3m",
        "positive_fraction_3m",
    ])
    write_csv(out / "recovery-3x3-trajectory-quadrants.csv", state_quad_rows, [
        "growth_band", "inflation_band", "trajectory_quadrant", "months", "n_3m",
        "mean_3m", "median_3m", "positive_fraction_3m",
    ])

    print(json.dumps({
        "verdict": verdict,
        "primary_episodes_total": result["primary_episodes_total"],
        "primary_episodes_triggered": result["primary_episodes_triggered"],
        "signals_with_3m_payoff": primary_desc["n"],
        "controls_with_3m_payoff": control_desc["n"],
        "signal_mean_3m": primary_desc["mean"],
        "control_mean_3m": control_desc["mean"],
        "incremental_mean_3m": primary_incremental,
        "bootstrap": boot,
        "gates": gates,
        "macro_blob_sha256_ok": got == MACRO_BLOB_SHA256,
    }, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
