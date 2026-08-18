#!/usr/bin/env python3
"""Issue #59 joint-axis walk-forward holdout for frozen Macro Pressure Map V6.6."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from incremental_validation import (
    OOC_MARKER,
    PARITY_MARKER,
    build_research_frame,
    entry_events,
    outcome_column,
    parse_marker_file,
)

TRAIN_END = "2019-12-31"
TEST_START = "2020-01-01"
LOW_Q = 0.20
HIGH_Q = 0.80
HORIZON = 20
BOOTSTRAP_DRAWS = 5000
BOOTSTRAP_SEED = 59067

OUTCOMES = ("us10y_tvc", "us02y_tvc", "usdjpy", "eurusd", "zn1", "tlt")


def fixed_entry_masks(series: pd.Series, low_cut: float, high_cut: float) -> tuple[pd.Series, pd.Series]:
    high = entry_events(series >= high_cut)
    low = entry_events(series <= low_cut)
    return high, low


def bootstrap_contrast(
    a: np.ndarray,
    b: np.ndarray,
    draws: int = BOOTSTRAP_DRAWS,
    seed: int = BOOTSTRAP_SEED,
) -> tuple[float, float]:
    a = a[np.isfinite(a)]
    b = b[np.isfinite(b)]
    if len(a) < 5 or len(b) < 5:
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    sims = np.empty(draws, dtype=float)
    for i in range(draws):
        sims[i] = (
            rng.choice(a, size=len(a), replace=True).mean()
            - rng.choice(b, size=len(b), replace=True).mean()
        )
    return float(np.quantile(sims, 0.025)), float(np.quantile(sims, 0.975))


def contrast_stats(
    frame: pd.DataFrame,
    positive_mask: pd.Series,
    negative_mask: pd.Series,
    outcome: pd.Series,
) -> dict:
    a = outcome[positive_mask & outcome.notna()].to_numpy(float)
    b = outcome[negative_mask & outcome.notna()].to_numpy(float)
    if len(a) == 0 or len(b) == 0:
        return {
            "n_positive": int(len(a)),
            "n_negative": int(len(b)),
            "mean_positive": np.nan,
            "mean_negative": np.nan,
            "spread": np.nan,
            "ci95_low": np.nan,
            "ci95_high": np.nan,
        }
    spread = float(a.mean() - b.mean())
    ci_lo, ci_hi = bootstrap_contrast(a, b)
    return {
        "n_positive": int(len(a)),
        "n_negative": int(len(b)),
        "mean_positive": float(a.mean()),
        "mean_negative": float(b.mean()),
        "spread": spread,
        "ci95_low": ci_lo,
        "ci95_high": ci_hi,
    }


def build_patterns(frame: pd.DataFrame, cuts: dict[str, tuple[float, float]]) -> dict[str, pd.Series]:
    g_lo, g_hi = cuts["axis_gpi_change20"]
    i_lo, i_hi = cuts["axis_ipi_change20"]
    g = frame["axis_gpi_change20"]
    i = frame["axis_ipi_change20"]
    return {
        "reflation_impulse": (g >= g_hi) & (i >= i_hi),
        "goldilocks_impulse": (g >= g_hi) & (i <= i_lo),
        "stagflation_impulse": (g <= g_lo) & (i >= i_hi),
        "slowdown_disinflation_impulse": (g <= g_lo) & (i <= i_lo),
    }


def evaluate(frame: pd.DataFrame) -> dict:
    train = frame.loc[:TRAIN_END].copy()
    test = frame.loc[TEST_START:].copy()

    cuts = {
        "axis_gpi_change20": (
            float(train["axis_gpi_change20"].quantile(LOW_Q)),
            float(train["axis_gpi_change20"].quantile(HIGH_Q)),
        ),
        "axis_ipi_change20": (
            float(train["axis_ipi_change20"].quantile(LOW_Q)),
            float(train["axis_ipi_change20"].quantile(HIGH_Q)),
        ),
    }

    report = {
        "design": {
            "train_start": train.index.min().date().isoformat(),
            "train_end": train.index.max().date().isoformat(),
            "test_start": test.index.min().date().isoformat(),
            "test_end": test.index.max().date().isoformat(),
            "cuts": cuts,
            "horizon": HORIZON,
        },
        "periods": {},
    }

    for period_name, sub in (("train", train), ("holdout", test)):
        patterns = build_patterns(sub, cuts)
        reflation = entry_events(patterns["reflation_impulse"])
        slowdown = entry_events(patterns["slowdown_disinflation_impulse"])

        g_hi, g_lo = fixed_entry_masks(
            sub["axis_gpi_change20"],
            cuts["axis_gpi_change20"][0],
            cuts["axis_gpi_change20"][1],
        )
        i_hi, i_lo = fixed_entry_masks(
            sub["axis_ipi_change20"],
            cuts["axis_ipi_change20"][0],
            cuts["axis_ipi_change20"][1],
        )

        period = {
            "event_counts": {
                name: int(entry_events(mask).sum())
                for name, mask in patterns.items()
            },
            "outcomes": {},
        }

        for outcome in OUTCOMES:
            col = outcome_column(outcome, HORIZON)
            period["outcomes"][outcome] = {
                "joint_reflation_minus_slowdown": contrast_stats(
                    sub, reflation, slowdown, sub[col]
                ),
                "gpi_high_minus_low": contrast_stats(
                    sub, g_hi, g_lo, sub[col]
                ),
                "ipi_high_minus_low": contrast_stats(
                    sub, i_hi, i_lo, sub[col]
                ),
            }
        report["periods"][period_name] = period
    return report


def render_markdown(report: dict) -> str:
    d = report["design"]
    lines = [
        "# Issue #59 — Joint-axis walk-forward holdout",
        "",
        "Status: **JOINT-AXIS HOLDOUT COMPLETE**",
        "",
        f"Training: {d['train_start']} to {d['train_end']}; holdout: {d['test_start']} to {d['test_end']}.",
        "",
        f"Frozen train GPI d20 cuts: {d['cuts']['axis_gpi_change20'][0]:.2f}, {d['cuts']['axis_gpi_change20'][1]:.2f}.",
        f"Frozen train IPI d20 cuts: {d['cuts']['axis_ipi_change20'][0]:.2f}, {d['cuts']['axis_ipi_change20'][1]:.2f}.",
        "",
        "Joint contrast = first-entry Reflation impulse (GPI high + IPI high) minus first-entry Slowdown/Disinflation impulse (GPI low + IPI low).",
        "",
        "| Outcome | Train joint | Holdout joint | Holdout GPI-only | Holdout IPI-only |",
        "|---|---:|---:|---:|---:|",
    ]
    train = report["periods"]["train"]["outcomes"]
    holdout = report["periods"]["holdout"]["outcomes"]
    for outcome in OUTCOMES:
        t = train[outcome]["joint_reflation_minus_slowdown"]["spread"]
        h = holdout[outcome]["joint_reflation_minus_slowdown"]["spread"]
        g = holdout[outcome]["gpi_high_minus_low"]["spread"]
        i = holdout[outcome]["ipi_high_minus_low"]["spread"]
        unit = "bp" if outcome in {"us10y_tvc", "us02y_tvc"} else "%"
        lines.append(
            f"| {outcome} | {t:.2f} {unit} | {h:.2f} {unit} | {g:.2f} {unit} | {i:.2f} {unit} |"
        )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parity-log", type=Path, required=True)
    parser.add_argument("--ooc-log", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    parity = parse_marker_file(args.parity_log, PARITY_MARKER)
    ooc = parse_marker_file(args.ooc_log, OOC_MARKER)
    frame = build_research_frame(parity, ooc)
    report = evaluate(frame)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.output_md.write_text(render_markdown(report) + "\n", encoding="utf-8")
    print(json.dumps(report["design"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
