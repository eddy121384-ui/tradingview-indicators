#!/usr/bin/env python3
"""Issue #78 compression-structure Stage 1B analysis.

Reconstructs relative OHLC coordinates from the accepted Issue #76 one-step
logger fields, finds the first genuine post-entry 5-bar box breakout in each
known-start Markup / Markdown episode, and tests two preregistered structure
dimensions: mean pairwise bar-range IoU and box width / pre-breakout ATR.

Runtime expects the nine exported Issue #76 CSV files under /mnt/data.
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
from scipy.stats import rankdata, spearmanr

MARKER = "ISSUE76|schema=1"
TREND = {2: "Markup", 5: "Markdown"}
ERAS = (("2010-2014", 2010, 2014), ("2015-2019", 2015, 2019), ("2020-2026", 2020, 2026))
EXPECTED_EVENTS = 68118
EXPECTED_EPISODES = 1624
LOOKBACK = 5
BIN = ("survive_outside3", "survive_outside5", "extension5", "extension10", "remaining20")
ALL = BIN + ("remaining_life",)


def parse_marker(text):
    pos = text.find(MARKER)
    if pos < 0:
        return None
    out = {}
    for token in text[pos:].strip().split("|"):
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
    for name, start, end in ERAS:
        if start <= year <= end:
            return name
    return "pre-2010" if year < 2010 else "other"


def reconstruct(events):
    by_ticker = defaultdict(list)
    for event in events:
        by_ticker[event["ticker"]].append(event)

    frames = {}
    errors = []
    for ticker, group in by_ticker.items():
        group = sorted(group, key=lambda row: row["event_bar"])
        rows = []
        close_coord = 0.0
        for i, event in enumerate(group):
            if i == 0:
                rows.append({**event, "close_coord": close_coord, "high_coord": math.nan, "low_coord": math.nan})
                continue

            prev = group[i - 1]
            if event["event_bar"] != prev["event_bar"] + 1:
                close_coord = 0.0
                rows.append({**event, "close_coord": close_coord, "high_coord": math.nan, "low_coord": math.nan})
                continue

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
            row = records[i]
            stage = row["stage"]
            if stage in TREND and row["fresh"] == 1:
                j = i + 1
                while (
                    j < len(records)
                    and records[j]["stage"] == stage
                    and records[j]["event_bar"] == records[j - 1]["event_bar"] + 1
                ):
                    j += 1
                if j < len(records):
                    episodes.append((ticker, stage, episode_id, i, j, records[i:j]))
                    episode_id += 1
                i = j
            else:
                i += 1
    return episodes


def scale_raw(row):
    return row["scale"] * (100.0 if row["repr"] == "YIELD_LEVEL" else 1.0)


def mean_pairwise_iou(pre):
    intervals = list(zip(pre["high_coord"].to_numpy(float), pre["low_coord"].to_numpy(float)))
    values = []
    for i in range(len(intervals)):
        high_i, low_i = intervals[i]
        for j in range(i + 1, len(intervals)):
            high_j, low_j = intervals[j]
            intersection = max(0.0, min(high_i, high_j) - max(low_i, low_j))
            union = max(high_i, high_j) - min(low_i, low_j)
            values.append(intersection / union if union > 0 else 0.0)
    return float(np.mean(values))


def build_breakouts(frames, episodes):
    out = []
    stats = defaultdict(int)

    for ticker, stage, episode_id, start, _end, episode in episodes:
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
            box_height = box_high - box_low
            if not (math.isfinite(box_height) and box_height > 0):
                continue

            current_close = float(current["close_coord"])
            # Preregistered Stage 1B rule:
            # Markup: close[t] > box_high
            # Markdown: close[t] < box_low
            if not (current_close > box_high if direction == 1 else current_close < box_low):
                continue

            prebreak_scale = scale_raw(frame.iloc[idx - 1])
            if not (math.isfinite(prebreak_scale) and prebreak_scale > 0):
                continue

            ranges = (pre["high_coord"] - pre["low_coord"]).to_numpy(float)
            coverage80_count = int(np.sum(ranges >= 0.80 * box_height - 1e-15))
            overlap = mean_pairwise_iou(pre)
            breakout_favorable = float(current["high_coord"] if direction == 1 else current["low_coord"])

            def future(n):
                return frame.iloc[idx + 1:min(idx + 1 + n, len(frame))]

            f3, f5, f10 = future(3), future(5), future(10)
            if direction == 1:
                stay3 = int(len(f3) == 3 and np.all(f3["close_coord"].to_numpy(float) > box_high)) if len(f3) == 3 else math.nan
                stay5 = int(len(f5) == 5 and np.all(f5["close_coord"].to_numpy(float) > box_high)) if len(f5) == 5 else math.nan
                ext5 = int(len(f5) == 5 and np.nanmax(f5["high_coord"].to_numpy(float)) > breakout_favorable + 1e-12) if len(f5) == 5 else math.nan
                ext10 = int(len(f10) == 10 and np.nanmax(f10["high_coord"].to_numpy(float)) > breakout_favorable + 1e-12) if len(f10) == 10 else math.nan
            else:
                stay3 = int(len(f3) == 3 and np.all(f3["close_coord"].to_numpy(float) < box_low)) if len(f3) == 3 else math.nan
                stay5 = int(len(f5) == 5 and np.all(f5["close_coord"].to_numpy(float) < box_low)) if len(f5) == 5 else math.nan
                ext5 = int(len(f5) == 5 and np.nanmin(f5["low_coord"].to_numpy(float)) < breakout_favorable - 1e-12) if len(f5) == 5 else math.nan
                ext10 = int(len(f10) == 10 and np.nanmin(f10["low_coord"].to_numpy(float)) < breakout_favorable - 1e-12) if len(f10) == 10 else math.nan

            remaining = len(episode) - 1 - local_t
            out.append({
                "ticker": ticker,
                "stage": TREND[stage],
                "episode_id": episode_id,
                "entry_time": episode[0]["event_time"],
                "break_time": int(current["event_time"]),
                "era": era_name(episode[0]["event_time"]),
                "break_move": local_t,
                "box_height": box_height,
                "box_width_atr": box_height / prebreak_scale,
                "mean_pairwise_iou": overlap,
                "coverage80_count": coverage80_count,
                "old_cage": int(coverage80_count >= 3),
                "survive_outside3": stay3,
                "survive_outside5": stay5,
                "extension5": ext5,
                "extension10": ext10,
                "remaining20": int(remaining >= 20),
                "remaining_life": remaining,
            })
            found = True
            stats["breakout_events"] += 1
            break

        if not found:
            stats["no_breakout"] += 1

    return pd.DataFrame(out), dict(stats)


def auc(labels, scores):
    data = pd.DataFrame({"y": labels, "s": scores}).dropna()
    if data["y"].nunique() < 2:
        return math.nan
    y = data["y"].astype(int).to_numpy()
    s = data["s"].to_numpy(float)
    ranks = rankdata(s, method="average")
    positive = y == 1
    n_pos = positive.sum()
    n_neg = (~positive).sum()
    return float((ranks[positive].sum() - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


def add_quintiles(frame):
    out = frame.copy()
    for score, target in (("mean_pairwise_iou", "overlap_q"), ("box_width_atr", "width_q")):
        out[target] = 0
        for _, indices in out.groupby("ticker").groups.items():
            values = out.loc[indices, score].to_numpy(float)
            ranks = rankdata(values, method="average")
            out.loc[indices, target] = np.minimum(5, np.maximum(1, np.ceil(ranks / len(values) * 5))).astype(int)
    return out


def standalone(frame, kind, extra=()):
    score = "mean_pairwise_iou" if kind == "overlap" else "box_width_atr"
    group_cols = [*extra, "ticker"]
    data = frame.copy()
    data["qtmp"] = 0

    for _, indices in data.groupby(group_cols).groups.items():
        values = data.loc[indices, score].to_numpy(float)
        ranks = rankdata(values, method="average")
        data.loc[indices, "qtmp"] = np.minimum(5, np.maximum(1, np.ceil(ranks / len(values) * 5))).astype(int)

    market_rows = []
    for keys, group in data.groupby(group_cols):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(group_cols, keys))
        row["n"] = len(group)

        health_score = group[score] if kind == "overlap" else -group[score]
        for outcome in BIN:
            row[f"{outcome}_auc"] = auc(group[outcome], health_score)

        good = group[group["qtmp"] == 5] if kind == "overlap" else group[group["qtmp"] == 1]
        bad = group[group["qtmp"] == 1] if kind == "overlap" else group[group["qtmp"] == 5]
        for outcome in ALL:
            row[f"{outcome}_endpoint_delta"] = good[outcome].mean() - bad[outcome].mean()
        market_rows.append(row)

    markets = pd.DataFrame(market_rows)
    summaries = []
    summary_groups = list(extra)
    iterator = [((), markets)] if not summary_groups else markets.groupby(summary_groups)

    for keys, group in iterator:
        if not isinstance(keys, tuple):
            keys = (keys,) if summary_groups else ()
        row = dict(zip(summary_groups, keys))
        row["markets"] = group["ticker"].nunique()
        for outcome in BIN:
            values = group[f"{outcome}_auc"].dropna()
            row[f"{outcome}_auc_eq_market"] = values.mean()
            row[f"{outcome}_auc_gt_0_5_markets"] = int((values > 0.5).sum())
        for outcome in ALL:
            values = group[f"{outcome}_endpoint_delta"].dropna()
            row[f"{outcome}_endpoint_delta_eq_market"] = values.mean()
            row[f"{outcome}_positive_markets"] = int((values > 0).sum())
        summaries.append(row)

    return markets, pd.DataFrame(summaries)


def conditional_effect(frame, condition_on):
    outer_q = "width_q" if condition_on == "width" else "overlap_q"
    feature = "mean_pairwise_iou" if condition_on == "width" else "box_width_atr"
    high_is_good = condition_on == "width"
    cells = []

    for (ticker, q), group in frame.groupby(["ticker", outer_q]):
        ranks = rankdata(group[feature], method="average") / len(group)
        if high_is_good:
            good = group.iloc[np.where(ranks > 0.5)[0]]
            bad = group.iloc[np.where(ranks <= 0.5)[0]]
        else:
            good = group.iloc[np.where(ranks <= 0.5)[0]]
            bad = group.iloc[np.where(ranks > 0.5)[0]]

        if len(good) < 3 or len(bad) < 3:
            continue

        row = {
            "ticker": ticker,
            outer_q: int(q),
            "n_good": len(good),
            "n_bad": len(bad),
            "weight": min(len(good), len(bad)),
        }
        for outcome in ALL:
            row[f"{outcome}_delta"] = good[outcome].mean() - bad[outcome].mean()
        cells.append(row)

    cells = pd.DataFrame(cells)
    if cells.empty:
        return cells, pd.DataFrame(), pd.DataFrame()

    market_rows = []
    for ticker, group in cells.groupby("ticker"):
        row = {"ticker": ticker, "cells": len(group), "weight_sum": group["weight"].sum()}
        for outcome in ALL:
            row[f"{outcome}_delta"] = np.average(group[f"{outcome}_delta"], weights=group["weight"])
        market_rows.append(row)

    markets = pd.DataFrame(market_rows)
    summary = {"eligible_markets": markets["ticker"].nunique(), "eligible_cells": len(cells)}
    for outcome in ALL:
        summary[f"{outcome}_delta_eq_market"] = markets[f"{outcome}_delta"].mean()
        summary[f"{outcome}_positive_markets"] = int((markets[f"{outcome}_delta"] > 0).sum())
    return cells, markets, pd.DataFrame([summary])


def surface(frame):
    data = frame.copy()
    data["overlap_t"] = 0
    data["width_t"] = 0

    for _, indices in data.groupby("ticker").groups.items():
        for score, target in (("mean_pairwise_iou", "overlap_t"), ("box_width_atr", "width_t")):
            values = data.loc[indices, score].to_numpy(float)
            ranks = rankdata(values, method="average")
            data.loc[indices, target] = np.minimum(3, np.maximum(1, np.ceil(ranks / len(values) * 3))).astype(int)

    rows = []
    for (ticker, overlap_t, width_t), group in data.groupby(["ticker", "overlap_t", "width_t"]):
        row = {"ticker": ticker, "overlap_t": int(overlap_t), "width_t": int(width_t), "n": len(group)}
        for outcome in ALL:
            row[outcome] = group[outcome].mean()
        rows.append(row)

    markets = pd.DataFrame(rows)
    eligible = markets[markets["n"] >= 3]
    universal = (
        eligible.groupby(["overlap_t", "width_t"])
        .agg(markets=("ticker", "nunique"), pooled_n=("n", "sum"), **{o: (o, "mean") for o in ALL})
        .reset_index()
    )
    return markets, universal


def relationship(frame):
    rows = []
    for ticker, group in frame.groupby("ticker"):
        rows.append({
            "ticker": ticker,
            "n": len(group),
            "spearman_overlap_width": spearmanr(group["mean_pairwise_iou"], group["box_width_atr"]).statistic,
            "old_cage_rate": group["old_cage"].mean(),
        })
    markets = pd.DataFrame(rows)
    universal = pd.DataFrame([{
        "markets": len(markets),
        "spearman_eq_market": markets["spearman_overlap_width"].mean(),
        "old_cage_rate_eq_market": markets["old_cage_rate"].mean(),
    }])
    return markets, universal


def main():
    paths = sorted(glob.glob("/mnt/data/pine-logs-#76 Forward Logger*.csv"))
    events = read_events(paths)
    if len(events) != EXPECTED_EVENTS:
        raise AssertionError(f"event count drift: {len(events)}")

    frames, reconstruction_error = reconstruct(events)
    episodes = build_episodes(frames)
    if len(episodes) != EXPECTED_EPISODES:
        raise AssertionError(f"episode count drift: {len(episodes)}")

    breakouts, stats = build_breakouts(frames, episodes)
    breakouts = add_quintiles(breakouts)

    out = Path("/mnt/data/issue78-compression-stage1b")
    out.mkdir(parents=True, exist_ok=True)

    overlap_market, overlap_universal = standalone(breakouts, "overlap")
    width_market, width_universal = standalone(breakouts, "width")
    _, overlap_temporal = standalone(breakouts, "overlap", ("era",))
    _, width_temporal = standalone(breakouts, "width", ("era",))
    _, overlap_direction = standalone(breakouts, "overlap", ("stage",))
    _, width_direction = standalone(breakouts, "width", ("stage",))

    ocells, omarkets, ouniversal = conditional_effect(breakouts, "width")
    wcells, wmarkets, wuniversal = conditional_effect(breakouts, "overlap")
    surface_market, surface_universal = surface(breakouts)
    relation_market, relation_universal = relationship(breakouts)

    tables = {
        "events": breakouts,
        "overlap-per-market": overlap_market,
        "overlap-universal": overlap_universal,
        "overlap-temporal": overlap_temporal,
        "overlap-direction": overlap_direction,
        "width-per-market": width_market,
        "width-universal": width_universal,
        "width-temporal": width_temporal,
        "width-direction": width_direction,
        "overlap-cond-width-cells": ocells,
        "overlap-cond-width-per-market": omarkets,
        "overlap-cond-width-universal": ouniversal,
        "width-cond-overlap-cells": wcells,
        "width-cond-overlap-per-market": wmarkets,
        "width-cond-overlap-universal": wuniversal,
        "surface-per-market": surface_market,
        "surface-universal": surface_universal,
        "relationship-per-market": relation_market,
        "relationship-universal": relation_universal,
    }
    for name, frame in tables.items():
        frame.to_csv(out / f"issue78-compression-stage1b-{name}.csv", index=False)

    print("events", len(events), "episodes", len(episodes))
    print("reconstruction_error", reconstruction_error)
    print("stats", stats)
    print("breakouts", len(breakouts), "old_cage", int(breakouts["old_cage"].sum()))


if __name__ == "__main__":
    main()
