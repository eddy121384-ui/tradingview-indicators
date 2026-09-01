#!/usr/bin/env python3
"""Issue #68 B3.10 S5-vs-S2 local raw-formula duel. Diagnostic only."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import diagnose_issue66_reciprocal_symmetry as phasea
import diagnose_issue68_phase_b38_raw_feature_attribution as b38

HERE = Path(__file__).resolve().parent
COMPONENTS = tuple(b38.COMPONENT_WEIGHTS.keys())
RECON_TOL = 1e-9
MIRROR_GATE = 0.99


def _finite_components(arrays: dict[str, np.ndarray]) -> np.ndarray:
    matrix = np.column_stack([arrays[name] for name in COMPONENTS])
    return np.all(np.isfinite(matrix), axis=1) & np.isfinite(arrays["direct"])


def direction_duel_from_arrays(
    arrays: dict[str, np.ndarray], direction: int, warmup: int
) -> dict[str, Any]:
    """Orient the exact S2-S5 duel toward Bull(+1) or Bear(-1)."""
    if direction not in (1, -1):
        raise ValueError(direction)
    matrix = np.column_stack([np.asarray(arrays[name], dtype=float) for name in COMPONENTS])
    direct = np.asarray(arrays["direct"], dtype=float)
    finite = _finite_components(arrays)
    scored = finite.copy()
    scored[:warmup] = False

    oriented_matrix = direction * matrix
    oriented_direct = direction * direct
    target_loses = scored & (oriented_direct < 0.0)

    negative = oriented_matrix < 0.0
    neg_counts = {
        name: int(np.sum(target_loses & negative[:, i])) for i, name in enumerate(COMPONENTS)
    }
    loss_n = int(np.sum(target_loses))
    neg_share = {name: (neg_counts[name] / loss_n if loss_n else 0.0) for name in COMPONENTS}
    cumulative_negative = {
        name: float(np.sum(np.minimum(oriented_matrix[target_loses, i], 0.0))) if loss_n else 0.0
        for i, name in enumerate(COMPONENTS)
    }
    mean_edge = {
        name: float(np.mean(oriented_matrix[target_loses, i])) if loss_n else 0.0
        for i, name in enumerate(COMPONENTS)
    }
    median_edge = {
        name: float(np.median(oriented_matrix[target_loses, i])) if loss_n else 0.0
        for i, name in enumerate(COMPONENTS)
    }
    largest_negative_idx = np.argmin(oriented_matrix, axis=1)
    largest_negative_counts = {
        name: int(np.sum(target_loses & (largest_negative_idx == i))) for i, name in enumerate(COMPONENTS)
    }

    prev_scored = np.roll(scored, 1)
    prev_scored[0] = False
    prev_direct = np.roll(oriented_direct, 1)
    prev_direct[0] = np.nan
    handoff = scored & prev_scored & (prev_direct <= 0.0) & (oriented_direct > 0.0)
    handoff_idx = np.flatnonzero(handoff)

    final_blocker_counts = {name: 0 for name in COMPONENTS}
    driver_counts = {name: 0 for name in COMPONENTS}
    handoff_sign_counts = {
        name: {"positive": 0, "negative": 0, "zero": 0} for name in COMPONENTS
    }
    final_blocker_id = np.full(len(direct), -1, dtype=int)
    driver_id = np.full(len(direct), -1, dtype=int)
    for t in handoff_idx:
        prev_edges = oriented_matrix[t - 1]
        now_edges = oriented_matrix[t]
        change = now_edges - prev_edges
        blocker = int(np.argmin(prev_edges))
        driver = int(np.argmax(change))
        final_blocker_id[t] = blocker
        driver_id[t] = driver
        final_blocker_counts[COMPONENTS[blocker]] += 1
        driver_counts[COMPONENTS[driver]] += 1
        for i, name in enumerate(COMPONENTS):
            v = now_edges[i]
            key = "positive" if v > 0.0 else "negative" if v < 0.0 else "zero"
            handoff_sign_counts[name][key] += 1

    reconstructed = np.sum(matrix, axis=1)
    err = np.abs(reconstructed - direct)
    return {
        "direction": "bull_s5_to_s2" if direction == 1 else "bear_s2_to_s5",
        "usable_bars": int(np.sum(scored)),
        "target_losing_bars": loss_n,
        "negative_edge_counts": neg_counts,
        "negative_edge_share": neg_share,
        "cumulative_negative_edge": cumulative_negative,
        "mean_edge_on_target_loss": mean_edge,
        "median_edge_on_target_loss": median_edge,
        "largest_negative_component_counts": largest_negative_counts,
        "handoff_events": int(len(handoff_idx)),
        "final_blocker_counts": final_blocker_counts,
        "handoff_driver_counts": driver_counts,
        "component_sign_at_handoff": handoff_sign_counts,
        "max_reconstruction_error": float(np.nanmax(err[finite])) if np.any(finite) else 0.0,
        "_arrays": {
            "handoff": handoff,
            "final_blocker_id": final_blocker_id,
            "driver_id": driver_id,
        },
    }


def _mirror_event_compare(a: dict[str, Any], b: dict[str, Any], warmup: int) -> dict[str, Any]:
    ah = a["_arrays"]["handoff"][warmup:]
    bh = b["_arrays"]["handoff"][warmup:]
    event_agreement = float(np.mean(ah == bh)) if len(ah) else 1.0
    both = ah & bh
    af = a["_arrays"]["final_blocker_id"][warmup:]
    bf = b["_arrays"]["final_blocker_id"][warmup:]
    ad = a["_arrays"]["driver_id"][warmup:]
    bd = b["_arrays"]["driver_id"][warmup:]
    comparable = int(np.sum(both))
    blocker_agreement = float(np.mean(af[both] == bf[both])) if comparable else 1.0
    driver_agreement = float(np.mean(ad[both] == bd[both])) if comparable else 1.0
    return {
        "bars": int(len(ah)),
        "event_agreement": event_agreement,
        "event_mismatch_bars": int(np.sum(ah != bh)),
        "comparable_handoffs": comparable,
        "final_blocker_agreement": blocker_agreement,
        "handoff_driver_agreement": driver_agreement,
    }


def _strip_arrays(x: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in x.items() if k != "_arrays"}


def analyze_pair(frame: pd.DataFrame) -> dict[str, Any]:
    inv = phasea.reciprocal_ohlc(frame)
    model, cfg = b38._compute(frame)
    inv_model, inv_cfg = b38._compute(inv)
    warmup = int(cfg.rank_len - 1)
    if warmup != int(inv_cfg.rank_len - 1):
        raise AssertionError("warmup mismatch")

    fresh = b38.fresh_pair_components(model)
    inv_fresh = b38.fresh_pair_components(inv_model)
    bull = direction_duel_from_arrays(fresh["arrays"], 1, warmup)
    bear = direction_duel_from_arrays(fresh["arrays"], -1, warmup)
    inv_bull = direction_duel_from_arrays(inv_fresh["arrays"], 1, warmup)
    inv_bear = direction_duel_from_arrays(inv_fresh["arrays"], -1, warmup)

    mirror = {
        "bull_vs_inverse_bear": _mirror_event_compare(bull, inv_bear, warmup),
        "bear_vs_inverse_bull": _mirror_event_compare(bear, inv_bull, warmup),
    }
    return {
        "warmup": warmup,
        "bull": _strip_arrays(bull),
        "bear": _strip_arrays(bear),
        "inverse_bull": _strip_arrays(inv_bull),
        "inverse_bear": _strip_arrays(inv_bear),
        "mirror": mirror,
    }


def build_report() -> dict[str, Any]:
    pairs = {name: analyze_pair(frame) for name, frame in phasea.load_frozen_pairs().items()}
    agg = {
        "usable_direction_observations": 0,
        "target_losing_bars": 0,
        "handoff_events": 0,
        "negative_edge_counts": {name: 0 for name in COMPONENTS},
        "cumulative_negative_edge": {name: 0.0 for name in COMPONENTS},
        "largest_negative_component_counts": {name: 0 for name in COMPONENTS},
        "final_blocker_counts": {name: 0 for name in COMPONENTS},
        "handoff_driver_counts": {name: 0 for name in COMPONENTS},
        "max_reconstruction_error": 0.0,
        "minimum_event_mirror_agreement": 1.0,
        "minimum_final_blocker_mirror_agreement": 1.0,
        "minimum_handoff_driver_mirror_agreement": 1.0,
    }
    for p in pairs.values():
        for side in ("bull", "bear"):
            x = p[side]
            agg["usable_direction_observations"] += x["usable_bars"]
            agg["target_losing_bars"] += x["target_losing_bars"]
            agg["handoff_events"] += x["handoff_events"]
            agg["max_reconstruction_error"] = max(agg["max_reconstruction_error"], x["max_reconstruction_error"])
            for name in COMPONENTS:
                agg["negative_edge_counts"][name] += x["negative_edge_counts"][name]
                agg["cumulative_negative_edge"][name] += x["cumulative_negative_edge"][name]
                agg["largest_negative_component_counts"][name] += x["largest_negative_component_counts"][name]
                agg["final_blocker_counts"][name] += x["final_blocker_counts"][name]
                agg["handoff_driver_counts"][name] += x["handoff_driver_counts"][name]
        for m in p["mirror"].values():
            agg["minimum_event_mirror_agreement"] = min(agg["minimum_event_mirror_agreement"], m["event_agreement"])
            agg["minimum_final_blocker_mirror_agreement"] = min(agg["minimum_final_blocker_mirror_agreement"], m["final_blocker_agreement"])
            agg["minimum_handoff_driver_mirror_agreement"] = min(agg["minimum_handoff_driver_mirror_agreement"], m["handoff_driver_agreement"])

    loss = agg["target_losing_bars"]
    agg["negative_edge_share"] = {
        name: (agg["negative_edge_counts"][name] / loss if loss else 0.0) for name in COMPONENTS
    }
    primary = (
        agg["max_reconstruction_error"] <= RECON_TOL
        and agg["minimum_event_mirror_agreement"] >= MIRROR_GATE
        and agg["minimum_final_blocker_mirror_agreement"] >= MIRROR_GATE
        and agg["minimum_handoff_driver_mirror_agreement"] >= MIRROR_GATE
    )
    return {
        "schema_version": 1,
        "issue": 68,
        "phase": "B3.10",
        "status": "S5_VS_S2_LOCAL_FORMULA_DUEL_NO_PERFORMANCE",
        "primary_gate_pass": bool(primary),
        "aggregate": agg,
        "pairs": pairs,
        "boundary": "Exact frozen S2-vs-S5 raw duel attribution only; no model or performance rule is changed.",
    }


def render_markdown(r: dict[str, Any]) -> str:
    a = r["aggregate"]
    lines = [
        "# Issue #68 Phase B3.10 — S5 vs S2 Local Formula Duel",
        "",
        "Status: **diagnostic only / frozen C-2 / no performance use**",
        "",
        f"Primary engineering gate: **{'PASS' if r['primary_gate_pass'] else 'FAIL'}**",
        f"- target-losing direction observations: **{a['target_losing_bars']}**",
        f"- exact raw handoff events: **{a['handoff_events']}**",
        f"- max six-component reconstruction error: **{a['max_reconstruction_error']:.3e}**",
        f"- minimum reciprocal handoff-event agreement: **{100*a['minimum_event_mirror_agreement']:.3f}%**",
        f"- minimum reciprocal final-blocker agreement: **{100*a['minimum_final_blocker_mirror_agreement']:.3f}%**",
        f"- minimum reciprocal handoff-driver agreement: **{100*a['minimum_handoff_driver_mirror_agreement']:.3f}%**",
        "",
        "## Component drag while target fresh trend loses",
        "",
        "| Component | Negative-edge share | Cumulative negative edge | Largest-negative count |",
        "|---|---:|---:|---:|",
    ]
    for name in COMPONENTS:
        lines.append(
            f"| {name} | {100*a['negative_edge_share'][name]:.1f}% | {a['cumulative_negative_edge'][name]:.2f} | {a['largest_negative_component_counts'][name]} |"
        )
    lines += ["", "## Exact handoff attribution", "", "| Component | Final blocker | Handoff driver |", "|---|---:|---:|"]
    for name in COMPONENTS:
        lines.append(f"| {name} | {a['final_blocker_counts'][name]} | {a['handoff_driver_counts'][name]} |")
    lines += ["", "## Per-pair Bull handoffs", "", "| Pair | S5-leading bars | S5->S2 handoffs | Top final blocker | Top driver |", "|---|---:|---:|---|---|"]
    for pair, p in r["pairs"].items():
        b = p["bull"]
        blocker = max(b["final_blocker_counts"], key=b["final_blocker_counts"].get)
        driver = max(b["handoff_driver_counts"], key=b["handoff_driver_counts"].get)
        lines.append(f"| {pair} | {b['target_losing_bars']} | {b['handoff_events']} | {blocker} | {driver} |")
    lines += ["", "## Boundary", "", r["boundary"], ""]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path)
    ap.add_argument("--md", type=Path)
    args = ap.parse_args()
    report = build_report()
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.md:
        args.md.parent.mkdir(parents=True, exist_ok=True)
        args.md.write_text(render_markdown(report), encoding="utf-8")
    if not args.json and not args.md:
        print(render_markdown(report))
    return 0 if report["primary_gate_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
