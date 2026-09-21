#!/usr/bin/env python3
"""Issue #78 Heterogeneous OOS Challenge 1 analyzer.

Runs the frozen R0 No-de-risk and R0 + Warning-First architectures on the
preregistered six-market daily OOS cohort. The old Issue #76 log schema is
reused only as a data contract; discovery-market counts are not reused.
"""
from __future__ import annotations

import argparse
import glob
import math
import statistics
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

import analyze_issue78_retest_path_stage1 as retest
import analyze_issue78_second_entry_economic_policy as second
import analyze_issue78_r0_warning_first_composition as comp

EXPECTED_MARKETS = (
    "TVC:SPX",
    "NASDAQ:NDX",
    "OANDA:XAUUSD",
    "OANDA:XAGUSD",
    "BITSTAMP:BTCUSD",
    "BITSTAMP:ETHUSD",
)
ASSET_CLASS = {
    "TVC:SPX": "EquityIndex",
    "NASDAQ:NDX": "EquityIndex",
    "OANDA:XAUUSD": "PreciousMetals",
    "OANDA:XAGUSD": "PreciousMetals",
    "BITSTAMP:BTCUSD": "Crypto",
    "BITSTAMP:ETHUSD": "Crypto",
}
CANDIDATES = ("R0_NoDerisk", "R0_WarningFirst")
ALL_POLICIES = ("ProbeOnly", "FormalHold", *CANDIDATES)
ERAS = ("2010-2014", "2015-2019", "2020-2026")
MS_YEAR = 365.2425 * 24 * 60 * 60 * 1000


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


def profit_factor(values):
    vals = finite(values)
    pos = sum(x for x in vals if x > 0)
    neg = -sum(x for x in vals if x < 0)
    if neg <= 0:
        return math.inf if pos > 0 else math.nan
    return pos / neg


def max_drawdown(values):
    equity = peak = dd = 0.0
    for value in values:
        equity += value
        peak = max(peak, equity)
        dd = max(dd, peak - equity)
    return dd


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
    return vals[lo] * (1 - w) + vals[hi] * w


def policy_episode(policy, episode, state, levels, frames):
    steps = second.aligned_steps(episode)
    if policy == "ProbeOnly":
        exp = [second.PROBE] * len(steps)
    elif policy == "FormalHold":
        exp = [1.0] * len(steps)
    elif policy == "R0_NoDerisk":
        _, exp, _, _, _ = comp.simulate_episode(
            episode, state, levels, frames, "none"
        )
    elif policy == "R0_WarningFirst":
        _, _, exp, _, _ = comp.simulate_episode(
            episode, state, levels, frames, "warning_first"
        )
    else:
        raise ValueError(policy)
    ret = [e * step for e, step in zip(exp, steps)]
    return steps, exp, ret


def build_episode_records(episodes, state_map, frames, time_index):
    rows = []
    for episode in episodes:
        ticker, stage, episode_id, start, records = episode
        state = state_map.get((ticker, episode_id))
        levels = (
            second.frozen_levels(episode, state, frames, time_index)
            if state is not None
            else None
        )
        steps = second.aligned_steps(episode)
        mfe = second.episode_mfe(steps)
        path = state["path"] if state is not None else "NoUsableB3"
        era = retest.era_name(int(records[0]["event_time"]))

        for policy in ALL_POLICIES:
            _, exp, ret = policy_episode(
                policy, episode, state, levels, frames
            )
            rows.append({
                "ticker": ticker,
                "asset_class": ASSET_CLASS[ticker],
                "episode_id": episode_id,
                "direction": "Markup" if stage == 2 else "Markdown",
                "era": era,
                "path": path,
                "bars": len(records),
                "mfe": mfe,
                "policy": policy,
                "harvest": sum(ret),
                "avg_exposure": mean(exp),
                "turnover": second.path_turnover(exp),
            })
    return pd.DataFrame(rows)


def elapsed_years(times):
    if len(times) < 2:
        return math.nan
    span = max(times) - min(times)
    return span / MS_YEAR if span > 0 else math.nan


def path_metrics(returns, exposures, times, episode_count):
    if len(returns) < 2:
        raise ValueError("path too short")
    sd = statistics.stdev(returns)
    ratio = statistics.fmean(returns) / sd if sd > 0 else math.nan
    worst_n = max(1, math.ceil(0.05 * len(returns)))
    years = elapsed_years(times)
    turnover = second.path_turnover(exposures)
    return {
        "n_bars": len(returns),
        "calendar_years": years,
        "cum_return": sum(returns),
        "mean_bar_return": statistics.fmean(returns),
        "bar_vol": sd,
        "return_vol_ratio": ratio,
        "max_drawdown": max_drawdown(returns),
        "es5": statistics.fmean(sorted(returns)[:worst_n]),
        "q1": quantile(returns, 0.01),
        "avg_exposure": statistics.fmean(exposures),
        "calendarized_return": sum(returns) / years if years and years > 0 else math.nan,
        "turnover_per_calendar_year": turnover / years if years and years > 0 else math.nan,
        "turnover_per_episode": turnover / episode_count if episode_count > 0 else math.nan,
    }


def build_whole_market(events, episodes, state_map, frames, time_index):
    by_events = defaultdict(list)
    for row in events:
        by_events[row["ticker"]].append(row)
    for group in by_events.values():
        group.sort(key=lambda x: x["event_bar"])

    by_episodes = defaultdict(list)
    for ep in episodes:
        by_episodes[ep[0]].append(ep)

    out = []
    for ticker in EXPECTED_MARKETS:
        ticker_eps = by_episodes[ticker]
        cutoff = max(int(r["event_time"]) for ep in ticker_eps for r in ep[4])
        timeline = [r for r in by_events[ticker] if int(r["event_time"]) <= cutoff]
        times = [int(r["event_time"]) for r in timeline]
        index = {t: i for i, t in enumerate(times)}

        def emit(scope, scoped_eps, ids):
            for policy in ALL_POLICIES:
                returns = [0.0] * len(times)
                exposures = [0.0] * len(times)
                for ep in scoped_eps:
                    state = state_map.get((ticker, ep[2]))
                    levels = (
                        second.frozen_levels(ep, state, frames, time_index)
                        if state is not None else None
                    )
                    _, exp, ret = policy_episode(
                        policy, ep, state, levels, frames
                    )
                    for row, e, value in zip(ep[4], exp, ret):
                        i = index[int(row["event_time"])]
                        returns[i] = value
                        exposures[i] = e
                rr = [returns[i] for i in ids]
                ee = [exposures[i] for i in ids]
                tt = [times[i] for i in ids]
                out.append({
                    "ticker": ticker,
                    "asset_class": ASSET_CLASS[ticker],
                    "scope": scope,
                    "policy": policy,
                    **path_metrics(rr, ee, tt, len(scoped_eps)),
                })

        emit("all", ticker_eps, list(range(len(times))))

        for era in ERAS:
            ids = [i for i, t in enumerate(times) if retest.era_name(t) == era]
            eps_era = [ep for ep in ticker_eps if retest.era_name(int(ep[4][0]["event_time"])) == era]
            if len(ids) >= 20 and eps_era:
                emit(era, eps_era, ids)

        for code, name in ((2, "Markup"), (5, "Markdown")):
            eps_dir = [ep for ep in ticker_eps if ep[1] == code]
            if eps_dir:
                emit(name, eps_dir, list(range(len(times))))

    return pd.DataFrame(out)


def aggregate_table(market, group_key):
    metric_cols = [
        "cum_return", "mean_bar_return", "bar_vol", "return_vol_ratio",
        "max_drawdown", "es5", "q1", "avg_exposure",
        "calendarized_return", "turnover_per_calendar_year",
        "turnover_per_episode",
    ]
    rows = []
    groups = ["scope", "policy"]
    for keys, group in market.groupby(groups):
        scope, policy = keys
        row = {"scope": scope, "policy": policy}
        if group_key == "market":
            units = group
            row["units"] = group["ticker"].nunique()
            for metric in metric_cols:
                row[metric + "_eq_market"] = group[metric].mean()
                row[metric + "_median_market"] = group[metric].median()
            row["positive_calendarized_units"] = int((group["calendarized_return"] > 0).sum())
        elif group_key == "class":
            class_rows = (
                group.groupby("asset_class")[metric_cols]
                .mean()
                .reset_index()
            )
            row["units"] = class_rows["asset_class"].nunique()
            for metric in metric_cols:
                row[metric + "_eq_class"] = class_rows[metric].mean()
                row[metric + "_median_class"] = class_rows[metric].median()
            row["positive_calendarized_units"] = int((class_rows["calendarized_return"] > 0).sum())
        else:
            raise ValueError(group_key)
        rows.append(row)
    return pd.DataFrame(rows)


def episode_market_summary(records, extra=()):
    rows = []
    cols = [*extra, "ticker", "asset_class", "policy"]
    for keys, group in records.groupby(cols):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(cols, keys))
        vals = group["harvest"].tolist()
        row.update({
            "n": group["episode_id"].nunique(),
            "mean_episode_return": group["harvest"].mean(),
            "median_episode_return": group["harvest"].median(),
            "win_rate": float((group["harvest"] > 0).mean()),
            "profit_factor": profit_factor(vals),
            "avg_exposure": group["avg_exposure"].mean(),
            "turnover_per_episode": group["turnover"].mean(),
            "mfe_mean": group["mfe"].mean(),
        })
        rows.append(row)
    return pd.DataFrame(rows)


def aggregate_episode(market, by, extra=()):
    metrics = [
        "mean_episode_return", "median_episode_return", "win_rate",
        "profit_factor", "avg_exposure", "turnover_per_episode", "mfe_mean",
    ]
    rows = []
    group_cols = [*extra, "policy"]
    for keys, group in market.groupby(group_cols):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(group_cols, keys))
        if by == "market":
            units = group
            row["units"] = group["ticker"].nunique()
        elif by == "class":
            units = (
                group.groupby("asset_class")[metrics]
                .mean()
                .reset_index()
            )
            row["units"] = units["asset_class"].nunique()
        else:
            raise ValueError(by)
        row["pooled_n"] = int(group["n"].sum())
        for metric in metrics:
            row[metric + f"_eq_{by}"] = units[metric].mean()
        row["positive_mean_units"] = int((units["mean_episode_return"] > 0).sum())
        rows.append(row)
    return pd.DataFrame(rows)


def path_prevalence(paths):
    rows = []
    for (ticker, path), group in paths.groupby(["ticker", "path"]):
        rows.append({
            "ticker": ticker,
            "asset_class": ASSET_CLASS[ticker],
            "path": path,
            "n": len(group),
        })
    market = pd.DataFrame(rows)
    totals = market.groupby("ticker")["n"].sum().rename("total")
    market = market.join(totals, on="ticker")
    market["rate"] = market["n"] / market["total"]

    all_paths = ("P0_NoTouch", "P1_WickHold", "P2_Reclaim", "P3_FailedAcceptance")
    completed = []
    for ticker in EXPECTED_MARKETS:
        sub = market[market["ticker"] == ticker].set_index("path")
        for path in all_paths:
            n = int(sub.loc[path, "n"]) if path in sub.index else 0
            total = int(sub["total"].iloc[0]) if len(sub) else 0
            completed.append({
                "ticker": ticker,
                "asset_class": ASSET_CLASS[ticker],
                "path": path,
                "n": n,
                "total": total,
                "rate": n / total if total else math.nan,
            })
    market = pd.DataFrame(completed)

    eq_market = (
        market.groupby("path")
        .agg(rate_eq_market=("rate", "mean"), pooled_n=("n", "sum"))
        .reset_index()
    )
    class_rows = (
        market.groupby(["asset_class", "path"])["rate"]
        .mean().reset_index()
    )
    eq_class = (
        class_rows.groupby("path")["rate"]
        .mean().rename("rate_eq_class").reset_index()
    )
    return market, eq_market.merge(eq_class, on="path")


def slices(records):
    work = records.copy()
    work["mfe_slice"] = np.where(
        work["mfe"] < 4.0, "mfe_lt4",
        np.where(work["mfe"] >= 8.0, "mfe_ge8", "mfe_4_8")
    )
    market = episode_market_summary(work, ("mfe_slice",))
    return (
        aggregate_episode(market, "market", ("mfe_slice",)),
        aggregate_episode(market, "class", ("mfe_slice",)),
    )


def positive_share(values):
    pos = sorted([x for x in finite(values) if x > 0], reverse=True)
    if not pos:
        return math.nan
    k = max(1, math.ceil(0.01 * len(pos)))
    return sum(pos[:k]) / sum(pos)


def tail(records):
    rows = []
    for (ticker, policy), group in records.groupby(["ticker", "policy"]):
        vals = finite(group["harvest"].tolist())
        best_removed = vals.copy()
        if best_removed:
            best_removed.remove(max(best_removed))
        ordered = sorted(enumerate(vals), key=lambda x: x[1], reverse=True)
        winners = [x for x in ordered if x[1] > 0]
        k = max(1, math.ceil(0.01 * len(winners))) if winners else 0
        remove_ids = {i for i, _ in winners[:k]}
        top_removed = [v for i, v in enumerate(vals) if i not in remove_ids]
        rows.append({
            "ticker": ticker,
            "asset_class": ASSET_CLASS[ticker],
            "policy": policy,
            "n": len(vals),
            "top1pct_positive_share": positive_share(vals),
            "mean_return": mean(vals),
            "mean_remove_best": mean(best_removed),
            "mean_remove_top1pct_winners": mean(top_removed),
        })
    market = pd.DataFrame(rows)
    metrics = [
        "top1pct_positive_share", "mean_return",
        "mean_remove_best", "mean_remove_top1pct_winners",
    ]
    out = []
    for policy, group in market.groupby("policy"):
        classes = group.groupby("asset_class")[metrics].mean()
        row = {"policy": policy, "markets": group["ticker"].nunique(), "classes": classes.shape[0]}
        for metric in metrics:
            row[metric + "_eq_market"] = group[metric].mean()
            row[metric + "_eq_class"] = classes[metric].mean()
        out.append(row)
    return market, pd.DataFrame(out)


def write(path, frame):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--out", default="/mnt/data/issue78-heterogeneous-oos1")
    args = ap.parse_args()
    paths = args.paths or sorted(glob.glob("/mnt/data/pine-logs-#78 HET OOS1*.csv"))
    if not paths:
        raise SystemExit("no heterogeneous OOS1 logger CSVs found")

    events = retest.read_events(paths)
    tickers = tuple(sorted({r["ticker"] for r in events}))
    expected = tuple(sorted(EXPECTED_MARKETS))
    if tickers != expected:
        raise AssertionError(f"OOS ticker set mismatch: expected {expected}, got {tickers}")

    repr_by = defaultdict(set)
    for row in events:
        repr_by[row["ticker"]].add(row["repr"])
    bad_repr = {
        ticker: values for ticker, values in repr_by.items()
        if values != {"PRICE_LOG"}
    }
    if bad_repr:
        raise AssertionError(f"unexpected OOS representation: {bad_repr}")

    frames, reconstruction_error = retest.reconstruct(events)
    episodes = retest.build_episodes(frames)
    if not episodes:
        raise AssertionError("no completed OOS trend episodes")

    paths_frame, path_stats = retest.build_paths(frames, episodes)
    state_map = second.build_state_map(paths_frame)
    time_index = second.frame_time_index(frames)

    episode_records = build_episode_records(
        episodes, state_map, frames, time_index
    )
    whole_market = build_whole_market(
        events, episodes, state_map, frames, time_index
    )
    whole_eq_market = aggregate_table(whole_market, "market")
    whole_eq_class = aggregate_table(whole_market, "class")

    episode_market = episode_market_summary(episode_records)
    episode_eq_market = aggregate_episode(episode_market, "market")
    episode_eq_class = aggregate_episode(episode_market, "class")

    temporal_market = episode_market_summary(episode_records, ("era",))
    temporal_eq_market = aggregate_episode(temporal_market, "market", ("era",))
    temporal_eq_class = aggregate_episode(temporal_market, "class", ("era",))

    direction_market = episode_market_summary(episode_records, ("direction",))
    direction_eq_market = aggregate_episode(direction_market, "market", ("direction",))
    direction_eq_class = aggregate_episode(direction_market, "class", ("direction",))

    slice_market, slice_class = slices(episode_records)
    prevalence_market, prevalence = path_prevalence(paths_frame)
    tail_market, tail_summary = tail(episode_records)

    integrity = pd.DataFrame([{
        "events": len(events),
        "completed_episodes": len(episodes),
        "b3_events": len(paths_frame),
        "p12_events": int(paths_frame["path"].isin(["P1_WickHold", "P2_Reclaim"]).sum()),
        "markets": len(EXPECTED_MARKETS),
        "reconstruction_error": reconstruction_error,
        "path_stats": str(path_stats),
    }])

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    write(out / "issue78-heterogeneous-oos1-integrity.csv", integrity)
    write(out / "issue78-heterogeneous-oos1-episode-policy.csv", episode_records)
    write(out / "issue78-heterogeneous-oos1-whole-per-market.csv", whole_market)
    write(out / "issue78-heterogeneous-oos1-whole-eq-market.csv", whole_eq_market)
    write(out / "issue78-heterogeneous-oos1-whole-eq-class.csv", whole_eq_class)
    write(out / "issue78-heterogeneous-oos1-episode-eq-market.csv", episode_eq_market)
    write(out / "issue78-heterogeneous-oos1-episode-eq-class.csv", episode_eq_class)
    write(out / "issue78-heterogeneous-oos1-temporal-eq-market.csv", temporal_eq_market)
    write(out / "issue78-heterogeneous-oos1-temporal-eq-class.csv", temporal_eq_class)
    write(out / "issue78-heterogeneous-oos1-direction-eq-market.csv", direction_eq_market)
    write(out / "issue78-heterogeneous-oos1-direction-eq-class.csv", direction_eq_class)
    write(out / "issue78-heterogeneous-oos1-slices-eq-market.csv", slice_market)
    write(out / "issue78-heterogeneous-oos1-slices-eq-class.csv", slice_class)
    write(out / "issue78-heterogeneous-oos1-path-prevalence-per-market.csv", prevalence_market)
    write(out / "issue78-heterogeneous-oos1-path-prevalence.csv", prevalence)
    write(out / "issue78-heterogeneous-oos1-tail-per-market.csv", tail_market)
    write(out / "issue78-heterogeneous-oos1-tail-summary.csv", tail_summary)

    print("events", len(events))
    print("episodes", len(episodes))
    print("B3 events", len(paths_frame))
    print("P1/P2", int(paths_frame["path"].isin(["P1_WickHold", "P2_Reclaim"]).sum()))
    print("reconstruction_error", reconstruction_error)
    print("path_stats", path_stats)
    print("wrote", out)


if __name__ == "__main__":
    main()
