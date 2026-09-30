#!/usr/bin/env python3
"""Issue #78 progressive exposure-state-machine discovery analysis.

Reuses accepted Issue #76 Pine log exports. This is descriptive discovery research,
not a broker-fill backtest and not OOS validation.
"""
from __future__ import annotations

import argparse
import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path

MARKER = "ISSUE76|schema=1"
TREND_STAGES = {2: "Markup", 5: "Markdown"}
LADDERS = {
    "formal": (1.00, 1.00, 1.00, 1.00, 1.00),
    "gentle": (1.00, 1.00, 0.75, 0.50, 0.25),
    "balanced": (1.00, 0.75, 0.50, 0.25, 0.00),
    "defensive": (1.00, 0.50, 0.25, 0.00, 0.00),
}


def parse_marker(text: str) -> dict[str, str] | None:
    pos = text.find(MARKER)
    if pos < 0:
        return None
    out: dict[str, str] = {}
    for token in text[pos:].strip().split("|"):
        if "=" in token:
            k, v = token.split("=", 1)
            out[k] = v
    return out


def read_events(paths: list[Path]) -> list[dict[str, object]]:
    dedup: dict[tuple[str, int, int], dict[str, object]] = {}
    for path in paths:
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
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
                    "event_time": int(fields["event_time"]),
                    "event_bar": int(fields["event_bar"]),
                    "stage": int(fields["stage"]),
                    "fresh": int(fields["fresh"]),
                    "scale": float(fields["scale"]),
                    "move1": float(fields["move1"]),
                }
                key = (str(rec["ticker"]), int(rec["event_time"]), int(rec["event_bar"]))
                dedup[key] = rec
    return sorted(dedup.values(), key=lambda r: (str(r["ticker"]), int(r["event_bar"])))


def reconstruct_completed_episodes(events: list[dict[str, object]]):
    by_ticker: dict[str, list[dict[str, object]]] = defaultdict(list)
    for event in events:
        by_ticker[str(event["ticker"])].append(event)
    out = []
    for ticker, group in by_ticker.items():
        group.sort(key=lambda r: int(r["event_bar"]))
        i = 0
        episode_id = 0
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
                # Final spell is right-censored; do not pretend it ended.
                if j < len(group):
                    out.append((ticker, stage, episode_id, group[i:j]))
                    episode_id += 1
                i = j
            else:
                i += 1
    return out


def bucket(giveback: float) -> int:
    if giveback < 0.5:
        return 0
    if giveback < 1.0:
        return 1
    if giveback < 2.0:
        return 2
    if giveback < 4.0:
        return 3
    return 4


def entry_atr_steps(stage: int, rows: list[dict[str, object]]) -> list[float]:
    scale = float(rows[0]["scale"])
    denom = scale * (100.0 if rows[0]["repr"] == "YIELD_LEVEL" else 1.0)
    direction = 1.0 if stage == 2 else -1.0
    return [float(r["move1"]) / denom * direction for r in rows]


def memoryless_exposure(steps: list[float], mapping: tuple[float, ...]) -> list[float]:
    cum = 0.0
    peak = 0.0
    out: list[float] = []
    for step in steps:
        out.append(mapping[bucket(max(0.0, peak - cum))])
        cum += step
        peak = max(peak, cum)
    return out


def damage_latch_exposure(steps: list[float], mapping: tuple[float, ...]) -> list[float]:
    """De-risk on worsening; restore Full only after a new favorable close extreme."""
    cum = 0.0
    peak = 0.0
    exposure = 1.0
    new_extreme = False
    out: list[float] = []
    for index, step in enumerate(steps):
        if index == 0:
            exposure = 1.0
        elif new_extreme:
            exposure = 1.0
        else:
            target = mapping[bucket(max(0.0, peak - cum))]
            if target < exposure:
                exposure = target
        out.append(exposure)
        new_cum = cum + step
        new_extreme = new_cum > peak + 1e-12
        if new_extreme:
            peak = new_cum
        cum = new_cum
    return out


def simulate(episode):
    ticker, stage, episode_id, rows = episode
    steps = entry_atr_steps(stage, rows)
    cumulative = [0.0]
    running = 0.0
    for step in steps:
        running += step
        cumulative.append(running)
    mfe = max(cumulative)

    exposures = {name: memoryless_exposure(steps, mapping) for name, mapping in LADDERS.items()}
    exposures["gentle_latch"] = damage_latch_exposure(steps, LADDERS["gentle"])
    exposures["balanced_latch"] = damage_latch_exposure(steps, LADDERS["balanced"])

    out = []
    for name, exp in exposures.items():
        psteps = [e * r for e, r in zip(exp, steps)]
        equity = [0.0]
        running = 0.0
        for value in psteps:
            running += value
            equity.append(running)
        changes = [exp[0]] + [exp[i] - exp[i - 1] for i in range(1, len(exp))] + [-exp[-1]]
        out.append({
            "ticker": ticker,
            "stage_name": TREND_STAGES[stage],
            "episode_id": episode_id,
            "bars": len(steps),
            "mfe": mfe,
            "policy": name,
            "harvest": equity[-1],
            "capture_ratio": equity[-1] / mfe if mfe > 0 else math.nan,
            "terminal_giveback": max(equity) - equity[-1],
            "avg_exposure": statistics.fmean(exp),
            "underexposed_frac": statistics.fmean(1.0 if e < 1.0 else 0.0 for e in exp),
            "turnover": sum(abs(x) for x in changes),
            "derisk_count": sum(1 for x in changes[1:-1] if x < 0),
            "rerisk_count": sum(1 for x in changes[1:-1] if x > 0),
        })
    return out


def median(values):
    vals = [x for x in values if math.isfinite(x)]
    return statistics.median(vals) if vals else math.nan


def mean(values):
    vals = [x for x in values if math.isfinite(x)]
    return statistics.fmean(vals) if vals else math.nan


def summarize(records: list[dict[str, object]], slice_name: str, predicate):
    selected = [r for r in records if predicate(float(r["mfe"]))]
    market_groups: dict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in selected:
        market_groups[(str(row["stage_name"]), str(row["policy"]), str(row["ticker"]))].append(row)

    market_rows = []
    for (stage, policy, ticker), group in market_groups.items():
        market_rows.append({
            "stage_name": stage,
            "policy": policy,
            "ticker": ticker,
            "n": len(group),
            "median_harvest": median([float(r["harvest"]) for r in group]),
            "mean_harvest": mean([float(r["harvest"]) for r in group]),
            "median_capture": median([float(r["capture_ratio"]) for r in group]),
            "median_terminal_giveback": median([float(r["terminal_giveback"]) for r in group]),
            "median_avg_exposure": median([float(r["avg_exposure"]) for r in group]),
            "mean_turnover": mean([float(r["turnover"]) for r in group]),
            "mean_rerisk": mean([float(r["rerisk_count"]) for r in group]),
            "mean_derisk": mean([float(r["derisk_count"]) for r in group]),
        })

    universal_groups: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in market_rows:
        universal_groups[(str(row["stage_name"]), str(row["policy"]))].append(row)

    universal = []
    for (stage, policy), group in universal_groups.items():
        universal.append({
            "slice": slice_name,
            "stage_name": stage,
            "policy": policy,
            "markets": len(group),
            "n": sum(int(r["n"]) for r in group),
            "eqm_median_harvest": mean([float(r["median_harvest"]) for r in group]),
            "eqm_mean_harvest": mean([float(r["mean_harvest"]) for r in group]),
            "eqm_median_capture": mean([float(r["median_capture"]) for r in group]),
            "eqm_median_terminal_giveback": mean([float(r["median_terminal_giveback"]) for r in group]),
            "eqm_median_avg_exposure": mean([float(r["median_avg_exposure"]) for r in group]),
            "eqm_mean_turnover": mean([float(r["mean_turnover"]) for r in group]),
            "eqm_mean_rerisk": mean([float(r["mean_rerisk"]) for r in group]),
            "eqm_mean_derisk": mean([float(r["mean_derisk"]) for r in group]),
        })
    return universal


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("logs", nargs="+", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    events = read_events(args.logs)
    episodes = reconstruct_completed_episodes(events)
    records = [row for episode in episodes for row in simulate(episode)]

    rows = []
    rows += summarize(records, "all", lambda x: True)
    rows += summarize(records, "mfe_lt_4", lambda x: x < 4.0)
    rows += summarize(records, "mfe_ge_4", lambda x: x >= 4.0)
    rows += summarize(records, "mfe_ge_8", lambda x: x >= 8.0)
    write_csv(args.output, rows)

    counts = defaultdict(int)
    for _, stage, _, _ in episodes:
        counts[TREND_STAGES[stage]] += 1
    print(f"events={len(events)} episodes={dict(counts)} output={args.output}")


if __name__ == "__main__":
    main()
