#!/usr/bin/env python3
"""Issue #68 B3.8 raw-feature attribution. Diagnostic only; no performance metrics."""
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
from generate_issue66_phase_c2_stage14_conflict_core import render_phase_c2_source

HERE = Path(__file__).resolve().parent
STAGES = ("acc", "markup", "reacc", "dist", "markdown", "redist")
INSTRUMENT_ANCHOR = '        "acc_raw": acc_raw,\n'
INSTRUMENT_INSERT = '''        "b38_acc_raw0": acc_raw0,
        "b38_markup_raw0": markup_raw0,
        "b38_reacc_raw0": reacc_raw0,
        "b38_dist_raw0": dist_raw0,
        "b38_markdown_raw0": markdown_raw0,
        "b38_redist_raw0": redist_raw0,
        "b38_markup_base_raw": markup_base_raw,
        "b38_markdown_base_raw": markdown_base_raw,
        "b38_acc_trace": acc_trace_for_markup,
        "b38_dist_trace": dist_trace_for_markdown,
        "b38_breakout": breakout_score,
        "b38_breakdown": explicit_breakdown_score,
        "b38_heat_up": heat_up,
        "b38_panic_dn": panic_heat_dn,
        "b38_structure_up": structure_strong,
        "b38_structure_dn": structure_weak,
        "b38_extension_up": markup_extension_score,
        "b38_extension_dn": markdown_extension_score,
        "b38_continuation_up": markup_continuation_score,
        "b38_continuation_dn": markdown_continuation_score,
'''
COMPONENT_WEIGHTS = {
    "break": 0.17,
    "heat": 0.17,
    "structure": 0.17,
    "extension": 0.2125,
    "continuation": 0.1275,
    "trace": 0.15,
}
RECON_TOL = 1e-9


def load_instrumented_namespace() -> dict[str, object]:
    source = render_phase_c2_source()
    if source.count(INSTRUMENT_ANCHOR) != 1:
        raise RuntimeError(f"expected one C-2 diagnostic anchor; found {source.count(INSTRUMENT_ANCHOR)}")
    source = source.replace(INSTRUMENT_ANCHOR, INSTRUMENT_INSERT + INSTRUMENT_ANCHOR, 1)
    module_name = "wyckoff_issue68_b38_instrumented_c2"
    module = types.ModuleType(module_name)
    module.__file__ = str(HERE / "generated" / "wyckoff-issue68-b38-instrumented-c2.py")
    module.__package__ = None
    sys.modules[module_name] = module
    exec(compile(source, module.__file__, "exec"), module.__dict__)
    return module.__dict__


def _compute(frame: pd.DataFrame):
    ns = load_instrumented_namespace()
    cfg = ns["PriceOnlyConfig"]()
    return ns["compute_price_only"](frame.copy(), cfg), cfg


def _f(model: pd.DataFrame, key: str) -> np.ndarray:
    return pd.to_numeric(model[key], errors="coerce").to_numpy(float)


def _raw_matrix(model: pd.DataFrame) -> np.ndarray:
    return np.column_stack([_f(model, f"{s}_raw") for s in STAGES])


def _direction_indices(direction: int) -> tuple[list[int], list[int], list[int], int, int]:
    if direction == 1:
        return [1, 2], [0, 3], [4, 5], 0, 3
    if direction == -1:
        return [4, 5], [0, 3], [1, 2], 3, 0
    raise ValueError(direction)


def direction_raw_audit(model: pd.DataFrame, direction: int, warmup: int) -> dict[str, Any]:
    raw = _raw_matrix(model)
    target_idx, range_idx, opp_idx, precursor_idx, opp_range_idx = _direction_indices(direction)
    finite = np.all(np.isfinite(raw), axis=1)
    scored = finite.copy()
    scored[:warmup] = False

    target_raw = np.max(raw[:, target_idx], axis=1)
    range_raw = np.max(raw[:, range_idx], axis=1)
    opp_raw = np.max(raw[:, opp_idx], axis=1)
    other_raw = np.maximum(range_raw, opp_raw)
    raw_adv = target_raw > other_raw
    loss = scored & ~raw_adv

    winner = np.argmax(raw, axis=1) + 1  # same strict first-stage tie priority as C-2.
    precursor = loss & (winner == precursor_idx + 1)
    opp_range = loss & (winner == opp_range_idx + 1)
    opp_trend = loss & np.isin(winner, np.asarray(opp_idx) + 1)
    unexplained = loss & ~(precursor | opp_range | opp_trend)

    target_choice = np.asarray(target_idx, dtype=int)[np.argmax(raw[:, target_idx], axis=1)] + 1

    def n(mask: np.ndarray) -> int:
        return int(np.sum(mask & scored))

    loss_n = int(np.sum(loss))
    return {
        "direction": "bull" if direction == 1 else "bear",
        "usable_bars": int(np.sum(scored)),
        "raw_adv_bars": int(np.sum(scored & raw_adv)),
        "raw_loss_bars": loss_n,
        "raw_loss_share": float(loss_n / np.sum(scored)) if np.sum(scored) else 0.0,
        "winner_group": {
            "precursor_range": n(precursor),
            "opposite_range": n(opp_range),
            "opposite_trend": n(opp_trend),
            "unexplained": n(unexplained),
            "stage_counts": {str(stage): int(np.sum(loss & (winner == stage))) for stage in range(1, 7)},
        },
        "target_substage_on_loss": {
            str(stage): int(np.sum(loss & (target_choice == stage))) for stage in (np.asarray(target_idx) + 1)
        },
        "masks": {
            "raw_adv": raw_adv,
            "loss": loss,
            "precursor": precursor,
            "opposite_range": opp_range,
            "opposite_trend": opp_trend,
        },
    }


def fresh_pair_components(model: pd.DataFrame) -> dict[str, Any]:
    components = {
        "break": COMPONENT_WEIGHTS["break"] * (_f(model, "b38_breakout") - _f(model, "b38_breakdown")),
        "heat": COMPONENT_WEIGHTS["heat"] * (_f(model, "b38_heat_up") - _f(model, "b38_panic_dn")),
        "structure": COMPONENT_WEIGHTS["structure"] * (_f(model, "b38_structure_up") - _f(model, "b38_structure_dn")),
        "extension": COMPONENT_WEIGHTS["extension"] * (_f(model, "b38_extension_up") - _f(model, "b38_extension_dn")),
        "continuation": COMPONENT_WEIGHTS["continuation"] * (_f(model, "b38_continuation_up") - _f(model, "b38_continuation_dn")),
        "trace": COMPONENT_WEIGHTS["trace"] * (_f(model, "b38_acc_trace") - _f(model, "b38_dist_trace")),
    }
    reconstructed = np.sum(np.column_stack(list(components.values())), axis=1)
    direct = _f(model, "b38_markup_raw0") - _f(model, "b38_markdown_raw0")
    finite = np.isfinite(reconstructed) & np.isfinite(direct)
    err = np.abs(reconstructed - direct)

    matrix = np.column_stack(list(components.values()))
    names = np.asarray(list(components.keys()), dtype=object)
    largest_negative_idx = np.argmin(matrix, axis=1)
    largest_negative_name = names[largest_negative_idx]
    markup_loses = finite & (direct < 0.0)
    drag_counts = {name: int(np.sum(markup_loses & (largest_negative_name == name))) for name in names}

    return {
        "finite_bars": int(np.sum(finite)),
        "max_abs_reconstruction_error": float(np.nanmax(err[finite])) if np.any(finite) else 0.0,
        "mean_abs_reconstruction_error": float(np.nanmean(err[finite])) if np.any(finite) else 0.0,
        "markup_raw0_below_markdown_raw0_bars": int(np.sum(markup_loses)),
        "largest_negative_component_counts": drag_counts,
        "component_delta_mean": {
            name: float(np.nanmean(values[finite])) if np.any(finite) else 0.0 for name, values in components.items()
        },
        "arrays": {**components, "direct": direct, "reconstructed": reconstructed},
    }


def _bool_mirror(a: np.ndarray, b: np.ndarray, warmup: int) -> dict[str, float | int]:
    x = np.asarray(a, dtype=bool)[warmup:]
    y = np.asarray(b, dtype=bool)[warmup:]
    good = x == y
    return {
        "bars": int(len(x)),
        "mirror_agreement": float(np.mean(good)) if len(x) else 1.0,
        "mismatch_bars": int(np.sum(~good)),
    }


def analyze_pair(frame: pd.DataFrame) -> dict[str, Any]:
    inverse = phasea.reciprocal_ohlc(frame)
    model, cfg = _compute(frame)
    inv_model, inv_cfg = _compute(inverse)
    warmup = int(cfg.rank_len - 1)
    if warmup != int(inv_cfg.rank_len - 1):
        raise AssertionError("warmup mismatch")

    bull = direction_raw_audit(model, 1, warmup)
    bear = direction_raw_audit(model, -1, warmup)
    inv_bull = direction_raw_audit(inv_model, 1, warmup)
    inv_bear = direction_raw_audit(inv_model, -1, warmup)
    fresh = fresh_pair_components(model)
    inv_fresh = fresh_pair_components(inv_model)

    mirror = {
        "bull_raw_adv_vs_inverse_bear": _bool_mirror(bull["masks"]["raw_adv"], inv_bear["masks"]["raw_adv"], warmup),
        "bull_loss_vs_inverse_bear": _bool_mirror(bull["masks"]["loss"], inv_bear["masks"]["loss"], warmup),
        "bear_raw_adv_vs_inverse_bull": _bool_mirror(bear["masks"]["raw_adv"], inv_bull["masks"]["raw_adv"], warmup),
    }

    # Stage2-vs-Stage5 mirrored component deltas should negate under reciprocal quotation.
    component_mirror = {}
    for name in COMPONENT_WEIGHTS:
        a = fresh["arrays"][name][warmup:]
        b = inv_fresh["arrays"][name][warmup:]
        finite = np.isfinite(a) & np.isfinite(b)
        component_mirror[name] = {
            "bars": int(np.sum(finite)),
            "mae_to_negative_inverse": float(np.mean(np.abs(a[finite] + b[finite]))) if np.any(finite) else 0.0,
        }

    for x in (bull, bear):
        x.pop("masks", None)
    fresh.pop("arrays", None)
    inv_fresh.pop("arrays", None)
    return {
        "warmup": warmup,
        "bull": bull,
        "bear": bear,
        "fresh_stage2_vs5": fresh,
        "inverse_fresh_stage2_vs5": inv_fresh,
        "mirror": mirror,
        "component_mirror": component_mirror,
    }


def build_report() -> dict[str, Any]:
    pairs = {name: analyze_pair(frame) for name, frame in phasea.load_frozen_pairs().items()}
    agg = {
        "usable_direction_observations": 0,
        "raw_loss_bars": 0,
        "winner_precursor_range": 0,
        "winner_opposite_range": 0,
        "winner_opposite_trend": 0,
        "winner_unexplained": 0,
        "max_stage2_vs5_reconstruction_error": 0.0,
    }
    drag_counts = {name: 0 for name in COMPONENT_WEIGHTS}
    mirror_min = 1.0
    component_mirror_max_mae = 0.0

    for p in pairs.values():
        for side in ("bull", "bear"):
            x = p[side]
            agg["usable_direction_observations"] += int(x["usable_bars"])
            agg["raw_loss_bars"] += int(x["raw_loss_bars"])
            agg["winner_precursor_range"] += int(x["winner_group"]["precursor_range"])
            agg["winner_opposite_range"] += int(x["winner_group"]["opposite_range"])
            agg["winner_opposite_trend"] += int(x["winner_group"]["opposite_trend"])
            agg["winner_unexplained"] += int(x["winner_group"]["unexplained"])
        f = p["fresh_stage2_vs5"]
        agg["max_stage2_vs5_reconstruction_error"] = max(
            float(agg["max_stage2_vs5_reconstruction_error"]), float(f["max_abs_reconstruction_error"])
        )
        for name, value in f["largest_negative_component_counts"].items():
            drag_counts[name] += int(value)
        for m in p["mirror"].values():
            mirror_min = min(mirror_min, float(m["mirror_agreement"]))
        for m in p["component_mirror"].values():
            component_mirror_max_mae = max(component_mirror_max_mae, float(m["mae_to_negative_inverse"]))

    loss = int(agg["raw_loss_bars"])
    agg["winner_group_shares"] = {
        "precursor_range": float(agg["winner_precursor_range"] / loss) if loss else 0.0,
        "opposite_range": float(agg["winner_opposite_range"] / loss) if loss else 0.0,
        "opposite_trend": float(agg["winner_opposite_trend"] / loss) if loss else 0.0,
    }
    agg["fresh_pair_largest_negative_component_counts"] = drag_counts
    agg["minimum_boolean_mirror_agreement"] = mirror_min
    agg["max_component_mirror_mae"] = component_mirror_max_mae

    primary = (
        agg["winner_unexplained"] == 0
        and float(agg["max_stage2_vs5_reconstruction_error"]) <= RECON_TOL
        and mirror_min >= 0.99
        and component_mirror_max_mae <= 1e-6
    )
    return {
        "schema_version": 1,
        "issue": 68,
        "phase": "B3.8",
        "status": "RAW_FEATURE_ATTRIBUTION_NO_PERFORMANCE",
        "primary_gate_pass": bool(primary),
        "aggregate": agg,
        "pairs": pairs,
        "boundary": "Raw-stage attribution only. No classifier weight, threshold, gate, persistence, exposure rule, or strategy-performance metric is changed or optimized.",
    }


def render_markdown(r: dict[str, Any]) -> str:
    a = r["aggregate"]
    s = a["winner_group_shares"]
    lines = [
        "# Issue #68 Phase B3.8 — Raw Feature Attribution",
        "",
        "Status: **diagnostic only / frozen C-2 / no performance use**",
        "",
        f"Primary engineering gate: **{'PASS' if r['primary_gate_pass'] else 'FAIL'}**",
        f"- raw-loss observations, bull+bear four-FX: **{a['raw_loss_bars']}**",
        f"- raw winner = precursor range: **{a['winner_precursor_range']} ({100*s['precursor_range']:.1f}%)**",
        f"- raw winner = opposite range: **{a['winner_opposite_range']} ({100*s['opposite_range']:.1f}%)**",
        f"- raw winner = opposite trend: **{a['winner_opposite_trend']} ({100*s['opposite_trend']:.1f}%)**",
        f"- unexplained raw winner: **{a['winner_unexplained']}**",
        f"- Stage2-vs5 exact raw0 reconstruction max error: **{a['max_stage2_vs5_reconstruction_error']:.3e}**",
        f"- minimum reciprocal boolean mirror agreement: **{100*a['minimum_boolean_mirror_agreement']:.3f}%**",
        f"- max reciprocal component-delta MAE: **{a['max_component_mirror_mae']:.3e}**",
        "",
        "## Stage2-vs5 largest negative weighted component when Markup raw0 < Markdown raw0",
        "",
    ]
    for name, count in a["fresh_pair_largest_negative_component_counts"].items():
        lines.append(f"- {name}: **{count}**")
    lines += [
        "",
        "## Per pair raw winner groups",
        "",
        "| Pair | Side | Raw loss | Precursor range | Opp range | Opp trend |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for name, p in r["pairs"].items():
        for side in ("bull", "bear"):
            x = p[side]
            g = x["winner_group"]
            lines.append(
                f"| {name} | {side} | {x['raw_loss_bars']} | {g['precursor_range']} | {g['opposite_range']} | {g['opposite_trend']} |"
            )
    lines += ["", "## Boundary", "", r["boundary"], ""]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, default=HERE / "reports/issue-68-phase-b38-raw-feature-attribution.json")
    ap.add_argument("--md", type=Path, default=HERE / "reports/issue-68-phase-b38-raw-feature-attribution.md")
    args = ap.parse_args()
    report = build_report()
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    args.md.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["aggregate"], indent=2, sort_keys=True))
    if not report["primary_gate_pass"]:
        raise SystemExit("Issue #68 B3.8 raw attribution engineering gate failed")


if __name__ == "__main__":
    main()
