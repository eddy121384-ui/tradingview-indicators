#!/usr/bin/env python3
"""Issue #78 Second-Entry / Add-Risk Economic Policy Study.

Executes the preregistered complete-policy comparison after the
Breakout -> Acceptance -> Retest -> Resume evidence chain.

Candidate policies differ only in the timing of the extra 75 percentage
points of exposure after P1/P2 is known at t+3:

- R0: add immediately at t+3
- R5: add after frozen retest-segment favorable close break
- R1: add after frozen full favorable close extreme break
- R4: add after frozen +0.5 breakout-scale ATR progress

All policies use 25% Probe before add-risk. P0 adds at t+3 for every
candidate, P3 never adds, and episodes without a usable B3 breakout remain
at Probe. No deterioration overlay is used in this primary study.

Returns remain normalized underlying-move units, not executable instrument
PnL.
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

EXPECTED_EVENTS = 68118
EXPECTED_EPISODES = 1624
EXPECTED_B3_EVENTS = 997
EXPECTED_P12 = 236

PROBE = 0.25
FULL = 1.00
ADD_ON = FULL - PROBE

CANDIDATES = ("R0_Immediate", "R5_LocalClose", "R1_CloseExtreme", "R4_Progress05")
POLICIES = ("ProbeOnly", "FormalHold", *CANDIDATES)
ERAS = ("2010-2014", "2015-2019", "2020-2026")


def finite(values):
    return [
        float(value)
        for value in values
        if isinstance(value, (int, float, np.integer, np.floating))
        and math.isfinite(float(value))
    ]


def quantile(values, q):
    xs = sorted(finite(values))
    if not xs:
        return math.nan
    if len(xs) == 1:
        return xs[0]
    p = (len(xs) - 1) * q
    lo, hi = math.floor(p), math.ceil(p)
    if lo == hi:
        return xs[lo]
    w = p - lo
    return xs[lo] * (1.0 - w) + xs[hi] * w


def max_drawdown(returns):
    equity = peak = drawdown = 0.0
    for value in returns:
        equity += value
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
    return drawdown


def path_turnover(exposures):
    if not exposures:
        return 0.0
    return (
        abs(exposures[0])
        + sum(abs(exposures[i] - exposures[i - 1]) for i in range(1, len(exposures)))
        + abs(exposures[-1])
    )


def path_metrics(returns, exposures):
    if len(returns) < 2:
        raise ValueError("path too short")
    mean_daily = statistics.fmean(returns)
    daily_sd = statistics.stdev(returns)
    ann_return = mean_daily * 252.0
    ann_vol = daily_sd * math.sqrt(252.0)
    sharpe = mean_daily / daily_sd * math.sqrt(252.0) if daily_sd > 0 else math.nan

    downside_daily = math.sqrt(statistics.fmean(min(0.0, x) ** 2 for x in returns))
    ann_downside = downside_daily * math.sqrt(252.0)
    sortino = ann_return / ann_downside if ann_downside > 0 else math.nan

    worst_n = max(1, math.ceil(0.05 * len(returns)))
    es5 = statistics.fmean(sorted(returns)[:worst_n])
    turnover = path_turnover(exposures)
    years = len(returns) / 252.0

    return {
        "n_days": len(returns),
        "mean_daily": mean_daily,
        "ann_return": ann_return,
        "ann_vol": ann_vol,
        "sharpe": sharpe,
        "sortino": sortino,
        "cum_return": sum(returns),
        "max_drawdown": max_drawdown(returns),
        "es5": es5,
        "q1": quantile(returns, 0.01),
        "avg_exposure": statistics.fmean(exposures),
        "ann_turnover": turnover / years if years > 0 else math.nan,
    }


def episode_entry_scale(episode):
    row = episode[4][0]
    return retest.raw_scale(row)


def aligned_steps(episode):
    _, stage, _, _, rows = episode
    direction = 1.0 if stage == 2 else -1.0
    scale = episode_entry_scale(episode)
    if not (math.isfinite(scale) and scale > 0):
        raise ValueError("invalid episode entry scale")
    return [direction * float(row["move1"]) / scale for row in rows]


def episode_mfe(steps):
    cum = 0.0
    peak = 0.0
    for step in steps:
        cum += step
        peak = max(peak, cum)
    return peak


def build_state_map(paths):
    state_map = {}
    for _, row in paths.iterrows():
        key = (row["ticker"], int(row["episode_id"]))
        state_map[key] = row.to_dict()
    return state_map


def frame_time_index(frames):
    out = {}
    for ticker, frame in frames.items():
        out[ticker] = {
            int(event_time): int(i)
            for i, event_time in enumerate(frame["event_time"].tolist())
        }
    return out


def frozen_levels(episode, state, frames, time_index):
    ticker, stage, episode_id, start, rows = episode
    direction = 1 if stage == 2 else -1
    frame = frames[ticker]
    break_idx = time_index[ticker][int(state["break_time"])]
    t3_idx = break_idx + 3

    pre = frame.iloc[break_idx - retest.LOOKBACK:break_idx]
    box_high = float(pre["high_coord"].max())
    box_low = float(pre["low_coord"].min())
    t3_close = float(frame.iloc[t3_idx]["close_coord"])

    close_window = frame.iloc[break_idx:t3_idx + 1]
    if direction == 1:
        r1_anchor = float(close_window["close_coord"].max())
    else:
        r1_anchor = float(close_window["close_coord"].min())

    first_touch = state.get("first_touch_bar", math.nan)
    r5_anchor = math.nan
    if state["path"] in ("P1_WickHold", "P2_Reclaim"):
        if not math.isfinite(float(first_touch)):
            raise AssertionError("P1/P2 missing first touch")
        retest_start = break_idx + int(first_touch)
        retest_segment = frame.iloc[retest_start:t3_idx + 1]
        if direction == 1:
            r5_anchor = float(retest_segment["close_coord"].max())
        else:
            r5_anchor = float(retest_segment["close_coord"].min())

    # Preserve the already-frozen R4 definition from Resume Trigger Stage 1:
    # +0.5 ATR using the raw scale observed immediately before breakout.
    breakout_scale = retest.raw_scale(frame.iloc[break_idx - 1])
    r4_anchor = t3_close + direction * 0.5 * breakout_scale

    return {
        "break_idx": break_idx,
        "t3_idx": t3_idx,
        "t3_local": t3_idx - start,
        "box_high": box_high,
        "box_low": box_low,
        "r1_anchor": r1_anchor,
        "r5_anchor": r5_anchor,
        "r4_anchor": r4_anchor,
        "direction": direction,
    }


def first_trigger(policy, episode, state, levels, frames):
    ticker, stage, episode_id, start, rows = episode
    path = state["path"]
    t3_idx = int(levels["t3_idx"])
    episode_end = start + len(rows) - 1

    if path == "P0_NoTouch":
        return t3_idx
    if path == "P3_FailedAcceptance":
        return None
    if path not in ("P1_WickHold", "P2_Reclaim"):
        return None
    if policy == "R0_Immediate":
        return t3_idx

    frame = frames[ticker]
    direction = int(levels["direction"])
    for idx in range(t3_idx + 1, episode_end + 1):
        close = float(frame.iloc[idx]["close_coord"])
        if policy == "R5_LocalClose":
            hit = close > levels["r5_anchor"] if direction == 1 else close < levels["r5_anchor"]
        elif policy == "R1_CloseExtreme":
            hit = close > levels["r1_anchor"] if direction == 1 else close < levels["r1_anchor"]
        elif policy == "R4_Progress05":
            hit = close >= levels["r4_anchor"] if direction == 1 else close <= levels["r4_anchor"]
        else:
            raise ValueError(policy)
        if hit:
            return idx
    return None


def exposures_for_episode(policy, episode, state, levels, frames):
    _, _, _, start, rows = episode
    n = len(rows)
    if policy == "ProbeOnly":
        return [PROBE] * n, None
    if policy == "FormalHold":
        return [FULL] * n, start

    exposure = [PROBE] * n
    if state is None:
        return exposure, None

    trigger = first_trigger(policy, episode, state, levels, frames)
    if trigger is None:
        return exposure, None

    local = trigger - start
    if not (0 <= local < n):
        raise AssertionError((policy, start, trigger, n))
    for i in range(local, n):
        exposure[i] = FULL
    return exposure, trigger


def common_box_fail3(episode, state, levels, frames):
    if state is None or state["path"] not in ("P1_WickHold", "P2_Reclaim"):
        return math.nan

    ticker = episode[0]
    direction = int(levels["direction"])
    t3 = int(levels["t3_idx"])
    episode_end = episode[3] + len(episode[4]) - 1
    future = frames[ticker].iloc[t3 + 1:min(t3 + 4, episode_end + 1)]
    if len(future) == 0:
        return math.nan

    closes = future["close_coord"].to_numpy(float)
    if direction == 1:
        return int(np.any(closes <= float(levels["box_high"])))
    return int(np.any(closes >= float(levels["box_low"])))


def simulate_episode(policy, episode, state, levels, frames):
    steps = aligned_steps(episode)
    exposures, trigger = exposures_for_episode(policy, episode, state, levels, frames)
    returns = [e * step for e, step in zip(exposures, steps)]
    return steps, exposures, returns, trigger


def build_episode_economics(episodes, state_map, frames, time_index):
    rows = []

    for episode in episodes:
        ticker, stage, episode_id, start, records = episode
        state = state_map.get((ticker, episode_id))
        levels = frozen_levels(episode, state, frames, time_index) if state is not None else None
        steps = aligned_steps(episode)
        mfe = episode_mfe(steps)
        era = retest.era_name(int(records[0]["event_time"]))
        direction = "Markup" if stage == 2 else "Markdown"

        base = {
            "ticker": ticker,
            "episode_id": episode_id,
            "direction": direction,
            "era": era,
            "bars": len(records),
            "mfe": mfe,
            "path": state["path"] if state is not None else "NoUsableB3",
            "box_fail3_after_t3": (
                common_box_fail3(episode, state, levels, frames)
                if state is not None and levels is not None
                else math.nan
            ),
        }

        for policy in POLICIES:
            _, exposures, returns, trigger = simulate_episode(
                policy, episode, state, levels, frames
            )
            total_return = sum(returns)

            if state is not None and levels is not None:
                t3_local = int(levels["t3_local"])
                post_t3_return = sum(returns[t3_local:])
                add_on_return = sum(
                    (exposures[i] - PROBE) * steps[i]
                    for i in range(t3_local, len(steps))
                )
                post_t3_avg_exposure = statistics.fmean(exposures[t3_local:])
                full_bars = sum(e >= FULL - 1e-12 for e in exposures[t3_local:])
            else:
                post_t3_return = math.nan
                add_on_return = 0.0
                post_t3_avg_exposure = math.nan
                full_bars = 0

            rows.append({
                **base,
                "policy": policy,
                "triggered": int(trigger is not None) if policy in CANDIDATES else math.nan,
                "total_return": total_return,
                "post_t3_return": post_t3_return,
                "add_on_return": add_on_return,
                "add_on_win": int(add_on_return > 0) if policy in CANDIDATES else math.nan,
                "avg_exposure": statistics.fmean(exposures),
                "post_t3_avg_exposure": post_t3_avg_exposure,
                "turnover": path_turnover(exposures),
                "full_bars_after_t3": full_bars,
                "never_full_after_t3": (
                    int(full_bars == 0)
                    if policy in CANDIDATES and state is not None and state["path"] in ("P1_WickHold", "P2_Reclaim")
                    else math.nan
                ),
            })

    result = pd.DataFrame(rows)

    r0 = (
        result[
            (result["policy"] == "R0_Immediate")
            & (result["path"].isin(["P1_WickHold", "P2_Reclaim"]))
        ][["ticker", "episode_id", "add_on_return"]]
        .rename(columns={"add_on_return": "r0_add_on_return"})
    )
    result = result.merge(r0, on=["ticker", "episode_id"], how="left")
    result["foregone_add_return_vs_R0"] = (
        result["r0_add_on_return"] - result["add_on_return"]
    )
    return result


def market_timeline(events, episodes, episode_econ, state_map, frames, time_index):
    by_events = defaultdict(list)
    for row in events:
        by_events[row["ticker"]].append(row)
    for rows in by_events.values():
        rows.sort(key=lambda row: row["event_bar"])

    by_episodes = defaultdict(list)
    for episode in episodes:
        by_episodes[episode[0]].append(episode)

    output = []

    for ticker in sorted(by_events):
        ticker_episodes = by_episodes[ticker]
        cutoff = max(int(row["event_time"]) for ep in ticker_episodes for row in ep[4])
        timeline = [row for row in by_events[ticker] if int(row["event_time"]) <= cutoff]
        times = [int(row["event_time"]) for row in timeline]
        index = {event_time: i for i, event_time in enumerate(times)}

        for policy in POLICIES:
            returns = [0.0] * len(times)
            exposures = [0.0] * len(times)

            for episode in ticker_episodes:
                state = state_map.get((ticker, episode[2]))
                levels = (
                    frozen_levels(episode, state, frames, time_index)
                    if state is not None
                    else None
                )
                _, exp, ret, _ = simulate_episode(policy, episode, state, levels, frames)
                for row, e, value in zip(episode[4], exp, ret):
                    i = index[int(row["event_time"])]
                    returns[i] = value
                    exposures[i] = e

            output.append({
                "ticker": ticker,
                "scope": "all",
                "policy": policy,
                **path_metrics(returns, exposures),
            })

            for era in ERAS:
                ids = [i for i, event_time in enumerate(times) if retest.era_name(event_time) == era]
                if len(ids) < 20:
                    continue
                era_returns = [returns[i] for i in ids]
                era_exposures = [exposures[i] for i in ids]
                output.append({
                    "ticker": ticker,
                    "scope": era,
                    "policy": policy,
                    **path_metrics(era_returns, era_exposures),
                })

        for direction_code, direction_name in ((2, "Markup"), (5, "Markdown")):
            stage_eps = [ep for ep in ticker_episodes if ep[1] == direction_code]
            for policy in POLICIES:
                returns = [0.0] * len(times)
                exposures = [0.0] * len(times)
                for episode in stage_eps:
                    state = state_map.get((ticker, episode[2]))
                    levels = (
                        frozen_levels(episode, state, frames, time_index)
                        if state is not None
                        else None
                    )
                    _, exp, ret, _ = simulate_episode(policy, episode, state, levels, frames)
                    for row, e, value in zip(episode[4], exp, ret):
                        i = index[int(row["event_time"])]
                        returns[i] = value
                        exposures[i] = e

                output.append({
                    "ticker": ticker,
                    "scope": direction_name,
                    "policy": policy,
                    **path_metrics(returns, exposures),
                })

    return pd.DataFrame(output)


def add_equal_vol_fields(market):
    by_key = {
        (row.scope, row.ticker, row.policy): row
        for row in market.itertuples(index=False)
    }
    r0_scale = []
    r0_return = []
    formal_scale = []
    formal_return = []

    for row in market.itertuples(index=False):
        r0 = by_key[(row.scope, row.ticker, "R0_Immediate")]
        formal = by_key[(row.scope, row.ticker, "FormalHold")]

        if row.ann_vol > 0 and r0.ann_vol > 0:
            scale = r0.ann_vol / row.ann_vol
            r0_scale.append(scale)
            r0_return.append(row.ann_return * scale)
        else:
            r0_scale.append(math.nan)
            r0_return.append(math.nan)

        if row.ann_vol > 0 and formal.ann_vol > 0:
            scale = formal.ann_vol / row.ann_vol
            formal_scale.append(scale)
            formal_return.append(row.ann_return * scale)
        else:
            formal_scale.append(math.nan)
            formal_return.append(math.nan)

    market = market.copy()
    market["equal_vol_scale_vs_R0"] = r0_scale
    market["equal_vol_ann_return_vs_R0"] = r0_return
    market["equal_vol_scale_vs_FormalHold"] = formal_scale
    market["equal_vol_ann_return_vs_FormalHold"] = formal_return
    return market


def equal_market_whole(market):
    fields = (
        "ann_return", "ann_vol", "sharpe", "sortino", "max_drawdown",
        "es5", "q1", "avg_exposure", "ann_turnover",
        "equal_vol_ann_return_vs_R0", "equal_vol_ann_return_vs_FormalHold",
    )
    rows = []
    for (scope, policy), group in market.groupby(["scope", "policy"]):
        row = {
            "scope": scope,
            "policy": policy,
            "markets": group["ticker"].nunique(),
            "positive_return_markets": int((group["ann_return"] > 0).sum()),
        }
        for field in fields:
            vals = finite(group[field].tolist())
            row[field + "_eq_mean"] = statistics.fmean(vals) if vals else math.nan
            row[field + "_eq_median"] = statistics.median(vals) if vals else math.nan
        rows.append(row)
    return pd.DataFrame(rows)


def direct_whole_comparisons(market):
    pairs = (
        ("R5_LocalClose", "R0_Immediate"),
        ("R1_CloseExtreme", "R0_Immediate"),
        ("R4_Progress05", "R0_Immediate"),
        ("R5_LocalClose", "R1_CloseExtreme"),
    )
    metrics = (
        "ann_return", "sharpe", "max_drawdown", "es5",
        "equal_vol_ann_return_vs_R0", "avg_exposure", "ann_turnover",
    )
    rows = []

    for scope in ("all", *ERAS, "Markup", "Markdown"):
        sample = market[market["scope"] == scope]
        if sample.empty:
            continue
        keyed = {(r.ticker, r.policy): r for r in sample.itertuples(index=False)}
        tickers = sorted(sample["ticker"].unique())

        for a, b in pairs:
            deltas = defaultdict(list)
            used = []
            for ticker in tickers:
                if (ticker, a) not in keyed or (ticker, b) not in keyed:
                    continue
                ra, rb = keyed[(ticker, a)], keyed[(ticker, b)]
                used.append(ticker)
                for metric in metrics:
                    va, vb = getattr(ra, metric), getattr(rb, metric)
                    if math.isfinite(float(va)) and math.isfinite(float(vb)):
                        deltas[metric].append(float(va) - float(vb))

            row = {"scope": scope, "a": a, "b": b, "markets": len(used)}
            for metric in metrics:
                vals = deltas[metric]
                row[metric + "_delta_eq_mean"] = statistics.fmean(vals) if vals else math.nan
                row[metric + "_positive_markets"] = sum(x > 0 for x in vals)
            rows.append(row)

    return pd.DataFrame(rows)


def p12_only(econ):
    return econ[
        econ["path"].isin(["P1_WickHold", "P2_Reclaim"])
        & econ["policy"].isin(CANDIDATES)
    ].copy()


def p12_market_summary(econ, extra_cols=()):
    work = p12_only(econ)
    rows = []
    group_cols = [*extra_cols, "ticker", "policy"]

    for keys, group in work.groupby(group_cols):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(group_cols, keys))
        row["n"] = group["episode_id"].nunique()
        row["trigger_rate"] = group["triggered"].mean()
        row["no_trigger_rate"] = 1.0 - row["trigger_rate"]
        row["total_return_mean"] = group["total_return"].mean()
        row["total_return_median"] = group["total_return"].median()
        row["post_t3_return_mean"] = group["post_t3_return"].mean()
        row["add_on_return_mean"] = group["add_on_return"].mean()
        row["add_on_return_median"] = group["add_on_return"].median()
        row["add_on_win_rate"] = group["add_on_win"].mean()
        row["turnover_mean"] = group["turnover"].mean()
        row["avg_exposure_mean"] = group["avg_exposure"].mean()
        row["post_t3_avg_exposure_mean"] = group["post_t3_avg_exposure"].mean()
        row["full_bars_after_t3_mean"] = group["full_bars_after_t3"].mean()
        row["never_full_after_t3_rate"] = group["never_full_after_t3"].mean()
        row["foregone_add_return_vs_R0_mean"] = group["foregone_add_return_vs_R0"].mean()
        rows.append(row)

    return pd.DataFrame(rows)


def equal_market_from_p12(market, extra_cols=()):
    metrics = [
        c for c in market.columns
        if c not in {*extra_cols, "ticker", "policy", "n"}
    ]
    rows = []
    group_cols = [*extra_cols, "policy"]

    for keys, group in market.groupby(group_cols):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(group_cols, keys))
        row["markets"] = group["ticker"].nunique()
        row["pooled_n"] = int(group["n"].sum())
        for metric in metrics:
            row[metric + "_eq_market"] = group[metric].mean()
        rows.append(row)

    return pd.DataFrame(rows)


def p12_slices(econ):
    work = p12_only(econ).copy()
    labels = [
        ("all", np.ones(len(work), dtype=bool)),
        ("mfe_lt4", work["mfe"] < 4.0),
        ("mfe_ge8", work["mfe"] >= 8.0),
    ]
    outputs = []

    for label, mask in labels:
        sample = work[mask].copy()
        market = p12_market_summary(sample)
        universal = equal_market_from_p12(market)
        universal.insert(0, "slice", label)
        outputs.append(universal)

    return pd.concat(outputs, ignore_index=True)


def p12_box_fail(econ):
    work = p12_only(econ)
    work = work[work["box_fail3_after_t3"].notna()].copy()
    rows = []

    for (failed, policy, ticker), group in work.groupby(
        ["box_fail3_after_t3", "policy", "ticker"]
    ):
        rows.append({
            "box_fail3_after_t3": int(failed),
            "policy": policy,
            "ticker": ticker,
            "n": group["episode_id"].nunique(),
            "add_on_return_mean": group["add_on_return"].mean(),
            "total_return_mean": group["total_return"].mean(),
            "avg_exposure_mean": group["avg_exposure"].mean(),
        })

    market = pd.DataFrame(rows)
    universal = []
    for (failed, policy), group in market.groupby(["box_fail3_after_t3", "policy"]):
        universal.append({
            "box_fail3_after_t3": int(failed),
            "policy": policy,
            "markets": group["ticker"].nunique(),
            "pooled_n": int(group["n"].sum()),
            "add_on_return_mean_eq_market": group["add_on_return_mean"].mean(),
            "total_return_mean_eq_market": group["total_return_mean"].mean(),
            "avg_exposure_mean_eq_market": group["avg_exposure_mean"].mean(),
        })
    return market, pd.DataFrame(universal)


def positive_share(values):
    pos = sorted([x for x in finite(values) if x > 0], reverse=True)
    if not pos:
        return math.nan
    k = max(1, math.ceil(0.01 * len(pos)))
    return sum(pos[:k]) / sum(pos)


def p12_tail(econ):
    work = p12_only(econ)
    rows = []

    for (ticker, policy), group in work.groupby(["ticker", "policy"]):
        vals = finite(group["add_on_return"].tolist())
        winners = sorted([x for x in vals if x > 0], reverse=True)
        remove_best = vals.copy()
        if remove_best:
            remove_best.remove(max(remove_best))
        topk = max(1, math.ceil(0.01 * len(winners))) if winners else 0
        cutoff = set()
        # Remove values by sorted-index accounting rather than by value identity.
        ordered = sorted(enumerate(vals), key=lambda pair: pair[1], reverse=True)
        positive_ordered = [pair for pair in ordered if pair[1] > 0]
        remove_ids = {idx for idx, _ in positive_ordered[:topk]}
        remove_top = [v for i, v in enumerate(vals) if i not in remove_ids]

        rows.append({
            "ticker": ticker,
            "policy": policy,
            "n": len(vals),
            "top1pct_positive_share": positive_share(vals),
            "mean_add_on": statistics.fmean(vals),
            "mean_remove_best": statistics.fmean(remove_best) if remove_best else math.nan,
            "mean_remove_top1pct_winners": statistics.fmean(remove_top) if remove_top else math.nan,
        })

    market = pd.DataFrame(rows)
    universal = []
    for policy, group in market.groupby("policy"):
        universal.append({
            "policy": policy,
            "markets": group["ticker"].nunique(),
            "top1pct_positive_share_eq_market": group["top1pct_positive_share"].mean(),
            "mean_add_on_eq_market": group["mean_add_on"].mean(),
            "mean_remove_best_eq_market": group["mean_remove_best"].mean(),
            "mean_remove_top1pct_winners_eq_market": group["mean_remove_top1pct_winners"].mean(),
        })
    return market, pd.DataFrame(universal)


def write_csv(path, frame):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*")
    parser.add_argument("--out", default="/mnt/data/issue78-second-entry-economic")
    args = parser.parse_args()

    paths = args.paths or sorted(glob.glob("/mnt/data/pine-logs-#76 Forward Logger*.csv"))
    if not paths:
        raise SystemExit("no Issue #76 Forward Logger CSVs found")

    events = retest.read_events(paths)
    if len(events) != EXPECTED_EVENTS:
        raise AssertionError(f"event count drift: expected {EXPECTED_EVENTS}, got {len(events)}")

    frames, reconstruction_error = retest.reconstruct(events)
    episodes = retest.build_episodes(frames)
    if len(episodes) != EXPECTED_EPISODES:
        raise AssertionError(f"episode count drift: expected {EXPECTED_EPISODES}, got {len(episodes)}")

    paths_frame, path_stats = retest.build_paths(frames, episodes)
    if len(paths_frame) != EXPECTED_B3_EVENTS:
        raise AssertionError(
            f"B3 event count drift: expected {EXPECTED_B3_EVENTS}, got {len(paths_frame)}"
        )
    p12_n = int(paths_frame["path"].isin(["P1_WickHold", "P2_Reclaim"]).sum())
    if p12_n != EXPECTED_P12:
        raise AssertionError(f"P1/P2 count drift: expected {EXPECTED_P12}, got {p12_n}")

    state_map = build_state_map(paths_frame)
    time_index = frame_time_index(frames)

    episode_econ = build_episode_economics(
        episodes, state_map, frames, time_index
    )
    whole_market = market_timeline(
        events, episodes, episode_econ, state_map, frames, time_index
    )
    whole_market = add_equal_vol_fields(whole_market)

    whole_universal = equal_market_whole(whole_market)
    whole_comparisons = direct_whole_comparisons(whole_market)

    p12_market = p12_market_summary(episode_econ)
    p12_universal = equal_market_from_p12(p12_market)

    p12_temporal_market = p12_market_summary(episode_econ, ("era",))
    p12_temporal = equal_market_from_p12(p12_temporal_market, ("era",))

    p12_direction_market = p12_market_summary(episode_econ, ("direction",))
    p12_direction = equal_market_from_p12(p12_direction_market, ("direction",))

    p12_slice = p12_slices(episode_econ)
    box_market, box_universal = p12_box_fail(episode_econ)
    tail_market, tail_universal = p12_tail(episode_econ)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    write_csv(out / "issue78-second-entry-economic-episode-policy.csv", episode_econ)
    write_csv(out / "issue78-second-entry-economic-whole-per-market.csv", whole_market)
    write_csv(out / "issue78-second-entry-economic-whole-universal.csv", whole_universal)
    write_csv(out / "issue78-second-entry-economic-whole-comparisons.csv", whole_comparisons)
    write_csv(out / "issue78-second-entry-economic-p12-per-market.csv", p12_market)
    write_csv(out / "issue78-second-entry-economic-p12-universal.csv", p12_universal)
    write_csv(out / "issue78-second-entry-economic-p12-temporal.csv", p12_temporal)
    write_csv(out / "issue78-second-entry-economic-p12-direction.csv", p12_direction)
    write_csv(out / "issue78-second-entry-economic-p12-slices.csv", p12_slice)
    write_csv(out / "issue78-second-entry-economic-box-fail-per-market.csv", box_market)
    write_csv(out / "issue78-second-entry-economic-box-fail-universal.csv", box_universal)
    write_csv(out / "issue78-second-entry-economic-tail-per-market.csv", tail_market)
    write_csv(out / "issue78-second-entry-economic-tail-universal.csv", tail_universal)

    print("events", len(events))
    print("episodes", len(episodes))
    print("B3 events", len(paths_frame))
    print("P1/P2", p12_n)
    print("reconstruction_error", reconstruction_error)
    print("path_stats", path_stats)
    print("wrote", out)


if __name__ == "__main__":
    main()
