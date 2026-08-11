#!/usr/bin/env python3
"""Action-compatible Top-2 consensus diagnostic for Issue #57.

Semantic correction comes from frozen v0.5.2.1 Pine action logic:
- bullish actionable pair: stages 2 Markup + 3 Re-accumulation;
- bearish actionable pair: stages 5 Markdown + 6 Redistribution;
- stages 1/4 are transition/context, not directional consensus.

Primary threshold remains user-originated Top1+Top2 >= 90%.
All seven FX fixtures are already burned; this is hypothesis development only.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from diagnose_v06_top2_directional_consensus import (
    HORIZONS,
    PIP_SIZE,
    PRIMARY_THRESHOLD,
    future_aligned_metrics,
    half_stability,
    load_burned_pairs,
    top_ids_and_values,
    trading_metrics,
)
from generate_v06_phase_b_core import load_phase_b_namespace
from price_only_core import PriceOnlyConfig as V05Config
from price_only_core import compute_price_only as compute_v05


BULL_PAIR = {2, 3}
BEAR_PAIR = {5, 6}


def action_pair_signal(model, threshold: float = PRIMARY_THRESHOLD) -> np.ndarray:
    top1_id, top2_id, top1_value, top2_value = top_ids_and_values(model)
    out = np.zeros(len(model), dtype=float)
    for i in range(len(model)):
        total = top1_value[i] + top2_value[i]
        if not np.isfinite(total) or total < threshold:
            continue
        pair = {int(top1_id[i]), int(top2_id[i])}
        if pair == BULL_PAIR:
            out[i] = 1.0
        elif pair == BEAR_PAIR:
            out[i] = -1.0
    return out


def compute_v06(frame):
    ns = load_phase_b_namespace()
    return ns["compute_price_only"](frame.copy(), ns["PriceOnlyConfig"]())


def analyze_engine(pair: str, frame, model) -> dict[str, object]:
    signal = action_pair_signal(model, PRIMARY_THRESHOLD)
    return {
        "nonzero_bar_share": float(np.mean(signal != 0.0)),
        "horizons": {
            str(h): {
                **future_aligned_metrics(frame, signal, h),
                "half_stability": half_stability(frame, signal, h),
            }
            for h in HORIZONS
        },
        "trading": trading_metrics(frame, signal, PIP_SIZE[pair]),
    }


def analyze_pair(pair: str, frame) -> dict[str, object]:
    return {
        "v05": analyze_engine(pair, frame, compute_v05(frame.copy(), V05Config())),
        "v06": analyze_engine(pair, frame, compute_v06(frame)),
    }


def aggregate(pair_results: dict[str, dict[str, object]], engine: str) -> dict[str, object]:
    horizons = {}
    for h in HORIZONS:
        means, hits, coverage = [], [], []
        positive_pairs = positive_halves = comparable_halves = 0
        total_origins = 0
        for pair_result in pair_results.values():
            row = pair_result[engine]["horizons"][str(h)]  # type: ignore[index]
            if row["mean_aligned_return"] is not None:
                value = float(row["mean_aligned_return"])
                means.append(value)
                positive_pairs += int(value > 0.0)
            if row["hit_rate"] is not None:
                hits.append(float(row["hit_rate"]))
            coverage.append(float(row["coverage"]))
            total_origins += int(row["signal_origins"])
            half = row["half_stability"]
            positive_halves += int(half["positive_halves"])
            comparable_halves += int(half["comparable_halves"])
        horizons[str(h)] = {
            "median_pair_mean_aligned_return": float(np.median(means)) if means else None,
            "median_pair_hit_rate": float(np.median(hits)) if hits else None,
            "median_pair_coverage": float(np.median(coverage)) if coverage else None,
            "positive_pair_count": positive_pairs,
            "pair_count": len(pair_results),
            "positive_half_count": positive_halves,
            "comparable_half_count": comparable_halves,
            "total_signal_origins": total_origins,
        }
    ann, sharpes, exposures = [], [], []
    for pair_result in pair_results.values():
        row = pair_result[engine]["trading"]  # type: ignore[index]
        if row["net_annualized_return"] is not None:
            ann.append(float(row["net_annualized_return"]))
        if row["annualized_sharpe_zero_cash"] is not None:
            sharpes.append(float(row["annualized_sharpe_zero_cash"]))
        exposures.append(float(row["average_absolute_exposure"]))
    return {
        "horizons": horizons,
        "median_pair_net_annualized_return": float(np.median(ann)) if ann else None,
        "median_pair_sharpe": float(np.median(sharpes)) if sharpes else None,
        "median_pair_exposure": float(np.median(exposures)) if exposures else None,
    }


def build_report() -> dict[str, object]:
    pairs = {pair: analyze_pair(pair, frame) for pair, frame in load_burned_pairs().items()}
    return {
        "schema_version": 1,
        "issue": 57,
        "status": "BURNED_DATA_ACTION_COMPATIBLE_TOP2_DIAGNOSTIC_ONLY",
        "primary_rule": "Top1+Top2 >=90 and IDs are exactly {2,3} bullish or {5,6} bearish",
        "semantic_source": "frozen v0.5.2.1 Pine Flat Action stage mapping",
        "pairs": pairs,
        "aggregate": {"v05": aggregate(pairs, "v05"), "v06": aggregate(pairs, "v06")},
        "boundary": "All seven FX fixtures are burned; price-only only; Volume Auto not reproduced.",
    }


def pct(value) -> str:
    return "—" if value is None else f"{float(value) * 100:.2f}%"


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Issue #57 — Action-compatible Top-2 consensus, v0.5 vs v0.6",
        "",
        "**Burned-data / price-only diagnostic only.**",
        "",
        "Frozen Pine semantic correction: bullish consensus is the pair **Markup (2) + Re-accumulation (3)**; bearish consensus is **Markdown (5) + Redistribution (6)**. Top1+Top2 must sum to at least **90%**.",
        "",
        "| Engine | H | Median aligned return | Median hit rate | Median coverage | Positive pairs | Positive halves | Signal origins |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for engine in ("v05", "v06"):
        agg = report["aggregate"][engine]  # type: ignore[index]
        for h in HORIZONS:
            row = agg["horizons"][str(h)]
            lines.append(
                f"| {engine} | {h} | {pct(row['median_pair_mean_aligned_return'])} | {pct(row['median_pair_hit_rate'])} | "
                f"{pct(row['median_pair_coverage'])} | {row['positive_pair_count']}/{row['pair_count']} | "
                f"{row['positive_half_count']}/{row['comparable_half_count']} | {row['total_signal_origins']} |"
            )
    lines.extend(["", "## Trading diagnostic — median across seven pairs", "", "| Engine | Net ann. return | Sharpe | Exposure |", "|---|---:|---:|---:|"])
    for engine in ("v05", "v06"):
        row = report["aggregate"][engine]  # type: ignore[index]
        sharpe = "—" if row["median_pair_sharpe"] is None else f"{row['median_pair_sharpe']:.2f}"
        lines.append(f"| {engine} | {pct(row['median_pair_net_annualized_return'])} | {sharpe} | {pct(row['median_pair_exposure'])} |")
    lines.extend([
        "",
        "Boundary: this fixes stage-direction semantics but still does not reproduce v0.5.2.1 default Volume Auto. A failure here does not yet falsify the user's live-dashboard observation.",
        "",
    ])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
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
