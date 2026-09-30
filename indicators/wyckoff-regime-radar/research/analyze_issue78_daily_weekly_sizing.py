#!/usr/bin/env python3
"""Issue #78 Daily Trigger × Weekly Sizing Context analysis.

Consumes the accepted Issue #76 daily logger CSVs plus native-1W ISSUE78WEEKLY
logger CSVs. Weekly observations are joined causally using the frozen rule:

    week_close_time <= daily event_time

No incomplete weekly bar is visible to a daily decision.
"""
from __future__ import annotations

import argparse
import bisect
import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path

import analyze_issue78_participation_ramp as base
import analyze_issue78_economic_value_audit as econ

WEEKLY_MARKER = "ISSUE78WEEKLY|schema=1"
FROZEN_TICKERS = {
    "OANDA:EURUSD", "OANDA:GBPUSD", "OANDA:USDJPY",
    "TVC:US10Y", "TVC:DE10Y", "TVC:FR10Y", "TVC:GB10Y", "TVC:AU10Y", "TVC:JP10Y",
}
POLICY_DAILY = "daily_persistence_gentle"
POLICY_WEEKLY_DIR = "daily_plus_weekly_direction"
POLICY_WEEKLY_TREND = "daily_plus_weekly_direction_trendability"
POLICIES = (POLICY_DAILY, POLICY_WEEKLY_DIR, POLICY_WEEKLY_TREND)


def parse_marker(text: str):
    p = text.find(WEEKLY_MARKER)
    if p < 0:
        return None
    out = {}
    for token in text[p:].strip().split("|"):
        if "=" in token:
            key, value = token.split("=", 1)
            out[key] = value
    return out


def float_or_nan(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan


def read_weekly(paths):
    dedup = {}
    for path in paths:
        with Path(path).open(encoding="utf-8-sig", newline="") as fh:
            for row in csv.reader(fh):
                fields = None
                for cell in row:
                    fields = parse_marker(cell)
                    if fields:
                        break
                if not fields:
                    continue
                rec = {
                    "ticker": fields["ticker"],
                    "repr": fields["repr"],
                    "week_open_time": int(fields["week_open_time"]),
                    "week_close_time": int(fields["week_close_time"]),
                    "week_bar": int(fields["week_bar"]),
                    "formal": int(fields["formal"]),
                    "er13": float_or_nan(fields.get("er13")),
                    "er26": float_or_nan(fields.get("er26")),
                    "er52": float_or_nan(fields.get("er52")),
                    "er13r": float_or_nan(fields.get("er13r")),
                    "er26r": float_or_nan(fields.get("er26r")),
                    "er52r": float_or_nan(fields.get("er52r")),
                    "wtrend": float_or_nan(fields.get("wtrend")),
                }
                if rec["ticker"] not in FROZEN_TICKERS:
                    raise SystemExit(f"unexpected weekly ticker: {rec['ticker']}")
                if rec["week_close_time"] < rec["week_open_time"]:
                    raise SystemExit(f"weekly close before open: {rec}")
                key = (rec["ticker"], rec["week_open_time"], rec["week_bar"])
                old = dedup.get(key)
                if old is not None and old != rec:
                    raise SystemExit(f"conflicting duplicate weekly row: {key}")
                dedup[key] = rec

    rows = sorted(dedup.values(), key=lambda r: (r["ticker"], r["week_close_time"], r["week_bar"]))
    by_ticker = defaultdict(list)
    for rec in rows:
        by_ticker[rec["ticker"]].append(rec)

    if set(by_ticker) != FROZEN_TICKERS:
        missing = sorted(FROZEN_TICKERS - set(by_ticker))
        raise SystemExit(f"weekly ticker coverage incomplete; missing={missing}")

    for ticker, group in by_ticker.items():
        closes = [r["week_close_time"] for r in group]
        if closes != sorted(closes):
            raise SystemExit(f"weekly close times not monotonic: {ticker}")
        if len(closes) != len(set(closes)):
            raise SystemExit(f"duplicate weekly close times: {ticker}")
    return rows, by_ticker


def weekly_lookup_index(by_ticker):
    return {
        ticker: ([r["week_close_time"] for r in rows], rows)
        for ticker, rows in by_ticker.items()
    }


def asof_weekly(index, ticker, daily_event_time):
    closes, rows = index[ticker]
    i = bisect.bisect_right(closes, daily_event_time) - 1
    return rows[i] if i >= 0 else None


def weekly_direction_cap(daily_stage, ctx):
    if ctx is None:
        return 0.50
    wf = ctx["formal"]
    if wf == daily_stage:
        return 1.00
    if (daily_stage == 2 and wf == 5) or (daily_stage == 5 and wf == 2):
        return 0.25
    return 0.50


def weekly_trendability_cap(daily_stage, ctx):
    if ctx is None:
        return 0.50
    wf = ctx["formal"]
    if (daily_stage == 2 and wf == 5) or (daily_stage == 5 and wf == 2):
        return 0.25
    if wf != daily_stage:
        return 0.50
    wt = ctx["wtrend"]
    return 1.00 if math.isfinite(wt) and wt > 66.67 else 0.50


def exposure_stats(exposure):
    changes = [exposure[0]] + [exposure[i] - exposure[i - 1] for i in range(1, len(exposure))] + [-exposure[-1]]
    first_full = next((i for i, x in enumerate(exposure) if x >= 1.0 - 1e-12), None)
    return {
        "turnover": sum(abs(x) for x in changes),
        "avg_exposure": statistics.fmean(exposure),
        "underexposed_frac": statistics.fmean(1.0 if x < 1.0 - 1e-12 else 0.0 for x in exposure),
        "bars_to_full": float(first_full) if first_full is not None else math.nan,
        "ever_full": 1.0 if first_full is not None else 0.0,
    }


def simulate_episode(ep, weekly_index):
    ticker, stage, episode_id, rows = ep
    steps = base.steps_entry_atr(stage, rows)
    participation = base.participation_caps(steps, "persistence")
    health, _, _ = base.latch_series(steps, base.LADDERS["gentle"])
    daily_exp = [min(p, h) for p, h in zip(participation, health)]

    contexts = [asof_weekly(weekly_index, ticker, r["event_time"]) for r in rows]
    dir_caps = [weekly_direction_cap(stage, ctx) for ctx in contexts]
    trend_caps = [weekly_trendability_cap(stage, ctx) for ctx in contexts]

    exposure_by_policy = {
        POLICY_DAILY: daily_exp,
        POLICY_WEEKLY_DIR: [min(d, w) for d, w in zip(daily_exp, dir_caps)],
        POLICY_WEEKLY_TREND: [min(d, w) for d, w in zip(daily_exp, trend_caps)],
    }

    cum = 0.0
    mfe = 0.0
    for step in steps:
        cum += step
        mfe = max(mfe, cum)

    out = []
    base_exp = exposure_by_policy[POLICY_DAILY]
    for policy, exposure in exposure_by_policy.items():
        weighted = [e * move for e, move in zip(exposure, steps)]
        stats = exposure_stats(exposure)
        weekly_changes = 0
        if policy != POLICY_DAILY:
            caps = dir_caps if policy == POLICY_WEEKLY_DIR else trend_caps
            weekly_changes = sum(1 for i in range(1, len(caps)) if abs(caps[i] - caps[i - 1]) > 1e-12)

        favorable_missed = 0.0
        adverse_avoided = 0.0
        for b, e, move in zip(base_exp, exposure, steps):
            reduction = max(0.0, b - e)
            if move > 0:
                favorable_missed += reduction * move
            elif move < 0:
                adverse_avoided += reduction * (-move)

        out.append({
            "ticker": ticker,
            "stage_name": base.TREND[stage],
            "episode_id": episode_id,
            "start_time": rows[0]["event_time"],
            "bars": len(rows),
            "mfe": mfe,
            "policy": policy,
            "gross_return": sum(weighted),
            "turnover": stats["turnover"],
            "step_returns": weighted,
            "avg_exposure": stats["avg_exposure"],
            "underexposed_frac": stats["underexposed_frac"],
            "bars_to_full": stats["bars_to_full"],
            "ever_full": stats["ever_full"],
            "weekly_cap_changes": weekly_changes,
            "weekly_missing_frac": statistics.fmean(1.0 if c is None else 0.0 for c in contexts),
            "weekly_high_trend_frac": statistics.fmean(1.0 if c is not None and math.isfinite(c["wtrend"]) and c["wtrend"] > 66.67 else 0.0 for c in contexts),
            "favorable_missed_vs_daily": favorable_missed,
            "adverse_avoided_vs_daily": adverse_avoided,
        })
    return out


def write_csv(path, rows, omit=()):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    fields = [k for k in rows[0].keys() if k not in set(omit)]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def slice_summary(records):
    slices = (
        ("all", lambda x: True),
        ("mfe_lt4", lambda x: x < 4.0),
        ("mfe_ge4", lambda x: x >= 4.0),
        ("mfe_ge8", lambda x: x >= 8.0),
    )
    out = []
    for slice_name, pred in slices:
        selected = [r for r in records if pred(r["mfe"])]
        grouped = defaultdict(list)
        for row in selected:
            grouped[(row["policy"], row["ticker"], row["stage_name"])].append(row)
        market_rows = []
        for (policy, ticker, stage_name), group in grouped.items():
            returns = [r["gross_return"] for r in group]
            market_rows.append({
                "slice": slice_name,
                "policy": policy,
                "ticker": ticker,
                "stage_name": stage_name,
                "n": len(group),
                "mean_return": statistics.fmean(returns),
                "median_return": statistics.median(returns),
                "mean_avg_exposure": statistics.fmean(r["avg_exposure"] for r in group),
                "mean_underexposed_frac": statistics.fmean(r["underexposed_frac"] for r in group),
                "mean_favorable_missed_vs_daily": statistics.fmean(r["favorable_missed_vs_daily"] for r in group),
                "mean_adverse_avoided_vs_daily": statistics.fmean(r["adverse_avoided_vs_daily"] for r in group),
                "ever_full_rate": statistics.fmean(r["ever_full"] for r in group),
            })
        by = defaultdict(list)
        for row in market_rows:
            by[(row["slice"], row["policy"], row["stage_name"])].append(row)
        for (sl, policy, stage_name), group in by.items():
            out.append({
                "slice": sl,
                "policy": policy,
                "stage_name": stage_name,
                "markets": len(group),
                "pooled_n": sum(r["n"] for r in group),
                "eq_market_mean_return": statistics.fmean(r["mean_return"] for r in group),
                "eq_market_median_of_medians": statistics.fmean(r["median_return"] for r in group),
                "eq_market_mean_exposure": statistics.fmean(r["mean_avg_exposure"] for r in group),
                "eq_market_mean_favorable_missed": statistics.fmean(r["mean_favorable_missed_vs_daily"] for r in group),
                "eq_market_mean_adverse_avoided": statistics.fmean(r["mean_adverse_avoided_vs_daily"] for r in group),
                "eq_market_ever_full_rate": statistics.fmean(r["ever_full_rate"] for r in group),
            })
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--daily", nargs="+", required=True, help="accepted Issue #76 daily Pine-log CSVs")
    parser.add_argument("--weekly", nargs="+", required=True, help="Issue #78 native-1W context Pine-log CSVs")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    events = base.read_events([Path(x) for x in args.daily])
    episodes = base.episodes(events)
    if len(events) != 68118:
        raise SystemExit(f"daily event count drift: {len(events)}")
    if len(episodes) != 1624:
        raise SystemExit(f"daily episode count drift: {len(episodes)}")

    weekly_rows, weekly_by_ticker = read_weekly([Path(x) for x in args.weekly])
    weekly_index = weekly_lookup_index(weekly_by_ticker)

    records = []
    for episode in episodes:
        records.extend(simulate_episode(episode, weekly_index))

    # Verify the daily-only branch exactly reproduces the already-frozen practical candidate logic.
    daily_records = [r for r in records if r["policy"] == POLICY_DAILY]
    if len(daily_records) != 1624:
        raise SystemExit(f"daily benchmark record count drift: {len(daily_records)}")

    market_rows = econ.summarize_market(records)
    universal_rows = econ.summarize_universal(market_rows, records)
    temporal_rows = econ.summarize_temporal(records)
    slices = slice_summary(records)

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "issue78-daily-weekly-sizing-episodes.csv", records, omit=("step_returns",))
    write_csv(out / "issue78-daily-weekly-sizing-per-market.csv", market_rows)
    write_csv(out / "issue78-daily-weekly-sizing-universal.csv", universal_rows)
    write_csv(out / "issue78-daily-weekly-sizing-temporal.csv", temporal_rows)
    write_csv(out / "issue78-daily-weekly-sizing-slices.csv", slices)
    write_csv(out / "issue78-weekly-context-parsed.csv", weekly_rows)

    print(f"daily_events={len(events)} episodes={len(episodes)} weekly_rows={len(weekly_rows)} records={len(records)}")
    for row in universal_rows:
        print(
            f"{row['policy']:45s} mean={row['eq_market_mean_episode_return']:+.4f} "
            f"positive={row['positive_mean_markets']}/9 pf={row['eq_market_median_profit_factor']:.3f} "
            f"mdd={row['eq_market_mean_max_drawdown']:.2f} "
            f"top1stress={row['eq_market_stress_remove_top1pct_mean']:+.4f}"
        )
    print("\nTemporal:")
    for row in temporal_rows:
        print(
            f"{row['policy']:45s} {row['era']} mean={row['eq_market_mean_episode_return']:+.4f} "
            f"positive={row['positive_mean_markets']}/{row['markets']}"
        )


if __name__ == "__main__":
    main()
