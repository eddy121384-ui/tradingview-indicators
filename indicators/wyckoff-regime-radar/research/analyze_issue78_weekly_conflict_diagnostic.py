#!/usr/bin/env python3
"""Issue #78 static weekly-conflict diagnostic.

Consumes accepted Issue #76 daily logs and native-1W Issue #78 context logs.
Weekly context is joined causally with week_close_time <= daily event_time.
"""
from __future__ import annotations

import argparse
import bisect
import csv
import datetime as dt
import math
import statistics
from collections import defaultdict
from pathlib import Path

DAILY_MARKER = "ISSUE76|schema=1"
WEEKLY_MARKER = "ISSUE78WEEKLY|schema=1"
TREND = {2: "Markup", 5: "Markdown"}
ERAS = (
    ("2010-2014", dt.datetime(2010, 1, 1, tzinfo=dt.timezone.utc), dt.datetime(2015, 1, 1, tzinfo=dt.timezone.utc)),
    ("2015-2019", dt.datetime(2015, 1, 1, tzinfo=dt.timezone.utc), dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc)),
    ("2020-2026", dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc), dt.datetime(2027, 1, 1, tzinfo=dt.timezone.utc)),
)
GENTLE = (1.00, 1.00, 0.75, 0.50, 0.25)


def parse_marker(text, marker):
    pos = text.find(marker)
    if pos < 0:
        return None
    out = {}
    for token in text[pos:].strip().split("|"):
        if "=" in token:
            key, value = token.split("=", 1)
            out[key] = value
    return out


def mean_finite(values):
    xs = [x for x in values if isinstance(x, (int, float)) and math.isfinite(x)]
    return statistics.fmean(xs) if xs else math.nan


def read_daily(paths):
    dedup = {}
    for path in paths:
        with Path(path).open(encoding="utf-8-sig", newline="") as fh:
            for row in csv.reader(fh):
                fields = next((parse_marker(cell, DAILY_MARKER) for cell in row if DAILY_MARKER in cell), None)
                if not fields:
                    continue
                rec = {
                    "ticker": fields["ticker"],
                    "repr": fields["repr"],
                    "event_time": int(fields["event_time"]),
                    "event_bar": int(fields["event_bar"]),
                    "stage": int(fields["stage"]),
                    "fresh": int(fields["fresh"]),
                    "scale": float(fields["scale"]),
                    "move1": float(fields["move1"]),
                }
                for horizon in (1, 5, 10, 20):
                    rec[f"norm{horizon}"] = float(fields.get(f"norm{horizon}", "nan"))
                dedup[(rec["ticker"], rec["event_time"], rec["event_bar"])] = rec
    return sorted(dedup.values(), key=lambda row: (row["ticker"], row["event_bar"]))


def read_weekly(paths):
    dedup = {}
    for path in paths:
        with Path(path).open(encoding="utf-8-sig", newline="") as fh:
            for row in csv.reader(fh):
                fields = next((parse_marker(cell, WEEKLY_MARKER) for cell in row if WEEKLY_MARKER in cell), None)
                if not fields:
                    continue
                try:
                    wtrend = float(fields.get("wtrend", "nan"))
                except ValueError:
                    wtrend = math.nan
                rec = {
                    "ticker": fields["ticker"],
                    "week_open_time": int(fields["week_open_time"]),
                    "week_close_time": int(fields["week_close_time"]),
                    "week_bar": int(fields["week_bar"]),
                    "formal": int(fields["formal"]),
                    "wtrend": wtrend,
                }
                dedup[(rec["ticker"], rec["week_open_time"], rec["week_bar"])] = rec
    rows = sorted(dedup.values(), key=lambda row: (row["ticker"], row["week_close_time"]))
    by_ticker = defaultdict(list)
    for row in rows:
        by_ticker[row["ticker"]].append(row)
    index = {ticker: ([row["week_close_time"] for row in group], group) for ticker, group in by_ticker.items()}
    return rows, index


def asof_weekly(index, ticker, event_time):
    closes, rows = index[ticker]
    i = bisect.bisect_right(closes, event_time) - 1
    return rows[i] if i >= 0 else None


def context_bucket(daily_stage, weekly):
    if weekly is None:
        return "Other"
    wf = weekly["formal"]
    if daily_stage == 2:
        if wf in (2, 3):
            return "Aligned"
        if wf == 4:
            return "TurnRisk"
        if wf in (5, 6):
            return "DirectionalConflict"
        return "Other"
    if daily_stage == 5:
        if wf in (5, 6):
            return "Aligned"
        if wf == 1:
            return "TurnRisk"
        if wf in (2, 3):
            return "DirectionalConflict"
        return "Other"
    raise ValueError(daily_stage)


def reconstruct_episodes(events):
    by_ticker = defaultdict(list)
    for row in events:
        by_ticker[row["ticker"]].append(row)
    out = []
    for ticker, group in by_ticker.items():
        group.sort(key=lambda row: row["event_bar"])
        i = 0
        episode_id = 0
        while i < len(group):
            row = group[i]
            stage = row["stage"]
            if stage in TREND and row["fresh"] == 1:
                j = i + 1
                while j < len(group) and group[j]["stage"] == stage and group[j]["event_bar"] == group[j - 1]["event_bar"] + 1:
                    j += 1
                if j < len(group):
                    out.append((ticker, stage, episode_id, group[i:j]))
                    episode_id += 1
                i = j
            else:
                i += 1
    return out


def entry_atr_steps(stage, rows):
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


def persistence_cap(age):
    if age < 5:
        return 0.25
    if age < 10:
        return 0.50
    if age < 20:
        return 0.75
    return 1.00


def persistence_gentle_return(steps):
    cum = peak = 0.0
    latch = 1.0
    prior_new_extreme = False
    retained = 0.0
    for age, move in enumerate(steps):
        if age == 0 or prior_new_extreme:
            latch = 1.0
        else:
            latch = min(latch, GENTLE[giveback_bucket(max(0.0, peak - cum))])
        retained += min(persistence_cap(age), latch) * move
        new_cum = cum + move
        prior_new_extreme = new_cum > peak + 1e-12
        if prior_new_extreme:
            peak = new_cum
        cum = new_cum
    return retained


def era_name(timestamp_ms):
    when = dt.datetime.fromtimestamp(timestamp_ms / 1000.0, dt.timezone.utc)
    for name, start, end in ERAS:
        if start <= when < end:
            return name
    return ""


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

    events = read_daily(args.daily)
    weekly_rows, weekly_index = read_weekly(args.weekly)
    episodes = reconstruct_episodes(events)
    if len(events) != 68118 or len(episodes) != 1624:
        raise SystemExit(f"sample drift: events={len(events)} episodes={len(episodes)}")

    by_ticker = defaultdict(list)
    for row in events:
        by_ticker[row["ticker"]].append(row)
    stage_map = {ticker: {row["event_bar"]: row["stage"] for row in group} for ticker, group in by_ticker.items()}

    bar_records = []
    for row in events:
        if row["stage"] not in TREND:
            continue
        weekly = asof_weekly(weekly_index, row["ticker"], row["event_time"])
        direction = 1.0 if row["stage"] == 2 else -1.0
        record = {
            "ticker": row["ticker"],
            "stage_name": TREND[row["stage"]],
            "bucket": context_bucket(row["stage"], weekly),
        }
        for horizon in (1, 5, 10, 20):
            record[f"fwd{horizon}"] = direction * row[f"norm{horizon}"]
            record[f"surv{horizon}"] = 1.0 if all(
                stage_map[row["ticker"]].get(row["event_bar"] + k) == row["stage"]
                for k in range(1, horizon + 1)
            ) else 0.0
        bar_records.append(record)

    grouped = defaultdict(list)
    for record in bar_records:
        grouped[(record["ticker"], record["stage_name"], record["bucket"])].append(record)
    market_rows = []
    for (ticker, stage_name, bucket), group in grouped.items():
        row = {"ticker": ticker, "stage_name": stage_name, "bucket": bucket, "n": len(group)}
        for metric in ("fwd1", "fwd5", "fwd10", "fwd20", "surv5", "surv10", "surv20"):
            row[metric] = mean_finite([x[metric] for x in group])
        market_rows.append(row)

    grouped = defaultdict(list)
    for row in market_rows:
        grouped[(row["stage_name"], row["bucket"])].append(row)
    bar_universal = []
    for (stage_name, bucket), group in grouped.items():
        row = {"stage_name": stage_name, "bucket": bucket, "markets": len(group), "n": sum(x["n"] for x in group)}
        for metric in ("fwd1", "fwd5", "fwd10", "fwd20", "surv5", "surv10", "surv20"):
            row[metric] = mean_finite([x[metric] for x in group])
        bar_universal.append(row)

    entry_records = []
    for ticker, stage, _, rows in episodes:
        episode_steps = entry_atr_steps(stage, rows)
        cum = peak = 0.0
        for move in episode_steps:
            cum += move
            peak = max(peak, cum)
        weekly = asof_weekly(weekly_index, ticker, rows[0]["event_time"])
        entry_records.append({
            "ticker": ticker,
            "stage_name": TREND[stage],
            "bucket": context_bucket(stage, weekly),
            "start_time": rows[0]["event_time"],
            "era": era_name(rows[0]["event_time"]),
            "return": persistence_gentle_return(episode_steps),
            "mfe": peak,
            "duration": len(rows),
            "mfe4": 1.0 if peak >= 4.0 else 0.0,
            "mfe8": 1.0 if peak >= 8.0 else 0.0,
        })

    grouped = defaultdict(list)
    for record in entry_records:
        grouped[(record["ticker"], record["stage_name"], record["bucket"])].append(record)
    entry_market = []
    for (ticker, stage_name, bucket), group in grouped.items():
        entry_market.append({
            "ticker": ticker,
            "stage_name": stage_name,
            "bucket": bucket,
            "n": len(group),
            "return": mean_finite([x["return"] for x in group]),
            "mfe": mean_finite([x["mfe"] for x in group]),
            "duration": mean_finite([x["duration"] for x in group]),
            "mfe4": mean_finite([x["mfe4"] for x in group]),
            "mfe8": mean_finite([x["mfe8"] for x in group]),
        })

    grouped = defaultdict(list)
    for row in entry_market:
        grouped[(row["stage_name"], row["bucket"])].append(row)
    entry_universal = []
    for (stage_name, bucket), group in grouped.items():
        entry_universal.append({
            "stage_name": stage_name,
            "bucket": bucket,
            "markets": len(group),
            "n": sum(x["n"] for x in group),
            "return": mean_finite([x["return"] for x in group]),
            "mfe": mean_finite([x["mfe"] for x in group]),
            "duration": mean_finite([x["duration"] for x in group]),
            "mfe4": mean_finite([x["mfe4"] for x in group]),
            "mfe8": mean_finite([x["mfe8"] for x in group]),
        })

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "weekly-conflict-bar-universal.csv", bar_universal)
    write_csv(out / "weekly-conflict-entry-universal.csv", entry_universal)
    write_csv(out / "weekly-conflict-entry-per-market.csv", entry_market)

    print(f"daily={len(events)} weekly={len(weekly_rows)} episodes={len(episodes)}")


if __name__ == "__main__":
    main()
