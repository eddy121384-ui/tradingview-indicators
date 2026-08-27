#!/usr/bin/env python3
"""Issue #66 Phase B-3 Stage-2/Stage-5 trend-entry gate reciprocal A/B. No PnL."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

import diagnose_issue66_phase_b1_representation as b1
import diagnose_issue66_phase_b2_break_evidence as b2diag
from generate_issue66_phase_b2_break_evidence_core import load_phase_b2_namespace
from generate_issue66_phase_b3_trend_entry_gate_core import load_phase_b3_namespace

LAYER = "directional_evidence"
ENTRY_KEYS = {
    "entry_gate_up_to_inverse_down_mae": "breakout_markup_gate__to_inverse__breakdown_markdown_gate",
    "entry_gate_down_to_inverse_up_mae": "breakdown_markdown_gate__to_inverse__breakout_markup_gate",
}


def mean_pair(report: dict[str, Any], key: str) -> float:
    values: list[float] = []
    for row in report["pairs"].values():
        metric = row["numeric_layers"][LAYER][key]["mae"]
        if metric is not None:
            values.append(float(metric))
    return float(np.mean(values)) if values else float("nan")


def enrich(report: dict[str, Any]) -> dict[str, Any]:
    out = b2diag.enrich(report)
    out["aggregate"] = dict(out["aggregate"])
    for name, key in ENTRY_KEYS.items():
        out["aggregate"][name] = mean_pair(report, key)
    return out


def build_report() -> dict[str, Any]:
    parent = enrich(b1.build_with_loader(load_phase_b2_namespace))
    variant = enrich(b1.build_with_loader(load_phase_b3_namespace))
    p, v = parent["aggregate"], variant["aggregate"]

    lower_metrics = tuple(ENTRY_KEYS) + (
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
    gains = {k: float(p[k] - v[k]) for k in lower_metrics}
    gains.update({k: float(v[k] - p[k]) for k in agreement_metrics})

    b2_break_keys = tuple(b2diag.KEYS)
    break_preserved = all(abs(v[k] - p[k]) <= 1e-12 for k in b2_break_keys)
    invariants = bool(
        v["range_up_to_inverse_down_jaccard"] >= 0.999999
        and v["range_down_to_inverse_up_jaccard"] >= 0.999999
        and v["ma_up_to_inverse_down_jaccard"] >= 0.999999
        and v["ma_down_to_inverse_up_jaccard"] >= 0.999999
        and break_preserved
    )
    primary = bool(all(v[k] < p[k] for k in ENTRY_KEYS) and invariants)

    return {
        "schema_version": 1,
        "issue": 66,
        "phase": "B-3",
        "status": "TREND_ENTRY_GATE_ONLY_RECIPROCAL_AB_REUSED_DATA_NO_PNL",
        "primary_gate_pass": primary,
        "b2_break_metrics_preserved": break_preserved,
        "parent_b2": parent,
        "variant_b3": variant,
        "symmetry_gain": gains,
    }


def pct(x: float) -> str:
    return f"{x * 100.0:.2f}%"


def num(x: float) -> str:
    return f"{x:.6f}"


def render_markdown(report: dict[str, Any]) -> str:
    p = report["parent_b2"]["aggregate"]
    v = report["variant_b3"]["aggregate"]
    g = report["symmetry_gain"]
    lines = [
        "# Issue #66 Phase B-3 — Direction-Neutral Trend-Entry Gate A/B",
        "",
        "Status: **reused frozen data / no PnL**",
        "",
        f"Primary trend-entry gate: **{'PASS' if report['primary_gate_pass'] else 'FAIL'}**",
        "",
        "Only the Stage-2 / Stage-5 fresh trend-entry gate differs from B-2.",
        "",
        "| Primary metric | B-2 | B-3 | Gain (lower) |",
        "|---|---:|---:|---:|",
        f"| Markup entry → inverse Markdown entry MAE | {num(p['entry_gate_up_to_inverse_down_mae'])} | {num(v['entry_gate_up_to_inverse_down_mae'])} | {num(g['entry_gate_up_to_inverse_down_mae'])} |",
        f"| Markdown entry → inverse Markup entry MAE | {num(p['entry_gate_down_to_inverse_up_mae'])} | {num(v['entry_gate_down_to_inverse_up_mae'])} | {num(g['entry_gate_down_to_inverse_up_mae'])} |",
        "",
        "## Frozen invariants",
        "",
        f"Range U→D {pct(v['range_up_to_inverse_down_jaccard'])}; Range D→U {pct(v['range_down_to_inverse_up_jaccard'])}  ",
        f"MA U→D {pct(v['ma_up_to_inverse_down_jaccard'])}; MA D→U {pct(v['ma_down_to_inverse_up_jaccard'])}  ",
        f"B-2 break metrics preserved exactly: **{'YES' if report['b2_break_metrics_preserved'] else 'NO'}**",
        "",
        "## Downstream observations (not tuning targets)",
        "",
        "| Metric | B-2 | B-3 | Symmetry gain |",
        "|---|---:|---:|---:|",
        f"| Raw stage-vector MAE | {num(p['raw_stage_vector_mae'])} | {num(v['raw_stage_vector_mae'])} | {num(g['raw_stage_vector_mae'])} lower |",
        f"| Gate-vector MAE | {num(p['stage_gate_vector_mae'])} | {num(v['stage_gate_vector_mae'])} | {num(g['stage_gate_vector_mae'])} lower |",
        f"| Effective-vector MAE | {num(p['effective_stage_vector_mae'])} | {num(v['effective_stage_vector_mae'])} | {num(g['effective_stage_vector_mae'])} lower |",
        f"| Probability-vector MAE | {num(p['probability_stage_vector_mae'])} | {num(v['probability_stage_vector_mae'])} | {num(g['probability_stage_vector_mae'])} lower |",
        f"| Candidate mirror | {pct(p['candidate_display_mirror_agreement'])} | {pct(v['candidate_display_mirror_agreement'])} | {pct(g['candidate_display_mirror_agreement'])} |",
        f"| Formal mirror | {pct(p['formal_stage_mirror_agreement'])} | {pct(v['formal_stage_mirror_agreement'])} | {pct(g['formal_stage_mirror_agreement'])} |",
        f"| Formal transition mirror | {pct(p['formal_transition_pair_mirror_agreement'])} | {pct(v['formal_transition_pair_mirror_agreement'])} | {pct(g['formal_transition_pair_mirror_agreement'])} |",
        "",
        "Downstream metrics may not be used to retune B-3.",
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
        "b2_break_metrics_preserved": report["b2_break_metrics_preserved"],
        "parent_b2": report["parent_b2"]["aggregate"],
        "variant_b3": report["variant_b3"]["aggregate"],
        "symmetry_gain": report["symmetry_gain"],
    }, indent=2))


if __name__ == "__main__":
    main()
