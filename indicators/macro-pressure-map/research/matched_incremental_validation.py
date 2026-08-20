#!/usr/bin/env python3
"""Issue #59 matched conditional incremental test for frozen MPM V6.6.

This study does not treat 2020-2026 as an untouched holdout. The period was
already inspected during earlier Issue #59 diagnostics, so all results here are
exploratory. The purpose is narrower: test whether same-direction confirmation
from the second axis adds separation within one fixed anchor-event universe.

Reproducibility contract:
- this script writes machine-generated evidence under `research/generated/` by default;
- `research/decisions/issue-59-matched-incremental.{md,json}` are curated synthesis
  artifacts and are intentionally not script output;
- the script refuses to overwrite those curated decision paths.
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
from joint_holdout_validation import (
    BOOTSTRAP_DRAWS,
    BOOTSTRAP_SEED,
    HIGH_Q,
    HORIZON,
    LOW_Q,
    OUTCOMES,
    TEST_START,
    TRAIN_END,
    embargo_pair,
    entry_events,
    evaluation_indices,
)

MATCHED_BOOTSTRAP_SEED = BOOTSTRAP_SEED + 1
RESEARCH_DIR = Path(__file__).resolve().parent
GENERATED_DIR = RESEARCH_DIR / "generated"
DEFAULT_OUTPUT_JSON = GENERATED_DIR / "issue-59-matched-incremental.generated.json"
DEFAULT_OUTPUT_MD = GENERATED_DIR / "issue-59-matched-incremental.generated.md"
CURATED_DECISION_JSON = RESEARCH_DIR / "decisions" / "issue-59-matched-incremental.json"
CURATED_DECISION_MD = RESEARCH_DIR / "decisions" / "issue-59-matched-incremental.md"


def frozen_cuts(train_for_cuts: pd.DataFrame) -> dict[str, tuple[float, float]]:
    return {
        "axis_gpi_change20": (
            float(train_for_cuts["axis_gpi_change20"].quantile(LOW_Q)),
            float(train_for_cuts["axis_gpi_change20"].quantile(HIGH_Q)),
        ),
        "axis_ipi_change20": (
            float(train_for_cuts["axis_ipi_change20"].quantile(LOW_Q)),
            float(train_for_cuts["axis_ipi_change20"].quantile(HIGH_Q)),
        ),
    }


def anchor_event_table(
    frame: pd.DataFrame,
    period_index: pd.DatetimeIndex,
    cuts: dict[str, tuple[float, float]],
    anchor_axis: str,
) -> pd.DataFrame:
    """Build one de-overlapped anchor-event universe and tag second-axis confirmation.

    High/low entries are detected on the full chronological frame, then a shared
    horizon embargo is applied within the evaluation period. `aligned=True`
    means the *other* axis is already in the same-direction extreme bucket on
    the anchor date. No future data are used for that classification.
    """
    if anchor_axis not in {"gpi", "ipi"}:
        raise ValueError("anchor_axis must be 'gpi' or 'ipi'")

    if anchor_axis == "gpi":
        anchor_col = "axis_gpi_change20"
        other_col = "axis_ipi_change20"
    else:
        anchor_col = "axis_ipi_change20"
        other_col = "axis_gpi_change20"

    anchor_lo, anchor_hi = cuts[anchor_col]
    other_lo, other_hi = cuts[other_col]

    high_entries = entry_events(frame[anchor_col] >= anchor_hi)
    low_entries = entry_events(frame[anchor_col] <= anchor_lo)
    keep_high, keep_low = embargo_pair(high_entries, low_entries, period_index, HORIZON)

    rows: list[dict] = []
    for date in period_index:
        sign = 1 if bool(keep_high.loc[date]) else (-1 if bool(keep_low.loc[date]) else 0)
        if sign == 0:
            continue
        other_value = frame.loc[date, other_col]
        aligned = bool(other_value >= other_hi) if sign > 0 else bool(other_value <= other_lo)
        opposite = bool(other_value <= other_lo) if sign > 0 else bool(other_value >= other_hi)
        row = {
            "date": date,
            "sign": sign,
            "aligned": aligned,
            "opposite": opposite,
        }
        for outcome in OUTCOMES:
            row[outcome] = frame.loc[date, outcome_column(outcome, HORIZON)]
        rows.append(row)

    if not rows:
        return pd.DataFrame(columns=["sign", "aligned", "opposite", *OUTCOMES]).set_index(
            pd.DatetimeIndex([], name="date")
        )
    return pd.DataFrame(rows).set_index("date")


def _spread(values: pd.DataFrame, outcome: str) -> float:
    positive = values.loc[values["sign"] > 0, outcome]
    negative = values.loc[values["sign"] < 0, outcome]
    if positive.empty or negative.empty:
        return np.nan
    return float(positive.mean() - negative.mean())


def matched_lift_stats(
    events: pd.DataFrame,
    outcome: str,
    draws: int = BOOTSTRAP_DRAWS,
    seed: int = MATCHED_BOOTSTRAP_SEED,
) -> dict:
    """Estimate conditional confirmation lift inside one anchor-event universe.

    `aligned_minus_all` directly tests the claim that requiring confirmation
    from the second axis increases the high-minus-low spread relative to the
    same anchor events without that condition. Bootstrap draws resample the
    positive and negative anchor-event strata and recompute both nested
    statistics from the same draw, preserving their covariance.
    """
    usable = events.loc[events[outcome].notna(), ["sign", "aligned", outcome]].copy()
    positive = usable.loc[usable["sign"] > 0]
    negative = usable.loc[usable["sign"] < 0]
    aligned = usable.loc[usable["aligned"]]
    unaligned = usable.loc[~usable["aligned"]]

    all_spread = _spread(usable, outcome)
    aligned_spread = _spread(aligned, outcome)
    unaligned_spread = _spread(unaligned, outcome)

    result = {
        "n_positive": int(len(positive)),
        "n_negative": int(len(negative)),
        "n_aligned_positive": int(((usable["sign"] > 0) & usable["aligned"]).sum()),
        "n_aligned_negative": int(((usable["sign"] < 0) & usable["aligned"]).sum()),
        "n_unaligned_positive": int(((usable["sign"] > 0) & ~usable["aligned"]).sum()),
        "n_unaligned_negative": int(((usable["sign"] < 0) & ~usable["aligned"]).sum()),
        "anchor_all_spread": all_spread,
        "aligned_spread": aligned_spread,
        "unaligned_spread": unaligned_spread,
        "aligned_minus_all": (
            float(aligned_spread - all_spread)
            if np.isfinite(aligned_spread) and np.isfinite(all_spread)
            else np.nan
        ),
        "aligned_minus_unaligned": (
            float(aligned_spread - unaligned_spread)
            if np.isfinite(aligned_spread) and np.isfinite(unaligned_spread)
            else np.nan
        ),
        "aligned_minus_all_ci95": [np.nan, np.nan],
        "aligned_minus_unaligned_ci95": [np.nan, np.nan],
        "bootstrap_valid_draws": 0,
    }

    if len(positive) < 5 or len(negative) < 5:
        return result

    pos_values = positive[outcome].to_numpy(float)
    pos_aligned = positive["aligned"].to_numpy(bool)
    neg_values = negative[outcome].to_numpy(float)
    neg_aligned = negative["aligned"].to_numpy(bool)
    rng = np.random.default_rng(seed)
    lift_all: list[float] = []
    lift_unaligned: list[float] = []

    for _ in range(draws):
        pos_idx = rng.integers(0, len(pos_values), len(pos_values))
        neg_idx = rng.integers(0, len(neg_values), len(neg_values))
        pv = pos_values[pos_idx]
        pa = pos_aligned[pos_idx]
        nv = neg_values[neg_idx]
        na = neg_aligned[neg_idx]

        if not pa.any() or not na.any():
            continue
        draw_all = float(pv.mean() - nv.mean())
        draw_aligned = float(pv[pa].mean() - nv[na].mean())
        lift_all.append(draw_aligned - draw_all)

        if (~pa).any() and (~na).any():
            draw_unaligned = float(pv[~pa].mean() - nv[~na].mean())
            lift_unaligned.append(draw_aligned - draw_unaligned)

    if lift_all:
        result["aligned_minus_all_ci95"] = [
            float(np.quantile(lift_all, 0.025)),
            float(np.quantile(lift_all, 0.975)),
        ]
        result["bootstrap_valid_draws"] = int(len(lift_all))
    if lift_unaligned:
        result["aligned_minus_unaligned_ci95"] = [
            float(np.quantile(lift_unaligned, 0.025)),
            float(np.quantile(lift_unaligned, 0.975)),
        ]
    return result


def evaluate(frame: pd.DataFrame) -> dict:
    train_eval_index, post_index, train_for_cuts = evaluation_indices(frame)
    cuts = frozen_cuts(train_for_cuts)

    report = {
        "design": {
            "threshold_definition_start": train_for_cuts.index.min().date().isoformat(),
            "threshold_definition_end": train_for_cuts.index.max().date().isoformat(),
            "development_eval_end": train_eval_index.max().date().isoformat(),
            "post_2019_start": post_index.min().date().isoformat(),
            "post_2019_end": post_index.max().date().isoformat(),
            "post_2019_status": "exploratory_reused_era_not_untouched_holdout",
            "cuts": cuts,
            "horizon": HORIZON,
            "event_embargo_trading_rows": HORIZON,
            "test": "nested matched conditional lift within a fixed anchor-event universe",
        },
        "periods": {},
    }

    for period_name, period_index in (
        ("development", train_eval_index),
        ("post_2019_exploratory", post_index),
    ):
        period: dict = {}
        for anchor_axis in ("gpi", "ipi"):
            events = anchor_event_table(frame, period_index, cuts, anchor_axis)
            axis_report = {
                "event_count": int(len(events)),
                "aligned_event_count": int(events["aligned"].sum()) if len(events) else 0,
                "outcomes": {},
            }
            for outcome in OUTCOMES:
                axis_report["outcomes"][outcome] = matched_lift_stats(events, outcome)
            period[anchor_axis] = axis_report
        report["periods"][period_name] = period
    return report


def _fmt(value: float, digits: int = 2) -> str:
    return "n/a" if not np.isfinite(value) else f"{value:.{digits}f}"


def render_markdown(report: dict) -> str:
    d = report["design"]
    lines = [
        "# Issue #59 — Matched conditional incremental test — generated evidence",
        "",
        "Status: **EXPLORATORY MATCHED TEST COMPLETE — SCRIPT GENERATED**",
        "",
        "This file is machine-generated by `matched_incremental_validation.py`. The separately maintained `decisions/issue-59-matched-incremental.md` is the curated research synthesis and is not overwritten by this script.",
        "",
        "This study was added after review identified that comparing independently sampled joint/GPI/IPI spreads does not establish incremental information.",
        "",
        f"Thresholds are still frozen from {d['threshold_definition_start']} through {d['threshold_definition_end']}.",
        f"The post-2019 era ({d['post_2019_start']} through {d['post_2019_end']}) is explicitly **not an untouched holdout** because earlier Issue #59 work already inspected it.",
        "",
        "Method: take one de-overlapped anchor-event universe (GPI entries, then IPI entries separately). Within those exact anchor events, tag whether the second axis is already in the same-direction extreme bucket. Compare the confirmed subset spread against the spread from all anchor events, and bootstrap the **nested lift** from the same resampled events.",
        "",
        "A lift CI that crosses zero does not support the claim that the second axis adds incremental separation beyond the anchor axis in this sample.",
        "",
    ]

    for period_name in ("development", "post_2019_exploratory"):
        lines += [f"## {period_name.replace('_', ' ').title()}", ""]
        for anchor_axis in ("gpi", "ipi"):
            axis = report["periods"][period_name][anchor_axis]
            lines += [
                f"### {anchor_axis.upper()} anchor; other-axis confirmation",
                "",
                f"Anchor events: {axis['event_count']}; aligned-confirmation events: {axis['aligned_event_count']}.",
                "",
                "| Outcome | Anchor-only spread | Confirmed spread | Confirmation lift | Lift 95% CI |",
                "|---|---:|---:|---:|---:|",
            ]
            for outcome in OUTCOMES:
                stats = axis["outcomes"][outcome]
                unit = "bp" if outcome in {"us10y_tvc", "us02y_tvc"} else "%"
                ci = stats["aligned_minus_all_ci95"]
                lines.append(
                    f"| {outcome} | {_fmt(stats['anchor_all_spread'])} {unit} | "
                    f"{_fmt(stats['aligned_spread'])} {unit} | "
                    f"{_fmt(stats['aligned_minus_all'])} {unit} | "
                    f"[{_fmt(ci[0])}, {_fmt(ci[1])}] |"
                )
            lines.append("")

    lines += [
        "## Interpretation boundary",
        "",
        "- The matched test does not use different independently embargoed event samples to infer incremental lift.",
        "- The post-2019 results remain exploratory because the hypothesis was selected after that era had already been inspected.",
        "- No production V6.6 parameter is changed.",
        "- If the matched lift intervals cross zero, the correct conclusion is that synchronized GPI+IPI movement may describe a distinctive subset, but incremental predictive information from the second axis is **not demonstrated**.",
        "",
    ]
    return "\n".join(lines)


def _assert_not_curated_output(path: Path) -> None:
    resolved = path.resolve()
    if resolved in {CURATED_DECISION_JSON.resolve(), CURATED_DECISION_MD.resolve()}:
        raise ValueError(
            "matched_incremental_validation.py writes generated evidence only; "
            "do not overwrite curated decisions/issue-59-matched-incremental artifacts"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parity-log", type=Path, required=True)
    parser.add_argument("--ooc-log", type=Path, required=True)
    parser.add_argument(
        "--output-json",
        type=Path,
        default=DEFAULT_OUTPUT_JSON,
        help=f"script-generated JSON output (default: {DEFAULT_OUTPUT_JSON})",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=DEFAULT_OUTPUT_MD,
        help=f"script-generated Markdown output (default: {DEFAULT_OUTPUT_MD})",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    _assert_not_curated_output(args.output_json)
    _assert_not_curated_output(args.output_md)
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