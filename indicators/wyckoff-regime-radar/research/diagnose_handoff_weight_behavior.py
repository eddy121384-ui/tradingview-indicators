#!/usr/bin/env python3
"""Issue #57 burned-data behavior map for bridge-stage weight handoff."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from diagnose_bridge_formation_outcomes import bridge_direction, extract_bridge_watches
from diagnose_consensus_formation_and_formal_lag import action_pair_direction, compute_v06, load_burned_pairs
from diagnose_transition_formation_and_regime_decay import weight_matrix
from diagnose_v06_top2_directional_consensus import top_ids_and_values

LOOKBACK = 3
PRIMARY_HORIZON = 10


def median_or_none(values: list[float]) -> float | None:
    return float(np.median(values)) if values else None


def mean_or_none(values: list[float]) -> float | None:
    return float(np.mean(values)) if values else None


def decompose_bridge(top1: int, top2: int, direction: float) -> tuple[int, int, int]:
    ids = {int(top1), int(top2)}
    if direction > 0:
        context = 1
        targets = {2, 3}
    else:
        context = 4
        targets = {5, 6}
    carried_set = ids & targets
    if context not in ids or len(carried_set) != 1:
        raise ValueError("not a semantic bridge pair")
    carried = next(iter(carried_set))
    companion = next(iter(targets - {carried}))
    return context, carried, companion


def build_rows(frame: pd.DataFrame, model: pd.DataFrame) -> list[dict[str, object]]:
    top1, top2, _, _ = top_ids_and_values(model)
    bridge = bridge_direction(top1, top2)
    actionable = action_pair_direction(top1, top2)
    watches = extract_bridge_watches(bridge, actionable)
    w = weight_matrix(model)

    rows: list[dict[str, object]] = []
    for watch in watches:
        i = int(watch["onset"])
        d = float(watch["direction"])
        context_id, carried_id, companion_id = decompose_bridge(int(top1[i]), int(top2[i]), d)
        context = float(w[i, context_id - 1])
        carried = float(w[i, carried_id - 1])
        companion = float(w[i, companion_id - 1])
        family = carried + companion
        row = dict(watch)
        row.update(
            {
                "context_id": context_id,
                "carried_id": carried_id,
                "companion_id": companion_id,
                "context_weight": context,
                "carried_weight": carried,
                "companion_weight": companion,
                "carried_minus_context": carried - context,
                "companion_minus_context": companion - context,
                "family_minus_context": family - context,
                "carried_already_leads_context": carried > context,
            }
        )

        if i >= LOOKBACK:
            j = i - LOOKBACK
            prior_context = float(w[j, context_id - 1])
            prior_carried = float(w[j, carried_id - 1])
            prior_companion = float(w[j, companion_id - 1])
            dc = context - prior_context
            dr = carried - prior_carried
            dp = companion - prior_companion
            row.update(
                {
                    "context_change_3": dc,
                    "carried_change_3": dr,
                    "companion_change_3": dp,
                    "carried_minus_context_change_3": (carried - context) - (prior_carried - prior_context),
                    "companion_minus_context_change_3": (companion - context) - (prior_companion - prior_context),
                    "context_falling_carried_rising_3": dc < 0.0 and dr > 0.0,
                    "context_falling_companion_rising_3": dc < 0.0 and dp > 0.0,
                    "both_new_targets_rising_context_falling_3": dc < 0.0 and dr > 0.0 and dp > 0.0,
                }
            )
        else:
            row.update(
                {
                    "context_change_3": None,
                    "carried_change_3": None,
                    "companion_change_3": None,
                    "carried_minus_context_change_3": None,
                    "companion_minus_context_change_3": None,
                    "context_falling_carried_rising_3": False,
                    "context_falling_companion_rising_3": False,
                    "both_new_targets_rising_context_falling_3": False,
                }
            )
        rows.append(row)
    return rows


METRICS = (
    "context_weight",
    "carried_weight",
    "companion_weight",
    "carried_minus_context",
    "companion_minus_context",
    "family_minus_context",
    "context_change_3",
    "carried_change_3",
    "companion_change_3",
    "carried_minus_context_change_3",
    "companion_minus_context_change_3",
)
FLAGS = (
    "carried_already_leads_context",
    "context_falling_carried_rising_3",
    "context_falling_companion_rising_3",
    "both_new_targets_rising_context_falling_3",
)


def summarize_rows(rows: list[dict[str, object]]) -> dict[str, object]:
    success = [r for r in rows if bool(r["success_within_10"])]
    fail = [r for r in rows if not bool(r["success_within_10"])]
    out: dict[str, object] = {
        "events": len(rows),
        "success_within_5_rate": float(np.mean([bool(r["success_within_5"]) for r in rows])) if rows else None,
        "success_within_10_rate": float(np.mean([bool(r["success_within_10"]) for r in rows])) if rows else None,
        "success_within_20_rate": float(np.mean([bool(r["success_within_20"]) for r in rows])) if rows else None,
    }
    groups: dict[str, dict[str, object]] = {}
    for name, group in (("success_within_10", success), ("no_success_within_10", fail)):
        g: dict[str, object] = {"events": len(group)}
        for metric in METRICS:
            vals = [float(r[metric]) for r in group if r.get(metric) is not None and np.isfinite(float(r[metric]))]
            g[f"median_{metric}"] = median_or_none(vals)
        groups[name] = g
    out["groups"] = groups

    flags: dict[str, object] = {}
    for flag in FLAGS:
        yes = [r for r in rows if bool(r.get(flag, False))]
        no = [r for r in rows if not bool(r.get(flag, False))]
        flags[flag] = {
            "yes_events": len(yes),
            "yes_success_rate_10": float(np.mean([bool(r["success_within_10"]) for r in yes])) if yes else None,
            "no_events": len(no),
            "no_success_rate_10": float(np.mean([bool(r["success_within_10"]) for r in no])) if no else None,
        }
    out["flags"] = flags
    return out


def analyze_pair(frame: pd.DataFrame) -> dict[str, object]:
    model = compute_v06(frame.copy())
    rows = build_rows(frame, model)
    return {
        "rows": len(frame),
        "start_date": str(frame["date"].iloc[0]),
        "end_date": str(frame["date"].iloc[-1]),
        "summary": summarize_rows(rows),
    }


def aggregate_pairs(pairs: dict[str, dict[str, object]]) -> dict[str, object]:
    summaries = [v["summary"] for v in pairs.values()]  # type: ignore[index]
    out: dict[str, object] = {
        "total_events": int(sum(int(s["events"]) for s in summaries)),
        "pairs_with_events": int(sum(int(s["events"]) > 0 for s in summaries)),
    }
    for metric in ("success_within_5_rate", "success_within_10_rate", "success_within_20_rate"):
        vals = [float(s[metric]) for s in summaries if s.get(metric) is not None]
        out[f"median_pair_{metric}"] = median_or_none(vals)

    groups: dict[str, object] = {}
    for group_name in ("success_within_10", "no_success_within_10"):
        pair_groups = [s["groups"][group_name] for s in summaries]  # type: ignore[index]
        g: dict[str, object] = {"total_events": int(sum(int(x["events"]) for x in pair_groups))}
        for metric in METRICS:
            vals = [float(x[f"median_{metric}"]) for x in pair_groups if x.get(f"median_{metric}") is not None]
            g[f"median_pair_median_{metric}"] = median_or_none(vals)
        groups[group_name] = g
    out["groups"] = groups

    flags: dict[str, object] = {}
    for flag in FLAGS:
        pair_flags = [s["flags"][flag] for s in summaries]  # type: ignore[index]
        yes_rates = [float(x["yes_success_rate_10"]) for x in pair_flags if x.get("yes_success_rate_10") is not None]
        no_rates = [float(x["no_success_rate_10"]) for x in pair_flags if x.get("no_success_rate_10") is not None]
        flags[flag] = {
            "total_yes_events": int(sum(int(x["yes_events"]) for x in pair_flags)),
            "total_no_events": int(sum(int(x["no_events"]) for x in pair_flags)),
            "median_pair_yes_success_rate_10": median_or_none(yes_rates),
            "median_pair_no_success_rate_10": median_or_none(no_rates),
        }
    out["flags"] = flags
    return out


def build_report() -> dict[str, object]:
    pairs = {pair: analyze_pair(frame) for pair, frame in load_burned_pairs().items()}
    return {
        "schema_version": 1,
        "issue": 57,
        "status": "BURNED_DATA_HANDOFF_WEIGHT_BEHAVIOR_MAP_ONLY",
        "lookback_bars": LOOKBACK,
        "primary_outcome_horizon": PRIMARY_HORIZON,
        "pairs": pairs,
        "aggregate": aggregate_pairs(pairs),
        "boundary": "Descriptive behavior map on burned fixtures. No numeric cutoff or production rule is selected.",
    }


def pct(v: float | None) -> str:
    return "—" if v is None else f"{100*v:.2f}%"


def num(v: float | None) -> str:
    return "—" if v is None else f"{v:.2f}"


def render_markdown(report: dict[str, object]) -> str:
    agg = report["aggregate"]  # type: ignore[index]
    success = agg["groups"]["success_within_10"]
    fail = agg["groups"]["no_success_within_10"]
    lines = [
        "# Issue #57 — Bridge handoff-weight behavior map",
        "",
        "**Burned-data structural study only. Existing v0.6 is unchanged.**",
        "",
        f"- Bridge events: **{agg['total_events']}** across **{agg['pairs_with_events']}** FX pairs.",
        f"- Median-pair conversion <=5 / <=10 / <=20: **{pct(agg['median_pair_success_within_5_rate'])} / {pct(agg['median_pair_success_within_10_rate'])} / {pct(agg['median_pair_success_within_20_rate'])}**.",
        "",
        "## Successful vs unsuccessful bridge at onset",
        "",
        "| Metric | Success <=10 | No success <=10 |",
        "|---|---:|---:|",
    ]
    labels = {
        "context_weight": "Old context weight",
        "carried_weight": "New carried target weight",
        "companion_weight": "New companion weight",
        "carried_minus_context": "Carried - context margin",
        "companion_minus_context": "Companion - context margin",
        "family_minus_context": "New family - context margin",
        "context_change_3": "3-bar old context change",
        "carried_change_3": "3-bar carried change",
        "companion_change_3": "3-bar companion change",
        "carried_minus_context_change_3": "3-bar carried-context margin change",
        "companion_minus_context_change_3": "3-bar companion-context margin change",
    }
    for metric, label in labels.items():
        lines.append(f"| {label} | {num(success[f'median_pair_median_{metric}'])} | {num(fail[f'median_pair_median_{metric}'])} |")

    lines += ["", "## Mechanical handoff flags", "", "| Flag | Events yes | Success <=10 when yes | Success <=10 when no |", "|---|---:|---:|---:|"]
    for flag in FLAGS:
        x = agg["flags"][flag]
        lines.append(f"| {flag} | {x['total_yes_events']} | {pct(x['median_pair_yes_success_rate_10'])} | {pct(x['median_pair_no_success_rate_10'])} |")

    lines += ["", "## Per pair", "", "| Pair | Events | <=10 success | Carried-leads success | Carried-not-leads success |", "|---|---:|---:|---:|---:|"]
    for pair, result in report["pairs"].items():  # type: ignore[index]
        s = result["summary"]
        f = s["flags"]["carried_already_leads_context"]
        lines.append(f"| {pair} | {s['events']} | {pct(s['success_within_10_rate'])} | {pct(f['yes_success_rate_10'])} | {pct(f['no_success_rate_10'])} |")
    lines += ["", "## Boundary", "", str(report["boundary"]), ""]
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
