#!/usr/bin/env python3
"""Issue #66 Phase B-7 Stage-1/Stage-4 gate reciprocal A/B. No PnL."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

import diagnose_issue66_phase_b1_representation as b1
import diagnose_issue66_phase_b2_break_evidence as b2diag
import diagnose_issue66_phase_b3_trend_entry_gate as b3diag
import diagnose_issue66_phase_b5_stage36_raw as b5diag
import diagnose_issue66_phase_b6_stage14_raw as b6diag
from generate_issue66_phase_b6_stage14_raw_core import load_phase_b6_namespace
from generate_issue66_phase_b7_stage14_gate_core import load_phase_b7_namespace

GATE_LAYER = "stage_gates"
GATE_KEYS = {
    "acc_gate_to_inverse_dist_gate_mae": "acc_gate__to_inverse__dist_gate",
    "dist_gate_to_inverse_acc_gate_mae": "dist_gate__to_inverse__acc_gate",
}


def mean_pair(report: dict[str, Any], layer: str, key: str) -> float:
    values: list[float] = []
    for row in report["pairs"].values():
        metric = row["numeric_layers"][layer][key]["mae"]
        if metric is not None:
            values.append(float(metric))
    return float(np.mean(values)) if values else float("nan")


def enrich(report: dict[str, Any]) -> dict[str, Any]:
    out = b6diag.enrich(report)
    out["aggregate"] = dict(out["aggregate"])
    for name, key in GATE_KEYS.items():
        out["aggregate"][name] = mean_pair(report, GATE_LAYER, key)
    return out


def build_report() -> dict[str, Any]:
    parent = enrich(b1.build_with_loader(load_phase_b6_namespace))
    variant = enrich(b1.build_with_loader(load_phase_b7_namespace))
    p, v = parent["aggregate"], variant["aggregate"]

    inherited_exact_keys = (
        tuple(b2diag.KEYS)
        + tuple(b3diag.ENTRY_KEYS)
        + tuple(b5diag.RAW_KEYS)
        + tuple(b6diag.RAW_KEYS)
    )
    inherited_preserved = all(abs(v[key] - p[key]) <= 1e-12 for key in inherited_exact_keys)
    structural_invariants = bool(
        v["range_up_to_inverse_down_jaccard"] >= 0.999999
        and v["range_down_to_inverse_up_jaccard"] >= 0.999999
        and v["ma_up_to_inverse_down_jaccard"] >= 0.999999
        and v["ma_down_to_inverse_up_jaccard"] >= 0.999999
        and inherited_preserved
    )
    primary = bool(all(v[key] < p[key] for key in GATE_KEYS) and structural_invariants)

    lower_metrics = tuple(GATE_KEYS) + (
        "raw_stage_vector_mae",
        "stage_gate_vector_mae",
        "effective_stage_vector_mae",
        "probability_stage_vector_mae",
    )
    agreement_metrics = (
        "candidate_display_mirror_agreement",
        "formal_stage_mirror_agreement",
        "candidate_transition_pair_mirror_agreement",
        "formal_transition_pair_mirror_agreement",
    )
    gains = {key: float(p[key] - v[key]) for key in lower_metrics}
    gains.update({key: float(v[key] - p[key]) for key in agreement_metrics})

    return {
        "schema_version": 1,
        "issue": 66,
        "phase": "B-7",
        "status": "STAGE14_GATE_ONLY_RECIPROCAL_AB_REUSED_DATA_NO_PNL",
        "primary_gate_pass": primary,
        "inherited_b2_b3_b5_b6_metrics_preserved": inherited_preserved,
        "parent_b6": parent,
        "variant_b7": variant,
        "symmetry_gain": gains,
    }


def pct(x: float) -> str:
    return f"{x * 100.0:.2f}%"


def num(x: float) -> str:
    return f"{x:.6f}"


def render_markdown(report: dict[str, Any]) -> str:
    p = report["parent_b6"]["aggregate"]
    v = report["variant_b7"]["aggregate"]
    g = report["symmetry_gain"]
    lines = [
        "# Issue #66 Phase B-7 — Stage 1/4 Gate Symmetry Repair A/B",
        "",
        "Status: **reused frozen data / no PnL**",
        "",
        f"Primary Stage 1/4 gate: **{'PASS' if report['primary_gate_pass'] else 'FAIL'}**",
        "",
        "Only the Stage-1 / Stage-4 background/maturity gate factor differs from B-6.",
        "",
        "| Primary metric | B-6 | B-7 | Gain (lower) |",
        "|---|---:|---:|---:|",
        f"| Acc gate → inverse Dist gate MAE | {num(p['acc_gate_to_inverse_dist_gate_mae'])} | {num(v['acc_gate_to_inverse_dist_gate_mae'])} | {num(g['acc_gate_to_inverse_dist_gate_mae'])} |",
        f"| Dist gate → inverse Acc gate MAE | {num(p['dist_gate_to_inverse_acc_gate_mae'])} | {num(v['dist_gate_to_inverse_acc_gate_mae'])} | {num(g['dist_gate_to_inverse_acc_gate_mae'])} |",
        "",
        "## Frozen invariants",
        "",
        f"Range U→D {pct(v['range_up_to_inverse_down_jaccard'])}; Range D→U {pct(v['range_down_to_inverse_up_jaccard'])}  ",
        f"MA U→D {pct(v['ma_up_to_inverse_down_jaccard'])}; MA D→U {pct(v['ma_down_to_inverse_up_jaccard'])}  ",
        f"B-2/B-3/B-5/B-6 registered metrics preserved exactly: **{'YES' if report['inherited_b2_b3_b5_b6_metrics_preserved'] else 'NO'}**",
        "",
        "## Downstream observations (not tuning targets)",
        "",
        "| Metric | B-6 | B-7 | Symmetry gain |",
        "|---|---:|---:|---:|",
        f"| Raw stage-vector MAE | {num(p['raw_stage_vector_mae'])} | {num(v['raw_stage_vector_mae'])} | {num(g['raw_stage_vector_mae'])} lower |",
        f"| Gate-vector MAE | {num(p['stage_gate_vector_mae'])} | {num(v['stage_gate_vector_mae'])} | {num(g['stage_gate_vector_mae'])} lower |",
        f"| Effective-vector MAE | {num(p['effective_stage_vector_mae'])} | {num(v['effective_stage_vector_mae'])} | {num(g['effective_stage_vector_mae'])} lower |",
        f"| Probability-vector MAE | {num(p['probability_stage_vector_mae'])} | {num(v['probability_stage_vector_mae'])} | {num(g['probability_stage_vector_mae'])} lower |",
        f"| Candidate mirror | {pct(p['candidate_display_mirror_agreement'])} | {pct(v['candidate_display_mirror_agreement'])} | {pct(g['candidate_display_mirror_agreement'])} |",
        f"| Formal mirror | {pct(p['formal_stage_mirror_agreement'])} | {pct(v['formal_stage_mirror_agreement'])} | {pct(g['formal_stage_mirror_agreement'])} |",
        f"| Formal transition mirror | {pct(p['formal_transition_pair_mirror_agreement'])} | {pct(v['formal_transition_pair_mirror_agreement'])} | {pct(g['formal_transition_pair_mirror_agreement'])} |",
        "",
        "Downstream metrics may not be used to retune B-7.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, required=True)
    ap.add_argument("--markdown", type=Path, required=True)
    args = ap.parse_args()
    report = build_report()
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.markdown.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({
        "primary_gate_pass": report["primary_gate_pass"],
        "inherited_b2_b3_b5_b6_metrics_preserved": report["inherited_b2_b3_b5_b6_metrics_preserved"],
        "parent_b6": report["parent_b6"]["aggregate"],
        "variant_b7": report["variant_b7"]["aggregate"],
        "symmetry_gain": report["symmetry_gain"],
    }, indent=2))


if __name__ == "__main__":
    main()
