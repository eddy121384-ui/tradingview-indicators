#!/usr/bin/env python3
"""Issue #57 burned-data behavior map after the carried stage has seized the lead."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from diagnose_bridge_formation_outcomes import bridge_direction, extract_bridge_watches
from diagnose_consensus_formation_and_formal_lag import action_pair_direction, compute_v06, load_burned_pairs
from diagnose_handoff_weight_behavior import decompose_bridge
from diagnose_transition_formation_and_regime_decay import weight_matrix
from diagnose_v06_top2_directional_consensus import top_ids_and_values

CHECKPOINTS = (1, 3, 5)
OUTCOME_HORIZONS = (5, 10)


def median_or_none(values: list[float]) -> float | None:
    return float(np.median(values)) if values else None


def tie_rank(weights: np.ndarray, stage_id: int) -> int:
    value = float(weights[stage_id - 1])
    return 1 + int(np.sum(weights > value))


def companion_top3(weights: np.ndarray, stage_id: int) -> bool:
    value = float(weights[stage_id - 1])
    return value > 0.0 and tie_rank(weights, stage_id) <= 3


def future_resolution(actionable: np.ndarray, start: int, direction: float, horizon: int) -> str:
    end = min(len(actionable) - 1, start + horizon)
    for j in range(start + 1, end + 1):
        value = float(actionable[j])
        if value == direction:
            return "success"
        if value == -direction:
            return "failure"
    return "unresolved"


def build_checkpoint_rows(model: pd.DataFrame) -> list[dict[str, object]]:
    top1, top2, _, _ = top_ids_and_values(model)
    bridge = bridge_direction(top1, top2)
    actionable = action_pair_direction(top1, top2)
    watches = extract_bridge_watches(bridge, actionable)
    weights = weight_matrix(model)

    rows: list[dict[str, object]] = []
    for watch in watches:
        onset = int(watch["onset"])
        direction = float(watch["direction"])
        context_id, carried_id, companion_id = decompose_bridge(int(top1[onset]), int(top2[onset]), direction)
        w0 = weights[onset]
        context0 = float(w0[context_id - 1])
        carried0 = float(w0[carried_id - 1])
        companion0 = float(w0[companion_id - 1])
        if not carried0 > context0:
            continue
        onset_companion_rank = tie_rank(w0, companion_id)
        resolution_lag = int(watch["resolution_lag"])

        for checkpoint in CHECKPOINTS:
            if resolution_lag <= checkpoint:
                continue
            j = onset + checkpoint
            if j >= len(model):
                continue
            wj = weights[j]
            context = float(wj[context_id - 1])
            carried = float(wj[carried_id - 1])
            companion = float(wj[companion_id - 1])
            companion_rank = tie_rank(wj, companion_id)

            row: dict[str, object] = {
                "onset": onset,
                "checkpoint": checkpoint,
                "direction": direction,
                "context_id": context_id,
                "carried_id": carried_id,
                "companion_id": companion_id,
                "context_weight": context,
                "carried_weight": carried,
                "companion_weight": companion,
                "context_change": context - context0,
                "carried_change": carried - carried0,
                "companion_change": companion - companion0,
                "companion_minus_context": companion - context,
                "companion_minus_context_change": (companion - context) - (companion0 - context0),
                "companion_rising": companion > companion0,
                "companion_top3": companion_top3(wj, companion_id),
                "companion_overtakes_context": companion > context,
                "context_falling_companion_rising": context < context0 and companion > companion0,
                "companion_rank_improved": companion_rank < onset_companion_rank,
                "carried_still_leads_context": carried > context,
                "companion_rank": companion_rank,
                "onset_companion_rank": onset_companion_rank,
            }
            for horizon in OUTCOME_HORIZONS:
                outcome = future_resolution(actionable, j, direction, horizon)
                row[f"outcome_{horizon}"] = outcome
                row[f"success_within_{horizon}"] = outcome == "success"
            rows.append(row)
    return rows


FEATURES = (
    "companion_rising",
    "companion_top3",
    "companion_overtakes_context",
    "context_falling_companion_rising",
    "companion_rank_improved",
    "carried_still_leads_context",
)
CONTINUOUS = (
    "context_weight",
    "carried_weight",
    "companion_weight",
    "context_change",
    "carried_change",
    "companion_change",
    "companion_minus_context",
    "companion_minus_context_change",
)


def summarize_checkpoint(rows: list[dict[str, object]], checkpoint: int) -> dict[str, object]:
    subset = [r for r in rows if int(r["checkpoint"]) == checkpoint]
    out: dict[str, object] = {"rows": len(subset)}
    for horizon in OUTCOME_HORIZONS:
        out[f"success_rate_{horizon}"] = (
            float(np.mean([bool(r[f"success_within_{horizon}"]) for r in subset])) if subset else None
        )
    flags: dict[str, object] = {}
    for feature in FEATURES:
        yes = [r for r in subset if bool(r[feature])]
        no = [r for r in subset if not bool(r[feature])]
        f: dict[str, object] = {"yes_rows": len(yes), "no_rows": len(no)}
        for horizon in OUTCOME_HORIZONS:
            f[f"yes_success_rate_{horizon}"] = (
                float(np.mean([bool(r[f"success_within_{horizon}"]) for r in yes])) if yes else None
            )
            f[f"no_success_rate_{horizon}"] = (
                float(np.mean([bool(r[f"success_within_{horizon}"]) for r in no])) if no else None
            )
        flags[feature] = f
    out["flags"] = flags

    success = [r for r in subset if bool(r["success_within_10"])]
    no_success = [r for r in subset if not bool(r["success_within_10"])]
    groups: dict[str, object] = {}
    for name, group in (("success_within_10", success), ("no_success_within_10", no_success)):
        g: dict[str, object] = {"rows": len(group)}
        for metric in CONTINUOUS:
            vals = [float(r[metric]) for r in group if np.isfinite(float(r[metric]))]
            g[f"median_{metric}"] = median_or_none(vals)
        groups[name] = g
    out["groups"] = groups
    return out


def analyze_pair(frame: pd.DataFrame) -> dict[str, object]:
    model = compute_v06(frame.copy())
    rows = build_checkpoint_rows(model)
    return {
        "rows": len(frame),
        "start_date": str(frame["date"].iloc[0]),
        "end_date": str(frame["date"].iloc[-1]),
        "checkpoints": {str(cp): summarize_checkpoint(rows, cp) for cp in CHECKPOINTS},
    }


def aggregate_pairs(pairs: dict[str, dict[str, object]]) -> dict[str, object]:
    out: dict[str, object] = {"checkpoints": {}}
    for cp in CHECKPOINTS:
        key = str(cp)
        summaries = [p["checkpoints"][key] for p in pairs.values()]  # type: ignore[index]
        a: dict[str, object] = {"total_rows": int(sum(int(s["rows"]) for s in summaries))}
        for horizon in OUTCOME_HORIZONS:
            vals = [float(s[f"success_rate_{horizon}"]) for s in summaries if s.get(f"success_rate_{horizon}") is not None]
            a[f"median_pair_success_rate_{horizon}"] = median_or_none(vals)

        flags: dict[str, object] = {}
        for feature in FEATURES:
            pair_flags = [s["flags"][feature] for s in summaries]  # type: ignore[index]
            f: dict[str, object] = {
                "total_yes_rows": int(sum(int(x["yes_rows"]) for x in pair_flags)),
                "total_no_rows": int(sum(int(x["no_rows"]) for x in pair_flags)),
            }
            for horizon in OUTCOME_HORIZONS:
                yes_rates = [float(x[f"yes_success_rate_{horizon}"]) for x in pair_flags if x.get(f"yes_success_rate_{horizon}") is not None]
                no_rates = [float(x[f"no_success_rate_{horizon}"]) for x in pair_flags if x.get(f"no_success_rate_{horizon}") is not None]
                f[f"median_pair_yes_success_rate_{horizon}"] = median_or_none(yes_rates)
                f[f"median_pair_no_success_rate_{horizon}"] = median_or_none(no_rates)
            flags[feature] = f
        a["flags"] = flags

        groups: dict[str, object] = {}
        for group_name in ("success_within_10", "no_success_within_10"):
            pair_groups = [s["groups"][group_name] for s in summaries]  # type: ignore[index]
            g: dict[str, object] = {"total_rows": int(sum(int(x["rows"]) for x in pair_groups))}
            for metric in CONTINUOUS:
                vals = [float(x[f"median_{metric}"]) for x in pair_groups if x.get(f"median_{metric}") is not None]
                g[f"median_pair_median_{metric}"] = median_or_none(vals)
            groups[group_name] = g
        a["groups"] = groups
        out["checkpoints"][key] = a  # type: ignore[index]
    return out


def build_report() -> dict[str, object]:
    pairs = {pair: analyze_pair(frame) for pair, frame in load_burned_pairs().items()}
    return {
        "schema_version": 1,
        "issue": 57,
        "status": "BURNED_DATA_POST_HANDOFF_COMPANION_PROGRESSION_ONLY",
        "checkpoints": list(CHECKPOINTS),
        "outcome_horizons": list(OUTCOME_HORIZONS),
        "pairs": pairs,
        "aggregate": aggregate_pairs(pairs),
        "boundary": "Descriptive reuse of burned fixtures; no numeric cutoff or production rule is selected.",
    }


def pct(v: float | None) -> str:
    return "—" if v is None else f"{100.0 * v:.2f}%"


def num(v: float | None) -> str:
    return "—" if v is None else f"{v:.2f}"


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Issue #57 — Post-handoff companion progression map",
        "",
        "**Burned-data structural study only. Existing v0.6 is unchanged.**",
        "",
    ]
    agg = report["aggregate"]["checkpoints"]  # type: ignore[index]
    for cp in CHECKPOINTS:
        a = agg[str(cp)]
        lines += [
            f"## Checkpoint +{cp}",
            "",
            f"- Still-unresolved rows: **{a['total_rows']}**.",
            f"- Median-pair future success next 5 / 10 bars: **{pct(a['median_pair_success_rate_5'])} / {pct(a['median_pair_success_rate_10'])}**.",
            "",
            "| Mechanical feature | Yes rows | Success next 10 when yes | Success next 10 when no |",
            "|---|---:|---:|---:|",
        ]
        for feature in FEATURES:
            f = a["flags"][feature]
            lines.append(
                f"| {feature} | {f['total_yes_rows']} | {pct(f['median_pair_yes_success_rate_10'])} | {pct(f['median_pair_no_success_rate_10'])} |"
            )
        success = a["groups"]["success_within_10"]
        fail = a["groups"]["no_success_within_10"]
        lines += [
            "",
            "| Continuous metric | Later success | No success |",
            "|---|---:|---:|",
        ]
        for metric in CONTINUOUS:
            lines.append(
                f"| {metric} | {num(success[f'median_pair_median_{metric}'])} | {num(fail[f'median_pair_median_{metric}'])} |"
            )
        lines.append("")

    lines += ["## Boundary", "", str(report["boundary"]), ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--md-output", type=Path, required=True)
    args = parser.parse_args()
    report = build_report()
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.md_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.md_output.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["aggregate"], indent=2))


if __name__ == "__main__":
    main()
