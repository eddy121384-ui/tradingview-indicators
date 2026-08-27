#!/usr/bin/env python3
"""Issue #68 Phase B3.2 range-grace semantic diagnostic. No PnL."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import diagnose_issue66_reciprocal_symmetry as phasea
from generate_issue66_phase_c2_stage14_conflict_core import load_phase_c2_namespace
from issue68_lifecycle_v3_regime_first import holding_durations as v3_holding_durations, lifecycle_v3_regime_first
from issue68_lifecycle_v32_range_grace import holding_durations as v32_holding_durations, lifecycle_v32_range_grace

HERE = Path(__file__).resolve().parent
POSITION_MIRROR_GATE = 0.99


def _arr_float(model: pd.DataFrame, key: str) -> np.ndarray:
    return pd.to_numeric(model[key], errors="coerce").to_numpy(float)


def _arr_int(model: pd.DataFrame, key: str) -> np.ndarray:
    return np.nan_to_num(_arr_float(model, key), nan=0.0).astype(int)


def _compute(frame: pd.DataFrame):
    ns = load_phase_c2_namespace()
    cfg = ns["PriceOnlyConfig"]()
    model = ns["compute_price_only"](frame.copy(), cfg)
    return model, cfg


def _occupancy(position: np.ndarray, warmup: int) -> dict[str, float | int]:
    x = np.asarray(position, dtype=int)[warmup:]
    n = len(x)
    return {
        "bars": int(n),
        "flat_bars": int(np.sum(x == 0)),
        "long_bars": int(np.sum(x == 1)),
        "short_bars": int(np.sum(x == -1)),
        "flat_share": float(np.mean(x == 0)) if n else 1.0,
        "long_share": float(np.mean(x == 1)) if n else 0.0,
        "short_share": float(np.mean(x == -1)) if n else 0.0,
    }


def _holding(position: np.ndarray, warmup: int, fn) -> dict[str, float | int | None]:
    d = fn(position, start=warmup)
    if not d:
        return {"episodes": 0, "median_bars": None, "mean_bars": None, "max_bars": None}
    a = np.asarray(d, dtype=float)
    return {
        "episodes": int(len(d)),
        "median_bars": float(np.median(a)),
        "mean_bars": float(np.mean(a)),
        "max_bars": int(np.max(a)),
    }


def _position_mirror(a: np.ndarray, b: np.ndarray, warmup: int) -> dict[str, float | int]:
    x = np.asarray(a, dtype=int)[warmup:]
    y = np.asarray(b, dtype=int)[warmup:]
    good = x == -y
    return {
        "bars": int(len(x)),
        "mirror_agreement": float(np.mean(good)) if len(x) else 1.0,
        "mismatch_bars": int(np.sum(~good)),
    }


def _event_counts(events: dict[str, np.ndarray], warmup: int) -> dict[str, int]:
    return {k: int(np.sum(v[warmup:])) for k, v in events.items()}


def _v3_immediate_range_exits(formal: np.ndarray, position: np.ndarray, warmup: int) -> int:
    pos = np.asarray(position, dtype=int)
    prev = np.roll(pos, 1)
    prev[0] = 0
    mask = (
        (np.arange(len(pos)) >= warmup)
        & (prev != 0)
        & np.isin(np.asarray(formal, dtype=int), [1, 4])
        & (pos == 0)
    )
    return int(np.sum(mask))


def analyze_pair(frame: pd.DataFrame) -> dict[str, Any]:
    inv = phasea.reciprocal_ohlc(frame)
    model, cfg = _compute(frame)
    inv_model, inv_cfg = _compute(inv)
    warmup = int(cfg.rank_len - 1)
    if int(inv_cfg.rank_len - 1) != warmup:
        raise AssertionError("warmup mismatch")

    formal = _arr_int(model, "formal_id")
    inv_formal = _arr_int(inv_model, "formal_id")
    v3 = lifecycle_v3_regime_first(formal, warmup=warmup)
    v32 = lifecycle_v32_range_grace(formal, warmup=warmup, confirm_bars=int(cfg.confirm_bars))
    inv_v32 = lifecycle_v32_range_grace(inv_formal, warmup=warmup, confirm_bars=int(cfg.confirm_bars))

    return {
        "rows": int(len(frame)),
        "warmup_bars": warmup,
        "confirm_bars": int(cfg.confirm_bars),
        "formal_stage_mirror": phasea.stage_metrics(formal, inv_formal, warmup),
        "v32_position_mirror": _position_mirror(v32.position, inv_v32.position, warmup),
        "v3": {
            "occupancy": _occupancy(v3.position, warmup),
            "holding": _holding(v3.position, warmup, v3_holding_durations),
            "immediate_stage14_exit_bars": _v3_immediate_range_exits(formal, v3.position, warmup),
        },
        "v32": {
            "occupancy": _occupancy(v32.position, warmup),
            "holding": _holding(v32.position, warmup, v32_holding_durations),
            "event_counts": _event_counts(v32.events, warmup),
            "max_range_grace_bars": int(np.max(v32.range_grace_bars[warmup:])) if len(v32.range_grace_bars[warmup:]) else 0,
        },
    }


def build_report() -> dict[str, Any]:
    pairs = {name: analyze_pair(frame) for name, frame in phasea.load_frozen_pairs().items()}
    bars = sum(int(v["v32_position_mirror"]["bars"]) for v in pairs.values())
    mismatch = sum(int(v["v32_position_mirror"]["mismatch_bars"]) for v in pairs.values())
    mirror = 1.0 if bars == 0 else 1.0 - mismatch / bars

    scored = list(pairs.values())
    v3_flat = float(np.mean([p["v3"]["occupancy"]["flat_share"] for p in scored]))
    v32_flat = float(np.mean([p["v32"]["occupancy"]["flat_share"] for p in scored]))
    v3_medians = [p["v3"]["holding"]["median_bars"] for p in scored if p["v3"]["holding"]["median_bars"] is not None]
    v32_medians = [p["v32"]["holding"]["median_bars"] for p in scored if p["v32"]["holding"]["median_bars"] is not None]
    immediate = sum(int(p["v3"]["immediate_stage14_exit_bars"]) for p in scored)
    grace_exits = sum(
        int(p["v32"]["event_counts"]["range_grace_exit_long"]) + int(p["v32"]["event_counts"]["range_grace_exit_short"])
        for p in scored
    )

    return {
        "schema_version": 1,
        "issue": 68,
        "phase": "B3.2",
        "status": "RANGE_GRACE_HOLD_DIAGNOSTIC_NO_PNL",
        "primary_gate_pass": bool(mirror >= POSITION_MIRROR_GATE),
        "aggregate": {
            "v32_position_mirror_gate": POSITION_MIRROR_GATE,
            "v32_position_mirror_agreement": mirror,
            "v32_position_mismatch_bars": mismatch,
            "mean_pair_flat_share_v3": v3_flat,
            "mean_pair_flat_share_v32": v32_flat,
            "median_of_pair_median_holding_v3": float(np.median(v3_medians)) if v3_medians else None,
            "median_of_pair_median_holding_v32": float(np.median(v32_medians)) if v32_medians else None,
            "v3_immediate_stage14_exit_bars": immediate,
            "v32_confirmed_range_grace_exits": grace_exits,
            "stage14_washout_exits_suppressed": immediate - grace_exits,
        },
        "pairs": pairs,
        "boundary": "Semantic lifecycle diagnostic only. No return, PnL, Sharpe, drawdown, hit-rate, cost, sizing, stop, target, or Strategy Tester metric is computed.",
    }


def _pct(x: float) -> str:
    return f"{100.0*x:.2f}%"


def render_markdown(r: dict[str, Any]) -> str:
    a = r["aggregate"]
    lines = [
        "# Issue #68 Phase B3.2 — Range-Grace Hold Semantic Diagnostic",
        "",
        "Status: **burned development evidence / no PnL**",
        "",
        f"Primary reciprocal gate: **{'PASS' if r['primary_gate_pass'] else 'FAIL'}**",
        f"- v3.2 desired-position mirror: **{_pct(a['v32_position_mirror_agreement'])}**",
        f"- preregistered gate: **>= {_pct(a['v32_position_mirror_gate'])}**",
        f"- v3 immediate Stage1/4 exits: **{a['v3_immediate_stage14_exit_bars']}**",
        f"- v3.2 confirmed range-grace exits: **{a['v32_confirmed_range_grace_exits']}**",
        f"- Stage1/4 washout exits suppressed: **{a['stage14_washout_exits_suppressed']}**",
        f"- mean pair flat share: **{_pct(a['mean_pair_flat_share_v3'])} v3 -> {_pct(a['mean_pair_flat_share_v32'])} v3.2**",
        f"- median of pair median-holds: **{a['median_of_pair_median_holding_v3']} -> {a['median_of_pair_median_holding_v32']} bars**",
        "",
        "## Per pair",
        "",
        "| Pair | Formal mirror | v3.2 position mirror | v3 Flat | v3.2 Flat | v3 median hold | v3.2 median hold | v3 immediate range exits | v3.2 grace exits |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, p in r["pairs"].items():
        grace_exits = p["v32"]["event_counts"]["range_grace_exit_long"] + p["v32"]["event_counts"]["range_grace_exit_short"]
        lines.append(
            f"| {name} | {_pct(p['formal_stage_mirror']['mirror_agreement'])} | {_pct(p['v32_position_mirror']['mirror_agreement'])} | "
            f"{_pct(p['v3']['occupancy']['flat_share'])} | {_pct(p['v32']['occupancy']['flat_share'])} | "
            f"{p['v3']['holding']['median_bars']} | {p['v32']['holding']['median_bars']} | "
            f"{p['v3']['immediate_stage14_exit_bars']} | {grace_exits} |"
        )
    lines += ["", "## Boundary", "", r["boundary"], ""]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, default=HERE / "reports/issue-68-phase-b32-range-grace.json")
    ap.add_argument("--md", type=Path, default=HERE / "reports/issue-68-phase-b32-range-grace.md")
    args = ap.parse_args()
    report = build_report()
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    args.md.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["aggregate"], indent=2, sort_keys=True))
    if not report["primary_gate_pass"]:
        raise SystemExit("Issue #68 B3.2 reciprocal gate failed")


if __name__ == "__main__":
    main()
