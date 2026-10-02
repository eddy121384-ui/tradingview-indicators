#!/usr/bin/env python3
"""Issue #78 equity Trendability / broad-oscillation autopsy.

Post-outcome mechanism diagnostic on the already-inspected OOS3 cohort.
No policy thresholds are tuned or selected here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

import analyze_issue78_bbg_equity_oos2 as base
import analyze_issue78_equity_proof_policy_oos3 as policy
import analyze_issue78_retest_path_stage1 as retest
import analyze_issue78_second_entry_economic_policy as second
from audit_issue119_bbg_oos2_snapshot import audit_snapshot
from smoke_issue119_frozen_classifier import (
    FROZEN_CLASSIFIER_BLOB,
    load_classifier,
)

EXPECTED_UNIVERSE_SHA = (
    "9d4a14d163ed308238737647b94e722c62fd023b641e1015e6d97679f9ba3b44"
)
EXPECTED_FIGI_SET_SHA = (
    "017e9360402afa002dc0970088649e7c411c4f02333dec550f2432be3c0dd701"
)

ER_HORIZONS = (63, 126, 252)
RANK_LEN = 756
WIDTH_HORIZON = 252

BUCKETS = ("Low", "Neutral", "High")
WIDTH_BUCKETS = ("Narrow", "Medium", "Wide")
ROBUST_ERAS = ("2010-2014", "2015-2019", "2020-2026")


class Fenwick:
    def __init__(self, n: int):
        self.n = int(n)
        self.tree = [0] * (self.n + 1)

    def add(self, idx: int, delta: int) -> None:
        i = int(idx) + 1
        while i <= self.n:
            self.tree[i] += int(delta)
            i += i & -i

    def prefix(self, idx: int) -> int:
        if idx < 0:
            return 0
        total = 0
        i = int(idx) + 1
        while i > 0:
            total += self.tree[i]
            i -= i & -i
        return total


def pine_previous_percentrank(values, length=RANK_LEN):
    """Percent rank against the previous length values, excluding current."""
    arr = np.asarray(values, dtype=float)
    out = np.full(len(arr), np.nan, dtype=float)

    finite_vals = arr[np.isfinite(arr)]
    if len(finite_vals) == 0:
        return out

    coords = np.unique(finite_vals)
    fw = Fenwick(len(coords))
    finite_count = 0

    def coord(v):
        return int(np.searchsorted(coords, v, side="left"))

    for t in range(len(arr)):
        if t > 0 and np.isfinite(arr[t - 1]):
            fw.add(coord(arr[t - 1]), 1)
            finite_count += 1

        old = t - length - 1
        if old >= 0 and np.isfinite(arr[old]):
            fw.add(coord(arr[old]), -1)
            finite_count -= 1

        if (
            t >= length
            and finite_count == length
            and np.isfinite(arr[t])
        ):
            hi = int(np.searchsorted(coords, arr[t], side="right") - 1)
            out[t] = 100.0 * fw.prefix(hi) / length

    return out


def rolling_er(src, length):
    s = pd.Series(np.asarray(src, dtype=float))
    path = s.diff().abs().rolling(length, min_periods=length).sum()
    displacement = (s - s.shift(length)).abs()
    out = displacement / path.replace(0.0, np.nan)
    return out.to_numpy(float)


def figi_set_sha(universe: pd.DataFrame) -> str:
    figis = sorted(universe["figi"].astype(str).tolist())
    payload = "\n".join(figis) + "\n"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def bucket_score(x):
    if not math.isfinite(float(x)):
        return None
    if x < 33.33:
        return "Low"
    if x <= 66.67:
        return "Neutral"
    return "High"


def width_bucket(x):
    if not math.isfinite(float(x)):
        return None
    if x < 33.33:
        return "Narrow"
    if x <= 66.67:
        return "Medium"
    return "Wide"


def add_context(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    src = pd.to_numeric(out["close_coord"], errors="coerce").to_numpy(float)

    ranks = []
    for horizon in ER_HORIZONS:
        er = rolling_er(src, horizon)
        rank = pine_previous_percentrank(er, RANK_LEN)
        out[f"er{horizon}"] = er
        out[f"er{horizon}_rank"] = rank
        ranks.append(rank)

    rank_matrix = np.column_stack(ranks)
    valid = np.isfinite(rank_matrix).all(axis=1)
    trend = np.full(len(out), np.nan)
    trend[valid] = rank_matrix[valid].mean(axis=1)
    out["trendability"] = trend

    high = pd.to_numeric(
        out["high_coord"], errors="coerce"
    ).rolling(WIDTH_HORIZON, min_periods=WIDTH_HORIZON).max()
    low = pd.to_numeric(
        out["low_coord"], errors="coerce"
    ).rolling(WIDTH_HORIZON, min_periods=WIDTH_HORIZON).min()
    scale = pd.to_numeric(out["scale"], errors="coerce")
    width = (high - low) / scale.where(scale > 0)
    out["range_width_252_atr"] = width
    out["range_width_rank"] = pine_previous_percentrank(
        width.to_numpy(float), RANK_LEN
    )

    out["trend_bucket"] = [
        bucket_score(x) for x in out["trendability"]
    ]
    out["width_bucket"] = [
        width_bucket(x) for x in out["range_width_rank"]
    ]
    return out


def episode_context_records(
    episodes,
    frames,
    state_map,
    time_index,
    metadata,
):
    rows = []
    missing_context = 0

    for episode in episodes:
        figi, stage, episode_id, start, records = episode
        frame = frames[figi]
        entry = frame.iloc[int(start)]

        trend = float(entry["trendability"])
        width_rank_value = float(entry["range_width_rank"])
        tb = entry["trend_bucket"]
        wb = entry["width_bucket"]
        if (
            not math.isfinite(trend)
            or not math.isfinite(width_rank_value)
            or tb not in BUCKETS
            or wb not in WIDTH_BUCKETS
        ):
            missing_context += 1
            continue

        state = state_map.get((figi, episode_id))
        levels = (
            second.frozen_levels(
                episode, state, frames, time_index
            )
            if state is not None
            else None
        )
        path = state["path"] if state is not None else "NoUsableB3"
        bad_structure = int(
            path in ("NoUsableB3", "P3_FailedAcceptance")
        )

        steps = second.aligned_steps(episode)
        mfe = second.episode_mfe(steps)
        entry_date = pd.Timestamp(records[0]["date"])

        for pol in policy.POLICIES:
            _, _, actual, returns, _ = policy.simulate_policy(
                pol, episode, state, levels, frames
            )
            rows.append(
                {
                    **metadata[figi],
                    "episode_id": int(episode_id),
                    "entry_date": str(entry_date.date()),
                    "era": base.block_name(entry_date),
                    "direction": "Markup" if stage == 2 else "Markdown",
                    "path": path,
                    "bad_structure": bad_structure,
                    "mfe": float(mfe),
                    "mfe_lt4": int(mfe < 4.0),
                    "mfe_ge8": int(mfe >= 8.0),
                    "trendability": trend,
                    "trend_bucket": str(tb),
                    "er63": float(entry["er63"]),
                    "er126": float(entry["er126"]),
                    "er252": float(entry["er252"]),
                    "er63_rank": float(entry["er63_rank"]),
                    "er126_rank": float(entry["er126_rank"]),
                    "er252_rank": float(entry["er252_rank"]),
                    "range_width_252_atr": float(
                        entry["range_width_252_atr"]
                    ),
                    "range_width_rank": width_rank_value,
                    "width_bucket": str(wb),
                    "broad_oscillation": int(
                        tb == "Low" and wb == "Wide"
                    ),
                    "narrow_oscillation": int(
                        tb == "Low" and wb == "Narrow"
                    ),
                    "policy": pol,
                    "harvest": float(sum(returns)),
                    "avg_exposure": base.mean(actual),
                }
            )

    return pd.DataFrame(rows), missing_context


def summarize_equal_stock(records, group_cols):
    rows = []
    grouped = records.groupby([*group_cols, "figi", "policy"])
    stock_rows = []

    for keys, g in grouped:
        if not isinstance(keys, tuple):
            keys = (keys,)
        names = [*group_cols, "figi", "policy"]
        row = dict(zip(names, keys))
        row.update(
            {
                "episodes": int(g["episode_id"].nunique()),
                "mean_harvest": float(g["harvest"].mean()),
                "mfe_lt4_share": float(g["mfe_lt4"].mean()),
                "mfe_ge8_share": float(g["mfe_ge8"].mean()),
                "bad_structure_share": float(
                    g["bad_structure"].mean()
                ),
                "median_trendability": float(
                    g["trendability"].median()
                ),
                "median_range_width_rank": float(
                    g["range_width_rank"].median()
                ),
            }
        )
        stock_rows.append(row)

    stock = pd.DataFrame(stock_rows)
    if stock.empty:
        return stock, pd.DataFrame()

    for keys, g in stock.groupby([*group_cols, "policy"]):
        if not isinstance(keys, tuple):
            keys = (keys,)
        names = [*group_cols, "policy"]
        vals = g["mean_harvest"].to_numpy(float)
        rows.append(
            {
                **dict(zip(names, keys)),
                "stocks": int(g["figi"].nunique()),
                "episodes": int(g["episodes"].sum()),
                "equal_stock_mean_harvest": float(np.mean(vals)),
                "median_stock_harvest": float(np.median(vals)),
                "positive_stock_fraction": float(np.mean(vals > 0)),
                "equal_stock_mfe_lt4_share": float(
                    g["mfe_lt4_share"].mean()
                ),
                "equal_stock_mfe_ge8_share": float(
                    g["mfe_ge8_share"].mean()
                ),
                "equal_stock_bad_structure_share": float(
                    g["bad_structure_share"].mean()
                ),
                "equal_stock_median_trendability": float(
                    g["median_trendability"].mean()
                ),
                "equal_stock_median_range_width_rank": float(
                    g["median_range_width_rank"].mean()
                ),
            }
        )

    return stock, pd.DataFrame(rows)


def pick(summary, policy_name, **filters):
    work = summary[summary["policy"] == policy_name]
    for col, value in filters.items():
        work = work[work[col] == value]
    if len(work) != 1:
        return None
    return work.iloc[0].to_dict()


def support_checks(trend_summary, grid_summary, era_summary):
    r0 = "R0_NoDerisk"
    low = pick(trend_summary, r0, trend_bucket="Low")
    neutral = pick(trend_summary, r0, trend_bucket="Neutral")
    high = pick(trend_summary, r0, trend_bucket="High")

    low_narrow = pick(
        grid_summary,
        r0,
        trend_bucket="Low",
        width_bucket="Narrow",
    )
    low_medium = pick(
        grid_summary,
        r0,
        trend_bucket="Low",
        width_bucket="Medium",
    )
    low_wide = pick(
        grid_summary,
        r0,
        trend_bucket="Low",
        width_bucket="Wide",
    )

    checks = {
        "trend_monotonic_expectancy_low_lt_neutral_lt_high": False,
        "low_has_more_mfe_lt4_than_high": False,
        "low_has_more_bad_structure_than_high": False,
        "low_wide_worse_than_low_narrow": False,
        "low_wide_worse_than_low_medium": False,
        "low_vs_high_negative_in_at_least_2_of_3_robust_eras": False,
    }

    if low and neutral and high:
        checks[
            "trend_monotonic_expectancy_low_lt_neutral_lt_high"
        ] = bool(
            low["equal_stock_mean_harvest"]
            < neutral["equal_stock_mean_harvest"]
            < high["equal_stock_mean_harvest"]
        )
        checks["low_has_more_mfe_lt4_than_high"] = bool(
            low["equal_stock_mfe_lt4_share"]
            > high["equal_stock_mfe_lt4_share"]
        )
        checks["low_has_more_bad_structure_than_high"] = bool(
            low["equal_stock_bad_structure_share"]
            > high["equal_stock_bad_structure_share"]
        )

    if low_wide and low_narrow:
        checks["low_wide_worse_than_low_narrow"] = bool(
            low_wide["equal_stock_mean_harvest"]
            < low_narrow["equal_stock_mean_harvest"]
        )
    if low_wide and low_medium:
        checks["low_wide_worse_than_low_medium"] = bool(
            low_wide["equal_stock_mean_harvest"]
            < low_medium["equal_stock_mean_harvest"]
        )

    era_signs = 0
    for era in ROBUST_ERAS:
        lo = pick(
            era_summary,
            r0,
            era=era,
            trend_bucket="Low",
        )
        hi = pick(
            era_summary,
            r0,
            era=era,
            trend_bucket="High",
        )
        if (
            lo
            and hi
            and lo["equal_stock_mean_harvest"]
            < hi["equal_stock_mean_harvest"]
        ):
            era_signs += 1
    checks[
        "low_vs_high_negative_in_at_least_2_of_3_robust_eras"
    ] = era_signs >= 2

    checks["broad_oscillation_story_structurally_supported"] = bool(
        all(
            value
            for key, value in checks.items()
            if key != "robust_era_sign_count"
        )
    )
    checks["robust_era_sign_count"] = era_signs
    return checks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--raw-dir", type=Path, required=True)
    ap.add_argument(
        "--classifier",
        type=Path,
        default=Path("generated/wyckoff-issue78-rc-python.py"),
    )
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    audit = audit_snapshot(
        args.universe, args.manifest, args.raw_dir
    )
    if not audit["pass"]:
        raise SystemExit("OOS3 snapshot audit failed")
    universe = pd.read_csv(args.universe)
    if len(universe) != 300 or universe["figi"].nunique() != 300:
        raise AssertionError("OOS3 universe membership drift")
    cohort_sha = figi_set_sha(universe)
    if cohort_sha != EXPECTED_FIGI_SET_SHA:
        raise AssertionError(
            f"OOS3 FIGI-set drift: {cohort_sha}"
        )

    # The original frozen manifest byte SHA is preferred when available.
    # A recovery manifest reconstructed from the already-completed OOS3
    # coverage.csv is accepted only when the exact 300-FIGI set matches the
    # pre-recorded cohort identity above.
    original_manifest_bytes = (
        audit["universe_sha256_actual"] == EXPECTED_UNIVERSE_SHA
    )

    classifier, blob = load_classifier(args.classifier)
    if blob != FROZEN_CLASSIFIER_BLOB:
        raise AssertionError("frozen classifier blob drift")

    frames, episodes, coverage, metadata = base.build_research_set(
        universe, args.raw_dir, classifier
    )

    for figi in list(frames):
        frames[figi] = add_context(frames[figi])

    paths_frame, path_stats = retest.build_paths(frames, episodes)
    state_map = second.build_state_map(paths_frame)
    time_index = second.frame_time_index(frames)

    records, missing_context = episode_context_records(
        episodes, frames, state_map, time_index, metadata
    )
    if records.empty:
        raise AssertionError("no context-eligible episodes")

    context_eps = int(
        records[["figi", "episode_id"]].drop_duplicates().shape[0]
    )
    context_coverage = context_eps / len(episodes)

    trend_stock, trend_summary = summarize_equal_stock(
        records, ["trend_bucket"]
    )
    grid_stock, grid_summary = summarize_equal_stock(
        records, ["trend_bucket", "width_bucket"]
    )
    era_stock, era_summary = summarize_equal_stock(
        records, ["era", "trend_bucket"]
    )
    direction_stock, direction_summary = summarize_equal_stock(
        records, ["direction", "trend_bucket"]
    )
    sleeve_stock, sleeve_summary = summarize_equal_stock(
        records, ["sleeve", "trend_bucket"]
    )

    checks = support_checks(
        trend_summary, grid_summary, era_summary
    )

    r0_trend = trend_summary[
        trend_summary["policy"] == "R0_NoDerisk"
    ].to_dict("records")
    r0_grid = grid_summary[
        grid_summary["policy"] == "R0_NoDerisk"
    ].to_dict("records")

    summary = {
        "integrity": {
            "issue": 78,
            "study": "Equity Trendability / broad-oscillation autopsy",
            "role": "post-outcome mechanism diagnostic; not policy OOS",
            "classifier_blob": blob,
            "universe_sha256": audit["universe_sha256_actual"],
            "original_frozen_universe_bytes": original_manifest_bytes,
            "figi_set_sha256": cohort_sha,
            "stocks_in_universe": int(len(universe)),
            "completed_eligible_episodes": int(len(episodes)),
            "context_eligible_episodes": context_eps,
            "context_missing_episodes": int(missing_context),
            "context_coverage": float(context_coverage),
            "path_stats": path_stats,
            "trendability_horizons": list(ER_HORIZONS),
            "rank_len": RANK_LEN,
            "width_horizon": WIDTH_HORIZON,
            "bucket_cutoffs": [33.33, 66.67],
        },
        "r0_trendability": r0_trend,
        "r0_trend_width_grid": r0_grid,
        "support_checks": checks,
        "notes": [
            "This cohort's strategy outcomes were already inspected before this diagnostic.",
            "Trendability horizons and bucket thresholds were inherited from the earlier frozen Issue #78 trendability preregistration.",
            "Low Trendability + Wide range is the preregistered proxy for broad oscillation / a large box.",
            "No production filter is validated by this diagnostic.",
        ],
    }

    args.out.mkdir(parents=True, exist_ok=True)
    base.write_csv(args.out / "coverage.csv", coverage)
    base.write_csv(args.out / "episode_context_policy.csv", records)
    base.write_csv(args.out / "trendability_per_stock.csv", trend_stock)
    base.write_csv(args.out / "trendability_summary.csv", trend_summary)
    base.write_csv(
        args.out / "trend_width_grid_per_stock.csv", grid_stock
    )
    base.write_csv(
        args.out / "trend_width_grid_summary.csv", grid_summary
    )
    base.write_csv(args.out / "era_trend_per_stock.csv", era_stock)
    base.write_csv(args.out / "era_trend_summary.csv", era_summary)
    base.write_csv(
        args.out / "direction_trend_per_stock.csv",
        direction_stock,
    )
    base.write_csv(
        args.out / "direction_trend_summary.csv",
        direction_summary,
    )
    base.write_csv(
        args.out / "sleeve_trend_per_stock.csv",
        sleeve_stock,
    )
    base.write_csv(
        args.out / "sleeve_trend_summary.csv",
        sleeve_summary,
    )
    (args.out / "summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
