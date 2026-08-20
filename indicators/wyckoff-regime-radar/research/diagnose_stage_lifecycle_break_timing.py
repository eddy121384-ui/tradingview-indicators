#!/usr/bin/env python3
"""Issue #61 Phase-A timing audit for fresh structural breaks vs v0.6 Formal stages.

This diagnostic is intentionally outcome-free.  It uses the frozen Issue #57
v0.6 Phase-B core and already-burned Issue #55 static FX fixtures to answer only
when a fresh 20-bar range break happens relative to Formal Markup/Markdown.
No return, hit-rate, Sharpe, stop, sizing, or PnL statistic is computed here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from generate_v06_phase_b_core import load_phase_b_namespace

HERE = Path(__file__).resolve().parent
MANIFEST = HERE / "data" / "issue-55-static-fx-canonical-manifest.json"
HORIZON = 20
CHECKPOINTS = (0, 1, 3, 5, 20)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_frozen_pairs() -> dict[str, pd.DataFrame]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    pairs: dict[str, pd.DataFrame] = {}
    for pair, meta in manifest["pairs"].items():
        path = MANIFEST.parent / meta["frozen_file"]
        actual = sha256_file(path)
        expected = str(meta["frozen_sha256"])
        if actual != expected:
            raise RuntimeError(f"{pair}: frozen SHA mismatch: {actual} != {expected}")
        frame = pd.read_csv(path)
        frame["date"] = pd.to_datetime(frame["date"], errors="raise")
        pairs[pair] = frame.reset_index(drop=True)
    return pairs


def first_target_lag(formal: np.ndarray, start: int, target: int, horizon: int = HORIZON) -> int | None:
    end = min(len(formal) - 1, start + horizon)
    for idx in range(start, end + 1):
        if int(formal[idx]) == target:
            return idx - start
    return None


def last_event_age(events: np.ndarray, index: int, horizon: int = HORIZON) -> int | None:
    start = max(0, index - horizon)
    for idx in range(index, start - 1, -1):
        if bool(events[idx]):
            return index - idx
    return None


def lag_histogram(lags: Iterable[int | None], horizon: int = HORIZON) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for lag in lags:
        counter["none"] += int(lag is None)
        if lag is not None:
            counter[str(int(lag))] += 1
    return {str(i): int(counter[str(i)]) for i in range(horizon + 1)} | {"none": int(counter["none"])}


def checkpoint_counts(lags: list[int | None]) -> dict[str, int]:
    return {
        str(checkpoint): int(sum(lag is not None and lag <= checkpoint for lag in lags))
        for checkpoint in CHECKPOINTS
    }


def summarize_break_side(
    formal: np.ndarray,
    events: np.ndarray,
    target: int,
    warmup: int,
) -> dict[str, object]:
    event_indices = np.flatnonzero(events & (np.arange(len(events)) >= warmup))
    already_target = []
    needs_confirmation_lags: list[int | None] = []
    prev_stage_counts: Counter[str] = Counter()
    current_stage_counts: Counter[str] = Counter()

    for index in event_indices:
        previous = int(formal[index - 1]) if index > 0 else 0
        current = int(formal[index])
        prev_stage_counts[str(previous)] += 1
        current_stage_counts[str(current)] += 1
        was_already_target = previous == target
        already_target.append(was_already_target)
        if not was_already_target:
            needs_confirmation_lags.append(first_target_lag(formal, int(index), target))

    finite_lags = [lag for lag in needs_confirmation_lags if lag is not None]
    return {
        "fresh_breaks": int(len(event_indices)),
        "already_target_before_break": int(sum(already_target)),
        "not_already_target_before_break": int(len(needs_confirmation_lags)),
        "confirmation_within": checkpoint_counts(needs_confirmation_lags),
        "confirmation_lag_histogram_0_20": lag_histogram(needs_confirmation_lags),
        "matched_within_20": int(len(finite_lags)),
        "median_confirmation_lag_if_matched": None if not finite_lags else float(np.median(finite_lags)),
        "previous_formal_stage_at_break": dict(sorted(prev_stage_counts.items(), key=lambda item: int(item[0]))),
        "current_formal_stage_at_break": dict(sorted(current_stage_counts.items(), key=lambda item: int(item[0]))),
    }


def summarize_target_onsets(
    formal: np.ndarray,
    events: np.ndarray,
    target: int,
    initial_from: int,
    renewal_from: int,
    warmup: int,
) -> dict[str, object]:
    onsets = [
        index
        for index in range(max(1, warmup), len(formal))
        if int(formal[index]) == target and int(formal[index - 1]) != target
    ]
    previous_counts: Counter[str] = Counter(str(int(formal[index - 1])) for index in onsets)
    ages = [last_event_age(events, index) for index in onsets]

    def transition_summary(previous_stage: int) -> dict[str, object]:
        subset = [index for index in onsets if int(formal[index - 1]) == previous_stage]
        subset_ages = [last_event_age(events, index) for index in subset]
        return {
            "events": int(len(subset)),
            "fresh_break_same_bar": int(sum(age == 0 for age in subset_ages)),
            "fresh_break_within_prior": {
                str(checkpoint): int(sum(age is not None and age <= checkpoint for age in subset_ages))
                for checkpoint in (1, 3, 5, 20)
            },
            "last_break_age_histogram_0_20": lag_histogram(subset_ages),
        }

    return {
        "target_onsets": int(len(onsets)),
        "previous_formal_stage": dict(sorted(previous_counts.items(), key=lambda item: int(item[0]))),
        "fresh_break_same_bar": int(sum(age == 0 for age in ages)),
        "fresh_break_within_prior": {
            str(checkpoint): int(sum(age is not None and age <= checkpoint for age in ages))
            for checkpoint in (1, 3, 5, 20)
        },
        "last_break_age_histogram_0_20": lag_histogram(ages),
        "initial_transition": transition_summary(initial_from),
        "renewal_transition": transition_summary(renewal_from),
    }


def stage_occupancy(formal: np.ndarray, warmup: int) -> dict[str, object]:
    eligible = formal[warmup:]
    counts = {str(stage): int(np.sum(eligible == stage)) for stage in range(7)}
    total = max(1, len(eligible))
    shares = {stage: count / total for stage, count in counts.items()}
    return {"bars": int(len(eligible)), "counts": counts, "shares": shares}


def analyze_pair(frame: pd.DataFrame) -> dict[str, object]:
    namespace = load_phase_b_namespace()
    config_type = namespace["PriceOnlyConfig"]
    compute_price_only = namespace["compute_price_only"]
    config = config_type()
    model = compute_price_only(frame.copy(), config)

    formal = pd.to_numeric(model["formal_id"], errors="coerce").fillna(0).to_numpy(int)
    up = pd.to_numeric(model["range_break_up"], errors="coerce").fillna(0).to_numpy(float) > 0.5
    down = pd.to_numeric(model["range_break_dn"], errors="coerce").fillna(0).to_numpy(float) > 0.5
    # rank_len is the longest frozen percentile warm-up and is fixed by the model,
    # not selected from this audit's event counts.
    warmup = int(config.rank_len - 1)

    return {
        "rows": int(len(frame)),
        "start_date": str(pd.Timestamp(frame["date"].iloc[0]).date()),
        "end_date": str(pd.Timestamp(frame["date"].iloc[-1]).date()),
        "warmup_bars": warmup,
        "eligible_start_date": str(pd.Timestamp(frame["date"].iloc[warmup]).date()),
        "formal_stage_occupancy": stage_occupancy(formal, warmup),
        "bull": {
            "break_to_stage": summarize_break_side(formal, up, target=2, warmup=warmup),
            "stage_onsets": summarize_target_onsets(formal, up, target=2, initial_from=1, renewal_from=3, warmup=warmup),
        },
        "bear": {
            "break_to_stage": summarize_break_side(formal, down, target=5, warmup=warmup),
            "stage_onsets": summarize_target_onsets(formal, down, target=5, initial_from=4, renewal_from=6, warmup=warmup),
        },
    }


def aggregate_side(pairs: dict[str, dict[str, object]], side: str) -> dict[str, object]:
    break_rows = [pair[side]["break_to_stage"] for pair in pairs.values()]  # type: ignore[index]
    onset_rows = [pair[side]["stage_onsets"] for pair in pairs.values()]  # type: ignore[index]

    confirmation = {
        str(checkpoint): int(sum(int(row["confirmation_within"][str(checkpoint)]) for row in break_rows))  # type: ignore[index]
        for checkpoint in CHECKPOINTS
    }
    break_hist = {
        str(lag): int(sum(int(row["confirmation_lag_histogram_0_20"][str(lag)]) for row in break_rows))  # type: ignore[index]
        for lag in range(HORIZON + 1)
    }
    break_hist["none"] = int(sum(int(row["confirmation_lag_histogram_0_20"]["none"]) for row in break_rows))  # type: ignore[index]

    def aggregate_transition(name: str) -> dict[str, object]:
        rows = [row[name] for row in onset_rows]  # type: ignore[index]
        return {
            "events": int(sum(int(row["events"]) for row in rows)),
            "fresh_break_same_bar": int(sum(int(row["fresh_break_same_bar"]) for row in rows)),
            "fresh_break_within_prior": {
                str(checkpoint): int(sum(int(row["fresh_break_within_prior"][str(checkpoint)]) for row in rows))  # type: ignore[index]
                for checkpoint in (1, 3, 5, 20)
            },
        }

    return {
        "fresh_breaks": int(sum(int(row["fresh_breaks"]) for row in break_rows)),
        "already_target_before_break": int(sum(int(row["already_target_before_break"]) for row in break_rows)),
        "not_already_target_before_break": int(sum(int(row["not_already_target_before_break"]) for row in break_rows)),
        "confirmation_within": confirmation,
        "confirmation_lag_histogram_0_20": break_hist,
        "target_onsets": int(sum(int(row["target_onsets"]) for row in onset_rows)),
        "target_onsets_with_fresh_break_same_bar": int(sum(int(row["fresh_break_same_bar"]) for row in onset_rows)),
        "initial_transition": aggregate_transition("initial_transition"),
        "renewal_transition": aggregate_transition("renewal_transition"),
    }


def build_report() -> dict[str, object]:
    pairs = {pair: analyze_pair(frame) for pair, frame in load_frozen_pairs().items()}
    return {
        "schema_version": 1,
        "issue": 61,
        "status": "PHASE_A_TIMING_AUDIT_REUSED_DATA_NO_PNL",
        "engine": "Issue #57 frozen v0.6 Phase-B six-stage core",
        "fresh_break_definition": "existing 20-bar rangeBreakUp/rangeBreakDn pulse",
        "horizon_bars": HORIZON,
        "checkpoints": list(CHECKPOINTS),
        "pairs": pairs,
        "aggregate": {
            "pair_count": len(pairs),
            "bull": aggregate_side(pairs, "bull"),
            "bear": aggregate_side(pairs, "bear"),
        },
        "boundary": "Timing/state counts only. All fixtures are reused evidence. No PnL or independent validation claim.",
    }


def pct(count: int, total: int) -> str:
    return "—" if total <= 0 else f"{100.0 * count / total:.1f}%"


def render_markdown(report: dict[str, object]) -> str:
    lines = [
        "# Issue #61 — Phase A fresh-break / Formal-stage timing audit",
        "",
        "**Reused-data semantic/timing audit only. No PnL.**",
        "",
        f"- Engine: {report['engine']}",
        f"- Fresh break: {report['fresh_break_definition']}",
        f"- Frozen descriptive horizon: +{report['horizon_bars']} bars.",
        "- Warm-up: model `rank_len - 1` (755 bars under frozen defaults).",
        "",
        "## Aggregate",
        "",
        "| Side | Fresh breaks | Already in target before break | Need later target confirmation | Target by same bar | by +1 | by +3 | by +5 | by +20 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for side, label in (("bull", "Bull → Stage 2"), ("bear", "Bear → Stage 5")):
        row = report["aggregate"][side]  # type: ignore[index]
        need = int(row["not_already_target_before_break"])
        c = row["confirmation_within"]
        lines.append(
            f"| {label} | {row['fresh_breaks']} | {row['already_target_before_break']} | {need} | "
            f"{c['0']} ({pct(int(c['0']), need)}) | {c['1']} ({pct(int(c['1']), need)}) | "
            f"{c['3']} ({pct(int(c['3']), need)}) | {c['5']} ({pct(int(c['5']), need)}) | "
            f"{c['20']} ({pct(int(c['20']), need)}) |"
        )

    lines += [
        "",
        "## Stage-onset alignment",
        "",
        "| Side | Target onsets | Fresh break same bar | Initial 1→2 / 4→5 | Initial same-bar break | Renewal 3→2 / 6→5 | Renewal same-bar break |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for side, label in (("bull", "Bull"), ("bear", "Bear")):
        row = report["aggregate"][side]  # type: ignore[index]
        initial = row["initial_transition"]
        renewal = row["renewal_transition"]
        lines.append(
            f"| {label} | {row['target_onsets']} | {row['target_onsets_with_fresh_break_same_bar']} | "
            f"{initial['events']} | {initial['fresh_break_same_bar']} | {renewal['events']} | {renewal['fresh_break_same_bar']} |"
        )

    lines += ["", "## Per pair", ""]
    for pair, pair_result in report["pairs"].items():  # type: ignore[index]
        lines += [f"### {pair}", "", "| Side | Fresh breaks | Already target | Need confirm | Same bar | +3 | +5 | +20 | Renewal events | Renewal same-bar break |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for side, label in (("bull", "Bull"), ("bear", "Bear")):
            br = pair_result[side]["break_to_stage"]
            on = pair_result[side]["stage_onsets"]
            renewal = on["renewal_transition"]
            c = br["confirmation_within"]
            lines.append(
                f"| {label} | {br['fresh_breaks']} | {br['already_target_before_break']} | {br['not_already_target_before_break']} | "
                f"{c['0']} | {c['3']} | {c['5']} | {c['20']} | {renewal['events']} | {renewal['fresh_break_same_bar']} |"
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
    args.json_output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.md_output.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["aggregate"], indent=2))


if __name__ == "__main__":
    main()
