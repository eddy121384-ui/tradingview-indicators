#!/usr/bin/env python3
"""Issue #61 apples-to-apples buy-and-hold benchmark.

Uses the exact frozen Issue #55 FX fixtures, the same model warmup, the same
close-observed / next-bar execution convention, and the same 2bp turnover cost
metric as the stage-lifecycle evaluators. Spot only: no FX carry/swap points.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from diagnose_stage_lifecycle_break_timing import load_frozen_pairs
from evaluate_stage_lifecycle_base import strategy_metrics, stage_lifecycle_signal
from evaluate_stage_lifecycle_early_invalidation import early_breakout_invalidation_signal
from generate_v06_phase_b_core import load_phase_b_namespace


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

    base_signal, _ = stage_lifecycle_signal(
        formal,
        fresh_up,
        fresh_down,
        warmup=warmup,
        confirm_bars=confirm_bars,
    )
    early_signal, _ = early_breakout_invalidation_signal(
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

    buy_hold = np.zeros(len(frame), dtype=int)
    buy_hold[warmup:] = 1

    return {
        "rows": int(len(frame)),
        "raw_start_date": str(pd.Timestamp(frame["date"].iloc[0]).date()),
        "raw_end_date": str(pd.Timestamp(frame["date"].iloc[-1]).date()),
        "score_start_date": str(pd.Timestamp(frame["date"].iloc[warmup + 1]).date()),
        "score_end_date": str(pd.Timestamp(frame["date"].iloc[-1]).date()),
        "warmup_bars": warmup,
        "variants": {
            "buy_and_hold_spot": strategy_metrics(frame, buy_hold, warmup),
            "stage_lifecycle_base": strategy_metrics(frame, base_signal, warmup),
            "stage_lifecycle_early_invalidation": strategy_metrics(frame, early_signal, warmup),
        },
    }


def _median(values: list[float]) -> float | None:
    return None if not values else float(np.median(values))


def aggregate_pairs(pairs: dict[str, dict[str, object]]) -> dict[str, object]:
    metrics = (
        "gross_ann_return",
        "gross_sharpe",
        "gross_max_drawdown",
        "net_2bp_ann_return",
        "net_2bp_sharpe",
        "net_2bp_max_drawdown",
        "exposure_share",
        "annualized_turnover",
    )
    variants: dict[str, object] = {}
    for variant in ("buy_and_hold_spot", "stage_lifecycle_base", "stage_lifecycle_early_invalidation"):
        row: dict[str, object] = {}
        for metric in metrics:
            vals = [
                float(pair["variants"][variant][metric])  # type: ignore[index]
                for pair in pairs.values()
                if pair["variants"][variant][metric] is not None  # type: ignore[index]
            ]
            row[f"median_pair_{metric}"] = _median(vals)
        variants[variant] = row

    wins = {
        "pair_count": len(pairs),
        "early_return_better_than_buy_hold": 0,
        "early_sharpe_better_than_buy_hold": 0,
        "early_drawdown_better_than_buy_hold": 0,
        "early_net_return_better_than_buy_hold": 0,
        "early_net_sharpe_better_than_buy_hold": 0,
        "early_net_drawdown_better_than_buy_hold": 0,
    }
    for pair in pairs.values():
        bh = pair["variants"]["buy_and_hold_spot"]  # type: ignore[index]
        early = pair["variants"]["stage_lifecycle_early_invalidation"]  # type: ignore[index]
        wins["early_return_better_than_buy_hold"] += int(float(early["gross_ann_return"]) > float(bh["gross_ann_return"]))
        wins["early_sharpe_better_than_buy_hold"] += int(float(early["gross_sharpe"]) > float(bh["gross_sharpe"]))
        wins["early_drawdown_better_than_buy_hold"] += int(float(early["gross_max_drawdown"]) > float(bh["gross_max_drawdown"]))
        wins["early_net_return_better_than_buy_hold"] += int(float(early["net_2bp_ann_return"]) > float(bh["net_2bp_ann_return"]))
        wins["early_net_sharpe_better_than_buy_hold"] += int(float(early["net_2bp_sharpe"]) > float(bh["net_2bp_sharpe"]))
        wins["early_net_drawdown_better_than_buy_hold"] += int(float(early["net_2bp_max_drawdown"]) > float(bh["net_2bp_max_drawdown"]))
    return {"variants": variants, "wins": wins}


def build_report() -> dict[str, object]:
    pairs = {pair: analyze_pair(frame) for pair, frame in load_frozen_pairs().items()}
    return {
        "schema_version": 1,
        "issue": 61,
        "status": "BUY_HOLD_BENCHMARK_REUSED_DATA",
        "benchmark": "long one unit of quoted FX spot from first scoreable bar onward",
        "carry": "excluded from both benchmark and lifecycle strategies",
        "execution": "same one-bar lag and 2bp turnover-cost sensitivity as lifecycle evaluators",
        "pairs": pairs,
        "aggregate": aggregate_pairs(pairs),
    }


def pct(value: float | None) -> str:
    return "—" if value is None else f"{100.0 * value:.2f}%"


def num(value: float | None) -> str:
    return "—" if value is None else f"{value:.3f}"


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Issue #61 — Buy & Hold benchmark",
        "",
        "Spot-only apples-to-apples benchmark. FX carry / swap points are excluded from both benchmark and lifecycle variants.",
        "",
        "| Pair | Score period | B&H ann ret | B&H Sharpe | B&H max DD | Early ann ret | Early Sharpe | Early max DD | Early exposure |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for pair, result in report["pairs"].items():  # type: ignore[index]
        bh = result["variants"]["buy_and_hold_spot"]
        early = result["variants"]["stage_lifecycle_early_invalidation"]
        lines.append(
            f"| {pair} | {result['score_start_date']} → {result['score_end_date']} | "
            f"{pct(bh['gross_ann_return'])} | {num(bh['gross_sharpe'])} | {pct(bh['gross_max_drawdown'])} | "
            f"{pct(early['gross_ann_return'])} | {num(early['gross_sharpe'])} | {pct(early['gross_max_drawdown'])} | {pct(early['exposure_share'])} |"
        )
    agg = report["aggregate"]  # type: ignore[index]
    lines += [
        "",
        "## Median pair",
        "",
        "| Variant | Gross ann ret | Gross Sharpe | Gross max DD | Net 2bp ann ret | Net 2bp Sharpe | Net 2bp max DD | Exposure |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for variant in ("buy_and_hold_spot", "stage_lifecycle_base", "stage_lifecycle_early_invalidation"):
        row = agg["variants"][variant]
        lines.append(
            f"| {variant} | {pct(row['median_pair_gross_ann_return'])} | {num(row['median_pair_gross_sharpe'])} | "
            f"{pct(row['median_pair_gross_max_drawdown'])} | {pct(row['median_pair_net_2bp_ann_return'])} | "
            f"{num(row['median_pair_net_2bp_sharpe'])} | {pct(row['median_pair_net_2bp_max_drawdown'])} | "
            f"{pct(row['median_pair_exposure_share'])} |"
        )
    w = agg["wins"]
    lines += [
        "",
        "## Early invalidation vs Buy & Hold",
        "",
        f"- Gross return better: **{w['early_return_better_than_buy_hold']}/{w['pair_count']}**",
        f"- Gross Sharpe better: **{w['early_sharpe_better_than_buy_hold']}/{w['pair_count']}**",
        f"- Gross max DD better: **{w['early_drawdown_better_than_buy_hold']}/{w['pair_count']}**",
        f"- Net 2bp return better: **{w['early_net_return_better_than_buy_hold']}/{w['pair_count']}**",
        f"- Net 2bp Sharpe better: **{w['early_net_sharpe_better_than_buy_hold']}/{w['pair_count']}**",
        f"- Net 2bp max DD better: **{w['early_net_drawdown_better_than_buy_hold']}/{w['pair_count']}**",
        "",
    ]
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
