#!/usr/bin/env python3
"""Issue #68 Phase A: semantic/symmetry audit of transplanted lifecycle v2.

Strictly no PnL.  Reuses burned four-FX development fixtures only to test
engineering semantics and reciprocal lifecycle behavior.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import diagnose_issue66_reciprocal_symmetry as phasea
from generate_issue66_phase_c2_stage14_conflict_core import load_phase_c2_namespace
from issue68_lifecycle_v2 import LifecycleResult, holding_durations, lifecycle_v2


HERE = Path(__file__).resolve().parent
OLD_LIFECYCLE_MIRROR_BASELINE = 0.8644
PHASE_A_GATE = 0.95

EVENT_MIRRORS = {
    "arm_long": "arm_short",
    "arm_short": "arm_long",
    "entry_long": "entry_short",
    "entry_short": "entry_long",
    "early_fail_long": "early_fail_short",
    "early_fail_short": "early_fail_long",
    "opposite_exit_long": "opposite_exit_short",
    "opposite_exit_short": "opposite_exit_long",
    "add_long_candidate": "add_short_candidate",
    "add_short_candidate": "add_long_candidate",
    "cancel_long_arm": "cancel_short_arm",
    "cancel_short_arm": "cancel_long_arm",
    "direct_transition_long": "direct_transition_short",
    "direct_transition_short": "direct_transition_long",
}


def _arr_float(model: pd.DataFrame, key: str) -> np.ndarray:
    return pd.to_numeric(model[key], errors="coerce").to_numpy(float)


def _arr_bool(model: pd.DataFrame, key: str) -> np.ndarray:
    return np.nan_to_num(_arr_float(model, key), nan=0.0) > 0.5


def _arr_int(model: pd.DataFrame, key: str) -> np.ndarray:
    return np.nan_to_num(_arr_float(model, key), nan=0.0).astype(int)


def _compute_c2(frame: pd.DataFrame) -> tuple[pd.DataFrame, Any]:
    ns = load_phase_c2_namespace()
    cfg = ns["PriceOnlyConfig"]()
    return ns["compute_price_only"](frame.copy(), cfg), cfg


def _run_lifecycle(frame: pd.DataFrame) -> tuple[pd.DataFrame, Any, LifecycleResult, int]:
    model, cfg = _compute_c2(frame)
    warmup = int(cfg.rank_len - 1)  # exact canonical Pine `issue61Ready` gate
    result = lifecycle_v2(
        _arr_int(model, "formal_id"),
        _arr_bool(model, "range_break_up"),
        _arr_bool(model, "range_break_dn"),
        pd.to_numeric(frame["close"], errors="coerce").to_numpy(float),
        _arr_float(model, "range_high_break"),
        _arr_float(model, "range_low_break"),
        warmup=warmup,
        confirm_bars=int(cfg.confirm_bars),
    )
    return model, cfg, result, warmup


def _boolean_pair(left: np.ndarray, right: np.ndarray, warmup: int) -> dict[str, float | int]:
    a = np.asarray(left, dtype=bool)[warmup:]
    b = np.asarray(right, dtype=bool)[warmup:]
    union = a | b
    both = a & b
    return {
        "bars": int(len(a)),
        "bar_agreement": float(np.mean(a == b)) if len(a) else 1.0,
        "left_true": int(np.sum(a)),
        "right_true": int(np.sum(b)),
        "both_true": int(np.sum(both)),
        "either_true": int(np.sum(union)),
        "event_jaccard": float(np.sum(both) / np.sum(union)) if np.any(union) else 1.0,
        "mismatch_bars": int(np.sum(a != b)),
    }


def _position_mirror(left: np.ndarray, inverse: np.ndarray, warmup: int) -> dict[str, float | int]:
    a = np.asarray(left, dtype=int)[warmup:]
    b = np.asarray(inverse, dtype=int)[warmup:]
    matches = a == -b
    return {
        "bars": int(len(a)),
        "mirror_agreement": float(np.mean(matches)) if len(a) else 1.0,
        "mismatch_bars": int(np.sum(~matches)),
    }


def _occupancy(position: np.ndarray, warmup: int) -> dict[str, float | int]:
    values = np.asarray(position, dtype=int)[warmup:]
    n = len(values)
    return {
        "bars": int(n),
        "flat_bars": int(np.sum(values == 0)),
        "long_bars": int(np.sum(values == 1)),
        "short_bars": int(np.sum(values == -1)),
        "flat_share": float(np.mean(values == 0)) if n else 1.0,
        "long_share": float(np.mean(values == 1)) if n else 0.0,
        "short_share": float(np.mean(values == -1)) if n else 0.0,
    }


def _lag_hist(result: LifecycleResult, warmup: int, confirm_bars: int) -> dict[str, int]:
    lag = result.entry_lag[warmup:]
    finite = lag[np.isfinite(lag)].astype(int)
    out = {str(i): int(np.sum(finite == i)) for i in range(confirm_bars + 1)}
    out["other"] = int(np.sum((finite < 0) | (finite > confirm_bars)))
    return out


def _event_counts(result: LifecycleResult, warmup: int) -> dict[str, int]:
    return {key: int(np.sum(values[warmup:])) for key, values in result.events.items()}


def _holding_summary(position: np.ndarray, warmup: int) -> dict[str, float | int | None]:
    durations = holding_durations(position, start=warmup)
    if not durations:
        return {"episodes": 0, "median_bars": None, "mean_bars": None, "max_bars": None}
    arr = np.asarray(durations, dtype=float)
    return {
        "episodes": int(len(durations)),
        "median_bars": float(np.median(arr)),
        "mean_bars": float(np.mean(arr)),
        "max_bars": int(np.max(arr)),
    }


def analyze_pair(frame: pd.DataFrame) -> dict[str, Any]:
    inv_frame = phasea.reciprocal_ohlc(frame)
    model, cfg, life, warmup = _run_lifecycle(frame)
    inv_model, _, inv_life, inv_warmup = _run_lifecycle(inv_frame)
    if warmup != inv_warmup:
        raise AssertionError("original/inverse warmup differs")

    event_mirrors = {
        f"{left}__to_inverse__{right}": _boolean_pair(life.events[left], inv_life.events[right], warmup)
        for left, right in EVENT_MIRRORS.items()
    }

    formal = _arr_int(model, "formal_id")
    inv_formal = _arr_int(inv_model, "formal_id")
    formal_mirror = phasea.stage_metrics(formal, inv_formal, warmup)
    position = _position_mirror(life.position, inv_life.position, warmup)

    # Armed direction and entry age are state-machine internals.  Armed direction
    # should sign-mirror; entry age should be identical whenever both sides are
    # in mirrored desired-position states.
    arm_state = _position_mirror(life.armed_dir, inv_life.armed_dir, warmup)
    a_pos = life.position[warmup:]
    b_pos = inv_life.position[warmup:]
    mirrored_pos = a_pos == -b_pos
    a_age = life.entry_age[warmup:]
    b_age = inv_life.entry_age[warmup:]
    age_mask = mirrored_pos & (a_age >= 0) & (b_age >= 0)
    age_agreement = 1.0 if not np.any(age_mask) else float(np.mean(a_age[age_mask] == b_age[age_mask]))

    return {
        "rows": int(len(frame)),
        "start_date": str(pd.Timestamp(frame["date"].iloc[0]).date()),
        "end_date": str(pd.Timestamp(frame["date"].iloc[-1]).date()),
        "warmup_bars": warmup,
        "confirm_bars": int(cfg.confirm_bars),
        "formal_stage_mirror": formal_mirror,
        "desired_position_mirror": position,
        "armed_direction_mirror": arm_state,
        "entry_age_mirror_on_mirrored_positions": age_agreement,
        "event_mirrors": event_mirrors,
        "original": {
            "event_counts": _event_counts(life, warmup),
            "entry_lag_histogram": _lag_hist(life, warmup, int(cfg.confirm_bars)),
            "occupancy": _occupancy(life.position, warmup),
            "holding": _holding_summary(life.position, warmup),
        },
        "inverse": {
            "event_counts": _event_counts(inv_life, warmup),
            "entry_lag_histogram": _lag_hist(inv_life, warmup, int(cfg.confirm_bars)),
            "occupancy": _occupancy(inv_life.position, warmup),
            "holding": _holding_summary(inv_life.position, warmup),
        },
    }


def build_report() -> dict[str, Any]:
    pairs = {name: analyze_pair(frame) for name, frame in phasea.load_frozen_pairs().items()}
    total_bars = sum(int(row["desired_position_mirror"]["bars"]) for row in pairs.values())
    total_mismatch = sum(int(row["desired_position_mirror"]["mismatch_bars"]) for row in pairs.values())
    aggregate_agreement = 1.0 if total_bars == 0 else 1.0 - total_mismatch / total_bars

    formal_bars = sum(int(row["formal_stage_mirror"]["bars"]) for row in pairs.values())
    formal_mismatch = sum(int(row["formal_stage_mirror"]["mismatch_bars"]) for row in pairs.values())
    formal_agreement = 1.0 if formal_bars == 0 else 1.0 - formal_mismatch / formal_bars

    event_totals: dict[str, dict[str, float | int]] = {}
    for key in next(iter(pairs.values()))["event_mirrors"].keys() if pairs else []:
        bars = sum(int(row["event_mirrors"][key]["bars"]) for row in pairs.values())
        mismatch = sum(int(row["event_mirrors"][key]["mismatch_bars"]) for row in pairs.values())
        both = sum(int(row["event_mirrors"][key]["both_true"]) for row in pairs.values())
        union = sum(int(row["event_mirrors"][key]["either_true"]) for row in pairs.values())
        event_totals[key] = {
            "bars": bars,
            "bar_agreement": 1.0 if bars == 0 else 1.0 - mismatch / bars,
            "mismatch_bars": mismatch,
            "both_true": both,
            "either_true": union,
            "event_jaccard": 1.0 if union == 0 else both / union,
        }

    return {
        "schema_version": 1,
        "issue": 68,
        "phase": "A",
        "status": "LIFECYCLE_V2_TRANSPLANT_REUSED_DATA_NO_PNL",
        "old_issue61_desired_position_mirror_baseline": OLD_LIFECYCLE_MIRROR_BASELINE,
        "preregistered_desired_position_gate": PHASE_A_GATE,
        "primary_gate_pass": bool(aggregate_agreement >= PHASE_A_GATE),
        "aggregate": {
            "pair_count": len(pairs),
            "desired_position_mirror_agreement": aggregate_agreement,
            "desired_position_mismatch_bars": total_mismatch,
            "formal_stage_mirror_agreement": formal_agreement,
            "gain_vs_old_issue61_lifecycle_mirror": aggregate_agreement - OLD_LIFECYCLE_MIRROR_BASELINE,
            "event_mirrors": event_totals,
        },
        "pairs": pairs,
        "boundary": "No PnL/return/Sharpe/drawdown/sizing/stop/target metrics are computed. Burned four-FX evidence is semantic engineering data only.",
    }


def _pct(x: float) -> str:
    return f"{100.0 * x:.2f}%"


def render_markdown(r: dict[str, Any]) -> str:
    a = r["aggregate"]
    lines = [
        "# Issue #68 Phase A — Human-review-v2 Lifecycle Transplant Audit",
        "",
        "Status: **reused burned development data / semantic engineering only / no PnL**",
        "",
        f"Primary gate: **{'PASS' if r['primary_gate_pass'] else 'FAIL'}**",
        f"- Old Issue #61 desired-position mirror: **{_pct(r['old_issue61_desired_position_mirror_baseline'])}**",
        f"- Preregistered Issue #68 gate: **>= {_pct(r['preregistered_desired_position_gate'])}**",
        f"- Current C-2 lifecycle desired-position mirror: **{_pct(a['desired_position_mirror_agreement'])}**",
        f"- Gain vs old lifecycle mirror: **{100.0 * a['gain_vs_old_issue61_lifecycle_mirror']:.2f} pp**",
        f"- Current C-2 Formal mirror on same scored bars: **{_pct(a['formal_stage_mirror_agreement'])}**",
        "",
        "## Per pair",
        "",
        "| Pair | Formal mirror | Lifecycle position mirror | Position mismatch bars | Flat / Long / Short | Median hold |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, row in r["pairs"].items():
        occ = row["original"]["occupancy"]
        hold = row["original"]["holding"]
        median = "—" if hold["median_bars"] is None else f"{hold['median_bars']:.1f}"
        lines.append(
            f"| {name} | {_pct(row['formal_stage_mirror']['mirror_agreement'])} | "
            f"{_pct(row['desired_position_mirror']['mirror_agreement'])} | {row['desired_position_mirror']['mismatch_bars']} | "
            f"{_pct(occ['flat_share'])} / {_pct(occ['long_share'])} / {_pct(occ['short_share'])} | {median} |"
        )

    lines += ["", "## Aggregate mirrored event families", "", "| Event mirror | Bar agreement | Jaccard | Mismatch bars | Either event |", "|---|---:|---:|---:|---:|"]
    for key, row in a["event_mirrors"].items():
        lines.append(f"| `{key}` | {_pct(row['bar_agreement'])} | {_pct(row['event_jaccard'])} | {row['mismatch_bars']} | {row['either_true']} |")

    lines += ["", "## Event counts and setup lag", ""]
    for name, row in r["pairs"].items():
        lines += [f"### {name}", "", f"- Original events: `{row['original']['event_counts']}`", f"- Original entry lag histogram: `{row['original']['entry_lag_histogram']}`", f"- Holding summary: `{row['original']['holding']}`", ""]

    lines += ["## Boundary", "", str(r["boundary"]), ""]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json-output", type=Path, required=True)
    ap.add_argument("--md-output", type=Path, required=True)
    args = ap.parse_args()
    report = build_report()
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.md_output.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({
        "primary_gate_pass": report["primary_gate_pass"],
        "desired_position_mirror_agreement": report["aggregate"]["desired_position_mirror_agreement"],
    }, indent=2))


if __name__ == "__main__":
    main()
