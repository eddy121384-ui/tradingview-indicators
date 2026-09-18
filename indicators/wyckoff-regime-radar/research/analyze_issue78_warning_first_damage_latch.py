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
ADD_POLICIES = ("simple_1atr", "progressive")
MANAGEMENT = ("none", "gentle_latch", "balanced_latch", "warning_first")
EXPECTED_EVENTS = 68118
EXPECTED_EPISODES = 1624
METRICS = (
    "harvest",
    "avg_exposure",
    "below_earned_frac",
    "turnover",
    "de_risk_count",
    "re_risk_count",
    "max_reduction",
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

def earned_cap(add_policy, peak):
    if add_policy == "simple_1atr":
        return 1.0 if peak >= 1.0 else 0.25
    if peak >= 2.0:
        return 1.0
    if peak >= 1.0:
        return 0.75
    if peak >= 0.5:
        return 0.50
    return 0.25

def gentle_target(giveback):
    if giveback < 1.0:
        return 1.0
    if giveback < 2.0:
        return 0.75
    if giveback < 4.0:
        return 0.50
    return 0.25

def balanced_target(giveback):
    if giveback < 0.5:
        return 1.0
    if giveback < 1.0:
        return 0.75
    if giveback < 2.0:
        return 0.50
    if giveback < 4.0:
        return 0.25
    return 0.0

def simulate(ep, add_policy, management):
    ticker, stage, episode_id, rows = ep
    steps = aligned_steps(ep)
    cum = 0.0
    peak = 0.0
    damage_cap = 1.0
    reduction_steps = 0
    previous_exposure = 0.0
    turnover = 0.0
    harvest = 0.0
    exposures = []
    earned_caps = []
    de_risk_count = 0
    re_risk_count = 0
    max_reduction = 0.0

    for step in steps:
        ecap = earned_cap(add_policy, peak)
        giveback = peak - cum

        if management == "none":
            actual = ecap
        elif management in ("gentle_latch", "balanced_latch"):
            target = gentle_target(giveback) if management == "gentle_latch" else balanced_target(giveback)
            if target < damage_cap - 1e-12:
                damage_cap = target
                de_risk_count += 1
            actual = min(ecap, damage_cap)
        elif management == "warning_first":
            target_steps = 2 if giveback >= 4.0 else (1 if giveback >= 2.0 else 0)
            if target_steps > reduction_steps:
                reduction_steps = target_steps
                de_risk_count += 1
            actual = max(0.25, ecap - 0.25 * reduction_steps)
        else:
            raise ValueError(management)

        turnover += abs(actual - previous_exposure)
        previous_exposure = actual
        exposures.append(actual)
        earned_caps.append(ecap)
        max_reduction = max(max_reduction, ecap - actual)
        harvest += actual * step

        cum += step
        if cum > peak + 1e-12:
            peak = cum
            if management in ("gentle_latch", "balanced_latch") and damage_cap < 1.0 - 1e-12:
                damage_cap = 1.0
                re_risk_count += 1
            elif management == "warning_first" and reduction_steps > 0:
                reduction_steps = 0
                re_risk_count += 1

    turnover += abs(previous_exposure)
    mfe = peak
    slice_name = "failed" if mfe < 4.0 else ("large" if mfe >= 8.0 else "middle")

    return {
        "ticker": ticker,
        "stage": TREND[stage],
        "episode_id": episode_id,
        "era": era_name(rows[0]["event_time"]),
        "slice": slice_name,
        "add_policy": add_policy,
        "management": management,
        "mfe": mfe,
        "harvest": harvest,
        "avg_exposure": mean(exposures),
        "below_earned_frac": mean([1.0 if a < e - 1e-12 else 0.0 for a, e in zip(exposures, earned_caps)]),
        "turnover": turnover,
        "de_risk_count": float(de_risk_count),
        "re_risk_count": float(re_risk_count),
        "max_reduction": max_reduction,
    }

def summarize(records, group_fields):
    market_groups = defaultdict(list)
    for r in records:
        market_groups[tuple(r[f] for f in group_fields) + (r["ticker"],)].append(r)

    market_rows = []
    for key, group in market_groups.items():
        row = {f: v for f, v in zip(group_fields, key[:-1])}
        row["ticker"] = key[-1]
        row["n"] = len(group)
        for metric in METRICS:
            row[metric] = mean([r[metric] for r in group])
        market_rows.append(row)

    universal_groups = defaultdict(list)
    for r in market_rows:
        universal_groups[tuple(r[f] for f in group_fields)].append(r)

    universal_rows = []
    for key, group in universal_groups.items():
        row = {f: v for f, v in zip(group_fields, key)}
        row["markets"] = len(group)
        row["pooled_n"] = sum(r["n"] for r in group)
        for metric in METRICS:
            row[f"{metric}_eq_market_mean"] = mean([r[metric] for r in group])
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
    parser.add_argument("--out", default="/mnt/data/issue78-warning-first-damage-latch")
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

    records = []
    for ep in eps:
        for add_policy in ADD_POLICIES:
            for management in MANAGEMENT:
                records.append(simulate(ep, add_policy, management))

    market_slice, slices = summarize(records, ("slice", "add_policy", "management"))
    _, universal = summarize(records, ("add_policy", "management"))
    _, temporal = summarize(records, ("era", "add_policy", "management"))
    _, direction = summarize(records, ("stage", "add_policy", "management"))

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "issue78-warning-first-per-market.csv", market_slice)
    write_csv(out / "issue78-warning-first-slices.csv", slices)
    write_csv(out / "issue78-warning-first-universal.csv", universal)
    write_csv(out / "issue78-warning-first-temporal.csv", temporal)
    write_csv(out / "issue78-warning-first-direction.csv", direction)

    print("events", len(events), "episodes", len(eps), "records", len(records))
    print("wrote", out)

if __name__ == "__main__":
    main()
