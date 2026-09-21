#!/usr/bin/env python3
"""Issue #78 R0 + Warning-First composition study.

Composes two already-frozen layers without retuning either one:

1. R0 evidence-based participation:
   - 25% Probe from fresh formal trend entry;
   - P0/P1/P2 promote to 100% Full at t+3;
   - P3 / no usable B3 remain at Probe.

2. Frozen deterioration overlays:
   - none;
   - Warning-First 2 / 4 entry-ATR latched giveback reduction;
   - Gentle / Balanced frozen comparators.

The primary comparison is R0 + No De-risk versus R0 + Warning-First.
All actions are causal and apply only to the next move.
"""
from __future__ import annotations

import argparse
import glob
import math
import statistics
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

import analyze_issue78_second_entry_economic_policy as base
import analyze_issue78_retest_path_stage1 as retest

EXPECTED_EVENTS = 68118
EXPECTED_EPISODES = 1624
EXPECTED_B3_EVENTS = 997
EXPECTED_P12 = 236

MANAGEMENT = ("none", "warning_first", "gentle_latch", "balanced_latch")
POLICY_NAMES = {
    "none": "R0_NoDerisk",
    "warning_first": "R0_WarningFirst",
    "gentle_latch": "R0_Gentle",
    "balanced_latch": "R0_Balanced",
}
ERAS = ("2010-2014", "2015-2019", "2020-2026")


def finite(values):
    return [
        float(v)
        for v in values
        if isinstance(v, (int, float, np.integer, np.floating))
        and math.isfinite(float(v))
    ]


def mean(values):
    vals = finite(values)
    return statistics.fmean(vals) if vals else math.nan


def median(values):
    vals = finite(values)
    return statistics.median(vals) if vals else math.nan


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


def apply_management(steps, earned, management, promotion_local=None):
    """Apply frozen deterioration management to an already-earned participation path."""
    cum = 0.0
    peak = 0.0
    damage_cap = 1.0
    reduction_steps = 0
    actual = []
    de_risk_count = 0
    re_risk_count = 0
    max_reduction = 0.0

    promotion_latched = math.nan
    promotion_exposure = math.nan
    promotion_giveback = math.nan
    first_2_after = math.nan
    first_4_after = math.nan

    for i, step in enumerate(steps):
        giveback = max(0.0, peak - cum)
        before_state = reduction_steps if management == "warning_first" else damage_cap

        if management == "none":
            exposure = earned[i]
        elif management == "warning_first":
            target_steps = 2 if giveback >= 4.0 else (1 if giveback >= 2.0 else 0)
            if target_steps > reduction_steps:
                reduction_steps = target_steps
                de_risk_count += 1
            exposure = max(base.PROBE, earned[i] - 0.25 * reduction_steps)
        elif management in ("gentle_latch", "balanced_latch"):
            target = gentle_target(giveback) if management == "gentle_latch" else balanced_target(giveback)
            if target < damage_cap - 1e-12:
                damage_cap = target
                de_risk_count += 1
            exposure = min(earned[i], damage_cap)
        else:
            raise ValueError(management)

        actual.append(exposure)
        max_reduction = max(max_reduction, earned[i] - exposure)

        if promotion_local is not None and i == promotion_local:
            promotion_giveback = giveback
            promotion_exposure = exposure
            if management == "warning_first":
                promotion_latched = int(reduction_steps > 0)

        if promotion_local is not None and i >= promotion_local:
            delay = i - promotion_local
            if math.isnan(first_2_after) and giveback >= 2.0:
                first_2_after = delay
            if math.isnan(first_4_after) and giveback >= 4.0:
                first_4_after = delay

        cum += step
        if cum > peak + 1e-12:
            peak = cum
            if management == "warning_first" and reduction_steps > 0:
                reduction_steps = 0
                re_risk_count += 1
            elif management in ("gentle_latch", "balanced_latch") and damage_cap < 1.0 - 1e-12:
                damage_cap = 1.0
                re_risk_count += 1

    return {
        "actual": actual,
        "de_risk_count": de_risk_count,
        "re_risk_count": re_risk_count,
        "max_reduction": max_reduction,
        "promotion_latched": promotion_latched,
        "promotion_exposure": promotion_exposure,
        "promotion_giveback": promotion_giveback,
        "first_2_after": first_2_after,
        "first_4_after": first_4_after,
    }


def simulate_episode(episode, state, levels, frames, management):
    steps = base.aligned_steps(episode)
    earned, trigger = base.exposures_for_episode(
        "R0_Immediate", episode, state, levels, frames
    )

    promotion_local = None
    if (
        state is not None
        and state["path"] in ("P0_NoTouch", "P1_WickHold", "P2_Reclaim")
        and levels is not None
    ):
        promotion_local = int(levels["t3_local"])

    managed = apply_management(steps, earned, management, promotion_local)
    actual = managed["actual"]
    returns = [e * step for e, step in zip(actual, steps)]

    return steps, earned, actual, returns, managed


def build_episode_records(episodes, state_map, frames, time_index):
    rows = []

    for episode in episodes:
        ticker, stage, episode_id, start, records = episode
        state = state_map.get((ticker, episode_id))
        levels = (
            base.frozen_levels(episode, state, frames, time_index)
            if state is not None
            else None
        )
        steps = base.aligned_steps(episode)
        mfe = base.episode_mfe(steps)
        era = retest.era_name(int(records[0]["event_time"]))
        direction = "Markup" if stage == 2 else "Markdown"
        path = state["path"] if state is not None else "NoUsableB3"

        for management in MANAGEMENT:
            _, earned, actual, returns, managed = simulate_episode(
                episode, state, levels, frames, management
            )

            promotion_local = (
                int(levels["t3_local"])
                if state is not None
                and levels is not None
                and path in ("P0_NoTouch", "P1_WickHold", "P2_Reclaim")
                else None
            )
            post_promotion_return = (
                sum(returns[promotion_local:]) if promotion_local is not None else math.nan
            )
            post_promotion_derisk_bars = (
                sum(actual[i] < earned[i] - 1e-12 for i in range(promotion_local, len(actual)))
                if promotion_local is not None
                else math.nan
            )

            rows.append({
                "ticker": ticker,
                "episode_id": episode_id,
                "direction": direction,
                "era": era,
                "path": path,
                "mfe": mfe,
                "management": management,
                "policy": POLICY_NAMES[management],
                "bars": len(steps),
                "harvest": sum(returns),
                "harvest_median_unit": sum(returns),
                "avg_exposure": mean(actual),
                "turnover": base.path_turnover(actual),
                "below_earned_frac": mean([
                    1.0 if a < e - 1e-12 else 0.0
                    for a, e in zip(actual, earned)
                ]),
                "de_risk_count": float(managed["de_risk_count"]),
                "re_risk_count": float(managed["re_risk_count"]),
                "max_reduction": managed["max_reduction"],
                "promotion_latched": managed["promotion_latched"],
                "promotion_exposure": managed["promotion_exposure"],
                "promotion_giveback": managed["promotion_giveback"],
                "first_2_after_promotion": managed["first_2_after"],
                "first_4_after_promotion": managed["first_4_after"],
                "post_promotion_return": post_promotion_return,
                "post_promotion_derisk_bar_frac": (
                    post_promotion_derisk_bars / (len(actual) - promotion_local)
                    if promotion_local is not None and len(actual) > promotion_local
                    else math.nan
                ),
            })

    return pd.DataFrame(rows)


def build_whole_market(events, episodes, state_map, frames, time_index):
    by_events = defaultdict(list)
    for row in events:
        by_events[row["ticker"]].append(row)
    for rows in by_events.values():
        rows.sort(key=lambda row: row["event_bar"])

    by_episodes = defaultdict(list)
    for episode in episodes:
        by_episodes[episode[0]].append(episode)

    output = []

    for ticker in sorted(by_events):
        ticker_episodes = by_episodes[ticker]
        cutoff = max(int(row["event_time"]) for ep in ticker_episodes for row in ep[4])
        timeline = [row for row in by_events[ticker] if int(row["event_time"]) <= cutoff]
        times = [int(row["event_time"]) for row in timeline]
        index = {event_time: i for i, event_time in enumerate(times)}

        scopes = [("all", None), *[(era, era) for era in ERAS]]

        for management in MANAGEMENT:
            full_returns = [0.0] * len(times)
            full_exposures = [0.0] * len(times)

            for episode in ticker_episodes:
                state = state_map.get((ticker, episode[2]))
                levels = (
                    base.frozen_levels(episode, state, frames, time_index)
                    if state is not None
                    else None
                )
                _, _, exp, ret, _ = simulate_episode(
                    episode, state, levels, frames, management
                )
                for row, e, value in zip(episode[4], exp, ret):
                    i = index[int(row["event_time"])]
                    full_returns[i] = value
                    full_exposures[i] = e

            for scope, era in scopes:
                if scope == "all":
                    ids = list(range(len(times)))
                else:
                    ids = [i for i, t in enumerate(times) if retest.era_name(t) == era]
                if len(ids) < 20:
                    continue
                returns = [full_returns[i] for i in ids]
                exposures = [full_exposures[i] for i in ids]
                output.append({
                    "ticker": ticker,
                    "scope": scope,
                    "management": management,
                    "policy": POLICY_NAMES[management],
                    **base.path_metrics(returns, exposures),
                })

        for direction_code, direction_name in ((2, "Markup"), (5, "Markdown")):
            stage_eps = [ep for ep in ticker_episodes if ep[1] == direction_code]
            for management in MANAGEMENT:
                returns = [0.0] * len(times)
                exposures = [0.0] * len(times)
                for episode in stage_eps:
                    state = state_map.get((ticker, episode[2]))
                    levels = (
                        base.frozen_levels(episode, state, frames, time_index)
                        if state is not None
                        else None
                    )
                    _, _, exp, ret, _ = simulate_episode(
                        episode, state, levels, frames, management
                    )
                    for row, e, value in zip(episode[4], exp, ret):
                        i = index[int(row["event_time"])]
                        returns[i] = value
                        exposures[i] = e
                output.append({
                    "ticker": ticker,
                    "scope": direction_name,
                    "management": management,
                    "policy": POLICY_NAMES[management],
                    **base.path_metrics(returns, exposures),
                })

    return pd.DataFrame(output)


def add_equal_vol(whole):
    keyed = {
        (row.scope, row.ticker, row.management): row
        for row in whole.itertuples(index=False)
    }
    scales = []
    returns = []
    for row in whole.itertuples(index=False):
        ref = keyed[(row.scope, row.ticker, "none")]
        if row.ann_vol > 0 and ref.ann_vol > 0:
            scale = ref.ann_vol / row.ann_vol
            scales.append(scale)
            returns.append(row.ann_return * scale)
        else:
            scales.append(math.nan)
            returns.append(math.nan)
    result = whole.copy()
    result["equal_vol_scale_vs_R0"] = scales
    result["equal_vol_ann_return_vs_R0"] = returns
    return result


def universal_whole(whole):
    fields = (
        "ann_return", "ann_vol", "sharpe", "sortino", "max_drawdown",
        "es5", "q1", "avg_exposure", "ann_turnover",
        "equal_vol_ann_return_vs_R0",
    )
    rows = []
    for (scope, management), group in whole.groupby(["scope", "management"]):
        row = {
            "scope": scope,
            "management": management,
            "policy": POLICY_NAMES[management],
            "markets": group["ticker"].nunique(),
            "positive_return_markets": int((group["ann_return"] > 0).sum()),
        }
        for field in fields:
            vals = finite(group[field].tolist())
            row[field + "_eq_mean"] = mean(vals)
            row[field + "_eq_median"] = median(vals)
        rows.append(row)
    return pd.DataFrame(rows)


def primary_comparisons(whole):
    metrics = (
        "ann_return", "sharpe", "sortino", "max_drawdown", "es5",
        "equal_vol_ann_return_vs_R0", "avg_exposure", "ann_turnover",
    )
    rows = []
    for scope in ("all", *ERAS, "Markup", "Markdown"):
        sample = whole[whole["scope"] == scope]
        keyed = {(r.ticker, r.management): r for r in sample.itertuples(index=False)}
        tickers = sorted(sample["ticker"].unique())
        for management in ("warning_first", "gentle_latch", "balanced_latch"):
            row = {
                "scope": scope,
                "a": POLICY_NAMES[management],
                "b": POLICY_NAMES["none"],
                "markets": len(tickers),
            }
            for metric in metrics:
                deltas = []
                for ticker in tickers:
                    a = keyed[(ticker, management)]
                    b = keyed[(ticker, "none")]
                    va = float(getattr(a, metric))
                    vb = float(getattr(b, metric))
                    if math.isfinite(va) and math.isfinite(vb):
                        deltas.append(va - vb)
                row[metric + "_delta_eq_mean"] = mean(deltas)
                row[metric + "_delta_eq_median"] = median(deltas)
                row[metric + "_positive_markets"] = sum(x > 0 for x in deltas)
            rows.append(row)
    return pd.DataFrame(rows)


def summarize_episode(records, extra_cols=()):
    rows = []
    group_cols = [*extra_cols, "ticker", "management"]
    metrics = (
        "harvest", "avg_exposure", "turnover", "below_earned_frac",
        "de_risk_count", "re_risk_count", "max_reduction",
    )
    for keys, group in records.groupby(group_cols):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(group_cols, keys))
        row["n"] = group["episode_id"].nunique()
        row["harvest_mean"] = group["harvest"].mean()
        row["harvest_median"] = group["harvest"].median()
        for metric in metrics[1:]:
            row[metric + "_mean"] = group[metric].mean()
        rows.append(row)
    return pd.DataFrame(rows)


def equal_market_episode(market, extra_cols=()):
    metric_cols = [
        c for c in market.columns
        if c not in {*extra_cols, "ticker", "management", "n"}
    ]
    rows = []
    group_cols = [*extra_cols, "management"]
    for keys, group in market.groupby(group_cols):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(group_cols, keys))
        row["policy"] = POLICY_NAMES[row["management"]]
        row["markets"] = group["ticker"].nunique()
        row["pooled_n"] = int(group["n"].sum())
        for metric in metric_cols:
            row[metric + "_eq_market"] = group[metric].mean()
        rows.append(row)
    return pd.DataFrame(rows)


def episode_slices(records):
    work = records.copy()
    work["mfe_slice"] = np.where(
        work["mfe"] < 4.0,
        "mfe_lt4",
        np.where(work["mfe"] >= 8.0, "mfe_ge8", "mfe_4_8"),
    )
    market = summarize_episode(work, ("mfe_slice",))
    return equal_market_episode(market, ("mfe_slice",))


def promotion_diagnostics(records):
    work = records[
        records["path"].isin(["P0_NoTouch", "P1_WickHold", "P2_Reclaim"])
        & records["promotion_exposure"].notna()
    ].copy()
    rows = []
    for (ticker, management), group in work.groupby(["ticker", "management"]):
        rows.append({
            "ticker": ticker,
            "management": management,
            "n": group["episode_id"].nunique(),
            "promotion_latched_rate": group["promotion_latched"].mean(),
            "promotion_exposure_mean": group["promotion_exposure"].mean(),
            "promotion_giveback_mean": group["promotion_giveback"].mean(),
            "post_promotion_return_mean": group["post_promotion_return"].mean(),
            "post_promotion_derisk_bar_frac_mean": group["post_promotion_derisk_bar_frac"].mean(),
            "first_2_after_promotion_mean": group["first_2_after_promotion"].mean(),
            "first_4_after_promotion_mean": group["first_4_after_promotion"].mean(),
        })
    market = pd.DataFrame(rows)
    universal = []
    for management, group in market.groupby("management"):
        universal.append({
            "management": management,
            "policy": POLICY_NAMES[management],
            "markets": group["ticker"].nunique(),
            "pooled_n": int(group["n"].sum()),
            **{
                c + "_eq_market": group[c].mean()
                for c in market.columns
                if c not in ("ticker", "management", "n")
            },
        })
    return market, pd.DataFrame(universal)


def tail_diagnostics(records):
    rows = []
    for (ticker, management), group in records.groupby(["ticker", "management"]):
        vals = finite(group["harvest"].tolist())
        positives = sorted([x for x in vals if x > 0], reverse=True)
        k = max(1, math.ceil(0.01 * len(positives))) if positives else 0
        top_share = sum(positives[:k]) / sum(positives) if positives else math.nan

        remove_best = vals.copy()
        if remove_best:
            remove_best.remove(max(remove_best))

        ordered = sorted(enumerate(vals), key=lambda p: p[1], reverse=True)
        positive_ordered = [p for p in ordered if p[1] > 0]
        remove_ids = {idx for idx, _ in positive_ordered[:k]}
        remove_top = [v for i, v in enumerate(vals) if i not in remove_ids]

        rows.append({
            "ticker": ticker,
            "management": management,
            "n": len(vals),
            "top1pct_positive_share": top_share,
            "mean_harvest": mean(vals),
            "mean_remove_best": mean(remove_best),
            "mean_remove_top1pct_winners": mean(remove_top),
        })

    market = pd.DataFrame(rows)
    universal = []
    for management, group in market.groupby("management"):
        universal.append({
            "management": management,
            "policy": POLICY_NAMES[management],
            "markets": group["ticker"].nunique(),
            "top1pct_positive_share_eq_market": group["top1pct_positive_share"].mean(),
            "mean_harvest_eq_market": group["mean_harvest"].mean(),
            "mean_remove_best_eq_market": group["mean_remove_best"].mean(),
            "mean_remove_top1pct_winners_eq_market": group["mean_remove_top1pct_winners"].mean(),
        })
    return market, pd.DataFrame(universal)


def write_csv(path, frame):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*")
    parser.add_argument("--out", default="/mnt/data/issue78-r0-warning-first-composition")
    args = parser.parse_args()

    paths = args.paths or sorted(glob.glob("/mnt/data/pine-logs-#76 Forward Logger*.csv"))
    if not paths:
        raise SystemExit("no Issue #76 Forward Logger CSVs found")

    events = retest.read_events(paths)
    if len(events) != EXPECTED_EVENTS:
        raise AssertionError(f"event count drift: {len(events)}")

    frames, reconstruction_error = retest.reconstruct(events)
    episodes = retest.build_episodes(frames)
    if len(episodes) != EXPECTED_EPISODES:
        raise AssertionError(f"episode count drift: {len(episodes)}")

    paths_frame, path_stats = retest.build_paths(frames, episodes)
    if len(paths_frame) != EXPECTED_B3_EVENTS:
        raise AssertionError(f"B3 event count drift: {len(paths_frame)}")
    p12_n = int(paths_frame["path"].isin(["P1_WickHold", "P2_Reclaim"]).sum())
    if p12_n != EXPECTED_P12:
        raise AssertionError(f"P1/P2 count drift: {p12_n}")

    state_map = base.build_state_map(paths_frame)
    time_index = base.frame_time_index(frames)

    episode_records = build_episode_records(
        episodes, state_map, frames, time_index
    )
    whole_market = build_whole_market(
        events, episodes, state_map, frames, time_index
    )
    whole_market = add_equal_vol(whole_market)
    whole_universal = universal_whole(whole_market)
    comparisons = primary_comparisons(whole_market)

    episode_market = summarize_episode(episode_records)
    episode_universal = equal_market_episode(episode_market)

    temporal_market = summarize_episode(episode_records, ("era",))
    temporal = equal_market_episode(temporal_market, ("era",))

    direction_market = summarize_episode(episode_records, ("direction",))
    direction = equal_market_episode(direction_market, ("direction",))

    slices = episode_slices(episode_records)
    promo_market, promo_universal = promotion_diagnostics(episode_records)
    tail_market, tail_universal = tail_diagnostics(episode_records)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "issue78-r0-warning-first-episode-policy.csv", episode_records)
    write_csv(out / "issue78-r0-warning-first-whole-per-market.csv", whole_market)
    write_csv(out / "issue78-r0-warning-first-whole-universal.csv", whole_universal)
    write_csv(out / "issue78-r0-warning-first-whole-comparisons.csv", comparisons)
    write_csv(out / "issue78-r0-warning-first-episode-universal.csv", episode_universal)
    write_csv(out / "issue78-r0-warning-first-temporal.csv", temporal)
    write_csv(out / "issue78-r0-warning-first-direction.csv", direction)
    write_csv(out / "issue78-r0-warning-first-slices.csv", slices)
    write_csv(out / "issue78-r0-warning-first-promotion-per-market.csv", promo_market)
    write_csv(out / "issue78-r0-warning-first-promotion-universal.csv", promo_universal)
    write_csv(out / "issue78-r0-warning-first-tail-per-market.csv", tail_market)
    write_csv(out / "issue78-r0-warning-first-tail-universal.csv", tail_universal)

    print("events", len(events))
    print("episodes", len(episodes))
    print("B3 events", len(paths_frame))
    print("P1/P2", p12_n)
    print("reconstruction_error", reconstruction_error)
    print("path_stats", path_stats)
    print("wrote", out)


if __name__ == "__main__":
    main()
