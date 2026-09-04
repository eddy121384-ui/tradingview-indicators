#!/usr/bin/env python3
"""Issue #68 B3.5 Core Bias reversal forensic. Engineering semantics only."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import diagnose_issue66_reciprocal_symmetry as phasea
from generate_issue66_phase_c2_stage14_conflict_core import load_phase_c2_namespace
from issue68_core_bias_v33 import core_bias_v33

HERE = Path(__file__).resolve().parent
CORE_MIRROR_GATE = 0.99


def _arr_float(model: pd.DataFrame, key: str) -> np.ndarray:
    return pd.to_numeric(model[key], errors="coerce").to_numpy(float)


def _arr_int(model: pd.DataFrame, key: str) -> np.ndarray:
    return np.nan_to_num(_arr_float(model, key), nan=0.0).astype(int)


def trend_direction(stage_ids: np.ndarray) -> np.ndarray:
    """Map C-2 stage ids to bull trend family +1, bear trend family -1, else 0."""
    x = np.asarray(stage_ids, dtype=int)
    out = np.zeros(len(x), dtype=int)
    out[np.isin(x, (2, 3))] = 1
    out[np.isin(x, (5, 6))] = -1
    return out


def _direction_mirror(a: np.ndarray, b: np.ndarray, warmup: int) -> dict[str, float | int]:
    x = np.asarray(a, dtype=int)[warmup:]
    y = np.asarray(b, dtype=int)[warmup:]
    good = x == -y
    return {
        "bars": int(len(x)),
        "mirror_agreement": float(np.mean(good)) if len(x) else 1.0,
        "mismatch_bars": int(np.sum(~good)),
    }


def _compute(frame: pd.DataFrame):
    ns = load_phase_c2_namespace()
    cfg = ns["PriceOnlyConfig"]()
    return ns["compute_price_only"](frame.copy(), cfg), cfg


def _date_value(frame: pd.DataFrame, i: int) -> str | None:
    for key in ("date", "datetime", "time"):
        if key in frame.columns:
            value = frame.iloc[i][key]
            return None if pd.isna(value) else str(value)
    return None


def _run_starts(direction: np.ndarray, wanted: int, lo: int, hi: int) -> list[int]:
    starts: list[int] = []
    for j in range(max(lo, 0), max(lo, hi)):
        if direction[j] == wanted and (j == 0 or direction[j - 1] != wanted):
            starts.append(j)
    return starts


def _flip_events(frame: pd.DataFrame, model: pd.DataFrame, warmup: int) -> list[dict[str, Any]]:
    formal = _arr_int(model, "formal_id")
    top = trend_direction(_arr_int(model, "top_id"))
    strong_mask = model["strong_candidate"].astype(bool).to_numpy()
    strong = np.where(strong_mask, top, 0).astype(int)
    candidate_bars = _arr_int(model, "candidate_bars")
    fast_switch = model["fast_switch"].astype(bool).to_numpy()
    bias_result = core_bias_v33(formal, warmup=warmup)
    bias = bias_result.bias

    flip_mask = bias_result.events["flip_bull_to_bear"] | bias_result.events["flip_bear_to_bull"]
    indices = np.flatnonzero(flip_mask)
    events: list[dict[str, Any]] = []
    previous_flip = warmup - 1

    for i in indices:
        new_dir = int(bias[i])
        old_dir = -new_dir
        formal_dir = int(trend_direction(np.array([formal[i]], dtype=int))[0])
        if formal_dir != new_dir:
            raise AssertionError(f"Core flip at {i} is not triggered by opposite Formal family")

        direct_strong_start = i
        while direct_strong_start > warmup and strong[direct_strong_start - 1] == new_dir:
            direct_strong_start -= 1
        if strong[i] != new_dir:
            raise AssertionError(f"Core flip at {i} lacks same-bar opposite strong candidate")

        local_top_start = direct_strong_start
        while local_top_start > warmup and top[local_top_start - 1] == new_dir:
            local_top_start -= 1

        prior_starts = _run_starts(strong, new_dir, previous_flip + 1, direct_strong_start)
        events.append({
            "index": int(i),
            "date": _date_value(frame, int(i)),
            "old_bias": old_dir,
            "new_bias": new_dir,
            "formal_stage": int(formal[i]),
            "formal_to_core_lag_bars": 0,
            "candidate_bars_at_flip": int(candidate_bars[i]),
            "fast_switch_at_flip": bool(fast_switch[i]),
            "direct_strong_run_start": int(direct_strong_start),
            "direct_strong_run_bars": int(i - direct_strong_start + 1),
            "local_top_run_start": int(local_top_start),
            "local_top_to_strong_lag_bars": int(direct_strong_start - local_top_start),
            "strong_to_formal_lag_bars": int(i - direct_strong_start),
            "prior_opposite_strong_runs_since_previous_flip": int(len(prior_starts)),
            "bars_since_previous_core_flip": int(i - previous_flip),
        })
        previous_flip = int(i)
    return events


def analyze_pair(frame: pd.DataFrame) -> dict[str, Any]:
    inv = phasea.reciprocal_ohlc(frame)
    model, cfg = _compute(frame)
    inv_model, inv_cfg = _compute(inv)
    warmup = int(cfg.rank_len - 1)
    if int(inv_cfg.rank_len - 1) != warmup:
        raise AssertionError("warmup mismatch")

    top = trend_direction(_arr_int(model, "top_id"))
    inv_top = trend_direction(_arr_int(inv_model, "top_id"))
    strong = np.where(model["strong_candidate"].astype(bool).to_numpy(), top, 0)
    inv_strong = np.where(inv_model["strong_candidate"].astype(bool).to_numpy(), inv_top, 0)
    formal = trend_direction(_arr_int(model, "formal_id"))
    inv_formal = trend_direction(_arr_int(inv_model, "formal_id"))
    bias = core_bias_v33(_arr_int(model, "formal_id"), warmup=warmup).bias
    inv_bias = core_bias_v33(_arr_int(inv_model, "formal_id"), warmup=warmup).bias
    events = _flip_events(frame, model, warmup)

    return {
        "warmup": warmup,
        "top_direction_mirror": _direction_mirror(top, inv_top, warmup),
        "strong_direction_mirror": _direction_mirror(strong, inv_strong, warmup),
        "formal_direction_mirror": _direction_mirror(formal, inv_formal, warmup),
        "core_direction_mirror": _direction_mirror(bias, inv_bias, warmup),
        "core_flip_count": len(events),
        "flip_events": events,
    }


def _event_values(pairs: dict[str, Any], key: str) -> list[int]:
    return [int(e[key]) for p in pairs.values() for e in p["flip_events"]]


def _median(values: list[int]) -> float:
    return float(np.median(values)) if values else 0.0


def build_report() -> dict[str, Any]:
    pairs = {name: analyze_pair(frame) for name, frame in phasea.load_frozen_pairs().items()}
    core_bars = sum(int(p["core_direction_mirror"]["bars"]) for p in pairs.values())
    core_bad = sum(int(p["core_direction_mirror"]["mismatch_bars"]) for p in pairs.values())
    core_mirror = 1.0 if core_bars == 0 else 1.0 - core_bad / core_bars

    formal_to_core = _event_values(pairs, "formal_to_core_lag_bars")
    top_to_strong = _event_values(pairs, "local_top_to_strong_lag_bars")
    strong_to_formal = _event_values(pairs, "strong_to_formal_lag_bars")
    prior_attempts = _event_values(pairs, "prior_opposite_strong_runs_since_previous_flip")
    direct_runs = _event_values(pairs, "direct_strong_run_bars")

    invariant_ok = all(v == 0 for v in formal_to_core)
    return {
        "schema_version": 1,
        "issue": 68,
        "phase": "B3.5",
        "status": "CORE_BIAS_REVERSAL_FORENSIC_NO_PERFORMANCE",
        "primary_gate_pass": bool(invariant_ok and core_mirror >= CORE_MIRROR_GATE),
        "aggregate": {
            "core_mirror_gate": CORE_MIRROR_GATE,
            "core_direction_mirror_agreement": core_mirror,
            "core_flip_events": len(formal_to_core),
            "formal_to_core_zero_lag_invariant": invariant_ok,
            "max_formal_to_core_lag_bars": max(formal_to_core) if formal_to_core else 0,
            "median_local_top_to_strong_lag_bars": _median(top_to_strong),
            "median_strong_to_formal_lag_bars": _median(strong_to_formal),
            "max_strong_to_formal_lag_bars": max(strong_to_formal) if strong_to_formal else 0,
            "median_direct_strong_run_bars": _median(direct_runs),
            "median_prior_opposite_strong_runs": _median(prior_attempts),
            "total_prior_opposite_strong_runs": int(sum(prior_attempts)),
        },
        "pairs": pairs,
        "boundary": "Diagnostic semantics only. No strategy performance, sizing, stops, targets, or execution optimization is evaluated.",
    }


def render_markdown(r: dict[str, Any]) -> str:
    a = r["aggregate"]
    lines = [
        "# Issue #68 Phase B3.5 — Core Bias Reversal Forensic",
        "",
        "Status: **diagnostic only / frozen C-2 + frozen B3.3**",
        "",
        f"Primary gate: **{'PASS' if r['primary_gate_pass'] else 'FAIL'}**",
        f"- Core reciprocal mirror: **{100*a['core_direction_mirror_agreement']:.2f}%**",
        f"- Formal -> Core zero-lag invariant: **{a['formal_to_core_zero_lag_invariant']}**",
        f"- Core flip events inspected: **{a['core_flip_events']}**",
        f"- median local TOP -> STRONG lag: **{a['median_local_top_to_strong_lag_bars']:.1f} bars**",
        f"- median STRONG -> FORMAL lag: **{a['median_strong_to_formal_lag_bars']:.1f} bars**",
        f"- max STRONG -> FORMAL lag: **{a['max_strong_to_formal_lag_bars']} bars**",
        f"- median direct STRONG run: **{a['median_direct_strong_run_bars']:.1f} bars**",
        f"- prior opposite-STRONG attempts before successful flips: **{a['total_prior_opposite_strong_runs']} total**",
        "",
        "## Per pair",
        "",
        "| Pair | TOP mirror | STRONG mirror | FORMAL mirror | CORE mirror | Core flips |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, p in r["pairs"].items():
        lines.append(
            f"| {name} | {100*p['top_direction_mirror']['mirror_agreement']:.2f}% | "
            f"{100*p['strong_direction_mirror']['mirror_agreement']:.2f}% | "
            f"{100*p['formal_direction_mirror']['mirror_agreement']:.2f}% | "
            f"{100*p['core_direction_mirror']['mirror_agreement']:.2f}% | {p['core_flip_count']} |"
        )
    lines += [
        "",
        "## Interpretation boundary",
        "",
        "The local TOP/STRONG lags describe the classifier's immediate lead-in to an actual Core flip. They do not claim to identify the economically true reversal date. Cross-market TradingView review is required to determine whether suspected stale bias begins before TOP, between TOP and STRONG, or between STRONG and FORMAL.",
        "",
        r["boundary"],
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, default=HERE / "reports/issue-68-phase-b35-core-bias-reversal.json")
    ap.add_argument("--md", type=Path, default=HERE / "reports/issue-68-phase-b35-core-bias-reversal.md")
    args = ap.parse_args()
    report = build_report()
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    args.md.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["aggregate"], indent=2, sort_keys=True))
    if not report["primary_gate_pass"]:
        raise SystemExit("Issue #68 B3.5 forensic invariant failed")


if __name__ == "__main__":
    main()
