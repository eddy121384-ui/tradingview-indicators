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
CHECKPOINTS = (5, 10)
ERAS = (("2010-2014", 2010, 2014), ("2015-2019", 2015, 2019), ("2020-2026", 2020, 2026))
EXPECTED_EVENTS = 68118
EXPECTED_EPISODES = 1624

OUTCOMES = (
    "future_net_atr",
    "future_mfe_atr",
    "future_mae_atr",
    "future_plus2",
    "future_plus4",
    "remaining_bars",
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
                # Exclude right-censored terminal spell, matching prior Issue #78 studies.
                if j < len(group):
                    out.append((ticker, stage, episode_id, group[i:j]))
                    episode_id += 1
                i = j
            else:
                i += 1
    return out


def entry_atr_denom(row):
    return row["scale"] * (100.0 if row["repr"] == "YIELD_LEVEL" else 1.0)


def aligned_steps(stage, rows):
    direction = 1.0 if stage == 2 else -1.0
    den = entry_atr_denom(rows[0])
    return [direction * r["move1"] / den for r in rows]


def era_name(ms):
    year = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).year
    for name, start, end in ERAS:
        if start <= year <= end:
            return name
    return "other"


def checkpoint_record(ep, k):
    ticker, stage, episode_id, rows = ep
    steps = aligned_steps(stage, rows)

    # Need at least one post-checkpoint move: len == k means the formal trend has
    # ended by the checkpoint and contributes no live continuation decision.
    if len(steps) <= k:
        return None

    observed = steps[:k]
    future = steps[k:]

    cum = sum(observed)
    path = sum(abs(x) for x in observed)
    eff = cum / path if path > 0 else math.nan

    x = 0.0
    hi = 0.0
    lo = 0.0
    for step in future:
        x += step
        hi = max(hi, x)
        lo = min(lo, x)

    return {
        "ticker": ticker,
        "stage": TREND[stage],
        "episode_id": episode_id,
        "entry_time": rows[0]["event_time"],
        "era": era_name(rows[0]["event_time"]),
        "checkpoint": k,
        "bars_total": len(steps),
        "cum_atr": cum,
        "dir_eff": eff,
        "future_net_atr": sum(future),
        "future_mfe_atr": hi,
        "future_mae_atr": -lo,
        "future_plus2": 1.0 if hi >= 2.0 else 0.0,
        "future_plus4": 1.0 if hi >= 4.0 else 0.0,
        "remaining_bars": len(future),
    }


def percentile_ranks(values):
    n = len(values)
    if n == 1:
        return [0.5]
    order = sorted(range(n), key=lambda i: values[i])
    out = [0.0] * n
    i = 0
    while i < n:
        j = i + 1
        while j < n and values[order[j]] == values[order[i]]:
            j += 1
        avg = (i + j - 1) / 2.0
        pct = avg / (n - 1)
        for p in range(i, j):
            out[order[p]] = pct
        i = j
    return out


def q5(rank):
    return min(5, int(math.floor(rank * 5.0)) + 1)


def add_within_market_ranks(records):
    groups = defaultdict(list)
    for idx, r in enumerate(records):
        if math.isfinite(r["cum_atr"]) and math.isfinite(r["dir_eff"]):
            groups[(r["ticker"], r["checkpoint"])].append(idx)

    for idxs in groups.values():
        progress_ranks = percentile_ranks([records[i]["cum_atr"] for i in idxs])
        efficiency_ranks = percentile_ranks([records[i]["dir_eff"] for i in idxs])
        for i, pr, er in zip(idxs, progress_ranks, efficiency_ranks):
            records[i]["progress_rank"] = pr
            records[i]["eff_rank"] = er
            records[i]["progress_q"] = q5(pr)
            records[i]["eff_q"] = q5(er)
    return records


def finite(xs):
    return [x for x in xs if isinstance(x, (int, float)) and math.isfinite(x)]


def mean(xs):
    xs = finite(xs)
    return statistics.fmean(xs) if xs else math.nan


def median(xs):
    xs = finite(xs)
    return statistics.median(xs) if xs else math.nan


def scopes(records):
    yield "all", records
    for era, _, _ in ERAS:
        yield era, [r for r in records if r["era"] == era]


def summarize_cells(records, dim):
    # First summarize within market to preserve equal-market weighting.
    market_rows = []
    for scope, subset in scopes(records):
        groups = defaultdict(list)
        for r in subset:
            if dim == "progress":
                key = (r["checkpoint"], r["progress_q"])
            elif dim == "efficiency":
                key = (r["checkpoint"], r["eff_q"])
            elif dim == "joint":
                key = (r["checkpoint"], r["progress_q"], r["eff_q"])
            else:
                raise ValueError(dim)
            groups[(r["ticker"],) + key].append(r)

        for key, g in groups.items():
            ticker = key[0]
            row = {
                "scope": scope,
                "dimension": dim,
                "ticker": ticker,
                "checkpoint": key[1],
                "n": len(g),
            }
            if dim == "progress":
                row["progress_q"] = key[2]
                row["eff_q"] = ""
            elif dim == "efficiency":
                row["progress_q"] = ""
                row["eff_q"] = key[2]
            else:
                row["progress_q"] = key[2]
                row["eff_q"] = key[3]

            for outcome in OUTCOMES:
                row[f"{outcome}_mean"] = mean([r[outcome] for r in g])
                row[f"{outcome}_median"] = median([r[outcome] for r in g])
            market_rows.append(row)

    universal_rows = []
    ugroups = defaultdict(list)
    for r in market_rows:
        key = (
            r["scope"],
            r["dimension"],
            r["checkpoint"],
            r["progress_q"],
            r["eff_q"],
        )
        ugroups[key].append(r)

    for key, g in ugroups.items():
        scope, dim_name, checkpoint, pq, eq = key
        row = {
            "scope": scope,
            "dimension": dim_name,
            "checkpoint": checkpoint,
            "progress_q": pq,
            "eff_q": eq,
            "markets": len(g),
            "pooled_n": sum(r["n"] for r in g),
        }
        for outcome in OUTCOMES:
            # Equal-market mean of market means + median of market medians.
            row[f"{outcome}_eq_market_mean"] = mean([r[f"{outcome}_mean"] for r in g])
            row[f"{outcome}_eq_market_median"] = median([r[f"{outcome}_median"] for r in g])
        universal_rows.append(row)
    return market_rows, universal_rows


def conditional_contrasts(records):
    rows = []
    for scope, subset in scopes(records):
        for checkpoint in CHECKPOINTS:
            cp = [r for r in subset if r["checkpoint"] == checkpoint]

            # Efficiency Q5-Q1 within each progress quintile.
            for pq in range(1, 6):
                market_effects = defaultdict(list)
                for r in cp:
                    if r["progress_q"] == pq and r["eff_q"] in (1, 5):
                        market_effects[(r["ticker"], r["eff_q"])].append(r)
                tickers = sorted({t for t, _ in market_effects})
                for outcome in OUTCOMES:
                    effects = []
                    for ticker in tickers:
                        low = market_effects.get((ticker, 1), [])
                        high = market_effects.get((ticker, 5), [])
                        if len(low) >= 3 and len(high) >= 3:
                            effects.append(mean([r[outcome] for r in high]) - mean([r[outcome] for r in low]))
                    if effects:
                        expected_positive = outcome != "future_mae_atr"
                        signed = effects if expected_positive else [-x for x in effects]
                        rows.append(
                            {
                                "scope": scope,
                                "checkpoint": checkpoint,
                                "conditional_on": "progress_q",
                                "condition_bucket": pq,
                                "contrast": "eff_q5_minus_q1",
                                "outcome": outcome,
                                "markets": len(effects),
                                "eq_market_mean_effect": mean(effects),
                                "eq_market_median_effect": median(effects),
                                "markets_expected_sign": sum(x > 0 for x in signed),
                            }
                        )

            # Progress Q5-Q1 within each efficiency quintile.
            for eq in range(1, 6):
                market_effects = defaultdict(list)
                for r in cp:
                    if r["eff_q"] == eq and r["progress_q"] in (1, 5):
                        market_effects[(r["ticker"], r["progress_q"])].append(r)
                tickers = sorted({t for t, _ in market_effects})
                for outcome in OUTCOMES:
                    effects = []
                    for ticker in tickers:
                        low = market_effects.get((ticker, 1), [])
                        high = market_effects.get((ticker, 5), [])
                        if len(low) >= 3 and len(high) >= 3:
                            effects.append(mean([r[outcome] for r in high]) - mean([r[outcome] for r in low]))
                    if effects:
                        expected_positive = outcome != "future_mae_atr"
                        signed = effects if expected_positive else [-x for x in effects]
                        rows.append(
                            {
                                "scope": scope,
                                "checkpoint": checkpoint,
                                "conditional_on": "eff_q",
                                "condition_bucket": eq,
                                "contrast": "progress_q5_minus_q1",
                                "outcome": outcome,
                                "markets": len(effects),
                                "eq_market_mean_effect": mean(effects),
                                "eq_market_median_effect": median(effects),
                                "markets_expected_sign": sum(x > 0 for x in signed),
                            }
                        )
    return rows


def direction_diagnostic(records):
    rows = []
    for stage in ("Markup", "Markdown"):
        stage_rows = [r for r in records if r["stage"] == stage]
        _, u_progress = summarize_cells(stage_rows, "progress")
        _, u_eff = summarize_cells(stage_rows, "efficiency")
        for r in u_progress + u_eff:
            row = dict(r)
            row["stage"] = stage
            rows.append(row)
    return rows


def write_csv(path, rows):
    if not rows:
        return
    with Path(path).open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "paths",
        nargs="*",
        help="Issue #76 Forward Logger CSVs; defaults to /mnt/data/pine-logs-#76 Forward Logger*.csv",
    )
    parser.add_argument(
        "--out",
        default="/mnt/data/issue78-add-risk-evidence",
        help="output directory",
    )
    args = parser.parse_args()

    paths = args.paths or sorted(glob.glob("/mnt/data/pine-logs-#76 Forward Logger*.csv"))
    if not paths:
        raise SystemExit("no Issue #76 forward-log CSVs found")

    events = read_events(paths)
    eps = episodes(events)
    if len(events) != EXPECTED_EVENTS:
        raise AssertionError(f"event count drift: expected {EXPECTED_EVENTS}, got {len(events)}")
    if len(eps) != EXPECTED_EPISODES:
        raise AssertionError(f"episode count drift: expected {EXPECTED_EPISODES}, got {len(eps)}")

    records = []
    for ep in eps:
        for k in CHECKPOINTS:
            rec = checkpoint_record(ep, k)
            if rec is not None:
                records.append(rec)

    add_within_market_ranks(records)

    market_rows = []
    universal_rows = []
    for dim in ("progress", "efficiency", "joint"):
        market, universal = summarize_cells(records, dim)
        market_rows.extend(market)
        universal_rows.extend(universal)

    contrasts = conditional_contrasts(records)
    direction = direction_diagnostic(records)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "issue78-add-risk-evidence-checkpoints.csv", records)
    write_csv(out / "issue78-add-risk-evidence-per-market.csv", market_rows)
    write_csv(out / "issue78-add-risk-evidence-universal.csv", universal_rows)
    write_csv(out / "issue78-add-risk-evidence-conditional-contrasts.csv", contrasts)
    write_csv(out / "issue78-add-risk-evidence-direction.csv", direction)

    for k in CHECKPOINTS:
        n = sum(r["checkpoint"] == k for r in records)
        print(f"checkpoint={k} eligible={n}")
    print("events", len(events), "episodes", len(eps), "records", len(records))
    print("wrote", out)


if __name__ == "__main__":
    main()
