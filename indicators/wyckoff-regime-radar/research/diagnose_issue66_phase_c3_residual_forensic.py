#!/usr/bin/env python3
"""Issue #66 Phase C-3: forensic of residual C-2 strong/Formal mismatches. No PnL."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

import diagnose_issue66_phase_c2_stage14_conflict as c2diag
import diagnose_issue66_phase_c_persistence_localization_v3 as cdiag
from generate_issue66_phase_c2_stage14_conflict_core import load_phase_c2_namespace


HERE = Path(__file__).resolve().parent


def _finite_stats(values: list[float]) -> dict[str, float | int | None]:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if not len(arr):
        return {"n": 0, "mean": None, "median": None, "max": None, "p90": None}
    return {
        "n": int(len(arr)),
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "max": float(np.max(arr)),
        "p90": float(np.quantile(arr, 0.90)),
    }


def predicate_forensic_pair(frame) -> dict[str, Any]:
    model, inverse, cfg, warmup = c2diag.load_pair_with_loader(frame, load_phase_c2_namespace)
    top = cdiag.v1.arr_int(model, "top_id")[warmup:]
    inv_top = cdiag.v1.arr_int(inverse, "top_id")[warmup:]
    conflict = cdiag.v1.arr_bool(model, "candidate_conflict")[warmup:]
    inv_conflict = cdiag.v1.arr_bool(inverse, "candidate_conflict")[warmup:]

    res_hold = cdiag.v1.arr_float(model, "resistance_holding")[warmup:]
    sup_hold = cdiag.v1.arr_float(model, "support_holding")[warmup:]
    up_exh = cdiag.v1.arr_float(model, "upside_exhaustion")[warmup:]
    dn_exh = cdiag.v1.arr_float(model, "downside_exhaustion")[warmup:]

    inv_res_hold = cdiag.v1.arr_float(inverse, "resistance_holding")[warmup:]
    inv_sup_hold = cdiag.v1.arr_float(inverse, "support_holding")[warmup:]
    inv_up_exh = cdiag.v1.arr_float(inverse, "upside_exhaustion")[warmup:]
    inv_dn_exh = cdiag.v1.arr_float(inverse, "downside_exhaustion")[warmup:]

    top_mirrored = cdiag.v1.mirror_stage(top) == inv_top
    family14 = np.isin(top, [1, 4])
    residual = top_mirrored & family14 & (conflict != inv_conflict)

    holding_mismatch = np.zeros(len(top), dtype=bool)
    exhaustion_mismatch = np.zeros(len(top), dtype=bool)
    holding_left_margins: list[float] = []
    holding_right_margins: list[float] = []
    exhaustion_left_margins: list[float] = []
    exhaustion_right_margins: list[float] = []

    threshold = float(cfg.absorb_threshold)
    indices = np.flatnonzero(residual)
    for i in indices:
        if top[i] == 1:
            lh, rh = res_hold[i], inv_sup_hold[i]
            le, re = up_exh[i], inv_dn_exh[i]
        else:  # left Stage 4 mirrors inverse Stage 1
            lh, rh = sup_hold[i], inv_res_hold[i]
            le, re = dn_exh[i], inv_up_exh[i]

        hm = bool((lh >= threshold) != (rh >= threshold))
        em = bool((le >= threshold) != (re >= threshold))
        holding_mismatch[i] = hm
        exhaustion_mismatch[i] = em
        if hm:
            holding_left_margins.append(abs(float(lh) - threshold))
            holding_right_margins.append(abs(float(rh) - threshold))
        if em:
            exhaustion_left_margins.append(abs(float(le) - threshold))
            exhaustion_right_margins.append(abs(float(re) - threshold))

    # The C-2 Stage1/4 clauses are syntactically mirrored and contain exactly
    # holding, exhaustion, and the mirrored continuation override. If final
    # conflict differs while holding/exhaustion truth values match, the remaining
    # predicate difference must be in the continuation override path.
    inferred_override_only = residual & ~holding_mismatch & ~exhaustion_mismatch

    return {
        "residual_stage14_conflict_mismatch_bars": int(np.sum(residual)),
        "holding_predicate_mismatch_bars": int(np.sum(residual & holding_mismatch)),
        "exhaustion_predicate_mismatch_bars": int(np.sum(residual & exhaustion_mismatch)),
        "holding_and_exhaustion_both_mismatch": int(np.sum(residual & holding_mismatch & exhaustion_mismatch)),
        "inferred_continuation_override_only_bars": int(np.sum(inferred_override_only)),
        "holding_left_threshold_distance": _finite_stats(holding_left_margins),
        "holding_right_threshold_distance": _finite_stats(holding_right_margins),
        "exhaustion_left_threshold_distance": _finite_stats(exhaustion_left_margins),
        "exhaustion_right_threshold_distance": _finite_stats(exhaustion_right_margins),
    }


def build_report() -> dict[str, Any]:
    persistence = c2diag.persistence_with_loader(load_phase_c2_namespace)
    pairs = cdiag.v1.phasea.load_frozen_pairs()
    predicate_pairs = {name: predicate_forensic_pair(frame) for name, frame in pairs.items()}

    # Current-bar strong-stage attribution is already computed by the exact
    # Phase-C v3 machinery, now injected with the C-2 core.
    attribution = persistence["strong_stage_mismatch_attribution"]
    ranked_causes = persistence["ranked_current_bar_causes"]

    pred_totals = {
        "residual_stage14_conflict_mismatch_bars": 0,
        "holding_predicate_mismatch_bars": 0,
        "exhaustion_predicate_mismatch_bars": 0,
        "holding_and_exhaustion_both_mismatch": 0,
        "inferred_continuation_override_only_bars": 0,
    }
    margin_buckets: dict[str, list[float]] = {
        "holding_left": [], "holding_right": [], "exhaustion_left": [], "exhaustion_right": []
    }

    # Recollect raw threshold distances so aggregate stats are not averages of averages.
    for name, frame in pairs.items():
        row = predicate_pairs[name]
        for key in pred_totals:
            pred_totals[key] += int(row[key])

        model, inverse, cfg, warmup = c2diag.load_pair_with_loader(frame, load_phase_c2_namespace)
        top = cdiag.v1.arr_int(model, "top_id")[warmup:]
        inv_top = cdiag.v1.arr_int(inverse, "top_id")[warmup:]
        conflict = cdiag.v1.arr_bool(model, "candidate_conflict")[warmup:]
        inv_conflict = cdiag.v1.arr_bool(inverse, "candidate_conflict")[warmup:]
        res_hold = cdiag.v1.arr_float(model, "resistance_holding")[warmup:]
        sup_hold = cdiag.v1.arr_float(model, "support_holding")[warmup:]
        up_exh = cdiag.v1.arr_float(model, "upside_exhaustion")[warmup:]
        dn_exh = cdiag.v1.arr_float(model, "downside_exhaustion")[warmup:]
        inv_res_hold = cdiag.v1.arr_float(inverse, "resistance_holding")[warmup:]
        inv_sup_hold = cdiag.v1.arr_float(inverse, "support_holding")[warmup:]
        inv_up_exh = cdiag.v1.arr_float(inverse, "upside_exhaustion")[warmup:]
        inv_dn_exh = cdiag.v1.arr_float(inverse, "downside_exhaustion")[warmup:]
        residual = (cdiag.v1.mirror_stage(top) == inv_top) & np.isin(top, [1, 4]) & (conflict != inv_conflict)
        threshold = float(cfg.absorb_threshold)
        for i in np.flatnonzero(residual):
            if top[i] == 1:
                lh, rh, le, re = res_hold[i], inv_sup_hold[i], up_exh[i], inv_dn_exh[i]
            else:
                lh, rh, le, re = sup_hold[i], inv_res_hold[i], dn_exh[i], inv_up_exh[i]
            if bool((lh >= threshold) != (rh >= threshold)):
                margin_buckets["holding_left"].append(abs(float(lh) - threshold))
                margin_buckets["holding_right"].append(abs(float(rh) - threshold))
            if bool((le >= threshold) != (re >= threshold)):
                margin_buckets["exhaustion_left"].append(abs(float(le) - threshold))
                margin_buckets["exhaustion_right"].append(abs(float(re) - threshold))

    formal_by_pair = {
        name: {
            "formal_mismatch_bars": int(row["episodes"]["formal"]["mismatch_bars"]),
            "formal_mismatch_episodes": int(row["episodes"]["formal"]["episodes"]),
            "formal_mean_episode_bars": float(row["episodes"]["formal"]["mean_episode_bars"]),
            "formal_max_episode_bars": int(row["episodes"]["formal"]["max_episode_bars"]),
            "state_carry_share": float(row["formal_state_carry"]["state_carry_share_of_formal_mismatch"]),
        }
        for name, row in persistence["pairs"].items()
    }

    return {
        "schema_version": 1,
        "issue": 66,
        "phase": "C-3",
        "status": "RESIDUAL_FORENSIC_REUSED_DATA_NO_PNL_NO_FORMULA_CHANGE",
        "c2_exact_persistence_replay": bool(persistence["all_original_replays_exact"]),
        "agreements": persistence["agreements"],
        "mismatch_bars": persistence["mismatch_bars"],
        "strong_stage_mismatch_attribution": attribution,
        "ranked_current_bar_causes": ranked_causes,
        "stage14_conflict_predicate_forensic": {
            **pred_totals,
            "holding_left_threshold_distance": _finite_stats(margin_buckets["holding_left"]),
            "holding_right_threshold_distance": _finite_stats(margin_buckets["holding_right"]),
            "exhaustion_left_threshold_distance": _finite_stats(margin_buckets["exhaustion_left"]),
            "exhaustion_right_threshold_distance": _finite_stats(margin_buckets["exhaustion_right"]),
        },
        "formal_residual": {
            "by_pair": formal_by_pair,
            "state_carry_formal_mismatch_bars": int(persistence["state_carry_formal_mismatch_bars"]),
            "state_carry_share_of_formal_mismatch": float(persistence["state_carry_share_of_formal_mismatch"]),
            "stale_pressure_reason_mirror": float(persistence["agreements"]["stale_pressure_reason"]),
            "stale_pressure_bars_mirror": float(persistence["agreements"]["stale_pressure_bars"]),
        },
        "predicate_pairs": predicate_pairs,
    }


def pct(x: float) -> str:
    return f"{x * 100.0:.2f}%"


def nfmt(x: float | None) -> str:
    return "n/a" if x is None else f"{x:.6f}"


def render_markdown(r: dict[str, Any]) -> str:
    a = r["agreements"]
    attr = r["strong_stage_mismatch_attribution"]
    pred = r["stage14_conflict_predicate_forensic"]
    lines = [
        "# Issue #66 Phase C-3 — Residual Strong/Formal Mismatch Forensic", "",
        "Status: **reused frozen data / no PnL / no formula change**", "",
        f"C-2 persistence exact replay: **{'YES' if r['c2_exact_persistence_replay'] else 'NO'}**", "",
        f"Strong-stage mirror: **{pct(a['strong_stage'])}** ({r['mismatch_bars']['strong_stage']} mismatch bars)  ",
        f"Formal mirror: **{pct(a['formal'])}** ({r['mismatch_bars']['formal']} mismatch bars)  ",
        f"Candidate-display mirror: **{pct(a['candidate_display'])}**", "",
        "## Residual strong-stage attribution", "",
        "| Rank | Cause | Mismatch overlap | Share of strong-stage mismatch |", "|---:|---|---:|---:|",
    ]
    labels = {
        "candidate_conflict": "Candidate conflict",
        "top_stage": "Top-stage / argmax",
        "top_gap_threshold": "Top-gap threshold",
        "evidence_threshold": "Evidence threshold",
        "dominant_threshold": "Dominant threshold",
        "has_sharp": "Probability validity",
    }
    for rank, key in enumerate(r["ranked_current_bar_causes"], 1):
        node = attr[key]
        lines.append(f"| {rank} | {labels[key]} | {node['strong_stage_mismatch_overlap']} | {pct(node['share_of_strong_stage_mismatch'])} |")
    lines += ["", f"Unexplained strong-stage mismatch bars: **{attr['unexplained']['strong_stage_mismatch_overlap']}**.", "",
        "## Stage 1/4 residual conflict predicate forensic", "",
        f"Residual Stage 1/4 conflict mismatch bars with top stage already mirrored: **{pred['residual_stage14_conflict_mismatch_bars']}**", "",
        "| Predicate | Mismatch bars |", "|---|---:|",
        f"| Holding threshold predicate | {pred['holding_predicate_mismatch_bars']} |",
        f"| Exhaustion threshold predicate | {pred['exhaustion_predicate_mismatch_bars']} |",
        f"| Both holding + exhaustion | {pred['holding_and_exhaustion_both_mismatch']} |",
        f"| Inferred continuation-override only | {pred['inferred_continuation_override_only_bars']} |", "",
        "Threshold distance on predicate-mismatch bars (existing absorb threshold; descriptive only):", "",
        "| Margin | Median | P90 | Max |", "|---|---:|---:|---:|",
        f"| Holding left | {nfmt(pred['holding_left_threshold_distance']['median'])} | {nfmt(pred['holding_left_threshold_distance']['p90'])} | {nfmt(pred['holding_left_threshold_distance']['max'])} |",
        f"| Holding inverse | {nfmt(pred['holding_right_threshold_distance']['median'])} | {nfmt(pred['holding_right_threshold_distance']['p90'])} | {nfmt(pred['holding_right_threshold_distance']['max'])} |",
        f"| Exhaustion left | {nfmt(pred['exhaustion_left_threshold_distance']['median'])} | {nfmt(pred['exhaustion_left_threshold_distance']['p90'])} | {nfmt(pred['exhaustion_left_threshold_distance']['max'])} |",
        f"| Exhaustion inverse | {nfmt(pred['exhaustion_right_threshold_distance']['median'])} | {nfmt(pred['exhaustion_right_threshold_distance']['p90'])} | {nfmt(pred['exhaustion_right_threshold_distance']['max'])} |", "",
        "## Formal residual by pair", "",
        "| Pair | Mismatch bars | Episodes | Max episode | State-carry share |", "|---|---:|---:|---:|---:|",
    ]
    for pair, row in r["formal_residual"]["by_pair"].items():
        lines.append(f"| {pair} | {row['formal_mismatch_bars']} | {row['formal_mismatch_episodes']} | {row['formal_max_episode_bars']} | {pct(row['state_carry_share'])} |")
    lines += ["",
        f"Aggregate Formal state-carry share: **{pct(r['formal_residual']['state_carry_share_of_formal_mismatch'])}**  ",
        f"Stale-pressure reason mirror: **{pct(r['formal_residual']['stale_pressure_reason_mirror'])}**  ",
        f"Stale-pressure bars mirror: **{pct(r['formal_residual']['stale_pressure_bars_mirror'])}**", "",
        "## Decision boundary", "",
        "This forensic does not authorize threshold movement. If no explicit non-isomorphic source remains, stop classifier-formula repair and hand off the C-2 core to Phase D Pine↔Python parity.", "",
    ]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description="Issue #66 Phase C-3 residual forensic")
    ap.add_argument("--json", type=Path, required=True)
    ap.add_argument("--markdown", type=Path, required=True)
    args = ap.parse_args()
    report = build_report()
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.markdown.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({
        "c2_exact_persistence_replay": report["c2_exact_persistence_replay"],
        "agreements": report["agreements"],
        "mismatch_bars": report["mismatch_bars"],
        "ranked_current_bar_causes": report["ranked_current_bar_causes"],
        "stage14_conflict_predicate_forensic": report["stage14_conflict_predicate_forensic"],
        "formal_residual": report["formal_residual"],
    }, indent=2))


if __name__ == "__main__":
    main()
