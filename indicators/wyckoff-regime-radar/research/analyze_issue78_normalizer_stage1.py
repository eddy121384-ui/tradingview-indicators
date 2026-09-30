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
from scipy.stats import pearsonr, rankdata, spearmanr

MARKER = "ISSUE76|schema=1"
TREND = {2: "Markup", 5: "Markdown"}
ERAS = (("2010-2014", 2010, 2014), ("2015-2019", 2015, 2019), ("2020-2026", 2020, 2026))
EXPECTED_EVENTS = 68118
EXPECTED_EPISODES = 1624
NORMALIZERS = ("atr", "sigma20", "medabs20")
CHECKPOINTS = (5, 10)
OUTCOMES = ("future_extension", "future_net_positive", "remaining20")


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


def auc_score(labels, scores):
    labels = np.asarray(labels, dtype=int)
    scores = np.asarray(scores, dtype=float)
    positives = labels == 1
    negatives = labels == 0
    n_pos = positives.sum()
    n_neg = negatives.sum()
    if n_pos == 0 or n_neg == 0:
        return math.nan
    ranks = rankdata(scores, method="average")
    return float(
        (ranks[positives].sum() - n_pos * (n_pos + 1) / 2.0)
        / (n_pos * n_neg)
    )


def build_features(events, eps):
    by_ticker = defaultdict(list)
    for event in events:
        by_ticker[event["ticker"]].append(event)
    lookup = {}
    for ticker, group in by_ticker.items():
        group.sort(key=lambda row: row["event_bar"])
        lookup[ticker] = {row["event_bar"]: row for row in group}

    rows = []
    eligibility = {"pre20_missing": 0, "bad_scale": 0, "eligible_base": 0}

    for ticker, stage, episode_id, episode_rows in eps:
        entry = episode_rows[0]
        entry_bar = entry["event_bar"]
        market = lookup[ticker]

        previous_moves = []
        consecutive = True
        for bar in range(entry_bar - 20, entry_bar):
            if bar not in market:
                consecutive = False
                break
            previous_moves.append(market[bar]["move1"])
        if not consecutive:
            eligibility["pre20_missing"] += 1
            continue

        atr = entry["scale"] * (100.0 if entry["repr"] == "YIELD_LEVEL" else 1.0)
        sigma20 = float(np.std(previous_moves, ddof=1))
        medabs20 = float(np.median(np.abs(previous_moves)))
        scales = {"atr": atr, "sigma20": sigma20, "medabs20": medabs20}

        if not all(math.isfinite(value) and value > 0 for value in scales.values()):
            eligibility["bad_scale"] += 1
            continue
        eligibility["eligible_base"] += 1

        direction = 1.0 if stage == 2 else -1.0
        aligned_moves = [direction * row["move1"] for row in episode_rows]
        cumulative = [0.0]
        total = 0.0
        for move in aligned_moves:
            total += move
            cumulative.append(total)

        mfe_atr = max(cumulative) / atr
        legacy_label = (
            "failed" if mfe_atr < 4.0
            else "large" if mfe_atr >= 8.0
            else "middle"
        )

        for checkpoint in CHECKPOINTS:
            if len(aligned_moves) < checkpoint:
                continue

            progress_raw = cumulative[checkpoint]
            peak_at_checkpoint = max(cumulative[: checkpoint + 1])
            future_path = cumulative[checkpoint + 1:]
            future_extension = int(
                bool(future_path)
                and max(future_path) > peak_at_checkpoint + 1e-12
            )
            future_net = cumulative[-1] - cumulative[checkpoint]
            remaining_life = len(aligned_moves) - checkpoint

            record = {
                "ticker": ticker,
                "stage": TREND[stage],
                "episode_id": episode_id,
                "entry_time": entry["event_time"],
                "era": era_name(entry["event_time"]),
                "checkpoint": checkpoint,
                "future_extension": future_extension,
                "future_net_positive": int(future_net > 0),
                "remaining20": int(remaining_life >= 20),
                "remaining_life": remaining_life,
                "legacy_label": legacy_label,
                "mfe_atr": mfe_atr,
                "progress_raw": progress_raw,
            }
            for normalizer, scale in scales.items():
                record[f"{normalizer}_scale"] = scale
                record[f"progress_{normalizer}"] = progress_raw / scale
            rows.append(record)

    return pd.DataFrame(rows), eligibility


def market_auc(df, extra_groups=()):
    rows = []
    groups = ["checkpoint", *extra_groups, "ticker"]
    for keys, group in df.groupby(groups):
        if not isinstance(keys, tuple):
            keys = (keys,)
        base = dict(zip(groups, keys))
        for normalizer in NORMALIZERS:
            for outcome in OUTCOMES:
                auc = auc_score(group[outcome], group[f"progress_{normalizer}"])
                if math.isfinite(auc):
                    rows.append({
                        **base,
                        "normalizer": normalizer,
                        "outcome": outcome,
                        "n": len(group),
                        "auc": auc,
                    })
    return pd.DataFrame(rows)


def summarize_auc(market_rows, extra_groups=()):
    if market_rows.empty:
        return pd.DataFrame()
    groups = ["checkpoint", *extra_groups, "normalizer", "outcome"]
    rows = []
    for keys, group in market_rows.groupby(groups):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(groups, keys))
        values = group["auc"].values
        row.update({
            "markets": len(group),
            "auc_eq_mean": float(np.mean(values)),
            "auc_eq_median": float(np.median(values)),
            "markets_gt_0_5": int((values > 0.5).sum()),
        })
        rows.append(row)
    return pd.DataFrame(rows)


def add_quintiles(df):
    out = df.copy()
    for normalizer in NORMALIZERS:
        column = f"q_{normalizer}"
        out[column] = 0
        for _, indices in out.groupby(["ticker", "checkpoint"]).groups.items():
            values = out.loc[indices, f"progress_{normalizer}"].values
            ranks = rankdata(values, method="average")
            quintiles = np.minimum(
                5, np.maximum(1, np.ceil(ranks / len(values) * 5))
            ).astype(int)
            out.loc[indices, column] = quintiles
    return out


def quintile_summary(df, extra_groups=()):
    market_rows = []
    for normalizer in NORMALIZERS:
        groups = ["checkpoint", *extra_groups, "ticker", f"q_{normalizer}"]
        for keys, group in df.groupby(groups):
            if not isinstance(keys, tuple):
                keys = (keys,)
            values = dict(zip(groups, keys))
            market_rows.append({
                **values,
                "normalizer": normalizer,
                "quintile": int(values[f"q_{normalizer}"]),
                "n": len(group),
                "future_extension": group["future_extension"].mean(),
                "future_net_positive": group["future_net_positive"].mean(),
                "remaining20": group["remaining20"].mean(),
                "remaining_life": group["remaining_life"].mean(),
            })

    market = pd.DataFrame(market_rows)
    if market.empty:
        return market, pd.DataFrame()

    groups = ["checkpoint", *extra_groups, "normalizer", "quintile"]
    universal = (
        market.groupby(groups)
        .agg(
            markets=("ticker", "nunique"),
            pooled_n=("n", "sum"),
            future_extension=("future_extension", "mean"),
            future_net_positive=("future_net_positive", "mean"),
            remaining20=("remaining20", "mean"),
            remaining_life=("remaining_life", "mean"),
        )
        .reset_index()
    )
    return market, universal


def q5_minus_q1(universal, extra_groups=()):
    rows = []
    groups = ["checkpoint", *extra_groups, "normalizer"]
    for keys, group in universal.groupby(groups):
        if not isinstance(keys, tuple):
            keys = (keys,)
        q1 = group[group["quintile"] == 1]
        q5 = group[group["quintile"] == 5]
        if q1.empty or q5.empty:
            continue
        row = dict(zip(groups, keys))
        for outcome in (
            "future_extension",
            "future_net_positive",
            "remaining20",
            "remaining_life",
        ):
            row[f"{outcome}_q5_minus_q1"] = float(
                q5.iloc[0][outcome] - q1.iloc[0][outcome]
            )
        rows.append(row)
    return pd.DataFrame(rows)


def ranking_stability(df):
    pairs = (
        ("atr", "sigma20"),
        ("atr", "medabs20"),
        ("sigma20", "medabs20"),
    )
    rows = []
    for checkpoint, group in df.groupby("checkpoint"):
        for left, right in pairs:
            pearsons = []
            spearmans = []
            same_quintile = []
            within_one = []
            for _, market in group.groupby("ticker"):
                if len(market) < 3:
                    continue
                pearsons.append(
                    pearsonr(
                        market[f"progress_{left}"],
                        market[f"progress_{right}"],
                    ).statistic
                )
                spearmans.append(
                    spearmanr(
                        market[f"progress_{left}"],
                        market[f"progress_{right}"],
                    ).statistic
                )
                q_left = market[f"q_{left}"].astype(int).values
                q_right = market[f"q_{right}"].astype(int).values
                same_quintile.append(np.mean(q_left == q_right))
                within_one.append(np.mean(np.abs(q_left - q_right) <= 1))

            rows.append({
                "checkpoint": checkpoint,
                "a": left,
                "b": right,
                "markets": len(pearsons),
                "pearson_eq_mean": np.mean(pearsons),
                "spearman_eq_mean": np.mean(spearmans),
                "same_quintile_eq_mean": np.mean(same_quintile),
                "within_one_quintile_eq_mean": np.mean(within_one),
            })
    return pd.DataFrame(rows)


def legacy_auc(df):
    legacy = df[df["legacy_label"].isin(["failed", "large"])].copy()
    legacy["large"] = (legacy["legacy_label"] == "large").astype(int)
    rows = []
    for (checkpoint, ticker), group in legacy.groupby(["checkpoint", "ticker"]):
        for normalizer in NORMALIZERS:
            auc = auc_score(group["large"], group[f"progress_{normalizer}"])
            if math.isfinite(auc):
                rows.append({
                    "checkpoint": checkpoint,
                    "ticker": ticker,
                    "normalizer": normalizer,
                    "n": len(group),
                    "auc": auc,
                })
    market = pd.DataFrame(rows)
    universal = (
        market.groupby(["checkpoint", "normalizer"])
        .agg(
            markets=("ticker", "nunique"),
            auc_eq_mean=("auc", "mean"),
            auc_eq_median=("auc", "median"),
            markets_gt_0_5=("auc", lambda values: int((values > 0.5).sum())),
        )
        .reset_index()
    )
    return market, universal


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

    features, eligibility = build_features(events, eps)
    features = add_quintiles(features)

    out = Path("/mnt/data/issue78-normalizer-stage1")
    out.mkdir(parents=True, exist_ok=True)

    auc_market = market_auc(features)
    auc_universal = summarize_auc(auc_market)
    auc_temporal = summarize_auc(market_auc(features, ("era",)), ("era",))
    auc_direction = summarize_auc(market_auc(features, ("stage",)), ("stage",))

    _, quintile_universal = quintile_summary(features)
    _, quintile_temporal = quintile_summary(features, ("era",))
    _, quintile_direction = quintile_summary(features, ("stage",))

    ranking = ranking_stability(features)
    _, legacy_universal = legacy_auc(features)

    write_csv(out / "issue78-normalizer-features.csv", features)
    write_csv(out / "issue78-normalizer-auc-per-market.csv", auc_market)
    write_csv(out / "issue78-normalizer-auc-universal.csv", auc_universal)
    write_csv(out / "issue78-normalizer-auc-temporal.csv", auc_temporal)
    write_csv(out / "issue78-normalizer-auc-direction.csv", auc_direction)
    write_csv(out / "issue78-normalizer-quintiles-universal.csv", quintile_universal)
    write_csv(out / "issue78-normalizer-quintile-diffs.csv", q5_minus_q1(quintile_universal))
    write_csv(out / "issue78-normalizer-quintile-diffs-temporal.csv", q5_minus_q1(quintile_temporal, ("era",)))
    write_csv(out / "issue78-normalizer-quintile-diffs-direction.csv", q5_minus_q1(quintile_direction, ("stage",)))
    write_csv(out / "issue78-normalizer-ranking-stability.csv", ranking)
    write_csv(out / "issue78-normalizer-legacy-auc-universal.csv", legacy_universal)

    print("events", len(events), "episodes", len(eps))
    print("eligibility", eligibility)
    print("checkpoint5", int((features["checkpoint"] == 5).sum()))
    print("checkpoint10", int((features["checkpoint"] == 10).sum()))
    print("wrote", out)


if __name__ == "__main__":
    main()
