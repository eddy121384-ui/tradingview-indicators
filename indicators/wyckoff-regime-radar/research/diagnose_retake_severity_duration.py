#!/usr/bin/env python3
"""Issue #57 reused-data map of old-context retake severity and persistence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from diagnose_consensus_formation_and_formal_lag import compute_v06, load_burned_pairs
from diagnose_post_handoff_hold_persistence import build_rows
from diagnose_transition_formation_and_regime_decay import weight_matrix

DURATION_BINS = ("1_bar", "2_3_bars", "4_plus_bars")
SEVERITY_BINS = ("low", "mid", "high")


def normalized_margin(context: float, carried: float) -> float:
    denom = context + carried
    if denom <= 0.0:
        return 0.0
    return float((context - carried) / denom)


def first_control_spell_metrics(
    weights: np.ndarray,
    onset: int,
    retake_lag: int,
    resolution_lag: int,
    context_id: int,
    carried_id: int,
) -> dict[str, float | int]:
    """Measure the first old-context control spell after the first retake.

    The spell begins at the first retake bar and stops before original-watch
    resolution or the first bar on which carried regains a strict lead.
    """
    margins: list[float] = []
    for lag in range(retake_lag, resolution_lag):
        j = onset + lag
        if j >= len(weights):
            break
        context = float(weights[j, context_id - 1])
        carried = float(weights[j, carried_id - 1])
        if context < carried:
            break
        margins.append(max(0.0, normalized_margin(context, carried)))
    if not margins:
        return {
            "normalized_first_retake_margin": 0.0,
            "first_control_spell_bars": 0,
            "max_normalized_retake_margin": 0.0,
            "dominance_area": 0.0,
        }
    return {
        "normalized_first_retake_margin": float(margins[0]),
        "first_control_spell_bars": int(len(margins)),
        "max_normalized_retake_margin": float(max(margins)),
        "dominance_area": float(sum(margins)),
    }


def duration_bin(bars: int) -> str:
    if bars <= 1:
        return "1_bar"
    if bars <= 3:
        return "2_3_bars"
    return "4_plus_bars"


def severity_terciles(values: pd.Series) -> pd.Series:
    """Predictor-only within-pair terciles via percentile rank; no outcomes used."""
    ranks = values.rank(method="average", pct=True)
    out = pd.Series(index=values.index, dtype="object")
    out.loc[ranks <= (1.0 / 3.0)] = "low"
    out.loc[(ranks > (1.0 / 3.0)) & (ranks <= (2.0 / 3.0))] = "mid"
    out.loc[ranks > (2.0 / 3.0)] = "high"
    return out


def safe_spearman(x: pd.Series, y: pd.Series) -> float | None:
    mask = x.notna() & y.notna()
    if int(mask.sum()) < 3:
        return None
    xv = x.loc[mask].astype(float)
    yv = y.loc[mask].astype(float)
    if xv.nunique() < 2 or yv.nunique() < 2:
        return None
    value = xv.corr(yv, method="spearman")
    return None if pd.isna(value) else float(value)


def analyze_pair(frame: pd.DataFrame) -> dict[str, object]:
    model = compute_v06(frame.copy())
    weights = weight_matrix(model)
    events, _ = build_rows(model)
    rows: list[dict[str, object]] = []
    for event in events:
        retake_lag = event.get("retake_lag")
        if retake_lag is None:
            continue
        metrics = first_control_spell_metrics(
            weights,
            int(event["onset"]),
            int(retake_lag),
            int(event["resolution_lag"]),
            int(event["context_id"]),
            int(event["carried_id"]),
        )
        row = {
            "onset": int(event["onset"]),
            "resolution": str(event["resolution"]),
            "same_direction_completion": str(event["resolution"]) == "same_direction_actionable",
            "opposite_actionable_failure": str(event["resolution"]) == "opposite_actionable",
            **metrics,
        }
        row["duration_bin"] = duration_bin(int(metrics["first_control_spell_bars"]))
        rows.append(row)

    df = pd.DataFrame(rows)
    if not df.empty:
        df["severity_bin"] = severity_terciles(df["normalized_first_retake_margin"].astype(float))

    predictors = [
        "normalized_first_retake_margin",
        "first_control_spell_bars",
        "max_normalized_retake_margin",
        "dominance_area",
    ]
    correlations: dict[str, object] = {}
    for predictor in predictors:
        correlations[predictor] = {
            "rho_same_direction_completion": safe_spearman(
                df[predictor] if not df.empty else pd.Series(dtype=float),
                df["same_direction_completion"] if not df.empty else pd.Series(dtype=float),
            ),
            "rho_opposite_actionable_failure": safe_spearman(
                df[predictor] if not df.empty else pd.Series(dtype=float),
                df["opposite_actionable_failure"] if not df.empty else pd.Series(dtype=float),
            ),
        }

    def summarize_group(sub: pd.DataFrame) -> dict[str, object]:
        if sub.empty:
            return {"events": 0, "success_rate": None, "opposite_failure_rate": None, "timeout_rate": None}
        return {
            "events": int(len(sub)),
            "success_rate": float(sub["same_direction_completion"].mean()),
            "opposite_failure_rate": float(sub["opposite_actionable_failure"].mean()),
            "timeout_rate": float((sub["resolution"] == "timeout").mean()),
        }

    by_duration = {b: summarize_group(df.loc[df["duration_bin"] == b]) if not df.empty else summarize_group(df) for b in DURATION_BINS}
    by_severity = {b: summarize_group(df.loc[df["severity_bin"] == b]) if not df.empty else summarize_group(df) for b in SEVERITY_BINS}
    matrix: dict[str, object] = {}
    for severity in SEVERITY_BINS:
        matrix[severity] = {}
        for duration in DURATION_BINS:
            sub = df.loc[(df["severity_bin"] == severity) & (df["duration_bin"] == duration)] if not df.empty else df
            matrix[severity][duration] = summarize_group(sub)  # type: ignore[index]

    return {
        "rows": len(frame),
        "start_date": str(frame["date"].iloc[0]),
        "end_date": str(frame["date"].iloc[-1]),
        "retake_events": int(len(df)),
        "correlations": correlations,
        "by_duration": by_duration,
        "by_severity": by_severity,
        "matrix": matrix,
    }


def median_or_none(values: list[float]) -> float | None:
    return float(np.median(values)) if values else None


def aggregate_pairs(pairs: dict[str, dict[str, object]]) -> dict[str, object]:
    predictors = [
        "normalized_first_retake_margin",
        "first_control_spell_bars",
        "max_normalized_retake_margin",
        "dominance_area",
    ]
    correlations: dict[str, object] = {}
    for predictor in predictors:
        same = []
        opp = []
        for pair in pairs.values():
            item = pair["correlations"][predictor]  # type: ignore[index]
            if item["rho_same_direction_completion"] is not None:
                same.append(float(item["rho_same_direction_completion"]))
            if item["rho_opposite_actionable_failure"] is not None:
                opp.append(float(item["rho_opposite_actionable_failure"]))
        correlations[predictor] = {
            "median_pair_rho_same_direction_completion": median_or_none(same),
            "median_pair_rho_opposite_actionable_failure": median_or_none(opp),
            "pairs_same_direction": len(same),
            "pairs_opposite_failure": len(opp),
        }

    def aggregate_group(section: str, label: str) -> dict[str, object]:
        success: list[float] = []
        opposite: list[float] = []
        timeout: list[float] = []
        events = 0
        pairs_with_events = 0
        for pair in pairs.values():
            item = pair[section][label]  # type: ignore[index]
            events += int(item["events"])
            if int(item["events"]) > 0:
                pairs_with_events += 1
            if item["success_rate"] is not None:
                success.append(float(item["success_rate"]))
                opposite.append(float(item["opposite_failure_rate"]))
                timeout.append(float(item["timeout_rate"]))
        return {
            "events": events,
            "pairs_with_events": pairs_with_events,
            "median_pair_success_rate": median_or_none(success),
            "median_pair_opposite_failure_rate": median_or_none(opposite),
            "median_pair_timeout_rate": median_or_none(timeout),
        }

    by_duration = {b: aggregate_group("by_duration", b) for b in DURATION_BINS}
    by_severity = {b: aggregate_group("by_severity", b) for b in SEVERITY_BINS}
    matrix: dict[str, object] = {}
    for severity in SEVERITY_BINS:
        matrix[severity] = {}
        for duration in DURATION_BINS:
            success: list[float] = []
            events = 0
            pair_count = 0
            for pair in pairs.values():
                item = pair["matrix"][severity][duration]  # type: ignore[index]
                events += int(item["events"])
                if int(item["events"]) > 0:
                    pair_count += 1
                if item["success_rate"] is not None:
                    success.append(float(item["success_rate"]))
            matrix[severity][duration] = {  # type: ignore[index]
                "events": events,
                "pairs_with_events": pair_count,
                "median_pair_success_rate": median_or_none(success),
            }

    return {
        "total_retake_events": int(sum(int(p["retake_events"]) for p in pairs.values())),
        "pairs_with_retake_events": int(sum(int(p["retake_events"]) > 0 for p in pairs.values())),
        "correlations": correlations,
        "by_duration": by_duration,
        "by_severity": by_severity,
        "matrix": matrix,
    }


def build_report() -> dict[str, object]:
    pairs = {pair: analyze_pair(frame) for pair, frame in load_burned_pairs().items()}
    return {
        "schema_version": 1,
        "issue": 57,
        "status": "BURNED_DATA_RETAKE_SEVERITY_DURATION_ONLY",
        "pairs": pairs,
        "aggregate": aggregate_pairs(pairs),
        "boundary": "Reused-data structural research only; bins were frozen before outcomes and are not production thresholds.",
    }


def pct(v: float | None) -> str:
    return "—" if v is None else f"{100.0 * v:.2f}%"


def num(v: float | None) -> str:
    return "—" if v is None else f"{v:.3f}"


def render_markdown(report: dict[str, object]) -> str:
    agg = report["aggregate"]  # type: ignore[index]
    lines = [
        "# Issue #57 — Retake severity × duration map",
        "",
        "**Reused-data structural study only. Existing v0.6 is unchanged.**",
        "",
        f"- Retake events: **{agg['total_retake_events']}** across **{agg['pairs_with_retake_events']}** FX pairs.",
        "",
        "## Continuous pair-aware associations",
        "",
        "| Predictor | Median pair rho vs same-direction completion | Median pair rho vs opposite failure |",
        "|---|---:|---:|",
    ]
    for predictor, item in agg["correlations"].items():
        lines.append(
            f"| {predictor} | {num(item['median_pair_rho_same_direction_completion'])} | "
            f"{num(item['median_pair_rho_opposite_actionable_failure'])} |"
        )

    lines += [
        "",
        "## First-control duration (fixed bins)",
        "",
        "| Duration | Events | Pair-median success | Pair-median opposite failure | Pair-median timeout |",
        "|---|---:|---:|---:|---:|",
    ]
    for label in DURATION_BINS:
        item = agg["by_duration"][label]
        lines.append(
            f"| {label} | {item['events']} | {pct(item['median_pair_success_rate'])} | "
            f"{pct(item['median_pair_opposite_failure_rate'])} | {pct(item['median_pair_timeout_rate'])} |"
        )

    lines += [
        "",
        "## First-retake severity (within-pair predictor-only terciles)",
        "",
        "| Severity | Events | Pair-median success | Pair-median opposite failure | Pair-median timeout |",
        "|---|---:|---:|---:|---:|",
    ]
    for label in SEVERITY_BINS:
        item = agg["by_severity"][label]
        lines.append(
            f"| {label} | {item['events']} | {pct(item['median_pair_success_rate'])} | "
            f"{pct(item['median_pair_opposite_failure_rate'])} | {pct(item['median_pair_timeout_rate'])} |"
        )

    lines += [
        "",
        "## Severity × duration matrix",
        "",
        "| Severity | 1 bar | 2–3 bars | 4+ bars |",
        "|---|---:|---:|---:|",
    ]
    for severity in SEVERITY_BINS:
        cells = []
        for duration in DURATION_BINS:
            item = agg["matrix"][severity][duration]
            cells.append(f"{pct(item['median_pair_success_rate'])} (n={item['events']})")
        lines.append(f"| {severity} | {' | '.join(cells)} |")

    lines += ["", "## Boundary", "", str(report["boundary"]), ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--md-output", type=Path, required=True)
    args = parser.parse_args()
    report = build_report()
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.md_output.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["aggregate"], indent=2))


if __name__ == "__main__":
    main()
