#!/usr/bin/env python3
"""Issue #136 — preregistered R7 asynchronous turning-point evaluator.

Primary exact-modern signal:
- exact V6.6 Regime 7;
- each raw monthly axis turns when dX_t > 0 and dX_(t-1) <= 0;
- both axis-turn events occurred within {t, t-1, t-2};
- only the first completion inside a contiguous R7 episode is a primary signal;
- primary payoff is next-3M SPY minus TLT;
- primary CI is an R7-episode cluster bootstrap.

Long-history layer:
- frozen Issue #91 / #121 HMRA structural analogue;
- annual turn-event analogue with a two-year completion window;
- strict causal state_t -> return_(t+2);
- underlying S&P 500 total return minus 10Y Treasury total return.
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

BOOTSTRAP_REPS = 10_000
R7_NAME = "Slowdown / Disinflation"
EXPECTED_SIGNAL_SHA = "1d03923503e7fe82a69b033897484c48aa646279ecf70164d090ed62a5a70719"


def _seed(*parts: object) -> int:
    raw = "|".join(map(str, parts)).encode("utf-8")
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big") & 0xFFFFFFFF


def _finite(s: pd.Series) -> np.ndarray:
    a = pd.to_numeric(s, errors="coerce").to_numpy(float)
    return a[np.isfinite(a)]


def summary(s: pd.Series) -> dict:
    a = _finite(s)
    if not len(a):
        return {"n": 0, "mean": None, "median": None, "positive_fraction": None}
    return {
        "n": int(len(a)),
        "mean": float(a.mean()),
        "median": float(np.median(a)),
        "positive_fraction": float(np.mean(a > 0)),
    }


def _mean_diff(frame: pd.DataFrame, value_col: str, signal_col: str = "is_signal") -> float | None:
    a = _finite(frame.loc[frame[signal_col], value_col])
    b = _finite(frame.loc[~frame[signal_col], value_col])
    if not len(a) or not len(b):
        return None
    return float(a.mean() - b.mean())


def cluster_bootstrap_diff(
    frame: pd.DataFrame,
    value_col: str,
    *,
    key: str,
    episode_col: str = "episode_id",
    signal_col: str = "is_signal",
) -> dict:
    x = frame.loc[
        frame[episode_col].gt(0)
        & frame[value_col].notna()
        & frame[signal_col].notna()
    ].copy()
    episodes = sorted(x[episode_col].astype(int).unique())
    if not episodes:
        return {
            "episodes": 0,
            "signal_n": 0,
            "control_n": 0,
            "mean_diff": None,
            "ci_low": None,
            "ci_high": None,
            "valid_bootstrap_reps": 0,
        }

    signal = _finite(x.loc[x[signal_col], value_col])
    control = _finite(x.loc[~x[signal_col], value_col])
    if not len(signal) or not len(control):
        return {
            "episodes": int(len(episodes)),
            "signal_n": int(len(signal)),
            "control_n": int(len(control)),
            "mean_diff": None,
            "ci_low": None,
            "ci_high": None,
            "valid_bootstrap_reps": 0,
        }

    clusters = {eid: x.loc[x[episode_col].eq(eid)].copy() for eid in episodes}
    rng = np.random.default_rng(_seed(136, key))
    diffs: list[float] = []
    for _ in range(BOOTSTRAP_REPS):
        draw = rng.choice(episodes, size=len(episodes), replace=True)
        parts = [clusters[int(e)] for e in draw]
        sample = pd.concat(parts, ignore_index=True)
        d = _mean_diff(sample, value_col, signal_col)
        if d is not None and np.isfinite(d):
            diffs.append(float(d))
    if not diffs:
        lo = hi = None
    else:
        lo, hi = [float(v) for v in np.quantile(np.asarray(diffs), [0.025, 0.975])]
    return {
        "episodes": int(len(episodes)),
        "signal_n": int(len(signal)),
        "control_n": int(len(control)),
        "mean_diff": float(signal.mean() - control.mean()),
        "ci_low": lo,
        "ci_high": hi,
        "valid_bootstrap_reps": int(len(diffs)),
    }


def assign_episode_ids(flags: pd.Series, dates: pd.Series, *, annual: bool = False) -> pd.Series:
    ids: list[int] = []
    eid = 0
    prev_flag = False
    prev_key = None
    for flag, d in zip(flags.astype(bool), pd.to_datetime(dates)):
        key = d.year if annual else d.to_period("M").ordinal
        consecutive = prev_key is not None and key == prev_key + 1
        if flag and (not prev_flag or not consecutive):
            eid += 1
        ids.append(eid if flag else 0)
        prev_flag = bool(flag)
        prev_key = key
    return pd.Series(ids, index=flags.index, dtype=int)


def mark_first_triggers(frame: pd.DataFrame, candidate_col: str) -> pd.Series:
    out = pd.Series(False, index=frame.index, dtype=bool)
    for eid, g in frame.loc[frame["episode_id"].gt(0)].groupby("episode_id", sort=True):
        hit = g.index[g[candidate_col].fillna(False)]
        if len(hit):
            out.loc[hit[0]] = True
    return out


def assign_roles(frame: pd.DataFrame, eligible_col: str) -> pd.Series:
    role = pd.Series("ineligible", index=frame.index, dtype="object")
    for eid, g in frame.loc[frame["episode_id"].gt(0)].groupby("episode_id", sort=True):
        trig = g.index[g["is_signal"]]
        if len(trig):
            t = trig[0]
            for idx in g.index:
                if not bool(frame.loc[idx, eligible_col]):
                    continue
                if idx < t:
                    role.loc[idx] = "control"
                elif idx == t:
                    role.loc[idx] = "signal"
                else:
                    role.loc[idx] = "excluded_post_trigger"
        else:
            eligible_idx = g.index[frame.loc[g.index, eligible_col].astype(bool)]
            role.loc[eligible_idx] = "control"
    return role


def recent_turn_offset(turns: pd.Series, idx: int, window: int) -> int | None:
    for offset in range(window):
        j = idx - offset
        if j >= 0 and bool(turns.iloc[j]):
            return offset
    return None


def _segment(d: pd.Timestamp) -> str:
    if d.year < 2020:
        return "pre-2020"
    if d.year <= 2022:
        return "2020-2022"
    return "2023+"


def load_issue133_signals(issue133_root: Path) -> tuple[pd.DataFrame, dict]:
    data = issue133_root / "data"
    manifest = json.loads((data / "issue-133-exact-monthly-manifest.json").read_text(encoding="utf-8"))
    if manifest["normalized_csv_sha256"] != EXPECTED_SIGNAL_SHA:
        raise RuntimeError("Issue #136 source guard: Issue #133 normalized signal SHA drift")
    gz = base64.b64decode((data / "issue-133-exact-monthly.csv.gz.b64").read_text().strip(), validate=True)
    if hashlib.sha256(gz).hexdigest() != manifest["deterministic_gzip_sha256"]:
        raise RuntimeError("Issue #136 source guard: Issue #133 gzip SHA drift")
    csv_bytes = gzip.decompress(gz)
    if hashlib.sha256(csv_bytes).hexdigest() != manifest["normalized_csv_sha256"]:
        raise RuntimeError("Issue #136 source guard: Issue #133 CSV SHA drift")
    x = pd.read_csv(io.BytesIO(csv_bytes))
    if list(x.columns) != ["date", "gpi", "ipi", "regime"]:
        raise RuntimeError(f"unexpected Issue #133 columns: {list(x.columns)}")
    x["date"] = pd.to_datetime(x["date"], errors="raise").dt.normalize()
    x["gpi"] = pd.to_numeric(x["gpi"], errors="raise")
    x["ipi"] = pd.to_numeric(x["ipi"], errors="raise")
    x["regime"] = pd.to_numeric(x["regime"], errors="raise").astype(int)
    if x["date"].duplicated().any():
        raise RuntimeError("duplicate exact monthly date")
    return x.sort_values("date").reset_index(drop=True), manifest


def load_modern_prices(modern_root: Path) -> tuple[pd.DataFrame, dict]:
    sys.path.insert(0, str(modern_root))
    try:
        mod = importlib.import_module("issue_64_outcome_snapshot")
        prices, meta = mod.load_frozen_prices("2007-01-01", None)
    finally:
        sys.path.pop(0)
    return prices[["SPY", "TLT"]].copy(), meta


def build_modern_labels(sig: pd.DataFrame) -> pd.DataFrame:
    x = sig.loc[sig["date"].ge("2007-01-01")].copy().reset_index(drop=True)
    periods = x["date"].dt.to_period("M").astype(int)
    if len(periods) > 1 and not np.all(np.diff(periods) == 1):
        raise RuntimeError("Issue #136 exact monthly signal has missing calendar months")

    x["dg"] = x["gpi"].diff()
    x["di"] = x["ipi"].diff()
    x["g_turn"] = (x["dg"] > 0) & (x["dg"].shift(1) <= 0)
    x["i_turn"] = (x["di"] > 0) & (x["di"].shift(1) <= 0)
    x["g_recent"] = x["g_turn"].rolling(3, min_periods=3).max().fillna(0).astype(bool)
    x["i_recent"] = x["i_turn"].rolling(3, min_periods=3).max().fillna(0).astype(bool)
    x["turn_history_ok"] = x["gpi"].shift(4).notna() & x["ipi"].shift(4).notna()
    x["is_r7"] = x["regime"].eq(7)
    x["episode_id"] = assign_episode_ids(x["is_r7"], x["date"], annual=False)
    x["async_candidate"] = x["is_r7"] & x["turn_history_ok"] & x["g_recent"] & x["i_recent"]
    x["is_signal"] = mark_first_triggers(x, "async_candidate")
    x["role"] = assign_roles(x, "turn_history_ok")
    x["segment"] = x["date"].map(_segment)

    x["g_turn_offset"] = np.nan
    x["i_turn_offset"] = np.nan
    x["turn_order"] = ""
    x["turn_lag"] = np.nan
    for idx in x.index[x["is_signal"]]:
        go = recent_turn_offset(x["g_turn"], idx, 3)
        io_ = recent_turn_offset(x["i_turn"], idx, 3)
        if go is None or io_ is None:
            raise RuntimeError("signal without both recent turns")
        x.loc[idx, "g_turn_offset"] = go
        x.loc[idx, "i_turn_offset"] = io_
        x.loc[idx, "turn_lag"] = abs(go - io_)
        if go == io_:
            order = "same_month"
        elif go > io_:
            order = "GPI_first"
        else:
            order = "IPI_first"
        x.loc[idx, "turn_order"] = order
    return x


def add_modern_outcomes(x: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    px = prices.reset_index().rename(columns={prices.index.name or "index": "date"})
    px["date"] = pd.to_datetime(px["date"]).dt.normalize()
    out = x.merge(px, on="date", how="left", validate="one_to_one")
    for h in (1, 3, 6):
        out[f"spy_fwd_{h}m"] = out["SPY"].shift(-h) / out["SPY"] - 1.0
        out[f"tlt_fwd_{h}m"] = out["TLT"].shift(-h) / out["TLT"] - 1.0
        out[f"spread_fwd_{h}m"] = out[f"spy_fwd_{h}m"] - out[f"tlt_fwd_{h}m"]
    out["spy_delay1_fwd_3m"] = out["SPY"].shift(-4) / out["SPY"].shift(-1) - 1.0
    out["tlt_delay1_fwd_3m"] = out["TLT"].shift(-4) / out["TLT"].shift(-1) - 1.0
    out["spread_delay1_fwd_3m"] = out["spy_delay1_fwd_3m"] - out["tlt_delay1_fwd_3m"]
    return out


def modern_trigger_descriptive(x: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for idx in x.index[x["is_signal"]]:
        row = x.loc[idx]
        future = x.loc[x.index > idx]
        exit_rows = future.loc[~future["is_r7"]]
        exit_date = None
        exit_regime = None
        months_to_exit = None
        if len(exit_rows):
            e = exit_rows.iloc[0]
            exit_date = e["date"].date().isoformat()
            exit_regime = int(e["regime"])
            months_to_exit = int(e["date"].to_period("M").ordinal - row["date"].to_period("M").ordinal)
        rows.append({
            "signal_date": row["date"].date().isoformat(),
            "episode_id": int(row["episode_id"]),
            "turn_order": row["turn_order"],
            "turn_lag_months": int(row["turn_lag"]),
            "spread_fwd_1m": row["spread_fwd_1m"],
            "spread_fwd_3m": row["spread_fwd_3m"],
            "spread_fwd_6m": row["spread_fwd_6m"],
            "spread_delay1_fwd_3m": row["spread_delay1_fwd_3m"],
            "first_non_r7_date": exit_date,
            "first_non_r7_regime": exit_regime,
            "months_to_r7_exit": months_to_exit,
        })
    return pd.DataFrame(rows)


def modern_leave_one_episode_out(analysis: pd.DataFrame) -> pd.DataFrame:
    rows = []
    trigger_eps = sorted(analysis.loc[analysis["is_signal"], "episode_id"].astype(int).unique())
    for eid in trigger_eps:
        left = analysis.loc[~analysis["episode_id"].eq(eid)].copy()
        d = _mean_diff(left, "spread_fwd_3m")
        rows.append({
            "omitted_episode_id": int(eid),
            "remaining_signal_n": int(left["is_signal"].sum()),
            "remaining_control_n": int((~left["is_signal"]).sum()),
            "mean_diff": d,
            "evaluable": d is not None,
        })
    return pd.DataFrame(rows)


def run_modern(issue133_root: Path, modern_root: Path, outdir: Path) -> dict:
    sig, manifest = load_issue133_signals(issue133_root)
    prices, price_meta = load_modern_prices(modern_root)
    x = add_modern_outcomes(build_modern_labels(sig), prices)

    analysis = x.loc[
        x["role"].isin(["signal", "control"])
        & x["spread_fwd_3m"].notna()
    ].copy()
    analysis["is_signal"] = analysis["role"].eq("signal")

    primary = cluster_bootstrap_diff(analysis, "spread_fwd_3m", key="modern-primary")
    delayed = cluster_bootstrap_diff(analysis, "spread_delay1_fwd_3m", key="modern-delay")

    temporal_rows = []
    for seg in ("pre-2020", "2020-2022", "2023+"):
        g = analysis.loc[analysis["segment"].eq(seg)]
        d = _mean_diff(g, "spread_fwd_3m")
        temporal_rows.append({
            "segment": seg,
            "signal_n": int(g["is_signal"].sum()),
            "control_n": int((~g["is_signal"]).sum()),
            "mean_diff": d,
            "evaluable": d is not None,
        })
    temporal = pd.DataFrame(temporal_rows)

    loeo = modern_leave_one_episode_out(analysis)
    sig_rows = analysis.loc[analysis["is_signal"]].copy()
    pos = sig_rows["spread_fwd_3m"].clip(lower=0)
    concentration = float(pos.max() / pos.sum()) if len(pos) and pos.sum() > 0 else None

    eval_segments = temporal.loc[temporal["evaluable"]]
    positive_segments = int(eval_segments["mean_diff"].gt(0).sum()) if len(eval_segments) else 0
    leaveout_ok = bool(len(loeo) and loeo["evaluable"].all() and loeo["mean_diff"].gt(0).all())
    gates = {
        "1_trigger_episodes_ge_8": int(sig_rows["episode_id"].nunique()) >= 8,
        "2_signal_mean_positive": bool(len(sig_rows) and sig_rows["spread_fwd_3m"].mean() > 0),
        "3_incremental_mean_positive": bool(primary["mean_diff"] is not None and primary["mean_diff"] > 0),
        "4_cluster_ci_low_gt_0": bool(primary["ci_low"] is not None and primary["ci_low"] > 0),
        "5_at_least_2_segments_evaluable": len(eval_segments) >= 2,
        "6_segment_sign_requirement": bool(
            (len(eval_segments) >= 3 and positive_segments >= 2)
            or (len(eval_segments) == 2 and positive_segments == 2)
        ),
        "7_leave_one_trigger_episode_out_positive": leaveout_ok,
        "8_strongest_positive_trigger_share_le_50pct": bool(concentration is not None and concentration <= 0.50),
        "9_delayed_incremental_positive": bool(delayed["mean_diff"] is not None and delayed["mean_diff"] > 0),
    }
    trigger_n = int(sig_rows["episode_id"].nunique())
    if trigger_n < 8:
        verdict = "inconclusive_async_turn_sample"
    elif all(gates.values()):
        verdict = "async_turn_candidate"
    elif gates["3_incremental_mean_positive"]:
        verdict = "async_turn_suggestive_not_robust"
    else:
        verdict = "async_turn_not_confirmed"

    x.to_csv(outdir / "issue-136-modern-monthly-evidence.csv", index=False, float_format="%.12g")
    analysis.to_csv(outdir / "issue-136-modern-primary-analysis.csv", index=False, float_format="%.12g")
    temporal.to_csv(outdir / "issue-136-modern-temporal.csv", index=False, float_format="%.12g")
    loeo.to_csv(outdir / "issue-136-modern-leave-one-trigger-episode-out.csv", index=False, float_format="%.12g")
    modern_trigger_descriptive(x).to_csv(outdir / "issue-136-modern-trigger-descriptive.csv", index=False, float_format="%.12g")

    return {
        "source": {
            "issue133_signal_manifest": manifest,
            "modern_price_snapshot_last_date": str(prices.index.max().date()),
            "modern_price_snapshot_meta": price_meta,
        },
        "sample": {
            "eligible_primary_rows": int(len(analysis)),
            "r7_episodes_in_primary": int(analysis["episode_id"].nunique()),
            "trigger_episodes": trigger_n,
            "trigger_dates": [d.date().isoformat() for d in sig_rows["date"]],
            "trigger_orders": sig_rows["turn_order"].value_counts().sort_index().to_dict(),
        },
        "signal": summary(sig_rows["spread_fwd_3m"]),
        "control": summary(analysis.loc[~analysis["is_signal"], "spread_fwd_3m"]),
        "primary_incremental": primary,
        "delayed_incremental": delayed,
        "strongest_positive_trigger_share": concentration,
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


def build_long_labels(structural: pd.DataFrame) -> pd.DataFrame:
    cols = ["state_year", "growth_score", "inflation_score", "core_regime", "era"]
    x = structural[cols].drop_duplicates("state_year").sort_values("state_year").copy().reset_index(drop=True)
    if len(x) > 1 and not np.all(np.diff(x["state_year"].to_numpy(int)) == 1):
        raise RuntimeError("Issue #136 HMRA states are not consecutive annual observations")
    x["date"] = pd.to_datetime(x["state_year"].astype(str) + "-12-31")
    x["dg"] = x["growth_score"].diff()
    x["di"] = x["inflation_score"].diff()
    x["g_turn"] = (x["dg"] > 0) & (x["dg"].shift(1) <= 0)
    x["i_turn"] = (x["di"] > 0) & (x["di"].shift(1) <= 0)
    x["g_recent"] = x["g_turn"].rolling(2, min_periods=2).max().fillna(0).astype(bool)
    x["i_recent"] = x["i_turn"].rolling(2, min_periods=2).max().fillna(0).astype(bool)
    x["turn_history_ok"] = x["growth_score"].shift(3).notna() & x["inflation_score"].shift(3).notna()
    x["is_r7"] = x["core_regime"].eq(R7_NAME)
    x["episode_id"] = assign_episode_ids(x["is_r7"], x["date"], annual=True)
    x["async_candidate"] = x["is_r7"] & x["turn_history_ok"] & x["g_recent"] & x["i_recent"]
    x["is_signal"] = mark_first_triggers(x, "async_candidate")
    x["role"] = assign_roles(x, "turn_history_ok")

    x["g_turn_offset"] = np.nan
    x["i_turn_offset"] = np.nan
    x["turn_order"] = ""
    x["turn_lag"] = np.nan
    for idx in x.index[x["is_signal"]]:
        go = recent_turn_offset(x["g_turn"], idx, 2)
        io_ = recent_turn_offset(x["i_turn"], idx, 2)
        if go is None or io_ is None:
            raise RuntimeError("HMRA signal without both recent turns")
        x.loc[idx, "g_turn_offset"] = go
        x.loc[idx, "i_turn_offset"] = io_
        x.loc[idx, "turn_lag"] = abs(go - io_)
        x.loc[idx, "turn_order"] = "same_year" if go == io_ else ("Growth_first" if go > io_ else "Inflation_first")
    return x


def long_trigger_descriptive(labels: pd.DataFrame, causal_analysis: pd.DataFrame) -> pd.DataFrame:
    payoff = causal_analysis.loc[causal_analysis["is_signal"], [
        "state_year", "return_year", "equity", "treasury", "spread"
    ]].copy()
    rows = []
    for idx in labels.index[labels["is_signal"]]:
        row = labels.loc[idx]
        future = labels.loc[labels.index > idx]
        exit_rows = future.loc[~future["is_r7"]]
        exit_year = None
        exit_regime = None
        years_to_exit = None
        if len(exit_rows):
            e = exit_rows.iloc[0]
            exit_year = int(e["state_year"])
            exit_regime = str(e["core_regime"])
            years_to_exit = int(e["state_year"] - row["state_year"])
        rows.append({
            "state_year": int(row["state_year"]),
            "episode_id": int(row["episode_id"]),
            "turn_order": row["turn_order"],
            "turn_lag_years": int(row["turn_lag"]),
            "first_non_r7_year": exit_year,
            "first_non_r7_regime": exit_regime,
            "years_to_r7_exit": years_to_exit,
        })
    desc = pd.DataFrame(rows)
    return desc.merge(payoff, on="state_year", how="left", validate="one_to_one")


def long_leave_one_era_out(analysis: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for era in sorted(analysis["era"].dropna().astype(str).unique()):
        left = analysis.loc[~analysis["era"].astype(str).eq(era)].copy()
        d = _mean_diff(left, "spread")
        rows.append({
            "omitted_era": era,
            "signal_n": int(left["is_signal"].sum()),
            "control_n": int((~left["is_signal"]).sum()),
            "mean_diff": d,
            "evaluable": d is not None,
        })
    return pd.DataFrame(rows)


def long_leave_one_trigger_episode_out(analysis: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for eid in sorted(analysis.loc[analysis["is_signal"], "episode_id"].astype(int).unique()):
        left = analysis.loc[~analysis["episode_id"].eq(eid)].copy()
        d = _mean_diff(left, "spread")
        rows.append({
            "omitted_episode_id": int(eid),
            "signal_n": int(left["is_signal"].sum()),
            "control_n": int((~left["is_signal"]).sum()),
            "mean_diff": d,
            "evaluable": d is not None,
        })
    return pd.DataFrame(rows)


def run_long(long_root: Path, outdir: Path) -> dict:
    structural, causal, manifest = load_long_history(long_root)
    labels = build_long_labels(structural)
    keep = ["state_year", "episode_id", "turn_history_ok", "is_signal", "role", "turn_order", "turn_lag"]
    x = causal.merge(labels[keep], on="state_year", how="left", validate="one_to_one")
    x["spread"] = pd.to_numeric(x["equity"], errors="coerce") - pd.to_numeric(x["treasury"], errors="coerce")
    analysis = x.loc[x["role"].isin(["signal", "control"]) & x["spread"].notna()].copy()
    analysis["is_signal"] = analysis["role"].eq("signal")

    primary = cluster_bootstrap_diff(analysis, "spread", key="long-primary")
    sig_rows = analysis.loc[analysis["is_signal"]]
    control_rows = analysis.loc[~analysis["is_signal"]]

    era_rows = []
    for era, g in analysis.groupby("era", sort=True):
        d = _mean_diff(g, "spread")
        era_rows.append({
            "era": str(era),
            "signal_n": int(g["is_signal"].sum()),
            "control_n": int((~g["is_signal"]).sum()),
            "mean_diff": d,
            "evaluable": d is not None,
        })
    eras = pd.DataFrame(era_rows)
    eval_eras = eras.loc[eras["evaluable"]].copy()

    loeo_era = long_leave_one_era_out(analysis)
    loeo_episode = long_leave_one_trigger_episode_out(analysis)

    baseline = float(control_rows["spread"].mean()) if len(control_rows) else math.nan
    if len(sig_rows) and np.isfinite(baseline):
        tmp = sig_rows.assign(pos_increment=(sig_rows["spread"] - baseline).clip(lower=0))
        contrib = tmp.groupby("era")["pos_increment"].sum()
        concentration = float(contrib.max() / contrib.sum()) if len(contrib) and contrib.sum() > 0 else None
    else:
        concentration = None

    positive_eras = int(eval_eras["mean_diff"].gt(0).sum()) if len(eval_eras) else 0
    no_bad_era = bool(len(eval_eras) and eval_eras["mean_diff"].ge(-0.05).all())
    era_leaveout_ok = bool(
        len(loeo_era)
        and loeo_era["evaluable"].all()
        and loeo_era["mean_diff"].gt(0).all()
    )
    gates = {
        "1_trigger_observations_ge_8": int(len(sig_rows)) >= 8,
        "2_signal_mean_positive": bool(len(sig_rows) and sig_rows["spread"].mean() > 0),
        "3_incremental_mean_positive": bool(primary["mean_diff"] is not None and primary["mean_diff"] > 0),
        "4_cluster_ci_low_gt_0": bool(primary["ci_low"] is not None and primary["ci_low"] > 0),
        "5_at_least_2_eras_evaluable": len(eval_eras) >= 2,
        "6_at_least_2_evaluable_eras_positive": positive_eras >= 2,
        "7_no_evaluable_era_below_minus_5pp": no_bad_era,
        "8_leave_one_era_out_positive": era_leaveout_ok,
        "9_strongest_positive_era_share_le_50pct": bool(concentration is not None and concentration <= 0.50),
    }
    if len(sig_rows) < 8 or len(eval_eras) < 2:
        verdict = "inconclusive_long_history_async_turn_sample"
    elif all(gates.values()):
        verdict = "long_history_async_turn_candidate"
    elif gates["3_incremental_mean_positive"]:
        verdict = "long_history_async_turn_era_dependent"
    else:
        verdict = "long_history_async_turn_not_confirmed"

    x.to_csv(outdir / "issue-136-long-history-evidence.csv", index=False, float_format="%.12g")
    analysis.to_csv(outdir / "issue-136-long-history-primary-analysis.csv", index=False, float_format="%.12g")
    eras.to_csv(outdir / "issue-136-long-history-era.csv", index=False, float_format="%.12g")
    loeo_era.to_csv(outdir / "issue-136-long-history-leave-one-era-out.csv", index=False, float_format="%.12g")
    loeo_episode.to_csv(outdir / "issue-136-long-history-leave-one-trigger-episode-out.csv", index=False, float_format="%.12g")
    long_trigger_descriptive(labels, analysis).to_csv(outdir / "issue-136-long-history-trigger-descriptive.csv", index=False, float_format="%.12g")

    return {
        "source": {
            "issue91_hmra_freeze_validated": bool(manifest["hmra_freeze_validated_before_asset_join"]),
            "causal_return_last_year": int(manifest["pairings"]["strict_causal_t_plus_2"]["last_return_year"]),
            "damodaran_sha256": manifest["sources"]["damodaran"]["raw_sha256"],
        },
        "sample": {
            "eligible_primary_rows": int(len(analysis)),
            "r7_episodes_in_primary": int(analysis["episode_id"].nunique()),
            "trigger_observations": int(len(sig_rows)),
            "trigger_state_years": [int(y) for y in sig_rows["state_year"]],
            "trigger_orders": sig_rows["turn_order"].value_counts().sort_index().to_dict(),
            "evaluable_eras": int(len(eval_eras)),
        },
        "signal": summary(sig_rows["spread"]),
        "control": summary(control_rows["spread"]),
        "primary_incremental": primary,
        "strongest_positive_era_share": concentration,
        "gates": gates,
        "verdict": verdict,
    }


def synthesis(modern: str, long: str) -> str:
    mp = modern == "async_turn_candidate"
    lp = long == "long_history_async_turn_candidate"
    mi = modern == "inconclusive_async_turn_sample"
    li = long == "inconclusive_long_history_async_turn_sample"
    if mp and lp:
        return "cross_history_async_turn_supported"
    if mp and not lp:
        return "modern_only_async_turn_support"
    if lp and not mp:
        return "long_history_only_async_turn_support"
    if mi or li:
        return "async_turn_evidence_inconclusive"
    return "async_turn_not_robust_across_history"


def run(issue133_root: Path, modern_root: Path, long_root: Path, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    modern = run_modern(issue133_root, modern_root, output_dir)
    long = run_long(long_root, output_dir)
    result = {
        "schema_version": 1,
        "issue": 136,
        "phase": "r7-asynchronous-turning-point",
        "modern_exact": modern,
        "long_history_hmra": long,
        "cross_history_synthesis": synthesis(modern["verdict"], long["verdict"]),
        "production_authorized": False,
    }
    (output_dir / "issue-136-result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    finding = [
        "# Issue #136 — R7 asynchronous turning-point finding",
        "",
        f"Modern exact verdict: **{modern['verdict']}**",
        f"Long-history HMRA verdict: **{long['verdict']}**",
        f"Cross-history synthesis: **{result['cross_history_synthesis']}**",
        "",
        f"Modern first-trigger episodes: {modern['sample']['trigger_episodes']}.",
        f"Long-history first-trigger observations: {long['sample']['trigger_observations']}.",
        "",
        "Issue #133 remains frozen and is not retuned by this study.",
        "HMRA remains a structural analogue, not exact V6.6.",
        "No production rule is authorized by this finding.",
    ]
    (output_dir / "issue-136-finding.md").write_text("\n".join(finding) + "\n", encoding="utf-8")
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--issue133-root", type=Path, required=True)
    ap.add_argument("--modern-root", type=Path, required=True)
    ap.add_argument("--long-root", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    result = run(args.issue133_root, args.modern_root, args.long_root, args.output_dir)
    print(json.dumps({
        "modern_verdict": result["modern_exact"]["verdict"],
        "modern_sample": result["modern_exact"]["sample"],
        "modern_primary": result["modern_exact"]["primary_incremental"],
        "long_verdict": result["long_history_hmra"]["verdict"],
        "long_sample": result["long_history_hmra"]["sample"],
        "long_primary": result["long_history_hmra"]["primary_incremental"],
        "synthesis": result["cross_history_synthesis"],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
