#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import glob
import math
import statistics
from collections import defaultdict
from pathlib import Path

import analyze_issue78_warning_first_damage_latch as base

EXPECTED_EVENTS=68118
EXPECTED_EPISODES=1624

POLICIES = (
    "formal_hold",
    "simple_none",
    "simple_warning",
    "simple_gentle",
    "simple_balanced",
    "progressive_none",
    "progressive_warning",
    "progressive_gentle",
    "progressive_balanced",
)

ERAS = ("2010-2014", "2015-2019", "2020-2026")


def policy_spec(policy):
    if policy == "formal_hold":
        return "full", "none"
    add = "simple_1atr" if policy.startswith("simple_") else "progressive"
    suffix = policy.split("_", 1)[1]
    management = {
        "none": "none",
        "warning": "warning_first",
        "gentle": "gentle_latch",
        "balanced": "balanced_latch",
    }[suffix]
    return add, management


def earned_cap(add_policy, peak):
    if add_policy == "full":
        return 1.0
    return base.earned_cap(add_policy, peak)


def simulate_path(ep, policy):
    ticker, stage, episode_id, rows = ep
    steps = base.aligned_steps(ep)
    add_policy, management = policy_spec(policy)

    cum = 0.0
    peak = 0.0
    damage_cap = 1.0
    reduction_steps = 0
    previous_exposure = 0.0
    turnover = 0.0
    path = []

    for row, step in zip(rows, steps):
        ecap = earned_cap(add_policy, peak)
        giveback = max(0.0, peak - cum)

        if management == "none":
            actual = ecap
        elif management in ("gentle_latch", "balanced_latch"):
            target = (
                base.gentle_target(giveback)
                if management == "gentle_latch"
                else base.balanced_target(giveback)
            )
            if target < damage_cap:
                damage_cap = target
            actual = min(ecap, damage_cap)
        elif management == "warning_first":
            target_steps = 2 if giveback >= 4.0 else (1 if giveback >= 2.0 else 0)
            reduction_steps = max(reduction_steps, target_steps)
            actual = max(0.25, ecap - 0.25 * reduction_steps)
        else:
            raise ValueError(management)

        turnover += abs(actual - previous_exposure)
        previous_exposure = actual
        path.append((row["event_time"], actual * step, actual))

        new_cum = cum + step
        if new_cum > peak + 1e-12:
            peak = new_cum
            if management in ("gentle_latch", "balanced_latch"):
                damage_cap = 1.0
            elif management == "warning_first":
                reduction_steps = 0
        cum = new_cum

    turnover += abs(previous_exposure)
    return path, turnover


def quantile(values, q):
    xs = sorted(values)
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


def metrics(returns, exposures, turnover):
    n = len(returns)
    mean_daily = statistics.fmean(returns)
    daily_sd = statistics.stdev(returns)
    ann_return = mean_daily * 252.0
    ann_vol = daily_sd * math.sqrt(252.0)
    sharpe = mean_daily / daily_sd * math.sqrt(252.0) if daily_sd > 0 else math.nan

    downside_daily = math.sqrt(
        statistics.fmean(min(0.0, value) ** 2 for value in returns)
    )
    ann_downside = downside_daily * math.sqrt(252.0)
    sortino = ann_return / ann_downside if ann_downside > 0 else math.nan

    drawdown = max_drawdown(returns)
    calmar = ann_return / drawdown if drawdown > 0 else math.nan

    worst_n = max(1, math.ceil(0.05 * n))
    expected_shortfall_5 = statistics.fmean(sorted(returns)[:worst_n])

    years = n / 252.0
    return {
        "n_days": n,
        "mean_daily": mean_daily,
        "ann_return": ann_return,
        "ann_vol": ann_vol,
        "sharpe": sharpe,
        "ann_downside": ann_downside,
        "sortino": sortino,
        "cum_return": sum(returns),
        "max_drawdown": drawdown,
        "calmar": calmar,
        "es5": expected_shortfall_5,
        "q1": quantile(returns, 0.01),
        "avg_exposure": statistics.fmean(exposures),
        "ann_turnover": turnover / years,
    }


def era_name(ms):
    return base.era_name(ms)


def build_market_rows(events, episodes):
    by_events = defaultdict(list)
    for row in events:
        by_events[row["ticker"]].append(row)
    for rows in by_events.values():
        rows.sort(key=lambda row: row["event_bar"])

    by_episodes = defaultdict(list)
    for ep in episodes:
        by_episodes[ep[0]].append(ep)

    output = []
    for ticker in sorted(by_events):
        ticker_episodes = by_episodes[ticker]
        cutoff = max(row["event_time"] for ep in ticker_episodes for row in ep[3])
        timeline = [row for row in by_events[ticker] if row["event_time"] <= cutoff]
        times = [row["event_time"] for row in timeline]
        index = {value: i for i, value in enumerate(times)}

        for policy in POLICIES:
            returns = [0.0] * len(times)
            exposures = [0.0] * len(times)
            turnover = 0.0

            for ep in ticker_episodes:
                path, episode_turnover = simulate_path(ep, policy)
                turnover += episode_turnover
                for event_time, value, exposure in path:
                    i = index[event_time]
                    returns[i] = value
                    exposures[i] = exposure

            output.append(
                {
                    "ticker": ticker,
                    "policy": policy,
                    "scope": "all",
                    **metrics(returns, exposures, turnover),
                }
            )

            for era in ERAS:
                ids = [i for i, event_time in enumerate(times) if era_name(event_time) == era]
                if len(ids) < 20:
                    continue
                era_returns = [returns[i] for i in ids]
                era_exposures = [exposures[i] for i in ids]
                era_turnover = (
                    abs(era_exposures[0])
                    + sum(
                        abs(era_exposures[i] - era_exposures[i - 1])
                        for i in range(1, len(era_exposures))
                    )
                    + abs(era_exposures[-1])
                )
                output.append(
                    {
                        "ticker": ticker,
                        "policy": policy,
                        "scope": era,
                        **metrics(era_returns, era_exposures, era_turnover),
                    }
                )
    return output


def add_equal_vol_fields(rows):
    by_key = {
        (row["scope"], row["ticker"], row["policy"]): row
        for row in rows
    }
    for row in rows:
        formal = by_key[(row["scope"], row["ticker"], "formal_hold")]
        if row["ann_vol"] > 0 and formal["ann_vol"] > 0:
            row["equal_vol_scale_vs_formal"] = formal["ann_vol"] / row["ann_vol"]
            row["equal_vol_ann_return_vs_formal"] = (
                row["ann_return"] * row["equal_vol_scale_vs_formal"]
            )
        else:
            row["equal_vol_scale_vs_formal"] = math.nan
            row["equal_vol_ann_return_vs_formal"] = math.nan
        row["formal_ann_return"] = formal["ann_return"]
        row["formal_ann_vol"] = formal["ann_vol"]


def finite(values):
    return [
        value
        for value in values
        if isinstance(value, (int, float)) and math.isfinite(value)
    ]


def summarize(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["scope"], row["policy"])].append(row)

    output = []
    fields = (
        "ann_return",
        "ann_vol",
        "sharpe",
        "sortino",
        "max_drawdown",
        "calmar",
        "es5",
        "q1",
        "avg_exposure",
        "ann_turnover",
        "equal_vol_ann_return_vs_formal",
    )

    for (scope, policy), group in sorted(grouped.items()):
        row = {"scope": scope, "policy": policy, "markets": len(group)}
        for field in fields:
            values = finite([item[field] for item in group])
            row[f"{field}_eq_mean"] = statistics.fmean(values)
            row[f"{field}_eq_median"] = statistics.median(values)
        row["positive_return_markets"] = sum(item["ann_return"] > 0 for item in group)
        output.append(row)
    return output


def comparison_rows(rows):
    comparisons = (
        ("simple_warning", "simple_none"),
        ("simple_gentle", "simple_none"),
        ("simple_balanced", "simple_none"),
        ("progressive_warning", "progressive_none"),
        ("progressive_gentle", "progressive_none"),
        ("progressive_balanced", "progressive_none"),
        ("simple_none", "formal_hold"),
        ("progressive_none", "formal_hold"),
    )

    by_key = {
        (row["scope"], row["ticker"], row["policy"]): row
        for row in rows
    }

    output = []
    for scope in ("all",) + ERAS:
        tickers = sorted(
            {row["ticker"] for row in rows if row["scope"] == scope}
        )
        for policy, benchmark in comparisons:
            pairs = [
                (
                    by_key[(scope, ticker, policy)],
                    by_key[(scope, ticker, benchmark)],
                )
                for ticker in tickers
            ]

            equal_vol_diffs = [
                policy_row["ann_return"]
                * (benchmark_row["ann_vol"] / policy_row["ann_vol"])
                - benchmark_row["ann_return"]
                for policy_row, benchmark_row in pairs
            ]

            output.append(
                {
                    "scope": scope,
                    "policy": policy,
                    "benchmark": benchmark,
                    "markets": len(pairs),
                    "eq_mean_ann_return_diff": statistics.fmean(
                        p["ann_return"] - b["ann_return"] for p, b in pairs
                    ),
                    "eq_mean_ann_vol_diff": statistics.fmean(
                        p["ann_vol"] - b["ann_vol"] for p, b in pairs
                    ),
                    "eq_mean_sharpe_diff": statistics.fmean(
                        p["sharpe"] - b["sharpe"] for p, b in pairs
                    ),
                    "eq_mean_sortino_diff": statistics.fmean(
                        p["sortino"] - b["sortino"] for p, b in pairs
                    ),
                    "eq_mean_maxdd_diff": statistics.fmean(
                        p["max_drawdown"] - b["max_drawdown"] for p, b in pairs
                    ),
                    "eq_mean_es5_diff": statistics.fmean(
                        p["es5"] - b["es5"] for p, b in pairs
                    ),
                    "eq_mean_turnover_diff": statistics.fmean(
                        p["ann_turnover"] - b["ann_turnover"] for p, b in pairs
                    ),
                    "sharpe_improve_markets": sum(
                        p["sharpe"] > b["sharpe"] for p, b in pairs
                    ),
                    "sortino_improve_markets": sum(
                        p["sortino"] > b["sortino"] for p, b in pairs
                    ),
                    "maxdd_improve_markets": sum(
                        p["max_drawdown"] < b["max_drawdown"] for p, b in pairs
                    ),
                    "es5_improve_markets": sum(
                        p["es5"] > b["es5"] for p, b in pairs
                    ),
                    "equal_vol_return_diff_eq_mean": statistics.fmean(equal_vol_diffs),
                    "equal_vol_return_improve_markets": sum(value > 0 for value in equal_vol_diffs),
                }
            )
    return output


def direction_rows(events, episodes):
    by_events = defaultdict(list)
    for row in events:
        by_events[row["ticker"]].append(row)
    for rows in by_events.values():
        rows.sort(key=lambda row: row["event_bar"])

    by_episodes = defaultdict(list)
    for ep in episodes:
        by_episodes[ep[0]].append(ep)

    market_rows = []
    for ticker in sorted(by_events):
        ticker_episodes = by_episodes[ticker]
        cutoff = max(row["event_time"] for ep in ticker_episodes for row in ep[3])
        timeline = [row for row in by_events[ticker] if row["event_time"] <= cutoff]
        times = [row["event_time"] for row in timeline]
        index = {value: i for i, value in enumerate(times)}

        for stage_code, direction in ((2, "Markup"), (5, "Markdown")):
            stage_episodes = [ep for ep in ticker_episodes if ep[1] == stage_code]
            for policy in POLICIES:
                returns = [0.0] * len(times)
                exposures = [0.0] * len(times)
                turnover = 0.0
                for ep in stage_episodes:
                    path, episode_turnover = simulate_path(ep, policy)
                    turnover += episode_turnover
                    for event_time, value, exposure in path:
                        i = index[event_time]
                        returns[i] = value
                        exposures[i] = exposure

                market_rows.append(
                    {
                        "ticker": ticker,
                        "direction": direction,
                        "policy": policy,
                        **metrics(returns, exposures, turnover),
                    }
                )

    grouped = defaultdict(list)
    for row in market_rows:
        grouped[(row["direction"], row["policy"])].append(row)

    output = []
    fields = (
        "ann_return",
        "ann_vol",
        "sharpe",
        "sortino",
        "max_drawdown",
        "es5",
        "ann_turnover",
    )
    for (direction, policy), group in sorted(grouped.items()):
        row = {"direction": direction, "policy": policy, "markets": len(group)}
        for field in fields:
            row[f"{field}_eq_mean"] = statistics.fmean(item[field] for item in group)
        output.append(row)
    return output


def write_csv(path, rows):
    with Path(path).open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*")
    parser.add_argument("--out", default="/mnt/data/issue78-risk-adjusted-edge")
    args = parser.parse_args()

    paths = args.paths or sorted(
        glob.glob("/mnt/data/pine-logs-#76 Forward Logger*.csv")
    )
    if not paths:
        raise SystemExit("no Issue #76 Forward Logger CSVs found")

    events = base.read_events(paths)
    episodes = base.episodes(events)

    if len(events) != EXPECTED_EVENTS:
        raise AssertionError(
            f"event count drift: expected {EXPECTED_EVENTS}, got {len(events)}"
        )
    if len(episodes) != EXPECTED_EPISODES:
        raise AssertionError(
            f"episode count drift: expected {EXPECTED_EPISODES}, got {len(episodes)}"
        )

    market_rows = build_market_rows(events, episodes)
    add_equal_vol_fields(market_rows)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    write_csv(out / "issue78-risk-adjusted-edge-per-market.csv", market_rows)
    write_csv(out / "issue78-risk-adjusted-edge-universal.csv", summarize(market_rows))
    write_csv(
        out / "issue78-risk-adjusted-edge-comparisons.csv",
        comparison_rows(market_rows),
    )
    write_csv(
        out / "issue78-risk-adjusted-edge-direction.csv",
        direction_rows(events, episodes),
    )

    print("events", len(events), "episodes", len(episodes), "market_rows", len(market_rows))
    print("wrote", out)


if __name__ == "__main__":
    main()
