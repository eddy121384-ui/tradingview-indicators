#!/usr/bin/env python3
"""Issue #78 weekly opposition age / maturity diagnostic.

Uses accepted Issue #76 daily logs plus native-1W Issue #78 context logs.
Only fresh daily Markup / Markdown entries whose latest completed weekly bar is
in the opposite directional family are included.
"""
from __future__ import annotations

import argparse
import bisect
import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path

import analyze_issue78_weekly_conflict_diagnostic as base

GENTLE = (1.00, 1.00, 0.75, 0.50, 0.25)


def weekly_family(formal: int):
    if formal in (2, 3):
        return "bull"
    if formal in (5, 6):
        return "bear"
    return None


def opposing_family(daily_stage: int):
    return "bear" if daily_stage == 2 else "bull"


def age_bucket(age: int):
    if age <= 4:
        return "Young_1_4"
    if age <= 13:
        return "Intermediate_5_13"
    return "Mature_14p"


def weekly_index(rows):
    by_ticker = defaultdict(list)
    for row in rows:
        by_ticker[row["ticker"]].append(row)
    return {
        ticker: ([row["week_close_time"] for row in group], group)
        for ticker, group in by_ticker.items()
    }


def opposing_spell_age(index, ticker, event_time, daily_stage):
    closes, rows = index[ticker]
    i = bisect.bisect_right(closes, event_time) - 1
    if i < 0:
        return 0
    wanted = opposing_family(daily_stage)
    if weekly_family(rows[i]["formal"]) != wanted:
        return 0
    age = 1
    i -= 1
    while i >= 0 and weekly_family(rows[i]["formal"]) == wanted:
        age += 1
        i -= 1
    return age


def steps_entry_atr(stage, rows):
    denom = rows[0]["scale"] * (100.0 if rows[0]["repr"] == "YIELD_LEVEL" else 1.0)
    direction = 1.0 if stage == 2 else -1.0
    return [row["move1"] / denom * direction for row in rows]


def giveback_bucket(value):
    if value < 0.5:
        return 0
    if value < 1.0:
        return 1
    if value < 2.0:
        return 2
    if value < 4.0:
        return 3
    return 4


def participation_cap(age):
    if age < 5:
        return 0.25
    if age < 10:
        return 0.50
    if age < 20:
        return 0.75
    return 1.00


def persistence_gentle(steps):
    cum = peak = retained = 0.0
    latch = 1.0
    prior_new_extreme = False
    for age, move in enumerate(steps):
        if age == 0 or prior_new_extreme:
            latch = 1.0
        else:
            latch = min(latch, GENTLE[giveback_bucket(max(0.0, peak - cum))])
        retained += min(participation_cap(age), latch) * move
        new_cum = cum + move
        prior_new_extreme = new_cum > peak + 1e-12
        if prior_new_extreme:
            peak = new_cum
        cum = new_cum
    return retained


def mean(values):
    return statistics.fmean(values) if values else math.nan


def write_csv(path, rows):
    if not rows:
        return
    with Path(path).open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--daily", nargs="+", required=True)
    parser.add_argument("--weekly", nargs="+", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    events = base.read_daily(args.daily)
    weekly_rows, _ = base.read_weekly(args.weekly)
    episodes = base.reconstruct_episodes(events)
    if len(events) != 68118 or len(weekly_rows) != 16372 or len(episodes) != 1624:
        raise SystemExit(f"sample drift: daily={len(events)} weekly={len(weekly_rows)} episodes={len(episodes)}")

    windex = weekly_index(weekly_rows)
    records = []
    for ticker, stage, _, rows in episodes:
        age = opposing_spell_age(windex, ticker, rows[0]["event_time"], stage)
        if age <= 0:
            continue
        steps = steps_entry_atr(stage, rows)
        cum = peak = 0.0
        for move in steps:
            cum += move
            peak = max(peak, cum)
        records.append({
            "ticker": ticker,
            "stage": base.TREND[stage],
            "bucket": age_bucket(age),
            "age_weeks": age,
            "ret": persistence_gentle(steps),
            "mfe": peak,
            "duration": len(rows),
            "mfe4": 1.0 if peak >= 4.0 else 0.0,
            "mfe8": 1.0 if peak >= 8.0 else 0.0,
            "positive": 1.0 if persistence_gentle(steps) > 0 else 0.0,
        })

    grouped = defaultdict(list)
    for row in records:
        grouped[(row["ticker"], row["stage"], row["bucket"])].append(row)
    per_market = []
    for (ticker, stage, bucket), group in grouped.items():
        per_market.append({
            "ticker": ticker,
            "stage": stage,
            "bucket": bucket,
            "n": len(group),
            "ret": mean([x["ret"] for x in group]),
            "mfe": mean([x["mfe"] for x in group]),
            "duration": mean([x["duration"] for x in group]),
            "mfe4": mean([x["mfe4"] for x in group]),
            "mfe8": mean([x["mfe8"] for x in group]),
            "positive": mean([x["positive"] for x in group]),
        })

    grouped = defaultdict(list)
    for row in per_market:
        grouped[(row["stage"], row["bucket"])].append(row)
    universal = []
    for (stage, bucket), group in grouped.items():
        universal.append({
            "stage": stage,
            "bucket": bucket,
            "markets": len(group),
            "n": sum(x["n"] for x in group),
            "ret": mean([x["ret"] for x in group]),
            "mfe": mean([x["mfe"] for x in group]),
            "duration": mean([x["duration"] for x in group]),
            "mfe4": mean([x["mfe4"] for x in group]),
            "mfe8": mean([x["mfe8"] for x in group]),
            "positive": mean([x["positive"] for x in group]),
        })

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "issue78-weekly-opposition-age-episodes.csv", records)
    write_csv(out / "issue78-weekly-opposition-age-per-market.csv", per_market)
    write_csv(out / "issue78-weekly-opposition-age-universal.csv", universal)
    print(f"opposing_entries={len(records)}")
    for row in sorted(universal, key=lambda x: (x["stage"], x["bucket"])):
        print(row)


if __name__ == "__main__":
    main()
