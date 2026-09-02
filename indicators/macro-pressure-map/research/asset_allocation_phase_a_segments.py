#!/usr/bin/env python3
"""Issue #64 Phase A stability split: pre-2020 development vs post-2019 reused exploratory."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from asset_allocation_phase_a import REGIMES, summarize_forward_returns
from asset_allocation_phase_a_frozen import load_frozen_transitions, map_regimes_to_outcome_calendar
from asset_allocation_relative import PAIRS, summarize_relative_returns
from issue_64_outcome_snapshot import load_frozen_prices

DEVELOPMENT_START = pd.Timestamp("2007-01-04")
DEVELOPMENT_END = pd.Timestamp("2019-12-31")
EXPLORATORY_START = pd.Timestamp("2020-01-01")


def load_segment_prices(end: str | None = None) -> pd.DataFrame:
    """Load only the committed hash-verified Issue #64 outcome panel.

    Phase A segment evidence is durable evidence, so it must never silently fall
    back to a fresh Yahoo download on a later workflow rerun.
    """
    prices, manifest = load_frozen_prices("2007-01-01", end)
    if manifest.get("source_mode") != "committed_frozen_snapshot":
        raise RuntimeError("Phase A segment evidence requires the committed frozen outcome snapshot")
    return prices


def add_segment(frame: pd.DataFrame, name: str) -> pd.DataFrame:
    result = frame.copy()
    result.insert(0, "segment", name)
    return result


def leader_table(inference: pd.DataFrame, segment: str) -> pd.DataFrame:
    rows: list[dict] = []
    for (regime, horizon), block in inference.groupby(["regime", "horizon"], sort=False):
        clean = block.dropna(subset=["embargoed_mean_forward_return"])
        if clean.empty:
            continue
        best = clean.sort_values("embargoed_mean_forward_return", ascending=False).iloc[0]
        rows.append({
            "segment": segment,
            "regime": regime,
            "horizon": horizon,
            "leader_asset": best["asset"],
            "leader_embargoed_mean_return": float(best["embargoed_mean_forward_return"]),
            "leader_embargoed_observations": int(best["embargoed_observations"]),
        })
    return pd.DataFrame(rows)


def segment_frames(
    prices: pd.DataFrame,
    history: pd.DataFrame,
    *,
    start: pd.Timestamp,
    end: pd.Timestamp | None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    mask = prices.index >= start
    if end is not None:
        mask &= prices.index <= end
    segment_prices = prices.loc[mask].copy()
    segment_history = history.reindex(segment_prices.index).copy()
    return segment_prices, segment_history


def build_relative_stability(relative: pd.DataFrame) -> pd.DataFrame:
    dev = relative.loc[relative["segment"].eq("development_pre2020")].copy()
    post = relative.loc[relative["segment"].eq("post2019_reused_exploratory")].copy()
    keys = ["regime", "horizon", "asset_a", "asset_b"]
    joined = dev.merge(post, on=keys, suffixes=("_dev", "_post"), how="outer", validate="one_to_one")
    rows: list[dict] = []
    for row in joined.itertuples(index=False):
        dev_mean = getattr(row, "embargoed_mean_return_spread_dev")
        post_mean = getattr(row, "embargoed_mean_return_spread_post")
        dev_sign = 0 if pd.isna(dev_mean) or dev_mean == 0 else int(np.sign(dev_mean))
        post_sign = 0 if pd.isna(post_mean) or post_mean == 0 else int(np.sign(post_mean))
        rows.append({
            "regime": row.regime,
            "horizon": row.horizon,
            "asset_a": row.asset_a,
            "asset_b": row.asset_b,
            "development_mean_spread": dev_mean,
            "development_ci_low": getattr(row, "mean_spread_ci95_low_dev"),
            "development_ci_high": getattr(row, "mean_spread_ci95_high_dev"),
            "development_n": getattr(row, "embargoed_observations_dev"),
            "post2019_mean_spread": post_mean,
            "post2019_ci_low": getattr(row, "mean_spread_ci95_low_post"),
            "post2019_ci_high": getattr(row, "mean_spread_ci95_high_post"),
            "post2019_n": getattr(row, "embargoed_observations_post"),
            "same_point_sign": bool(dev_sign != 0 and dev_sign == post_sign),
            "both_intervals_exclude_zero_same_direction": bool(
                getattr(row, "ci_excludes_zero_dev")
                and getattr(row, "ci_excludes_zero_post")
                and dev_sign != 0
                and dev_sign == post_sign
            ),
        })
    return pd.DataFrame(rows)


def run(output_dir: Path, end: str | None = None) -> None:
    prices = load_segment_prices(end)
    prices.index = pd.DatetimeIndex(prices.index).astype("datetime64[ns]")
    history = map_regimes_to_outcome_calendar(prices, load_frozen_transitions())

    all_inf: list[pd.DataFrame] = []
    all_rel: list[pd.DataFrame] = []
    leaders: list[pd.DataFrame] = []
    specs = (
        ("development_pre2020", DEVELOPMENT_START, DEVELOPMENT_END),
        ("post2019_reused_exploratory", EXPLORATORY_START, None),
    )
    for name, start, finish in specs:
        segment_prices, segment_history = segment_frames(
            prices, history, start=start, end=finish
        )
        _, inference = summarize_forward_returns(segment_history, segment_prices)
        relative = summarize_relative_returns(segment_history, segment_prices)
        all_inf.append(add_segment(inference, name))
        all_rel.append(add_segment(relative, name))
        leaders.append(leader_table(inference, name))

    inference_all = pd.concat(all_inf, ignore_index=True)
    relative_all = pd.concat(all_rel, ignore_index=True)
    leader_all = pd.concat(leaders, ignore_index=True)
    dev_leaders = leader_all.loc[leader_all["segment"].eq("development_pre2020")]
    post_leaders = leader_all.loc[leader_all["segment"].eq("post2019_reused_exploratory")]
    leader_stability = dev_leaders.merge(
        post_leaders,
        on=["regime", "horizon"],
        suffixes=("_dev", "_post"),
        how="outer",
        validate="one_to_one",
    )
    leader_stability["same_leader"] = (
        leader_stability["leader_asset_dev"] == leader_stability["leader_asset_post"]
    )
    relative_stability = build_relative_stability(relative_all)

    output_dir.mkdir(parents=True, exist_ok=True)
    inference_all.to_csv(output_dir / "phase-a-segment-forward-inference.csv", index=False)
    relative_all.to_csv(output_dir / "phase-a-segment-relative-returns.csv", index=False)
    leader_stability.to_csv(output_dir / "phase-a-segment-leader-stability.csv", index=False)
    relative_stability.to_csv(output_dir / "phase-a-segment-relative-stability.csv", index=False)

    print(
        f"leader comparisons={len(leader_stability)} same={int(leader_stability['same_leader'].sum())}; "
        f"relative comparisons={len(relative_stability)} same-sign={int(relative_stability['same_point_sign'].sum())}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Issue #64 Phase A pre/post-2020 stability diagnostic")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--end", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run(args.output_dir, args.end)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
