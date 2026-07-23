#!/usr/bin/env python3
"""Compare the three Issue #28 SPY 1D feature sets through K=3..8."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import compare_state_counts
import train_hmm

LOOKBACK = 20
EFFICIENCY_RATIO = "signed_efficiency_ratio_20"
DOWNSIDE_SHARE = "downside_variance_share_20"
FEATURE_SETS = {
    "baseline": tuple(train_hmm.FEATURE_NAMES),
    "baseline_er": (*train_hmm.FEATURE_NAMES, EFFICIENCY_RATIO),
    "baseline_er_downside": (*train_hmm.FEATURE_NAMES, EFFICIENCY_RATIO, DOWNSIDE_SHARE),
}
MATERIAL_IMPROVEMENT = 0.10


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare SPY 1D HMM feature sufficiency")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--date-column", default="Date")
    parser.add_argument("--open-column", default="Open")
    parser.add_argument("--high-column", default="High")
    parser.add_argument("--low-column", default="Low")
    parser.add_argument("--close-column", default="Close")
    parser.add_argument("--symbol", default="SPY")
    parser.add_argument("--timeframe", default="1D")
    parser.add_argument("--train-fraction", type=float, default=0.80)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(compare_state_counts.DEFAULT_SEEDS))
    return parser.parse_args()


def calculate_path_features(frame: pd.DataFrame, lookback: int = LOOKBACK) -> pd.DataFrame:
    """Calculate the two causal Issue #28 formulas; undefined denominators map to zero."""
    if lookback < 1:
        raise ValueError("lookback must be positive")
    close = frame["close"].astype(float)
    changes = close.diff()
    path_length = changes.abs().rolling(lookback, min_periods=lookback).sum()
    displacement = close - close.shift(lookback)
    efficiency = displacement.div(path_length.where(path_length != 0.0)).fillna(
        displacement.where(path_length == 0.0, np.nan) * 0.0
    )

    log_return = np.log(close / close.shift(1))
    squared_return = log_return.pow(2)
    total_variance = squared_return.rolling(lookback, min_periods=lookback).sum()
    downside_variance = log_return.clip(upper=0.0).pow(2).rolling(
        lookback, min_periods=lookback
    ).sum()
    downside_share = downside_variance.div(total_variance.where(total_variance != 0.0)).fillna(
        total_variance.where(total_variance == 0.0, np.nan) * 0.0
    )

    result = pd.DataFrame({
        "date": frame["date"],
        EFFICIENCY_RATIO: efficiency,
        DOWNSIDE_SHARE: downside_share,
    })
    # Preserve causal warm-up NaNs; only true zero denominators become zero.
    result.loc[path_length.isna(), EFFICIENCY_RATIO] = np.nan
    result.loc[total_variance.isna(), DOWNSIDE_SHARE] = np.nan
    return result


def add_path_features(baseline: pd.DataFrame, raw: pd.DataFrame) -> pd.DataFrame:
    path = calculate_path_features(raw)
    enriched = baseline.merge(path, on="date", how="left", validate="one_to_one")
    if enriched[[EFFICIENCY_RATIO, DOWNSIDE_SHARE]].isna().any().any():
        raise ValueError("path-shape features are unavailable after baseline warm-up")
    return enriched


def metric_leaders(result: dict[str, Any]) -> dict[str, int | None]:
    complete = [row for row in result["candidates"] if row["status"] == "ok"]
    if not complete:
        return {"aic": None, "bic": None, "oos_likelihood": None}
    return {
        "aic": min(complete, key=lambda row: row["aggregate"]["aic"]["mean"])["k"],
        "bic": min(complete, key=lambda row: row["aggregate"]["bic"]["mean"])["k"],
        "oos_likelihood": max(complete, key=lambda row: row["aggregate"]["oos_log_likelihood_per_observation"]["mean"])["k"],
    }


def candidate_for_k(result: dict[str, Any], k: int) -> dict[str, Any] | None:
    return next((row for row in result["candidates"] if row["k"] == k and row["status"] == "ok"), None)


def cross_feature_diagnostics(candidate: dict[str, Any], dimensions: int) -> dict[str, Any]:
    """Return conservative raw and dimension-normalized cross-feature metrics."""
    if dimensions < 1:
        raise ValueError("feature dimensions must be positive")
    fits = candidate["fits"]
    raw = {
        "minimum_separation": min(fit["minimum_pairwise_separation"] for fit in fits),
        "maximum_likelihood_drift": max(fit["train_oos_likelihood_drift"] for fit in fits),
        "maximum_occupancy_drift_l1": max(fit["occupancy_drift_l1"] for fit in fits),
    }
    normalized = {
        "minimum_separation_per_sqrt_dimension": raw["minimum_separation"] / np.sqrt(dimensions),
        "maximum_likelihood_drift_per_dimension": raw["maximum_likelihood_drift"] / dimensions,
        # Occupancy is already a dimensionless probability distance.
        "maximum_occupancy_drift_l1": raw["maximum_occupancy_drift_l1"],
    }
    return {"dimensions": dimensions, "raw_worst_seed": raw, "normalized_worst_seed": normalized}


def diagnostic_summary(result: dict[str, Any]) -> dict[str, Any]:
    selected_k = result["decision"]["selected_k"]
    leaders = metric_leaders(result)
    reference_k = selected_k if selected_k is not None else leaders["oos_likelihood"]
    row = candidate_for_k(result, reference_k) if reference_k is not None else None
    all_candidate_failed = sorted(
        {name for candidate in result["candidates"] if candidate["status"] == "ok" for name in candidate["guardrails"]["failed"]}
        | {f"incomplete_k_{candidate['k']}" for candidate in result["candidates"] if candidate["status"] != "ok"}
    )
    if row is None:
        return {
            "reference_k": None,
            "failed_guardrails": [],
            "all_candidate_failed_guardrails": all_candidate_failed,
            "leaders": leaders,
            "cross_feature_diagnostics": None,
        }
    return {
        "reference_k": reference_k,
        "failed_guardrails": list(row["guardrails"]["failed"]),
        "all_candidate_failed_guardrails": all_candidate_failed,
        "leaders": leaders,
        "cross_feature_diagnostics": cross_feature_diagnostics(
            row, len(result["method"]["features"])
        ),
    }


def materially_clearer(baseline: dict[str, Any], variant: dict[str, Any]) -> bool:
    k = variant["decision"]["selected_k"]
    if k is None:
        return False
    left, right = candidate_for_k(baseline, k), candidate_for_k(variant, k)
    if left is None or right is None:
        return False
    left_metrics = cross_feature_diagnostics(left, len(baseline["method"]["features"]))["normalized_worst_seed"]
    right_metrics = cross_feature_diagnostics(right, len(variant["method"]["features"]))["normalized_worst_seed"]
    left_separation = left_metrics["minimum_separation_per_sqrt_dimension"]
    right_separation = right_metrics["minimum_separation_per_sqrt_dimension"]
    separation = right_separation >= (1.0 + MATERIAL_IMPROVEMENT) * left_separation
    left_ll = left_metrics["maximum_likelihood_drift_per_dimension"]
    right_ll = right_metrics["maximum_likelihood_drift_per_dimension"]
    left_occ = left_metrics["maximum_occupancy_drift_l1"]
    right_occ = right_metrics["maximum_occupancy_drift_l1"]
    consistency = (
        (right_ll <= (1.0 - MATERIAL_IMPROVEMENT) * left_ll or right_occ <= (1.0 - MATERIAL_IMPROVEMENT) * left_occ)
        and right_ll <= left_ll and right_occ <= left_occ
    )
    return bool(separation and consistency)


def choose_feature_set(variants: dict[str, dict[str, Any]]) -> dict[str, Any]:
    baseline = variants["baseline"]
    if baseline["decision"]["selected_k"] is not None:
        return {"outcome": "retain_baseline", "selected_feature_set": "baseline", "selected_k": baseline["decision"]["selected_k"], "reason": "The baseline already supports a stable fixed-K selection, so the simplest sufficient feature set is retained."}
    for name in ("baseline_er", "baseline_er_downside"):
        variant = variants[name]
        if variant["decision"]["selected_k"] is not None and materially_clearer(baseline, variant):
            return {"outcome": "select_feature_set", "selected_feature_set": name, "selected_k": variant["decision"]["selected_k"], "reason": "This is the simplest feature set with a stable internal K decision and at least 10% better worst-seed dimension-normalized separation plus non-worsening worst-seed OOS consistency, including at least one 10% consistency improvement, versus baseline at the same K."}
    return {"outcome": "keep_productization_paused", "selected_feature_set": None, "selected_k": None, "reason": "None of the three feature sets supports both a stable fixed-K decision and materially clearer worst-seed, dimension-normalized state separation/OOS consistency."}


def compare(args: argparse.Namespace) -> dict[str, Any]:
    if args.symbol.upper() != "SPY" or args.timeframe.upper() != "1D":
        raise ValueError("Issue #28 comparison is restricted to SPY 1D")
    if not 0.50 <= args.train_fraction < 1.0:
        raise ValueError("train_fraction must be in [0.50, 1.0)")
    compare_state_counts.validate_seed_groups(args.seeds)
    config = train_hmm.FeatureConfig()
    raw = train_hmm.load_ohlc(args)
    baseline = train_hmm.calculate_features(raw, config)
    enriched = add_path_features(baseline, raw)
    variants = {
        name: compare_state_counts.compare_features(args, enriched, list(names), config)
        for name, names in FEATURE_SETS.items()
    }
    summaries = {name: diagnostic_summary(result) for name, result in variants.items()}
    return compare_state_counts.strict_json({
        "schema_version": 1,
        "scope": {"symbol": "SPY", "timeframe": "1D", "feature_sets": list(FEATURE_SETS)},
        "feature_formulas": {
            EFFICIENCY_RATIO: "(close - close[20]) / sum(abs(close - close[1]), 20)",
            DOWNSIDE_SHARE: "sum(min(log_return, 0)^2, 20) / sum(log_return^2, 20)",
        },
        "cross_feature_policy": {
            "material_improvement_fraction": MATERIAL_IMPROVEMENT,
            "likelihood_alone_is_sufficient": False,
            "seed_summary": "worst_seed",
            "separation_normalization": "minimum_pairwise_separation / sqrt(feature_dimensions)",
            "likelihood_drift_normalization": "train_oos_likelihood_drift / feature_dimensions",
            "occupancy_drift_normalization": "none; L1 probability distance is dimensionless",
        },
        "variants": variants,
        "variant_summaries": summaries,
        "decision": choose_feature_set(variants),
    })


def markdown_report(result: dict[str, Any]) -> str:
    decision = result["decision"]
    lines = ["# SPY 1D HMM feature-sufficiency decision", "", f"**Outcome:** `{decision['outcome']}`", f"**Feature set:** `{decision['selected_feature_set'] or 'none'}`", f"**Selected K:** {decision['selected_k'] if decision['selected_k'] is not None else 'none'}", "", decision["reason"], "", "| Feature set | Internal decision | Leaders AIC/BIC/OOS LL | Failed guardrails | Worst separation raw / normalized | Worst LL drift raw / normalized | Worst occupancy drift | Reason |", "|---|---|---|---|---:|---:|---:|---|"]
    for name in FEATURE_SETS:
        variant, summary = result["variants"][name], result["variant_summaries"][name]
        selected = variant["decision"]["selected_k"]
        internal = f"K={selected}" if selected is not None else "inconclusive"
        leaders = summary["leaders"]
        leader_text = f"{leaders['aic']}/{leaders['bic']}/{leaders['oos_likelihood']}"
        failed = ", ".join(summary["failed_guardrails"]) or "none"
        diagnostics = summary["cross_feature_diagnostics"]
        if diagnostics:
            raw = diagnostics["raw_worst_seed"]
            normalized = diagnostics["normalized_worst_seed"]
            separation = f"{raw['minimum_separation']:.3f} / {normalized['minimum_separation_per_sqrt_dimension']:.3f}"
            likelihood = f"{raw['maximum_likelihood_drift']:.3f} / {normalized['maximum_likelihood_drift_per_dimension']:.3f}"
            occupancy = f"{raw['maximum_occupancy_drift_l1']:.3f}"
        else:
            separation = likelihood = occupancy = "—"
        reason = variant["decision"]["reason"]
        lines.append(f"| `{name}` | {internal} | {leader_text} | {failed} | {separation} | {likelihood} | {occupancy} | {reason} |")
    lines += ["", "Cross-feature materiality uses only worst-seed, dimension-normalized separation and likelihood drift plus worst-seed occupancy drift. Raw and normalized values are both shown; seed means cannot establish improvement.", "", "All three variants use the unchanged #26 split, training-only scaler, K=3–8 HMM configuration, seeds/restarts, causal filter, alignment, diagnostics, guardrails, and internal decision logic. The 10% rule applies only to the new cross-feature-set materiality decision; likelihood improvement alone cannot select a richer feature set.", ""]
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    result = compare(args)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "feature-set-comparison.json"
    report_path = args.output_dir / "feature-set-decision.md"
    json_path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    report_path.write_text(markdown_report(result), encoding="utf-8")
    print(f"decision: {result['decision']['outcome']}")
    print(f"wrote: {json_path}")
    print(f"wrote: {report_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"error: {exc}")
        raise SystemExit(2)
