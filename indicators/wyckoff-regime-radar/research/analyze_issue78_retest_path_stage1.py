#!/usr/bin/env python3
"""Issue #78 Retest / Acceptance Path Challenge Stage 1.

Reconstruct relative OHLC coordinates from the accepted Issue #76 logger,
reuse the frozen first post-entry 5-bar-box breakout, classify the next three
bars into four causal path states, and measure only future outcomes beginning
after the t+3 evidence window.
"""
from __future__ import annotations

import csv
import glob
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata

MARKER = "ISSUE76|schema=1"
EXPECTED_EVENTS = 68118
EXPECTED_EPISODES = 1624
LOOKBACK = 5
OUTCOMES = (
    "reexpand5",
    "reexpand10",
    "future_net_positive",
    "remaining20_after3",
    "remaining_life_after3",
)


def parse_marker(text):
    p = text.find(MARKER)
    if p < 0:
        return None
    out = {}
    for token in text[p:].strip().split("|"):
        if "=" in token:
            key, value = token.split("=", 1)
            out[key] = value
    return out


def read_events(paths):
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
                    "event_time": int(fields["event_time"]),
                    "event_bar": int(fields["event_bar"]),
                    "stage": int(fields["stage"]),
                    "fresh": int(fields["fresh"]),
                    "scale": float(fields["scale"]),
                    "move1": float(fields["move1"]),
                    "mfe1": float(fields["mfe1"]),
                    "mae1": float(fields["mae1"]),
                }
                dedup[(rec["ticker"], rec["event_time"], rec["event_bar"])] = rec
    return sorted(dedup.values(), key=lambda row: (row["ticker"], row["event_bar"]))


def era_name(ms):
    year = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).year
    if 2010 <= year <= 2014:
        return "2010-2014"
    if 2015 <= year <= 2019:
        return "2015-2019"
    if 2020 <= year <= 2026:
        return "2020-2026"
    return "pre-2010" if year < 2010 else "other"


def reconstruct(events):
    grouped = defaultdict(list)
    for event in events:
        grouped[event["ticker"]].append(event)

    frames = {}
    errors = []
    for ticker, group in grouped.items():
        group = sorted(group, key=lambda row: row["event_bar"])
        rows = []
        close_coord = 0.0
        for i, event in enumerate(group):
            if i == 0 or event["event_bar"] != group[i - 1]["event_bar"] + 1:
                close_coord = 0.0
                rows.append({**event, "close_coord": close_coord, "high_coord": math.nan, "low_coord": math.nan})
                continue
            prev = group[i - 1]
            prev_close = rows[-1]["close_coord"]
            close_coord = prev_close + prev["move1"]
            high_coord = prev_close + prev["mfe1"]
            low_coord = prev_close + prev["mae1"]
            rows.append({**event, "close_coord": close_coord, "high_coord": high_coord, "low_coord": low_coord})
            errors.extend([
                abs((close_coord - prev_close) - prev["move1"]),
                abs((high_coord - prev_close) - prev["mfe1"]),
                abs((low_coord - prev_close) - prev["mae1"]),
            ])
        frames[ticker] = pd.DataFrame(rows)
    return frames, max(errors) if errors else math.nan


def build_episodes(frames):
    episodes = []
    for ticker, frame in frames.items():
        records = frame.to_dict("records")
        i = 0
        episode_id = 0
        while i < len(records):
            stage = records[i]["stage"]
            if stage in (2, 5) and records[i]["fresh"] == 1:
                j = i + 1
                while (
                    j < len(records)
                    and records[j]["stage"] == stage
                    and records[j]["event_bar"] == records[j - 1]["event_bar"] + 1
                ):
                    j += 1
                if j < len(records):
                    episodes.append((ticker, stage, episode_id, i, records[i:j]))
                    episode_id += 1
                i = j
            else:
                i += 1
    return episodes


def raw_scale(row):
    return row["scale"] * (100.0 if row["repr"] == "YIELD_LEVEL" else 1.0)


def build_paths(frames, episodes):
    rows = []
    stats = defaultdict(int)

    for ticker, stage, episode_id, start, episode in episodes:
        if len(episode) < 7:
            stats["too_short"] += 1
            continue

        frame = frames[ticker]
        direction = 1 if stage == 2 else -1
        found = False

        for local_t in range(6, len(episode)):
            idx = start + local_t
            pre = frame.iloc[idx - LOOKBACK:idx]
            current = frame.iloc[idx]
            if (
                len(pre) != LOOKBACK
                or pre[["high_coord", "low_coord"]].isna().any().any()
                or pd.isna(current["high_coord"])
                or pd.isna(current["low_coord"])
            ):
                continue

            box_high = float(pre["high_coord"].max())
            box_low = float(pre["low_coord"].min())
            if not box_high > box_low:
                continue

            close = float(current["close_coord"])
            if not (close > box_high if direction == 1 else close < box_low):
                continue

            scale = raw_scale(frame.iloc[idx - 1])
            if not scale > 0:
                continue

            remaining = len(episode) - 1 - local_t
            found = True
            if remaining < 3:
                stats["b3_ineligible"] += 1
                break

            early = frame.iloc[idx + 1:idx + 4]
            if len(early) != 3 or early[["close_coord", "high_coord", "low_coord"]].isna().any().any():
                stats["b3_missing"] += 1
                break

            closes = early["close_coord"].to_numpy(float)
            highs = early["high_coord"].to_numpy(float)
            lows = early["low_coord"].to_numpy(float)

            if direction == 1:
                touch_mask = lows <= box_high
                reentry_mask = closes <= box_high
                final_outside = closes[-1] > box_high
                close_margins = (closes - box_high) / scale
                wick_margins = (lows - box_high) / scale
                followthrough = (closes[-1] - close) / scale
                overshoot = (close - box_high) / scale
                known_best = max(float(current["high_coord"]), float(np.max(highs)))
            else:
                touch_mask = highs >= box_low
                reentry_mask = closes >= box_low
                final_outside = closes[-1] < box_low
                close_margins = (box_low - closes) / scale
                wick_margins = (box_low - highs) / scale
                followthrough = (close - closes[-1]) / scale
                overshoot = (box_low - close) / scale
                known_best = min(float(current["low_coord"]), float(np.min(lows)))

            any_touch = bool(touch_mask.any())
            any_reentry = bool(reentry_mask.any())

            if not any_touch:
                path = "P0_NoTouch"
            elif not any_reentry:
                path = "P1_WickHold"
            elif final_outside:
                path = "P2_Reclaim"
            else:
                path = "P3_FailedAcceptance"

            future_start = idx + 4
            f5 = frame.iloc[future_start:min(future_start + 5, len(frame))]
            f10 = frame.iloc[future_start:min(future_start + 10, len(frame))]
            episode_end_close = float(episode[-1]["close_coord"])

            if direction == 1:
                reexpand5 = int(len(f5) == 5 and np.nanmax(f5["high_coord"].to_numpy(float)) > known_best + 1e-12) if len(f5) == 5 else math.nan
                reexpand10 = int(len(f10) == 10 and np.nanmax(f10["high_coord"].to_numpy(float)) > known_best + 1e-12) if len(f10) == 10 else math.nan
                future_net = int(episode_end_close - closes[-1] > 0)
            else:
                reexpand5 = int(len(f5) == 5 and np.nanmin(f5["low_coord"].to_numpy(float)) < known_best - 1e-12) if len(f5) == 5 else math.nan
                reexpand10 = int(len(f10) == 10 and np.nanmin(f10["low_coord"].to_numpy(float)) < known_best - 1e-12) if len(f10) == 10 else math.nan
                future_net = int(closes[-1] - episode_end_close > 0)

            remaining3 = remaining - 3
            rows.append({
                "ticker": ticker,
                "stage": "Markup" if stage == 2 else "Markdown",
                "episode_id": episode_id,
                "entry_time": episode[0]["event_time"],
                "break_time": int(current["event_time"]),
                "era": era_name(episode[0]["event_time"]),
                "path": path,
                "first_touch_bar": int(np.where(touch_mask)[0][0]) + 1 if any_touch else math.nan,
                "first_reentry_bar": int(np.where(reentry_mask)[0][0]) + 1 if any_reentry else math.nan,
                "outside_close_fraction3": float(np.mean(close_margins > 0)),
                "deepest_wick_margin3_atr": float(np.min(wick_margins)),
                "t3_acceptance_margin_atr": float(close_margins[-1]),
                "followthrough3_atr": float(followthrough),
                "overshoot_atr": float(overshoot),
                "reexpand5": reexpand5,
                "reexpand10": reexpand10,
                "future_net_positive": future_net,
                "remaining20_after3": int(remaining3 >= 20),
                "remaining_life_after3": remaining3,
            })
            stats["accepted"] += 1
            break

        if not found:
            stats["no_breakout"] += 1

    return pd.DataFrame(rows), dict(stats)


def prevalence(frame):
    pooled = frame["path"].value_counts(normalize=True)
    pooled_n = frame["path"].value_counts()
    market = (
        frame.groupby(["ticker", "path"]).size().rename("n").reset_index()
    )
    totals = frame.groupby("ticker").size().rename("total").reset_index()
    market = market.merge(totals, on="ticker")
    market["rate"] = market["n"] / market["total"]

    paths = sorted(frame["path"].unique())
    completed = []
    for ticker in sorted(frame["ticker"].unique()):
        values = market[market["ticker"] == ticker].set_index("path")["rate"]
        for path in paths:
            completed.append({"ticker": ticker, "path": path, "rate": float(values.get(path, 0.0))})
    complete = pd.DataFrame(completed)

    universal = (
        complete.groupby("path")
        .agg(prevalence_eq_market=("rate", "mean"))
        .reset_index()
    )
    universal["prevalence_pooled"] = universal["path"].map(pooled)
    universal["pooled_n"] = universal["path"].map(pooled_n)
    return complete, universal


def path_outcomes(frame):
    market = frame.groupby(["ticker", "path"])[list(OUTCOMES)].mean().reset_index()
    universal = market.groupby("path")[list(OUTCOMES)].mean().reset_index()
    counts = frame.groupby("path").size().rename("pooled_n").reset_index()
    return market, universal.merge(counts, on="path")


def pairwise(frame, pairs, extra=None):
    group_cols = ([] if extra is None else [extra]) + ["ticker"]
    rows = []
    for keys, group in frame.groupby(group_cols):
        if not isinstance(keys, tuple):
            keys = (keys,)
        base = dict(zip(group_cols, keys))
        for a, b in pairs:
            ga = group[group["path"] == a]
            gb = group[group["path"] == b]
            if len(ga) < 3 or len(gb) < 3:
                continue
            row = {**base, "a": a, "b": b, "n_a": len(ga), "n_b": len(gb)}
            for outcome in OUTCOMES:
                row[f"{outcome}_delta"] = ga[outcome].mean() - gb[outcome].mean()
            rows.append(row)

    per_market = pd.DataFrame(rows)
    if per_market.empty:
        return per_market, pd.DataFrame()

    summary_groups = ([] if extra is None else [extra]) + ["a", "b"]
    summary = []
    for keys, group in per_market.groupby(summary_groups):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(summary_groups, keys))
        row["markets"] = group["ticker"].nunique()
        for outcome in OUTCOMES:
            values = group[f"{outcome}_delta"]
            row[f"{outcome}_delta_eq_market"] = values.mean()
            row[f"{outcome}_positive_markets"] = int((values > 0).sum())
        summary.append(row)
    return per_market, pd.DataFrame(summary)


def conditional_p1_vs_p0(frame):
    work = frame.copy()
    work["followthrough_q"] = 0
    for _, indices in work.groupby("ticker").groups.items():
        values = work.loc[indices, "followthrough3_atr"].to_numpy(float)
        ranks = rankdata(values, method="average")
        work.loc[indices, "followthrough_q"] = np.minimum(5, np.maximum(1, np.ceil(ranks / len(values) * 5))).astype(int)

    cells = []
    for (ticker, quintile), group in work.groupby(["ticker", "followthrough_q"]):
        p1 = group[group["path"] == "P1_WickHold"]
        p0 = group[group["path"] == "P0_NoTouch"]
        if len(p1) < 3 or len(p0) < 3:
            continue
        row = {"ticker": ticker, "quintile": int(quintile), "n_p1": len(p1), "n_p0": len(p0), "weight": min(len(p1), len(p0))}
        for outcome in OUTCOMES:
            row[f"{outcome}_delta"] = p1[outcome].mean() - p0[outcome].mean()
        cells.append(row)

    cells = pd.DataFrame(cells)
    market_rows = []
    for ticker, group in cells.groupby("ticker"):
        row = {"ticker": ticker, "cells": len(group)}
        for outcome in OUTCOMES:
            row[f"{outcome}_delta"] = np.average(group[f"{outcome}_delta"], weights=group["weight"])
        market_rows.append(row)

    markets = pd.DataFrame(market_rows)
    summary = {"markets": markets["ticker"].nunique(), "cells": len(cells)}
    for outcome in OUTCOMES:
        summary[f"{outcome}_delta_eq_market"] = markets[f"{outcome}_delta"].mean()
        summary[f"{outcome}_positive_markets"] = int((markets[f"{outcome}_delta"] > 0).sum())
    return cells, markets, pd.DataFrame([summary])


def conditional_p2_vs_p3(frame):
    work = frame[frame["path"].isin(["P2_Reclaim", "P3_FailedAcceptance"])].copy()
    work["penetration_q"] = 0
    for _, indices in work.groupby("ticker").groups.items():
        values = work.loc[indices, "deepest_wick_margin3_atr"].to_numpy(float)
        ranks = rankdata(values, method="average")
        work.loc[indices, "penetration_q"] = np.minimum(5, np.maximum(1, np.ceil(ranks / len(values) * 5))).astype(int)

    cells = []
    for (ticker, quintile), group in work.groupby(["ticker", "penetration_q"]):
        p2 = group[group["path"] == "P2_Reclaim"]
        p3 = group[group["path"] == "P3_FailedAcceptance"]
        if len(p2) < 3 or len(p3) < 3:
            continue
        row = {"ticker": ticker, "quintile": int(quintile), "n_p2": len(p2), "n_p3": len(p3), "weight": min(len(p2), len(p3))}
        for outcome in OUTCOMES:
            row[f"{outcome}_delta"] = p2[outcome].mean() - p3[outcome].mean()
        cells.append(row)

    cells = pd.DataFrame(cells)
    market_rows = []
    for ticker, group in cells.groupby("ticker"):
        row = {"ticker": ticker, "cells": len(group)}
        for outcome in OUTCOMES:
            row[f"{outcome}_delta"] = np.average(group[f"{outcome}_delta"], weights=group["weight"])
        market_rows.append(row)

    markets = pd.DataFrame(market_rows)
    summary = {"markets": markets["ticker"].nunique(), "cells": len(cells)}
    for outcome in OUTCOMES:
        summary[f"{outcome}_delta_eq_market"] = markets[f"{outcome}_delta"].mean()
        summary[f"{outcome}_positive_markets"] = int((markets[f"{outcome}_delta"] > 0).sum())
    return cells, markets, pd.DataFrame([summary])


def main():
    paths = sorted(glob.glob("/mnt/data/pine-logs-#76 Forward Logger*.csv"))
    events = read_events(paths)
    if len(events) != EXPECTED_EVENTS:
        raise AssertionError(f"event count drift: {len(events)}")

    frames, reconstruction_error = reconstruct(events)
    episodes = build_episodes(frames)
    if len(episodes) != EXPECTED_EPISODES:
        raise AssertionError(f"episode count drift: {len(episodes)}")

    frame, stats = build_paths(frames, episodes)
    if len(frame) != 997:
        raise AssertionError(f"B3 event count drift: {len(frame)}")

    out = Path("/mnt/data/issue78-retest-path-stage1")
    out.mkdir(parents=True, exist_ok=True)

    prevalence_market, prevalence_universal = prevalence(frame)
    outcome_market, outcome_universal = path_outcomes(frame)

    pairs = [
        ("P1_WickHold", "P3_FailedAcceptance"),
        ("P2_Reclaim", "P3_FailedAcceptance"),
        ("P1_WickHold", "P0_NoTouch"),
        ("P2_Reclaim", "P1_WickHold"),
    ]
    pair_market, pair_universal = pairwise(frame, pairs)
    _, pair_temporal = pairwise(frame, pairs, "era")
    _, pair_direction = pairwise(frame, pairs, "stage")

    p10_cells, p10_market, p10_universal = conditional_p1_vs_p0(frame)
    p23_cells, p23_market, p23_universal = conditional_p2_vs_p3(frame)

    geometry = (
        frame.groupby("path")
        .agg(
            pooled_n=("path", "size"),
            overshoot_atr=("overshoot_atr", "mean"),
            followthrough3_atr=("followthrough3_atr", "mean"),
            deepest_wick_margin3_atr=("deepest_wick_margin3_atr", "mean"),
            t3_acceptance_margin_atr=("t3_acceptance_margin_atr", "mean"),
            outside_close_fraction3=("outside_close_fraction3", "mean"),
        )
        .reset_index()
    )

    tables = {
        "events": frame,
        "prevalence-per-market": prevalence_market,
        "prevalence-universal": prevalence_universal,
        "outcomes-per-market": outcome_market,
        "outcomes-universal": outcome_universal,
        "pairwise-per-market": pair_market,
        "pairwise-universal": pair_universal,
        "pairwise-temporal": pair_temporal,
        "pairwise-direction": pair_direction,
        "p1-vs-p0-followthrough-cells": p10_cells,
        "p1-vs-p0-followthrough-per-market": p10_market,
        "p1-vs-p0-followthrough-universal": p10_universal,
        "p2-vs-p3-penetration-cells": p23_cells,
        "p2-vs-p3-penetration-per-market": p23_market,
        "p2-vs-p3-penetration-universal": p23_universal,
        "geometry-universal": geometry,
    }
    for name, table in tables.items():
        table.to_csv(out / f"issue78-retest-path-stage1-{name}.csv", index=False)

    print("events", len(events), "episodes", len(episodes))
    print("reconstruction_error", reconstruction_error)
    print("stats", stats)
    print(frame["path"].value_counts().sort_index().to_dict())


if __name__ == "__main__":
    main()
