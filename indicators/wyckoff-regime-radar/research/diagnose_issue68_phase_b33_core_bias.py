#!/usr/bin/env python3
"""Issue #68 Phase B3.3 core-bias semantic diagnostic. No PnL."""
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
from issue68_lifecycle_v3_regime_first import lifecycle_v3_regime_first

HERE = Path(__file__).resolve().parent
BIAS_MIRROR_GATE = 0.99


def _arr_float(model: pd.DataFrame, key: str) -> np.ndarray:
    return pd.to_numeric(model[key], errors="coerce").to_numpy(float)


def _arr_int(model: pd.DataFrame, key: str) -> np.ndarray:
    return np.nan_to_num(_arr_float(model, key), nan=0.0).astype(int)


def _compute(frame: pd.DataFrame):
    ns = load_phase_c2_namespace()
    cfg = ns["PriceOnlyConfig"]()
    return ns["compute_price_only"](frame.copy(), cfg), cfg


def _mirror(a: np.ndarray, b: np.ndarray, warmup: int) -> dict[str, float | int]:
    x = np.asarray(a, dtype=int)[warmup:]
    y = np.asarray(b, dtype=int)[warmup:]
    good = x == -y
    return {
        "bars": int(len(x)),
        "mirror_agreement": float(np.mean(good)) if len(x) else 1.0,
        "mismatch_bars": int(np.sum(~good)),
    }


def _transitions(values: np.ndarray, warmup: int) -> int:
    x = np.asarray(values, dtype=int)[warmup:]
    if len(x) <= 1:
        return 0
    return int(np.sum(x[1:] != x[:-1]))


def _nonzero_episodes(values: np.ndarray, warmup: int) -> int:
    x = np.asarray(values, dtype=int)[warmup:]
    if not len(x):
        return 0
    starts = (x != 0) & np.r_[True, x[1:] != x[:-1]]
    return int(np.sum(starts))


def analyze_pair(frame: pd.DataFrame) -> dict[str, Any]:
    inv = phasea.reciprocal_ohlc(frame)
    model, cfg = _compute(frame)
    inv_model, inv_cfg = _compute(inv)
    warmup = int(cfg.rank_len - 1)
    if int(inv_cfg.rank_len - 1) != warmup:
        raise AssertionError("warmup mismatch")

    formal = _arr_int(model, "formal_id")
    inv_formal = _arr_int(inv_model, "formal_id")
    b3 = lifecycle_v3_regime_first(formal, warmup=warmup)
    bias = core_bias_v33(formal, warmup=warmup)
    inv_bias = core_bias_v33(inv_formal, warmup=warmup)
    scored_bias = bias.bias[warmup:]

    return {
        "formal_stage_mirror": phasea.stage_metrics(formal, inv_formal, warmup),
        "core_bias_mirror": _mirror(bias.bias, inv_bias.bias, warmup),
        "core_bias_unknown_share": float(np.mean(scored_bias == 0)) if len(scored_bias) else 1.0,
        "core_bias_transitions": _transitions(bias.bias, warmup),
        "core_bias_flip_events": int(np.sum(bias.events["flip_bull_to_bear"][warmup:]) + np.sum(bias.events["flip_bear_to_bull"][warmup:])),
        "b3_position_transitions": _transitions(b3.position, warmup),
        "b3_nonzero_episodes": _nonzero_episodes(b3.position, warmup),
    }


def build_report() -> dict[str, Any]:
    pairs = {name: analyze_pair(frame) for name, frame in phasea.load_frozen_pairs().items()}
    bars = sum(int(p["core_bias_mirror"]["bars"]) for p in pairs.values())
    mismatches = sum(int(p["core_bias_mirror"]["mismatch_bars"]) for p in pairs.values())
    mirror = 1.0 if bars == 0 else 1.0 - mismatches / bars
    b3_transitions = sum(int(p["b3_position_transitions"]) for p in pairs.values())
    bias_transitions = sum(int(p["core_bias_transitions"]) for p in pairs.values())

    return {
        "schema_version": 1,
        "issue": 68,
        "phase": "B3.3",
        "status": "CORE_BIAS_MEMORY_DIAGNOSTIC_NO_PNL_NOT_EXPOSURE",
        "primary_gate_pass": bool(mirror >= BIAS_MIRROR_GATE),
        "aggregate": {
            "core_bias_mirror_gate": BIAS_MIRROR_GATE,
            "core_bias_mirror_agreement": mirror,
            "core_bias_mismatch_bars": mismatches,
            "b3_position_transitions": b3_transitions,
            "core_bias_transitions": bias_transitions,
            "transition_churn_reduction": b3_transitions - bias_transitions,
            "mean_pair_unknown_bias_share": float(np.mean([p["core_bias_unknown_share"] for p in pairs.values()])),
        },
        "pairs": pairs,
        "boundary": "Core bias is regime memory, not executable exposure. No return, PnL, Sharpe, drawdown, hit-rate, cost, sizing, stop, target, or Strategy Tester metric is computed.",
    }


def _pct(x: float) -> str:
    return f"{100.0*x:.2f}%"


def render_markdown(r: dict[str, Any]) -> str:
    a = r["aggregate"]
    lines = [
        "# Issue #68 Phase B3.3 — Core Bias Memory Semantic Diagnostic",
        "",
        "Status: **burned development evidence / no PnL / bias is not exposure**",
        "",
        f"Primary reciprocal gate: **{'PASS' if r['primary_gate_pass'] else 'FAIL'}**",
        f"- core-bias mirror: **{_pct(a['core_bias_mirror_agreement'])}**",
        f"- preregistered gate: **>= {_pct(a['core_bias_mirror_gate'])}**",
        f"- B3 position transitions: **{a['b3_position_transitions']}**",
        f"- B3.3 core-bias transitions: **{a['core_bias_transitions']}**",
        f"- transition churn removed from the memory layer: **{a['transition_churn_reduction']}**",
        f"- mean pair unknown-bias share: **{_pct(a['mean_pair_unknown_bias_share'])}**",
        "",
        "## Per pair",
        "",
        "| Pair | Formal mirror | Bias mirror | Unknown bias | B3 position transitions | Bias transitions | B3 episodes |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, p in r["pairs"].items():
        lines.append(
            f"| {name} | {_pct(p['formal_stage_mirror']['mirror_agreement'])} | {_pct(p['core_bias_mirror']['mirror_agreement'])} | "
            f"{_pct(p['core_bias_unknown_share'])} | {p['b3_position_transitions']} | {p['core_bias_transitions']} | {p['b3_nonzero_episodes']} |"
        )
    lines += ["", "## Boundary", "", r["boundary"], ""]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, default=HERE / "reports/issue-68-phase-b33-core-bias.json")
    ap.add_argument("--md", type=Path, default=HERE / "reports/issue-68-phase-b33-core-bias.md")
    args = ap.parse_args()
    report = build_report()
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    args.md.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["aggregate"], indent=2, sort_keys=True))
    if not report["primary_gate_pass"]:
        raise SystemExit("Issue #68 B3.3 reciprocal gate failed")


if __name__ == "__main__":
    main()
