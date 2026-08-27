#!/usr/bin/env python3
"""Issue #66 Phase C-2 Stage-1/Stage-4 candidate-conflict reciprocal A/B. No PnL."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

import numpy as np

import diagnose_issue66_phase_b1_representation as b1
import diagnose_issue66_phase_b2_break_evidence as b2diag
import diagnose_issue66_phase_b3_trend_entry_gate as b3diag
import diagnose_issue66_phase_b5_stage36_raw as b5diag
import diagnose_issue66_phase_b6_stage14_raw as b6diag
import diagnose_issue66_phase_b7_stage14_gate as b7diag
import diagnose_issue66_phase_c_persistence_localization_v3 as cdiag
import diagnose_issue66_phase_c1_candidate_conflict_preaudit as c1diag
from generate_issue66_phase_b7_stage14_gate_core import load_phase_b7_namespace
from generate_issue66_phase_c2_stage14_conflict_core import load_phase_c2_namespace


HERE = Path(__file__).resolve().parent


def load_pair_with_loader(frame, loader: Callable[[], dict[str, object]]):
    ns = loader()
    cfg = ns["PriceOnlyConfig"]()
    compute = ns["compute_price_only"]
    model = compute(frame.copy(), cfg)
    inverse = compute(cdiag.v1.phasea.reciprocal_ohlc(frame), cfg)
    warmup = int(cfg.rank_len - 1)
    return model, inverse, cfg, warmup


def conflict_localization_with_loader(loader: Callable[[], dict[str, object]]) -> dict[str, Any]:
    totals = {key: 0 for key in c1diag.FAMILIES}
    eligible = {key: 0 for key in c1diag.FAMILIES}
    total_mismatch = 0
    attributable = 0
    top_not_mirrored = 0
    total_bars = 0
    agreement_matches = 0

    for frame in cdiag.v1.phasea.load_frozen_pairs().values():
        model, inverse, _cfg, warmup = load_pair_with_loader(frame, loader)
        top = cdiag.v1.arr_int(model, "top_id")[warmup:]
        inv_top = cdiag.v1.arr_int(inverse, "top_id")[warmup:]
        conflict = cdiag.v1.arr_bool(model, "candidate_conflict")[warmup:]
        inv_conflict = cdiag.v1.arr_bool(inverse, "candidate_conflict")[warmup:]

        top_mirrored = cdiag.v1.mirror_stage(top) == inv_top
        mismatch = conflict != inv_conflict
        attributable_mask = top_mirrored & mismatch

        total_bars += len(top)
        agreement_matches += int(np.sum(~mismatch))
        total_mismatch += int(np.sum(mismatch))
        attributable += int(np.sum(attributable_mask))
        top_not_mirrored += int(np.sum(mismatch & ~top_mirrored))

        for key, stages in c1diag.FAMILIES.items():
            family_mask = np.isin(top, list(stages)) & top_mirrored
            eligible[key] += int(np.sum(family_mask))
            totals[key] += int(np.sum(attributable_mask & np.isin(top, list(stages))))

    return {
        "candidate_conflict_mirror_agreement": float(agreement_matches / total_bars) if total_bars else 1.0,
        "total_conflict_mismatch_bars": int(total_mismatch),
        "attributable_conflict_mismatch_bars": int(attributable),
        "conflict_mismatch_with_top_not_mirrored": int(top_not_mirrored),
        "families": {
            key: {
                "eligible_top_mirrored_bars": int(eligible[key]),
                "conflict_mismatch_bars": int(totals[key]),
                "share_of_attributable_conflict_mismatch": float(totals[key] / attributable) if attributable else 0.0,
            }
            for key in c1diag.FAMILIES
        },
    }


def persistence_with_loader(loader: Callable[[], dict[str, object]]) -> dict[str, Any]:
    original_load_pair = cdiag.v1.load_pair

    def injected(frame):
        return load_pair_with_loader(frame, loader)

    cdiag.v1.load_pair = injected
    try:
        return cdiag.build_report()
    finally:
        cdiag.v1.load_pair = original_load_pair


def numeric_with_loader(loader: Callable[[], dict[str, object]]) -> dict[str, Any]:
    return b7diag.enrich(b1.build_with_loader(loader))


def build_report() -> dict[str, Any]:
    parent_numeric = numeric_with_loader(load_phase_b7_namespace)
    variant_numeric = numeric_with_loader(load_phase_c2_namespace)
    pnum, vnum = parent_numeric["aggregate"], variant_numeric["aggregate"]

    parent_conflict = conflict_localization_with_loader(load_phase_b7_namespace)
    variant_conflict = conflict_localization_with_loader(load_phase_c2_namespace)

    inherited_numeric_keys = (
        tuple(b2diag.KEYS)
        + tuple(b3diag.ENTRY_KEYS)
        + tuple(b5diag.RAW_KEYS)
        + tuple(b6diag.RAW_KEYS)
        + tuple(b7diag.GATE_KEYS)
        + (
            "raw_stage_vector_mae",
            "stage_gate_vector_mae",
            "effective_stage_vector_mae",
            "probability_stage_vector_mae",
            "range_up_to_inverse_down_jaccard",
            "range_down_to_inverse_up_jaccard",
            "ma_up_to_inverse_down_jaccard",
            "ma_down_to_inverse_up_jaccard",
        )
    )
    numeric_preserved = all(abs(float(vnum[key]) - float(pnum[key])) <= 1e-12 for key in inherited_numeric_keys)

    parent_persistence = persistence_with_loader(load_phase_b7_namespace)
    variant_persistence = persistence_with_loader(load_phase_c2_namespace)

    p14 = parent_conflict["families"]["stage1_4"]["conflict_mismatch_bars"]
    v14 = variant_conflict["families"]["stage1_4"]["conflict_mismatch_bars"]
    other_zero = bool(
        variant_conflict["families"]["stage2_5"]["conflict_mismatch_bars"] == 0
        and variant_conflict["families"]["stage3_6"]["conflict_mismatch_bars"] == 0
    )
    primary = bool(
        variant_conflict["candidate_conflict_mirror_agreement"] > parent_conflict["candidate_conflict_mirror_agreement"]
        and v14 < p14
        and other_zero
        and numeric_preserved
        and variant_persistence["all_original_replays_exact"]
    )

    secondary_keys = (
        "candidate_conflict", "strong_stage", "candidate_display", "formal",
        "stale_pressure_reason", "stale_pressure_bars",
    )
    downstream = {
        key: {
            "b7": float(parent_persistence["agreements"][key]),
            "c2": float(variant_persistence["agreements"][key]),
            "gain": float(variant_persistence["agreements"][key] - parent_persistence["agreements"][key]),
        }
        for key in secondary_keys
    }
    downstream["formal_transition"] = {
        "b7": float(pnum["formal_transition_pair_mirror_agreement"]),
        "c2": float(vnum["formal_transition_pair_mirror_agreement"]),
        "gain": float(vnum["formal_transition_pair_mirror_agreement"] - pnum["formal_transition_pair_mirror_agreement"]),
    }

    return {
        "schema_version": 1,
        "issue": 66,
        "phase": "C-2",
        "status": "STAGE14_CONFLICT_ONLY_RECIPROCAL_AB_REUSED_DATA_NO_PNL",
        "primary_gate_pass": primary,
        "inherited_b7_numeric_metrics_preserved": numeric_preserved,
        "other_conflict_families_remain_zero": other_zero,
        "parent_b7_conflict": parent_conflict,
        "variant_c2_conflict": variant_conflict,
        "parent_b7_persistence": {
            "agreements": parent_persistence["agreements"],
            "mismatch_bars": parent_persistence["mismatch_bars"],
            "state_carry_share": parent_persistence["state_carry_share_of_formal_mismatch"],
        },
        "variant_c2_persistence": {
            "agreements": variant_persistence["agreements"],
            "mismatch_bars": variant_persistence["mismatch_bars"],
            "state_carry_share": variant_persistence["state_carry_share_of_formal_mismatch"],
            "all_original_replays_exact": variant_persistence["all_original_replays_exact"],
        },
        "downstream_observations": downstream,
        "numeric_parent_aggregate": pnum,
        "numeric_variant_aggregate": vnum,
    }


def pct(x: float) -> str:
    return f"{x * 100.0:.2f}%"


def render_markdown(r: dict[str, Any]) -> str:
    p = r["parent_b7_conflict"]
    v = r["variant_c2_conflict"]
    d = r["downstream_observations"]
    lines = [
        "# Issue #66 Phase C-2 — Stage 1/4 Candidate-Conflict Symmetry Repair A/B",
        "",
        "Status: **reused frozen data / no PnL**",
        "",
        f"Primary Stage 1/4 conflict gate: **{'PASS' if r['primary_gate_pass'] else 'FAIL'}**",
        "",
        "Only the Stage-1 candidate-conflict clause differs from accepted B-7; Stage 4 is the frozen canonical mirror source.",
        "",
        "## Primary conflict layer",
        "",
        "| Metric | B-7 | C-2 |",
        "|---|---:|---:|",
        f"| Candidate-conflict mirror agreement | {pct(p['candidate_conflict_mirror_agreement'])} | {pct(v['candidate_conflict_mirror_agreement'])} |",
        f"| Total conflict mismatch bars | {p['total_conflict_mismatch_bars']} | {v['total_conflict_mismatch_bars']} |",
        f"| Stage 1↔4 attributable mismatch bars | {p['families']['stage1_4']['conflict_mismatch_bars']} | {v['families']['stage1_4']['conflict_mismatch_bars']} |",
        f"| Stage 2↔5 attributable mismatch bars | {p['families']['stage2_5']['conflict_mismatch_bars']} | {v['families']['stage2_5']['conflict_mismatch_bars']} |",
        f"| Stage 3↔6 attributable mismatch bars | {p['families']['stage3_6']['conflict_mismatch_bars']} | {v['families']['stage3_6']['conflict_mismatch_bars']} |",
        "",
        "## Frozen invariants",
        "",
        f"B-7 registered numeric classifier metrics preserved: **{'YES' if r['inherited_b7_numeric_metrics_preserved'] else 'NO'}**  ",
        f"Stage 2/5 and 3/6 conflict mismatch remain zero: **{'YES' if r['other_conflict_families_remain_zero'] else 'NO'}**  ",
        f"Actual Issue #57 persistence replay still exact under C-2: **{'YES' if r['variant_c2_persistence']['all_original_replays_exact'] else 'NO'}**",
        "",
        "## Downstream observations (not tuning targets)",
        "",
        "| Metric | B-7 | C-2 | Gain |",
        "|---|---:|---:|---:|",
    ]
    labels = {
        "candidate_conflict": "Candidate conflict mirror",
        "strong_stage": "Strong-stage mirror",
        "candidate_display": "Candidate-display mirror",
        "formal": "Formal mirror",
        "formal_transition": "Formal transition mirror",
        "stale_pressure_reason": "Stale-pressure reason mirror",
        "stale_pressure_bars": "Stale-pressure bars mirror",
    }
    for key in (
        "candidate_conflict", "strong_stage", "candidate_display", "formal",
        "formal_transition", "stale_pressure_reason", "stale_pressure_bars",
    ):
        node = d[key]
        lines.append(f"| {labels[key]} | {pct(node['b7'])} | {pct(node['c2'])} | {pct(node['gain'])} |")
    lines += [
        "",
        f"Formal mismatch bars: {r['parent_b7_persistence']['mismatch_bars']['formal']} → {r['variant_c2_persistence']['mismatch_bars']['formal']}  ",
        f"Strong-stage mismatch bars: {r['parent_b7_persistence']['mismatch_bars']['strong_stage']} → {r['variant_c2_persistence']['mismatch_bars']['strong_stage']}  ",
        f"Formal state-carry share: {pct(r['parent_b7_persistence']['state_carry_share'])} → {pct(r['variant_c2_persistence']['state_carry_share'])}",
        "",
        "Downstream results may not be used to retune C-2.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description="Issue #66 Phase C-2 Stage1/4 conflict A/B")
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
        "inherited_b7_numeric_metrics_preserved": report["inherited_b7_numeric_metrics_preserved"],
        "parent_conflict": report["parent_b7_conflict"],
        "variant_conflict": report["variant_c2_conflict"],
        "downstream_observations": report["downstream_observations"],
    }, indent=2))


if __name__ == "__main__":
    main()
