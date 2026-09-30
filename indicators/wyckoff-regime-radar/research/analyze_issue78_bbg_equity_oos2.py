#!/usr/bin/env python3
"""Issue #78 Bloomberg 300-stock survivorship-limited OOS2 diagnostic.

This is the first economic run permitted after Issue #119 closed.
The analyzer is intentionally frozen before results are inspected.

Primary cross-sectional unit: one stock, one vote.
Policies: frozen R0 NoDerisk and R0 WarningFirst only.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

import analyze_issue78_retest_path_stage1 as retest
import analyze_issue78_second_entry_economic_policy as second
import analyze_issue78_r0_warning_first_composition as comp
from audit_issue119_bbg_oos2_snapshot import audit_snapshot
from smoke_issue119_frozen_classifier import (
    FROZEN_CLASSIFIER_BLOB,
    load_classifier,
)

EVENT_START = pd.Timestamp("2000-01-03")
EVENT_END = pd.Timestamp("2026-08-31")
MIN_PRIOR_VALID = 252
LIQUIDITY_WINDOW = 60
MIN_PRICE = 5.0
MIN_MEDIAN_DOLLAR_VOLUME = 5_000_000.0
MIN_PRIMARY_EPISODES = 5
MIN_TEMPORAL_STOCKS = 20
MIN_SECTOR_STOCKS = 5

POLICIES = ("R0_NoDerisk", "R0_WarningFirst")
MANAGEMENT = {
    "R0_NoDerisk": "none",
    "R0_WarningFirst": "warning_first",
}
BLOCKS = (
    ("2000-2004", 2000, 2004),
    ("2005-2009", 2005, 2009),
    ("2010-2014", 2010, 2014),
    ("2015-2019", 2015, 2019),
    ("2020-2026", 2020, 2026),
)


def finite(values):
    return [
        float(v)
        for v in values
        if isinstance(v, (int, float, np.integer, np.floating))
        and math.isfinite(float(v))
    ]


def mean(values):
    vals = finite(values)
    return statistics.fmean(vals) if vals else math.nan


def median(values):
    vals = finite(values)
    return statistics.median(vals) if vals else math.nan


def quantile(values, q):
    vals = sorted(finite(values))
    if not vals:
        return math.nan
    if len(vals) == 1:
        return vals[0]
    p = (len(vals) - 1) * q
    lo = math.floor(p)
    hi = math.ceil(p)
    if lo == hi:
        return vals[lo]
    w = p - lo
    return vals[lo] * (1.0 - w) + vals[hi] * w


def profit_factor(values):
    vals = finite(values)
    pos = sum(v for v in vals if v > 0)
    neg = -sum(v for v in vals if v < 0)
    if neg <= 0:
        return math.inf if pos > 0 else math.nan
    return pos / neg


def block_name(ts: pd.Timestamp) -> str:
    year = int(ts.year)
    for name, lo, hi in BLOCKS:
        if lo <= year <= hi:
            return name
    return "outside"


def max_drawdown(values):
    equity = peak = drawdown = 0.0
    for value in finite(values):
        equity += value
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
    return drawdown


def es5(values):
    vals = finite(values)
    if not vals:
        return math.nan
    n = max(1, math.ceil(0.05 * len(vals)))
    return statistics.fmean(sorted(vals)[:n])


def timeline_metrics(returns, exposures):
    rr = finite(returns)
    ee = finite(exposures)
    if len(rr) < 2 or len(ee) != len(rr):
        return {
            "bars": len(rr),
            "bar_vol": math.nan,
            "max_drawdown": math.nan,
            "es5": math.nan,
            "turnover": math.nan,
            "avg_exposure": math.nan,
        }
    return {
        "bars": len(rr),
        "bar_vol": statistics.stdev(rr),
        "max_drawdown": max_drawdown(rr),
        "es5": es5(rr),
        "turnover": second.path_turnover(ee),
        "avg_exposure": statistics.fmean(ee),
    }


def prepare_frame(raw: pd.DataFrame, classifier_module, unit_id: str) -> pd.DataFrame:
    frame = raw.copy()
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    if frame["date"].isna().any():
        raise ValueError(f"{unit_id}: invalid date")
    if frame["date"].duplicated().any():
        raise ValueError(f"{unit_id}: duplicate dates")
    frame = frame.sort_values("date").reset_index(drop=True)

    classified = classifier_module.compute_price_only(frame)
    if len(classified) != len(frame):
        raise AssertionError(f"{unit_id}: classifier row drift")

    ohlc = frame[["open", "high", "low", "close"]].apply(
        pd.to_numeric, errors="coerce"
    )
    valid_ohlc = (
        np.isfinite(ohlc.to_numpy()).all(axis=1)
        & (ohlc.to_numpy() > 0).all(axis=1)
    )

    sym_atr = pd.to_numeric(
        classified["sym_atr"], errors="coerce"
    ).to_numpy(float)
    formal = pd.to_numeric(
        classified["formal_id"], errors="coerce"
    ).fillna(0).astype(int).to_numpy()
    effective = np.where(
        valid_ohlc & np.isfinite(sym_atr) & (sym_atr > 0),
        formal,
        0,
    ).astype(int)

    fresh = np.zeros(len(frame), dtype=int)
    if len(frame):
        prior = np.roll(effective, 1)
        prior[0] = 0
        fresh = (
            np.isin(effective, [2, 5])
            & (effective != prior)
        ).astype(int)

    close = pd.to_numeric(frame["close"], errors="coerce").to_numpy(float)
    high = pd.to_numeric(frame["high"], errors="coerce").to_numpy(float)
    low = pd.to_numeric(frame["low"], errors="coerce").to_numpy(float)
    volume = pd.to_numeric(frame["volume"], errors="coerce").to_numpy(float)

    close_coord = np.where(valid_ohlc, np.log(close), np.nan)
    high_coord = np.where(valid_ohlc, np.log(high), np.nan)
    low_coord = np.where(valid_ohlc, np.log(low), np.nan)

    move1 = np.full(len(frame), np.nan)
    mfe1 = np.full(len(frame), np.nan)
    mae1 = np.full(len(frame), np.nan)
    if len(frame) > 1:
        pair = valid_ohlc[:-1] & valid_ohlc[1:]
        move1[:-1] = np.where(
            pair,
            close_coord[1:] - close_coord[:-1],
            np.nan,
        )
        mfe1[:-1] = np.where(
            pair,
            high_coord[1:] - close_coord[:-1],
            np.nan,
        )
        mae1[:-1] = np.where(
            pair,
            low_coord[1:] - close_coord[:-1],
            np.nan,
        )

    event_time = (
        frame["date"].astype("int64") // 1_000_000
    ).astype(np.int64)

    out = pd.DataFrame(
        {
            "ticker": unit_id,
            "repr": "PRICE_LOG",
            "event_time": event_time,
            "event_bar": np.arange(len(frame), dtype=int),
            "stage": effective,
            "fresh": fresh,
            "scale": sym_atr,
            "move1": move1,
            "mfe1": mfe1,
            "mae1": mae1,
            "close_coord": close_coord,
            "high_coord": high_coord,
            "low_coord": low_coord,
            "raw_close": close,
            "raw_volume": volume,
            "valid_ohlc": valid_ohlc,
            "date": frame["date"],
        }
    )

    valid_count_before = np.concatenate(
        [[0], np.cumsum(valid_ohlc.astype(int))[:-1]]
    )
    dollar_volume = close * volume
    finite_dv = np.isfinite(dollar_volume) & (dollar_volume >= 0)
    dv_series = pd.Series(
        np.where(finite_dv, dollar_volume, np.nan),
        dtype=float,
    )
    out["prior_valid_bars"] = valid_count_before
    out["liq60_count"] = (
        dv_series.rolling(
            LIQUIDITY_WINDOW,
            min_periods=LIQUIDITY_WINDOW,
        ).count().to_numpy()
    )
    out["liq60_median"] = (
        dv_series.rolling(
            LIQUIDITY_WINDOW,
            min_periods=LIQUIDITY_WINDOW,
        ).median().to_numpy()
    )
    return out


def entry_eligibility(frame: pd.DataFrame, start: int) -> tuple[bool, str]:
    row = frame.iloc[start]
    date = pd.Timestamp(row["date"])
    if date < EVENT_START or date > EVENT_END:
        return False, "outside_event_window"
    if not bool(row["valid_ohlc"]):
        return False, "invalid_entry_ohlc"
    if int(row["prior_valid_bars"]) < MIN_PRIOR_VALID:
        return False, "prior_valid_lt252"
    if not (math.isfinite(float(row["raw_close"])) and float(row["raw_close"]) >= MIN_PRICE):
        return False, "close_lt5"
    if int(row["liq60_count"]) < LIQUIDITY_WINDOW:
        return False, "liquidity_window_incomplete"
    med = float(row["liq60_median"])
    if not (math.isfinite(med) and med >= MIN_MEDIAN_DOLLAR_VOLUME):
        return False, "median_dollar_volume_lt5m"
    return True, "eligible"


def completed_episode_is_usable(episode) -> bool:
    rows = episode[4]
    if not rows:
        return False
    for row in rows:
        if not all(
            math.isfinite(float(row[name]))
            for name in ("move1", "mfe1", "mae1")
        ):
            return False
    return True


def build_research_set(
    universe: pd.DataFrame,
    raw_dir: Path,
    classifier_module,
):
    frames = {}
    episodes = []
    coverage_rows = []
    metadata = {}

    for idx, meta in enumerate(universe.itertuples(index=False), start=1):
        unit_id = str(meta.figi)
        metadata[unit_id] = {
            "figi": unit_id,
            "ticker": str(meta.ticker),
            "sector": str(meta.sector),
            "sleeve": str(meta.sleeve),
            "security": str(meta.security),
        }
        raw_path = raw_dir / f"{unit_id}.csv.gz"
        if not raw_path.exists():
            raise FileNotFoundError(raw_path)

        raw = pd.read_csv(raw_path)
        frame = prepare_frame(raw, classifier_module, unit_id)
        frames[unit_id] = frame

        all_eps = retest.build_episodes({unit_id: frame})
        fresh_mask = (
            frame["fresh"].eq(1)
            & frame["stage"].isin([2, 5])
            & frame["date"].between(EVENT_START, EVENT_END)
        )
        fresh_starts = set(frame.index[fresh_mask].astype(int))
        eligible_starts = set()
        reasons = defaultdict(int)
        for start in sorted(fresh_starts):
            ok, reason = entry_eligibility(frame, start)
            reasons[reason] += 1
            if ok:
                eligible_starts.add(start)

        usable = []
        unusable_completed = 0
        for ep in all_eps:
            start = int(ep[3])
            if start not in eligible_starts:
                continue
            if completed_episode_is_usable(ep):
                usable.append(ep)
            else:
                unusable_completed += 1

        episodes.extend(usable)
        completed_starts = {int(ep[3]) for ep in usable}
        censored = len(eligible_starts - completed_starts)

        structural_ready = (
            frame["stage"].isin([1, 2, 3, 4, 5, 6])
            & np.isfinite(frame["scale"].to_numpy(float))
            & (frame["scale"].to_numpy(float) > 0)
        )

        coverage_rows.append(
            {
                **metadata[unit_id],
                "raw_rows": len(frame),
                "valid_ohlc_rows": int(frame["valid_ohlc"].sum()),
                "structurally_active_rows": int(structural_ready.sum()),
                "fresh_trend_entries": len(fresh_starts),
                "eligible_fresh_entries": len(eligible_starts),
                "completed_eligible_episodes": len(usable),
                "censored_eligible_entries": censored,
                "completed_but_unusable": unusable_completed,
                **{f"elig_{k}": int(v) for k, v in reasons.items()},
            }
        )
        print(
            f"[oos2] {idx}/{len(universe)} {meta.ticker} "
            f"fresh={len(fresh_starts)} eligible={len(eligible_starts)} "
            f"completed={len(usable)} censored={censored}",
            flush=True,
        )

    return frames, episodes, pd.DataFrame(coverage_rows), metadata


def episode_records(episodes, state_map, frames, time_index, metadata):
    rows = []
    for episode in episodes:
        unit_id, stage, episode_id, start, records = episode
        meta = metadata[unit_id]
        state = state_map.get((unit_id, episode_id))
        levels = (
            second.frozen_levels(
                episode, state, frames, time_index
            )
            if state is not None
            else None
        )
        steps = second.aligned_steps(episode)
        mfe = second.episode_mfe(steps)
        entry_date = pd.to_datetime(records[0]["date"])
        direction = "Markup" if stage == 2 else "Markdown"
        path = state["path"] if state is not None else "NoUsableB3"

        for policy in POLICIES:
            management = MANAGEMENT[policy]
            _, earned, actual, returns, managed = comp.simulate_episode(
                episode, state, levels, frames, management
            )
            rows.append(
                {
                    **meta,
                    "episode_id": int(episode_id),
                    "entry_date": str(entry_date.date()),
                    "block": block_name(entry_date),
                    "direction": direction,
                    "path": path,
                    "bars": len(records),
                    "mfe": mfe,
                    "policy": policy,
                    "harvest": sum(returns),
                    "avg_exposure": mean(actual),
                    "turnover": second.path_turnover(actual),
                    "de_risk_count": int(managed["de_risk_count"]),
                    "re_risk_count": int(managed["re_risk_count"]),
                }
            )
    return pd.DataFrame(rows)


def build_timelines(episodes, records, frames, state_map, time_index, metadata):
    by_eps = defaultdict(list)
    for ep in episodes:
        by_eps[ep[0]].append(ep)

    rows = []
    for unit_id, frame in frames.items():
        valid = (
            frame["valid_ohlc"]
            & frame["date"].between(EVENT_START, EVENT_END)
        )
        timeline = frame.loc[valid, ["event_time"]].copy()
        if len(timeline) < 2:
            continue
        times = timeline["event_time"].astype(np.int64).tolist()
        index = {int(t): i for i, t in enumerate(times)}

        for policy in POLICIES:
            rr = [0.0] * len(times)
            ee = [0.0] * len(times)
            for ep in by_eps.get(unit_id, []):
                state = state_map.get((unit_id, ep[2]))
                levels = (
                    second.frozen_levels(
                        ep, state, frames, time_index
                    )
                    if state is not None
                    else None
                )
                _, _, actual, returns, _ = comp.simulate_episode(
                    ep,
                    state,
                    levels,
                    frames,
                    MANAGEMENT[policy],
                )
                for row, exposure, value in zip(
                    ep[4], actual, returns
                ):
                    t = int(row["event_time"])
                    if t not in index:
                        raise AssertionError(
                            f"{unit_id}: episode time absent from valid timeline"
                        )
                    i = index[t]
                    rr[i] = float(value)
                    ee[i] = float(exposure)

            rows.append(
                {
                    **metadata[unit_id],
                    "policy": policy,
                    **timeline_metrics(rr, ee),
                }
            )
    return pd.DataFrame(rows)


def stock_summary(records: pd.DataFrame) -> pd.DataFrame:
    rows = []
    keys = ["figi", "ticker", "sector", "sleeve", "policy"]
    for values, group in records.groupby(keys):
        base = dict(zip(keys, values))
        vals = finite(group["harvest"].tolist())
        winners = [v for v in vals if v > 0]
        losers = [v for v in vals if v < 0]
        avg_winner = mean(winners)
        avg_loser = mean(losers)
        payoff = (
            avg_winner / abs(avg_loser)
            if math.isfinite(avg_winner)
            and math.isfinite(avg_loser)
            and avg_loser < 0
            else math.nan
        )
        rows.append(
            {
                **base,
                "episodes": int(group["episode_id"].nunique()),
                "mean_expectancy": mean(vals),
                "median_episode": median(vals),
                "win_rate": mean([int(v > 0) for v in vals]),
                "avg_winner": avg_winner,
                "avg_loser": avg_loser,
                "payoff_ratio": payoff,
                "profit_factor": profit_factor(vals),
                "avg_exposure": mean(group["avg_exposure"].tolist()),
                "turnover_per_episode": mean(group["turnover"].tolist()),
            }
        )
    return pd.DataFrame(rows)


def aggregate_primary(primary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for policy, group in primary.groupby("policy"):
        exp = finite(group["mean_expectancy"].tolist())
        rows.append(
            {
                "policy": policy,
                "stocks": int(group["figi"].nunique()),
                "episodes": int(group["episodes"].sum()),
                "equal_stock_mean_expectancy": mean(exp),
                "median_stock_expectancy": median(exp),
                "positive_stock_fraction": mean(
                    [int(v > 0) for v in exp]
                ),
                "p25_stock_expectancy": quantile(exp, 0.25),
                "p75_stock_expectancy": quantile(exp, 0.75),
                "equal_stock_win_rate": mean(group["win_rate"].tolist()),
                "equal_stock_avg_winner": mean(group["avg_winner"].tolist()),
                "equal_stock_avg_loser": mean(group["avg_loser"].tolist()),
                "equal_stock_payoff_ratio": mean(
                    group["payoff_ratio"].tolist()
                ),
                "equal_stock_profit_factor": mean(
                    group["profit_factor"].replace(
                        [np.inf, -np.inf], np.nan
                    ).tolist()
                ),
                "equal_stock_avg_exposure": mean(
                    group["avg_exposure"].tolist()
                ),
                "equal_stock_turnover_per_episode": mean(
                    group["turnover_per_episode"].tolist()
                ),
            }
        )
    return pd.DataFrame(rows)


def concentration(primary: pd.DataFrame) -> dict:
    r0 = primary[
        primary["policy"] == "R0_NoDerisk"
    ].copy()
    positive = r0[r0["mean_expectancy"] > 0].sort_values(
        "mean_expectancy", ascending=False
    )
    denom = positive["mean_expectancy"].sum()

    def share(frac):
        if len(positive) == 0 or denom <= 0:
            return math.nan, 0
        k = max(1, math.ceil(frac * len(positive)))
        return (
            float(positive.head(k)["mean_expectancy"].sum() / denom),
            k,
        )

    top1, k1 = share(0.01)
    top5, k5 = share(0.05)
    best = (
        float(positive.iloc[0]["mean_expectancy"] / denom)
        if len(positive) and denom > 0
        else math.nan
    )
    remove_figi = set(positive.head(k1)["figi"])
    remaining = r0[~r0["figi"].isin(remove_figi)]
    return {
        "positive_stocks": int(len(positive)),
        "top1pct_positive_stock_count": int(k1),
        "top1pct_positive_contribution_share": top1,
        "top5pct_positive_stock_count": int(k5),
        "top5pct_positive_contribution_share": top5,
        "best_single_positive_contribution_share": best,
        "equal_stock_mean_after_removing_top1pct_positive": mean(
            remaining["mean_expectancy"].tolist()
        ),
    }


def episode_slice_table(records, primary_ids):
    work = records[records["figi"].isin(primary_ids)].copy()
    work["mfe_slice"] = np.where(
        work["mfe"] < 4.0,
        "mfe_lt4",
        np.where(work["mfe"] >= 8.0, "mfe_ge8", "mfe_4_8"),
    )
    stock = (
        work.groupby(["figi", "policy", "mfe_slice"])["harvest"]
        .mean()
        .rename("mean_harvest")
        .reset_index()
    )
    out = (
        stock.groupby(["policy", "mfe_slice"])
        .agg(
            stocks=("figi", "nunique"),
            equal_stock_mean_harvest=("mean_harvest", "mean"),
        )
        .reset_index()
    )
    return stock, out


def temporal_table(records, primary_ids):
    work = records[records["figi"].isin(primary_ids)].copy()
    stock = (
        work.groupby(["block", "figi", "policy"])["harvest"]
        .mean()
        .rename("mean_expectancy")
        .reset_index()
    )
    rows = []
    for (block, policy), group in stock.groupby(["block", "policy"]):
        values = group["mean_expectancy"].tolist()
        rows.append(
            {
                "block": block,
                "policy": policy,
                "stocks": int(group["figi"].nunique()),
                "equal_stock_mean_expectancy": mean(values),
                "median_stock_expectancy": median(values),
                "positive_stock_fraction": mean(
                    [int(v > 0) for v in finite(values)]
                ),
                "adequate": int(
                    group["figi"].nunique() >= MIN_TEMPORAL_STOCKS
                ),
            }
        )
    return stock, pd.DataFrame(rows)


def direction_table(records, primary_ids):
    work = records[records["figi"].isin(primary_ids)].copy()
    stock = (
        work.groupby(["direction", "figi", "policy"])["harvest"]
        .mean()
        .rename("mean_expectancy")
        .reset_index()
    )
    out = (
        stock.groupby(["direction", "policy"])
        .agg(
            stocks=("figi", "nunique"),
            equal_stock_mean_expectancy=("mean_expectancy", "mean"),
        )
        .reset_index()
    )
    return stock, out


def sector_table(primary):
    rows = []
    for (sector, policy), group in primary.groupby(["sector", "policy"]):
        vals = group["mean_expectancy"].tolist()
        rows.append(
            {
                "sector": sector,
                "policy": policy,
                "stocks": int(group["figi"].nunique()),
                "equal_stock_mean_expectancy": mean(vals),
                "median_stock_expectancy": median(vals),
                "positive_stock_fraction": mean(
                    [int(v > 0) for v in finite(vals)]
                ),
                "adequate": int(
                    group["figi"].nunique() >= MIN_SECTOR_STOCKS
                ),
            }
        )

    r0 = primary[primary["policy"] == "R0_NoDerisk"]
    loo = []
    for sector in sorted(r0["sector"].unique()):
        remaining = r0[r0["sector"] != sector]
        loo.append(
            {
                "removed_sector": sector,
                "remaining_stocks": int(remaining["figi"].nunique()),
                "equal_stock_mean_expectancy": mean(
                    remaining["mean_expectancy"].tolist()
                ),
            }
        )
    return pd.DataFrame(rows), pd.DataFrame(loo)


def sleeve_table(primary):
    rows = []
    for (sleeve, policy), group in primary.groupby(["sleeve", "policy"]):
        vals = group["mean_expectancy"].tolist()
        rows.append(
            {
                "sleeve": sleeve,
                "policy": policy,
                "stocks": int(group["figi"].nunique()),
                "equal_stock_mean_expectancy": mean(vals),
                "median_stock_expectancy": median(vals),
                "positive_stock_fraction": mean(
                    [int(v > 0) for v in finite(vals)]
                ),
            }
        )
    return pd.DataFrame(rows)


def warning_first_table(
    primary,
    timelines,
    slice_stock,
    slice_summary,
):
    ids = set(
        primary[primary["policy"] == "R0_NoDerisk"]["figi"]
    )
    risk = timelines[timelines["figi"].isin(ids)].copy()
    r0 = risk[risk["policy"] == "R0_NoDerisk"].set_index("figi")
    wf = risk[risk["policy"] == "R0_WarningFirst"].set_index("figi")
    common = sorted(set(r0.index) & set(wf.index))

    rows = []
    for figi in common:
        a = r0.loc[figi]
        b = wf.loc[figi]
        rows.append(
            {
                "figi": figi,
                "bar_vol_improved": int(b.bar_vol < a.bar_vol),
                "max_drawdown_improved": int(
                    b.max_drawdown < a.max_drawdown
                ),
                "es5_improved": int(b.es5 > a.es5),
                "bar_vol_delta": b.bar_vol - a.bar_vol,
                "max_drawdown_delta": b.max_drawdown - a.max_drawdown,
                "es5_delta": b.es5 - a.es5,
                "turnover_delta": b.turnover - a.turnover,
            }
        )
    defense = pd.DataFrame(rows)

    lt4 = slice_stock[slice_stock["mfe_slice"] == "mfe_lt4"]
    r0_lt = lt4[lt4["policy"] == "R0_NoDerisk"].set_index("figi")
    wf_lt = lt4[lt4["policy"] == "R0_WarningFirst"].set_index("figi")
    common_lt = sorted(set(r0_lt.index) & set(wf_lt.index))
    mfe_lt4_improved = [
        int(wf_lt.loc[x, "mean_harvest"] > r0_lt.loc[x, "mean_harvest"])
        for x in common_lt
    ]

    def slice_value(policy, label):
        rows = slice_summary[
            (slice_summary["policy"] == policy)
            & (slice_summary["mfe_slice"] == label)
        ]
        return (
            float(rows.iloc[0]["equal_stock_mean_harvest"])
            if len(rows)
            else math.nan
        )

    r0_ge8 = slice_value("R0_NoDerisk", "mfe_ge8")
    wf_ge8 = slice_value("R0_WarningFirst", "mfe_ge8")
    retention = (
        wf_ge8 / r0_ge8
        if math.isfinite(r0_ge8)
        and math.isfinite(wf_ge8)
        and r0_ge8 > 0
        else math.nan
    )

    raw = primary.pivot(
        index="figi", columns="policy", values="mean_expectancy"
    ).dropna()
    raw_delta = (
        raw["R0_WarningFirst"] - raw["R0_NoDerisk"]
        if len(raw)
        else pd.Series(dtype=float)
    )

    summary = {
        "stocks_risk_metrics": int(len(defense)),
        "bar_vol_improved_fraction": mean(
            defense["bar_vol_improved"].tolist()
        ) if len(defense) else math.nan,
        "max_drawdown_improved_fraction": mean(
            defense["max_drawdown_improved"].tolist()
        ) if len(defense) else math.nan,
        "es5_improved_fraction": mean(
            defense["es5_improved"].tolist()
        ) if len(defense) else math.nan,
        "mfe_lt4_stocks": int(len(common_lt)),
        "mfe_lt4_harvest_improved_fraction": mean(mfe_lt4_improved),
        "mfe_ge8_r0_equal_stock_mean": r0_ge8,
        "mfe_ge8_wf_equal_stock_mean": wf_ge8,
        "mfe_ge8_retention": retention,
        "equal_stock_raw_expectancy_delta": mean(raw_delta.tolist()),
        "equal_stock_turnover_delta": mean(
            defense["turnover_delta"].tolist()
        ) if len(defense) else math.nan,
    }
    summary["strong_defensive_gate"] = bool(
        all(
            math.isfinite(summary[k]) and summary[k] >= 0.60
            for k in (
                "bar_vol_improved_fraction",
                "max_drawdown_improved_fraction",
                "es5_improved_fraction",
                "mfe_lt4_harvest_improved_fraction",
            )
        )
        and math.isfinite(retention)
        and retention >= 0.70
    )
    return defense, pd.DataFrame([summary])


def classify_r0(primary_summary, concentration_result, temporal, sector, loo):
    row = primary_summary[
        primary_summary["policy"] == "R0_NoDerisk"
    ].iloc[0]
    adequate_temporal = temporal[
        (temporal["policy"] == "R0_NoDerisk")
        & (temporal["adequate"] == 1)
    ]
    adequate_sector = sector[
        (sector["policy"] == "R0_NoDerisk")
        & (sector["adequate"] == 1)
    ]

    gates = {
        "mean_gt0": bool(row.equal_stock_mean_expectancy > 0),
        "median_gt0": bool(row.median_stock_expectancy > 0),
        "positive_stock_fraction_ge55pct": bool(
            row.positive_stock_fraction >= 0.55
        ),
        "top1pct_positive_share_lt25pct": bool(
            math.isfinite(
                concentration_result[
                    "top1pct_positive_contribution_share"
                ]
            )
            and concentration_result[
                "top1pct_positive_contribution_share"
            ] < 0.25
        ),
        "mean_after_top1pct_removal_gt0": bool(
            concentration_result[
                "equal_stock_mean_after_removing_top1pct_positive"
            ] > 0
        ),
        "temporal_positive_at_least_4_of_5": bool(
            len(adequate_temporal) == 5
            and int(
                (
                    adequate_temporal[
                        "equal_stock_mean_expectancy"
                    ] > 0
                ).sum()
            ) >= 4
        ),
        "sector_positive_at_least_8": bool(
            int(
                (
                    adequate_sector[
                        "equal_stock_mean_expectancy"
                    ] > 0
                ).sum()
            ) >= 8
        ),
        "no_single_sector_required": bool(
            len(loo) > 0
            and (
                loo["equal_stock_mean_expectancy"] > 0
            ).all()
        ),
    }

    if all(gates.values()):
        label = "Diagnostic Strong"
    elif (
        row.equal_stock_mean_expectancy <= 0
        and row.median_stock_expectancy <= 0
    ) or row.positive_stock_fraction < 0.45:
        label = "Diagnostic Weak / Failed"
    elif row.equal_stock_mean_expectancy > 0:
        label = "Diagnostic Mixed"
    else:
        label = "Diagnostic Ambiguous"

    return {
        "label": label,
        "gates": gates,
        "adequate_temporal_blocks": int(len(adequate_temporal)),
        "positive_adequate_temporal_blocks": int(
            (
                adequate_temporal["equal_stock_mean_expectancy"] > 0
            ).sum()
        ),
        "adequate_sectors": int(len(adequate_sector)),
        "positive_adequate_sectors": int(
            (
                adequate_sector["equal_stock_mean_expectancy"] > 0
            ).sum()
        ),
    }


def write_csv(path: Path, frame: pd.DataFrame):
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--raw-dir", type=Path, required=True)
    ap.add_argument(
        "--classifier",
        type=Path,
        default=Path("generated/wyckoff-issue78-rc-python.py"),
    )
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    audit = audit_snapshot(
        args.universe,
        args.manifest,
        args.raw_dir,
    )
    if not audit["pass"]:
        raise SystemExit("Issue #119 snapshot audit failed")

    classifier, blob = load_classifier(args.classifier)
    if blob != FROZEN_CLASSIFIER_BLOB:
        raise AssertionError("frozen classifier blob drift")

    universe = pd.read_csv(args.universe)
    if len(universe) != 300:
        raise AssertionError(f"universe rows drift: {len(universe)}")

    frames, episodes, coverage, metadata = build_research_set(
        universe,
        args.raw_dir,
        classifier,
    )
    if not episodes:
        raise AssertionError("no eligible completed episodes")

    paths_frame, path_stats = retest.build_paths(frames, episodes)
    state_map = second.build_state_map(paths_frame)
    time_index = second.frame_time_index(frames)

    records = episode_records(
        episodes,
        state_map,
        frames,
        time_index,
        metadata,
    )
    timelines = build_timelines(
        episodes,
        records,
        frames,
        state_map,
        time_index,
        metadata,
    )

    stocks = stock_summary(records)
    primary = stocks[
        stocks["episodes"] >= MIN_PRIMARY_EPISODES
    ].copy()
    primary_ids = set(
        primary[primary["policy"] == "R0_NoDerisk"]["figi"]
    )
    if not primary_ids:
        raise AssertionError("no stocks meet 5-episode primary rule")

    primary_summary = aggregate_primary(primary)
    concentration_result = concentration(primary)
    slice_stock, slice_summary = episode_slice_table(
        records, primary_ids
    )
    temporal_stock, temporal_summary = temporal_table(
        records, primary_ids
    )
    direction_stock, direction_summary = direction_table(
        records, primary_ids
    )
    sector_summary, sector_loo = sector_table(primary)
    sleeve_summary = sleeve_table(primary)
    wf_stock, wf_summary = warning_first_table(
        primary,
        timelines,
        slice_stock,
        slice_summary,
    )
    classification = classify_r0(
        primary_summary,
        concentration_result,
        temporal_summary,
        sector_summary,
        sector_loo,
    )

    path_prevalence = (
        paths_frame.groupby("path")
        .size()
        .rename("episodes")
        .reset_index()
    )
    if len(path_prevalence):
        path_prevalence["fraction"] = (
            path_prevalence["episodes"]
            / path_prevalence["episodes"].sum()
        )

    integrity = {
        "issue": 78,
        "study": "Bloomberg 300-stock survivorship-limited OOS2 diagnostic",
        "classifier_blob": blob,
        "universe_sha256": audit["universe_sha256_actual"],
        "raw_files": audit["completed"],
        "raw_failures": audit["failures"],
        "stocks_in_universe": int(len(universe)),
        "completed_eligible_episodes": int(len(episodes)),
        "b3_events": int(len(paths_frame)),
        "p1_p2_events": int(
            paths_frame["path"].isin(
                ["P1_WickHold", "P2_Reclaim"]
            ).sum()
        ) if len(paths_frame) else 0,
        "primary_stocks": int(len(primary_ids)),
        "path_stats": path_stats,
        "policy_economics_computed": True,
        "survivorship_limited": True,
    }

    summary = {
        "integrity": integrity,
        "primary": primary_summary.to_dict("records"),
        "r0_concentration": concentration_result,
        "r0_classification": classification,
        "warning_first": (
            wf_summary.iloc[0].to_dict()
            if len(wf_summary)
            else {}
        ),
        "notes": [
            "This is a survivorship-limited diagnostic cohort, not the formal point-in-time/delisted-security OOS2.",
            "One stock receives one vote in the primary table.",
            "Primary stocks require at least 5 completed eligible episodes.",
            "No policy or classifier threshold may be changed after this output is inspected.",
        ],
    }

    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out / "coverage.csv", coverage)
    write_csv(args.out / "episode_policy.csv", records)
    write_csv(args.out / "stock_policy.csv", stocks)
    write_csv(args.out / "primary_stock_policy.csv", primary)
    write_csv(args.out / "primary_summary.csv", primary_summary)
    write_csv(args.out / "timeline_policy.csv", timelines)
    write_csv(args.out / "mfe_slice_per_stock.csv", slice_stock)
    write_csv(args.out / "mfe_slice_summary.csv", slice_summary)
    write_csv(args.out / "temporal_per_stock.csv", temporal_stock)
    write_csv(args.out / "temporal_summary.csv", temporal_summary)
    write_csv(args.out / "direction_per_stock.csv", direction_stock)
    write_csv(args.out / "direction_summary.csv", direction_summary)
    write_csv(args.out / "sector_summary.csv", sector_summary)
    write_csv(args.out / "sector_leave_one_out.csv", sector_loo)
    write_csv(args.out / "sleeve_summary.csv", sleeve_summary)
    write_csv(args.out / "warning_first_per_stock.csv", wf_stock)
    write_csv(args.out / "warning_first_summary.csv", wf_summary)
    write_csv(args.out / "path_prevalence.csv", path_prevalence)
    (args.out / "summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
