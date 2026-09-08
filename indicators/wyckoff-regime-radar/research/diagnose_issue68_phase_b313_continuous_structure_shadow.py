#!/usr/bin/env python3
"""Issue #68 B3.13 continuous Structure shadow audit. Diagnostic only."""
from __future__ import annotations

import argparse
import json
import sys
import types
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import diagnose_issue66_reciprocal_symmetry as phasea
import diagnose_issue68_phase_b38_raw_feature_attribution as b38
import diagnose_issue68_phase_b310_s5_vs_s2_local_duel as b310

HERE = Path(__file__).resolve().parent
GATE = 0.99
TOL = 1e-9
ANCHOR = b38.INSTRUMENT_ANCHOR
B313_INSERT = '''        "b313_dist_rank": dist_rank,
        "b313_maturity_dist_rank": maturity_dist_rank,
'''


def load_namespace() -> dict[str, object]:
    source = b38.render_phase_c2_source()
    if source.count(ANCHOR) != 1:
        raise RuntimeError(f"expected one diagnostic anchor; found {source.count(ANCHOR)}")
    source = source.replace(ANCHOR, b38.INSTRUMENT_INSERT + B313_INSERT + ANCHOR, 1)
    name = "wyckoff_issue68_b313_instrumented_c2"
    module = types.ModuleType(name)
    module.__file__ = str(HERE / "generated" / "wyckoff-issue68-b313-instrumented-c2.py")
    module.__package__ = None
    sys.modules[name] = module
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    return module.__dict__


def compute(frame: pd.DataFrame):
    ns = load_namespace()
    cfg = ns["PriceOnlyConfig"]()
    return ns["compute_price_only"](frame.copy(), cfg), cfg


def f(model: pd.DataFrame, key: str) -> np.ndarray:
    return pd.to_numeric(model[key], errors="coerce").to_numpy(float)


def continuous_structure_edge(model: pd.DataFrame) -> np.ndarray:
    delta = (f(model, "b313_dist_rank") - 50.0) + (f(model, "b313_maturity_dist_rank") - 50.0)
    return 0.17 * delta


def transitions(target_side: np.ndarray, scored: np.ndarray) -> int:
    if len(target_side) < 2:
        return 0
    valid = scored[1:] & scored[:-1]
    return int(np.sum(valid & (target_side[1:] != target_side[:-1])))


def stable_lead_within_original_loss_run(
    original_oriented: np.ndarray,
    shadow_oriented: np.ndarray,
    scored: np.ndarray,
    handoff_index: int,
    warmup: int,
) -> int | None:
    t = handoff_index
    if not scored[t] or not np.isfinite(shadow_oriented[t]) or shadow_oriented[t] <= 0.0:
        return None
    start = t - 1
    while start - 1 >= warmup and scored[start - 1] and original_oriented[start - 1] <= 0.0:
        start -= 1
    lead = 0
    j = t - 1
    while j >= start and scored[j] and shadow_oriented[j] > 0.0:
        lead += 1
        j -= 1
    return lead


def stats(values: list[int]) -> dict[str, float | int | None]:
    a = np.asarray(values, dtype=float)
    if len(a) == 0:
        return {"n": 0, "median": None, "p90": None, "max": None}
    return {
        "n": int(len(a)),
        "median": float(np.median(a)),
        "p90": float(np.percentile(a, 90)),
        "max": float(np.max(a)),
    }


def audit_direction(model: pd.DataFrame, direction: int, warmup: int) -> dict[str, Any]:
    fresh = b38.fresh_pair_components(model)
    arrays = fresh["arrays"]
    duel = b310.direction_duel_from_arrays(arrays, direction, warmup)
    handoff = duel["_arrays"]["handoff"]
    old_structure = np.asarray(arrays["structure"], dtype=float)
    old_direct = np.asarray(arrays["direct"], dtype=float)
    new_structure = continuous_structure_edge(model)
    shadow_direct = old_direct - old_structure + new_structure

    finite = (
        np.isfinite(old_direct)
        & np.isfinite(old_structure)
        & np.isfinite(new_structure)
        & np.isfinite(shadow_direct)
    )
    scored = finite.copy()
    scored[:warmup] = False

    old_o = direction * old_direct
    shadow_o = direction * shadow_direct
    old_struct_o = direction * old_structure
    new_struct_o = direction * new_structure
    old_side = old_o > 0.0
    shadow_side = shadow_o > 0.0

    hs = np.flatnonzero(handoff & scored)
    leads: list[int] = []
    already_prev = 0
    positive_at_handoff = 0
    delayed_at_handoff = 0
    accounted = 0
    for t in hs:
        if t <= warmup:
            continue
        accounted += 1
        already_prev += int(scored[t - 1] and shadow_o[t - 1] > 0.0)
        if shadow_o[t] > 0.0:
            positive_at_handoff += 1
        else:
            delayed_at_handoff += 1
        lead = stable_lead_within_original_loss_run(old_o, shadow_o, scored, int(t), warmup)
        if lead is not None:
            leads.append(lead)

    shadow_entry = np.zeros(len(shadow_side), dtype=bool)
    if len(shadow_side) > 1:
        shadow_entry[1:] = scored[1:] & scored[:-1] & shadow_side[1:] & ~shadow_side[:-1]
    shadow_only_entries = int(np.sum(shadow_entry & ~handoff))

    recon = np.asarray(arrays["reconstructed"], dtype=float)
    direct = np.asarray(arrays["direct"], dtype=float)
    recon_finite = np.isfinite(recon) & np.isfinite(direct)
    recon_error = float(np.nanmax(np.abs(recon[recon_finite] - direct[recon_finite]))) if np.any(recon_finite) else 0.0

    return {
        "direction": "bull_s5_to_s2" if direction == 1 else "bear_s2_to_s5",
        "usable_bars": int(np.sum(scored)),
        "original_handoffs": int(len(hs)),
        "handoff_accounted": accounted,
        "shadow_target_positive_t_minus_1": already_prev,
        "shadow_target_positive_t_minus_1_share": already_prev / accounted if accounted else 0.0,
        "shadow_target_positive_at_handoff": positive_at_handoff,
        "shadow_target_positive_at_handoff_share": positive_at_handoff / accounted if accounted else 0.0,
        "shadow_delayed_at_original_handoff": delayed_at_handoff,
        "stable_lead_bars": stats(leads),
        "old_target_side_transitions": transitions(old_side, scored),
        "shadow_target_side_transitions": transitions(shadow_side, scored),
        "shadow_only_target_entries": shadow_only_entries,
        "max_old_reconstruction_error": recon_error,
        "_arrays": {
            "scored": scored,
            "handoff": handoff,
            "shadow_side": shadow_side,
            "continuous_structure_side": new_struct_o > 0.0,
            "old_structure_side": old_struct_o > 0.0,
        },
    }


def mirror_compare(a: dict[str, Any], b: dict[str, Any], warmup: int) -> dict[str, Any]:
    sa = a["_arrays"]["scored"][warmup:]
    sb = b["_arrays"]["scored"][warmup:]
    valid = sa & sb
    xa = a["_arrays"]["shadow_side"][warmup:]
    xb = b["_arrays"]["shadow_side"][warmup:]
    ca = a["_arrays"]["continuous_structure_side"][warmup:]
    cb = b["_arrays"]["continuous_structure_side"][warmup:]
    ha = a["_arrays"]["handoff"][warmup:]
    hb = b["_arrays"]["handoff"][warmup:]
    n = int(np.sum(valid))
    return {
        "bars": n,
        "shadow_target_side_agreement": float(np.mean(xa[valid] == xb[valid])) if n else 1.0,
        "continuous_structure_side_agreement": float(np.mean(ca[valid] == cb[valid])) if n else 1.0,
        "original_handoff_agreement": float(np.mean(ha[valid] == hb[valid])) if n else 1.0,
    }


def clean(x: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in x.items() if k != "_arrays"}


def analyze_pair(frame: pd.DataFrame) -> dict[str, Any]:
    inv = phasea.reciprocal_ohlc(frame)
    model, cfg = compute(frame)
    inv_model, inv_cfg = compute(inv)
    warmup = int(cfg.rank_len - 1)
    if warmup != int(inv_cfg.rank_len - 1):
        raise AssertionError("warmup mismatch")

    bull = audit_direction(model, 1, warmup)
    bear = audit_direction(model, -1, warmup)
    inv_bull = audit_direction(inv_model, 1, warmup)
    inv_bear = audit_direction(inv_model, -1, warmup)
    mirrors = {
        "bull_vs_inverse_bear": mirror_compare(bull, inv_bear, warmup),
        "bear_vs_inverse_bull": mirror_compare(bear, inv_bull, warmup),
    }
    return {
        "warmup": warmup,
        "bull": clean(bull),
        "bear": clean(bear),
        "mirror": mirrors,
    }


def build_report() -> dict[str, Any]:
    pairs = {name: analyze_pair(frame) for name, frame in phasea.load_frozen_pairs().items()}
    agg: dict[str, Any] = {
        "original_handoffs": 0,
        "handoff_accounted": 0,
        "shadow_target_positive_t_minus_1": 0,
        "shadow_target_positive_at_handoff": 0,
        "shadow_delayed_at_original_handoff": 0,
        "old_target_side_transitions": 0,
        "shadow_target_side_transitions": 0,
        "shadow_only_target_entries": 0,
        "max_old_reconstruction_error": 0.0,
        "minimum_shadow_target_side_mirror_agreement": 1.0,
        "minimum_continuous_structure_side_mirror_agreement": 1.0,
        "minimum_original_handoff_mirror_agreement": 1.0,
    }
    for p in pairs.values():
        for side in ("bull", "bear"):
            x = p[side]
            for key in (
                "original_handoffs",
                "handoff_accounted",
                "shadow_target_positive_t_minus_1",
                "shadow_target_positive_at_handoff",
                "shadow_delayed_at_original_handoff",
                "old_target_side_transitions",
                "shadow_target_side_transitions",
                "shadow_only_target_entries",
            ):
                agg[key] += int(x[key])
            agg["max_old_reconstruction_error"] = max(agg["max_old_reconstruction_error"], float(x["max_old_reconstruction_error"]))
        for m in p["mirror"].values():
            agg["minimum_shadow_target_side_mirror_agreement"] = min(
                agg["minimum_shadow_target_side_mirror_agreement"], m["shadow_target_side_agreement"]
            )
            agg["minimum_continuous_structure_side_mirror_agreement"] = min(
                agg["minimum_continuous_structure_side_mirror_agreement"], m["continuous_structure_side_agreement"]
            )
            agg["minimum_original_handoff_mirror_agreement"] = min(
                agg["minimum_original_handoff_mirror_agreement"], m["original_handoff_agreement"]
            )

    n = agg["handoff_accounted"]
    agg["shadow_target_positive_t_minus_1_share"] = agg["shadow_target_positive_t_minus_1"] / n if n else 0.0
    agg["shadow_target_positive_at_handoff_share"] = agg["shadow_target_positive_at_handoff"] / n if n else 0.0
    agg["transition_ratio_shadow_over_old"] = (
        agg["shadow_target_side_transitions"] / agg["old_target_side_transitions"]
        if agg["old_target_side_transitions"] else None
    )
    unexplained = agg["original_handoffs"] - agg["handoff_accounted"]
    agg["unexplained_handoff_accounting"] = unexplained

    primary = (
        agg["max_old_reconstruction_error"] <= TOL
        and unexplained == 0
        and agg["minimum_shadow_target_side_mirror_agreement"] >= GATE
        and agg["minimum_continuous_structure_side_mirror_agreement"] >= GATE
        and agg["minimum_original_handoff_mirror_agreement"] >= GATE
    )
    return {
        "issue": 68,
        "phase": "B3.13",
        "status": "CONTINUOUS_STRUCTURE_SHADOW_NO_PERFORMANCE",
        "primary_gate_pass": bool(primary),
        "aggregate": agg,
        "pairs": pairs,
        "boundary": "Single locked continuous Structure shadow only; C-2, weights, MA lengths, thresholds, lifecycle and performance rules are unchanged.",
    }


def render_markdown(r: dict[str, Any]) -> str:
    a = r["aggregate"]
    lines = [
        "# Issue #68 Phase B3.13 — Continuous Structure Shadow Audit",
        "",
        "Status: **diagnostic only / frozen C-2 / no performance use**",
        "",
        f"Primary engineering gate: **{'PASS' if r['primary_gate_pass'] else 'FAIL'}**",
        f"- anchored original raw handoffs: **{a['original_handoffs']}**",
        f"- shadow already target-positive at t-1: **{a['shadow_target_positive_t_minus_1']}** ({100*a['shadow_target_positive_t_minus_1_share']:.1f}%)",
        f"- shadow target-positive on original handoff bar: **{a['shadow_target_positive_at_handoff']}** ({100*a['shadow_target_positive_at_handoff_share']:.1f}%)",
        f"- shadow still delayed on original handoff bar: **{a['shadow_delayed_at_original_handoff']}**",
        f"- old target-side transitions: **{a['old_target_side_transitions']}**",
        f"- shadow target-side transitions: **{a['shadow_target_side_transitions']}**",
        f"- shadow/old transition ratio: **{a['transition_ratio_shadow_over_old']:.3f}**" if a["transition_ratio_shadow_over_old"] is not None else "- shadow/old transition ratio: n/a",
        f"- shadow-only target entries: **{a['shadow_only_target_entries']}**",
        f"- max old six-component reconstruction error: **{a['max_old_reconstruction_error']:.3e}**",
        f"- min reciprocal shadow target-side agreement: **{100*a['minimum_shadow_target_side_mirror_agreement']:.3f}%**",
        f"- min reciprocal continuous-Structure-side agreement: **{100*a['minimum_continuous_structure_side_mirror_agreement']:.3f}%**",
        f"- unexplained handoff accounting: **{a['unexplained_handoff_accounting']}**",
        "",
        "## Per-pair Bull diagnostic",
        "",
        "| Pair | Handoffs | Shadow + at t-1 | Shadow + at t | Old transitions | Shadow transitions | Stable lead median |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for pair, p in r["pairs"].items():
        b = p["bull"]
        med = b["stable_lead_bars"]["median"]
        med_text = "n/a" if med is None else f"{med:.1f}"
        lines.append(
            f"| {pair} | {b['original_handoffs']} | {b['shadow_target_positive_t_minus_1']} | {b['shadow_target_positive_at_handoff']} | {b['old_target_side_transitions']} | {b['shadow_target_side_transitions']} | {med_text} |"
        )
    lines += ["", "## Boundary", "", r["boundary"], ""]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-json", type=Path)
    ap.add_argument("--report-md", type=Path)
    args = ap.parse_args()
    report = build_report()
    if args.report_json:
        args.report_json.parent.mkdir(parents=True, exist_ok=True)
        args.report_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if args.report_md:
        args.report_md.parent.mkdir(parents=True, exist_ok=True)
        args.report_md.write_text(render_markdown(report), encoding="utf-8")
    print(render_markdown(report))
    raise SystemExit(0 if report["primary_gate_pass"] else 1)


if __name__ == "__main__":
    main()
