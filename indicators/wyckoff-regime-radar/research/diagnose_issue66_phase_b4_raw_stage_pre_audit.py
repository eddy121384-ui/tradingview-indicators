#!/usr/bin/env python3
"""Issue #66 Phase B-4 raw-stage residual localization. Diagnostic only; no PnL."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import diagnose_issue66_phase_b1_representation as b1
from generate_issue66_phase_b3_trend_entry_gate_core import load_phase_b3_namespace

FAMILIES = {
    "stage_1_4": {
        "label": "Stage 1 Accumulation ↔ Stage 4 Distribution",
        "stage_raw": (("acc_raw", "dist_raw"), ("dist_raw", "acc_raw")),
        "stage_gates": (("acc_gate", "dist_gate"), ("dist_gate", "acc_gate")),
        "effective_weights": (("acc_eff", "dist_eff"), ("dist_eff", "acc_eff")),
        "probability_weights": (("prob_acc", "prob_dist"), ("prob_dist", "prob_acc")),
    },
    "stage_2_5": {
        "label": "Stage 2 Markup ↔ Stage 5 Markdown",
        "stage_raw": (("markup_raw", "markdown_raw"), ("markdown_raw", "markup_raw")),
        "stage_gates": (("markup_gate", "markdown_gate"), ("markdown_gate", "markup_gate")),
        "effective_weights": (("markup_eff", "markdown_eff"), ("markdown_eff", "markup_eff")),
        "probability_weights": (("prob_markup", "prob_markdown"), ("prob_markdown", "prob_markup")),
    },
    "stage_3_6": {
        "label": "Stage 3 Re-accumulation ↔ Stage 6 Re-distribution",
        "stage_raw": (("reacc_raw", "redist_raw"), ("redist_raw", "reacc_raw")),
        "stage_gates": (("reacc_gate", "redist_gate"), ("redist_gate", "reacc_gate")),
        "effective_weights": (("reacc_eff", "redist_eff"), ("redist_eff", "reacc_eff")),
        "probability_weights": (("prob_reacc", "prob_redist"), ("prob_redist", "prob_reacc")),
    },
}
LAYERS = ("stage_raw", "stage_gates", "effective_weights", "probability_weights")


def metric_key(left: str, right: str) -> str:
    return f"{left}__to_inverse__{right}"


def metric_from_row(row: dict[str, Any], layer: str, left: str, right: str) -> dict[str, Any]:
    return row["numeric_layers"][layer][metric_key(left, right)]


def aggregate_family(report: dict[str, Any], family: dict[str, Any], layer: str) -> dict[str, Any]:
    orientations = family[layer]
    total_abs_error = 0.0
    total_valid = 0
    per_orientation: dict[str, Any] = {}
    for left, right in orientations:
        orient_abs = 0.0
        orient_valid = 0
        per_fx: dict[str, Any] = {}
        for pair, row in report["pairs"].items():
            metric = metric_from_row(row, layer, left, right)
            valid = int(metric["valid_bars"])
            mae = metric["mae"]
            abs_error = float(mae) * valid if mae is not None else 0.0
            orient_abs += abs_error
            orient_valid += valid
            per_fx[pair] = {"valid_bars": valid, "mae": mae, "absolute_error_sum": abs_error}
        key = f"{left}__to_inverse__{right}"
        per_orientation[key] = {
            "valid_bars": orient_valid,
            "mae": orient_abs / orient_valid if orient_valid else None,
            "absolute_error_sum": orient_abs,
            "per_fx": per_fx,
        }
        total_abs_error += orient_abs
        total_valid += orient_valid
    return {
        "valid_values": total_valid,
        "weighted_mae": total_abs_error / total_valid if total_valid else None,
        "absolute_error_sum": total_abs_error,
        "orientations": per_orientation,
    }


def build_report() -> dict[str, Any]:
    parent = b1.build_with_loader(load_phase_b3_namespace)
    decomposition: dict[str, Any] = {}
    layer_totals: dict[str, Any] = {}

    for family_id, spec in FAMILIES.items():
        decomposition[family_id] = {"label": spec["label"]}
        for layer in LAYERS:
            decomposition[family_id][layer] = aggregate_family(parent, spec, layer)

    for layer in LAYERS:
        total_abs = sum(decomposition[f][layer]["absolute_error_sum"] for f in FAMILIES)
        total_valid = sum(decomposition[f][layer]["valid_values"] for f in FAMILIES)
        reconstructed = total_abs / total_valid if total_valid else None
        for family_id in FAMILIES:
            family_abs = decomposition[family_id][layer]["absolute_error_sum"]
            decomposition[family_id][layer]["absolute_error_share"] = (
                family_abs / total_abs if total_abs > 0.0 else 0.0
            )
        layer_totals[layer] = {
            "valid_values": total_valid,
            "absolute_error_sum": total_abs,
            "reconstructed_weighted_mae": reconstructed,
        }

    expected_raw = float(parent["aggregate"]["raw_stage_vector_mae"])
    reconstructed_raw = float(layer_totals["stage_raw"]["reconstructed_weighted_mae"])
    reconstruction_error = abs(expected_raw - reconstructed_raw)

    ranked = sorted(
        FAMILIES,
        key=lambda family_id: (
            decomposition[family_id]["stage_raw"]["absolute_error_sum"],
            decomposition[family_id]["stage_raw"]["weighted_mae"],
        ),
        reverse=True,
    )
    dominant = ranked[0]

    return {
        "schema_version": 1,
        "issue": 66,
        "phase": "B-4-pre-audit",
        "status": "RAW_STAGE_RESIDUAL_LOCALIZATION_REUSED_DATA_NO_PNL_NO_FORMULA_CHANGE",
        "parent": "accepted B-3 core",
        "raw_stage_vector_mae": expected_raw,
        "reconstructed_raw_stage_mae": reconstructed_raw,
        "reconstruction_error": reconstruction_error,
        "reconstruction_pass": reconstruction_error <= 1e-12,
        "dominant_raw_stage_family": dominant,
        "ranking": ranked,
        "families": decomposition,
        "layer_totals": layer_totals,
    }


def pct(x: float) -> str:
    return f"{x * 100.0:.2f}%"


def num(x: float | None) -> str:
    return "n/a" if x is None else f"{x:.6f}"


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Issue #66 Phase B-4 — Raw-Stage Residual Pre-Audit",
        "",
        "Status: **reused frozen data / no PnL / no formula change**",
        "",
        f"B-3 raw-stage vector MAE: **{num(report['raw_stage_vector_mae'])}**  ",
        f"Reconstructed from three mirrored families: **{num(report['reconstructed_raw_stage_mae'])}**  ",
        f"Reconstruction check: **{'PASS' if report['reconstruction_pass'] else 'FAIL'}**",
        "",
        "## Raw-stage localization",
        "",
        "| Rank | Mirrored family | Weighted raw MAE | Share of raw absolute error |",
        "|---:|---|---:|---:|",
    ]
    for rank, family_id in enumerate(report["ranking"], 1):
        node = report["families"][family_id]
        raw = node["stage_raw"]
        lines.append(
            f"| {rank} | {node['label']} | {num(raw['weighted_mae'])} | {pct(raw['absolute_error_share'])} |"
        )

    dominant = report["dominant_raw_stage_family"]
    lines += [
        "",
        f"Dominant residual family by preregistered rule: **{report['families'][dominant]['label']}**.",
        "",
        "## Secondary layer context",
        "",
        "These values localize propagation only; they do not choose the next formula.",
        "",
        "| Mirrored family | Gate MAE | Effective MAE | Probability MAE |",
        "|---|---:|---:|---:|",
    ]
    for family_id in report["ranking"]:
        node = report["families"][family_id]
        lines.append(
            f"| {node['label']} | {num(node['stage_gates']['weighted_mae'])} | "
            f"{num(node['effective_weights']['weighted_mae'])} | {num(node['probability_weights']['weighted_mae'])} |"
        )

    lines += [
        "",
        "## Next-step boundary",
        "",
        "No classifier change is authorized by this report. Inspect the dominant raw family's source formula for explicit non-isomorphic primitives, then preregister one B-5 repair family before changing code. Candidate/Formal/PnL results are not selection criteria.",
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
        "raw_stage_vector_mae": report["raw_stage_vector_mae"],
        "reconstructed_raw_stage_mae": report["reconstructed_raw_stage_mae"],
        "reconstruction_pass": report["reconstruction_pass"],
        "dominant_raw_stage_family": report["dominant_raw_stage_family"],
        "ranking": report["ranking"],
        "raw_families": {
            key: {
                "weighted_mae": value["stage_raw"]["weighted_mae"],
                "absolute_error_share": value["stage_raw"]["absolute_error_share"],
            }
            for key, value in report["families"].items()
        },
    }, indent=2))


if __name__ == "__main__":
    main()
