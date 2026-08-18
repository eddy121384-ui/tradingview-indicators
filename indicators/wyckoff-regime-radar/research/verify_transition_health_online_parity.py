#!/usr/bin/env python3
"""Verify the online Transition Health implementation against frozen research semantics."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from diagnose_consensus_formation_and_formal_lag import compute_v06, load_burned_pairs
from diagnose_post_handoff_hold_persistence import build_rows
from transition_health_online import (
    CHECKPOINT,
    MAX_WATCH_BARS,
    STATE_DAMAGED,
    STATE_HEALTHY,
    compute_transition_health,
)

HERE = Path(__file__).resolve().parent
INDEPENDENT_MANIFEST = HERE / "data" / "issue-57-transition-health-independent-oos-manifest.json"


def load_independent_pairs() -> dict[str, pd.DataFrame]:
    manifest = json.loads(INDEPENDENT_MANIFEST.read_text(encoding="utf-8"))
    pairs: dict[str, pd.DataFrame] = {}
    for pair, meta in manifest["pairs"].items():
        path = INDEPENDENT_MANIFEST.parent / meta["frozen_file"]
        frame = pd.read_csv(path)
        frame["date"] = pd.to_datetime(frame["date"], errors="raise").dt.date
        pairs[pair] = frame.reset_index(drop=True)
    return pairs


def expected_health_labels(model: pd.DataFrame) -> dict[int, int]:
    _, checkpoints = build_rows(model)
    expected: dict[int, int] = {}
    for item in checkpoints:
        if int(item["checkpoint"]) != CHECKPOINT:
            continue
        bar = int(item["onset"]) + CHECKPOINT
        expected[bar] = STATE_HEALTHY if bool(item["lead_held_through_checkpoint"]) else STATE_DAMAGED
    return expected


def actual_health_labels(model: pd.DataFrame) -> tuple[dict[int, int], pd.DataFrame, int]:
    """Historical-comparable online labels plus count of legitimate live-tail labels.

    The retrospective research extractor intentionally excluded bridge onsets
    without a full 20-bar future observation window. A live TradingView state
    machine cannot and should not suppress such current-tail events. Therefore
    those labels are counted but excluded only from the parity comparison.
    """
    online = compute_transition_health(model)
    actual: dict[int, int] = {}
    tail_labels = 0
    mask = online["transition_health_healthy_pulse"].to_numpy(bool) | online[
        "transition_health_damaged_pulse"
    ].to_numpy(bool)
    for bar_raw in np.flatnonzero(mask):
        bar = int(bar_raw)
        onset = bar - CHECKPOINT
        if onset + MAX_WATCH_BARS >= len(model):
            tail_labels += 1
            continue
        actual[bar] = int(online.iloc[bar]["transition_health_state"])
    return actual, online, tail_labels


def analyze_pair(frame: pd.DataFrame) -> dict[str, object]:
    model = compute_v06(frame.copy())
    expected = expected_health_labels(model)
    actual, online, tail_labels = actual_health_labels(model)
    if actual != expected:
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        mismatched = sorted(i for i in set(actual) & set(expected) if actual[i] != expected[i])
        raise AssertionError(f"Transition Health parity mismatch: missing={missing[:10]} extra={extra[:10]} mismatch={mismatched[:10]}")

    handoffs = np.flatnonzero(online["transition_health_handoff_pulse"].to_numpy(bool)).tolist()
    healthy = np.flatnonzero(online["transition_health_healthy_pulse"].to_numpy(bool)).tolist()
    damaged = np.flatnonzero(online["transition_health_damaged_pulse"].to_numpy(bool)).tolist()

    def anchors(indices: list[int]) -> list[dict[str, object]]:
        chosen = indices[:3] + (indices[-3:] if len(indices) > 3 else [])
        deduped: list[int] = []
        for i in chosen:
            if i not in deduped:
                deduped.append(i)
        return [{"bar": int(i), "date": str(frame.iloc[i]["date"])} for i in deduped]

    return {
        "rows": len(frame),
        "start_date": str(frame.iloc[0]["date"]),
        "end_date": str(frame.iloc[-1]["date"]),
        "handoff_pulses": len(handoffs),
        "healthy_pulses": len(healthy),
        "damaged_pulses": len(damaged),
        "eligible_plus3_labels": len(expected),
        "live_tail_labels_excluded_from_research_parity": tail_labels,
        "exact_match": True,
        "healthy_anchors": anchors(healthy),
        "damaged_anchors": anchors(damaged),
    }


def build_report() -> dict[str, object]:
    suites = {
        "used_research_fx": load_burned_pairs(),
        "independent_oos_fx": load_independent_pairs(),
    }
    report_suites: dict[str, object] = {}
    total_pairs = 0
    total_labels = 0
    total_tail_labels = 0
    for suite_name, pairs in suites.items():
        pair_results = {pair: analyze_pair(frame) for pair, frame in pairs.items()}
        report_suites[suite_name] = pair_results
        total_pairs += len(pair_results)
        total_labels += sum(int(item["eligible_plus3_labels"]) for item in pair_results.values())
        total_tail_labels += sum(int(item["live_tail_labels_excluded_from_research_parity"]) for item in pair_results.values())
    return {
        "schema_version": 1,
        "issue": 57,
        "status": "PASS_EXACT_ONLINE_TO_FROZEN_RESEARCH_PARITY",
        "checkpoint": CHECKPOINT,
        "total_pairs": total_pairs,
        "total_plus3_labels": total_labels,
        "live_tail_labels_excluded_from_research_parity": total_tail_labels,
        "suites": report_suites,
        "boundary": "Engineering parity on the historical research-eligible window only. Live-tail labels are valid real-time outputs but were not part of retrospective research because their 20-bar outcome window was incomplete. No tuning is permitted.",
    }


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Issue #57 — Transition Health online-state parity",
        "",
        f"**{report['status']}**",
        "",
        f"- Frozen checkpoint: **+{report['checkpoint']} bars**.",
        f"- Pairs checked: **{report['total_pairs']}**.",
        f"- Research-eligible +3 labels checked: **{report['total_plus3_labels']}**.",
        f"- Live-tail labels intentionally outside retrospective parity window: **{report['live_tail_labels_excluded_from_research_parity']}**.",
        "- Online implementation is compared bar-for-bar with the previously frozen retrospective extractor wherever the original research had a complete 20-bar future window.",
        "",
    ]
    for suite_name, pair_results in report["suites"].items():
        lines += [f"## {suite_name}", "", "| Pair | Handoff | Healthy | Damaged | +3 labels | Tail live | Exact |", "|---|---:|---:|---:|---:|---:|---|"]
        for pair, item in pair_results.items():
            lines.append(
                f"| {pair} | {item['handoff_pulses']} | {item['healthy_pulses']} | {item['damaged_pulses']} | "
                f"{item['eligible_plus3_labels']} | {item['live_tail_labels_excluded_from_research_parity']} | {'PASS' if item['exact_match'] else 'FAIL'} |"
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
    print(json.dumps({"status": report["status"], "pairs": report["total_pairs"], "labels": report["total_plus3_labels"], "tail_live": report["live_tail_labels_excluded_from_research_parity"]}, indent=2))


if __name__ == "__main__":
    main()
