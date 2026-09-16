#!/usr/bin/env python3
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

POLICIES = (
    "p0_persistence_gentle",
    "p1_excursion_gentle",
    "p2_proof_eff_gentle",
    "p3_proof_eff_extension_gentle",
)
FRICTIONS = (0.00, 0.01, 0.02, 0.05, 0.10)
ERAS = (
    ("2010-2014", dt.datetime(2010, 1, 1, tzinfo=dt.timezone.utc), dt.datetime(2015, 1, 1, tzinfo=dt.timezone.utc)),
    ("2015-2019", dt.datetime(2015, 1, 1, tzinfo=dt.timezone.utc), dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc)),
    ("2020-2026", dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc), dt.datetime(2027, 1, 1, tzinfo=dt.timezone.utc)),
)
BOOTSTRAP_SEED = 8501
BOOTSTRAP_REPS = 5000
EPS = 1e-12


def excursion_cap(peak: float) -> float:
    if peak >= 2.0:
        return 1.0
    if peak >= 1.0:
        return 0.75
    if peak >= 0.5:
        return 0.50
    return 0.25


def participation_p2(steps: list[float]) -> list[float]:
    """Existing excursion proof plus the frozen 0.50 path-efficiency gate."""
    caps: list[float] = []
    cumulative = 0.0
    peak = 0.0
    path = 0.0
    for step in steps:
        efficiency = cumulative / path if path > EPS else math.nan
        baseline = excursion_cap(peak)
        if baseline <= 0.25 + EPS:
            cap = baseline
        elif math.isfinite(efficiency) and efficiency >= 0.50:
            cap = baseline
        else:
            cap = 0.25
        caps.append(cap)
        cumulative += step
        path += abs(step)
        peak = max(peak, cumulative)
    return caps


def participation_p3(steps: list[float]) -> list[float]:
    """P2 plus upgrade only after a fresh favorable close-path extreme."""
    caps: list[float] = []
    cumulative = 0.0
    peak = 0.0
    path = 0.0
    earned = 0.25
    previous_close_was_new_extreme = False

    for index, step in enumerate(steps):
        efficiency = cumulative / path if path > EPS else math.nan
        baseline = excursion_cap(peak)
        if (
            index > 0
            and previous_close_was_new_extreme
            and math.isfinite(efficiency)
            and efficiency >= 0.50
            and baseline > earned
        ):
            earned = baseline
        caps.append(earned)

        new_cumulative = cumulative + step
        previous_close_was_new_extreme = new_cumulative > peak + EPS
        if previous_close_was_new_extreme:
            peak = new_cumulative
        cumulative = new_cumulative
        path += abs(step)

    return caps


def participation(policy: str, steps: list[float]) -> list[float]:
    if policy == "p0_persistence_gentle":
        return base.participation_caps(steps, "persistence")
    if policy == "p1_excursion_gentle":
        return base.participation_caps(steps, "excursion")
    if policy == "p2_proof_eff_gentle":
        return participation_p2(steps)
    if policy == "p3_proof_eff_extension_gentle":
        return participation_p3(steps)
    raise ValueError(policy)


def simulate_episode(episode):
    ticker, stage, episode_id, rows = episode
    steps = base.steps_entry_atr(stage, rows)

    cumulative = 0.0
    mfe = 0.0
    for step in steps:
        cumulative += step
        mfe = max(mfe, cumulative)
    label = "Failed" if mfe < 4.0 else ("Large" if mfe >= 8.0 else "Middle")

    damage_latch, _, _ = base.latch_series(steps, base.LADDERS["gentle"])
    out = []
    for policy in POLICIES:
        caps = participation(policy, steps)
        exposure = [min(cap, damage) for cap, damage in zip(caps, damage_latch)]
        weighted = [e * move for e, move in zip(exposure, steps)]
        changes = [exposure[0]] + [exposure[i] - exposure[i - 1] for i in range(1, len(exposure))] + [-exposure[-1]]
        full_index = next((i for i, value in enumerate(exposure) if value >= 1.0 - EPS), None)
        out.append({
            "ticker": ticker,
            "stage_name": base.TREND[stage],
            "episode_id": episode_id,
            "start_time": rows[0]["event_time"],
            "bars": len(steps),
            "mfe": mfe,
            "label": label,
            "policy": policy,
            "gross_return": sum(weighted),
            "turnover": sum(abs(change) for change in changes),
            "step_returns": weighted,
            "avg_exposure": statistics.fmean(exposure),
            "bars_to_full_actual": float(full_index) if full_index is not None else math.nan,
            "ever_full_actual": 1.0 if full_index is not None else 0.0,
        })
    return out


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


def finite_mean(values):
    vals = [x for x in values if isinstance(x, (int, float)) and math.isfinite(x)]
    return statistics.fmean(vals) if vals else math.nan


def profit_factor(values):
    positive = sum(x for x in values if x > 0)
    negative = -sum(x for x in values if x < 0)
    if negative == 0:
        return math.inf if positive > 0 else math.nan
    return positive / negative


def max_drawdown(step_returns):
    equity = 0.0
    peak = 0.0
    drawdown = 0.0
    for value in step_returns:
        equity += value
        peak = max(peak, equity)
        drawdown = max(drawdown, peak - equity)
    return drawdown


def summarize_market(records):
    grouped = defaultdict(list)
    for row in records:
        grouped[(row["policy"], row["ticker"])].append(row)

    out = []
    for (policy, ticker), group in sorted(grouped.items()):
        group.sort(key=lambda r: r["start_time"])
        returns = [r["gross_return"] for r in group]
        step_path = [x for row in group for x in row["step_returns"]]
        turnover = sum(r["turnover"] for r in group)
        gross = sum(returns)
        row = {
            "policy": policy,
            "ticker": ticker,
            "n": len(group),
            "mean_episode_return": statistics.fmean(returns),
            "median_episode_return": statistics.median(returns),
            "profit_factor": profit_factor(returns),
            "cumulative_return": gross,
            "max_drawdown": max_drawdown(step_path),
            "turnover": turnover,
            "turnover_per_episode": turnover / len(group),
            "break_even_friction": gross / turnover if gross > 0 and turnover > 0 else math.nan,
            "avg_exposure": statistics.fmean(r["avg_exposure"] for r in group),
            "ever_full_actual": statistics.fmean(r["ever_full_actual"] for r in group),
            "bars_to_full_actual": finite_mean([r["bars_to_full_actual"] for r in group]),
        }
        for friction in FRICTIONS:
            row[f"net_mean_friction_{friction:.2f}"] = (gross - friction * turnover) / len(group)
            row[f"net_cum_friction_{friction:.2f}"] = gross - friction * turnover
        out.append(row)
    return out


def bootstrap95(records, policy):
    values_by_market = defaultdict(list)
    for row in records:
        if row["policy"] == policy:
            values_by_market[row["ticker"]].append(row["gross_return"])
    rng = random.Random(BOOTSTRAP_SEED)
    sims = []
    for _ in range(BOOTSTRAP_REPS):
        market_means = []
        for ticker in sorted(values_by_market):
            values = values_by_market[ticker]
            sample = [values[rng.randrange(len(values))] for _ in range(len(values))]
            market_means.append(statistics.fmean(sample))
        sims.append(statistics.fmean(market_means))
    return quantile(sims, 0.025), quantile(sims, 0.975)


def summarize_universal(records):
    market_rows = summarize_market(records)
    by_policy = defaultdict(list)
    for row in market_rows:
        by_policy[row["policy"]].append(row)

    out = []
    for policy, rows in sorted(by_policy.items()):
        means = [r["mean_episode_return"] for r in rows]
        loo = [statistics.fmean(means[:i] + means[i + 1:]) for i in range(len(means))]
        finite_pf = [r["profit_factor"] for r in rows if math.isfinite(r["profit_factor"])]
        lo, hi = bootstrap95(records, policy)
        result = {
            "policy": policy,
            "markets": len(rows),
            "episodes": sum(r["n"] for r in rows),
            "eq_market_mean_episode_return": statistics.fmean(means),
            "positive_mean_markets": sum(x > 0 for x in means),
            "eq_market_median_profit_factor": statistics.median(finite_pf),
            "eq_market_mean_max_drawdown": statistics.fmean(r["max_drawdown"] for r in rows),
            "eq_market_turnover_per_episode": statistics.fmean(r["turnover_per_episode"] for r in rows),
            "eq_market_break_even_friction": finite_mean([r["break_even_friction"] for r in rows]),
            "eq_market_avg_exposure": statistics.fmean(r["avg_exposure"] for r in rows),
            "eq_market_ever_full_actual": statistics.fmean(r["ever_full_actual"] for r in rows),
            "bootstrap95_lo": lo,
            "bootstrap95_hi": hi,
            "loo_min_eq_mean": min(loo),
            "loo_positive_count": sum(x > 0 for x in loo),
        }
        for friction in FRICTIONS:
            result[f"eq_market_net_mean_friction_{friction:.2f}"] = statistics.fmean(
                r[f"net_mean_friction_{friction:.2f}"] for r in rows
            )
            result[f"positive_markets_friction_{friction:.2f}"] = sum(
                r[f"net_cum_friction_{friction:.2f}"] > 0 for r in rows
            )
        out.append(result)
    return market_rows, out


def temporal_rows(records):
    out = []
    for policy in POLICIES:
        for era_name, start, end in ERAS:
            selected = []
            for row in records:
                when = dt.datetime.fromtimestamp(row["start_time"] / 1000.0, dt.timezone.utc)
                if row["policy"] == policy and start <= when < end:
                    selected.append(row)
            market = summarize_market(selected)
            means = [r["mean_episode_return"] for r in market]
            pfs = [r["profit_factor"] for r in market if math.isfinite(r["profit_factor"])]
            out.append({
                "policy": policy,
                "era": era_name,
                "episodes": len(selected),
                "markets": len(market),
                "eq_market_mean_episode_return": finite_mean(means),
                "positive_mean_markets": sum(x > 0 for x in means),
                "eq_market_median_profit_factor": statistics.median(pfs) if pfs else math.nan,
            })
    return out


def direction_rows(records):
    out = []
    for stage in ("Markup", "Markdown"):
        market = summarize_market([r for r in records if r["stage_name"] == stage])
        by_policy = defaultdict(list)
        for row in market:
            by_policy[row["policy"]].append(row)
        for policy, rows in sorted(by_policy.items()):
            means = [r["mean_episode_return"] for r in rows]
            pfs = [r["profit_factor"] for r in rows if math.isfinite(r["profit_factor"])]
            out.append({
                "stage": stage,
                "policy": policy,
                "markets": len(rows),
                "eq_market_mean_episode_return": statistics.fmean(means),
                "positive_mean_markets": sum(x > 0 for x in means),
                "eq_market_median_profit_factor": statistics.median(pfs),
            })
    return out


def decomposition_rows(records):
    raw = []
    for label in ("Failed", "Large", "Middle"):
        selected = [r for r in records if r["label"] == label]
        market = summarize_market(selected)
        by_policy = defaultdict(list)
        for row in market:
            by_policy[row["policy"]].append(row)
        for policy, rows in sorted(by_policy.items()):
            raw.append({
                "label": label,
                "policy": policy,
                "markets": len(rows),
                "episodes": sum(r["n"] for r in rows),
                "eq_market_mean_episode_return": statistics.fmean(r["mean_episode_return"] for r in rows),
                "eq_market_median_episode_return": statistics.fmean(r["median_episode_return"] for r in rows),
                "eq_market_avg_exposure": statistics.fmean(r["avg_exposure"] for r in rows),
                "eq_market_ever_full_actual": statistics.fmean(r["ever_full_actual"] for r in rows),
                "eq_market_bars_to_full_actual": finite_mean([r["bars_to_full_actual"] for r in rows]),
            })

    lookup = {(r["label"], r["policy"]): r for r in raw}
    p0_large = lookup[("Large", "p0_persistence_gentle")]["eq_market_mean_episode_return"]
    p0_failed = lookup[("Failed", "p0_persistence_gentle")]["eq_market_mean_episode_return"]
    for row in raw:
        if row["label"] == "Large":
            row["vs_p0_ratio"] = row["eq_market_mean_episode_return"] / p0_large
            row["vs_p0_delta"] = row["eq_market_mean_episode_return"] - p0_large
        elif row["label"] == "Failed":
            row["vs_p0_ratio"] = abs(row["eq_market_mean_episode_return"]) / abs(p0_failed)
            row["vs_p0_delta"] = row["eq_market_mean_episode_return"] - p0_failed
        else:
            row["vs_p0_ratio"] = math.nan
            row["vs_p0_delta"] = math.nan
    return raw


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
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

    records = [row for episode in episodes for row in simulate_episode(episode)]
    market, universal = summarize_universal(records)
    temporal = temporal_rows(records)
    direction = direction_rows(records)
    decomposition = decomposition_rows(records)

    out = Path(args.output_dir)
    write_csv(out / "issue85-proof-sizing-per-market.csv", market)
    write_csv(out / "issue85-proof-sizing-universal.csv", universal)
    write_csv(out / "issue85-proof-sizing-temporal.csv", temporal)
    write_csv(out / "issue85-proof-sizing-direction.csv", direction)
    write_csv(out / "issue85-proof-sizing-decomposition.csv", decomposition)

    print(f"events={len(events)} episodes={len(episodes)} policies={len(POLICIES)}")
    for row in universal:
        print(
            row["policy"],
            f"mean={row['eq_market_mean_episode_return']:+.3f}",
            f"pos={row['positive_mean_markets']}/{row['markets']}",
            f"pf={row['eq_market_median_profit_factor']:.3f}",
            f"mdd={row['eq_market_mean_max_drawdown']:.2f}",
        )


if __name__ == "__main__":
    main()
