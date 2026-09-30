#!/usr/bin/env python3
"""Issue #78 equity early-proof replication.

Reuses the feature definitions frozen in the 2026-09-15 Big Trend vs Failed
Trend study and applies them to the Issue #119 Bloomberg 300-stock diagnostic
cohort.

No threshold selection or policy optimization is performed here.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path

import numpy as np
import pandas as pd

import analyze_issue78_bbg_equity_oos2 as equity
import analyze_issue78_big_vs_failed_features as prior
import analyze_issue78_retest_path_stage1 as retest
import analyze_issue78_second_entry_economic_policy as second
import analyze_issue78_r0_warning_first_composition as comp
from audit_issue119_bbg_oos2_snapshot import audit_snapshot
from smoke_issue119_frozen_classifier import (
    FROZEN_CLASSIFIER_BLOB,
    load_classifier,
)

FEATURES = {
    "e5_cum_atr": (+1, "E5"),
    "e5_mfe_atr": (+1, "E5"),
    "e5_giveback_atr": (-1, "E5"),
    "e5_dir_eff": (+1, "E5"),
    "e10_cum_atr": (+1, "E10"),
    "e10_mfe_atr": (+1, "E10"),
    "e10_giveback_atr": (-1, "E10"),
    "e10_dir_eff": (+1, "E10"),
}

TARGETS = {
    "failed_vs_large": ("Large", "Failed"),
    "usable_b3_vs_no_b3": ("UsableB3", "NoUsableB3"),
}

MIN_CLASS_N_PER_STOCK = 3
MIN_STOCKS_FOR_SLICE = 5


def finite(values):
    return [
        float(x)
        for x in values
        if isinstance(x, (int, float, np.integer, np.floating))
        and math.isfinite(float(x))
    ]


def mean(values):
    vals = finite(values)
    return statistics.fmean(vals) if vals else math.nan


def median(values):
    vals = finite(values)
    return statistics.median(vals) if vals else math.nan


def block_name(value) -> str:
    ts = pd.Timestamp(value)
    return equity.block_name(ts)


def episode_feature_rows(
    episodes,
    paths_frame: pd.DataFrame,
    frames,
    time_index,
    metadata,
):
    state_map = second.build_state_map(paths_frame)
    out = []

    for episode in episodes:
        figi, stage, episode_id, start, records = episode
        state = state_map.get((figi, episode_id))
        levels = (
            second.frozen_levels(episode, state, frames, time_index)
            if state is not None
            else None
        )
        steps = second.aligned_steps(episode)
        final_mfe = second.episode_mfe(steps)

        if final_mfe < 4.0:
            trend_label = "Failed"
        elif final_mfe >= 8.0:
            trend_label = "Large"
        else:
            trend_label = "Middle"

        path = state["path"] if state is not None else "NoUsableB3"
        b3_label = "UsableB3" if state is not None else "NoUsableB3"

        _, _, _, r0_returns, _ = comp.simulate_episode(
            episode, state, levels, frames, "none"
        )

        meta = metadata[figi]
        entry_date = pd.Timestamp(records[0]["date"])
        row = {
            **meta,
            "episode_id": int(episode_id),
            "entry_date": str(entry_date.date()),
            "block": block_name(entry_date),
            "direction": "Markup" if stage == 2 else "Markdown",
            "bars": len(steps),
            "final_mfe": final_mfe,
            "trend_label": trend_label,
            "path": path,
            "b3_label": b3_label,
            "r0_harvest": float(sum(r0_returns)),
        }

        for k in (5, 10):
            cum, mfe, giveback, eff = prior.early_features(steps, k)
            row[f"e{k}_cum_atr"] = cum
            row[f"e{k}_mfe_atr"] = mfe
            row[f"e{k}_giveback_atr"] = giveback
            row[f"e{k}_dir_eff"] = eff

        out.append(row)

    return pd.DataFrame(out)


def survival_summary(rows: pd.DataFrame) -> pd.DataFrame:
    output = []
    for label_col, labels in (
        ("trend_label", ("Failed", "Middle", "Large")),
        ("b3_label", ("NoUsableB3", "UsableB3")),
    ):
        for label in labels:
            group = rows[rows[label_col] == label]
            n = len(group)
            output.append(
                {
                    "label_family": label_col,
                    "label": label,
                    "episodes": n,
                    "survive_e5_fraction": (
                        float((group["bars"] >= 5).mean()) if n else math.nan
                    ),
                    "survive_e10_fraction": (
                        float((group["bars"] >= 10).mean()) if n else math.nan
                    ),
                    "median_bars": (
                        float(group["bars"].median()) if n else math.nan
                    ),
                }
            )
    return pd.DataFrame(output)


def target_label(row, target: str):
    if target == "failed_vs_large":
        return row["trend_label"]
    if target == "usable_b3_vs_no_b3":
        return row["b3_label"]
    raise ValueError(target)


def auc_for_group(group: pd.DataFrame, feature: str, target: str, orient: int):
    positive, negative = TARGETS[target]
    work = group[np.isfinite(pd.to_numeric(group[feature], errors="coerce"))]
    labels = work.apply(lambda r: target_label(r, target), axis=1)
    pos = (orient * work.loc[labels == positive, feature]).tolist()
    neg = (orient * work.loc[labels == negative, feature]).tolist()
    if len(pos) < MIN_CLASS_N_PER_STOCK or len(neg) < MIN_CLASS_N_PER_STOCK:
        return None
    return {
        "auc": prior.auc(pos, neg),
        "positive_n": len(pos),
        "negative_n": len(neg),
        "positive_median": median(
            work.loc[labels == positive, feature].tolist()
        ),
        "negative_median": median(
            work.loc[labels == negative, feature].tolist()
        ),
    }


def separation_table(rows: pd.DataFrame) -> pd.DataFrame:
    out = []
    for target in TARGETS:
        for feature, (orient, info) in FEATURES.items():
            per_stock = []
            for figi, group in rows.groupby("figi"):
                result = auc_for_group(group, feature, target, orient)
                if result is not None:
                    per_stock.append({"figi": figi, **result})

            if not per_stock:
                continue
            ps = pd.DataFrame(per_stock)
            out.append(
                {
                    "target": target,
                    "feature": feature,
                    "information_set": info,
                    "orientation": orient,
                    "stocks": int(len(ps)),
                    "positive_n": int(ps["positive_n"].sum()),
                    "negative_n": int(ps["negative_n"].sum()),
                    "equal_stock_mean_auc": float(ps["auc"].mean()),
                    "equal_stock_median_auc": float(ps["auc"].median()),
                    "stocks_auc_gt_0_5": int((ps["auc"] > 0.5).sum()),
                    "fraction_stocks_auc_gt_0_5": float(
                        (ps["auc"] > 0.5).mean()
                    ),
                    "equal_stock_positive_median": float(
                        ps["positive_median"].mean()
                    ),
                    "equal_stock_negative_median": float(
                        ps["negative_median"].mean()
                    ),
                }
            )
    return pd.DataFrame(out)


def per_stock_table(rows: pd.DataFrame) -> pd.DataFrame:
    out = []
    for target in TARGETS:
        for feature, (orient, info) in FEATURES.items():
            for figi, group in rows.groupby("figi"):
                result = auc_for_group(group, feature, target, orient)
                if result is None:
                    continue
                first = group.iloc[0]
                out.append(
                    {
                        "target": target,
                        "feature": feature,
                        "information_set": info,
                        "figi": figi,
                        "ticker": first["ticker"],
                        "sector": first["sector"],
                        "sleeve": first["sleeve"],
                        **result,
                    }
                )
    return pd.DataFrame(out)


def sliced_auc_table(rows: pd.DataFrame) -> pd.DataFrame:
    out = []
    slices = (
        ("direction", "direction"),
        ("sleeve", "sleeve"),
        ("sector", "sector"),
        ("block", "block"),
    )

    for target in TARGETS:
        for feature, (orient, info) in FEATURES.items():
            for slice_type, column in slices:
                for slice_value, sliced in rows.groupby(column):
                    per_stock = []
                    for figi, group in sliced.groupby("figi"):
                        result = auc_for_group(
                            group, feature, target, orient
                        )
                        if result is not None:
                            per_stock.append(result)
                    if len(per_stock) < MIN_STOCKS_FOR_SLICE:
                        continue
                    aucs = [x["auc"] for x in per_stock]
                    out.append(
                        {
                            "target": target,
                            "feature": feature,
                            "information_set": info,
                            "slice_type": slice_type,
                            "slice_value": slice_value,
                            "stocks": len(per_stock),
                            "equal_stock_mean_auc": mean(aucs),
                            "equal_stock_median_auc": median(aucs),
                            "stocks_auc_gt_0_5": sum(x > 0.5 for x in aucs),
                            "fraction_stocks_auc_gt_0_5": mean(
                                [int(x > 0.5) for x in aucs]
                            ),
                        }
                    )
    return pd.DataFrame(out)


def quintile_table(rows: pd.DataFrame) -> pd.DataFrame:
    out = []

    for target, (positive, negative) in TARGETS.items():
        for feature, (orient, info) in FEATURES.items():
            assigned = []
            for figi, group in rows.groupby("figi"):
                work = group[
                    np.isfinite(pd.to_numeric(group[feature], errors="coerce"))
                ].copy()
                if len(work) < 20:
                    continue
                scores = (orient * work[feature]).tolist()
                pcts = prior.percentile_ranks(scores)
                work["quality_quintile"] = [
                    min(5, int(p * 5) + 1) for p in pcts
                ]
                assigned.append(work)

            if not assigned:
                continue
            work = pd.concat(assigned, ignore_index=True)

            for q in range(1, 6):
                qrows = work[work["quality_quintile"] == q]
                per_stock = []
                for figi, group in qrows.groupby("figi"):
                    labels = group.apply(
                        lambda r: target_label(r, target), axis=1
                    )
                    per_stock.append(
                        {
                            "positive_share": float(
                                (labels == positive).mean()
                            ),
                            "negative_share": float(
                                (labels == negative).mean()
                            ),
                            "r0_harvest": float(group["r0_harvest"].mean()),
                            "episodes": int(len(group)),
                        }
                    )
                out.append(
                    {
                        "target": target,
                        "feature": feature,
                        "information_set": info,
                        "quality_quintile": q,
                        "stocks": len(per_stock),
                        "episodes": sum(x["episodes"] for x in per_stock),
                        "equal_stock_positive_share": mean(
                            [x["positive_share"] for x in per_stock]
                        ),
                        "equal_stock_negative_share": mean(
                            [x["negative_share"] for x in per_stock]
                        ),
                        "equal_stock_r0_harvest": mean(
                            [x["r0_harvest"] for x in per_stock]
                        ),
                    }
                )
    return pd.DataFrame(out)


def write_csv(path: Path, frame: pd.DataFrame):
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


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

    audit = audit_snapshot(args.universe, args.manifest, args.raw_dir)
    if not audit["pass"]:
        raise SystemExit("Issue #119 snapshot audit failed")

    classifier, blob = load_classifier(args.classifier)
    if blob != FROZEN_CLASSIFIER_BLOB:
        raise AssertionError("frozen classifier blob drift")

    universe = pd.read_csv(args.universe)
    frames, episodes, coverage, metadata = equity.build_research_set(
        universe, args.raw_dir, classifier
    )
    paths_frame, path_stats = retest.build_paths(frames, episodes)
    time_index = second.frame_time_index(frames)

    episode_rows = episode_feature_rows(
        episodes, paths_frame, frames, time_index, metadata
    )
    survival = survival_summary(episode_rows)
    separation = separation_table(episode_rows)
    per_stock = per_stock_table(episode_rows)
    slices = sliced_auc_table(episode_rows)
    quintiles = quintile_table(episode_rows)

    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out / "episode_features.csv", episode_rows)
    write_csv(args.out / "survival_summary.csv", survival)
    write_csv(args.out / "separation_summary.csv", separation)
    write_csv(args.out / "per_stock_auc.csv", per_stock)
    write_csv(args.out / "slice_auc.csv", slices)
    write_csv(args.out / "quintiles.csv", quintiles)

    key_features = ("e5_cum_atr", "e5_dir_eff", "e10_cum_atr", "e10_dir_eff")
    key = separation[separation["feature"].isin(key_features)].copy()
    key = key.sort_values(["target", "information_set", "feature"])

    summary = {
        "issue": 78,
        "study": "Equity early-proof replication diagnostic",
        "classifier_blob": blob,
        "universe_sha256": audit["universe_sha256_actual"],
        "episodes": int(len(episode_rows)),
        "path_stats": path_stats,
        "result_role": {
            "failed_vs_large": "external-feature replication diagnostic",
            "usable_b3_vs_no_b3": "post-outcome mechanism diagnostic",
        },
        "survival": survival.to_dict("records"),
        "key_separation": key.to_dict("records"),
        "guardrail": (
            "No threshold, composite score, or sizing policy is selected by this run."
        ),
    }
    (args.out / "summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
