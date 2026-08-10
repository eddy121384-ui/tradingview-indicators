#!/usr/bin/env python3
"""Test price-only Evidence / Top Gap calibration before final OOS for Issue #55.

To avoid inventing a directional meaning for every Wyckoff transition state,
this calibration gate uses only the two unambiguous directional formal states:

* 2 Markup: a stronger signal should be followed by a larger positive return.
* 5 Markdown: a stronger signal should be followed by a larger negative return.

For each pair/stage/confidence field, low/medium/high cut points are learned from
Development bars only (33rd and 67th percentiles) and then applied unchanged to
Exploratory OOS. Final-OOS rows are never passed into the model and forward
windows may not cross the exploratory boundary.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from evaluate_regime_paths_pre_final import HORIZONS, future_metrics, load_frozen_pair
from price_only_core import PriceOnlyConfig, compute_price_only


DIRECTIONAL_STAGES = {2: 1.0, 5: -1.0}
CONFIDENCE_FIELDS = ("evidence_strength", "top_gap")
MIN_DEV_STATE_N = 60
MIN_EXP_BIN_N = 10


def development_cutpoints(values: np.ndarray) -> tuple[float, float] | None:
    finite = values[np.isfinite(values)]
    if len(finite) < MIN_DEV_STATE_N:
        return None
    low, high = np.quantile(finite, [1.0 / 3.0, 2.0 / 3.0])
    return float(low), float(high)


def confidence_bin(value: float, low: float, high: float) -> str | None:
    if not np.isfinite(value):
        return None
    if value <= low:
        return "low"
    if value <= high:
        return "medium"
    return "high"


def _mean(values: list[float]) -> float | None:
    finite = [value for value in values if np.isfinite(value)]
    return float(np.mean(finite)) if finite else None


def analyze_pair(frame: pd.DataFrame, meta: dict) -> dict:
    dev = meta["splits"]["development"]
    exp = meta["splits"]["exploratory_oos"]
    dev_start, dev_end = int(dev["start_index"]), int(dev["end_index"])
    exp_start, exp_end = int(exp["start_index"]), int(exp["end_index"])

    pre_final = frame.iloc[: exp_end + 1].copy().reset_index(drop=True)
    model = compute_price_only(pre_final, PriceOnlyConfig())
    formal = pd.to_numeric(model["formal_id"], errors="coerce").fillna(0).to_numpy(int)
    metrics_by_horizon = {h: future_metrics(pre_final, h) for h in HORIZONS}

    output = {
        "model_rows_computed": len(pre_final),
        "final_oos_rows_computed": 0,
        "development": {"start_date": dev["start_date"], "end_date": dev["end_date"]},
        "exploratory_oos": {"start_date": exp["start_date"], "end_date": exp["end_date"]},
        "stages": {},
    }

    for stage, direction in DIRECTIONAL_STAGES.items():
        stage_result = {"direction_multiplier": direction, "confidence_fields": {}}
        dev_stage_mask = np.zeros(len(pre_final), dtype=bool)
        dev_stage_mask[dev_start : dev_end + 1] = True
        dev_stage_mask &= formal == stage

        for field in CONFIDENCE_FIELDS:
            confidence = pd.to_numeric(model[field], errors="coerce").to_numpy(float)
            cutpoints = development_cutpoints(confidence[dev_stage_mask])
            field_result = {
                "development_state_bar_count": int(np.sum(dev_stage_mask & np.isfinite(confidence))),
                "development_cutpoints": None,
                "horizons": {},
            }
            if cutpoints is None:
                field_result["skip_reason"] = f"development stage count < {MIN_DEV_STATE_N}"
                stage_result["confidence_fields"][field] = field_result
                continue
            low_cut, high_cut = cutpoints
            field_result["development_cutpoints"] = {"q33": low_cut, "q67": high_cut}

            for horizon in HORIZONS:
                metrics = metrics_by_horizon[horizon]
                last_origin = exp_end - horizon
                bins = {"low": [], "medium": [], "high": []}
                raw_returns = {"low": [], "medium": [], "high": []}
                if last_origin >= exp_start:
                    for idx in range(exp_start, last_origin + 1):
                        if formal[idx] != stage:
                            continue
                        fwd = metrics["forward_return"][idx]
                        bucket = confidence_bin(confidence[idx], low_cut, high_cut)
                        if bucket is None or not np.isfinite(fwd):
                            continue
                        raw_returns[bucket].append(float(fwd))
                        bins[bucket].append(float(fwd) * direction)

                means = {bucket: _mean(values) for bucket, values in bins.items()}
                counts = {bucket: len(values) for bucket, values in bins.items()}
                raw_means = {bucket: _mean(values) for bucket, values in raw_returns.items()}
                high_low_comparable = counts["low"] >= MIN_EXP_BIN_N and counts["high"] >= MIN_EXP_BIN_N
                all_bins_comparable = all(counts[bucket] >= MIN_EXP_BIN_N for bucket in bins)
                high_minus_low = (
                    None
                    if not high_low_comparable or means["high"] is None or means["low"] is None
                    else means["high"] - means["low"]
                )
                monotonic = (
                    None
                    if not all_bins_comparable
                    else means["low"] <= means["medium"] <= means["high"]
                )
                field_result["horizons"][str(horizon)] = {
                    "bin_counts": counts,
                    "raw_forward_return_mean": raw_means,
                    "stage_aligned_return_mean": means,
                    "high_low_comparable": high_low_comparable,
                    "all_bins_comparable": all_bins_comparable,
                    "high_minus_low_stage_aligned_return": high_minus_low,
                    "high_better_than_low": None if high_minus_low is None else high_minus_low > 0.0,
                    "monotonic_low_medium_high": monotonic,
                }
            stage_result["confidence_fields"][field] = field_result
        output["stages"][str(stage)] = stage_result
    return output


def aggregate(pairs: dict) -> dict:
    fields = {}
    for field in CONFIDENCE_FIELDS:
        comparable = 0
        positive = 0
        monotonic_comparable = 0
        monotonic_count = 0
        rows = []
        for pair, pair_result in pairs.items():
            for stage in DIRECTIONAL_STAGES:
                field_result = pair_result["stages"][str(stage)]["confidence_fields"][field]
                if field_result["development_cutpoints"] is None:
                    continue
                for horizon in HORIZONS:
                    row = field_result["horizons"][str(horizon)]
                    if row["high_low_comparable"]:
                        comparable += 1
                        positive += int(bool(row["high_better_than_low"]))
                    if row["all_bins_comparable"]:
                        monotonic_comparable += 1
                        monotonic_count += int(bool(row["monotonic_low_medium_high"]))
                    rows.append(
                        {
                            "pair": pair,
                            "stage": stage,
                            "horizon": horizon,
                            "bin_counts": row["bin_counts"],
                            "high_minus_low_stage_aligned_return": row["high_minus_low_stage_aligned_return"],
                            "high_better_than_low": row["high_better_than_low"],
                            "monotonic_low_medium_high": row["monotonic_low_medium_high"],
                        }
                    )
        fields[field] = {
            "high_low_comparable_cases": comparable,
            "high_better_than_low_cases": positive,
            "high_better_than_low_rate": positive / comparable if comparable else None,
            "all_bins_comparable_cases": monotonic_comparable,
            "monotonic_cases": monotonic_count,
            "monotonic_rate": monotonic_count / monotonic_comparable if monotonic_comparable else None,
            "rows": rows,
        }
    return {"confidence_fields": fields}


def build_report(manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("final_oos_status") != "SEALED_DO_NOT_EVALUATE":
        raise ValueError("refusing to run without final-OOS seal")
    pairs = {
        pair: analyze_pair(load_frozen_pair(manifest_path, meta), meta)
        for pair, meta in manifest["pairs"].items()
    }
    return {
        "schema_version": 1,
        "issue": 55,
        "status": "pre_final_directional_confidence_calibration",
        "directional_stages": {"2": "Markup (+return desired)", "5": "Markdown (-return desired)"},
        "confidence_fields": list(CONFIDENCE_FIELDS),
        "development_bin_rule": "per pair + formal stage, q33/q67 learned on Development only",
        "minimum_development_stage_bars": MIN_DEV_STATE_N,
        "minimum_exploratory_bin_bars": MIN_EXP_BIN_N,
        "final_oos_status": "SEALED_NOT_COMPUTED",
        "pairs": pairs,
        "aggregate": aggregate(pairs),
        "boundary": (
            "Exploratory-OOS calibration uses Development-derived confidence cut points. "
            "No final-OOS model output or final-OOS price path is computed. This calibration gate covers only "
            "the unambiguous directional Markup/Markdown states and is not a trading backtest."
        ),
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# Issue #55 — Pre-final confidence calibration",
        "",
        "Final OOS remains **SEALED / NOT COMPUTED**.",
        "",
        "Low/medium/high confidence cut points are learned from Development only and applied unchanged to Exploratory OOS. Calibration is tested only for the unambiguous directional states: Markup (2) and Markdown (5). For Markdown the return sign is reversed, so a larger stage-aligned value is always better agreement with the regime direction.",
        "",
    ]
    for field in CONFIDENCE_FIELDS:
        agg = report["aggregate"]["confidence_fields"][field]
        high_rate = "—" if agg["high_better_than_low_rate"] is None else f"{agg['high_better_than_low_rate'] * 100:.1f}%"
        mono_rate = "—" if agg["monotonic_rate"] is None else f"{agg['monotonic_rate'] * 100:.1f}%"
        lines.extend(
            [
                f"## {field}",
                "",
                f"High confidence beats low confidence in **{agg['high_better_than_low_cases']} / {agg['high_low_comparable_cases']}** comparable cases ({high_rate}).",
                f"Strict Low ≤ Medium ≤ High monotonicity appears in **{agg['monotonic_cases']} / {agg['all_bins_comparable_cases']}** cases with all three bins sufficiently populated ({mono_rate}).",
                "",
                "| Pair | Stage | H | Low/Med/High n | High − Low aligned return | High better? | Monotonic? |",
                "|---|---:|---:|---|---:|---|---|",
            ]
        )
        for row in agg["rows"]:
            counts = row["bin_counts"]
            diff = row["high_minus_low_stage_aligned_return"]
            diff_text = "—" if diff is None else f"{diff * 100:.3f}%"
            high_text = "—" if row["high_better_than_low"] is None else ("yes" if row["high_better_than_low"] else "no")
            mono_text = "—" if row["monotonic_low_medium_high"] is None else ("yes" if row["monotonic_low_medium_high"] else "no")
            lines.append(
                f"| {row['pair']} | {row['stage']} | {row['horizon']} | "
                f"{counts['low']}/{counts['medium']}/{counts['high']} | {diff_text} | {high_text} | {mono_text} |"
            )
        lines.append("")
    lines.extend([
        "Boundary: Development-derived bins + Exploratory OOS outcomes only; final OOS remains sealed.",
        "",
    ])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    here = Path(__file__).resolve().parent
    parser.add_argument("--manifest", type=Path, default=here / "data" / "issue-55-static-fx-canonical-manifest.json")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--md-output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_report(args.manifest)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.md_output:
        args.md_output.parent.mkdir(parents=True, exist_ok=True)
        args.md_output.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["aggregate"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
