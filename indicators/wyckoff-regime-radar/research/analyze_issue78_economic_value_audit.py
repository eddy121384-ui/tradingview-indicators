#!/usr/bin/env python3
"""Issue #78 risk-normalized economic-value audit.

Reuses the frozen episode reconstruction and exposure rules from
analyze_issue78_participation_ramp.py. This is descriptive in-sample research,
not an executable broker-fill / futures PnL backtest.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import math
import random
import statistics
from collections import defaultdict
from pathlib import Path

import analyze_issue78_participation_ramp as base

POLICIES = [
    ("formal_hold", "full", None),
    ("full_gentle_latch", "full", "gentle"),
    ("full_balanced_latch", "full", "balanced"),
    ("persistence_gentle_latch", "persistence", "gentle"),
    ("persistence_balanced_latch", "persistence", "balanced"),
    ("excursion_gentle_latch", "excursion", "gentle"),
    ("excursion_balanced_latch", "excursion", "balanced"),
]
FRICTIONS = (0.00, 0.01, 0.02, 0.05, 0.10)
BOOTSTRAP_SEED = 7801
BOOTSTRAP_REPS = 5000
ERAS = (
    ("2010-2014", dt.datetime(2010, 1, 1, tzinfo=dt.timezone.utc), dt.datetime(2015, 1, 1, tzinfo=dt.timezone.utc)),
    ("2015-2019", dt.datetime(2015, 1, 1, tzinfo=dt.timezone.utc), dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc)),
    ("2020-2026", dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc), dt.datetime(2027, 1, 1, tzinfo=dt.timezone.utc)),
)


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


def profit_factor(values):
    pos = sum(x for x in values if x > 0)
    neg = -sum(x for x in values if x < 0)
    if neg == 0:
        return math.inf if pos > 0 else math.nan
    return pos / neg


def max_drawdown(step_returns):
    equity = peak = drawdown = 0.0
    for value in step_returns:
        equity += value
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
    return drawdown


def simulate_episode(ep):
    ticker, stage, episode_id, rows = ep
    steps = base.steps_entry_atr(stage, rows)
    out = []
    for policy, participation_mode, latch_name in POLICIES:
        caps = base.participation_caps(steps, participation_mode)
        if latch_name is None:
            latch = [1.0] * len(steps)
        else:
            latch, _, _ = base.latch_series(steps, base.LADDERS[latch_name])
        exposure = [min(cap, damage) for cap, damage in zip(caps, latch)]
        weighted = [e * move for e, move in zip(exposure, steps)]
        changes = [exposure[0]] + [exposure[i] - exposure[i - 1] for i in range(1, len(exposure))] + [-exposure[-1]]
        out.append({
            "ticker": ticker,
            "stage_name": base.TREND[stage],
            "episode_id": episode_id,
            "start_time": rows[0]["event_time"],
            "policy": policy,
            "gross_return": sum(weighted),
            "turnover": sum(abs(x) for x in changes),
            "step_returns": weighted,
        })
    return out


def summarize_market(records):
    grouped = defaultdict(list)
    for row in records:
        grouped[(row["policy"], row["ticker"])].append(row)
    out = []
    for (policy, ticker), group in sorted(grouped.items()):
        group.sort(key=lambda r: r["start_time"])
        returns = [r["gross_return"] for r in group]
        winners = [x for x in returns if x > 0]
        losers = [x for x in returns if x < 0]
        step_path = [x for row in group for x in row["step_returns"]]
        turnover = sum(r["turnover"] for r in group)
        gross = sum(returns)
        k = max(1, math.ceil(0.01 * len(returns)))
        positive_sorted = sorted(winners, reverse=True)
        positive_sum = sum(positive_sorted)

        remove_best = list(returns)
        if remove_best:
            i = max(range(len(remove_best)), key=lambda j: remove_best[j])
            if remove_best[i] > 0:
                remove_best[i] = 0.0

        remove_top1 = list(returns)
        pos_idx = sorted((i for i, x in enumerate(remove_top1) if x > 0), key=lambda i: remove_top1[i], reverse=True)
        for i in pos_idx[:k]:
            remove_top1[i] = 0.0

        cap95 = quantile(winners, 0.95) if winners else math.nan
        capped = [min(x, cap95) if x > 0 and math.isfinite(cap95) else x for x in returns]

        row = {
            "policy": policy,
            "ticker": ticker,
            "n": len(returns),
            "mean_episode_return": statistics.fmean(returns),
            "median_episode_return": statistics.median(returns),
            "win_rate": len(winners) / len(returns),
            "mean_winner": statistics.fmean(winners) if winners else math.nan,
            "mean_loser": statistics.fmean(losers) if losers else math.nan,
            "profit_factor": profit_factor(returns),
            "cumulative_return": gross,
            "max_drawdown": max_drawdown(step_path),
            "turnover": turnover,
            "break_even_friction": gross / turnover if gross > 0 and turnover > 0 else math.nan,
            "top1pct_positive_share": sum(positive_sorted[:k]) / positive_sum if positive_sum > 0 else math.nan,
            "stress_remove_best_mean": statistics.fmean(remove_best),
            "stress_remove_top1pct_mean": statistics.fmean(remove_top1),
            "stress_cap95_mean": statistics.fmean(capped),
        }
        for friction in FRICTIONS:
            row[f"net_mean_friction_{friction:.2f}"] = (gross - friction * turnover) / len(returns)
            row[f"net_cum_friction_{friction:.2f}"] = gross - friction * turnover
        out.append(row)
    return out


def bootstrap95(values_by_market):
    rng = random.Random(BOOTSTRAP_SEED)
    tickers = sorted(values_by_market)
    sims = []
    for _ in range(BOOTSTRAP_REPS):
        market_means = []
        for ticker in tickers:
            values = values_by_market[ticker]
            sample = [values[rng.randrange(len(values))] for _ in range(len(values))]
            market_means.append(statistics.fmean(sample))
        sims.append(statistics.fmean(market_means))
    return quantile(sims, 0.025), quantile(sims, 0.975)


def summarize_universal(market_rows, records):
    by_policy = defaultdict(list)
    episode_values = defaultdict(lambda: defaultdict(list))
    for row in market_rows:
        by_policy[row["policy"]].append(row)
    for row in records:
        episode_values[row["policy"]][row["ticker"]].append(row["gross_return"])

    out = []
    for policy, rows in sorted(by_policy.items()):
        means = [r["mean_episode_return"] for r in rows]
        loo = [statistics.fmean(means[:i] + means[i + 1:]) for i in range(len(means))]
        pf = [r["profit_factor"] for r in rows if math.isfinite(r["profit_factor"])]
        lo, hi = bootstrap95(episode_values[policy])
        result = {
            "policy": policy,
            "markets": len(rows),
            "eq_market_mean_episode_return": statistics.fmean(means),
            "positive_mean_markets": sum(x > 0 for x in means),
            "pf_gt1_markets": sum(r["profit_factor"] > 1 for r in rows),
            "positive_cumulative_markets": sum(r["cumulative_return"] > 0 for r in rows),
            "eq_market_median_profit_factor": statistics.median(pf),
            "eq_market_mean_max_drawdown": statistics.fmean(r["max_drawdown"] for r in rows),
            "bootstrap95_lo": lo,
            "bootstrap95_hi": hi,
            "loo_min_eq_mean": min(loo),
            "loo_max_eq_mean": max(loo),
            "loo_positive_count": sum(x > 0 for x in loo),
            "eq_market_top1pct_positive_share": statistics.fmean(r["top1pct_positive_share"] for r in rows),
            "eq_market_stress_remove_best_mean": statistics.fmean(r["stress_remove_best_mean"] for r in rows),
            "eq_market_stress_remove_top1pct_mean": statistics.fmean(r["stress_remove_top1pct_mean"] for r in rows),
            "eq_market_stress_cap95_mean": statistics.fmean(r["stress_cap95_mean"] for r in rows),
        }
        for friction in FRICTIONS:
            key = f"net_mean_friction_{friction:.2f}"
            result[f"eq_market_{key}"] = statistics.fmean(r[key] for r in rows)
            result[f"positive_markets_friction_{friction:.2f}"] = sum(r[f"net_cum_friction_{friction:.2f}"] > 0 for r in rows)
        out.append(result)
    return out


def summarize_temporal(records):
    out = []
    policies = sorted(set(r["policy"] for r in records))
    for policy in policies:
        for era, start, end in ERAS:
            by_market = defaultdict(list)
            for row in records:
                if row["policy"] != policy:
                    continue
                when = dt.datetime.fromtimestamp(row["start_time"] / 1000.0, dt.timezone.utc)
                if start <= when < end:
                    by_market[row["ticker"]].append(row["gross_return"])
            means = [statistics.fmean(v) for v in by_market.values()]
            pfs = [profit_factor(v) for v in by_market.values()]
            out.append({
                "policy": policy,
                "era": era,
                "total_episodes": sum(len(v) for v in by_market.values()),
                "markets": len(by_market),
                "eq_market_mean_episode_return": statistics.fmean(means),
                "positive_mean_markets": sum(x > 0 for x in means),
                "eq_market_median_profit_factor": statistics.median(pfs),
                "min_market_episode_count": min(len(v) for v in by_market.values()),
                "max_market_episode_count": max(len(v) for v in by_market.values()),
            })
    return out


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", help="accepted Issue #76 Pine-log CSV files")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    events = base.read_events([Path(x) for x in args.inputs])
    episodes = base.episodes(events)
    if len(events) != 68118:
        raise SystemExit(f"event count drift: {len(events)}")
    if len(episodes) != 1624:
        raise SystemExit(f"episode count drift: {len(episodes)}")

    records = []
    for episode in episodes:
        records.extend(simulate_episode(episode))

    market_rows = summarize_market(records)
    universal_rows = summarize_universal(market_rows, records)
    temporal_rows = summarize_temporal(records)

    out = Path(args.output_dir)
    write_csv(out / "issue78-economic-value-per-market.csv", market_rows)
    write_csv(out / "issue78-economic-value-universal.csv", universal_rows)
    write_csv(out / "issue78-economic-value-temporal.csv", temporal_rows)
    print(f"events={len(events)} episodes={len(episodes)} policies={len(POLICIES)}")


if __name__ == "__main__":
    main()
