#!/usr/bin/env python3
"""Issue #68 Phase B3 regime-first semantic diagnostic.

No PnL. Compares rejected v2 and preregistered v3 only on lifecycle semantics,
occupancy, holding duration, events, and reciprocal symmetry.
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
from issue68_lifecycle_v2 import holding_durations as v2_holding_durations, lifecycle_v2
from issue68_lifecycle_v3_regime_first import holding_durations as v3_holding_durations, lifecycle_v3_regime_first

HERE = Path(__file__).resolve().parent
V3_POSITION_MIRROR_GATE = 0.99


def _arr_float(model: pd.DataFrame, key: str) -> np.ndarray:
    return pd.to_numeric(model[key], errors="coerce").to_numpy(float)


def _arr_bool(model: pd.DataFrame, key: str) -> np.ndarray:
    return np.nan_to_num(_arr_float(model, key), nan=0.0) > 0.5


def _arr_int(model: pd.DataFrame, key: str) -> np.ndarray:
    return np.nan_to_num(_arr_float(model, key), nan=0.0).astype(int)


def _compute(frame: pd.DataFrame):
    ns = load_phase_c2_namespace()
    cfg = ns["PriceOnlyConfig"]()
    model = ns["compute_price_only"](frame.copy(), cfg)
    return model, cfg


def _run(frame: pd.DataFrame):
    model, cfg = _compute(frame)
    warmup = int(cfg.rank_len - 1)
    formal = _arr_int(model, "formal_id")
    v2 = lifecycle_v2(
        formal,
        _arr_bool(model, "range_break_up"),
        _arr_bool(model, "range_break_dn"),
        pd.to_numeric(frame["close"], errors="coerce").to_numpy(float),
        _arr_float(model, "range_high_break"),
        _arr_float(model, "range_low_break"),
        warmup=warmup,
        confirm_bars=int(cfg.confirm_bars),
    )
    v3 = lifecycle_v3_regime_first(formal, warmup=warmup)
    return model, warmup, v2, v3


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


def analyze_pair(frame: pd.DataFrame) -> dict[str, Any]:
    inv = phasea.reciprocal_ohlc(frame)
    model, warmup, v2, v3 = _run(frame)
    inv_model, inv_warmup, _, inv_v3 = _run(inv)
    if warmup != inv_warmup:
        raise AssertionError("warmup mismatch")

    formal = _arr_int(model, "formal_id")
    inv_formal = _arr_int(inv_model, "formal_id")
    return {
        "rows": int(len(frame)),
        "warmup_bars": warmup,
        "formal_stage_mirror": phasea.stage_metrics(formal, inv_formal, warmup),
        "v3_position_mirror": _position_mirror(v3.position, inv_v3.position, warmup),
        "v2": {
            "occupancy": _occupancy(v2.position, warmup),
            "holding": _holding(v2.position, warmup, v2_holding_durations),
        },
        "v3": {
            "occupancy": _occupancy(v3.position, warmup),
            "holding": _holding(v3.position, warmup, v3_holding_durations),
            "event_counts": _event_counts(v3.events, warmup),
        },
    }


def build_report() -> dict[str, Any]:
    pairs = {name: analyze_pair(frame) for name, frame in phasea.load_frozen_pairs().items()}
    bars = sum(int(v["v3_position_mirror"]["bars"]) for v in pairs.values())
    mismatch = sum(int(v["v3_position_mirror"]["mismatch_bars"]) for v in pairs.values())
    mirror = 1.0 if bars == 0 else 1.0 - mismatch / bars

    scored = [v for v in pairs.values() if int(v["v3"]["occupancy"]["bars"]) > 0]
    v2_flat = float(np.mean([v["v2"]["occupancy"]["flat_share"] for v in scored])) if scored else 1.0
    v3_flat = float(np.mean([v["v3"]["occupancy"]["flat_share"] for v in scored])) if scored else 1.0
    v2_medians = [v["v2"]["holding"]["median_bars"] for v in scored if v["v2"]["holding"]["median_bars"] is not None]
    v3_medians = [v["v3"]["holding"]["median_bars"] for v in scored if v["v3"]["holding"]["median_bars"] is not None]

    return {
        "schema_version": 1,
        "issue": 68,
        "phase": "B3",
        "status": "REGIME_FIRST_V3_SEMANTIC_DIAGNOSTIC_NO_PNL",
        "primary_gate_pass": bool(mirror >= V3_POSITION_MIRROR_GATE),
        "aggregate": {
            "v3_position_mirror_gate": V3_POSITION_MIRROR_GATE,
            "v3_position_mirror_agreement": mirror,
            "v3_position_mismatch_bars": mismatch,
            "mean_pair_flat_share_v2": v2_flat,
            "mean_pair_flat_share_v3": v3_flat,
            "flat_share_change_v3_minus_v2": v3_flat - v2_flat,
            "median_of_pair_median_holding_v2": float(np.median(v2_medians)) if v2_medians else None,
            "median_of_pair_median_holding_v3": float(np.median(v3_medians)) if v3_medians else None,
        },
        "pairs": pairs,
        "boundary": "Semantic lifecycle diagnostic only. No return, Sharpe, drawdown, hit-rate, cost, sizing, stop, target, or Strategy Tester metric is computed.",
    }


def _pct(x: float) -> str:
    return f"{100.0*x:.2f}%"


def render_markdown(r: dict[str, Any]) -> str:
    a = r["aggregate"]
    lines = [
        "# Issue #68 Phase B3 — Regime-first v3 Semantic Diagnostic",
        "",
        "Status: **burned development evidence / no PnL**",
        "",
        f"Primary reciprocal gate: **{'PASS' if r['primary_gate_pass'] else 'FAIL'}**",
        f"- v3 desired-position mirror: **{_pct(a['v3_position_mirror_agreement'])}**",
        f"- preregistered gate: **>= {_pct(a['v3_position_mirror_gate'])}**",
        f"- mean pair flat share, rejected v2: **{_pct(a['mean_pair_flat_share_v2'])}**",
        f"- mean pair flat share, regime-first v3: **{_pct(a['mean_pair_flat_share_v3'])}**",
        f"- median of pair median-holds, v2: **{a['median_of_pair_median_holding_v2']} bars**",
        f"- median of pair median-holds, v3: **{a['median_of_pair_median_holding_v3']} bars**",
        "",
        "## Per pair",
        "",
        "| Pair | Formal mirror | v3 position mirror | v2 Flat | v3 Flat | v2 median hold | v3 median hold |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, p in r["pairs"].items():
        lines.append(
            f"| {name} | {_pct(p['formal_stage_mirror']['mirror_agreement'])} | "
            f"{_pct(p['v3_position_mirror']['mirror_agreement'])} | "
            f"{_pct(p['v2']['occupancy']['flat_share'])} | {_pct(p['v3']['occupancy']['flat_share'])} | "
            f"{p['v2']['holding']['median_bars']} | {p['v3']['holding']['median_bars']} |"
        )
    lines += [
        "",
        "## v3 event counts",
        "",
    ]
    for name, p in r["pairs"].items():
        lines.append(f"- **{name}**: `{p['v3']['event_counts']}`")
    lines += ["", "## Boundary", "", r["boundary"], ""]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, default=HERE / "reports/issue-68-phase-b3-regime-first.json")
    ap.add_argument("--md", type=Path, default=HERE / "reports/issue-68-phase-b3-regime-first.md")
    args = ap.parse_args()
    report = build_report()
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    args.md.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["aggregate"], indent=2, sort_keys=True))
    if not report["primary_gate_pass"]:
        raise SystemExit("Issue #68 B3 reciprocal gate failed")


if __name__ == "__main__":
    main()
