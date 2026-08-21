#!/usr/bin/env python3
"""Issue #61 Phase-E early breakout-invalidation evaluator."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from diagnose_stage_lifecycle_break_timing import load_frozen_pairs
from evaluate_stage_lifecycle_base import stage_lifecycle_signal, strategy_metrics
from evaluate_stage_lifecycle_breakout_invalidation import (
    _entry_anchor,
    _matching_fresh,
    breakout_invalidation_signal,
)
from generate_v06_phase_b_core import load_phase_b_namespace


def early_breakout_invalidation_signal(
    base_signal: np.ndarray,
    close: np.ndarray,
    formal: np.ndarray,
    fresh_up: np.ndarray,
    fresh_down: np.ndarray,
    range_high_break: np.ndarray,
    range_low_break: np.ndarray,
    warmup: int,
    confirm_bars: int,
) -> tuple[np.ndarray, dict[str, int]]:
    """Apply structural invalidation only at entry ages 1..confirm_bars."""
    arrays = (close, formal, fresh_up, fresh_down, range_high_break, range_low_break)
    n = len(base_signal)
    if not all(len(values) == n for values in arrays):
        raise ValueError("all arrays must have equal length")

    out = np.zeros(n, dtype=int)
    position = 0
    entry_level = float("nan")
    entry_age = -1
    stopped_dir = 0
    previous_base = 0

    stats = {
        "long_early_invalidation_exits": 0,
        "short_early_invalidation_exits": 0,
        "long_reentries_after_early_invalidation": 0,
        "short_reentries_after_early_invalidation": 0,
        "windows_survived": 0,
        "entry_anchor_missing": 0,
    }

    for i in range(n):
        if i < warmup:
            previous_base = int(base_signal[i])
            continue

        base_dir = int(base_signal[i])

        if base_dir != previous_base:
            stopped_dir = 0
            if base_dir == 0:
                position = 0
                entry_level = float("nan")
                entry_age = -1
            else:
                position = base_dir
                entry_level = _entry_anchor(
                    i,
                    base_dir,
                    formal,
                    fresh_up,
                    fresh_down,
                    range_high_break,
                    range_low_break,
                    confirm_bars,
                )
                entry_age = 0
                if not np.isfinite(entry_level):
                    stats["entry_anchor_missing"] += 1

        elif base_dir != 0 and stopped_dir == base_dir:
            if _matching_fresh(base_dir, i, formal, fresh_up, fresh_down):
                position = base_dir
                stopped_dir = 0
                entry_level = float(range_high_break[i] if base_dir == 1 else range_low_break[i])
                entry_age = 0
                if base_dir == 1:
                    stats["long_reentries_after_early_invalidation"] += 1
                else:
                    stats["short_reentries_after_early_invalidation"] += 1
            else:
                position = 0

        elif base_dir == 0:
            position = 0
            entry_level = float("nan")
            entry_age = -1
            stopped_dir = 0

        was_holding = i > warmup and int(out[i - 1]) == position and position != 0
        if was_holding and np.isfinite(entry_level):
            entry_age += 1
            if entry_age <= confirm_bars and np.isfinite(close[i]):
                invalidated = (
                    position == 1 and float(close[i]) <= entry_level
                ) or (
                    position == -1 and float(close[i]) >= entry_level
                )
                if invalidated:
                    stopped_dir = position
                    if position == 1:
                        stats["long_early_invalidation_exits"] += 1
                    else:
                        stats["short_early_invalidation_exits"] += 1
                    position = 0
                    entry_level = float("nan")
                    entry_age = -1
            elif entry_age > confirm_bars:
                stats["windows_survived"] += 1
                entry_level = float("nan")
                entry_age = -1

        out[i] = position
        previous_base = base_dir

    return out, stats


def analyze_pair(frame: pd.DataFrame) -> dict[str, object]:
    ns = load_phase_b_namespace()
    config_type = ns["PriceOnlyConfig"]
    compute_price_only = ns["compute_price_only"]
    config = config_type()
    model = compute_price_only(frame.copy(), config)

    formal = pd.to_numeric(model["formal_id"], errors="coerce").fillna(0).to_numpy(int)
    fresh_up = pd.to_numeric(model["range_break_up"], errors="coerce").fillna(0).to_numpy(float) > 0.5
    fresh_down = pd.to_numeric(model["range_break_dn"], errors="coerce").fillna(0).to_numpy(float) > 0.5
    range_high_break = pd.to_numeric(model["range_high_break"], errors="coerce").to_numpy(float)
    range_low_break = pd.to_numeric(model["range_low_break"], errors="coerce").to_numpy(float)
    close = pd.to_numeric(frame["close"], errors="coerce").to_numpy(float)
    warmup = int(config.rank_len - 1)
    confirm_bars = int(config.confirm_bars)

    base_signal, base_events = stage_lifecycle_signal(
        formal, fresh_up, fresh_down, warmup=warmup, confirm_bars=confirm_bars
    )
    always_signal, always_events = breakout_invalidation_signal(
        base_signal,
        close,
        formal,
        fresh_up,
        fresh_down,
        range_high_break,
        range_low_break,
        warmup,
        confirm_bars,
    )
    early_signal, early_events = early_breakout_invalidation_signal(
        base_signal,
        close,
        formal,
        fresh_up,
        fresh_down,
        range_high_break,
        range_low_break,
        warmup,
        confirm_bars,
    )

    return {
        "rows": int(len(frame)),
        "warmup_bars": warmup,
        "base_events": base_events,
        "always_stop_events": always_events,
        "early_stop_events": early_events,
        "variants": {
            "stage_lifecycle_base": strategy_metrics(frame, base_signal, warmup),
            "stage_lifecycle_breakout_invalidation": strategy_metrics(frame, always_signal, warmup),
            "stage_lifecycle_early_breakout_invalidation": strategy_metrics(frame, early_signal, warmup),
        },
    }


def _median(values: list[float]) -> float | None:
    return None if not values else float(np.median(values))


def aggregate_pairs(pairs: dict[str, dict[str, object]]) -> dict[str, object]:
    metrics = (
        "gross_ann_return",
        "gross_ann_vol",
        "gross_sharpe",
        "gross_max_drawdown",
        "net_2bp_ann_return",
        "net_2bp_sharpe",
        "net_2bp_max_drawdown",
        "annualized_turnover",
        "exposure_share",
        "median_holding_bars",
        "signal_entries",
    )
    variants: dict[str, object] = {}
    variant_names = (
        "stage_lifecycle_base",
        "stage_lifecycle_breakout_invalidation",
        "stage_lifecycle_early_breakout_invalidation",
    )
    for variant in variant_names:
        row: dict[str, object] = {}
        for metric in metrics:
            values = [
                float(pair["variants"][variant][metric])  # type: ignore[index]
                for pair in pairs.values()
                if pair["variants"][variant][metric] is not None  # type: ignore[index]
            ]
            row[f"median_pair_{metric}"] = _median(values)
        variants[variant] = row

    wins = {
        "comparable_pairs": len(pairs),
        "early_gross_return_wins_vs_base": 0,
        "early_gross_sharpe_wins_vs_base": 0,
        "early_gross_drawdown_wins_vs_base": 0,
        "early_net_return_wins_vs_base": 0,
        "early_net_sharpe_wins_vs_base": 0,
        "early_net_drawdown_wins_vs_base": 0,
    }
    for pair in pairs.values():
        base = pair["variants"]["stage_lifecycle_base"]  # type: ignore[index]
        early = pair["variants"]["stage_lifecycle_early_breakout_invalidation"]  # type: ignore[index]
        wins["early_gross_return_wins_vs_base"] += int(float(early["gross_ann_return"]) > float(base["gross_ann_return"]))
        wins["early_gross_sharpe_wins_vs_base"] += int(float(early["gross_sharpe"]) > float(base["gross_sharpe"]))
        wins["early_gross_drawdown_wins_vs_base"] += int(float(early["gross_max_drawdown"]) > float(base["gross_max_drawdown"]))
        wins["early_net_return_wins_vs_base"] += int(float(early["net_2bp_ann_return"]) > float(base["net_2bp_ann_return"]))
        wins["early_net_sharpe_wins_vs_base"] += int(float(early["net_2bp_sharpe"]) > float(base["net_2bp_sharpe"]))
        wins["early_net_drawdown_wins_vs_base"] += int(float(early["net_2bp_max_drawdown"]) > float(base["net_2bp_max_drawdown"]))

    event_keys = next(iter(pairs.values()))["early_stop_events"].keys() if pairs else []  # type: ignore[index]
    early_events = {
        key: int(sum(int(pair["early_stop_events"][key]) for pair in pairs.values()))  # type: ignore[index]
        for key in event_keys
    }
    return {
        "pair_count": len(pairs),
        "variants": variants,
        "wins": wins,
        "early_stop_events": early_events,
    }


def build_report() -> dict[str, object]:
    pairs = {pair: analyze_pair(frame) for pair, frame in load_frozen_pairs().items()}
    return {
        "schema_version": 1,
        "issue": 61,
        "status": "PHASE_E_EARLY_INVALIDATION_REUSED_DATA_DEVELOPMENT_ONLY",
        "early_window_bars": 3,
        "pairs": pairs,
        "aggregate": aggregate_pairs(pairs),
        "boundary": "Existing confirmBars=3 only; reused development evidence; no buffer/ATR/target/sizing optimization.",
    }


def pct(value: float | None) -> str:
    return "—" if value is None else f"{100.0 * value:.2f}%"


def num(value: float | None) -> str:
    return "—" if value is None else f"{value:.3f}"


def render_markdown(report: dict[str, object]) -> str:
    agg = report["aggregate"]  # type: ignore[index]
    variants = (
        "stage_lifecycle_base",
        "stage_lifecycle_breakout_invalidation",
        "stage_lifecycle_early_breakout_invalidation",
    )
    lines = [
        "# Issue #61 — Phase E early breakout invalidation",
        "",
        "**Reused-data development evidence only. Rule frozen before PnL.**",
        "",
        "- Same structural anchor as Phase D.",
        "- Stop is active only at entry ages 1–3 (`confirmBars=3`).",
        "- Surviving age 3 retires the anchor and returns control to the base lifecycle.",
        "- New fresh break is required after an early stop.",
        "",
        "## Median-pair metrics",
        "",
        "| Variant | Gross ann return | Gross Sharpe | Gross max DD | Net 2bp ann return | Net 2bp Sharpe | Net 2bp max DD | Exposure | Turnover/yr | Median hold bars | Entries |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for variant in variants:
        row = agg["variants"][variant]
        lines.append(
            f"| {variant} | {pct(row['median_pair_gross_ann_return'])} | {num(row['median_pair_gross_sharpe'])} | "
            f"{pct(row['median_pair_gross_max_drawdown'])} | {pct(row['median_pair_net_2bp_ann_return'])} | "
            f"{num(row['median_pair_net_2bp_sharpe'])} | {pct(row['median_pair_net_2bp_max_drawdown'])} | "
            f"{pct(row['median_pair_exposure_share'])} | {num(row['median_pair_annualized_turnover'])} | "
            f"{num(row['median_pair_median_holding_bars'])} | {num(row['median_pair_signal_entries'])} |"
        )

    w = agg["wins"]
    lines += [
        "",
        "## Early-only consistency vs base",
        "",
        f"- Gross return better: **{w['early_gross_return_wins_vs_base']}/{w['comparable_pairs']}**.",
        f"- Gross Sharpe better: **{w['early_gross_sharpe_wins_vs_base']}/{w['comparable_pairs']}**.",
        f"- Gross max drawdown better: **{w['early_gross_drawdown_wins_vs_base']}/{w['comparable_pairs']}**.",
        f"- Net 2bp return better: **{w['early_net_return_wins_vs_base']}/{w['comparable_pairs']}**.",
        f"- Net 2bp Sharpe better: **{w['early_net_sharpe_wins_vs_base']}/{w['comparable_pairs']}**.",
        f"- Net 2bp max drawdown better: **{w['early_net_drawdown_wins_vs_base']}/{w['comparable_pairs']}**.",
        "",
        "## Early-stop events",
        "",
    ]
    for key, value in agg["early_stop_events"].items():
        lines.append(f"- `{key}`: {value}")

    lines += [
        "",
        "## Per pair",
        "",
        "| Pair | Base return | Always-stop return | Early-stop return | Base DD | Always DD | Early DD | Base hold | Always hold | Early hold |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for pair, result in report["pairs"].items():  # type: ignore[index]
        base = result["variants"]["stage_lifecycle_base"]
        always = result["variants"]["stage_lifecycle_breakout_invalidation"]
        early = result["variants"]["stage_lifecycle_early_breakout_invalidation"]
        lines.append(
            f"| {pair} | {pct(base['gross_ann_return'])} | {pct(always['gross_ann_return'])} | {pct(early['gross_ann_return'])} | "
            f"{pct(base['gross_max_drawdown'])} | {pct(always['gross_max_drawdown'])} | {pct(early['gross_max_drawdown'])} | "
            f"{num(base['median_holding_bars'])} | {num(always['median_holding_bars'])} | {num(early['median_holding_bars'])} |"
        )

    lines += ["", "## Boundary", "", str(report["boundary"]), ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--md-output", type=Path, required=True)
    args = parser.parse_args()
    report = build_report()
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.md_output.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["aggregate"], indent=2))


if __name__ == "__main__":
    main()
