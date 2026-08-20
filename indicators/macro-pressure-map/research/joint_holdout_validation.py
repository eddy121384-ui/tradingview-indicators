#!/usr/bin/env python3
"""Issue #59 joint-axis reused-era exploratory study for frozen Macro Pressure Map V6.6.

The post-2019 period is not an untouched holdout. Earlier Issue #59 diagnostics
had already inspected 2020-2026 before the synchronized-transition hypothesis
was selected. This script therefore preserves the historical split and frozen
thresholds only as an exploratory reused-era analysis.
"""
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
    outcome_column,
    parse_marker_file,
)

TRAIN_END = "2019-12-31"
POST_2019_START = "2020-01-01"
# Backward-compatible import for matched_incremental_validation.py and old notebooks.
TEST_START = POST_2019_START
LOW_Q = 0.20
HIGH_Q = 0.80
HORIZON = 20
BOOTSTRAP_DRAWS = 5000
BOOTSTRAP_SEED = 59067

OUTCOMES = ("us10y_tvc", "us02y_tvc", "usdjpy", "eurusd", "zn1", "tlt")


def entry_events(mask: pd.Series) -> pd.Series:
    prev = mask.shift(1, fill_value=False)
    return mask & ~prev


def embargo_pair(
    positive_entries: pd.Series,
    negative_entries: pd.Series,
    period_index: pd.DatetimeIndex,
    horizon: int = HORIZON,
) -> tuple[pd.Series, pd.Series]:
    """Keep chronologically first entries with non-overlapping forward windows.

    The embargo is shared across positive and negative events. An accepted event
    suppresses any later candidate of either sign until at least `horizon`
    trading rows have elapsed. This prevents overlapping forward-return windows
    from being treated as independent bootstrap observations.
    """
    pos = positive_entries.reindex(period_index, fill_value=False)
    neg = negative_entries.reindex(period_index, fill_value=False)
    keep_pos = pd.Series(False, index=period_index)
    keep_neg = pd.Series(False, index=period_index)
    last_position: int | None = None

    for position in range(len(period_index)):
        is_pos = bool(pos.iloc[position])
        is_neg = bool(neg.iloc[position])
        if not (is_pos or is_neg):
            continue
        if last_position is not None and position - last_position < horizon:
            continue
        if is_pos:
            keep_pos.iloc[position] = True
        else:
            keep_neg.iloc[position] = True
        last_position = position
    return keep_pos, keep_neg


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


def evaluation_indices(frame: pd.DataFrame) -> tuple[pd.DatetimeIndex, pd.DatetimeIndex, pd.DataFrame]:
    """Return leakage-safe development rows, post-2019 exploratory rows, and cut sample."""
    train_for_cuts = frame.loc[:TRAIN_END].copy()
    if len(train_for_cuts) <= HORIZON:
        raise ValueError("training sample is too short for the forward-horizon purge")
    development_index = train_for_cuts.index[:-HORIZON]
    post_2019_index = frame.loc[POST_2019_START:].index
    if post_2019_index.empty:
        raise ValueError("post-2019 exploratory sample is empty")
    return development_index, post_2019_index, train_for_cuts


def evaluate(frame: pd.DataFrame) -> dict:
    development_index, post_2019_index, train_for_cuts = evaluation_indices(frame)

    cuts = {
        "axis_gpi_change20": (
            float(train_for_cuts["axis_gpi_change20"].quantile(LOW_Q)),
            float(train_for_cuts["axis_gpi_change20"].quantile(HIGH_Q)),
        ),
        "axis_ipi_change20": (
            float(train_for_cuts["axis_ipi_change20"].quantile(LOW_Q)),
            float(train_for_cuts["axis_ipi_change20"].quantile(HIGH_Q)),
        ),
    }

    # Detect true entries on the complete chronological frame before splitting.
    # This avoids manufacturing a fresh post-2019 entry when a state was already
    # active across the 2019/2020 boundary.
    full_patterns = build_patterns(frame, cuts)
    joint_reflation_entries = entry_events(full_patterns["reflation_impulse"])
    joint_slowdown_entries = entry_events(full_patterns["slowdown_disinflation_impulse"])
    g_high_entries, g_low_entries = fixed_entry_masks(
        frame["axis_gpi_change20"],
        cuts["axis_gpi_change20"][0],
        cuts["axis_gpi_change20"][1],
    )
    i_high_entries, i_low_entries = fixed_entry_masks(
        frame["axis_ipi_change20"],
        cuts["axis_ipi_change20"][0],
        cuts["axis_ipi_change20"][1],
    )

    report = {
        "design": {
            "threshold_definition_start": train_for_cuts.index.min().date().isoformat(),
            "threshold_definition_end": train_for_cuts.index.max().date().isoformat(),
            "development_eval_end": development_index.max().date().isoformat(),
            "post_2019_start": post_2019_index.min().date().isoformat(),
            "post_2019_end": post_2019_index.max().date().isoformat(),
            "post_2019_status": "exploratory_reused_era_not_untouched_holdout",
            "cuts": cuts,
            "horizon": HORIZON,
            "event_embargo_trading_rows": HORIZON,
            "development_tail_purged_trading_rows": HORIZON,
        },
        "periods": {},
    }

    for period_name, period_index in (
        ("development", development_index),
        ("post_2019_exploratory", post_2019_index),
    ):
        sub = frame.loc[period_index]
        reflation, slowdown = embargo_pair(
            joint_reflation_entries, joint_slowdown_entries, period_index, HORIZON
        )
        g_hi, g_lo = embargo_pair(g_high_entries, g_low_entries, period_index, HORIZON)
        i_hi, i_lo = embargo_pair(i_high_entries, i_low_entries, period_index, HORIZON)

        period = {
            "event_counts": {
                "reflation_impulse": int(reflation.sum()),
                "slowdown_disinflation_impulse": int(slowdown.sum()),
                "gpi_high": int(g_hi.sum()),
                "gpi_low": int(g_lo.sum()),
                "ipi_high": int(i_hi.sum()),
                "ipi_low": int(i_lo.sum()),
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


def _fmt(value: float, digits: int = 2) -> str:
    return "n/a" if not np.isfinite(value) else f"{value:.{digits}f}"


def render_markdown(report: dict) -> str:
    d = report["design"]
    lines = [
        "# Issue #59 — Joint-axis post-2019 exploratory study",
        "",
        "Status: **JOINT-AXIS EXPLORATORY STUDY COMPLETE — NON-OVERLAPPING EVENTS**",
        "",
        "Evidence boundary: the post-2019 era is reused historical evidence, not an untouched holdout, because earlier Issue #59 diagnostics had already inspected it before this joint hypothesis was selected.",
        "",
        f"Threshold-definition sample: {d['threshold_definition_start']} to {d['threshold_definition_end']}.",
        f"Development outcome sample ends {d['development_eval_end']} after purging the final {d['development_tail_purged_trading_rows']} trading rows so no 20d development outcome crosses into 2020.",
        f"Post-2019 exploratory era: {d['post_2019_start']} to {d['post_2019_end']}.",
        "",
        f"Frozen GPI d20 cuts: {d['cuts']['axis_gpi_change20'][0]:.2f}, {d['cuts']['axis_gpi_change20'][1]:.2f}.",
        f"Frozen IPI d20 cuts: {d['cuts']['axis_ipi_change20'][0]:.2f}, {d['cuts']['axis_ipi_change20'][1]:.2f}.",
        "",
        f"All event contrasts use a shared {d['event_embargo_trading_rows']}-trading-row embargo across positive and negative entries, so accepted forward-20d windows do not overlap.",
        "True entry transitions are detected on the full chronological frame before period slicing.",
        "",
        "Joint contrast = non-overlapping Reflation impulse (GPI high + IPI high) minus Slowdown/Disinflation impulse (GPI low + IPI low).",
        "",
    ]

    for period_name in ("development", "post_2019_exploratory"):
        counts = report["periods"][period_name]["event_counts"]
        label = "Development" if period_name == "development" else "Post-2019 exploratory"
        lines.append(
            f"{label} non-overlapping joint events: "
            f"{counts['reflation_impulse']} reflation vs {counts['slowdown_disinflation_impulse']} slowdown/disinflation."
        )
    lines += [
        "",
        "| Outcome | Development joint | Development 95% CI | Post-2019 exploratory joint | Exploratory 95% CI | Exploratory GPI-only | Exploratory IPI-only |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    development = report["periods"]["development"]["outcomes"]
    post_2019 = report["periods"]["post_2019_exploratory"]["outcomes"]
    for outcome in OUTCOMES:
        t = development[outcome]["joint_reflation_minus_slowdown"]
        h = post_2019[outcome]["joint_reflation_minus_slowdown"]
        g = post_2019[outcome]["gpi_high_minus_low"]["spread"]
        i = post_2019[outcome]["ipi_high_minus_low"]["spread"]
        unit = "bp" if outcome in {"us10y_tvc", "us02y_tvc"} else "%"
        lines.append(
            f"| {outcome} | {_fmt(t['spread'])} {unit} | "
            f"[{_fmt(t['ci95_low'])}, {_fmt(t['ci95_high'])}] | "
            f"{_fmt(h['spread'])} {unit} | [{_fmt(h['ci95_low'])}, {_fmt(h['ci95_high'])}] | "
            f"{_fmt(g)} {unit} | {_fmt(i)} {unit} |"
        )
    lines += [
        "",
        "## Statistical interpretation",
        "",
        "- The 20-row embargo removes overlapping forward windows before the simple event bootstrap is applied.",
        "- The development tail purge prevents any development forward outcome from using 2020 prices.",
        "- The post-2019 sample is exploratory reused-era evidence and must not be described as an untouched holdout or decision-grade validation.",
        "- Raw joint-vs-single spread differences do not establish incremental information; see `issue-59-matched-incremental.md` for the matched conditional test.",
        "- Confidence intervals remain descriptive; they do not prove causal independence or correct every form of market time-series dependence.",
        "- No V6.6 weight, lookback, threshold, or production formula is changed by this study.",
        "",
    ]
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