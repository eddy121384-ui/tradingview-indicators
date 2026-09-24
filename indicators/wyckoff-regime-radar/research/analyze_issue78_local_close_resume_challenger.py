#!/usr/bin/env python3
"""Issue #78 local-close Resume challenger.

Compares the frozen R1 full favorable close extreme with one final definition-only
challenger: R5, the favorable CLOSE boundary of the frozen retest segment.

This script deliberately reuses the accepted Resume Trigger Stage 1 construction
rather than reimplementing the event sample.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

import analyze_issue78_resume_trigger_stage1 as base

EXPECTED_EVENTS = 68118
EXPECTED_EPISODES = 1624
EXPECTED_CANDIDATES = 236
RULES = ("R1_CloseExtreme", "R5_LocalClose")


def build_events(frames: dict[str, pd.DataFrame], candidates: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for _, row in candidates.iterrows():
        frame = frames[row.ticker]
        episode_start = int(row.episode_start_idx)
        episode_end = episode_start + int(row.episode_len) - 1
        direction = int(row.direction)
        scale = float(row.scale)
        t3 = int(row.t3_global_idx)
        t3_close = float(row.t3_close)
        breakout_idx = int(row.break_global_idx)

        first_touch = int(row.first_touch_bar)
        retest_start = breakout_idx + first_touch
        retest_segment = frame.iloc[retest_start:t3 + 1]

        if direction == 1:
            r5_anchor = float(retest_segment.close_coord.max())
        else:
            r5_anchor = float(retest_segment.close_coord.min())

        episode_future = frame.iloc[t3:episode_end + 1]
        if direction == 1:
            best_future_close = float(episode_future.close_coord.max())
            available = max(0.0, best_future_close - t3_close)
        else:
            best_future_close = float(episode_future.close_coord.min())
            available = max(0.0, t3_close - best_future_close)

        anchors = {
            "R1_CloseExtreme": float(row.close_anchor),
            "R5_LocalClose": r5_anchor,
        }

        for rule, anchor in anchors.items():
            trigger_idx = None
            for idx in range(t3 + 1, episode_end + 1):
                close = float(frame.iloc[idx].close_coord)
                hit = close > anchor if direction == 1 else close < anchor
                if hit:
                    trigger_idx = idx
                    break

            common = {
                "ticker": row.ticker,
                "stage": row.stage,
                "era": row.era,
                "episode_id": int(row.episode_id),
                "path": row.path,
                "rule": rule,
                "anchor": anchor,
                "triggered": int(trigger_idx is not None),
            }

            if trigger_idx is None:
                rows.append({
                    **common,
                    "delay": math.nan,
                    "trigger_close_progress_atr": math.nan,
                    "tax_fraction": math.nan,
                    "remaining_life": math.nan,
                    "remaining10": math.nan,
                    "remaining20": math.nan,
                    "reexpand5": math.nan,
                    "reexpand10": math.nan,
                    "oldbox_fail3": math.nan,
                })
                continue

            trigger = frame.iloc[trigger_idx]
            trigger_close = float(trigger.close_coord)
            delay = trigger_idx - t3
            remaining = episode_end - trigger_idx
            close_progress = max(0.0, direction * (trigger_close - t3_close)) / scale
            tax_fraction = (
                max(0.0, direction * (trigger_close - t3_close)) / available
                if available > 1e-15
                else math.nan
            )

            f3 = frame.iloc[trigger_idx + 1:min(trigger_idx + 4, episode_end + 1)]
            f5 = frame.iloc[trigger_idx + 1:min(trigger_idx + 6, episode_end + 1)]
            f10 = frame.iloc[trigger_idx + 1:min(trigger_idx + 11, episode_end + 1)]
            known = frame.iloc[breakout_idx:trigger_idx + 1]

            if direction == 1:
                known_best = float(known.high_coord.max())
                reexpand5 = (
                    int(len(f5) == 5 and float(f5.high_coord.max()) > known_best + 1e-12)
                    if len(f5) == 5 else math.nan
                )
                reexpand10 = (
                    int(len(f10) == 10 and float(f10.high_coord.max()) > known_best + 1e-12)
                    if len(f10) == 10 else math.nan
                )
                oldbox_fail3 = (
                    int(len(f3) > 0 and np.any(f3.close_coord.to_numpy(float) <= float(row.box_high)))
                    if len(f3) > 0 else math.nan
                )
            else:
                known_best = float(known.low_coord.min())
                reexpand5 = (
                    int(len(f5) == 5 and float(f5.low_coord.min()) < known_best - 1e-12)
                    if len(f5) == 5 else math.nan
                )
                reexpand10 = (
                    int(len(f10) == 10 and float(f10.low_coord.min()) < known_best - 1e-12)
                    if len(f10) == 10 else math.nan
                )
                oldbox_fail3 = (
                    int(len(f3) > 0 and np.any(f3.close_coord.to_numpy(float) >= float(row.box_low)))
                    if len(f3) > 0 else math.nan
                )

            rows.append({
                **common,
                "delay": delay,
                "trigger_close_progress_atr": close_progress,
                "tax_fraction": tax_fraction,
                "remaining_life": remaining,
                "remaining10": int(remaining >= 10),
                "remaining20": int(remaining >= 20),
                "reexpand5": reexpand5,
                "reexpand10": reexpand10,
                "oldbox_fail3": oldbox_fail3,
            })

    return pd.DataFrame(rows)


def summarize(events: pd.DataFrame, extra_cols: tuple[str, ...] = ()) -> tuple[pd.DataFrame, pd.DataFrame]:
    market_rows: list[dict[str, object]] = []
    group_cols = [*extra_cols, "ticker", "rule"]

    for keys, group in events.groupby(group_cols):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(group_cols, keys))
        row["n"] = group.episode_id.nunique()
        row["trigger_rate"] = group.triggered.mean()
        row["no_trigger_rate"] = 1.0 - row["trigger_rate"]

        triggered = group[group.triggered == 1]
        row["delay_median"] = triggered.delay.median()
        row["delay_mean"] = triggered.delay.mean()
        for horizon in (3, 5, 10):
            row[f"trigger_le_{horizon}_rate_all"] = (
                (group.triggered == 1) & (group.delay <= horizon)
            ).mean()

        row["close_progress_atr_mean"] = triggered.trigger_close_progress_atr.mean()
        row["tax_fraction_median"] = triggered.tax_fraction.median()
        row["tax_fraction_mean"] = triggered.tax_fraction.mean()
        row["remaining_life_mean"] = triggered.remaining_life.mean()
        row["remaining10_rate"] = triggered.remaining10.mean()
        row["remaining20_rate"] = triggered.remaining20.mean()
        row["reexpand5_rate"] = triggered.reexpand5.mean()
        row["reexpand10_rate"] = triggered.reexpand10.mean()
        row["oldbox_fail3_rate"] = triggered.oldbox_fail3.mean()
        market_rows.append(row)

    market = pd.DataFrame(market_rows)
    summary_rows: list[dict[str, object]] = []
    summary_group_cols = [*extra_cols, "rule"]

    metrics = (
        "trigger_rate", "no_trigger_rate", "delay_median", "delay_mean",
        "trigger_le_3_rate_all", "trigger_le_5_rate_all", "trigger_le_10_rate_all",
        "close_progress_atr_mean", "tax_fraction_median", "tax_fraction_mean",
        "remaining_life_mean", "remaining10_rate", "remaining20_rate",
        "reexpand5_rate", "reexpand10_rate", "oldbox_fail3_rate",
    )

    for keys, group in market.groupby(summary_group_cols):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(summary_group_cols, keys))
        row["markets"] = group.ticker.nunique()
        row["pooled_n"] = int(group.n.sum())
        for metric in metrics:
            row[f"{metric}_eq_market"] = group[metric].mean()
        summary_rows.append(row)

    return market, pd.DataFrame(summary_rows)


def paired(events: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, object]] = []

    for (ticker, episode_id, path), group in events.groupby(["ticker", "episode_id", "path"]):
        r5 = group[group.rule == "R5_LocalClose"]
        r1 = group[group.rule == "R1_CloseExtreme"]
        if (
            len(r5) != 1
            or len(r1) != 1
            or int(r5.iloc[0].triggered) != 1
            or int(r1.iloc[0].triggered) != 1
        ):
            continue

        a = r5.iloc[0]
        b = r1.iloc[0]
        rows.append({
            "ticker": ticker,
            "episode_id": episode_id,
            "path": path,
            "delay_delta": a.delay - b.delay,
            "tax_delta": a.tax_fraction - b.tax_fraction,
            "remaining_life_delta": a.remaining_life - b.remaining_life,
            "reexpand5_delta": (
                a.reexpand5 - b.reexpand5
                if pd.notna(a.reexpand5) and pd.notna(b.reexpand5)
                else math.nan
            ),
            "reexpand10_delta": (
                a.reexpand10 - b.reexpand10
                if pd.notna(a.reexpand10) and pd.notna(b.reexpand10)
                else math.nan
            ),
            "oldbox_fail3_delta": (
                a.oldbox_fail3 - b.oldbox_fail3
                if pd.notna(a.oldbox_fail3) and pd.notna(b.oldbox_fail3)
                else math.nan
            ),
        })

    paired_events = pd.DataFrame(rows)
    market_rows = []
    metrics = (
        "delay_delta", "tax_delta", "remaining_life_delta",
        "reexpand5_delta", "reexpand10_delta", "oldbox_fail3_delta",
    )

    for ticker, group in paired_events.groupby("ticker"):
        market_rows.append({
            "ticker": ticker,
            "n": len(group),
            **{metric: group[metric].mean() for metric in metrics},
        })

    market = pd.DataFrame(market_rows)
    universal = {
        "a": "R5_LocalClose",
        "b": "R1_CloseExtreme",
        "markets": market.ticker.nunique(),
        "paired_n": len(paired_events),
    }
    for metric in metrics:
        universal[f"{metric}_eq_market"] = market[metric].mean()

    return paired_events, market, pd.DataFrame([universal])


def main() -> None:
    paths = sorted(base.glob.glob("/mnt/data/pine-logs-#76 Forward Logger*.csv"))
    raw_events = base.read_events(paths)
    assert len(raw_events) == EXPECTED_EVENTS, len(raw_events)

    frames, reconstruction_error = base.reconstruct(raw_events)
    episodes = base.build_episodes(frames)
    assert len(episodes) == EXPECTED_EPISODES, len(episodes)

    candidates, stats = base.build_candidates(frames, episodes)
    assert len(candidates) == EXPECTED_CANDIDATES, len(candidates)

    events = build_events(frames, candidates)

    out = Path("/mnt/data/issue78-local-close-resume")
    out.mkdir(parents=True, exist_ok=True)

    events.to_csv(out / "issue78-local-close-resume-events.csv", index=False)

    market, universal = summarize(events)
    market.to_csv(out / "issue78-local-close-resume-per-market.csv", index=False)
    universal.to_csv(out / "issue78-local-close-resume-universal.csv", index=False)

    for extra, label in (
        (("path",), "by-path"),
        (("era",), "temporal"),
        (("stage",), "direction"),
    ):
        _, table = summarize(events, extra)
        table.to_csv(out / f"issue78-local-close-resume-{label}.csv", index=False)

    paired_events, paired_market, paired_universal = paired(events)
    paired_events.to_csv(out / "issue78-local-close-resume-paired-events.csv", index=False)
    paired_market.to_csv(out / "issue78-local-close-resume-paired-per-market.csv", index=False)
    paired_universal.to_csv(out / "issue78-local-close-resume-paired-universal.csv", index=False)

    print("events", len(raw_events))
    print("episodes", len(episodes))
    print("candidates", len(candidates))
    print("reconstruction_error", reconstruction_error)
    print("candidate_stats", stats)


if __name__ == "__main__":
    main()
