#!/usr/bin/env python3
"""Issue #57 reused-data map of new-stage reseizure after an old-context retake."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from diagnose_bridge_formation_outcomes import bridge_direction, extract_bridge_watches
from diagnose_consensus_formation_and_formal_lag import action_pair_direction, compute_v06, load_burned_pairs
from diagnose_handoff_weight_behavior import decompose_bridge
from diagnose_post_handoff_hold_persistence import first_retake_lag
from diagnose_transition_formation_and_regime_decay import weight_matrix
from diagnose_v06_top2_directional_consensus import top_ids_and_values

CHECKPOINTS = (1, 3, 5)


def median_or_none(values: list[float]) -> float | None:
    return float(np.median(values)) if values else None


def first_reseizure_after_retake(
    weights: np.ndarray,
    onset: int,
    retake_lag: int,
    resolution_lag: int,
    carried_id: int,
    context_id: int,
) -> int | None:
    """Return bars after retake to first carried>context, strictly before resolution."""
    for absolute_lag in range(retake_lag + 1, resolution_lag):
        j = onset + absolute_lag
        if j >= len(weights):
            break
        if float(weights[j, carried_id - 1]) > float(weights[j, context_id - 1]):
            return absolute_lag - retake_lag
    return None


def checkpoint_eligible_after_retake(resolution_lag: int, retake_lag: int, checkpoint: int) -> bool:
    """Checkpoint is predictive only if the original bridge remains unresolved beyond it."""
    return resolution_lag > retake_lag + checkpoint


def reseized_by_checkpoint(reseizure_lag: int | None, checkpoint: int) -> bool:
    return reseizure_lag is not None and reseizure_lag <= checkpoint


def rate(rows: list[dict[str, object]], key: str, value: object = True) -> float | None:
    return float(np.mean([r[key] == value for r in rows])) if rows else None


def build_rows(model: pd.DataFrame) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    top1, top2, _, _ = top_ids_and_values(model)
    bridge = bridge_direction(top1, top2)
    actionable = action_pair_direction(top1, top2)
    watches = extract_bridge_watches(bridge, actionable)
    weights = weight_matrix(model)

    events: list[dict[str, object]] = []
    checkpoints: list[dict[str, object]] = []

    for watch in watches:
        onset = int(watch["onset"])
        direction = float(watch["direction"])
        context_id, carried_id, _ = decompose_bridge(int(top1[onset]), int(top2[onset]), direction)
        if not float(weights[onset, carried_id - 1]) > float(weights[onset, context_id - 1]):
            continue

        resolution_lag = int(watch["resolution_lag"])
        retake_lag = first_retake_lag(weights, onset, resolution_lag, carried_id, context_id)
        if retake_lag is None:
            continue

        reseizure_lag = first_reseizure_after_retake(
            weights,
            onset,
            retake_lag,
            resolution_lag,
            carried_id,
            context_id,
        )
        success = str(watch["resolution"]) == "same_direction_actionable"
        event = {
            "onset": onset,
            "direction": direction,
            "resolution": str(watch["resolution"]),
            "resolution_lag": resolution_lag,
            "retake_lag": retake_lag,
            "reseizure_lag_after_retake": reseizure_lag,
            "reseizure_before_resolution": reseizure_lag is not None,
            "success_within_20": success,
        }
        events.append(event)

        for checkpoint in CHECKPOINTS:
            if not checkpoint_eligible_after_retake(resolution_lag, retake_lag, checkpoint):
                continue
            checkpoints.append(
                {
                    "onset": onset,
                    "checkpoint": checkpoint,
                    "reseized_by_checkpoint": reseized_by_checkpoint(reseizure_lag, checkpoint),
                    "success_within_20": success,
                    "resolution": str(watch["resolution"]),
                }
            )

    return events, checkpoints


def summarize_events(events: list[dict[str, object]]) -> dict[str, object]:
    yes = [r for r in events if bool(r["reseizure_before_resolution"])]
    no = [r for r in events if not bool(r["reseizure_before_resolution"])]
    lags = [float(r["reseizure_lag_after_retake"]) for r in yes if r.get("reseizure_lag_after_retake") is not None]
    return {
        "retake_events": len(events),
        "reseizure_events": len(yes),
        "no_reseizure_events": len(no),
        "reseizure_rate": float(len(yes) / len(events)) if events else None,
        "median_reseizure_lag_after_retake": median_or_none(lags),
        "reseizure_success_rate_20": rate(yes, "success_within_20"),
        "no_reseizure_success_rate_20": rate(no, "success_within_20"),
        "reseizure_opposite_failure_rate": rate(yes, "resolution", "opposite_actionable"),
        "no_reseizure_opposite_failure_rate": rate(no, "resolution", "opposite_actionable"),
        "reseizure_timeout_rate": rate(yes, "resolution", "timeout"),
        "no_reseizure_timeout_rate": rate(no, "resolution", "timeout"),
    }


def summarize_checkpoint(rows: list[dict[str, object]], checkpoint: int) -> dict[str, object]:
    subset = [r for r in rows if int(r["checkpoint"]) == checkpoint]
    yes = [r for r in subset if bool(r["reseized_by_checkpoint"])]
    no = [r for r in subset if not bool(r["reseized_by_checkpoint"])]
    return {
        "eligible_rows": len(subset),
        "reseized_rows": len(yes),
        "not_yet_reseized_rows": len(no),
        "reseized_success_rate_20": rate(yes, "success_within_20"),
        "not_yet_reseized_success_rate_20": rate(no, "success_within_20"),
        "reseized_opposite_failure_rate": rate(yes, "resolution", "opposite_actionable"),
        "not_yet_reseized_opposite_failure_rate": rate(no, "resolution", "opposite_actionable"),
        "reseized_timeout_rate": rate(yes, "resolution", "timeout"),
        "not_yet_reseized_timeout_rate": rate(no, "resolution", "timeout"),
    }


def analyze_pair(frame: pd.DataFrame) -> dict[str, object]:
    model = compute_v06(frame.copy())
    events, checkpoint_rows = build_rows(model)
    return {
        "rows": len(frame),
        "start_date": str(frame["date"].iloc[0]),
        "end_date": str(frame["date"].iloc[-1]),
        "events": summarize_events(events),
        "checkpoints": {str(cp): summarize_checkpoint(checkpoint_rows, cp) for cp in CHECKPOINTS},
    }


def aggregate_pairs(pairs: dict[str, dict[str, object]]) -> dict[str, object]:
    event_summaries = [p["events"] for p in pairs.values()]  # type: ignore[index]
    out: dict[str, object] = {
        "total_retake_events": int(sum(int(s["retake_events"]) for s in event_summaries)),
        "total_reseizure_events": int(sum(int(s["reseizure_events"]) for s in event_summaries)),
        "pairs_with_retake_events": int(sum(int(s["retake_events"]) > 0 for s in event_summaries)),
    }
    for metric in (
        "reseizure_rate",
        "median_reseizure_lag_after_retake",
        "reseizure_success_rate_20",
        "no_reseizure_success_rate_20",
        "reseizure_opposite_failure_rate",
        "no_reseizure_opposite_failure_rate",
        "reseizure_timeout_rate",
        "no_reseizure_timeout_rate",
    ):
        vals = [float(s[metric]) for s in event_summaries if s.get(metric) is not None]
        out[f"median_pair_{metric}"] = median_or_none(vals)

    wins = 0
    comparable = 0
    for s in event_summaries:
        a = s.get("reseizure_success_rate_20")
        b = s.get("no_reseizure_success_rate_20")
        if a is None or b is None:
            continue
        comparable += 1
        if float(a) > float(b):
            wins += 1
    out["pairs_where_reseizure_beats_no_reseizure"] = wins
    out["comparable_pairs_reseizure"] = comparable

    out["checkpoints"] = {}
    for cp in CHECKPOINTS:
        summaries = [p["checkpoints"][str(cp)] for p in pairs.values()]  # type: ignore[index]
        a_rates = [float(s["reseized_success_rate_20"]) for s in summaries if s.get("reseized_success_rate_20") is not None]
        b_rates = [float(s["not_yet_reseized_success_rate_20"]) for s in summaries if s.get("not_yet_reseized_success_rate_20") is not None]
        wins = 0
        comparable = 0
        for s in summaries:
            a = s.get("reseized_success_rate_20")
            b = s.get("not_yet_reseized_success_rate_20")
            if a is None or b is None:
                continue
            comparable += 1
            if float(a) > float(b):
                wins += 1
        out["checkpoints"][str(cp)] = {  # type: ignore[index]
            "eligible_rows": int(sum(int(s["eligible_rows"]) for s in summaries)),
            "reseized_rows": int(sum(int(s["reseized_rows"]) for s in summaries)),
            "not_yet_reseized_rows": int(sum(int(s["not_yet_reseized_rows"]) for s in summaries)),
            "median_pair_reseized_success_rate_20": median_or_none(a_rates),
            "median_pair_not_yet_reseized_success_rate_20": median_or_none(b_rates),
            "pairs_where_reseized_beats_not_yet": wins,
            "comparable_pairs": comparable,
        }
    return out


def build_report() -> dict[str, object]:
    pairs = {pair: analyze_pair(frame) for pair, frame in load_burned_pairs().items()}
    return {
        "schema_version": 1,
        "issue": 57,
        "status": "REUSED_DATA_POST_RETAKE_RESEIZURE_ONLY",
        "checkpoints_after_retake": list(CHECKPOINTS),
        "pairs": pairs,
        "aggregate": aggregate_pairs(pairs),
        "boundary": "Descriptive reuse of already-used fixtures; no checkpoint or production rule is selected.",
    }


def pct(v: float | None) -> str:
    return "—" if v is None else f"{100.0 * v:.2f}%"


def num(v: float | None) -> str:
    return "—" if v is None else f"{v:.2f}"


def render_markdown(report: dict[str, object]) -> str:
    a = report["aggregate"]  # type: ignore[index]
    lines = [
        "# Issue #57 — Post-retake reseizure map",
        "",
        "**Reused-data structural study only. Existing v0.6 is unchanged.**",
        "",
        f"- Old-context retake events: **{a['total_retake_events']}**.",
        f"- Pre-resolution reseizure events: **{a['total_reseizure_events']}**.",
        f"- Median-pair reseizure rate: **{pct(a['median_pair_reseizure_rate'])}**.",
        f"- Median-pair median reseizure lag after retake: **{num(a['median_pair_median_reseizure_lag_after_retake'])} bars**.",
        f"- Eventual same-direction completion <=20 with reseizure: **{pct(a['median_pair_reseizure_success_rate_20'])}**.",
        f"- Without reseizure: **{pct(a['median_pair_no_reseizure_success_rate_20'])}**.",
        f"- Reseizure beats no-reseizure on **{a['pairs_where_reseizure_beats_no_reseizure']}/{a['comparable_pairs_reseizure']}** comparable FX pairs.",
        "",
        "## Time-controlled checkpoints after the old-context retake",
        "",
        "| Checkpoint | Eligible unresolved | Reseized by then | Not yet | Success if reseized | Success if not yet | Pair wins |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for cp in CHECKPOINTS:
        c = a["checkpoints"][str(cp)]
        lines.append(
            f"| +{cp} | {c['eligible_rows']} | {c['reseized_rows']} | {c['not_yet_reseized_rows']} | "
            f"{pct(c['median_pair_reseized_success_rate_20'])} | {pct(c['median_pair_not_yet_reseized_success_rate_20'])} | "
            f"{c['pairs_where_reseized_beats_not_yet']}/{c['comparable_pairs']} |"
        )

    lines += [
        "",
        "## Per pair",
        "",
        "| Pair | Retakes | Reseizure rate | Success with reseizure | Success without |",
        "|---|---:|---:|---:|---:|",
    ]
    for pair, result in report["pairs"].items():  # type: ignore[index]
        e = result["events"]
        lines.append(
            f"| {pair} | {e['retake_events']} | {pct(e['reseizure_rate'])} | "
            f"{pct(e['reseizure_success_rate_20'])} | {pct(e['no_reseizure_success_rate_20'])} |"
        )
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
