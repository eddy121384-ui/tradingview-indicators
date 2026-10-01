#!/usr/bin/env python3
"""Issue #78 untouched-equity OOS3 proof-policy validation.

The cohort, proof thresholds, exposure states, WarningFirst semantics and
interpretation gates are frozen before this analyzer's first economic run.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

import analyze_issue78_bbg_equity_oos2 as base
import analyze_issue78_retest_path_stage1 as retest
import analyze_issue78_second_entry_economic_policy as second
import analyze_issue78_r0_warning_first_composition as comp
from audit_issue119_bbg_oos2_snapshot import audit_snapshot
from smoke_issue119_frozen_classifier import (
    FROZEN_CLASSIFIER_BLOB,
    load_classifier,
)

EXPECTED_UNIVERSE_SHA = (
    "9d4a14d163ed308238737647b94e722c62fd023b641e1015e6d97679f9ba3b44"
)

POLICIES = (
    "R0_NoDerisk",
    "R0_WarningFirst",
    "Proof1_NoDerisk",
    "Proof1_WarningFirst",
    "ProgressiveProof_NoDerisk",
    "ProgressiveProof_WarningFirst",
)

PAIR_MAP = {
    "R0": ("R0_NoDerisk", "R0_WarningFirst"),
    "Proof1": ("Proof1_NoDerisk", "Proof1_WarningFirst"),
    "ProgressiveProof": (
        "ProgressiveProof_NoDerisk",
        "ProgressiveProof_WarningFirst",
    ),
}


def proof_earned_exposures(steps, mode):
    """Causal proof participation path; threshold crossing affects next move."""
    current = 0.25
    cum = 0.0
    exposures = []

    for step in steps:
        exposures.append(current)
        cum += float(step)

        if mode == "proof1":
            if cum >= 1.0:
                current = 1.0
        elif mode == "progressive":
            if cum >= 2.0:
                current = 1.0
            elif cum >= 1.0:
                current = 0.75
            elif cum >= 0.5:
                current = 0.50
            else:
                current = 0.25
        else:
            raise ValueError(mode)

    return exposures


def simulate_policy(policy, episode, state, levels, frames):
    steps = second.aligned_steps(episode)

    if policy.startswith("R0_"):
        earned, _ = second.exposures_for_episode(
            "R0_Immediate", episode, state, levels, frames
        )
    elif policy.startswith("Proof1_"):
        earned = proof_earned_exposures(steps, "proof1")
    elif policy.startswith("ProgressiveProof_"):
        earned = proof_earned_exposures(steps, "progressive")
    else:
        raise ValueError(policy)

    management = (
        "warning_first"
        if policy.endswith("_WarningFirst")
        else "none"
    )
    managed = comp.apply_management(
        steps,
        earned,
        management,
        promotion_local=None,
    )
    actual = managed["actual"]
    returns = [e * step for e, step in zip(actual, steps)]
    return steps, earned, actual, returns, managed


def episode_records(episodes, state_map, frames, time_index, metadata):
    rows = []

    for episode in episodes:
        figi, stage, episode_id, _, records = episode
        state = state_map.get((figi, episode_id))
        levels = (
            second.frozen_levels(
                episode, state, frames, time_index
            )
            if state is not None
            else None
        )
        steps = second.aligned_steps(episode)
        mfe = second.episode_mfe(steps)
        entry_date = pd.Timestamp(records[0]["date"])
        direction = "Markup" if stage == 2 else "Markdown"
        path = state["path"] if state is not None else "NoUsableB3"

        for policy in POLICIES:
            _, earned, actual, returns, managed = simulate_policy(
                policy, episode, state, levels, frames
            )
            rows.append(
                {
                    **metadata[figi],
                    "episode_id": int(episode_id),
                    "entry_date": str(entry_date.date()),
                    "block": base.block_name(entry_date),
                    "direction": direction,
                    "path": path,
                    "bars": len(records),
                    "mfe": mfe,
                    "policy": policy,
                    "harvest": float(sum(returns)),
                    "avg_exposure": base.mean(actual),
                    "turnover": second.path_turnover(actual),
                    "de_risk_count": int(managed["de_risk_count"]),
                    "re_risk_count": int(managed["re_risk_count"]),
                    "max_reduction": float(managed["max_reduction"]),
                }
            )
    return pd.DataFrame(rows)


def build_timelines(
    episodes,
    frames,
    state_map,
    time_index,
    metadata,
):
    by_eps = defaultdict(list)
    for ep in episodes:
        by_eps[ep[0]].append(ep)

    rows = []
    for figi, frame in frames.items():
        valid = (
            frame["valid_ohlc"]
            & frame["date"].between(base.EVENT_START, base.EVENT_END)
        )
        timeline = frame.loc[valid, ["event_time"]].copy()
        if len(timeline) < 2:
            continue
        times = timeline["event_time"].astype(np.int64).tolist()
        index = {int(t): i for i, t in enumerate(times)}

        for policy in POLICIES:
            rr = [0.0] * len(times)
            ee = [0.0] * len(times)
            for ep in by_eps.get(figi, []):
                state = state_map.get((figi, ep[2]))
                levels = (
                    second.frozen_levels(
                        ep, state, frames, time_index
                    )
                    if state is not None
                    else None
                )
                _, _, actual, returns, _ = simulate_policy(
                    policy, ep, state, levels, frames
                )
                for row, exposure, value in zip(
                    ep[4], actual, returns
                ):
                    t = int(row["event_time"])
                    if t not in index:
                        raise AssertionError(
                            f"{figi}: episode time absent from timeline"
                        )
                    i = index[t]
                    rr[i] = float(value)
                    ee[i] = float(exposure)

            rows.append(
                {
                    **metadata[figi],
                    "policy": policy,
                    **base.timeline_metrics(rr, ee),
                }
            )
    return pd.DataFrame(rows)


def policy_concentration(primary, policy):
    work = primary[primary["policy"] == policy].copy()
    positive = work[work["mean_expectancy"] > 0].sort_values(
        "mean_expectancy", ascending=False
    )
    denom = positive["mean_expectancy"].sum()
    if len(positive) and denom > 0:
        k = max(1, math.ceil(0.01 * len(positive)))
        share = float(
            positive.head(k)["mean_expectancy"].sum() / denom
        )
        remove_ids = set(positive.head(k)["figi"])
    else:
        k = 0
        share = math.nan
        remove_ids = set()

    remaining = work[~work["figi"].isin(remove_ids)]
    return {
        "positive_stocks": int(len(positive)),
        "top1pct_positive_stock_count": int(k),
        "top1pct_positive_contribution_share": share,
        "equal_stock_mean_after_removing_top1pct_positive": (
            base.mean(remaining["mean_expectancy"].tolist())
        ),
    }


def standalone_classification(
    policy,
    primary_summary,
    primary,
    temporal,
    sector,
):
    row = primary_summary[
        primary_summary["policy"] == policy
    ].iloc[0]
    concentration = policy_concentration(primary, policy)

    adequate_temporal = temporal[
        (temporal["policy"] == policy)
        & (temporal["adequate"] == 1)
    ]
    adequate_sector = sector[
        (sector["policy"] == policy)
        & (sector["adequate"] == 1)
    ]

    policy_primary = primary[primary["policy"] == policy]
    loo_positive = True
    for sec in sorted(policy_primary["sector"].unique()):
        remain = policy_primary[policy_primary["sector"] != sec]
        if not (
            len(remain)
            and base.mean(remain["mean_expectancy"].tolist()) > 0
        ):
            loo_positive = False
            break

    gates = {
        "mean_gt0": bool(row.equal_stock_mean_expectancy > 0),
        "median_gt0": bool(row.median_stock_expectancy > 0),
        "positive_stock_fraction_ge55pct": bool(
            row.positive_stock_fraction >= 0.55
        ),
        "top1pct_positive_share_lt25pct": bool(
            math.isfinite(
                concentration["top1pct_positive_contribution_share"]
            )
            and concentration[
                "top1pct_positive_contribution_share"
            ] < 0.25
        ),
        "mean_after_top1pct_removal_gt0": bool(
            concentration[
                "equal_stock_mean_after_removing_top1pct_positive"
            ] > 0
        ),
        "temporal_positive_at_least_4_of_5": bool(
            len(adequate_temporal) == 5
            and (
                adequate_temporal["equal_stock_mean_expectancy"] > 0
            ).sum()
            >= 4
        ),
        "sector_positive_at_least_8_of_11": bool(
            len(adequate_sector) == 11
            and (
                adequate_sector["equal_stock_mean_expectancy"] > 0
            ).sum()
            >= 8
        ),
        "no_single_sector_required": bool(loo_positive),
    }

    if all(gates.values()):
        label = "Diagnostic Strong"
    elif (
        row.equal_stock_mean_expectancy <= 0
        and row.median_stock_expectancy <= 0
    ) or row.positive_stock_fraction < 0.45:
        label = "Diagnostic Weak / Failed"
    elif row.equal_stock_mean_expectancy > 0:
        label = "Diagnostic Mixed"
    else:
        label = "Diagnostic Ambiguous"

    return {
        "policy": policy,
        "label": label,
        "gates": gates,
        "concentration": concentration,
        "adequate_temporal_blocks": int(len(adequate_temporal)),
        "positive_adequate_temporal_blocks": int(
            (
                adequate_temporal["equal_stock_mean_expectancy"] > 0
            ).sum()
        ),
        "adequate_sectors": int(len(adequate_sector)),
        "positive_adequate_sectors": int(
            (
                adequate_sector["equal_stock_mean_expectancy"] > 0
            ).sum()
        ),
    }


def slice_lookup(slice_summary, policy, label):
    rows = slice_summary[
        (slice_summary["policy"] == policy)
        & (slice_summary["mfe_slice"] == label)
    ]
    return (
        float(rows.iloc[0]["equal_stock_mean_harvest"])
        if len(rows)
        else math.nan
    )


def frontier_vs_r0(
    policy,
    primary,
    primary_summary,
    slice_stock,
    slice_summary,
):
    r0 = primary[
        primary["policy"] == "R0_NoDerisk"
    ].set_index("figi")
    cand = primary[primary["policy"] == policy].set_index("figi")
    ids = sorted(set(r0.index) & set(cand.index))

    if not ids:
        return {}

    r0_mean = float(
        primary_summary[
            primary_summary["policy"] == "R0_NoDerisk"
        ].iloc[0]["equal_stock_mean_expectancy"]
    )
    cand_mean = float(
        primary_summary[
            primary_summary["policy"] == policy
        ].iloc[0]["equal_stock_mean_expectancy"]
    )
    r0_med = float(
        primary_summary[
            primary_summary["policy"] == "R0_NoDerisk"
        ].iloc[0]["median_stock_expectancy"]
    )
    cand_med = float(
        primary_summary[
            primary_summary["policy"] == policy
        ].iloc[0]["median_stock_expectancy"]
    )
    r0_pos = float(
        primary_summary[
            primary_summary["policy"] == "R0_NoDerisk"
        ].iloc[0]["positive_stock_fraction"]
    )
    cand_pos = float(
        primary_summary[
            primary_summary["policy"] == policy
        ].iloc[0]["positive_stock_fraction"]
    )

    lt4 = slice_stock[
        slice_stock["mfe_slice"] == "mfe_lt4"
    ]
    r0_lt = lt4[
        lt4["policy"] == "R0_NoDerisk"
    ].set_index("figi")
    cand_lt = lt4[lt4["policy"] == policy].set_index("figi")
    common_lt = sorted(set(r0_lt.index) & set(cand_lt.index))
    lt4_improved = base.mean(
        [
            int(
                cand_lt.loc[x, "mean_harvest"]
                > r0_lt.loc[x, "mean_harvest"]
            )
            for x in common_lt
        ]
    )

    r0_ge8 = slice_lookup(
        slice_summary, "R0_NoDerisk", "mfe_ge8"
    )
    cand_ge8 = slice_lookup(slice_summary, policy, "mfe_ge8")
    retention = (
        cand_ge8 / r0_ge8
        if math.isfinite(r0_ge8)
        and math.isfinite(cand_ge8)
        and r0_ge8 > 0
        else math.nan
    )

    gates = {
        "mean_better_than_r0": bool(cand_mean > r0_mean),
        "median_better_than_r0": bool(cand_med > r0_med),
        "positive_fraction_better_than_r0": bool(cand_pos > r0_pos),
        "mfe_lt4_improved_ge60pct": bool(
            math.isfinite(lt4_improved) and lt4_improved >= 0.60
        ),
        "mfe_ge8_retention_ge80pct": bool(
            math.isfinite(retention) and retention >= 0.80
        ),
    }

    return {
        "policy": policy,
        "paired_primary_stocks": len(ids),
        "equal_stock_mean_expectancy_delta_vs_r0": cand_mean - r0_mean,
        "median_stock_expectancy_delta_vs_r0": cand_med - r0_med,
        "positive_stock_fraction_delta_vs_r0": cand_pos - r0_pos,
        "mfe_lt4_improved_fraction": lt4_improved,
        "mfe_ge8_r0_equal_stock_mean": r0_ge8,
        "mfe_ge8_policy_equal_stock_mean": cand_ge8,
        "mfe_ge8_retention": retention,
        "gates": gates,
        "useful_transport_frontier_gate": bool(all(gates.values())),
    }


def warning_pair_summary(
    label,
    no_derisk,
    warning,
    primary,
    timelines,
    slice_stock,
    slice_summary,
):
    ids = set(
        primary[primary["policy"] == no_derisk]["figi"]
    )
    risk = timelines[timelines["figi"].isin(ids)]

    a = risk[risk["policy"] == no_derisk].set_index("figi")
    b = risk[risk["policy"] == warning].set_index("figi")
    common = sorted(set(a.index) & set(b.index))

    rows = []
    for figi in common:
        x, y = a.loc[figi], b.loc[figi]
        rows.append(
            {
                "bar_vol_improved": int(y.bar_vol < x.bar_vol),
                "max_drawdown_improved": int(
                    y.max_drawdown < x.max_drawdown
                ),
                "es5_improved": int(y.es5 > x.es5),
                "turnover_delta": float(y.turnover - x.turnover),
            }
        )
    defense = pd.DataFrame(rows)

    lt4 = slice_stock[
        slice_stock["mfe_slice"] == "mfe_lt4"
    ]
    a_lt = lt4[lt4["policy"] == no_derisk].set_index("figi")
    b_lt = lt4[lt4["policy"] == warning].set_index("figi")
    common_lt = sorted(set(a_lt.index) & set(b_lt.index))
    lt4_improved = base.mean(
        [
            int(
                b_lt.loc[x, "mean_harvest"]
                > a_lt.loc[x, "mean_harvest"]
            )
            for x in common_lt
        ]
    )

    a_ge8 = slice_lookup(slice_summary, no_derisk, "mfe_ge8")
    b_ge8 = slice_lookup(slice_summary, warning, "mfe_ge8")
    retention = (
        b_ge8 / a_ge8
        if math.isfinite(a_ge8)
        and math.isfinite(b_ge8)
        and a_ge8 > 0
        else math.nan
    )

    return {
        "pair": label,
        "stocks_risk_metrics": len(defense),
        "bar_vol_improved_fraction": (
            base.mean(defense["bar_vol_improved"].tolist())
            if len(defense)
            else math.nan
        ),
        "max_drawdown_improved_fraction": (
            base.mean(defense["max_drawdown_improved"].tolist())
            if len(defense)
            else math.nan
        ),
        "es5_improved_fraction": (
            base.mean(defense["es5_improved"].tolist())
            if len(defense)
            else math.nan
        ),
        "mfe_lt4_harvest_improved_fraction": lt4_improved,
        "mfe_ge8_retention": retention,
        "turnover_delta_equal_stock": (
            base.mean(defense["turnover_delta"].tolist())
            if len(defense)
            else math.nan
        ),
    }


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
        args.universe,
        args.manifest,
        args.raw_dir,
    )
    if not audit["pass"]:
        raise SystemExit("OOS3 snapshot audit failed")
    if audit["universe_sha256_actual"] != EXPECTED_UNIVERSE_SHA:
        raise AssertionError(
            "OOS3 universe SHA drift: "
            f"{audit['universe_sha256_actual']}"
        )

    classifier, blob = load_classifier(args.classifier)
    if blob != FROZEN_CLASSIFIER_BLOB:
        raise AssertionError("frozen classifier blob drift")

    universe = pd.read_csv(args.universe)
    if len(universe) != 300:
        raise AssertionError(f"universe rows drift: {len(universe)}")

    frames, episodes, coverage, metadata = base.build_research_set(
        universe,
        args.raw_dir,
        classifier,
    )
    if not episodes:
        raise AssertionError("no eligible completed episodes")

    paths_frame, path_stats = retest.build_paths(frames, episodes)
    state_map = second.build_state_map(paths_frame)
    time_index = second.frame_time_index(frames)

    records = episode_records(
        episodes,
        state_map,
        frames,
        time_index,
        metadata,
    )
    timelines = build_timelines(
        episodes,
        frames,
        state_map,
        time_index,
        metadata,
    )

    stocks = base.stock_summary(records)
    primary = stocks[
        stocks["episodes"] >= base.MIN_PRIMARY_EPISODES
    ].copy()
    primary_ids = set(
        primary[
            primary["policy"] == "R0_NoDerisk"
        ]["figi"]
    )
    if not primary_ids:
        raise AssertionError("no primary stocks")

    primary = primary[
        primary["figi"].isin(primary_ids)
    ].copy()
    primary_summary = base.aggregate_primary(primary)
    slice_stock, slice_summary = base.episode_slice_table(
        records, primary_ids
    )
    temporal_stock, temporal_summary = base.temporal_table(
        records, primary_ids
    )
    direction_stock, direction_summary = base.direction_table(
        records, primary_ids
    )
    sector_summary, _ = base.sector_table(primary)
    sleeve_summary = base.sleeve_table(primary)

    classifications = [
        standalone_classification(
            policy,
            primary_summary,
            primary,
            temporal_summary,
            sector_summary,
        )
        for policy in POLICIES
    ]

    frontier = [
        frontier_vs_r0(
            policy,
            primary,
            primary_summary,
            slice_stock,
            slice_summary,
        )
        for policy in POLICIES
        if policy != "R0_NoDerisk"
    ]

    warning_pairs = [
        warning_pair_summary(
            label,
            no_derisk,
            warning,
            primary,
            timelines,
            slice_stock,
            slice_summary,
        )
        for label, (no_derisk, warning) in PAIR_MAP.items()
    ]

    integrity = {
        "issue": 78,
        "study": "Untouched equity proof-policy OOS3",
        "classifier_blob": blob,
        "universe_sha256": audit["universe_sha256_actual"],
        "raw_files": audit["completed"],
        "raw_failures": audit["failures"],
        "stocks_in_universe": len(universe),
        "completed_eligible_episodes": len(episodes),
        "primary_stocks": len(primary_ids),
        "b3_events": len(paths_frame),
        "path_stats": path_stats,
        "survivorship_limited": True,
        "policy_economics_computed": True,
    }

    summary = {
        "integrity": integrity,
        "primary": primary_summary.to_dict("records"),
        "standalone_classification": classifications,
        "frontier_vs_r0": frontier,
        "warning_first_pairs": warning_pairs,
        "notes": [
            "Second deterministic 300-stock cohort; zero FIGI overlap with OOS2.",
            "Proof thresholds and exposure states were frozen before OOS3 history/economics.",
            "One stock receives one vote in primary summaries.",
            "No policy threshold may be changed after this output is inspected.",
        ],
    }

    args.out.mkdir(parents=True, exist_ok=True)
    base.write_csv(args.out / "coverage.csv", coverage)
    base.write_csv(args.out / "episode_policy.csv", records)
    base.write_csv(args.out / "stock_policy.csv", stocks)
    base.write_csv(args.out / "primary_stock_policy.csv", primary)
    base.write_csv(args.out / "primary_summary.csv", primary_summary)
    base.write_csv(args.out / "timeline_policy.csv", timelines)
    base.write_csv(args.out / "mfe_slice_per_stock.csv", slice_stock)
    base.write_csv(args.out / "mfe_slice_summary.csv", slice_summary)
    base.write_csv(args.out / "temporal_per_stock.csv", temporal_stock)
    base.write_csv(args.out / "temporal_summary.csv", temporal_summary)
    base.write_csv(args.out / "direction_per_stock.csv", direction_stock)
    base.write_csv(args.out / "direction_summary.csv", direction_summary)
    base.write_csv(args.out / "sector_summary.csv", sector_summary)
    base.write_csv(args.out / "sleeve_summary.csv", sleeve_summary)

    (args.out / "summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
