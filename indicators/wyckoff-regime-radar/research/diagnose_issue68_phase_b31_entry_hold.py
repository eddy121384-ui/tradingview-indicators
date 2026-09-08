#!/usr/bin/env python3
"""Issue #68 B3.1 entry/hold separation semantic diagnostic. No PnL."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import diagnose_issue66_reciprocal_symmetry as phasea
from generate_issue66_phase_c2_stage14_conflict_core import load_phase_c2_namespace
from issue68_lifecycle_v3_regime_first import holding_durations
from issue68_lifecycle_v31_entry_hold import lifecycle_v31

HERE = Path(__file__).resolve().parent
MIRROR_GATE = 0.99


def _arr_float(model: pd.DataFrame, key: str) -> np.ndarray:
    return pd.to_numeric(model[key], errors="coerce").to_numpy(float)


def _arr_bool(model: pd.DataFrame, key: str) -> np.ndarray:
    return np.nan_to_num(_arr_float(model, key), nan=0.0) > 0.5


def _arr_int(model: pd.DataFrame, key: str) -> np.ndarray:
    return np.nan_to_num(_arr_float(model, key), nan=0.0).astype(int)


def _compute(frame: pd.DataFrame):
    ns = load_phase_c2_namespace()
    cfg = ns["PriceOnlyConfig"]()
    return ns["compute_price_only"](frame.copy(), cfg), cfg


def _run(frame: pd.DataFrame):
    model, cfg = _compute(frame)
    warmup = int(cfg.rank_len - 1)
    formal = _arr_int(model, "formal_id")
    top = _arr_int(model, "top_id")
    strong = _arr_bool(model, "strong_candidate")
    strong_stage = np.where(strong, top, 0).astype(int)
    life = lifecycle_v31(formal, strong_stage, warmup=warmup)
    return model, warmup, strong_stage, life


def _position_mirror(a: np.ndarray, b: np.ndarray, warmup: int) -> dict[str, float | int]:
    x = np.asarray(a, dtype=int)[warmup:]
    y = np.asarray(b, dtype=int)[warmup:]
    good = x == -y
    return {"bars": int(len(x)), "mirror_agreement": float(np.mean(good)) if len(x) else 1.0, "mismatch_bars": int(np.sum(~good))}


def _occupancy(position: np.ndarray, warmup: int) -> dict[str, float | int]:
    x = np.asarray(position, dtype=int)[warmup:]
    n = len(x)
    return {
        "bars": int(n),
        "flat_share": float(np.mean(x == 0)) if n else 1.0,
        "long_share": float(np.mean(x == 1)) if n else 0.0,
        "short_share": float(np.mean(x == -1)) if n else 0.0,
    }


def _holding(position: np.ndarray, warmup: int) -> dict[str, float | int | None]:
    d = holding_durations(position, start=warmup)
    if not d:
        return {"episodes": 0, "median_bars": None, "mean_bars": None, "max_bars": None}
    a = np.asarray(d, dtype=float)
    return {"episodes": int(len(d)), "median_bars": float(np.median(a)), "mean_bars": float(np.mean(a)), "max_bars": int(np.max(a))}


def _event_counts(events: dict[str, np.ndarray], warmup: int) -> dict[str, int]:
    return {k: int(np.sum(v[warmup:])) for k, v in events.items()}


def analyze_pair(frame: pd.DataFrame) -> dict[str, Any]:
    inv = phasea.reciprocal_ohlc(frame)
    model, warmup, strong_stage, life = _run(frame)
    inv_model, inv_warmup, inv_strong_stage, inv_life = _run(inv)
    if warmup != inv_warmup:
        raise AssertionError("warmup mismatch")

    formal = _arr_int(model, "formal_id")
    inv_formal = _arr_int(inv_model, "formal_id")
    strong_mirror = phasea.stage_metrics(strong_stage, inv_strong_stage, warmup)
    return {
        "rows": int(len(frame)),
        "warmup_bars": warmup,
        "formal_stage_mirror": phasea.stage_metrics(formal, inv_formal, warmup),
        "strong_stage_mirror": strong_mirror,
        "v31_position_mirror": _position_mirror(life.position, inv_life.position, warmup),
        "v31": {
            "occupancy": _occupancy(life.position, warmup),
            "holding": _holding(life.position, warmup),
            "event_counts": _event_counts(life.events, warmup),
        },
    }


def build_report() -> dict[str, Any]:
    pairs = {name: analyze_pair(frame) for name, frame in phasea.load_frozen_pairs().items()}
    bars = sum(int(v["v31_position_mirror"]["bars"]) for v in pairs.values())
    mismatch = sum(int(v["v31_position_mirror"]["mismatch_bars"]) for v in pairs.values())
    mirror = 1.0 if bars == 0 else 1.0 - mismatch / bars
    entry_count = sum(v["v31"]["event_counts"]["enter_long"] + v["v31"]["event_counts"]["enter_short"] for v in pairs.values())
    blocked_count = sum(v["v31"]["event_counts"]["blocked_long_entry"] + v["v31"]["event_counts"]["blocked_short_entry"] for v in pairs.values())
    return {
        "schema_version": 1,
        "issue": 68,
        "phase": "B3.1",
        "status": "ENTRY_HOLD_SEPARATION_SEMANTIC_DIAGNOSTIC_NO_PNL",
        "primary_gate_pass": bool(mirror >= MIRROR_GATE),
        "aggregate": {
            "position_mirror_gate": MIRROR_GATE,
            "position_mirror_agreement": mirror,
            "position_mismatch_bars": mismatch,
            "entry_events": int(entry_count),
            "blocked_formal_trend_entry_bars": int(blocked_count),
            "mean_pair_flat_share": float(np.mean([v["v31"]["occupancy"]["flat_share"] for v in pairs.values()])),
        },
        "pairs": pairs,
        "boundary": "Semantic lifecycle diagnostic only. No return, Sharpe, drawdown, hit-rate, cost, sizing, stop, target, or Strategy Tester metric is computed.",
    }


def _pct(x: float) -> str:
    return f"{100.0*x:.2f}%"


def render_markdown(r: dict[str, Any]) -> str:
    a = r["aggregate"]
    lines = [
        "# Issue #68 Phase B3.1 — Entry / Hold Separation Semantic Diagnostic", "",
        "Status: **burned development evidence / no PnL**", "",
        f"Primary reciprocal gate: **{'PASS' if r['primary_gate_pass'] else 'FAIL'}**",
        f"- v3.1 desired-position mirror: **{_pct(a['position_mirror_agreement'])}**",
        f"- preregistered gate: **>= {_pct(a['position_mirror_gate'])}**",
        f"- total entry events: **{a['entry_events']}**",
        f"- Formal 2/5 bars blocked from new entry because strong stage was not aligned: **{a['blocked_formal_trend_entry_bars']}**",
        f"- mean pair flat share: **{_pct(a['mean_pair_flat_share'])}**", "",
        "## Per pair", "",
        "| Pair | Formal mirror | Strong-stage mirror | v3.1 position mirror | Flat | Median hold | Entries L/S | Blocked L/S |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, p in r["pairs"].items():
        e = p["v31"]["event_counts"]
        lines.append(
            f"| {name} | {_pct(p['formal_stage_mirror']['mirror_agreement'])} | {_pct(p['strong_stage_mirror']['mirror_agreement'])} | "
            f"{_pct(p['v31_position_mirror']['mirror_agreement'])} | {_pct(p['v31']['occupancy']['flat_share'])} | "
            f"{p['v31']['holding']['median_bars']} | {e['enter_long']}/{e['enter_short']} | {e['blocked_long_entry']}/{e['blocked_short_entry']} |"
        )
    lines += ["", "## Boundary", "", r["boundary"], ""]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, default=HERE / "reports/issue-68-phase-b31-entry-hold.json")
    ap.add_argument("--md", type=Path, default=HERE / "reports/issue-68-phase-b31-entry-hold.md")
    args = ap.parse_args()
    report = build_report()
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    args.md.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["aggregate"], indent=2, sort_keys=True))
    if not report["primary_gate_pass"]:
        raise SystemExit("Issue #68 B3.1 reciprocal gate failed")


if __name__ == "__main__":
    main()
