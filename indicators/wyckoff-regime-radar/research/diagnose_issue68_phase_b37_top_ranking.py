#!/usr/bin/env python3
"""Issue #68 B3.7 TOP formation / ranking audit. No performance metrics."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import diagnose_issue66_reciprocal_symmetry as phasea
from generate_issue66_phase_c2_stage14_conflict_core import load_phase_c2_namespace

HERE = Path(__file__).resolve().parent
STAGES = ("acc", "markup", "reacc", "dist", "markdown", "redist")
TOP_REPRO_GATE = 0.999


def _compute(frame: pd.DataFrame):
    ns = load_phase_c2_namespace()
    cfg = ns["PriceOnlyConfig"]()
    return ns["compute_price_only"](frame.copy(), cfg), cfg


def _f(model: pd.DataFrame, key: str) -> np.ndarray:
    return pd.to_numeric(model[key], errors="coerce").to_numpy(float)


def _i(model: pd.DataFrame, key: str) -> np.ndarray:
    return np.nan_to_num(_f(model, key), nan=0.0).astype(int)


def _layer(model: pd.DataFrame, suffix: str) -> np.ndarray:
    keys = [f"{s}_{suffix}" for s in STAGES]
    missing = [k for k in keys if k not in model.columns]
    if missing:
        raise KeyError(f"missing C-2 diagnostic columns for {suffix}: {missing}; available={list(model.columns)}")
    return np.column_stack([_f(model, k) for k in keys])


def _raw_gate_eff(model: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    raw = _layer(model, "raw")
    gate = _layer(model, "gate")
    eff_keys = [f"{s}_eff" for s in STAGES]
    if all(k in model.columns for k in eff_keys):
        eff = np.column_stack([_f(model, k) for k in eff_keys])
    else:
        # Price-only C-2 forces Volume/MTF/Divergence witness multipliers off, so
        # effective score is exactly raw * gate. TOP reproduction below is the
        # hard check that this transport is faithful.
        eff = raw * gate
    return raw, gate, eff


def _bool_mirror(a: np.ndarray, b: np.ndarray, warmup: int) -> dict[str, float | int]:
    x = np.asarray(a, dtype=bool)[warmup:]
    y = np.asarray(b, dtype=bool)[warmup:]
    good = x == y
    return {
        "bars": int(len(x)),
        "mirror_agreement": float(np.mean(good)) if len(x) else 1.0,
        "mismatch_bars": int(np.sum(~good)),
    }


def _direction_indices(direction: int) -> tuple[list[int], list[int], int, int, list[int]]:
    if direction == 1:
        # 0-based: target Stage2/3, precursor Stage1, opposite-range Stage4, opposite trend Stage5/6.
        return [1, 2], [0, 3, 4, 5], 0, 3, [4, 5]
    if direction == -1:
        return [4, 5], [0, 1, 2, 3], 3, 0, [1, 2]
    raise ValueError(direction)


def direction_audit(model: pd.DataFrame, direction: int, warmup: int) -> dict[str, Any]:
    raw, gate, eff = _raw_gate_eff(model)
    top = _i(model, "top_id")
    target_idx, other_idx, precursor_idx, opp_range_idx, opp_trend_idx = _direction_indices(direction)

    finite = np.all(np.isfinite(raw), axis=1) & np.all(np.isfinite(gate), axis=1) & np.all(np.isfinite(eff), axis=1)
    usable = finite & (top >= 1) & (top <= 6)
    top_target = usable & np.isin(top, np.asarray(target_idx) + 1)

    target_raw = np.max(raw[:, target_idx], axis=1)
    other_raw = np.max(raw[:, other_idx], axis=1)
    target_eff = np.max(eff[:, target_idx], axis=1)
    other_eff = np.max(eff[:, other_idx], axis=1)

    loss = usable & ~top_target
    raw_loss = loss & (target_raw <= other_raw)
    gate_flip = loss & (target_raw > other_raw) & (target_eff <= other_eff)
    residual = loss & ~(raw_loss | gate_flip)

    # Effective competitor identities among non-target stages.
    other_eff_matrix = eff[:, other_idx]
    competitor_stage = np.asarray(other_idx, dtype=int)[np.argmax(other_eff_matrix, axis=1)] + 1
    precursor = loss & (competitor_stage == precursor_idx + 1)
    opp_range = loss & (competitor_stage == opp_range_idx + 1)
    opp_trend = loss & np.isin(competitor_stage, np.asarray(opp_trend_idx) + 1)
    competitor_other = loss & ~(precursor | opp_range | opp_trend)

    # Reproduce public TOP from the existing effective score vector.
    eff_top = np.argmax(eff, axis=1) + 1
    top_match = usable & (eff_top == top)

    scored = np.zeros(len(top), dtype=bool)
    scored[warmup:] = True
    scored &= usable
    loss_scored = scored & loss

    def n(mask: np.ndarray) -> int:
        return int(np.sum(mask & scored))

    top_bars = int(np.sum(scored))
    top_match_n = int(np.sum(top_match & scored))
    loss_n = int(np.sum(loss_scored))
    return {
        "direction": "bull" if direction == 1 else "bear",
        "usable_bars": top_bars,
        "top_reproduction_agreement": float(top_match_n / top_bars) if top_bars else 1.0,
        "target_top_bars": n(top_target),
        "target_top_loss_bars": loss_n,
        "raw_layer_loss": n(raw_loss),
        "gate_layer_flip": n(gate_flip),
        "unexplained_loss": n(residual),
        "competitor": {
            "precursor_range": n(precursor),
            "opposite_range": n(opp_range),
            "opposite_trend": n(opp_trend),
            "other": n(competitor_other),
            "stage_counts": {str(stage): int(np.sum(loss_scored & (competitor_stage == stage))) for stage in range(1, 7)},
        },
        "masks": {
            "loss": loss,
            "raw_layer_loss": raw_loss,
            "gate_layer_flip": gate_flip,
            "precursor": precursor,
            "opposite_range": opp_range,
            "opposite_trend": opp_trend,
        },
    }


def analyze_pair(frame: pd.DataFrame) -> dict[str, Any]:
    inv = phasea.reciprocal_ohlc(frame)
    model, cfg = _compute(frame)
    inv_model, inv_cfg = _compute(inv)
    warmup = int(cfg.rank_len - 1)
    if warmup != int(inv_cfg.rank_len - 1):
        raise AssertionError("warmup mismatch")

    bull = direction_audit(model, 1, warmup)
    bear = direction_audit(model, -1, warmup)
    inv_bull = direction_audit(inv_model, 1, warmup)
    inv_bear = direction_audit(inv_model, -1, warmup)

    mirror = {
        "bull_loss_vs_inverse_bear": _bool_mirror(bull["masks"]["loss"], inv_bear["masks"]["loss"], warmup),
        "bull_raw_loss_vs_inverse_bear": _bool_mirror(bull["masks"]["raw_layer_loss"], inv_bear["masks"]["raw_layer_loss"], warmup),
        "bull_gate_flip_vs_inverse_bear": _bool_mirror(bull["masks"]["gate_layer_flip"], inv_bear["masks"]["gate_layer_flip"], warmup),
        "bear_loss_vs_inverse_bull": _bool_mirror(bear["masks"]["loss"], inv_bull["masks"]["loss"], warmup),
    }

    # Keep masks out of persisted JSON.
    for x in (bull, bear):
        x.pop("masks", None)
    return {"warmup": warmup, "bull": bull, "bear": bear, "mirror": mirror}


def build_report() -> dict[str, Any]:
    pairs = {name: analyze_pair(frame) for name, frame in phasea.load_frozen_pairs().items()}
    agg = {
        "usable_bars": 0,
        "target_top_loss_bars": 0,
        "raw_layer_loss": 0,
        "gate_layer_flip": 0,
        "unexplained_loss": 0,
        "competitor_precursor_range": 0,
        "competitor_opposite_range": 0,
        "competitor_opposite_trend": 0,
        "competitor_other": 0,
    }
    top_repro_weighted_num = 0.0
    for p in pairs.values():
        for side in ("bull", "bear"):
            x = p[side]
            agg["usable_bars"] += int(x["usable_bars"])
            agg["target_top_loss_bars"] += int(x["target_top_loss_bars"])
            agg["raw_layer_loss"] += int(x["raw_layer_loss"])
            agg["gate_layer_flip"] += int(x["gate_layer_flip"])
            agg["unexplained_loss"] += int(x["unexplained_loss"])
            agg["competitor_precursor_range"] += int(x["competitor"]["precursor_range"])
            agg["competitor_opposite_range"] += int(x["competitor"]["opposite_range"])
            agg["competitor_opposite_trend"] += int(x["competitor"]["opposite_trend"])
            agg["competitor_other"] += int(x["competitor"]["other"])
            top_repro_weighted_num += float(x["top_reproduction_agreement"]) * int(x["usable_bars"])

    agg["top_reproduction_agreement"] = top_repro_weighted_num / agg["usable_bars"] if agg["usable_bars"] else 1.0
    loss = agg["target_top_loss_bars"]
    agg["raw_loss_share"] = float(agg["raw_layer_loss"] / loss) if loss else 0.0
    agg["gate_flip_share"] = float(agg["gate_layer_flip"] / loss) if loss else 0.0

    primary = agg["unexplained_loss"] == 0 and agg["top_reproduction_agreement"] >= TOP_REPRO_GATE
    return {
        "schema_version": 1,
        "issue": 68,
        "phase": "B3.7",
        "status": "TOP_FORMATION_RANKING_AUDIT_NO_PERFORMANCE",
        "primary_gate_pass": bool(primary),
        "aggregate": agg,
        "pairs": pairs,
        "boundary": "Ranking attribution only. No classifier threshold or strategy-performance metric is changed or optimized.",
    }


def render_markdown(r: dict[str, Any]) -> str:
    a = r["aggregate"]
    lines = [
        "# Issue #68 Phase B3.7 — TOP Formation / Ranking Audit",
        "",
        "Status: **diagnostic only / frozen C-2 / no performance use**",
        "",
        f"Primary engineering gate: **{'PASS' if r['primary_gate_pass'] else 'FAIL'}**",
        f"- effective-score TOP reproduction: **{100*a['top_reproduction_agreement']:.3f}%**",
        f"- target-family TOP-loss observations (bull+bear, four FX): **{a['target_top_loss_bars']}**",
        f"- RAW-layer loss: **{a['raw_layer_loss']} ({100*a['raw_loss_share']:.1f}%)**",
        f"- gate-layer flip: **{a['gate_layer_flip']} ({100*a['gate_flip_share']:.1f}%)**",
        f"- unexplained loss: **{a['unexplained_loss']}**",
        "",
        "## Effective-score competitor groups",
        "",
        f"- precursor range: **{a['competitor_precursor_range']}**",
        f"- opposite range: **{a['competitor_opposite_range']}**",
        f"- opposite trend: **{a['competitor_opposite_trend']}**",
        f"- other: **{a['competitor_other']}**",
        "",
        "## Per pair",
        "",
        "| Pair | Side | Loss bars | Raw loss | Gate flip | Precursor | Opp range | Opp trend | TOP repro |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, p in r["pairs"].items():
        for side in ("bull", "bear"):
            x = p[side]
            c = x["competitor"]
            lines.append(
                f"| {name} | {side} | {x['target_top_loss_bars']} | {x['raw_layer_loss']} | {x['gate_layer_flip']} | "
                f"{c['precursor_range']} | {c['opposite_range']} | {c['opposite_trend']} | {100*x['top_reproduction_agreement']:.2f}% |"
            )
    lines += ["", "## Boundary", "", r["boundary"], ""]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, default=HERE / "reports/issue-68-phase-b37-top-ranking.json")
    ap.add_argument("--md", type=Path, default=HERE / "reports/issue-68-phase-b37-top-ranking.md")
    args = ap.parse_args()
    report = build_report()
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    args.md.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["aggregate"], indent=2, sort_keys=True))
    if not report["primary_gate_pass"]:
        raise SystemExit("Issue #68 B3.7 ranking attribution failed")


if __name__ == "__main__":
    main()
