#!/usr/bin/env python3
"""Evaluate Issue #55 regime future paths without opening final OOS.

This first economic/descriptive pass is deliberately limited to the development
and exploratory-OOS partitions of the already frozen canonical FX fixture.
Final-OOS model outputs are not computed, and a bar is excluded whenever its
forward horizon would cross the end of its allowed partition.

The report is descriptive only: it does not yet implement the preregistered
regime-response trading map or benchmark comparisons.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from price_only_core import STAGE_NAMES, PriceOnlyConfig, compute_price_only


HORIZONS = (5, 10, 20, 60)
ALLOWED_SPLITS = ("development", "exploratory_oos")
STAGES = tuple(range(1, 7))


def load_frozen_pair(manifest_path: Path, meta: dict) -> pd.DataFrame:
    path = manifest_path.parent / meta["frozen_file"]
    frame = pd.read_csv(path)
    frame["date"] = pd.to_datetime(frame["date"], errors="raise").dt.date
    return frame


def safe_mean(values: np.ndarray) -> float | None:
    finite = values[np.isfinite(values)]
    return float(np.mean(finite)) if len(finite) else None


def safe_median(values: np.ndarray) -> float | None:
    finite = values[np.isfinite(values)]
    return float(np.median(finite)) if len(finite) else None


def future_metrics(frame: pd.DataFrame, horizon: int) -> dict[str, np.ndarray]:
    close = frame["close"].to_numpy(float)
    high = frame["high"].to_numpy(float)
    low = frame["low"].to_numpy(float)
    n = len(frame)
    fwd_return = np.full(n, np.nan)
    mfe = np.full(n, np.nan)
    mae = np.full(n, np.nan)
    realized_vol = np.full(n, np.nan)

    log_returns = np.full(n, np.nan)
    log_returns[1:] = np.log(close[1:] / close[:-1])

    for i in range(n):
        end = i + horizon
        if end >= n:
            continue
        base = close[i]
        if not np.isfinite(base) or base <= 0:
            continue
        future_high = high[i + 1 : end + 1]
        future_low = low[i + 1 : end + 1]
        future_lr = log_returns[i + 1 : end + 1]
        fwd_return[i] = close[end] / base - 1.0
        mfe[i] = np.max(future_high) / base - 1.0
        mae[i] = np.min(future_low) / base - 1.0
        if np.all(np.isfinite(future_lr)) and len(future_lr) > 1:
            realized_vol[i] = np.std(future_lr, ddof=1) * np.sqrt(252.0)

    return {
        "forward_return": fwd_return,
        "mfe": mfe,
        "mae": mae,
        "realized_vol": realized_vol,
    }


def summarize_mask(metrics: dict[str, np.ndarray], mask: np.ndarray) -> dict:
    count = int(np.sum(mask))
    result = {"sample_count": count}
    for metric_name, values in metrics.items():
        selected = values[mask]
        result[metric_name] = {
            "mean": safe_mean(selected),
            "median": safe_median(selected),
        }
    selected_return = metrics["forward_return"][mask]
    finite_return = selected_return[np.isfinite(selected_return)]
    result["positive_return_rate"] = (
        float(np.mean(finite_return > 0.0)) if len(finite_return) else None
    )
    return result


def analyze_pair(frame: pd.DataFrame, meta: dict) -> dict:
    exploratory_end = int(meta["splits"]["exploratory_oos"]["end_index"])
    # Causality/final seal: never even compute the model on final-OOS rows.
    pre_final = frame.iloc[: exploratory_end + 1].copy().reset_index(drop=True)
    model = compute_price_only(pre_final, PriceOnlyConfig())
    formal = pd.to_numeric(model["formal_id"], errors="coerce").fillna(0).to_numpy(int)
    evidence = pd.to_numeric(model["evidence_strength"], errors="coerce").to_numpy(float)
    top_gap = pd.to_numeric(model["top_gap"], errors="coerce").to_numpy(float)

    result = {
        "model_rows_computed": len(pre_final),
        "final_oos_rows_computed": 0,
        "formal_state_counts_pre_final": {
            str(stage): int(np.sum(formal == stage)) for stage in STAGES
        },
        "splits": {},
    }

    for split_name in ALLOWED_SPLITS:
        split = meta["splits"][split_name]
        start = int(split["start_index"])
        end = int(split["end_index"])
        split_result = {
            "start_date": split["start_date"],
            "end_date": split["end_date"],
            "rows": split["rows"],
            "horizons": {},
        }
        for horizon in HORIZONS:
            metrics = future_metrics(pre_final, horizon)
            valid_index = np.zeros(len(pre_final), dtype=bool)
            # The forward path must end inside the same partition: no boundary leakage.
            last_origin = end - horizon
            if last_origin >= start:
                valid_index[start : last_origin + 1] = True
            finite = np.isfinite(metrics["forward_return"])
            horizon_result = {
                "eligible_origin_rows": int(np.sum(valid_index & finite)),
                "by_formal_stage": {},
            }
            for stage in STAGES:
                mask = valid_index & finite & (formal == stage)
                horizon_result["by_formal_stage"][str(stage)] = summarize_mask(metrics, mask)
            split_result["horizons"][str(horizon)] = horizon_result
        result["splits"][split_name] = split_result

    # Confidence descriptors only, no future outcome calibration yet.
    for name, values in (("evidence_strength", evidence), ("top_gap", top_gap)):
        finite = values[np.isfinite(values)]
        result[name + "_pre_final"] = {
            "mean": float(np.mean(finite)) if len(finite) else None,
            "median": float(np.median(finite)) if len(finite) else None,
        }
    return result


def directional_separation_summary(report: dict) -> dict:
    """Compact diagnostic: Markup vs Markdown mean forward returns, no trade rule."""
    rows = []
    for pair, pair_report in report["pairs"].items():
        for split_name in ALLOWED_SPLITS:
            for horizon in HORIZONS:
                stages = pair_report["splits"][split_name]["horizons"][str(horizon)]["by_formal_stage"]
                markup = stages["2"]["forward_return"]["mean"]
                markdown = stages["5"]["forward_return"]["mean"]
                rows.append(
                    {
                        "pair": pair,
                        "split": split_name,
                        "horizon": horizon,
                        "markup_mean_return": markup,
                        "markdown_mean_return": markdown,
                        "markup_minus_markdown": (
                            None if markup is None or markdown is None else markup - markdown
                        ),
                        "markup_n": stages["2"]["sample_count"],
                        "markdown_n": stages["5"]["sample_count"],
                    }
                )
    valid = [row["markup_minus_markdown"] for row in rows if row["markup_minus_markdown"] is not None]
    return {
        "rows": rows,
        "positive_markup_minus_markdown_cases": int(sum(value > 0 for value in valid)),
        "comparable_cases": len(valid),
        "median_markup_minus_markdown": float(np.median(valid)) if valid else None,
    }


def build_report(manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("final_oos_status") != "SEALED_DO_NOT_EVALUATE":
        raise ValueError("refusing to run: final-OOS seal missing")
    pairs = {}
    for pair, meta in manifest["pairs"].items():
        pairs[pair] = analyze_pair(load_frozen_pair(manifest_path, meta), meta)
    report = {
        "schema_version": 1,
        "issue": 55,
        "status": "pre_final_descriptive_regime_path_analysis",
        "canonical_manifest": str(manifest_path),
        "horizons": list(HORIZONS),
        "stage_names": {str(stage): STAGE_NAMES[stage] for stage in STAGES},
        "final_oos_status": "SEALED_NOT_COMPUTED",
        "pairs": pairs,
        "boundary": (
            "Development and exploratory OOS only. No final-OOS model output or future path is computed. "
            "This is descriptive regime separation, not a trading-strategy or incremental-utility result."
        ),
    }
    report["directional_separation_diagnostic"] = directional_separation_summary(report)
    return report


def render_markdown(report: dict) -> str:
    lines = [
        "# Issue #55 — Pre-final-OOS regime path report",
        "",
        "Final OOS remains **SEALED / NOT COMPUTED**.",
        "",
        "This first pass asks only whether formal Markup (2) and Markdown (5) states point to different future close-return directions. It is not yet a trading backtest.",
        "",
        "| Pair | Split | Horizon | Markup mean | n | Markdown mean | n | Mk − Md |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in report["directional_separation_diagnostic"]["rows"]:
        def pct(value):
            return "—" if value is None else f"{value * 100:.3f}%"
        lines.append(
            f"| {row['pair']} | {row['split']} | {row['horizon']} | {pct(row['markup_mean_return'])} | "
            f"{row['markup_n']} | {pct(row['markdown_mean_return'])} | {row['markdown_n']} | "
            f"{pct(row['markup_minus_markdown'])} |"
        )
    diag = report["directional_separation_diagnostic"]
    lines.extend(
        [
            "",
            f"Directional sign check: Markup minus Markdown is positive in **{diag['positive_markup_minus_markdown_cases']} / {diag['comparable_cases']}** pair/split/horizon comparisons.",
            f"Median Markup-minus-Markdown spread: **{diag['median_markup_minus_markdown'] * 100:.3f}%**" if diag["median_markup_minus_markdown"] is not None else "Median spread: —",
            "",
            "Full JSON alongside this report contains all six stages plus MFE, MAE, realized volatility, medians and positive-return rates.",
            "",
            "Boundary: descriptive development + exploratory OOS only; no final OOS and no trading utility claim.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    here = Path(__file__).resolve().parent
    parser.add_argument(
        "--manifest",
        type=Path,
        default=here / "data" / "issue-55-static-fx-canonical-manifest.json",
    )
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--md-output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_report(args.manifest)
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(text, encoding="utf-8")
    if args.md_output:
        args.md_output.parent.mkdir(parents=True, exist_ok=True)
        args.md_output.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["directional_separation_diagnostic"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
