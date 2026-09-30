#!/usr/bin/env python3
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
TREND = {2: "Markup", 5: "Markdown"}
ERAS = (("2010-2014", 2010, 2014), ("2015-2019", 2015, 2019), ("2020-2026", 2020, 2026))
EXPECTED_EVENTS = 68118
EXPECTED_EPISODES = 1624
CHECKPOINTS = (5, 10)
OUTCOMES = ("future_extension", "future_net_positive", "remaining20", "remaining_life")

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
                record = {
                    "ticker": fields["ticker"],
                    "repr": fields["repr"],
                    "event_time": int(fields["event_time"]),
                    "event_bar": int(fields["event_bar"]),
                    "stage": int(fields["stage"]),
                    "fresh": int(fields["fresh"]),
                    "scale": float(fields["scale"]),
                    "move1": float(fields["move1"]),
                }
                dedup[(record["ticker"], record["event_time"], record["event_bar"])] = record
    return sorted(dedup.values(), key=lambda row: (row["ticker"], row["event_bar"]))

def episodes(events):
    by_ticker = defaultdict(list)
    for event in events:
        by_ticker[event["ticker"]].append(event)
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

def era_name(ms):
    year = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc).year
    for name, start, end in ERAS:
        if start <= year <= end:
            return name
    return "other"

def build_features(events, eps):
    by_ticker = defaultdict(list)
    for event in events:
        by_ticker[event["ticker"]].append(event)

    lookup = {}
    for ticker, group in by_ticker.items():
        group.sort(key=lambda row: row["event_bar"])
        lookup[ticker] = {row["event_bar"]: row for row in group}

    rows = []
    eligibility = defaultdict(int)

    for ticker, stage, episode_id, episode_rows in eps:
        entry = episode_rows[0]
        entry_bar = entry["event_bar"]
        market = lookup[ticker]

        if any(bar not in market for bar in range(entry_bar - 20, entry_bar)):
            eligibility["pre20_missing"] += 1
            continue

        # Reconstruct the 20 completed closes preceding entry relative to entry close = 0.
        relative_close = 0.0
        prior_close_by_bar = {entry_bar: 0.0}
        for bar in range(entry_bar - 1, entry_bar - 21, -1):
            relative_close -= market[bar]["move1"]
            prior_close_by_bar[bar] = relative_close
        prior_closes = [prior_close_by_bar[bar] for bar in range(entry_bar - 20, entry_bar)]

        direction = 1.0 if stage == 2 else -1.0
        if stage == 2:
            boundary_aligned = max(prior_closes)
        else:
            boundary_aligned = -min(prior_closes)

        atr = entry["scale"] * (100.0 if entry["repr"] == "YIELD_LEVEL" else 1.0)
        if not (math.isfinite(atr) and atr > 0):
            eligibility["bad_atr"] += 1
            continue

        aligned_moves = [direction * row["move1"] for row in episode_rows]
        cumulative = [0.0]
        value = 0.0
        for move in aligned_moves:
            value += move
            cumulative.append(value)

        first_break_move = next(
            (i for i, cum in enumerate(cumulative) if cum > boundary_aligned + 1e-12),
            None,
        )
        structure_at_entry = int(first_break_move == 0)
        progress_at_break = (
            cumulative[first_break_move] / atr if first_break_move is not None else math.nan
        )

        eligibility["eligible_base"] += 1
        if first_break_move is not None:
            eligibility["ever_break"] += 1

        mfe_atr = max(cumulative) / atr
        legacy_label = "failed" if mfe_atr < 4.0 else ("large" if mfe_atr >= 8.0 else "middle")

        for checkpoint in CHECKPOINTS:
            if len(aligned_moves) < checkpoint:
                continue
            progress = cumulative[checkpoint] / atr
            checkpoint_peak = max(cumulative[: checkpoint + 1])
            future = cumulative[checkpoint + 1:]

            rows.append({
                "ticker": ticker,
                "stage": TREND[stage],
                "episode_id": episode_id,
                "entry_time": entry["event_time"],
                "era": era_name(entry["event_time"]),
                "checkpoint": checkpoint,
                "progress": progress,
                "progress_quintile": 0,
                "boundary_aligned_atr": boundary_aligned / atr,
                "structure_at_entry": structure_at_entry,
                "first_break_move": float(first_break_move) if first_break_move is not None else math.nan,
                "progress_at_break": progress_at_break,
                "structure_by_k": int(first_break_move is not None and first_break_move <= checkpoint),
                "post_entry_structure_by_k": int(first_break_move is not None and 1 <= first_break_move <= checkpoint),
                "future_extension": int(bool(future) and max(future) > checkpoint_peak + 1e-12),
                "future_net_positive": int(cumulative[-1] - cumulative[checkpoint] > 0),
                "remaining20": int(len(aligned_moves) - checkpoint >= 20),
                "remaining_life": len(aligned_moves) - checkpoint,
                "legacy_label": legacy_label,
                "mfe_atr": mfe_atr,
            })

    frame = pd.DataFrame(rows)

    for _, indices in frame.groupby(["ticker", "checkpoint"]).groups.items():
        values = frame.loc[indices, "progress"].values
        ranks = rankdata(values, method="average")
        quintiles = np.minimum(5, np.maximum(1, np.ceil(ranks / len(values) * 5))).astype(int)
        frame.loc[indices, "progress_quintile"] = quintiles

    return frame, dict(eligibility)

def structure_standalone(frame):
    market_rows = []
    for (checkpoint, ticker), group in frame.groupby(["checkpoint", "ticker"]):
        yes = group[group["structure_by_k"] == 1]
        no = group[group["structure_by_k"] == 0]
        if len(yes) < 3 or len(no) < 3:
            continue
        row = {
            "checkpoint": checkpoint,
            "ticker": ticker,
            "n_struct": len(yes),
            "n_no_struct": len(no),
            "structure_rate": len(yes) / len(group),
        }
        for outcome in OUTCOMES:
            row[f"{outcome}_delta"] = yes[outcome].mean() - no[outcome].mean()
        market_rows.append(row)

    market = pd.DataFrame(market_rows)
    universal_rows = []
    for checkpoint, group in market.groupby("checkpoint"):
        row = {
            "checkpoint": checkpoint,
            "markets": group["ticker"].nunique(),
            "structure_rate_eq_market": group["structure_rate"].mean(),
        }
        for outcome in OUTCOMES:
            row[f"{outcome}_delta_eq_market"] = group[f"{outcome}_delta"].mean()
            row[f"{outcome}_positive_markets"] = int((group[f"{outcome}_delta"] > 0).sum())
        universal_rows.append(row)
    return market, pd.DataFrame(universal_rows)

def conditional_cells(frame, state_column="structure_by_k", only_no_entry_structure=False, extra_groups=()):
    data = frame[frame["structure_at_entry"] == 0].copy() if only_no_entry_structure else frame.copy()
    cells = []
    groups = ["checkpoint", *extra_groups, "ticker", "progress_quintile"]

    for keys, group in data.groupby(groups):
        if not isinstance(keys, tuple):
            keys = (keys,)
        yes = group[group[state_column] == 1]
        no = group[group[state_column] == 0]
        if len(yes) < 3 or len(no) < 3:
            continue
        row = dict(zip(groups, keys))
        row["n_struct"] = len(yes)
        row["n_no_struct"] = len(no)
        row["weight"] = min(len(yes), len(no))
        for outcome in OUTCOMES:
            row[f"{outcome}_delta"] = yes[outcome].mean() - no[outcome].mean()
        cells.append(row)

    cells = pd.DataFrame(cells)
    if cells.empty:
        return cells, pd.DataFrame(), pd.DataFrame()

    market_rows = []
    market_groups = ["checkpoint", *extra_groups, "ticker"]
    for keys, group in cells.groupby(market_groups):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(market_groups, keys))
        row["eligible_cells"] = len(group)
        row["weight_sum"] = group["weight"].sum()
        for outcome in OUTCOMES:
            row[f"{outcome}_delta"] = np.average(
                group[f"{outcome}_delta"], weights=group["weight"]
            )
        market_rows.append(row)
    market = pd.DataFrame(market_rows)

    universal_rows = []
    universal_groups = ["checkpoint", *extra_groups]
    for keys, group in market.groupby(universal_groups):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(universal_groups, keys))
        row["eligible_markets"] = group["ticker"].nunique()
        row["eligible_cells"] = int(group["eligible_cells"].sum())
        for outcome in OUTCOMES:
            values = group[f"{outcome}_delta"]
            row[f"{outcome}_delta_eq_market"] = values.mean()
            row[f"{outcome}_delta_median_market"] = values.median()
            row[f"{outcome}_positive_markets"] = int((values > 0).sum())
        universal_rows.append(row)

    return cells, market, pd.DataFrame(universal_rows)

def progress_quintile_structure_rates(frame):
    market = (
        frame.groupby(["checkpoint", "ticker", "progress_quintile"])
        .agg(n=("structure_by_k", "size"), structure_rate=("structure_by_k", "mean"))
        .reset_index()
    )
    universal = (
        market.groupby(["checkpoint", "progress_quintile"])
        .agg(
            markets=("ticker", "nunique"),
            pooled_n=("n", "sum"),
            structure_rate_eq_market=("structure_rate", "mean"),
        )
        .reset_index()
    )
    return market, universal

def timing_summary(frame):
    # checkpoint-5 population is used to avoid mixing survival requirements.
    base = frame[frame["checkpoint"] == 5].copy()
    market_rows = []
    for ticker, group in base.groupby("ticker"):
        hit = group[group["first_break_move"].notna()]
        market_rows.append({
            "ticker": ticker,
            "n": len(group),
            "structure_at_entry_rate": group["structure_at_entry"].mean(),
            "structure_by5_rate": group["structure_by_k"].mean(),
            "ever_structure_rate": group["first_break_move"].notna().mean(),
            "mean_break_move": hit["first_break_move"].mean(),
            "median_break_move": hit["first_break_move"].median(),
            "mean_progress_at_break": hit["progress_at_break"].mean(),
            "median_progress_at_break": hit["progress_at_break"].median(),
        })
    market = pd.DataFrame(market_rows)
    row = {"markets": len(market), "pooled_n": int(market["n"].sum())}
    for column in market.columns:
        if column not in ("ticker", "n"):
            row[column] = market[column].mean()
    return market, pd.DataFrame([row])

def write_csv(path, frame):
    frame.to_csv(path, index=False)

def main():
    paths = sorted(glob.glob("/mnt/data/pine-logs-#76 Forward Logger*.csv"))
    events = read_events(paths)
    eps = episodes(events)
    if len(events) != EXPECTED_EVENTS:
        raise AssertionError(f"event count drift: {len(events)}")
    if len(eps) != EXPECTED_EPISODES:
        raise AssertionError(f"episode count drift: {len(eps)}")

    frame, eligibility = build_features(events, eps)
    out = Path("/mnt/data/issue78-structure-stage1")
    out.mkdir(parents=True, exist_ok=True)

    standalone_market, standalone_universal = structure_standalone(frame)
    cells, conditional_market, conditional_universal = conditional_cells(frame)
    _, _, temporal = conditional_cells(frame, extra_groups=("era",))
    _, _, direction = conditional_cells(frame, extra_groups=("stage",))
    _, post_entry_market, post_entry_universal = conditional_cells(
        frame,
        state_column="post_entry_structure_by_k",
        only_no_entry_structure=True,
    )
    _, entry_market, entry_universal = conditional_cells(
        frame,
        state_column="structure_at_entry",
    )
    rates_market, rates_universal = progress_quintile_structure_rates(frame)
    timing_market, timing_universal = timing_summary(frame)

    write_csv(out / "issue78-structure-stage1-features.csv", frame)
    write_csv(out / "issue78-structure-stage1-standalone-per-market.csv", standalone_market)
    write_csv(out / "issue78-structure-stage1-standalone-universal.csv", standalone_universal)
    write_csv(out / "issue78-structure-stage1-conditional-cells.csv", cells)
    write_csv(out / "issue78-structure-stage1-conditional-per-market.csv", conditional_market)
    write_csv(out / "issue78-structure-stage1-conditional-universal.csv", conditional_universal)
    write_csv(out / "issue78-structure-stage1-conditional-temporal.csv", temporal)
    write_csv(out / "issue78-structure-stage1-conditional-direction.csv", direction)
    write_csv(out / "issue78-structure-stage1-post-entry-conditional-per-market.csv", post_entry_market)
    write_csv(out / "issue78-structure-stage1-post-entry-conditional-universal.csv", post_entry_universal)
    write_csv(out / "issue78-structure-stage1-entry-structure-conditional-per-market.csv", entry_market)
    write_csv(out / "issue78-structure-stage1-entry-structure-conditional-universal.csv", entry_universal)
    write_csv(out / "issue78-structure-stage1-structure-rate-by-progress-per-market.csv", rates_market)
    write_csv(out / "issue78-structure-stage1-structure-rate-by-progress.csv", rates_universal)
    write_csv(out / "issue78-structure-stage1-timing-per-market.csv", timing_market)
    write_csv(out / "issue78-structure-stage1-timing-universal.csv", timing_universal)

    print("events", len(events), "episodes", len(eps), "eligibility", eligibility)
    print("rows", len(frame))

if __name__ == "__main__":
    main()
