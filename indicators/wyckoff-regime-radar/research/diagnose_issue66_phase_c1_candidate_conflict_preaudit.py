#!/usr/bin/env python3
"""Issue #66 Phase C-1: localize candidate-conflict mismatch by mirrored stage family. No PnL."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

import diagnose_issue66_phase_c_persistence_localization_v3 as cdiag


FAMILIES = {
    "stage1_4": {1, 4},
    "stage2_5": {2, 5},
    "stage3_6": {3, 6},
}
LABELS = {
    "stage1_4": "Stage 1 Accumulation ↔ Stage 4 Distribution",
    "stage2_5": "Stage 2 Markup ↔ Stage 5 Markdown",
    "stage3_6": "Stage 3 Re-accumulation ↔ Stage 6 Re-distribution",
}


def analyze_pair(frame) -> dict[str, Any]:
    model, inverse, _cfg, warmup = cdiag.v1.load_pair(frame)
    top = cdiag.v1.arr_int(model, "top_id")[warmup:]
    inv_top = cdiag.v1.arr_int(inverse, "top_id")[warmup:]
    conflict = cdiag.v1.arr_bool(model, "candidate_conflict")[warmup:]
    inv_conflict = cdiag.v1.arr_bool(inverse, "candidate_conflict")[warmup:]

    top_mirrored = cdiag.v1.mirror_stage(top) == inv_top
    conflict_mismatch = conflict != inv_conflict
    attributable = top_mirrored & conflict_mismatch

    family_counts: dict[str, int] = {}
    family_bars: dict[str, int] = {}
    for key, stages in FAMILIES.items():
        family_mask = np.isin(top, list(stages)) & top_mirrored
        family_bars[key] = int(np.sum(family_mask))
        family_counts[key] = int(np.sum(attributable & np.isin(top, list(stages))))

    return {
        "bars": int(len(top)),
        "top_mirrored_bars": int(np.sum(top_mirrored)),
        "conflict_mismatch_bars": int(np.sum(conflict_mismatch)),
        "attributable_conflict_mismatch_bars": int(np.sum(attributable)),
        "conflict_mismatch_with_top_not_mirrored": int(np.sum(conflict_mismatch & ~top_mirrored)),
        "family_bars": family_bars,
        "family_mismatch_counts": family_counts,
    }


def build_report() -> dict[str, Any]:
    pairs = {name: analyze_pair(frame) for name, frame in cdiag.v1.phasea.load_frozen_pairs().items()}
    totals = {key: 0 for key in FAMILIES}
    family_bars = {key: 0 for key in FAMILIES}
    attributable = 0
    total_mismatch = 0
    top_not_mirrored = 0
    for row in pairs.values():
        attributable += row["attributable_conflict_mismatch_bars"]
        total_mismatch += row["conflict_mismatch_bars"]
        top_not_mirrored += row["conflict_mismatch_with_top_not_mirrored"]
        for key in FAMILIES:
            totals[key] += row["family_mismatch_counts"][key]
            family_bars[key] += row["family_bars"][key]

    shares = {key: (totals[key] / attributable if attributable else 0.0) for key in FAMILIES}
    ranked = sorted(FAMILIES, key=lambda key: totals[key], reverse=True)
    dominant = ranked[0] if ranked else None
    gate_pass = bool(dominant is not None and shares[dominant] >= 0.90)

    return {
        "schema_version": 1,
        "issue": 66,
        "phase": "C-1",
        "status": "CANDIDATE_CONFLICT_PREAUDIT_REUSED_DATA_NO_PNL_NO_FORMULA_CHANGE",
        "total_conflict_mismatch_bars": int(total_mismatch),
        "attributable_conflict_mismatch_bars": int(attributable),
        "conflict_mismatch_with_top_not_mirrored": int(top_not_mirrored),
        "families": {
            key: {
                "label": LABELS[key],
                "eligible_top_mirrored_bars": int(family_bars[key]),
                "conflict_mismatch_bars": int(totals[key]),
                "share_of_attributable_conflict_mismatch": float(shares[key]),
            }
            for key in FAMILIES
        },
        "ranked_families": ranked,
        "dominant_family": dominant,
        "dominant_share": float(shares[dominant]) if dominant else 0.0,
        "preregistered_dominance_gate_pass": gate_pass,
        "pairs": pairs,
    }


def pct(x: float) -> str:
    return f"{x * 100.0:.2f}%"


def render_markdown(r: dict[str, Any]) -> str:
    lines = [
        "# Issue #66 Phase C-1 — Candidate-Conflict Residual Pre-Audit",
        "",
        "Status: **reused frozen data / no PnL / no formula change**",
        "",
        f"Total candidate-conflict mismatch bars: **{r['total_conflict_mismatch_bars']}**  ",
        f"Attributable with top stage already mirrored: **{r['attributable_conflict_mismatch_bars']}**  ",
        f"Conflict mismatch with top stage not mirrored: **{r['conflict_mismatch_with_top_not_mirrored']}**",
        "",
        "| Rank | Mirrored family | Conflict mismatch bars | Share of attributable mismatch |",
        "|---:|---|---:|---:|",
    ]
    for rank, key in enumerate(r["ranked_families"], 1):
        node = r["families"][key]
        lines.append(f"| {rank} | {node['label']} | {node['conflict_mismatch_bars']} | {pct(node['share_of_attributable_conflict_mismatch'])} |")
    lines += [
        "",
        f"Preregistered >=90% dominance gate: **{'PASS' if r['preregistered_dominance_gate_pass'] else 'FAIL'}**",
        "",
        f"Only eligible C-2 repair family if PASS: **{r['families'][r['dominant_family']]['label'] if r['dominant_family'] else 'None'}**.",
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
        "dominant_family": report["dominant_family"],
        "dominant_share": report["dominant_share"],
        "gate_pass": report["preregistered_dominance_gate_pass"],
        "families": report["families"],
    }, indent=2))


if __name__ == "__main__":
    main()
