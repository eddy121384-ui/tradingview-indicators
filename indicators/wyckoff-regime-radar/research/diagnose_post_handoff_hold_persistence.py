#!/usr/bin/env python3
"""Issue #57 reused-data map of post-handoff lead persistence and old-context retakes."""
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

CHECKPOINTS = (1, 3, 5, 10)


def median_or_none(values: list[float]) -> float | None:
    return float(np.median(values)) if values else None


def holds_lead_through(
    weights: np.ndarray,
    onset: int,
    checkpoint: int,
    carried_id: int,
    context_id: int,
) -> bool:
    """True only when carried > context on every bar from onset through +checkpoint."""
    end = onset + checkpoint
    if onset < 0 or checkpoint < 0 or end >= len(weights):
        return False
    carried = weights[onset : end + 1, carried_id - 1]
    context = weights[onset : end + 1, context_id - 1]
    return bool(np.all(carried > context))


def first_retake_lag(
    weights: np.ndarray,
    onset: int,
    resolution_lag: int,
    carried_id: int,
    context_id: int,
) -> int | None:
    """First pre-resolution bar where old context regains or ties the carried stage."""
    for lag in range(1, resolution_lag):
        j = onset + lag
        if j >= len(weights):
            break
        if float(weights[j, context_id - 1]) >= float(weights[j, carried_id - 1]):
            return lag
    return None


def checkpoint_eligible(resolution_lag: int, checkpoint: int) -> bool:
    """Checkpoint is predictive only while the bridge is still unresolved."""
    return resolution_lag > checkpoint


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
        context_id, carried_id, companion_id = decompose_bridge(int(top1[onset]), int(top2[onset]), direction)
        context0 = float(weights[onset, context_id - 1])
        carried0 = float(weights[onset, carried_id - 1])
        if not carried0 > context0:
            continue

        resolution_lag = int(watch["resolution_lag"])
        retake_lag = first_retake_lag(weights, onset, resolution_lag, carried_id, context_id)
        success = str(watch["resolution"]) == "same_direction_actionable"
        event = {
            "onset": onset,
            "direction": direction,
            "context_id": context_id,
            "carried_id": carried_id,
            "companion_id": companion_id,
            "resolution": str(watch["resolution"]),
            "resolution_lag": resolution_lag,
            "success_within_20": success,
            "retake_lag": retake_lag,
            "old_context_retake": retake_lag is not None,
        }
        events.append(event)

        for checkpoint in CHECKPOINTS:
            if not checkpoint_eligible(resolution_lag, checkpoint):
                continue
            if onset + checkpoint >= len(model):
                continue
            held = holds_lead_through(weights, onset, checkpoint, carried_id, context_id)
            checkpoints.append(
                {
                    "onset": onset,
                    "checkpoint": checkpoint,
                    "direction": direction,
                    "lead_held_through_checkpoint": held,
                    "success_within_20": success,
                    "resolution": str(watch["resolution"]),
                    "resolution_lag": resolution_lag,
                    "retake_lag": retake_lag,
                }
            )
    return events, checkpoints


def rate(rows: list[dict[str, object]], key: str, value: object = True) -> float | None:
    return float(np.mean([r[key] == value for r in rows])) if rows else None


def summarize_checkpoint(rows: list[dict[str, object]], checkpoint: int) -> dict[str, object]:
    subset = [r for r in rows if int(r["checkpoint"]) == checkpoint]
    held = [r for r in subset if bool(r["lead_held_through_checkpoint"])]
    lost = [r for r in subset if not bool(r["lead_held_through_checkpoint"])]
    return {
        "eligible_rows": len(subset),
        "held_rows": len(held),
        "lost_rows": len(lost),
        "held_success_rate_20": rate(held, "success_within_20"),
        "lost_success_rate_20": rate(lost, "success_within_20"),
        "held_opposite_failure_rate": rate(held, "resolution", "opposite_actionable"),
        "lost_opposite_failure_rate": rate(lost, "resolution", "opposite_actionable"),
        "held_timeout_rate": rate(held, "resolution", "timeout"),
        "lost_timeout_rate": rate(lost, "resolution", "timeout"),
    }


def summarize_retake(events: list[dict[str, object]]) -> dict[str, object]:
    retake = [r for r in events if bool(r["old_context_retake"])]
    no_retake = [r for r in events if not bool(r["old_context_retake"])]
    lags = [float(r["retake_lag"]) for r in retake if r.get("retake_lag") is not None]
    return {
        "events": len(events),
        "retake_events": len(retake),
        "no_retake_events": len(no_retake),
        "retake_rate": float(len(retake) / len(events)) if events else None,
        "median_retake_lag": median_or_none(lags),
        "retake_success_rate_20": rate(retake, "success_within_20"),
        "no_retake_success_rate_20": rate(no_retake, "success_within_20"),
        "retake_opposite_failure_rate": rate(retake, "resolution", "opposite_actionable"),
        "no_retake_opposite_failure_rate": rate(no_retake, "resolution", "opposite_actionable"),
        "retake_timeout_rate": rate(retake, "resolution", "timeout"),
        "no_retake_timeout_rate": rate(no_retake, "resolution", "timeout"),
    }


def analyze_pair(frame: pd.DataFrame) -> dict[str, object]:
    model = compute_v06(frame.copy())
    events, checkpoint_rows = build_rows(model)
    return {
        "rows": len(frame),
        "start_date": str(frame["date"].iloc[0]),
        "end_date": str(frame["date"].iloc[-1]),
        "seizure_events": len(events),
        "checkpoints": {str(cp): summarize_checkpoint(checkpoint_rows, cp) for cp in CHECKPOINTS},
        "retake": summarize_retake(events),
    }


def aggregate_pairs(pairs: dict[str, dict[str, object]]) -> dict[str, object]:
    out: dict[str, object] = {
        "total_seizure_events": int(sum(int(p["seizure_events"]) for p in pairs.values())),
        "pairs_with_events": int(sum(int(p["seizure_events"]) > 0 for p in pairs.values())),
        "checkpoints": {},
    }
    for cp in CHECKPOINTS:
        key = str(cp)
        summaries = [p["checkpoints"][key] for p in pairs.values()]  # type: ignore[index]
        held_rates = [float(s["held_success_rate_20"]) for s in summaries if s.get("held_success_rate_20") is not None]
        lost_rates = [float(s["lost_success_rate_20"]) for s in summaries if s.get("lost_success_rate_20") is not None]
        pair_wins = 0
        comparable = 0
        for s in summaries:
            if s.get("held_success_rate_20") is None or s.get("lost_success_rate_20") is None:
                continue
            comparable += 1
            if float(s["held_success_rate_20"]) > float(s["lost_success_rate_20"]):
                pair_wins += 1
        out["checkpoints"][key] = {  # type: ignore[index]
            "eligible_rows": int(sum(int(s["eligible_rows"]) for s in summaries)),
            "held_rows": int(sum(int(s["held_rows"]) for s in summaries)),
            "lost_rows": int(sum(int(s["lost_rows"]) for s in summaries)),
            "median_pair_held_success_rate_20": median_or_none(held_rates),
            "median_pair_lost_success_rate_20": median_or_none(lost_rates),
            "pairs_where_hold_beats_lost": pair_wins,
            "comparable_pairs": comparable,
        }

    retakes = [p["retake"] for p in pairs.values()]  # type: ignore[index]
    retake_success = [float(x["retake_success_rate_20"]) for x in retakes if x.get("retake_success_rate_20") is not None]
    no_retake_success = [float(x["no_retake_success_rate_20"]) for x in retakes if x.get("no_retake_success_rate_20") is not None]
    retake_rates = [float(x["retake_rate"]) for x in retakes if x.get("retake_rate") is not None]
    retake_lags = [float(x["median_retake_lag"]) for x in retakes if x.get("median_retake_lag") is not None]
    pair_wins = 0
    comparable = 0
    for x in retakes:
        if x.get("retake_success_rate_20") is None or x.get("no_retake_success_rate_20") is None:
            continue
        comparable += 1
        if float(x["no_retake_success_rate_20"]) > float(x["retake_success_rate_20"]):
            pair_wins += 1
    out["retake"] = {
        "total_retake_events": int(sum(int(x["retake_events"]) for x in retakes)),
        "total_no_retake_events": int(sum(int(x["no_retake_events"]) for x in retakes)),
        "median_pair_retake_rate": median_or_none(retake_rates),
        "median_pair_median_retake_lag": median_or_none(retake_lags),
        "median_pair_retake_success_rate_20": median_or_none(retake_success),
        "median_pair_no_retake_success_rate_20": median_or_none(no_retake_success),
        "pairs_where_no_retake_beats_retake": pair_wins,
        "comparable_pairs": comparable,
    }
    return out


def build_report() -> dict[str, object]:
    pairs = {pair: analyze_pair(frame) for pair, frame in load_burned_pairs().items()}
    return {
        "schema_version": 1,
        "issue": 57,
        "status": "BURNED_DATA_POST_HANDOFF_HOLD_PERSISTENCE_ONLY",
        "checkpoints": list(CHECKPOINTS),
        "pairs": pairs,
        "aggregate": aggregate_pairs(pairs),
        "boundary": "Descriptive reuse of already-used fixtures; no checkpoint or production rule is selected.",
    }


def pct(v: float | None) -> str:
    return "—" if v is None else f"{100.0 * v:.2f}%"


def num(v: float | None) -> str:
    return "—" if v is None else f"{v:.2f}"


def render_markdown(report: dict[str, object]) -> str:
    agg = report["aggregate"]  # type: ignore[index]
    lines = [
        "# Issue #57 — Post-handoff hold persistence map",
        "",
        "**Reused-data structural study only. Existing v0.6 is unchanged.**",
        "",
        f"- Seizure events: **{agg['total_seizure_events']}** across **{agg['pairs_with_events']}** FX pairs.",
        "",
        "## Does holding the lead improve eventual completion?",
        "",
        "| Checkpoint | Eligible unresolved | Held continuously | Lost lead | Success <=20 if held | Success <=20 if lost | Pair wins |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for cp in CHECKPOINTS:
        a = agg["checkpoints"][str(cp)]
        lines.append(
            f"| +{cp} | {a['eligible_rows']} | {a['held_rows']} | {a['lost_rows']} | "
            f"{pct(a['median_pair_held_success_rate_20'])} | {pct(a['median_pair_lost_success_rate_20'])} | "
            f"{a['pairs_where_hold_beats_lost']}/{a['comparable_pairs']} |"
        )

    r = agg["retake"]
    lines += [
        "",
        "## What happens when the old context retakes the lead?",
        "",
        f"- Retake / no-retake events: **{r['total_retake_events']} / {r['total_no_retake_events']}**.",
        f"- Median-pair retake rate: **{pct(r['median_pair_retake_rate'])}**.",
        f"- Median-pair median first-retake lag: **{num(r['median_pair_median_retake_lag'])} bars**.",
        f"- Same-direction completion <=20 after a retake: **{pct(r['median_pair_retake_success_rate_20'])}**.",
        f"- Same-direction completion <=20 with no retake: **{pct(r['median_pair_no_retake_success_rate_20'])}**.",
        f"- No-retake beats retake on **{r['pairs_where_no_retake_beats_retake']}/{r['comparable_pairs']}** comparable FX pairs.",
        "",
        "## Per pair retake comparison",
        "",
        "| Pair | Seizures | Retake rate | Success after retake | Success no retake |",
        "|---|---:|---:|---:|---:|",
    ]
    for pair, result in report["pairs"].items():  # type: ignore[index]
        rpair = result["retake"]
        lines.append(
            f"| {pair} | {result['seizure_events']} | {pct(rpair['retake_rate'])} | "
            f"{pct(rpair['retake_success_rate_20'])} | {pct(rpair['no_retake_success_rate_20'])} |"
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
