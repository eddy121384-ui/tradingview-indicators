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

    The embargo is shared across positive and negative events.  An accepted event
    suppresses any later candidate of either sign until at least `horizon`
    trading rows have elapsed.  This prevents overlapping forward-return windows
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
    """Return leakage-safe train evaluation rows, holdout rows, and full train cut sample."""
    train_for_cuts = frame.loc[:TRAIN_END].copy()
    if len(train_for_cuts) <= HORIZON:
        raise ValueError("training sample is too short for the forward-horizon purge")
    train_eval_index = train_for_cuts.index[:-HORIZON]
    holdout_index = frame.loc[TEST_START:].index
    if holdout_index.empty:
        raise ValueError("holdout sample is empty")
    return train_eval_index, holdout_index, train_for_cuts


def evaluate(frame: pd.DataFrame) -> dict:
    train_eval_index, holdout_index, train_for_cuts = evaluation_indices(frame)

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
    # This avoids treating a state already active on 2019-12-31 as a fresh
    # holdout entry simply because the holdout slice starts on 2020-01-01.
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
            "train_cut_start": train_for_cuts.index.min().date().isoformat(),
            "train_cut_end": train_for_cuts.index.max().date().isoformat(),
            "train_eval_end": train_eval_index.max().date().isoformat(),
            "test_start": holdout_index.min().date().isoformat(),
            "test_end": holdout_index.max().date().isoformat(),
            "cuts": cuts,
            "horizon": HORIZON,
            "event_embargo_trading_rows": HORIZON,
            "train_tail_purged_trading_rows": HORIZON,
        },
        "periods": {},
    }

    for period_name, period_index in (("train", train_eval_index), ("holdout", holdout_index)):
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
        "# Issue #59 — Joint-axis walk-forward holdout",
        "",
        "Status: **JOINT-AXIS HOLDOUT COMPLETE — NON-OVERLAPPING EVENTS**",
        "",
        f"Threshold-definition sample: {d['train_cut_start']} to {d['train_cut_end']}.",
        f"Training outcome sample ends {d['train_eval_end']} after purging the final {d['train_tail_purged_trading_rows']} trading rows so no 20d training outcome enters the holdout.",
        f"Holdout: {d['test_start']} to {d['test_end']}.",
        "",
        f"Frozen train GPI d20 cuts: {d['cuts']['axis_gpi_change20'][0]:.2f}, {d['cuts']['axis_gpi_change20'][1]:.2f}.",
        f"Frozen train IPI d20 cuts: {d['cuts']['axis_ipi_change20'][0]:.2f}, {d['cuts']['axis_ipi_change20'][1]:.2f}.",
        "",
        f"All event contrasts use a shared {d['event_embargo_trading_rows']}-trading-row embargo across positive and negative entries, so accepted forward-20d windows do not overlap.",
        "True entry transitions are detected on the full chronological frame before train/holdout slicing.",
        "",
        "Joint contrast = non-overlapping Reflation impulse (GPI high + IPI high) minus Slowdown/Disinflation impulse (GPI low + IPI low).",
        "",
    ]

    for period_name in ("train", "holdout"):
        counts = report["periods"][period_name]["event_counts"]
        lines.append(
            f"{period_name.title()} non-overlapping joint events: "
            f"{counts['reflation_impulse']} reflation vs {counts['slowdown_disinflation_impulse']} slowdown/disinflation."
        )
    lines += [
        "",
        "| Outcome | Train joint | Train 95% CI | Holdout joint | Holdout 95% CI | Holdout GPI-only | Holdout IPI-only |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    train = report["periods"]["train"]["outcomes"]
    holdout = report["periods"]["holdout"]["outcomes"]
    for outcome in OUTCOMES:
        t = train[outcome]["joint_reflation_minus_slowdown"]
        h = holdout[outcome]["joint_reflation_minus_slowdown"]
        g = holdout[outcome]["gpi_high_minus_low"]["spread"]
        i = holdout[outcome]["ipi_high_minus_low"]["spread"]
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
        "- The training tail purge prevents any training forward outcome from using 2020 holdout prices.",
        "- Confidence intervals remain descriptive; they do not prove causal independence or correct every form of market time-series dependence.",
        "- No V6.6 weight, lookback, threshold, or production formula is changed by this repair.",
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
