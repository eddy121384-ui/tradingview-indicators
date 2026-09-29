#!/usr/bin/env python3
"""Issue #125 — HMRA Reflation <-> exact V6.6 Reflation bridge.

State-only bridge. No asset returns are loaded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from issue_91_phase1_hmra_v01 import run as run_hmra

HERE = Path(__file__).resolve().parent
PREREG = HERE / "decisions" / "issue-125-reflation-bridge-preregistered.md"
FREEZE = HERE / "decisions" / "issue-91-phase1-hmra-v0.1-source-freeze.json"
TRANSITIONS = HERE / "data" / "issue-64-frozen-regime-transitions.csv"

EXPECTED_TRANSITION_SHA = "80446bbcb91be8b18eb0b95e62466edf892e4c04087696a04532f0fe214698af"
HMRA_REFLATION = "Reflation / Inflation Rising"
BOOTSTRAP_REPS = 10_000


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_seed(*parts: object) -> int:
    payload = "|".join(str(x) for x in parts).encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") & 0xFFFFFFFF


def validate_prereg() -> None:
    s = PREREG.read_text(encoding="utf-8")
    required = [
        "PREREGISTERED BEFORE BRIDGE RESULTS",
        "complete years 2007–2025",
        "Growth high = regimes 1/2/3",
        "Inflation high = regimes 3/6/9",
        "Regime 3 must have the largest positive occupancy lift",
        "No bridge result had been computed",
    ]
    missing = [x for x in required if x not in s]
    if missing:
        raise RuntimeError(f"prereg guard failed: {missing}")


def load_hmra() -> pd.DataFrame:
    frozen = json.loads(FREEZE.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="issue125-hmra-") as td:
        out = Path(td)
        manifest = run_hmra(out)
        states = pd.read_csv(out / "issue-91-hmra-v0.1-macro-states.csv")
    exp = frozen["canonical_input_freeze"]
    fed = manifest["sources"]["fed_ip"]["canonical_used_observations_sha256"]
    bls = manifest["sources"]["bls_cpi"]["canonical_observations_sha256"]
    if fed != exp["fed_ip"]["canonical_used_observations_sha256"]:
        raise RuntimeError("HMRA Fed canonical hash drift")
    if bls != exp["bls_cpi"]["canonical_observations_sha256"]:
        raise RuntimeError("HMRA BLS canonical hash drift")
    states = states.loc[
        states["year"].between(2007, 2025) & states["core_regime"].ne("n/a")
    ].copy()
    if len(states) != 19:
        raise RuntimeError(f"expected 19 HMRA overlap years, got {len(states)}")
    return states


def load_transitions() -> pd.DataFrame:
    if sha256_file(TRANSITIONS) != EXPECTED_TRANSITION_SHA:
        raise RuntimeError("exact V6.6 transition SHA mismatch")
    t = pd.read_csv(TRANSITIONS)
    t["start_date"] = pd.to_datetime(t["start_date"], errors="raise")
    t["regime_id"] = pd.to_numeric(t["regime_id"], errors="raise").astype(int)
    return t.sort_values("start_date").reset_index(drop=True)


def regime_on_date(transitions: pd.DataFrame, date: pd.Timestamp) -> int:
    starts = transitions["start_date"].to_numpy(dtype="datetime64[ns]")
    pos = int(np.searchsorted(starts, np.datetime64(date), side="right") - 1)
    if pos < 0:
        raise RuntimeError(f"no exact state available on {date}")
    return int(transitions.iloc[pos]["regime_id"])


def monthly_exact(transitions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for year in range(2007, 2026):
        for month in range(1, 13):
            end = pd.Timestamp(year, month, 1) + pd.offsets.MonthEnd(0)
            rid = regime_on_date(transitions, end)
            rows.append({"year": year, "month": month, "month_end": end, "regime_id": rid})
    return pd.DataFrame(rows)


def annual_features(monthly: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for year, g in monthly.groupby("year", sort=True):
        rec = {"year": int(year)}
        for rid in range(1, 10):
            rec[f"r{rid}_share"] = float((g["regime_id"] == rid).mean())
        rec["growth_high_share"] = float(g["regime_id"].isin([1, 2, 3]).mean())
        rec["inflation_high_share"] = float(g["regime_id"].isin([3, 6, 9]).mean())
        rec["r3_share"] = rec["r3_share"]
        rows.append(rec)
    return pd.DataFrame(rows)


def bootstrap_diff(a: np.ndarray, b: np.ndarray, seed: int) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    ia = rng.integers(0, len(a), size=(BOOTSTRAP_REPS, len(a)))
    ib = rng.integers(0, len(b), size=(BOOTSTRAP_REPS, len(b)))
    diffs = a[ia].mean(axis=1) - b[ib].mean(axis=1)
    lo, hi = np.quantile(diffs, [0.025, 0.975])
    return float(lo), float(hi)


def compare_feature(frame: pd.DataFrame, col: str, label: str) -> dict:
    a = frame.loc[frame["hmra_reflation"], col].to_numpy(float)
    b = frame.loc[~frame["hmra_reflation"], col].to_numpy(float)
    lo, hi = bootstrap_diff(a, b, stable_seed(125, label))
    return {
        "reflation_years_n": int(len(a)),
        "other_years_n": int(len(b)),
        "reflation_mean": float(a.mean()),
        "other_mean": float(b.mean()),
        "mean_lift": float(a.mean() - b.mean()),
        "reflation_median": float(np.median(a)),
        "other_median": float(np.median(b)),
        "median_lift": float(np.median(a) - np.median(b)),
        "ci_low": lo,
        "ci_high": hi,
    }


def same_year_bridge(hmra: pd.DataFrame, annual: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    x = annual.merge(
        hmra[["year", "core_regime"]],
        on="year",
        how="inner",
        validate="one_to_one",
    ).sort_values("year").reset_index(drop=True)
    x["hmra_reflation"] = x["core_regime"].eq(HMRA_REFLATION)

    primary = {
        "r3": compare_feature(x, "r3_share", "r3"),
        "growth_high": compare_feature(x, "growth_high_share", "growth_high"),
        "inflation_high": compare_feature(x, "inflation_high_share", "inflation_high"),
    }

    regime_lifts = {}
    for rid in range(1, 10):
        c = compare_feature(x, f"r{rid}_share", f"r{rid}")
        regime_lifts[str(rid)] = c
    lift_values = {rid: v["mean_lift"] for rid, v in regime_lifts.items()}
    max_lift = max(lift_values.values())
    r3_specific = lift_values["3"] > 0 and lift_values["3"] >= max_lift - 1e-12

    loo = {}
    refl_years = x.loc[x["hmra_reflation"], "year"].astype(int).tolist()
    for year in refl_years:
        z = x.loc[x["year"].ne(year)].copy()
        a = z.loc[z["hmra_reflation"], "r3_share"]
        b = z.loc[~z["hmra_reflation"], "r3_share"]
        loo[str(year)] = {
            "remaining_reflation_years": int(len(a)),
            "r3_mean_lift": float(a.mean() - b.mean()) if len(a) and len(b) else math.nan,
        }

    return x, {
        "years": int(len(x)),
        "hmra_reflation_years": int(x["hmra_reflation"].sum()),
        "primary": primary,
        "regime_specificity": {
            "lifts": {k: float(v) for k, v in lift_values.items()},
            "largest_lift": float(max_lift),
            "r3_is_largest_positive": bool(r3_specific),
            "ranking": sorted(
                [{"regime_id": int(k), "lift": float(v)} for k, v in lift_values.items()],
                key=lambda d: d["lift"],
                reverse=True,
            ),
        },
        "leave_one_reflation_year_out": loo,
    }


def binary_diagnostics(monthly: pd.DataFrame, hmra: pd.DataFrame) -> dict:
    m = monthly.merge(
        hmra[["year", "core_regime"]],
        on="year",
        how="inner",
        validate="many_to_one",
    )
    h = m["core_regime"].eq(HMRA_REFLATION)
    e = m["regime_id"].eq(3)
    tp = int((h & e).sum())
    fp = int((h & ~e).sum())
    fn = int((~h & e).sum())
    tn = int((~h & ~e).sum())
    return {
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "accuracy": float((tp + tn) / len(m)),
        "precision": float(tp / (tp + fp)) if tp + fp else math.nan,
        "recall": float(tp / (tp + fn)) if tp + fn else math.nan,
        "jaccard": float(tp / (tp + fp + fn)) if tp + fp + fn else math.nan,
    }


def timing_diag(hmra: pd.DataFrame, annual: pd.DataFrame, offset: int) -> dict:
    h = hmra[["year", "core_regime"]].copy()
    h["target_year"] = h["year"].astype(int) + offset
    h = h.rename(columns={"year": "signal_year"})
    x = annual.rename(columns={"year": "target_year"}).merge(
        h, on="target_year", how="inner", validate="one_to_one"
    )
    x["hmra_reflation"] = x["core_regime"].eq(HMRA_REFLATION)
    if x["hmra_reflation"].sum() == 0 or (~x["hmra_reflation"]).sum() == 0:
        return {"years": int(len(x)), "available": False}
    return {
        "years": int(len(x)),
        "available": True,
        "r3": compare_feature(x, "r3_share", f"tplus{offset}-r3"),
        "growth_high": compare_feature(x, "growth_high_share", f"tplus{offset}-growth"),
        "inflation_high": compare_feature(x, "inflation_high_share", f"tplus{offset}-inflation"),
    }


def main() -> None:
    validate_prereg()
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    hmra = load_hmra()
    transitions = load_transitions()
    monthly = monthly_exact(transitions)
    annual = annual_features(monthly)
    joined, bridge = same_year_bridge(hmra, annual)

    binary = binary_diagnostics(monthly, hmra)
    t1 = timing_diag(hmra, annual, 1)
    t2 = timing_diag(hmra, annual, 2)

    p = bridge["primary"]
    loo = bridge["leave_one_reflation_year_out"]
    all_loo_pos = bool(loo) and all(v["r3_mean_lift"] > 0 for v in loo.values())

    gate = {
        "1_at_least_15_common_years": bridge["years"] >= 15,
        "2_at_least_3_hmra_reflation_years": bridge["hmra_reflation_years"] >= 3,
        "3_r3_lift_positive": p["r3"]["mean_lift"] > 0,
        "4_r3_ci_positive": p["r3"]["ci_low"] > 0,
        "5_growth_high_lift_positive": p["growth_high"]["mean_lift"] > 0,
        "6_growth_high_ci_positive": p["growth_high"]["ci_low"] > 0,
        "7_inflation_high_lift_positive": p["inflation_high"]["mean_lift"] > 0,
        "8_inflation_high_ci_positive": p["inflation_high"]["ci_low"] > 0,
        "9_r3_largest_positive_regime_lift": bridge["regime_specificity"]["r3_is_largest_positive"],
        "10_all_reflation_year_leaveouts_positive": all_loo_pos,
    }

    sufficient = gate["1_at_least_15_common_years"] and gate["2_at_least_3_hmra_reflation_years"]
    semantic_related = (
        sufficient
        and gate["5_growth_high_lift_positive"]
        and gate["7_inflation_high_lift_positive"]
        and (gate["6_growth_high_ci_positive"] or gate["8_inflation_high_ci_positive"])
    )

    if not sufficient:
        verdict = "bridge_inconclusive_small_overlap"
    elif all(gate.values()):
        verdict = "bridge_supports_hmra_to_exact_v66_reflation_translation"
    elif semantic_related:
        verdict = "bridge_semantically_related_but_not_reflation_specific"
    else:
        verdict = "bridge_weak_or_mismatched"

    joined_path = args.output_dir / "issue-125-annual-bridge.csv"
    joined.to_csv(joined_path, index=False, float_format="%.12g")
    monthly_path = args.output_dir / "issue-125-monthly-exact.csv"
    monthly.to_csv(monthly_path, index=False)

    result = {
        "schema_version": 1,
        "issue": 125,
        "phase": "hmra-to-exact-v66-reflation-bridge",
        "verdict": verdict,
        "production_authorized": False,
        "bridge": bridge,
        "binary_monthly_diagnostic": binary,
        "timing_diagnostics": {"t_plus_1": t1, "t_plus_2": t2},
        "gate": gate,
        "gate_pass_count": int(sum(bool(v) for v in gate.values())),
        "source_hashes": {
            "exact_v66_transitions_sha256": sha256_file(TRANSITIONS),
        },
        "output_hashes": {
            "annual_bridge_csv_sha256": sha256_file(joined_path),
            "monthly_exact_csv_sha256": sha256_file(monthly_path),
        },
    }

    (args.output_dir / "issue-125-result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "verdict": verdict,
        "gate": gate,
        "years": bridge["years"],
        "hmra_reflation_years": bridge["hmra_reflation_years"],
        "primary": bridge["primary"],
        "specificity": bridge["regime_specificity"],
        "leaveout": bridge["leave_one_reflation_year_out"],
        "binary": binary,
        "t1": t1,
        "t2": t2,
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
