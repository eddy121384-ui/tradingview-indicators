#!/usr/bin/env python3
"""Issue #78 breakout-quality Stage 1 analysis.

Reconstructs relative OHLC coordinates from the accepted Issue #76 logger,
reuses the frozen Stage 1B first-post-entry breakout event, and separates
breakout-close evidence (B0) from three-bar acceptance/follow-through evidence
(B3). B3 future outcomes begin strictly after the three-bar evidence window.
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
B0_BIN = ("stay_outside3", "stay_outside5", "extension5", "extension10", "remaining20")
B0_ALL = B0_BIN + ("remaining_life",)
B3_BIN = ("reexpand5", "reexpand10", "future_net_positive", "remaining20_after3")
B3_ALL = B3_BIN + ("remaining_life_after3",)


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
                    episodes.append((ticker, stage, episode_id, i, records[i:j]))
                    episode_id += 1
                i = j
            else:
                i += 1
    return episodes


def raw_scale(row):
    return row["scale"] * (100.0 if row["repr"] == "YIELD_LEVEL" else 1.0)


def build_breakouts(frames, episodes):
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
            box_height = box_high - box_low
            if not (math.isfinite(box_height) and box_height > 0):
                continue

            close = float(current["close_coord"])
            if not (close > box_high if direction == 1 else close < box_low):
                continue

            scale = raw_scale(frame.iloc[idx - 1])
            if not (math.isfinite(scale) and scale > 0):
                continue

            high = float(current["high_coord"])
            low = float(current["low_coord"])
            bar_range = high - low
            overshoot = close - box_high if direction == 1 else box_low - close
            close_location = math.nan
            if bar_range > 0:
                close_location = (close - low) / bar_range if direction == 1 else (high - close) / bar_range
                close_location = float(np.clip(close_location, 0.0, 1.0))

            favorable_break_extreme = high if direction == 1 else low
            remaining = len(episode) - 1 - local_t

            def future(n):
                return frame.iloc[idx + 1:min(idx + 1 + n, len(frame))]

            f3, f5, f10 = future(3), future(5), future(10)
            if direction == 1:
                stay3 = int(len(f3) == 3 and np.all(f3["close_coord"].to_numpy(float) > box_high)) if len(f3) == 3 else math.nan
                stay5 = int(len(f5) == 5 and np.all(f5["close_coord"].to_numpy(float) > box_high)) if len(f5) == 5 else math.nan
                ext5 = int(len(f5) == 5 and np.nanmax(f5["high_coord"].to_numpy(float)) > favorable_break_extreme + 1e-12) if len(f5) == 5 else math.nan
                ext10 = int(len(f10) == 10 and np.nanmax(f10["high_coord"].to_numpy(float)) > favorable_break_extreme + 1e-12) if len(f10) == 10 else math.nan
            else:
                stay3 = int(len(f3) == 3 and np.all(f3["close_coord"].to_numpy(float) < box_low)) if len(f3) == 3 else math.nan
                stay5 = int(len(f5) == 5 and np.all(f5["close_coord"].to_numpy(float) < box_low)) if len(f5) == 5 else math.nan
                ext5 = int(len(f5) == 5 and np.nanmin(f5["low_coord"].to_numpy(float)) < favorable_break_extreme - 1e-12) if len(f5) == 5 else math.nan
                ext10 = int(len(f10) == 10 and np.nanmin(f10["low_coord"].to_numpy(float)) < favorable_break_extreme - 1e-12) if len(f10) == 10 else math.nan

            rec = {
                "ticker": ticker,
                "stage": TREND[stage],
                "episode_id": episode_id,
                "entry_time": episode[0]["event_time"],
                "break_time": int(current["event_time"]),
                "era": era_name(episode[0]["event_time"]),
                "break_move": local_t,
                "box_width_atr": box_height / scale,
                "overshoot_atr": overshoot / scale,
                "overshoot_box": overshoot / box_height,
                "close_location": close_location,
                "breakout_range_atr": bar_range / scale if bar_range > 0 else math.nan,
                "stay_outside3": stay3,
                "stay_outside5": stay5,
                "extension5": ext5,
                "extension10": ext10,
                "remaining20": int(remaining >= 20),
                "remaining_life": remaining,
                "b3_eligible": 0,
                "outside_close_fraction3": math.nan,
                "worst_acceptance_margin3": math.nan,
                "followthrough3_atr": math.nan,
                "early_extension3_atr": math.nan,
                "reexpand5": math.nan,
                "reexpand10": math.nan,
                "future_net_positive": math.nan,
                "remaining20_after3": math.nan,
                "remaining_life_after3": math.nan,
            }

            if remaining >= 3:
                early = frame.iloc[idx + 1:idx + 4]
                closes = early["close_coord"].to_numpy(float)
                if len(early) == 3:
                    if direction == 1:
                        margins = (closes - box_high) / scale
                        outside = np.mean(closes > box_high)
                        followthrough = (closes[-1] - close) / scale
                        known_best = max(favorable_break_extreme, float(np.nanmax(early["high_coord"])))
                        early_extension = max(0.0, known_best - favorable_break_extreme) / scale
                    else:
                        margins = (box_low - closes) / scale
                        outside = np.mean(closes < box_low)
                        followthrough = (close - closes[-1]) / scale
                        known_best = min(favorable_break_extreme, float(np.nanmin(early["low_coord"])))
                        early_extension = max(0.0, favorable_break_extreme - known_best) / scale

                    rec.update({
                        "b3_eligible": 1,
                        "outside_close_fraction3": outside,
                        "worst_acceptance_margin3": float(np.min(margins)),
                        "followthrough3_atr": followthrough,
                        "early_extension3_atr": early_extension,
                    })

                    future_start = idx + 4
                    g5 = frame.iloc[future_start:min(future_start + 5, len(frame))]
                    g10 = frame.iloc[future_start:min(future_start + 10, len(frame))]
                    episode_end_close = float(episode[-1]["close_coord"])

                    if direction == 1:
                        rec["reexpand5"] = int(len(g5) == 5 and np.nanmax(g5["high_coord"]) > known_best + 1e-12) if len(g5) == 5 else math.nan
                        rec["reexpand10"] = int(len(g10) == 10 and np.nanmax(g10["high_coord"]) > known_best + 1e-12) if len(g10) == 10 else math.nan
                        rec["future_net_positive"] = int(episode_end_close - closes[-1] > 0)
                    else:
                        rec["reexpand5"] = int(len(g5) == 5 and np.nanmin(g5["low_coord"]) < known_best - 1e-12) if len(g5) == 5 else math.nan
                        rec["reexpand10"] = int(len(g10) == 10 and np.nanmin(g10["low_coord"]) < known_best - 1e-12) if len(g10) == 10 else math.nan
                        rec["future_net_positive"] = int(closes[-1] - episode_end_close > 0)

                    remaining3 = remaining - 3
                    rec["remaining20_after3"] = int(remaining3 >= 20)
                    rec["remaining_life_after3"] = remaining3

            rows.append(rec)
            stats["breakout_events"] += 1
            found = True
            break

        if not found:
            stats["no_breakout"] += 1

    return pd.DataFrame(rows), dict(stats)


def auc_score(labels, scores):
    data = pd.DataFrame({"y": labels, "s": scores}).dropna()
    if data["y"].nunique() < 2:
        return math.nan
    y = data["y"].astype(int).to_numpy()
    s = data["s"].to_numpy(float)
    ranks = rankdata(s, method="average")
    positive = y == 1
    n_pos = positive.sum()
    n_neg = (~positive).sum()
    if n_pos == 0 or n_neg == 0:
        return math.nan
    return float((ranks[positive].sum() - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


def standalone(frame, feature, outcomes, extra=()):
    group_cols = [*extra, "ticker"]
    data = frame.dropna(subset=[feature]).copy()
    data["qtmp"] = 0

    for _, indices in data.groupby(group_cols).groups.items():
        values = data.loc[indices, feature].to_numpy(float)
        ranks = rankdata(values, method="average")
        data.loc[indices, "qtmp"] = np.minimum(5, np.maximum(1, np.ceil(ranks / len(values) * 5))).astype(int)

    market_rows = []
    for keys, group in data.groupby(group_cols):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(group_cols, keys))
        row["n"] = len(group)
        for outcome in outcomes:
            if not outcome.startswith("remaining_life"):
                row[f"{outcome}_auc"] = auc_score(group[outcome], group[feature])
        q5 = group[group["qtmp"] == 5]
        q1 = group[group["qtmp"] == 1]
        for outcome in outcomes:
            row[f"{outcome}_endpoint_delta"] = q5[outcome].mean() - q1[outcome].mean()
        market_rows.append(row)

    markets = pd.DataFrame(market_rows)
    summary_rows = []
    summary_groups = list(extra)
    iterator = [((), markets)] if not summary_groups else markets.groupby(summary_groups)

    for keys, group in iterator:
        if not isinstance(keys, tuple):
            keys = (keys,) if summary_groups else ()
        row = dict(zip(summary_groups, keys))
        row["markets"] = group["ticker"].nunique()
        row["pooled_n"] = int(group["n"].sum())
        for outcome in outcomes:
            if not outcome.startswith("remaining_life"):
                values = group[f"{outcome}_auc"].dropna()
                row[f"{outcome}_auc_eq_market"] = values.mean()
                row[f"{outcome}_auc_gt_0_5_markets"] = int((values > 0.5).sum())
            values = group[f"{outcome}_endpoint_delta"].dropna()
            row[f"{outcome}_endpoint_delta_eq_market"] = values.mean()
            row[f"{outcome}_positive_markets"] = int((values > 0).sum())
        summary_rows.append(row)

    return markets, pd.DataFrame(summary_rows)


def add_quintile(frame, feature):
    out = frame.copy()
    out["cond_q"] = 0
    for _, indices in out.groupby("ticker").groups.items():
        values = out.loc[indices, feature].to_numpy(float)
        ranks = rankdata(values, method="average")
        out.loc[indices, "cond_q"] = np.minimum(5, np.maximum(1, np.ceil(ranks / len(values) * 5))).astype(int)
    return out


def conditional(frame, condition_feature, test_feature, outcomes):
    data = frame.dropna(subset=[condition_feature, test_feature]).copy()
    data = add_quintile(data, condition_feature)
    cells = []

    for (ticker, quintile), group in data.groupby(["ticker", "cond_q"]):
        ranks = rankdata(group[test_feature], method="average") / len(group)
        high = group.iloc[np.where(ranks > 0.5)[0]]
        low = group.iloc[np.where(ranks <= 0.5)[0]]
        if len(high) < 3 or len(low) < 3:
            continue
        row = {
            "ticker": ticker,
            "cond_q": int(quintile),
            "n_high": len(high),
            "n_low": len(low),
            "weight": min(len(high), len(low)),
        }
        for outcome in outcomes:
            row[f"{outcome}_delta"] = high[outcome].mean() - low[outcome].mean()
        cells.append(row)

    cells = pd.DataFrame(cells)
    if cells.empty:
        return cells, pd.DataFrame(), pd.DataFrame()

    market_rows = []
    for ticker, group in cells.groupby("ticker"):
        row = {"ticker": ticker, "cells": len(group), "weight_sum": group["weight"].sum()}
        for outcome in outcomes:
            row[f"{outcome}_delta"] = np.average(group[f"{outcome}_delta"], weights=group["weight"])
        market_rows.append(row)

    markets = pd.DataFrame(market_rows)
    summary = {"eligible_markets": markets["ticker"].nunique(), "eligible_cells": len(cells)}
    for outcome in outcomes:
        summary[f"{outcome}_delta_eq_market"] = markets[f"{outcome}_delta"].mean()
        summary[f"{outcome}_positive_markets"] = int((markets[f"{outcome}_delta"] > 0).sum())

    return cells, markets, pd.DataFrame([summary])


def correlation_summary(frame, features):
    rows = []
    for ticker, group in frame.groupby("ticker"):
        for i, left in enumerate(features):
            for right in features[i + 1:]:
                data = group[[left, right]].dropna()
                if len(data) < 3:
                    continue
                rows.append({
                    "ticker": ticker,
                    "a": left,
                    "b": right,
                    "n": len(data),
                    "spearman": spearmanr(data[left], data[right]).statistic,
                })
    markets = pd.DataFrame(rows)
    universal = (
        markets.groupby(["a", "b"])
        .agg(markets=("ticker", "nunique"), spearman_eq_market=("spearman", "mean"))
        .reset_index()
    )
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

    frame, stats = build_breakouts(frames, episodes)
    out = Path("/mnt/data/issue78-breakout-quality-stage1")
    out.mkdir(parents=True, exist_ok=True)

    tables = {"events": frame}

    for feature in ("overshoot_atr", "close_location", "breakout_range_atr"):
        market, universal = standalone(frame, feature, B0_ALL)
        tables[f"b0-{feature}-per-market"] = market
        tables[f"b0-{feature}-universal"] = universal

    for extra, label in ((("era",), "temporal"), (("stage",), "direction")):
        _, summary = standalone(frame, "overshoot_atr", B0_ALL, extra)
        tables[f"b0-overshoot-{label}"] = summary

    for test_feature, label in (("close_location", "close-location"), ("breakout_range_atr", "range")):
        cells, market, universal = conditional(frame, "overshoot_atr", test_feature, B0_ALL)
        tables[f"b0-{label}-cond-overshoot-cells"] = cells
        tables[f"b0-{label}-cond-overshoot-per-market"] = market
        tables[f"b0-{label}-cond-overshoot-universal"] = universal

    b3 = frame[frame["b3_eligible"] == 1].copy()
    for feature in ("worst_acceptance_margin3", "outside_close_fraction3", "followthrough3_atr", "early_extension3_atr"):
        market, universal = standalone(b3, feature, B3_ALL)
        tables[f"b3-{feature}-per-market"] = market
        tables[f"b3-{feature}-universal"] = universal

    for feature, short in (("worst_acceptance_margin3", "acceptance"), ("followthrough3_atr", "followthrough")):
        for extra, label in ((("era",), "temporal"), (("stage",), "direction")):
            _, summary = standalone(b3, feature, B3_ALL, extra)
            tables[f"b3-{short}-{label}"] = summary

    cells, market, universal = conditional(b3, "overshoot_atr", "worst_acceptance_margin3", B3_ALL)
    tables["b3-acceptance-cond-overshoot-cells"] = cells
    tables["b3-acceptance-cond-overshoot-per-market"] = market
    tables["b3-acceptance-cond-overshoot-universal"] = universal

    cells, market, universal = conditional(b3, "worst_acceptance_margin3", "followthrough3_atr", B3_ALL)
    tables["b3-followthrough-cond-acceptance-cells"] = cells
    tables["b3-followthrough-cond-acceptance-per-market"] = market
    tables["b3-followthrough-cond-acceptance-universal"] = universal

    market, universal = correlation_summary(frame, ["overshoot_atr", "close_location", "breakout_range_atr"])
    tables["b0-correlations-per-market"] = market
    tables["b0-correlations-universal"] = universal

    market, universal = correlation_summary(
        b3,
        ["overshoot_atr", "worst_acceptance_margin3", "followthrough3_atr", "outside_close_fraction3"],
    )
    tables["b3-correlations-per-market"] = market
    tables["b3-correlations-universal"] = universal

    for name, table in tables.items():
        table.to_csv(out / f"issue78-breakout-quality-stage1-{name}.csv", index=False)

    print("events", len(events), "episodes", len(episodes))
    print("reconstruction_error", reconstruction_error)
    print("stats", stats)
    print("breakouts", len(frame), "b3_eligible", len(b3))


if __name__ == "__main__":
    main()
