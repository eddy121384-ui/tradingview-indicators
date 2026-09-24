#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import glob
import math
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

MARKER = "ISSUE76|schema=1"
TREND = {2: "Markup", 5: "Markdown"}
ERAS = (("2010-2014", 2010, 2014), ("2015-2019", 2015, 2019), ("2020-2026", 2020, 2026))
GIVEBACKS = (0.5, 1.0, 2.0, 4.0)
STALLS = (5, 10, 20)
EXPECTED_EVENTS = 68118
EXPECTED_EPISODES = 1624
EXPECTED_ELIGIBLE = 1031

METRICS = (
    "recovery",
    "end_before_recovery",
    "bars_to_recovery",
    "future_mfe",
    "future_mae",
    "future_net",
    "remaining_bars",
    "plus1",
    "plus2",
    "time_from_proof",
)

def parse_marker(text):
    p = text.find(MARKER)
    if p < 0:
        return None
    out = {}
    for tok in text[p:].strip().split("|"):
        if "=" in tok:
            k, v = tok.split("=", 1)
            out[k] = v
    return out

def read_events(paths):
    dedup = {}
    for path in paths:
        with Path(path).open(encoding="utf-8-sig", newline="") as fh:
            for row in csv.reader(fh):
                f = None
                for cell in row:
                    f = parse_marker(cell)
                    if f:
                        break
                if not f:
                    continue
                rec = {
                    "ticker": f["ticker"],
                    "repr": f["repr"],
                    "event_time": int(f["event_time"]),
                    "event_bar": int(f["event_bar"]),
                    "stage": int(f["stage"]),
                    "fresh": int(f["fresh"]),
                    "scale": float(f["scale"]),
                    "move1": float(f["move1"]),
                }
                dedup[(rec["ticker"], rec["event_time"], rec["event_bar"])] = rec
    return sorted(dedup.values(), key=lambda r: (r["ticker"], r["event_bar"]))

def episodes(events):
    by = defaultdict(list)
    for e in events:
        by[e["ticker"]].append(e)
    out = []
    for ticker, group in by.items():
        group.sort(key=lambda r: r["event_bar"])
        i = 0
        episode_id = 0
        while i < len(group):
            row = group[i]
            stage = row["stage"]
            if stage in TREND and row["fresh"] == 1:
                j = i + 1
                while (
                    j < len(group)
                    and group[j]["stage"] == stage
                    and group[j]["event_bar"] == group[j - 1]["event_bar"] + 1
                ):
                    j += 1
                if j < len(group):
                    out.append((ticker, stage, episode_id, group[i:j]))
                    episode_id += 1
                i = j
            else:
                i += 1
    return out

def aligned_steps(ep):
    ticker, stage, episode_id, rows = ep
    direction = 1.0 if stage == 2 else -1.0
    denom = rows[0]["scale"] * (100.0 if rows[0]["repr"] == "YIELD_LEVEL" else 1.0)
    return [direction * r["move1"] / denom for r in rows]

def era_name(ms):
    year = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).year
    for name, start, end in ERAS:
        if start <= year <= end:
            return name
    return "other"

def finite(values):
    return [v for v in values if isinstance(v, (int, float)) and math.isfinite(v)]

def mean(values):
    vals = finite(values)
    return statistics.fmean(vals) if vals else math.nan

def median(values):
    vals = finite(values)
    return statistics.median(vals) if vals else math.nan

def forward_outcomes(cums, event_idx, pre_event_peak):
    current = cums[event_idx]
    future = cums[event_idx + 1:]
    if not future:
        return {
            "recovery": 0.0,
            "bars_to_recovery": math.nan,
            "end_before_recovery": 1.0,
            "future_mfe": 0.0,
            "future_mae": 0.0,
            "future_net": 0.0,
            "remaining_bars": 0.0,
            "plus1": 0.0,
            "plus2": 0.0,
        }
    rel = [x - current for x in future]
    recovery_idx = None
    for i, x in enumerate(future, start=1):
        if x > pre_event_peak + 1e-12:
            recovery_idx = i
            break
    return {
        "recovery": 1.0 if recovery_idx is not None else 0.0,
        "bars_to_recovery": recovery_idx if recovery_idx is not None else math.nan,
        "end_before_recovery": 0.0 if recovery_idx is not None else 1.0,
        "future_mfe": max([0.0] + rel),
        "future_mae": -min([0.0] + rel),
        "future_net": rel[-1],
        "remaining_bars": float(len(rel)),
        "plus1": 1.0 if max([0.0] + rel) >= 1.0 else 0.0,
        "plus2": 1.0 if max([0.0] + rel) >= 2.0 else 0.0,
    }

def build_records(eps):
    records = []
    eligible_by_ticker = defaultdict(int)

    for ep in eps:
        ticker, stage, episode_id, rows = ep
        steps = aligned_steps(ep)
        cums = [0.0]
        x = 0.0
        for step in steps:
            x += step
            cums.append(x)

        proof_idx = next((i for i in range(1, len(cums)) if cums[i] >= 1.0), None)
        if proof_idx is None or proof_idx >= len(cums) - 1:
            continue

        eligible_by_ticker[ticker] += 1

        peaks = [0.0] * len(cums)
        stalls = [0] * len(cums)
        peak = 0.0
        last_high_idx = 0
        for i in range(1, len(cums)):
            if cums[i] > peak + 1e-12:
                peak = cums[i]
                last_high_idx = i
            peaks[i] = peak
            stalls[i] = i - last_high_idx

        for threshold in GIVEBACKS:
            idx = next(
                (
                    i
                    for i in range(proof_idx + 1, len(cums))
                    if peaks[i] - cums[i] >= threshold
                ),
                None,
            )
            if idx is not None:
                rec = {
                    "ticker": ticker,
                    "stage": TREND[stage],
                    "episode_id": episode_id,
                    "era": era_name(rows[0]["event_time"]),
                    "family": "giveback",
                    "threshold": threshold,
                    "time_from_proof": idx - proof_idx,
                }
                rec.update(forward_outcomes(cums, idx, peaks[idx]))
                records.append(rec)

        for threshold in STALLS:
            idx = next(
                (
                    i
                    for i in range(proof_idx + 1, len(cums))
                    if stalls[i] >= threshold
                ),
                None,
            )
            if idx is not None:
                rec = {
                    "ticker": ticker,
                    "stage": TREND[stage],
                    "episode_id": episode_id,
                    "era": era_name(rows[0]["event_time"]),
                    "family": "stall",
                    "threshold": threshold,
                    "time_from_proof": idx - proof_idx,
                }
                rec.update(forward_outcomes(cums, idx, peaks[idx]))
                records.append(rec)

    return records, eligible_by_ticker

def summarize(records, eligible_by_ticker, group_fields, include_event_rate=False):
    market_groups = defaultdict(list)
    for r in records:
        market_groups[tuple(r[f] for f in group_fields) + (r["ticker"],)].append(r)

    market_rows = []
    for key, group in market_groups.items():
        row = {f: v for f, v in zip(group_fields, key[:-1])}
        ticker = key[-1]
        row["ticker"] = ticker
        row["n_events"] = len(group)
        if include_event_rate:
            row["eligible_episodes"] = eligible_by_ticker[ticker]
            row["event_rate"] = len(group) / eligible_by_ticker[ticker]
        for metric in METRICS:
            row[f"{metric}_mean"] = mean([r[metric] for r in group])
            row[f"{metric}_median"] = median([r[metric] for r in group])
        market_rows.append(row)

    universal_groups = defaultdict(list)
    for r in market_rows:
        universal_groups[tuple(r[f] for f in group_fields)].append(r)

    universal_rows = []
    for key, group in universal_groups.items():
        row = {f: v for f, v in zip(group_fields, key)}
        row["markets"] = len(group)
        row["pooled_n"] = sum(r["n_events"] for r in group)
        if include_event_rate:
            row["event_rate_eq_market_mean"] = mean([r["event_rate"] for r in group])
        for metric in METRICS:
            row[f"{metric}_eq_market_mean"] = mean([r[f"{metric}_mean"] for r in group])
            row[f"{metric}_eq_market_median"] = median([r[f"{metric}_median"] for r in group])
        universal_rows.append(row)
    return market_rows, universal_rows

def write_csv(path, rows):
    if not rows:
        return
    with Path(path).open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*")
    parser.add_argument("--out", default="/mnt/data/issue78-post-proof-deterioration")
    args = parser.parse_args()

    paths = args.paths or sorted(glob.glob("/mnt/data/pine-logs-#76 Forward Logger*.csv"))
    if not paths:
        raise SystemExit("no Issue #76 Forward Logger CSVs found")

    events = read_events(paths)
    eps = episodes(events)
    if len(events) != EXPECTED_EVENTS:
        raise AssertionError(f"event count drift: expected {EXPECTED_EVENTS}, got {len(events)}")
    if len(eps) != EXPECTED_EPISODES:
        raise AssertionError(f"episode count drift: expected {EXPECTED_EPISODES}, got {len(eps)}")

    records, eligible_by_ticker = build_records(eps)
    eligible = sum(eligible_by_ticker.values())
    if eligible != EXPECTED_ELIGIBLE:
        raise AssertionError(f"eligible post-proof episode drift: expected {EXPECTED_ELIGIBLE}, got {eligible}")

    per_market, universal = summarize(
        records, eligible_by_ticker, ("family", "threshold"), include_event_rate=True
    )
    _, temporal = summarize(records, eligible_by_ticker, ("era", "family", "threshold"))
    _, direction = summarize(records, eligible_by_ticker, ("stage", "family", "threshold"))

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "issue78-post-proof-deterioration-per-market.csv", per_market)
    write_csv(out / "issue78-post-proof-deterioration-universal.csv", universal)
    write_csv(out / "issue78-post-proof-deterioration-temporal.csv", temporal)
    write_csv(out / "issue78-post-proof-deterioration-direction.csv", direction)

    print("events", len(events), "episodes", len(eps), "eligible_post_proof", eligible)
    for family, thresholds in (("giveback", GIVEBACKS), ("stall", STALLS)):
        for threshold in thresholds:
            group = [r for r in universal if r["family"] == family and float(r["threshold"]) == float(threshold)]
            if group:
                r = group[0]
                print(
                    family,
                    threshold,
                    "event_rate",
                    r.get("event_rate_eq_market_mean"),
                    "recovery",
                    r["recovery_eq_market_mean"],
                    "time_from_proof",
                    r["time_from_proof_eq_market_mean"],
                )
    print("wrote", out)

if __name__ == "__main__":
    main()
