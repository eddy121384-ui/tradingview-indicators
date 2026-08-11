#!/usr/bin/env python3
"""Compare the user-originated Top-2 directional-consensus hypothesis on v0.5 vs v0.6.

The user's observation was explicitly about the previous indicator version. This
comparison therefore applies the same frozen Top1+Top2 same-direction >=90%
rule to the frozen v0.5.2.1 price-only mirror and the v0.6 Phase-B core on the
same already-burned seven FX fixtures.

This is development evidence only, never independent validation.
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
    episode_stats,
    future_aligned_metrics,
    half_stability,
    load_burned_pairs,
    top2_consensus_signal,
    trading_metrics,
)
from generate_v06_phase_b_core import load_phase_b_namespace
from price_only_core import PriceOnlyConfig as V05Config
from price_only_core import compute_price_only as compute_v05


HERE = Path(__file__).resolve().parent


def compute_v06(frame):
    ns = load_phase_b_namespace()
    return ns["compute_price_only"](frame.copy(), ns["PriceOnlyConfig"]())


def analyze_engine(pair: str, frame, model) -> dict[str, object]:
    signal = top2_consensus_signal(model, PRIMARY_THRESHOLD)
    return {
        "nonzero_bar_share": float(np.mean(signal != 0.0)),
        "episodes": episode_stats(signal),
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
    v05 = compute_v05(frame.copy(), V05Config())
    v06 = compute_v06(frame)
    return {
        "rows": len(frame),
        "start_date": str(frame["date"].iloc[0]),
        "end_date": str(frame["date"].iloc[-1]),
        "v05": analyze_engine(pair, frame, v05),
        "v06": analyze_engine(pair, frame, v06),
    }


def aggregate(pair_results: dict[str, dict[str, object]], engine: str) -> dict[str, object]:
    horizons = {}
    for h in HORIZONS:
        means = []
        hits = []
        coverages = []
        positive_pairs = 0
        positive_halves = 0
        comparable_halves = 0
        for pair_result in pair_results.values():
            row = pair_result[engine]["horizons"][str(h)]  # type: ignore[index]
            if row["mean_aligned_return"] is not None:
                value = float(row["mean_aligned_return"])
                means.append(value)
                positive_pairs += int(value > 0.0)
            if row["hit_rate"] is not None:
                hits.append(float(row["hit_rate"]))
            coverages.append(float(row["coverage"]))
            half = row["half_stability"]
            positive_halves += int(half["positive_halves"])
            comparable_halves += int(half["comparable_halves"])
        horizons[str(h)] = {
            "median_pair_mean_aligned_return": float(np.median(means)) if means else None,
            "median_pair_hit_rate": float(np.median(hits)) if hits else None,
            "median_pair_coverage": float(np.median(coverages)) if coverages else None,
            "positive_pair_count": positive_pairs,
            "pair_count": len(pair_results),
            "positive_half_count": positive_halves,
            "comparable_half_count": comparable_halves,
        }
    ann = []
    sharpes = []
    exposures = []
    for pair_result in pair_results.values():
        trading = pair_result[engine]["trading"]  # type: ignore[index]
        if trading["net_annualized_return"] is not None:
            ann.append(float(trading["net_annualized_return"]))
        if trading["annualized_sharpe_zero_cash"] is not None:
            sharpes.append(float(trading["annualized_sharpe_zero_cash"]))
        exposures.append(float(trading["average_absolute_exposure"]))
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
        "status": "BURNED_DATA_V05_V06_TOP2_COMPARISON_ONLY",
        "rule": "Top1 and Top2 six-stage weights in same directional family and sum >= 90%",
        "threshold": PRIMARY_THRESHOLD,
        "engines": {
            "v05": "frozen v0.5.2.1 price-only Python mirror",
            "v06": "Issue #57 v0.6 Phase-B price-only core",
        },
        "pairs": pairs,
        "aggregate": {
            "v05": aggregate(pairs, "v05"),
            "v06": aggregate(pairs, "v06"),
        },
        "boundary": (
            "All seven FX fixtures are burned. This comparison tests whether the user's previous-version intuition "
            "is visible in the frozen price-only engines and whether v0.6 preserved or changed it."
        ),
    }


def pct(value) -> str:
    return "—" if value is None else f"{float(value) * 100:.2f}%"


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Issue #57 — Top-2 consensus: v0.5 vs v0.6 on burned data",
        "",
        "**Development diagnostic only; all seven FX fixtures are already burned.**",
        "",
        "Rule held fixed across engines: Top1 and Top2 six-stage weights must share a directional family and sum to at least **90%**.",
        "",
        "| Engine | H | Median aligned return | Median hit rate | Median coverage | Positive pairs | Positive halves |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for engine in ("v05", "v06"):
        row = report["aggregate"][engine]  # type: ignore[index]
        for h in HORIZONS:
            x = row["horizons"][str(h)]
            lines.append(
                f"| {engine} | {h} | {pct(x['median_pair_mean_aligned_return'])} | {pct(x['median_pair_hit_rate'])} | "
                f"{pct(x['median_pair_coverage'])} | {x['positive_pair_count']}/{x['pair_count']} | "
                f"{x['positive_half_count']}/{x['comparable_half_count']} |"
            )
    lines.extend([
        "",
        "## Trading diagnostic — median across seven pairs",
        "",
        "| Engine | Net ann. return | Sharpe | Exposure |",
        "|---|---:|---:|---:|",
    ])
    for engine in ("v05", "v06"):
        row = report["aggregate"][engine]  # type: ignore[index]
        sharpe = "—" if row["median_pair_sharpe"] is None else f"{row['median_pair_sharpe']:.2f}"
        lines.append(
            f"| {engine} | {pct(row['median_pair_net_annualized_return'])} | {sharpe} | {pct(row['median_pair_exposure'])} |"
        )
    lines.extend([
        "",
        "Interpretation boundary: if v0.5 materially outperforms v0.6 here, investigate whether the v0.6 redesign altered useful weight-agreement structure before abandoning the user's hypothesis. If both fail, the next question is whether the user's live observation depended on full-indicator witness layers rather than the price-only core.",
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
