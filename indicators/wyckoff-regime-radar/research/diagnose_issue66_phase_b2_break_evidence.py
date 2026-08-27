#!/usr/bin/env python3
"""Issue #66 Phase B-2 break-evidence reciprocal A/B. No PnL."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

import diagnose_issue66_phase_b1_representation as b1
from generate_issue66_phase_b1_representation_core import load_phase_b1_namespace
from generate_issue66_phase_b2_break_evidence_core import load_phase_b2_namespace

LAYER = "directional_evidence"
KEYS = {
    "break_score_up_to_inverse_down_mae": "breakout_score__to_inverse__explicit_breakdown_score",
    "break_score_down_to_inverse_up_mae": "explicit_breakdown_score__to_inverse__breakout_score",
    "break_gate_up_to_inverse_down_mae": "breakout_gate__to_inverse__explicit_breakdown_gate",
    "break_gate_down_to_inverse_up_mae": "explicit_breakdown_gate__to_inverse__breakout_gate",
}


def mean_pair(report: dict[str, Any], key: str) -> float:
    vals = []
    for row in report["pairs"].values():
        v = row["numeric_layers"][LAYER][key]["mae"]
        if v is not None:
            vals.append(float(v))
    return float(np.mean(vals)) if vals else float("nan")


def enrich(report: dict[str, Any]) -> dict[str, Any]:
    out = b1.enrich(report)
    out["aggregate"] = dict(out["aggregate"])
    for name, key in KEYS.items():
        out["aggregate"][name] = mean_pair(report, key)
    return out


def build_report() -> dict[str, Any]:
    parent = enrich(b1.build_with_loader(load_phase_b1_namespace))
    variant = enrich(b1.build_with_loader(load_phase_b2_namespace))
    p, v = parent["aggregate"], variant["aggregate"]
    mae = tuple(KEYS) + (
        "representation_numeric_mae", "raw_stage_vector_mae", "stage_gate_vector_mae",
        "effective_stage_vector_mae", "probability_stage_vector_mae",
    )
    agree = (
        "range_up_to_inverse_down_jaccard", "range_down_to_inverse_up_jaccard",
        "ma_up_to_inverse_down_jaccard", "ma_down_to_inverse_up_jaccard",
        "candidate_display_mirror_agreement", "formal_stage_mirror_agreement",
        "candidate_transition_pair_mirror_agreement", "formal_transition_pair_mirror_agreement",
    )
    gain = {k: float(p[k] - v[k]) for k in mae}
    gain.update({k: float(v[k] - p[k]) for k in agree})
    primary = bool(
        all(v[k] < p[k] for k in KEYS)
        and v["ma_up_to_inverse_down_jaccard"] >= 0.999999
        and v["ma_down_to_inverse_up_jaccard"] >= 0.999999
        and v["range_up_to_inverse_down_jaccard"] >= 0.999999
        and v["range_down_to_inverse_up_jaccard"] >= 0.999999
    )
    return {
        "schema_version": 1,
        "issue": 66,
        "phase": "B-2",
        "status": "BREAK_EVIDENCE_ONLY_RECIPROCAL_AB_REUSED_DATA_NO_PNL",
        "primary_gate_pass": primary,
        "parent_b1": parent,
        "variant_b2": variant,
        "symmetry_gain": gain,
    }


def pct(x: float) -> str:
    return f"{x * 100:.2f}%"


def num(x: float) -> str:
    return f"{x:.6f}"


def render_markdown(r: dict[str, Any]) -> str:
    p, v, g = r["parent_b1"]["aggregate"], r["variant_b2"]["aggregate"], r["symmetry_gain"]
    lines = [
        "# Issue #66 Phase B-2 — Direction-Neutral Break Evidence A/B", "",
        "Status: **reused frozen data / no PnL**", "",
        f"Primary break-evidence gate: **{'PASS' if r['primary_gate_pass'] else 'FAIL'}**", "",
        "Only break evidence and its directly-derived gate differ from B-1.", "",
        "| Primary metric | B-1 | B-2 | Gain (lower) |", "|---|---:|---:|---:|",
    ]
    labels = {
        "break_score_up_to_inverse_down_mae": "Break score U→inverse D MAE",
        "break_score_down_to_inverse_up_mae": "Break score D→inverse U MAE",
        "break_gate_up_to_inverse_down_mae": "Break gate U→inverse D MAE",
        "break_gate_down_to_inverse_up_mae": "Break gate D→inverse U MAE",
    }
    for k, label in labels.items():
        lines.append(f"| {label} | {num(p[k])} | {num(v[k])} | {num(g[k])} |")
    lines += ["", "## Frozen invariants", "",
        f"Range U→D: {pct(v['range_up_to_inverse_down_jaccard'])}; Range D→U: {pct(v['range_down_to_inverse_up_jaccard'])}  ",
        f"MA U→D: {pct(v['ma_up_to_inverse_down_jaccard'])}; MA D→U: {pct(v['ma_down_to_inverse_up_jaccard'])}", "",
        "## Downstream observations (not tuning targets)", "",
        "| Metric | B-1 | B-2 | Symmetry gain |", "|---|---:|---:|---:|",
        f"| Raw stage-vector MAE | {num(p['raw_stage_vector_mae'])} | {num(v['raw_stage_vector_mae'])} | {num(g['raw_stage_vector_mae'])} lower |",
        f"| Gate-vector MAE | {num(p['stage_gate_vector_mae'])} | {num(v['stage_gate_vector_mae'])} | {num(g['stage_gate_vector_mae'])} lower |",
        f"| Effective-vector MAE | {num(p['effective_stage_vector_mae'])} | {num(v['effective_stage_vector_mae'])} | {num(g['effective_stage_vector_mae'])} lower |",
        f"| Probability-vector MAE | {num(p['probability_stage_vector_mae'])} | {num(v['probability_stage_vector_mae'])} | {num(g['probability_stage_vector_mae'])} lower |",
        f"| Candidate mirror | {pct(p['candidate_display_mirror_agreement'])} | {pct(v['candidate_display_mirror_agreement'])} | {pct(g['candidate_display_mirror_agreement'])} |",
        f"| Formal mirror | {pct(p['formal_stage_mirror_agreement'])} | {pct(v['formal_stage_mirror_agreement'])} | {pct(g['formal_stage_mirror_agreement'])} |",
        f"| Formal transition mirror | {pct(p['formal_transition_pair_mirror_agreement'])} | {pct(v['formal_transition_pair_mirror_agreement'])} | {pct(g['formal_transition_pair_mirror_agreement'])} |",
        "", "Stage metrics above may not be used to retune B-2.", "",
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
    print(json.dumps({"primary_gate_pass": report["primary_gate_pass"], "parent_b1": report["parent_b1"]["aggregate"], "variant_b2": report["variant_b2"]["aggregate"], "symmetry_gain": report["symmetry_gain"]}, indent=2))


if __name__ == "__main__":
    main()
