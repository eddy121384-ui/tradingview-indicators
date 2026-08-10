#!/usr/bin/env python3
"""One-shot Final-OOS evaluation for Issue #55.

The Final-OOS opening record must already exist. This script evaluates the exact
frozen model, static FX fixture, response map, lag, costs, and baselines on the
predeclared 2020-04-30..2022-03-04 final partition. It does not tune anything.

Outputs cover:
- all six formal states' bar-level future paths at 5/10/20/60 bars;
- tail returns and 20-bar new-high/new-low continuation;
- formal-state occupancy, complete episode duration, and next-state transition;
- Development-frozen Evidence / Top Gap calibration on Final OOS;
- frozen response trading utility versus fixed FX baselines.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from evaluate_confidence_calibration_pre_final import (
    CONFIDENCE_FIELDS,
    DIRECTIONAL_STAGES,
    MIN_DEV_STATE_N,
    MIN_EXP_BIN_N,
    confidence_bin,
    development_cutpoints,
)
from evaluate_regime_episodes_pre_final import runs_in_split
from evaluate_regime_paths_pre_final import HORIZONS, future_metrics, load_frozen_pair
from evaluate_state_separation_pre_final import METRICS, MIN_GROUP_N, eta_squared
from evaluate_trading_utility_exploratory import (
    PRIMARY_COST_PIPS,
    aggregate_equal_weight,
    evaluate_targets,
    strategy_targets,
    PIP_SIZE,
)
from price_only_core import STAGE_NAMES, PriceOnlyConfig, compute_price_only


STAGES = tuple(range(1, 7))
CONTINUATION_LOOKBACK = 20


def _number(value) -> float | None:
    value = float(value)
    return value if np.isfinite(value) else None


def _mean(values: np.ndarray) -> float | None:
    finite = values[np.isfinite(values)]
    return float(np.mean(finite)) if len(finite) else None


def _median(values: np.ndarray) -> float | None:
    finite = values[np.isfinite(values)]
    return float(np.median(finite)) if len(finite) else None


def _quantile(values: np.ndarray, q: float) -> float | None:
    finite = values[np.isfinite(values)]
    return float(np.quantile(finite, q)) if len(finite) else None


def path_summary(
    frame: pd.DataFrame,
    formal: np.ndarray,
    start: int,
    end: int,
    horizon: int,
) -> dict:
    metrics = future_metrics(frame, horizon)
    high = pd.to_numeric(frame["high"], errors="coerce")
    low = pd.to_numeric(frame["low"], errors="coerce")
    prior_high = high.shift(1).rolling(CONTINUATION_LOOKBACK, min_periods=CONTINUATION_LOOKBACK).max().to_numpy(float)
    prior_low = low.shift(1).rolling(CONTINUATION_LOOKBACK, min_periods=CONTINUATION_LOOKBACK).min().to_numpy(float)
    high_array = high.to_numpy(float)
    low_array = low.to_numpy(float)

    last_origin = end - horizon
    result = {"eligible_origin_rows": max(0, last_origin - start + 1), "by_formal_stage": {}}
    for stage in STAGES:
        origins = [i for i in range(start, last_origin + 1) if formal[i] == stage]
        returns = np.array([metrics["forward_return"][i] for i in origins], dtype=float)
        mfe = np.array([metrics["mfe"][i] for i in origins], dtype=float)
        mae = np.array([metrics["mae"][i] for i in origins], dtype=float)
        vol = np.array([metrics["realized_vol"][i] for i in origins], dtype=float)
        new_high = []
        new_low = []
        for i in origins:
            if np.isfinite(prior_high[i]):
                new_high.append(float(np.max(high_array[i + 1 : i + horizon + 1]) > prior_high[i]))
            if np.isfinite(prior_low[i]):
                new_low.append(float(np.min(low_array[i + 1 : i + horizon + 1]) < prior_low[i]))
        finite_return = returns[np.isfinite(returns)]
        result["by_formal_stage"][str(stage)] = {
            "sample_count": int(len(finite_return)),
            "forward_return_mean": _mean(returns),
            "forward_return_median": _median(returns),
            "forward_return_q05": _quantile(returns, 0.05),
            "forward_return_q95": _quantile(returns, 0.95),
            "positive_return_rate": float(np.mean(finite_return > 0.0)) if len(finite_return) else None,
            "mfe_mean": _mean(mfe),
            "mae_mean": _mean(mae),
            "realized_vol_mean": _mean(vol),
            "new_20bar_high_within_horizon_rate": float(np.mean(new_high)) if new_high else None,
            "new_20bar_low_within_horizon_rate": float(np.mean(new_low)) if new_low else None,
        }

    retained = [stage for stage in STAGES if result["by_formal_stage"][str(stage)]["sample_count"] >= MIN_GROUP_N]
    valid_origins = [
        i
        for i in range(start, last_origin + 1)
        if formal[i] in retained and np.isfinite(metrics["forward_return"][i])
    ]
    separation = {}
    for metric in METRICS:
        idx = np.array([i for i in valid_origins if np.isfinite(metrics[metric][i])], dtype=int)
        if len(idx):
            separation[metric] = eta_squared(metrics[metric][idx], formal[idx].astype(float))
        else:
            separation[metric] = None
    result["separation"] = {
        "minimum_group_n": MIN_GROUP_N,
        "retained_stages": retained,
        "metric_eta_squared": separation,
    }

    markup = result["by_formal_stage"]["2"]["forward_return_mean"]
    markdown = result["by_formal_stage"]["5"]["forward_return_mean"]
    result["directional_sanity"] = {
        "markup_mean_minus_markdown_mean": None if markup is None or markdown is None else markup - markdown,
        "markup_above_markdown": None if markup is None or markdown is None else markup > markdown,
    }
    return result


def episode_summary(formal: np.ndarray, start: int, end: int) -> dict:
    values = formal[start : end + 1]
    counts = {str(stage): int(np.sum(values == stage)) for stage in range(0, 7)}
    shares = {str(stage): counts[str(stage)] / len(values) for stage in range(0, 7)}
    runs = runs_in_split(formal, start, end)
    stages = {}
    for stage in STAGES:
        stage_runs = [run for run in runs if int(run["stage"]) == stage]
        complete = [run for run in stage_runs if not run["left_censored"] and not run["right_censored"]]
        durations = np.array([run["duration_rows"] for run in complete], dtype=float)
        next_counts = {str(next_stage): 0 for next_stage in range(0, 7)}
        for index, run in enumerate(runs[:-1]):
            if int(run["stage"]) == stage:
                next_counts[str(int(runs[index + 1]["stage"]))] += 1
        transition_total = sum(next_counts.values())
        stages[str(stage)] = {
            "bar_count": counts[str(stage)],
            "bar_share": shares[str(stage)],
            "run_count_including_censored": len(stage_runs),
            "complete_episode_count": len(complete),
            "complete_duration_mean": _mean(durations),
            "complete_duration_median": _median(durations),
            "next_state_counts": next_counts,
            "next_state_rates": {
                key: (value / transition_total if transition_total else None)
                for key, value in next_counts.items()
            },
        }
    return {
        "state_counts_including_zero": counts,
        "state_shares_including_zero": shares,
        "stages": stages,
    }


def confidence_final(model: pd.DataFrame, formal: np.ndarray, meta: dict, metrics_by_horizon: dict) -> dict:
    dev = meta["splits"]["development"]
    final = meta["splits"]["final_oos"]
    dev_start, dev_end = int(dev["start_index"]), int(dev["end_index"])
    final_start, final_end = int(final["start_index"]), int(final["end_index"])
    result = {}
    for stage, direction in DIRECTIONAL_STAGES.items():
        stage_result = {}
        dev_mask = np.zeros(len(model), dtype=bool)
        dev_mask[dev_start : dev_end + 1] = True
        dev_mask &= formal == stage
        for field in CONFIDENCE_FIELDS:
            confidence = pd.to_numeric(model[field], errors="coerce").to_numpy(float)
            cutpoints = development_cutpoints(confidence[dev_mask])
            field_result = {
                "development_state_bar_count": int(np.sum(dev_mask & np.isfinite(confidence))),
                "development_cutpoints": None,
                "horizons": {},
            }
            if cutpoints is None:
                field_result["skip_reason"] = f"development stage count < {MIN_DEV_STATE_N}"
                stage_result[field] = field_result
                continue
            low_cut, high_cut = cutpoints
            field_result["development_cutpoints"] = {"q33": low_cut, "q67": high_cut}
            for horizon in HORIZONS:
                last_origin = final_end - horizon
                bins = {"low": [], "medium": [], "high": []}
                for i in range(final_start, last_origin + 1):
                    if formal[i] != stage:
                        continue
                    fwd = metrics_by_horizon[horizon]["forward_return"][i]
                    bucket = confidence_bin(confidence[i], low_cut, high_cut)
                    if bucket is not None and np.isfinite(fwd):
                        bins[bucket].append(float(fwd) * direction)
                means = {bucket: (_mean(np.asarray(values, dtype=float)) if values else None) for bucket, values in bins.items()}
                counts = {bucket: len(values) for bucket, values in bins.items()}
                comparable = counts["low"] >= MIN_EXP_BIN_N and counts["high"] >= MIN_EXP_BIN_N
                all_bins = all(counts[bucket] >= MIN_EXP_BIN_N for bucket in bins)
                high_minus_low = None if not comparable else means["high"] - means["low"]
                monotonic = None if not all_bins else means["low"] <= means["medium"] <= means["high"]
                field_result["horizons"][str(horizon)] = {
                    "bin_counts": counts,
                    "stage_aligned_return_mean": means,
                    "high_minus_low_stage_aligned_return": high_minus_low,
                    "high_better_than_low": None if high_minus_low is None else high_minus_low > 0.0,
                    "monotonic_low_medium_high": monotonic,
                }
            stage_result[field] = field_result
        result[str(stage)] = stage_result
    return result


def confidence_aggregate(pair_results: dict) -> dict:
    output = {}
    for field in CONFIDENCE_FIELDS:
        comparable = better = all_bins = monotonic = 0
        for pair_result in pair_results.values():
            for stage in DIRECTIONAL_STAGES:
                field_result = pair_result["confidence"][str(stage)][field]
                if field_result["development_cutpoints"] is None:
                    continue
                for row in field_result["horizons"].values():
                    if row["high_better_than_low"] is not None:
                        comparable += 1
                        better += int(bool(row["high_better_than_low"]))
                    if row["monotonic_low_medium_high"] is not None:
                        all_bins += 1
                        monotonic += int(bool(row["monotonic_low_medium_high"]))
        output[field] = {
            "high_low_comparable_cases": comparable,
            "high_better_than_low_cases": better,
            "high_better_than_low_rate": better / comparable if comparable else None,
            "all_bins_comparable_cases": all_bins,
            "monotonic_cases": monotonic,
            "monotonic_rate": monotonic / all_bins if all_bins else None,
        }
    return output


def analyze_pair(pair: str, frame: pd.DataFrame, meta: dict) -> tuple[dict, dict[str, pd.DataFrame]]:
    final = meta["splits"]["final_oos"]
    start, end = int(final["start_index"]), int(final["end_index"])
    model = compute_price_only(frame.reset_index(drop=True), PriceOnlyConfig())
    formal = pd.to_numeric(model["formal_id"], errors="coerce").fillna(0).to_numpy(int)
    metrics_by_horizon = {h: future_metrics(frame, h) for h in HORIZONS}

    paths = {str(h): path_summary(frame, formal, start, end, h) for h in HORIZONS}
    episodes = episode_summary(formal, start, end)
    confidence = confidence_final(model, formal, meta, metrics_by_horizon)

    targets = strategy_targets(frame, model)
    strategies = {}
    daily_outputs = {}
    for name, target in targets.items():
        perf, daily = evaluate_targets(frame, target, start, end, PIP_SIZE[pair], PRIMARY_COST_PIPS)
        strategies[name] = perf
        daily_outputs[name] = daily

    return (
        {
            "final_start_date": final["start_date"],
            "final_end_date": final["end_date"],
            "final_rows": final["rows"],
            "model_rows_computed": len(frame),
            "bar_level_paths": paths,
            "episodes": episodes,
            "confidence": confidence,
            "strategies": strategies,
        },
        daily_outputs,
    )


def final_summary(pair_results: dict, aggregate_strategies: dict, confidence: dict) -> dict:
    directional = []
    eta_return = []
    populated = []
    for pair, result in pair_results.items():
        stage_shares = result["episodes"]["stages"]
        populated.append(sum(stage_shares[str(stage)]["bar_share"] >= 0.01 for stage in STAGES))
        for horizon in HORIZONS:
            row = result["bar_level_paths"][str(horizon)]
            sanity = row["directional_sanity"]["markup_above_markdown"]
            if sanity is not None:
                directional.append(bool(sanity))
            eta = row["separation"]["metric_eta_squared"]["forward_return"]
            if eta is not None:
                eta_return.append(float(eta))

    wyckoff = aggregate_strategies["wyckoff_frozen_response"]
    beat_rows = {}
    for baseline in ("sma200", "momentum60", "donchian55"):
        base = aggregate_strategies[baseline]
        beat_rows[baseline] = {
            "net_annualized_return_difference": wyckoff["net_annualized_return"] - base["net_annualized_return"],
            "sharpe_difference": (
                None
                if wyckoff["annualized_sharpe_zero_cash"] is None or base["annualized_sharpe_zero_cash"] is None
                else wyckoff["annualized_sharpe_zero_cash"] - base["annualized_sharpe_zero_cash"]
            ),
        }
    positive_pairs = sum(
        pair_result["strategies"]["wyckoff_frozen_response"]["net_annualized_return"] > 0.0
        for pair_result in pair_results.values()
    )
    return {
        "markup_above_markdown_cases": int(sum(directional)),
        "directional_comparable_cases": len(directional),
        "median_final_return_eta_squared": float(np.median(eta_return)) if eta_return else None,
        "median_materially_populated_stage_count": float(np.median(populated)) if populated else None,
        "wyckoff_positive_pair_count": int(positive_pairs),
        "pair_count": len(pair_results),
        "wyckoff_equal_weight": wyckoff,
        "wyckoff_vs_baseline": beat_rows,
        "confidence_calibration": confidence,
    }


def build_report(manifest_path: Path, opening_record: Path) -> dict:
    if not opening_record.exists():
        raise ValueError("Final OOS opening record is missing; refusing to evaluate final sample")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("final_oos_status") != "SEALED_DO_NOT_EVALUATE":
        raise ValueError("canonical manifest seal changed unexpectedly")

    pairs = {}
    pair_daily = {}
    for pair, meta in manifest["pairs"].items():
        result, daily = analyze_pair(pair, load_frozen_pair(manifest_path, meta), meta)
        pairs[pair] = result
        pair_daily[pair] = daily
    aggregate_strategies = aggregate_equal_weight(pair_daily)
    confidence = confidence_aggregate(pairs)
    summary = final_summary(pairs, aggregate_strategies, confidence)
    return {
        "schema_version": 1,
        "issue": 55,
        "status": "FINAL_OOS_OPENED_AND_EVALUATED_ONE_SHOT",
        "final_window": {"start": "2020-04-30", "end": "2022-03-04", "rows_per_pair": 480},
        "continuation_definition": (
            "new-high/new-low uses the previous 20 completed daily highs/lows as the reference and asks whether "
            "the next horizon bars exceed/breach that reference"
        ),
        "tail_definition": "forward-return q05 and q95 within each formal state/horizon",
        "response_map_source": "decisions/issue-55-final-oos-response-map-and-baselines.md",
        "primary_cost_pips_per_unit_turnover": PRIMARY_COST_PIPS,
        "pairs": pairs,
        "equal_weight_four_pair_strategies": aggregate_strategies,
        "final_summary": summary,
        "boundary": (
            "This is the one-shot Final-OOS result. Do not alter the frozen model, mapping, lookbacks, lag, cost, "
            "or this final window and rerun it as an independent test. Any redesign requires a new sample."
        ),
    }


def render_markdown(report: dict) -> str:
    summary = report["final_summary"]
    lines = [
        "# Issue #55 — ONE-SHOT Final-OOS result",
        "",
        "Final OOS has been **OPENED AND EVALUATED**. This sample may not be reused as an independent test after any rule change.",
        "",
        "Window: **2020-04-30 through 2022-03-04**, 480 daily bars per pair.",
        "",
        "## Final directional / state-separation summary",
        "",
        f"- Formal Markup mean return exceeds Formal Markdown in **{summary['markup_above_markdown_cases']} / {summary['directional_comparable_cases']}** pair × horizon comparisons.",
        f"- Median formal-state forward-return eta-squared: **{summary['median_final_return_eta_squared']:.3f}**." if summary["median_final_return_eta_squared"] is not None else "- Median return eta-squared: —.",
        f"- Median count of stages occupying at least 1% of Final-OOS bars: **{summary['median_materially_populated_stage_count']:.1f} / 6**.",
        "",
        "## Frozen-response trading utility — equal-weight four-pair aggregate",
        "",
        "| Strategy | Net ann. return | Vol | Sharpe | Max DD | Exposure | Turnover |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name in ("wyckoff_frozen_response", "sma200", "momentum60", "donchian55", "always_flat"):
        row = report["equal_weight_four_pair_strategies"][name]
        def pct(value):
            return "—" if value is None else f"{value * 100:.2f}%"
        sharpe = "—" if row["annualized_sharpe_zero_cash"] is None else f"{row['annualized_sharpe_zero_cash']:.2f}"
        lines.append(
            f"| {name} | {pct(row['net_annualized_return'])} | {pct(row['annualized_volatility'])} | {sharpe} | "
            f"{pct(row['max_drawdown'])} | {row['average_absolute_exposure'] * 100:.1f}% | {row['total_turnover']:.1f} |"
        )

    lines.extend(["", "### Wyckoff per pair", ""])
    lines.append("| Pair | Net ann. return | Sharpe | Max DD | Exposure |")
    lines.append("|---|---:|---:|---:|---:|")
    for pair, result in report["pairs"].items():
        row = result["strategies"]["wyckoff_frozen_response"]
        def pct(value):
            return "—" if value is None else f"{value * 100:.2f}%"
        sharpe = "—" if row["annualized_sharpe_zero_cash"] is None else f"{row['annualized_sharpe_zero_cash']:.2f}"
        lines.append(f"| {pair} | {pct(row['net_annualized_return'])} | {sharpe} | {pct(row['max_drawdown'])} | {row['average_absolute_exposure'] * 100:.1f}% |")

    lines.extend(["", "## Final confidence calibration", ""])
    for field, row in summary["confidence_calibration"].items():
        high_rate = "—" if row["high_better_than_low_rate"] is None else f"{row['high_better_than_low_rate'] * 100:.1f}%"
        mono_rate = "—" if row["monotonic_rate"] is None else f"{row['monotonic_rate'] * 100:.1f}%"
        lines.append(
            f"- `{field}`: high beats low **{row['high_better_than_low_cases']}/{row['high_low_comparable_cases']}** ({high_rate}); "
            f"strict monotonic **{row['monotonic_cases']}/{row['all_bins_comparable_cases']}** ({mono_rate})."
        )

    lines.extend(["", "## All-six-state bar-level path snapshot", ""])
    for horizon in HORIZONS:
        lines.append(f"### {horizon}-bar horizon")
        lines.append("")
        lines.append("| Pair | Stage | n | Mean return | MFE | MAE | Vol | New20H | New20L |")
        lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|")
        for pair, result in report["pairs"].items():
            stages = result["bar_level_paths"][str(horizon)]["by_formal_stage"]
            for stage in STAGES:
                row = stages[str(stage)]
                def pct(value):
                    return "—" if value is None else f"{value * 100:.2f}%"
                lines.append(
                    f"| {pair} | {stage} {STAGE_NAMES[stage]} | {row['sample_count']} | {pct(row['forward_return_mean'])} | "
                    f"{pct(row['mfe_mean'])} | {pct(row['mae_mean'])} | {pct(row['realized_vol_mean'])} | "
                    f"{pct(row['new_20bar_high_within_horizon_rate'])} | {pct(row['new_20bar_low_within_horizon_rate'])} |"
                )
        lines.append("")

    lines.extend([
        "Full JSON contains q05/q95 tail returns, medians, positive-return rates, episode durations, and next-state transition matrices.",
        "",
        "Boundary: this is the one-shot Final-OOS result. Any redesign now requires a new independent sample.",
        "",
    ])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    here = Path(__file__).resolve().parent
    parser.add_argument("--manifest", type=Path, default=here / "data" / "issue-55-static-fx-canonical-manifest.json")
    parser.add_argument("--opening-record", type=Path, default=here / "decisions" / "issue-55-final-oos-opening.md")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--md-output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_report(args.manifest, args.opening_record)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.md_output:
        args.md_output.parent.mkdir(parents=True, exist_ok=True)
        args.md_output.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["final_summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
