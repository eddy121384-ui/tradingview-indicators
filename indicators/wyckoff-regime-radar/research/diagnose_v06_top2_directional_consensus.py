#!/usr/bin/env python3
"""Burned-data diagnostic for Issue #57 Top-2 directional consensus.

This is hypothesis-development only. It evaluates the already-observed Issue #55
and Issue #57 Phase-E FX fixtures. It must not be described as independent OOS.

Primary user-originated hypothesis:
- rank the six v0.6 stage weights;
- Top1 and Top2 must be in the same directional family;
- Top1 + Top2 >= 90%;
- bullish family = stages 1/2/3, bearish family = stages 4/5/6.

80/85/95 are sensitivity-only and may not replace 90 because they backtest better.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from generate_v06_phase_b_core import load_phase_b_namespace


HERE = Path(__file__).resolve().parent
ISSUE55_MANIFEST = HERE / "data" / "issue-55-static-fx-canonical-manifest.json"
ISSUE57_MANIFEST = HERE / "data" / "issue-57-phase-e-holdout-manifest.json"
HORIZONS = (5, 10, 20, 60)
PRIMARY_THRESHOLD = 90.0
SENSITIVITY_THRESHOLDS = (80.0, 85.0, 90.0, 95.0)
STAGE_TO_DIRECTION = {0: 0, 1: 1, 2: 1, 3: 1, 4: -1, 5: -1, 6: -1}
PIP_SIZE = {
    "EURUSD": 0.0001,
    "GBPUSD": 0.0001,
    "AUDUSD": 0.0001,
    "USDJPY": 0.01,
    "USDCAD": 0.0001,
    "USDCHF": 0.0001,
    "EURCHF": 0.0001,
}
ANNUALIZATION = 252.0
COST_PIPS = 1.0
WEIGHT_COLUMNS = (
    "prob_acc",
    "prob_markup",
    "prob_reacc",
    "prob_dist",
    "prob_markdown",
    "prob_redist",
)


def load_burned_pairs() -> dict[str, pd.DataFrame]:
    pairs: dict[str, pd.DataFrame] = {}
    for manifest_path in (ISSUE55_MANIFEST, ISSUE57_MANIFEST):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for pair, meta in manifest["pairs"].items():
            path = manifest_path.parent / meta["frozen_file"]
            frame = pd.read_csv(path)
            frame["date"] = pd.to_datetime(frame["date"], errors="raise").dt.date
            pairs[pair] = frame.reset_index(drop=True)
    expected = {"EURUSD", "USDJPY", "GBPUSD", "AUDUSD", "USDCAD", "USDCHF", "EURCHF"}
    if set(pairs) != expected:
        raise RuntimeError(f"burned pair set drifted: {sorted(pairs)}")
    return pairs


def compute_v06(frame: pd.DataFrame) -> pd.DataFrame:
    ns = load_phase_b_namespace()
    compute: Callable = ns["compute_price_only"]  # type: ignore[assignment]
    config_cls = ns["PriceOnlyConfig"]
    return compute(frame.copy(), config_cls())


def directional_weight_matrix(model: pd.DataFrame) -> np.ndarray:
    weights = model.loc[:, WEIGHT_COLUMNS].apply(pd.to_numeric, errors="coerce").to_numpy(float)
    return weights


def top_ids_and_values(model: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    weights = directional_weight_matrix(model)
    safe = np.where(np.isfinite(weights), weights, -np.inf)
    order = np.argsort(safe, axis=1)[:, ::-1]
    top1_index = order[:, 0]
    top2_index = order[:, 1]
    rows = np.arange(len(model))
    top1_value = safe[rows, top1_index]
    top2_value = safe[rows, top2_index]
    top1_id = top1_index + 1
    top2_id = top2_index + 1
    invalid = ~np.isfinite(top1_value) | (top1_value <= 0.0)
    top1_id = top1_id.astype(int)
    top2_id = top2_id.astype(int)
    top1_id[invalid] = 0
    top2_id[invalid] = 0
    top1_value[invalid] = np.nan
    top2_value[invalid] = np.nan
    return top1_id, top2_id, top1_value, top2_value


def map_direction(ids: np.ndarray) -> np.ndarray:
    return np.array([STAGE_TO_DIRECTION.get(int(value), 0) for value in ids], dtype=float)


def top2_consensus_signal(model: pd.DataFrame, threshold: float = PRIMARY_THRESHOLD) -> np.ndarray:
    top1_id, top2_id, top1_value, top2_value = top_ids_and_values(model)
    dir1 = map_direction(top1_id)
    dir2 = map_direction(top2_id)
    total = top1_value + top2_value
    aligned = (dir1 != 0.0) & (dir1 == dir2) & np.isfinite(total) & (total >= threshold)
    return np.where(aligned, dir1, 0.0)


def top1_signal(model: pd.DataFrame) -> np.ndarray:
    top1_id, _, top1_value, _ = top_ids_and_values(model)
    direction = map_direction(top1_id)
    return np.where(np.isfinite(top1_value) & (top1_value > 0.0), direction, 0.0)


def formal_family_signal(model: pd.DataFrame) -> np.ndarray:
    ids = pd.to_numeric(model["formal_id"], errors="coerce").fillna(0).to_numpy(int)
    return map_direction(ids)


def formal_trend_only_signal(model: pd.DataFrame) -> np.ndarray:
    ids = pd.to_numeric(model["formal_id"], errors="coerce").fillna(0).to_numpy(int)
    mapping = {0: 0.0, 1: 0.0, 2: 1.0, 3: 1.0, 4: 0.0, 5: -1.0, 6: -1.0}
    return np.array([mapping.get(int(value), 0.0) for value in ids], dtype=float)


def future_aligned_metrics(frame: pd.DataFrame, signal: np.ndarray, horizon: int) -> dict[str, float | int | None]:
    close = pd.to_numeric(frame["close"], errors="coerce").to_numpy(float)
    high = pd.to_numeric(frame["high"], errors="coerce").to_numpy(float)
    low = pd.to_numeric(frame["low"], errors="coerce").to_numpy(float)
    aligned_returns: list[float] = []
    favorable: list[float] = []
    adverse: list[float] = []
    n = len(frame)
    eligible = 0
    for i in range(0, n - horizon):
        direction = float(signal[i])
        if direction == 0.0 or not np.isfinite(close[i]) or close[i] <= 0.0:
            continue
        eligible += 1
        base = close[i]
        fwd = close[i + horizon] / base - 1.0
        aligned_returns.append(direction * fwd)
        future_high = float(np.max(high[i + 1 : i + horizon + 1]))
        future_low = float(np.min(low[i + 1 : i + horizon + 1]))
        if direction > 0:
            favorable.append(future_high / base - 1.0)
            adverse.append(future_low / base - 1.0)
        else:
            favorable.append(1.0 - future_low / base)
            adverse.append(1.0 - future_high / base)
    values = np.asarray(aligned_returns, dtype=float)
    fav = np.asarray(favorable, dtype=float)
    adv = np.asarray(adverse, dtype=float)
    if not len(values):
        return {
            "signal_origins": 0,
            "coverage": 0.0,
            "mean_aligned_return": None,
            "median_aligned_return": None,
            "hit_rate": None,
            "mean_aligned_mfe": None,
            "mean_aligned_mae": None,
        }
    return {
        "signal_origins": eligible,
        "coverage": eligible / (n - horizon),
        "mean_aligned_return": float(np.mean(values)),
        "median_aligned_return": float(np.median(values)),
        "hit_rate": float(np.mean(values > 0.0)),
        "mean_aligned_mfe": float(np.mean(fav)),
        "mean_aligned_mae": float(np.mean(adv)),
    }


def episode_stats(signal: np.ndarray) -> dict[str, float | int | None]:
    runs: list[int] = []
    current = 0.0
    length = 0
    for value in signal:
        value = float(value)
        if value != 0.0 and value == current:
            length += 1
        else:
            if current != 0.0 and length:
                runs.append(length)
            current = value
            length = 1 if value != 0.0 else 0
    if current != 0.0 and length:
        runs.append(length)
    if not runs:
        return {"episode_count": 0, "median_episode_bars": None, "p90_episode_bars": None}
    arr = np.asarray(runs, dtype=float)
    return {
        "episode_count": len(runs),
        "median_episode_bars": float(np.median(arr)),
        "p90_episode_bars": float(np.quantile(arr, 0.90)),
    }


def trading_metrics(frame: pd.DataFrame, signal: np.ndarray, pip_size: float) -> dict[str, float | int | None]:
    close = pd.to_numeric(frame["close"], errors="coerce").to_numpy(float)
    returns: list[float] = []
    gross_returns: list[float] = []
    turnovers: list[float] = []
    exposures: list[float] = []
    previous = 0.0
    for i in range(len(frame) - 1):
        position = float(signal[i])
        turnover = abs(position - previous)
        gross = position * (close[i + 1] / close[i] - 1.0)
        cost = turnover * COST_PIPS * pip_size / close[i]
        gross_returns.append(gross)
        returns.append(gross - cost)
        turnovers.append(turnover)
        exposures.append(abs(position))
        previous = position
    net = np.asarray(returns, dtype=float)
    gross = np.asarray(gross_returns, dtype=float)
    if not len(net):
        raise ValueError("no trading observations")
    wealth = float(np.prod(1.0 + net))
    gross_wealth = float(np.prod(1.0 + gross))
    ann = wealth ** (ANNUALIZATION / len(net)) - 1.0 if wealth > 0 else None
    gross_ann = gross_wealth ** (ANNUALIZATION / len(net)) - 1.0 if gross_wealth > 0 else None
    std = float(np.std(net, ddof=1)) if len(net) > 1 else 0.0
    sharpe = float(np.mean(net) / std * np.sqrt(ANNUALIZATION)) if std > 0 else None
    return {
        "observations": len(net),
        "net_annualized_return": ann,
        "gross_annualized_return": gross_ann,
        "annualized_sharpe_zero_cash": sharpe,
        "average_absolute_exposure": float(np.mean(exposures)),
        "total_turnover": float(np.sum(turnovers)),
    }


def half_stability(frame: pd.DataFrame, signal: np.ndarray, horizon: int) -> dict[str, object]:
    n = len(frame)
    midpoint = n // 2
    rows = []
    positive = 0
    comparable = 0
    for name, start, end in (("first_half", 0, midpoint - 1), ("second_half", midpoint, n - 1)):
        if end - start + 1 <= horizon:
            continue
        sub_frame = frame.iloc[start : end + 1].reset_index(drop=True)
        sub_signal = signal[start : end + 1]
        result = future_aligned_metrics(sub_frame, sub_signal, horizon)
        mean = result["mean_aligned_return"]
        if mean is not None:
            comparable += 1
            positive += int(float(mean) > 0.0)
        rows.append({"half": name, **result})
    return {"positive_halves": positive, "comparable_halves": comparable, "rows": rows}


def analyze_pair(pair: str, frame: pd.DataFrame) -> dict[str, object]:
    model = compute_v06(frame)
    signals = {
        "top2_consensus_90": top2_consensus_signal(model, PRIMARY_THRESHOLD),
        "top1_family": top1_signal(model),
        "formal_family": formal_family_signal(model),
        "formal_trend_only": formal_trend_only_signal(model),
    }
    result: dict[str, object] = {
        "rows": len(frame),
        "start_date": str(frame["date"].iloc[0]),
        "end_date": str(frame["date"].iloc[-1]),
        "signals": {},
        "threshold_sensitivity": {},
    }
    for name, signal in signals.items():
        signal_result = {
            "nonzero_bar_share": float(np.mean(signal != 0.0)),
            "episodes": episode_stats(signal),
            "horizons": {},
            "trading": trading_metrics(frame, signal, PIP_SIZE[pair]),
        }
        for horizon in HORIZONS:
            signal_result["horizons"][str(horizon)] = {
                **future_aligned_metrics(frame, signal, horizon),
                "half_stability": half_stability(frame, signal, horizon),
            }
        result["signals"][name] = signal_result

    for threshold in SENSITIVITY_THRESHOLDS:
        signal = top2_consensus_signal(model, threshold)
        result["threshold_sensitivity"][str(int(threshold))] = {
            "nonzero_bar_share": float(np.mean(signal != 0.0)),
            "horizons": {
                str(h): future_aligned_metrics(frame, signal, h) for h in HORIZONS
            },
            "trading": trading_metrics(frame, signal, PIP_SIZE[pair]),
        }
    return result


def aggregate(pair_results: dict[str, dict[str, object]]) -> dict[str, object]:
    signals = ("top2_consensus_90", "top1_family", "formal_family", "formal_trend_only")
    aggregate_signals: dict[str, object] = {}
    for signal_name in signals:
        horizon_rows: dict[str, object] = {}
        for horizon in HORIZONS:
            means = []
            hit_rates = []
            coverages = []
            positive_pairs = 0
            half_positive = 0
            half_total = 0
            for pair_result in pair_results.values():
                row = pair_result["signals"][signal_name]["horizons"][str(horizon)]  # type: ignore[index]
                mean = row["mean_aligned_return"]
                hit = row["hit_rate"]
                if mean is not None:
                    means.append(float(mean))
                    positive_pairs += int(float(mean) > 0.0)
                if hit is not None:
                    hit_rates.append(float(hit))
                coverages.append(float(row["coverage"]))
                half = row["half_stability"]
                half_positive += int(half["positive_halves"])
                half_total += int(half["comparable_halves"])
            horizon_rows[str(horizon)] = {
                "median_pair_mean_aligned_return": float(np.median(means)) if means else None,
                "median_pair_hit_rate": float(np.median(hit_rates)) if hit_rates else None,
                "median_pair_coverage": float(np.median(coverages)) if coverages else None,
                "positive_pair_count": positive_pairs,
                "pair_count": len(pair_results),
                "positive_half_count": half_positive,
                "comparable_half_count": half_total,
            }
        trading_returns = []
        sharpes = []
        exposures = []
        for pair_result in pair_results.values():
            trading = pair_result["signals"][signal_name]["trading"]  # type: ignore[index]
            if trading["net_annualized_return"] is not None:
                trading_returns.append(float(trading["net_annualized_return"]))
            if trading["annualized_sharpe_zero_cash"] is not None:
                sharpes.append(float(trading["annualized_sharpe_zero_cash"]))
            exposures.append(float(trading["average_absolute_exposure"]))
        aggregate_signals[signal_name] = {
            "horizons": horizon_rows,
            "median_pair_net_annualized_return": float(np.median(trading_returns)) if trading_returns else None,
            "median_pair_sharpe": float(np.median(sharpes)) if sharpes else None,
            "median_pair_exposure": float(np.median(exposures)) if exposures else None,
        }

    threshold_rows: dict[str, object] = {}
    for threshold in SENSITIVITY_THRESHOLDS:
        by_horizon: dict[str, object] = {}
        for horizon in HORIZONS:
            means = []
            hit_rates = []
            coverages = []
            for pair_result in pair_results.values():
                row = pair_result["threshold_sensitivity"][str(int(threshold))]["horizons"][str(horizon)]  # type: ignore[index]
                if row["mean_aligned_return"] is not None:
                    means.append(float(row["mean_aligned_return"]))
                if row["hit_rate"] is not None:
                    hit_rates.append(float(row["hit_rate"]))
                coverages.append(float(row["coverage"]))
            by_horizon[str(horizon)] = {
                "median_pair_mean_aligned_return": float(np.median(means)) if means else None,
                "median_pair_hit_rate": float(np.median(hit_rates)) if hit_rates else None,
                "median_pair_coverage": float(np.median(coverages)) if coverages else None,
            }
        threshold_rows[str(int(threshold))] = {"horizons": by_horizon}

    return {"signals": aggregate_signals, "threshold_sensitivity": threshold_rows}


def build_report() -> dict[str, object]:
    pairs = {pair: analyze_pair(pair, frame) for pair, frame in load_burned_pairs().items()}
    return {
        "schema_version": 1,
        "issue": 57,
        "status": "BURNED_DATA_HYPOTHESIS_DIAGNOSTIC_ONLY",
        "primary_hypothesis": {
            "signal": "top two six-stage weights are in same directional family and sum >= 90%",
            "bullish_family": [1, 2, 3],
            "bearish_family": [4, 5, 6],
            "primary_threshold": PRIMARY_THRESHOLD,
            "sensitivity_only_thresholds": list(SENSITIVITY_THRESHOLDS),
        },
        "burned_pairs": sorted(pairs),
        "horizons": list(HORIZONS),
        "cost_pips_per_unit_turnover": COST_PIPS,
        "pairs": pairs,
        "aggregate": aggregate(pairs),
        "boundary": (
            "All seven pairs are already-observed research data. Results may motivate a new frozen signal definition "
            "and a new untouched sample, but cannot validate Top-2 directional consensus independently."
        ),
    }


def pct(value: float | None) -> str:
    return "—" if value is None else f"{value * 100:.2f}%"


def render_markdown(report: dict[str, object]) -> str:
    aggregate_data = report["aggregate"]["signals"]  # type: ignore[index]
    lines = [
        "# Issue #57 — Top-2 directional consensus burned-data diagnostic",
        "",
        "**Hypothesis-development only. All seven FX pairs in this report are already burned / observed.**",
        "",
        "Primary rule: Top1 and Top2 six-stage weights must be in the same directional family and sum to at least **90%**.",
        "",
        "## Aggregate comparison across seven burned FX pairs",
        "",
        "| Signal | H | Median aligned return | Median hit rate | Median coverage | Positive pairs | Positive halves |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    labels = {
        "top2_consensus_90": "Top2 same-dir >=90%",
        "top1_family": "Top1 family",
        "formal_family": "Formal family",
        "formal_trend_only": "Formal trend-only",
    }
    for signal_name in ("top2_consensus_90", "top1_family", "formal_family", "formal_trend_only"):
        row = aggregate_data[signal_name]
        for horizon in HORIZONS:
            h = row["horizons"][str(horizon)]
            lines.append(
                f"| {labels[signal_name]} | {horizon} | {pct(h['median_pair_mean_aligned_return'])} | "
                f"{pct(h['median_pair_hit_rate'])} | {pct(h['median_pair_coverage'])} | "
                f"{h['positive_pair_count']}/{h['pair_count']} | {h['positive_half_count']}/{h['comparable_half_count']} |"
            )
    lines.extend([
        "",
        "## Trading diagnostic — median across seven pairs",
        "",
        "| Signal | Net ann. return | Sharpe | Exposure |",
        "|---|---:|---:|---:|",
    ])
    for signal_name in ("top2_consensus_90", "top1_family", "formal_family", "formal_trend_only"):
        row = aggregate_data[signal_name]
        sharpe = "—" if row["median_pair_sharpe"] is None else f"{row['median_pair_sharpe']:.2f}"
        lines.append(
            f"| {labels[signal_name]} | {pct(row['median_pair_net_annualized_return'])} | {sharpe} | {pct(row['median_pair_exposure'])} |"
        )
    lines.extend([
        "",
        "## Top-2 threshold sensitivity (NOT parameter selection)",
        "",
        "| Threshold | H | Median aligned return | Median hit rate | Median coverage |",
        "|---:|---:|---:|---:|---:|",
    ])
    threshold_data = report["aggregate"]["threshold_sensitivity"]  # type: ignore[index]
    for threshold in SENSITIVITY_THRESHOLDS:
        row = threshold_data[str(int(threshold))]
        for horizon in HORIZONS:
            h = row["horizons"][str(horizon)]
            lines.append(
                f"| {int(threshold)}% | {horizon} | {pct(h['median_pair_mean_aligned_return'])} | "
                f"{pct(h['median_pair_hit_rate'])} | {pct(h['median_pair_coverage'])} |"
            )
    lines.extend([
        "",
        "Interpretation boundary: 90% is the primary user-originated hypothesis. 80/85/95 are sensitivity diagnostics only and must not replace 90% because one happens to backtest better.",
        "",
        "Any positive result here earns only a new untouched test; it is not independent validation.",
        "",
    ])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Issue #57 Top-2 directional consensus burned-data diagnostic")
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--md-output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_report()
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.md_output:
        args.md_output.parent.mkdir(parents=True, exist_ok=True)
        args.md_output.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["aggregate"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
