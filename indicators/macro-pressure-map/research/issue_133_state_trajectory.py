#!/usr/bin/env python3
"""Issue #133 — preregistered State x Trajectory evaluator.

Modern layer:
  exact V6.6 monthly raw GPI/IPI snapshot supplied through TradingView Pine Logs
  + frozen Issue #64 SPY/TLT adjusted-price snapshot.

Long-history layer:
  frozen Issue #91 HMRA-v0.1 + Damodaran/JST source pipeline reused through
  Issue #121. HMRA is a structural analogue, never relabeled exact V6.6.
"""
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import importlib
import io
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
SIGNAL_B64 = DATA / "issue-133-exact-monthly.csv.gz.b64"
SIGNAL_MANIFEST = DATA / "issue-133-exact-monthly-manifest.json"
R7 = "Slowdown / Disinflation"
BOOTSTRAP_REPS = 10_000


def _seed(*parts: object) -> int:
    raw = "|".join(map(str, parts)).encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big") & 0xFFFFFFFF


def _finite(x: pd.Series) -> np.ndarray:
    a = pd.to_numeric(x, errors="coerce").to_numpy(float)
    return a[np.isfinite(a)]


def summary(x: pd.Series) -> dict:
    a = _finite(x)
    if not len(a):
        return {"n": 0, "mean": None, "median": None, "positive_fraction": None}
    return {
        "n": int(len(a)),
        "mean": float(a.mean()),
        "median": float(np.median(a)),
        "positive_fraction": float(np.mean(a > 0)),
    }


def bootstrap_diff(a: pd.Series, b: pd.Series, key: str) -> dict:
    aa, bb = _finite(a), _finite(b)
    if not len(aa) or not len(bb):
        return {"n_a": int(len(aa)), "n_b": int(len(bb)), "mean_diff": None, "ci_low": None, "ci_high": None}
    rng = np.random.default_rng(_seed(133, key))
    ia = rng.integers(0, len(aa), size=(BOOTSTRAP_REPS, len(aa)))
    ib = rng.integers(0, len(bb), size=(BOOTSTRAP_REPS, len(bb)))
    d = aa[ia].mean(axis=1) - bb[ib].mean(axis=1)
    lo, hi = np.quantile(d, [0.025, 0.975])
    return {
        "n_a": int(len(aa)),
        "n_b": int(len(bb)),
        "mean_diff": float(aa.mean() - bb.mean()),
        "ci_low": float(lo),
        "ci_high": float(hi),
    }


def load_exact_signals() -> tuple[pd.DataFrame, dict]:
    manifest = json.loads(SIGNAL_MANIFEST.read_text(encoding="utf-8"))
    gz = base64.b64decode(SIGNAL_B64.read_text(encoding="utf-8").strip(), validate=True)
    if hashlib.sha256(gz).hexdigest() != manifest["deterministic_gzip_sha256"]:
        raise RuntimeError("Issue #133 exact signal gzip hash mismatch")
    csv_bytes = gzip.decompress(gz)
    if hashlib.sha256(csv_bytes).hexdigest() != manifest["normalized_csv_sha256"]:
        raise RuntimeError("Issue #133 exact signal CSV hash mismatch")
    x = pd.read_csv(io.BytesIO(csv_bytes))
    if list(x.columns) != ["date", "gpi", "ipi", "regime"]:
        raise RuntimeError(f"unexpected Issue #133 signal columns: {list(x.columns)}")
    x["date"] = pd.to_datetime(x["date"], errors="raise").dt.normalize()
    for c in ("gpi", "ipi", "regime"):
        x[c] = pd.to_numeric(x[c], errors="raise")
    x["regime"] = x["regime"].astype(int)
    if len(x) != manifest["rows"] or x["date"].duplicated().any():
        raise RuntimeError("Issue #133 signal snapshot shape drift")
    return x.sort_values("date").reset_index(drop=True), manifest


def load_modern_prices(modern_root: Path) -> tuple[pd.DataFrame, dict]:
    sys.path.insert(0, str(modern_root))
    try:
        mod = importlib.import_module("issue_64_outcome_snapshot")
        prices, meta = mod.load_frozen_prices("2007-01-01", None)
    finally:
        sys.path.pop(0)
    return prices[["SPY", "TLT"]].copy(), meta


def _segment(d: pd.Timestamp) -> str:
    if d.year < 2020:
        return "pre-2020"
    if d.year <= 2022:
        return "2020-2022"
    return "2023+"


def _episode_ids(flag: pd.Series, dates: pd.Series) -> pd.Series:
    ids = []
    eid = 0
    prev_flag = False
    prev_period = None
    for f, d in zip(flag.astype(bool), pd.to_datetime(dates)):
        p = d.to_period("M")
        consecutive = prev_period is not None and p.ordinal == prev_period.ordinal + 1
        if f and (not prev_flag or not consecutive):
            eid += 1
        ids.append(eid if f else 0)
        prev_flag = bool(f)
        prev_period = p
    return pd.Series(ids, index=flag.index, dtype=int)


def run_modern(modern_root: Path, out: Path) -> dict:
    sig, sig_manifest = load_exact_signals()
    prices, price_meta = load_modern_prices(modern_root)

    # Primary exact-modern window. Pre-2007 rows remain audit context only.
    x = sig.loc[sig["date"].ge("2007-01-01")].copy().reset_index(drop=True)
    x["dg3"] = x["gpi"] - x["gpi"].shift(3)
    x["di3"] = x["ipi"] - x["ipi"].shift(3)
    x["dg1"] = x["gpi"] - x["gpi"].shift(1)
    x["di1"] = x["ipi"] - x["ipi"].shift(1)
    x["traj3"] = np.select(
        [
            (x.dg3 > 0) & (x.di3 > 0),
            (x.dg3 > 0) & (x.di3 <= 0),
            (x.dg3 <= 0) & (x.di3 > 0),
        ],
        ["GPI_up_IPI_up", "GPI_up_IPI_flat_or_down", "GPI_flat_or_down_IPI_up"],
        default="GPI_flat_or_down_IPI_flat_or_down",
    )
    x["r7_recovering"] = (x["regime"] == 7) & (x["dg3"] > 0) & (x["di3"] > 0)
    x["r7_recovering_1m_sensitivity"] = (x["regime"] == 7) & (x["dg1"] > 0) & (x["di1"] > 0)
    x["episode_id"] = _episode_ids(x["r7_recovering"], x["date"])
    x["segment"] = x["date"].map(_segment)

    # Exact month-end join to the already-frozen adjusted-price panel.
    px = prices.reset_index().rename(columns={prices.index.name or "index": "date"})
    px["date"] = pd.to_datetime(px["date"]).dt.normalize()
    x = x.merge(px, on="date", how="left", validate="one_to_one")
    x["spy_next"] = x["SPY"].shift(-1)
    x["tlt_next"] = x["TLT"].shift(-1)
    x["fwd_spy_1m"] = x["spy_next"] / x["SPY"] - 1.0
    x["fwd_tlt_1m"] = x["tlt_next"] / x["TLT"] - 1.0
    x["fwd_spy_tlt_1m"] = x["fwd_spy_1m"] - x["fwd_tlt_1m"]
    x["spy_next3"] = x["SPY"].shift(-3)
    x["tlt_next3"] = x["TLT"].shift(-3)
    x["fwd_spy_3m"] = x["spy_next3"] / x["SPY"] - 1.0
    x["fwd_tlt_3m"] = x["tlt_next3"] / x["TLT"] - 1.0
    x["fwd_spy_tlt_3m"] = x["fwd_spy_3m"] - x["fwd_tlt_3m"]

    eligible = x.loc[x["dg3"].notna() & x["fwd_spy_tlt_1m"].notna()].copy()
    r7 = eligible.loc[eligible["regime"].eq(7)].copy()
    rec = r7.loc[r7["r7_recovering"]].copy()
    non = r7.loc[~r7["r7_recovering"]].copy()
    inc = bootstrap_diff(rec["fwd_spy_tlt_1m"], non["fwd_spy_tlt_1m"], "modern-primary")
    episodes = int(rec["episode_id"].nunique()) if len(rec) else 0

    seg_rows = []
    for s in ("pre-2020", "2020-2022", "2023+"):
        g = r7.loc[r7["segment"].eq(s)]
        a, b = g.loc[g["r7_recovering"]], g.loc[~g["r7_recovering"]]
        d = bootstrap_diff(a["fwd_spy_tlt_1m"], b["fwd_spy_tlt_1m"], f"modern-segment-{s}")
        seg_rows.append({"segment": s, **d})
    seg = pd.DataFrame(seg_rows)

    # Leave one recovering episode out.
    loeo = []
    for eid in sorted(rec["episode_id"].unique()):
        left = r7.loc[~r7["episode_id"].eq(eid)]
        a, b = left.loc[left["r7_recovering"]], left.loc[~left["r7_recovering"]]
        d = bootstrap_diff(a["fwd_spy_tlt_1m"], b["fwd_spy_tlt_1m"], f"modern-loeo-{eid}")
        loeo.append({"episode_id": int(eid), **d})
    loeo_df = pd.DataFrame(loeo)

    # Positive episode concentration uses sum of positive primary spread.
    ep_contrib = rec.assign(pos=rec["fwd_spy_tlt_1m"].clip(lower=0)).groupby("episode_id")["pos"].sum()
    ep_share = float(ep_contrib.max() / ep_contrib.sum()) if len(ep_contrib) and ep_contrib.sum() > 0 else None

    evaluable_segments = seg.loc[seg["n_a"].ge(1) & seg["n_b"].ge(1)].copy()
    positive_segments = int(evaluable_segments["mean_diff"].gt(0).sum()) if len(evaluable_segments) else 0
    delayed = r7.copy()
    delayed["delayed_recovering"] = delayed["r7_recovering"].shift(1).fillna(False)
    delayed_a = delayed.loc[delayed["delayed_recovering"]]
    delayed_b = delayed.loc[~delayed["delayed_recovering"]]
    delayed_inc = bootstrap_diff(delayed_a["fwd_spy_tlt_1m"], delayed_b["fwd_spy_tlt_1m"], "modern-delay")

    gates = {
        "1_n_ge_12": len(rec) >= 12,
        "2_episodes_ge_4": episodes >= 4,
        "3_recovering_mean_positive": bool(len(rec) and rec["fwd_spy_tlt_1m"].mean() > 0),
        "4_incremental_mean_positive": bool(inc["mean_diff"] is not None and inc["mean_diff"] > 0),
        "5_incremental_ci_low_gt_0": bool(inc["ci_low"] is not None and inc["ci_low"] > 0),
        "6_at_least_2_segments_evaluable": len(evaluable_segments) >= 2,
        "7_segment_sign_requirement": bool(
            (len(evaluable_segments) >= 3 and positive_segments >= 2)
            or (len(evaluable_segments) == 2 and positive_segments == 2)
        ),
        "8_all_evaluable_episode_leaveouts_positive": bool(
            len(loeo_df) and loeo_df["mean_diff"].dropna().gt(0).all()
        ),
        "9_strongest_positive_episode_share_le_50pct": bool(ep_share is not None and ep_share <= 0.50),
        "10_delayed_signal_positive": bool(delayed_inc["mean_diff"] is not None and delayed_inc["mean_diff"] > 0),
    }
    if not gates["1_n_ge_12"] or not gates["2_episodes_ge_4"]:
        verdict = "inconclusive_sample"
    elif all(gates.values()):
        verdict = "state_trajectory_candidate"
    elif gates["4_incremental_mean_positive"]:
        verdict = "trajectory_suggestive_not_robust"
    else:
        verdict = "trajectory_not_confirmed"

    matrix = (
        eligible.groupby(["regime", "traj3"], dropna=False)
        .agg(
            n=("fwd_spy_tlt_1m", "size"),
            mean_spy=("fwd_spy_1m", "mean"),
            mean_tlt=("fwd_tlt_1m", "mean"),
            mean_spread=("fwd_spy_tlt_1m", "mean"),
            median_spread=("fwd_spy_tlt_1m", "median"),
            positive_spread_hit_rate=("fwd_spy_tlt_1m", lambda s: float((s > 0).mean())),
        )
        .reset_index()
    )

    x.to_csv(out / "issue-133-modern-monthly-evidence.csv", index=False, float_format="%.12g")
    r7.to_csv(out / "issue-133-modern-r7-primary.csv", index=False, float_format="%.12g")
    seg.to_csv(out / "issue-133-modern-temporal.csv", index=False, float_format="%.12g")
    loeo_df.to_csv(out / "issue-133-modern-leave-one-episode-out.csv", index=False, float_format="%.12g")
    matrix.to_csv(out / "issue-133-modern-state-trajectory-map.csv", index=False, float_format="%.12g")

    return {
        "source": {
            "signal_manifest": sig_manifest,
            "price_snapshot_last_date": str(prices.index.max().date()),
            "price_snapshot_meta": price_meta,
        },
        "sample": {
            "eligible_months": int(len(eligible)),
            "r7_months": int(len(r7)),
            "r7_recovering_months": int(len(rec)),
            "r7_recovering_episodes": episodes,
            "recovering_dates": [d.date().isoformat() for d in rec["date"]],
        },
        "recovering": summary(rec["fwd_spy_tlt_1m"]),
        "nonrecovering": summary(non["fwd_spy_tlt_1m"]),
        "incremental": inc,
        "strongest_positive_episode_share": ep_share,
        "delayed_incremental": delayed_inc,
        "gates": gates,
        "verdict": verdict,
    }


def load_long_history(long_root: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    sys.path.insert(0, str(long_root))
    try:
        mod = importlib.import_module("issue_121_long_history_rematch")
        structural, causal, manifest = mod.load_issue91_evidence()
    finally:
        sys.path.pop(0)
    return structural, causal, manifest


def run_long(long_root: Path, out: Path) -> dict:
    structural, causal, manifest = load_long_history(long_root)
    state_cols = ["state_year", "growth_score", "inflation_score", "core_regime", "era"]
    states = structural[state_cols].drop_duplicates("state_year").sort_values("state_year").copy()
    states["dg1"] = states["growth_score"] - states["growth_score"].shift(1)
    states["di1"] = states["inflation_score"] - states["inflation_score"].shift(1)
    states["r7_recovering"] = (
        states["core_regime"].eq(R7) & (states["dg1"] > 0) & (states["di1"] > 0)
    )
    labels = states[["state_year", "dg1", "di1", "r7_recovering"]]
    x = causal.merge(labels, on="state_year", how="left", validate="one_to_one")
    x["spread"] = pd.to_numeric(x["equity"], errors="coerce") - pd.to_numeric(x["treasury"], errors="coerce")
    r7 = x.loc[x["core_regime"].eq(R7) & x["dg1"].notna() & x["di1"].notna() & x["spread"].notna()].copy()
    rec = r7.loc[r7["r7_recovering"]].copy()
    non = r7.loc[~r7["r7_recovering"]].copy()
    inc = bootstrap_diff(rec["spread"], non["spread"], "long-primary")

    era_rows = []
    for era, g in r7.groupby("era", sort=True):
        a, b = g.loc[g["r7_recovering"]], g.loc[~g["r7_recovering"]]
        d = bootstrap_diff(a["spread"], b["spread"], f"long-era-{era}")
        era_rows.append({"era": era, **d})
    eras = pd.DataFrame(era_rows)
    eval_eras = eras.loc[eras["n_a"].ge(1) & eras["n_b"].ge(1)].copy()

    loeo = []
    for era in sorted(r7["era"].dropna().astype(str).unique()):
        g = r7.loc[~r7["era"].astype(str).eq(era)]
        a, b = g.loc[g["r7_recovering"]], g.loc[~g["r7_recovering"]]
        d = bootstrap_diff(a["spread"], b["spread"], f"long-loeo-{era}")
        loeo.append({"omitted_era": era, **d})
    loeo_df = pd.DataFrame(loeo)

    # Incremental positive contribution proxy: each recovering observation's
    # spread relative to the full-sample nonrecovering mean, clipped at zero.
    baseline = float(non["spread"].mean()) if len(non) else math.nan
    if len(rec) and np.isfinite(baseline):
        tmp = rec.assign(pos_increment=(rec["spread"] - baseline).clip(lower=0))
        contrib = tmp.groupby("era")["pos_increment"].sum()
        concentration = float(contrib.max() / contrib.sum()) if len(contrib) and contrib.sum() > 0 else None
    else:
        concentration = None

    positive_eval_eras = int(eval_eras["mean_diff"].gt(0).sum()) if len(eval_eras) else 0
    no_bad_era = bool(len(eval_eras) and eval_eras["mean_diff"].dropna().ge(-0.05).all())
    loeo_positive = bool(len(loeo_df) and loeo_df["mean_diff"].dropna().gt(0).all())

    gates = {
        "1_causal_recovering_n_ge_8": len(rec) >= 8,
        "2_recovering_mean_positive": bool(len(rec) and rec["spread"].mean() > 0),
        "3_incremental_mean_positive": bool(inc["mean_diff"] is not None and inc["mean_diff"] > 0),
        "4_incremental_ci_low_gt_0": bool(inc["ci_low"] is not None and inc["ci_low"] > 0),
        "5_at_least_2_evaluable_eras": len(eval_eras) >= 2,
        "6_at_least_2_evaluable_eras_positive": positive_eval_eras >= 2,
        "7_no_evaluable_era_below_minus_5pp": no_bad_era,
        "8_leave_one_era_out_never_negative": loeo_positive,
        "9_strongest_positive_era_share_le_50pct": bool(concentration is not None and concentration <= 0.50),
    }
    if len(rec) < 8 or len(eval_eras) < 2:
        verdict = "inconclusive_long_history_trajectory_sample"
    elif all(gates.values()):
        verdict = "long_history_trajectory_candidate"
    elif gates["3_incremental_mean_positive"]:
        verdict = "long_history_trajectory_era_dependent"
    else:
        verdict = "long_history_trajectory_not_confirmed"

    r7.to_csv(out / "issue-133-long-history-r7-primary.csv", index=False, float_format="%.12g")
    eras.to_csv(out / "issue-133-long-history-era.csv", index=False, float_format="%.12g")
    loeo_df.to_csv(out / "issue-133-long-history-leave-one-era-out.csv", index=False, float_format="%.12g")

    return {
        "source": {
            "issue91_hmra_freeze_validated": bool(manifest["hmra_freeze_validated_before_asset_join"]),
            "causal_return_last_year": int(manifest["pairings"]["strict_causal_t_plus_2"]["last_return_year"]),
            "damodaran_sha256": manifest["sources"]["damodaran"]["raw_sha256"],
        },
        "sample": {
            "r7_causal_years": int(len(r7)),
            "r7_recovering_years": int(len(rec)),
            "r7_recovering_state_years": [int(y) for y in rec["state_year"]],
            "evaluable_eras": int(len(eval_eras)),
        },
        "recovering": summary(rec["spread"]),
        "nonrecovering": summary(non["spread"]),
        "incremental": inc,
        "strongest_positive_era_share": concentration,
        "gates": gates,
        "verdict": verdict,
    }


def synthesis(modern: str, long: str) -> str:
    mp = modern == "state_trajectory_candidate"
    lp = long == "long_history_trajectory_candidate"
    mi = modern == "inconclusive_sample"
    li = long == "inconclusive_long_history_trajectory_sample"
    if mp and lp:
        return "cross_history_trajectory_supported"
    if mp and not lp:
        return "modern_only_trajectory_support"
    if lp and not mp:
        return "long_history_only_trajectory_support"
    if mi or li:
        return "trajectory_evidence_inconclusive"
    return "trajectory_not_robust_across_history"


def run(modern_root: Path, long_root: Path, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    modern = run_modern(modern_root, out)
    long = run_long(long_root, out)
    result = {
        "schema_version": 1,
        "issue": 133,
        "phase": "state-x-trajectory-early-recovery",
        "modern_exact": modern,
        "long_history_hmra": long,
        "cross_history_synthesis": synthesis(modern["verdict"], long["verdict"]),
        "production_authorized": False,
    }
    (out / "issue-133-result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    finding = [
        "# Issue #133 — State × Trajectory finding",
        "",
        f"Modern exact verdict: **{modern['verdict']}**",
        f"Long-history HMRA verdict: **{long['verdict']}**",
        f"Cross-history synthesis: **{result['cross_history_synthesis']}**",
        "",
        f"Modern exact R7 recovering sample: {modern['sample']['r7_recovering_months']} months / {modern['sample']['r7_recovering_episodes']} episodes.",
        f"Long-history HMRA R7 recovering causal sample: {long['sample']['r7_recovering_years']} years.",
        "",
        "HMRA is a historical structural analogue, not exact V6.6.",
        "No production rule is authorized by this finding.",
    ]
    (out / "issue-133-finding.md").write_text("\n".join(finding) + "\n", encoding="utf-8")
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--modern-root", type=Path, required=True)
    ap.add_argument("--long-root", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    result = run(args.modern_root, args.long_root, args.output_dir)
    print(json.dumps({
        "modern_verdict": result["modern_exact"]["verdict"],
        "modern_sample": result["modern_exact"]["sample"],
        "long_verdict": result["long_history_hmra"]["verdict"],
        "long_sample": result["long_history_hmra"]["sample"],
        "synthesis": result["cross_history_synthesis"],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
