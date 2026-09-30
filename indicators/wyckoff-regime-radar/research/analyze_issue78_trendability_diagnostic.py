#!/usr/bin/env python3
"""Issue #78 Trendability / Oscillation diagnostic.

Consumes:
  1) accepted Issue #76 forward-behavior Pine-log CSVs;
  2) new ISSUE78TREND fresh-entry Pine-log CSVs from the preregistered visualizer.

Produces equal-market diagnostics for era and entry-time trendability buckets.
This is discovery analysis only; it does not tune the classifier or exposure rules.
"""
from __future__ import annotations

import argparse
import csv
import math
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ISSUE76_MARKER = "ISSUE76|schema=1"
TREND_MARKER = "ISSUE78TREND|schema=1"
TREND_STAGES = {2: "Markup", 5: "Markdown"}
GENTLE = (1.00, 1.00, 0.75, 0.50, 0.25)


def parse_marker(text: str, marker: str) -> dict[str, str] | None:
    pos = text.find(marker)
    if pos < 0:
        return None
    out: dict[str, str] = {}
    for token in text[pos:].strip().split("|"):
        if "=" in token:
            key, value = token.split("=", 1)
            out[key] = value
    return out


def iter_csv_markers(path: Path, marker: str):
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        for row in csv.reader(fh):
            for cell in row:
                fields = parse_marker(cell, marker)
                if fields:
                    yield fields
                    break


def read_issue76(paths: list[Path]) -> list[dict[str, object]]:
    dedup: dict[tuple[str, int, int], dict[str, object]] = {}
    for path in paths:
        for f in iter_csv_markers(path, ISSUE76_MARKER):
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
            dedup[(str(rec["ticker"]), int(rec["event_time"]), int(rec["event_bar"]))] = rec
    return sorted(dedup.values(), key=lambda r: (str(r["ticker"]), int(r["event_bar"])))


def read_trendability(paths: list[Path]) -> dict[tuple[str, int, int], dict[str, float]]:
    out: dict[tuple[str, int, int], dict[str, float]] = {}
    for path in paths:
        for f in iter_csv_markers(path, TREND_MARKER):
            key = (f["ticker"], int(f["event_time"]), int(f["stage"]))
            out[key] = {
                "er63": float(f["er63"]),
                "er126": float(f["er126"]),
                "er252": float(f["er252"]),
                "er63r": float(f["er63r"]),
                "er126r": float(f["er126r"]),
                "er252r": float(f["er252r"]),
                "trendability": float(f["trendability"]),
            }
    return out


def reconstruct_completed_episodes(events: list[dict[str, object]]):
    by_ticker: dict[str, list[dict[str, object]]] = defaultdict(list)
    for event in events:
        by_ticker[str(event["ticker"])].append(event)
    episodes = []
    for ticker, group in by_ticker.items():
        group.sort(key=lambda r: int(r["event_bar"]))
        i = 0
        eid = 0
        while i < len(group):
            row = group[i]
            stage = int(row["stage"])
            if stage in TREND_STAGES and int(row["fresh"]) == 1:
                j = i + 1
                while (
                    j < len(group)
                    and int(group[j]["stage"]) == stage
                    and int(group[j]["event_bar"]) == int(group[j - 1]["event_bar"]) + 1
                ):
                    j += 1
                if j < len(group):  # exclude right-censored terminal spell
                    episodes.append((ticker, stage, eid, group[i:j]))
                    eid += 1
                i = j
            else:
                i += 1
    return episodes


def entry_atr_steps(stage: int, rows: list[dict[str, object]]) -> list[float]:
    scale = float(rows[0]["scale"])
    denom = scale * (100.0 if rows[0]["repr"] == "YIELD_LEVEL" else 1.0)
    direction = 1.0 if stage == 2 else -1.0
    return [float(r["move1"]) / denom * direction for r in rows]


def bucket_giveback(value: float) -> int:
    if value < 0.5:
        return 0
    if value < 1.0:
        return 1
    if value < 2.0:
        return 2
    if value < 4.0:
        return 3
    return 4


def persistence_cap(age: int) -> float:
    if age < 5:
        return 0.25
    if age < 10:
        return 0.50
    if age < 20:
        return 0.75
    return 1.00


def gentle_latch(steps: list[float]) -> list[float]:
    cum = 0.0
    peak = 0.0
    exposure = 1.0
    prior_step_new_extreme = False
    out: list[float] = []
    for i, step in enumerate(steps):
        if i == 0:
            exposure = 1.0
        elif prior_step_new_extreme:
            exposure = 1.0
        else:
            target = GENTLE[bucket_giveback(max(0.0, peak - cum))]
            if target < exposure:
                exposure = target
        out.append(exposure)
        new_cum = cum + step
        prior_step_new_extreme = new_cum > peak + 1e-12
        if prior_step_new_extreme:
            peak = new_cum
        cum = new_cum
    return out


def era_for(ms: int) -> str:
    year = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).year
    if 2010 <= year <= 2014:
        return "2010-2014"
    if 2015 <= year <= 2019:
        return "2015-2019"
    if 2020 <= year <= 2026:
        return "2020-2026"
    return "other"


def trend_bucket(score: float) -> str:
    if score < 33.33:
        return "Low"
    if score <= 66.67:
        return "Neutral"
    return "High"


def simulate_joined(episode, trow: dict[str, float]) -> dict[str, object]:
    ticker, stage, eid, rows = episode
    steps = entry_atr_steps(stage, rows)
    cum = 0.0
    peak = 0.0
    for step in steps:
        cum += step
        peak = max(peak, cum)
    latch = gentle_latch(steps)
    pexp = [persistence_cap(i) for i in range(len(steps))]
    pg_exp = [min(a, b) for a, b in zip(pexp, latch)]
    formal_ret = sum(steps)
    pg_ret = sum(e * step for e, step in zip(pg_exp, steps))
    entry_time = int(rows[0]["event_time"])
    return {
        "ticker": ticker,
        "stage": TREND_STAGES[stage],
        "stage_id": stage,
        "episode_id": eid,
        "entry_time": entry_time,
        "era": era_for(entry_time),
        "bars": len(steps),
        "mfe": peak,
        "formal_return": formal_ret,
        "persistence_gentle_return": pg_ret,
        **trow,
        "trend_bucket": trend_bucket(float(trow["trendability"])),
    }


def mean(values):
    vals = [float(v) for v in values if math.isfinite(float(v))]
    return statistics.fmean(vals) if vals else math.nan


def median(values):
    vals = [float(v) for v in values if math.isfinite(float(v))]
    return statistics.median(vals) if vals else math.nan


def summarize_group(group: list[dict[str, object]]) -> dict[str, float]:
    n = len(group)
    return {
        "n": n,
        "median_trendability": median([r["trendability"] for r in group]),
        "median_er63": median([r["er63"] for r in group]),
        "median_er126": median([r["er126"] for r in group]),
        "median_er252": median([r["er252"] for r in group]),
        "median_bars": median([r["bars"] for r in group]),
        "median_mfe": median([r["mfe"] for r in group]),
        "share_mfe_ge4": mean([1.0 if float(r["mfe"]) >= 4.0 else 0.0 for r in group]),
        "share_mfe_ge8": mean([1.0 if float(r["mfe"]) >= 8.0 else 0.0 for r in group]),
        "mean_formal_return": mean([r["formal_return"] for r in group]),
        "mean_persistence_gentle_return": mean([r["persistence_gentle_return"] for r in group]),
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise SystemExit(f"no rows for {path}")
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--issue76", type=Path, nargs="+", required=True)
    ap.add_argument("--trendability", type=Path, nargs="+", required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()

    events = read_issue76(args.issue76)
    entries = read_trendability(args.trendability)
    eps = reconstruct_completed_episodes(events)

    joined = []
    missing = []
    for ep in eps:
        ticker, stage, _, rows = ep
        key = (ticker, int(rows[0]["event_time"]), stage)
        trow = entries.get(key)
        if trow is None:
            missing.append(key)
            continue
        joined.append(simulate_joined(ep, trow))

    if not joined:
        raise SystemExit("no joined episodes; check ticker/event_time/stage alignment")

    eligible_eps = [ep for ep in eps if era_for(int(ep[3][0]["event_time"])) != "other"]
    coverage = len(joined) / len(eligible_eps) if eligible_eps else 0.0
    if coverage < 0.80:
        raise SystemExit(f"join coverage too low: {len(joined)}/{len(eligible_eps)} = {coverage:.1%}")

    out = args.output_dir
    write_csv(out / "issue78-trendability-joined-episodes.csv", joined)

    per_market_rows = []
    groups: dict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in joined:
        groups[(str(row["ticker"]), str(row["era"]), str(row["trend_bucket"]))].append(row)
    for (ticker, era, bucket), group in sorted(groups.items()):
        per_market_rows.append({"ticker": ticker, "era": era, "trend_bucket": bucket, **summarize_group(group)})
    write_csv(out / "issue78-trendability-per-market.csv", per_market_rows)

    universal_rows = []
    for era in ["2010-2014", "2015-2019", "2020-2026"]:
        for bucket in ["Low", "Neutral", "High"]:
            market_summaries = [r for r in per_market_rows if r["era"] == era and r["trend_bucket"] == bucket]
            if not market_summaries:
                continue
            universal_rows.append({
                "era": era,
                "trend_bucket": bucket,
                "markets": len(market_summaries),
                "episodes": sum(int(r["n"]) for r in market_summaries),
                "eq_market_median_trendability": mean([r["median_trendability"] for r in market_summaries]),
                "eq_market_median_bars": mean([r["median_bars"] for r in market_summaries]),
                "eq_market_median_mfe": mean([r["median_mfe"] for r in market_summaries]),
                "eq_market_share_mfe_ge4": mean([r["share_mfe_ge4"] for r in market_summaries]),
                "eq_market_share_mfe_ge8": mean([r["share_mfe_ge8"] for r in market_summaries]),
                "eq_market_mean_formal_return": mean([r["mean_formal_return"] for r in market_summaries]),
                "eq_market_mean_persistence_gentle_return": mean([r["mean_persistence_gentle_return"] for r in market_summaries]),
            })
    write_csv(out / "issue78-trendability-universal.csv", universal_rows)

    era_rows = []
    for era in ["2010-2014", "2015-2019", "2020-2026"]:
        market_groups: dict[str, list[dict[str, object]]] = defaultdict(list)
        for row in joined:
            if row["era"] == era:
                market_groups[str(row["ticker"])].append(row)
        if not market_groups:
            continue
        era_rows.append({
            "era": era,
            "markets": len(market_groups),
            "episodes": sum(len(g) for g in market_groups.values()),
            "eq_market_median_trendability": mean([median([r["trendability"] for r in g]) for g in market_groups.values()]),
            "eq_market_low_share": mean([mean([1.0 if r["trend_bucket"] == "Low" else 0.0 for r in g]) for g in market_groups.values()]),
            "eq_market_neutral_share": mean([mean([1.0 if r["trend_bucket"] == "Neutral" else 0.0 for r in g]) for g in market_groups.values()]),
            "eq_market_high_share": mean([mean([1.0 if r["trend_bucket"] == "High" else 0.0 for r in g]) for g in market_groups.values()]),
        })
    write_csv(out / "issue78-trendability-era-summary.csv", era_rows)

    print(f"issue76_events={len(events)} completed_episodes={len(eps)} trend_entries={len(entries)} joined={len(joined)} coverage={coverage:.1%}")
    print(out)


if __name__ == "__main__":
    main()
