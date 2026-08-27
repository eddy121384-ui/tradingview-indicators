#!/usr/bin/env python3
"""Issue #66 Phase C: localize Candidate→Formal reciprocal mismatch. No PnL.

This is a diagnostic-only phase on the accepted B-7 core. It does not modify
classifier formulas or persistence. Counterfactual replays are used only to
localize amplification mechanisms.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

import diagnose_issue66_reciprocal_symmetry as phasea
from generate_issue66_phase_b7_stage14_gate_core import load_phase_b7_namespace


HERE = Path(__file__).resolve().parent
MIRROR = phasea.STAGE_MIRROR


def arr_float(model, key: str) -> np.ndarray:
    return phasea.arr_float(model, key)


def arr_bool(model, key: str) -> np.ndarray:
    return phasea.arr_bool(model, key)


def arr_int(model, key: str) -> np.ndarray:
    return phasea.arr_int(model, key)


def mirror_stage(ids: np.ndarray) -> np.ndarray:
    return MIRROR[np.clip(ids.astype(int), 0, 6)]


def mismatch_stage(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    return mirror_stage(left) != right


def mismatch_bool(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    return left.astype(bool) != right.astype(bool)


def mismatch_int(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    return left.astype(int) != right.astype(int)


def episodes(mask: np.ndarray) -> dict[str, float | int]:
    mask = mask.astype(bool)
    lengths: list[int] = []
    run = 0
    for value in mask:
        if value:
            run += 1
        elif run:
            lengths.append(run)
            run = 0
    if run:
        lengths.append(run)
    return {
        "mismatch_bars": int(np.sum(mask)),
        "episodes": int(len(lengths)),
        "mean_episode_bars": float(np.mean(lengths)) if lengths else 0.0,
        "max_episode_bars": int(max(lengths)) if lengths else 0,
    }


def replay_formal(
    strong_stage: np.ndarray,
    chaos: np.ndarray,
    active_confirm_bars: np.ndarray,
    confirm_bars: int,
    *,
    immediate_confirm: bool = False,
    immediate_chaos_reset: bool = False,
    retain_confirmed: bool = True,
) -> np.ndarray:
    """Replay the generic B-7 inertia shell under diagnostic switches."""
    n = len(strong_stage)
    formal = np.zeros(n, dtype=int)
    confirmed = 0
    candidate = 0
    candidate_bars = 0
    no_regime_bars = 0

    for i in range(n):
        raw_id = int(strong_stage[i])
        if raw_id != 0:
            no_regime_bars = 0
            if raw_id == candidate:
                candidate_bars += 1
            else:
                candidate = raw_id
                candidate_bars = 1

            if immediate_confirm or candidate_bars >= int(active_confirm_bars[i]):
                confirmed = candidate
                current_confirmed = candidate
            else:
                current_confirmed = 0

            formal[i] = confirmed if retain_confirmed else current_confirmed
        else:
            candidate = 0
            candidate_bars = 0
            if not retain_confirmed:
                confirmed = 0
                no_regime_bars = 0
                formal[i] = 0
                continue

            if chaos[i]:
                no_regime_bars += 1
                if immediate_chaos_reset or no_regime_bars >= confirm_bars:
                    confirmed = 0
            else:
                no_regime_bars = 0
            formal[i] = confirmed

    return formal


def stage_agreement(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.mean(~mismatch_stage(left, right))) if len(left) else 1.0


def bool_agreement(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.mean(left == right)) if len(left) else 1.0


def int_agreement(left: np.ndarray, right: np.ndarray) -> float:
    return float(np.mean(left == right)) if len(left) else 1.0


def load_pair(frame) -> tuple[Any, Any, Any, int]:
    ns = load_phase_b7_namespace()
    cfg = ns["PriceOnlyConfig"]()
    compute = ns["compute_price_only"]
    model = compute(frame.copy(), cfg)
    inverse = compute(phasea.reciprocal_ohlc(frame), cfg)
    warmup = int(cfg.rank_len - 1)
    return model, inverse, cfg, warmup


def analyze_pair(frame) -> dict[str, Any]:
    model, inverse, cfg, warmup = load_pair(frame)
    sl = slice(warmup, None)

    top = arr_int(model, "top_id")[sl]
    inv_top = arr_int(inverse, "top_id")[sl]
    top_mismatch = mismatch_stage(top, inv_top)

    prob_acc = arr_float(model, "prob_acc")[sl]
    inv_prob_acc = arr_float(inverse, "prob_acc")[sl]
    has_sharp = np.isfinite(prob_acc)
    inv_has_sharp = np.isfinite(inv_prob_acc)

    top_value = arr_float(model, "top_value")[sl]
    inv_top_value = arr_float(inverse, "top_value")[sl]
    dominant_pass = np.isfinite(top_value) & (top_value >= cfg.dominant_min)
    inv_dominant_pass = np.isfinite(inv_top_value) & (inv_top_value >= cfg.dominant_min)

    top_gap = arr_float(model, "top_gap")[sl]
    inv_top_gap = arr_float(inverse, "top_gap")[sl]
    gap_pass = np.isfinite(top_gap) & (top_gap >= cfg.top_gap_min)
    inv_gap_pass = np.isfinite(inv_top_gap) & (inv_top_gap >= cfg.top_gap_min)

    evidence = arr_float(model, "evidence_strength")[sl]
    inv_evidence = arr_float(inverse, "evidence_strength")[sl]
    evidence_pass = np.isfinite(evidence) & (evidence >= cfg.evidence_min)
    inv_evidence_pass = np.isfinite(inv_evidence) & (inv_evidence >= cfg.evidence_min)

    conflict = arr_bool(model, "candidate_conflict")[sl]
    inv_conflict = arr_bool(inverse, "candidate_conflict")[sl]
    strong = arr_bool(model, "strong_candidate")[sl]
    inv_strong = arr_bool(inverse, "strong_candidate")[sl]
    weak = arr_bool(model, "weak_candidate")[sl]
    inv_weak = arr_bool(inverse, "weak_candidate")[sl]
    chaos = arr_bool(model, "chaos")[sl]
    inv_chaos = arr_bool(inverse, "chaos")[sl]
    coexist = arr_bool(model, "coexist")[sl]
    inv_coexist = arr_bool(inverse, "coexist")[sl]
    fast = arr_bool(model, "fast_switch")[sl]
    inv_fast = arr_bool(inverse, "fast_switch")[sl]

    active_confirm = np.where(fast, cfg.fast_switch_confirm_bars, cfg.confirm_bars).astype(int)
    inv_active_confirm = np.where(inv_fast, cfg.fast_switch_confirm_bars, cfg.confirm_bars).astype(int)

    strong_stage = np.where(strong, top, 0).astype(int)
    inv_strong_stage = np.where(inv_strong, inv_top, 0).astype(int)
    strong_stage_mismatch = mismatch_stage(strong_stage, inv_strong_stage)

    candidate_display = arr_int(model, "candidate_display_id")[sl]
    inv_candidate_display = arr_int(inverse, "candidate_display_id")[sl]
    candidate_mismatch = mismatch_stage(candidate_display, inv_candidate_display)

    formal = arr_int(model, "formal_id")[sl]
    inv_formal = arr_int(inverse, "formal_id")[sl]
    formal_mismatch = mismatch_stage(formal, inv_formal)

    candidate_id = arr_int(model, "candidate_id")[sl]
    inv_candidate_id = arr_int(inverse, "candidate_id")[sl]
    candidate_bars = arr_int(model, "candidate_bars")[sl]
    inv_candidate_bars = arr_int(inverse, "candidate_bars")[sl]

    component_masks = {
        "top_stage": top_mismatch,
        "has_sharp": mismatch_bool(has_sharp, inv_has_sharp),
        "dominant_threshold": mismatch_bool(dominant_pass, inv_dominant_pass),
        "top_gap_threshold": mismatch_bool(gap_pass, inv_gap_pass),
        "evidence_threshold": mismatch_bool(evidence_pass, inv_evidence_pass),
        "candidate_conflict": mismatch_bool(conflict, inv_conflict),
    }
    explained = np.zeros(len(top), dtype=bool)
    for mask in component_masks.values():
        explained |= mask
    unexplained_strong_stage = strong_stage_mismatch & ~explained

    current_loop_input_mismatch = (
        strong_stage_mismatch
        | mismatch_bool(chaos, inv_chaos)
        | mismatch_int(active_confirm, inv_active_confirm)
    )
    state_carry_formal = formal_mismatch & ~current_loop_input_mismatch

    # Replays must use only current B-7 outputs. They are diagnostic probes.
    original_replay = replay_formal(strong_stage, chaos, active_confirm, int(cfg.confirm_bars))
    inv_original_replay = replay_formal(inv_strong_stage, inv_chaos, inv_active_confirm, int(cfg.confirm_bars))

    fixed_confirm = np.full(len(top), int(cfg.confirm_bars), dtype=int)
    fixed_replay = replay_formal(strong_stage, chaos, fixed_confirm, int(cfg.confirm_bars))
    inv_fixed_replay = replay_formal(inv_strong_stage, inv_chaos, fixed_confirm, int(cfg.confirm_bars))

    no_confirmation = replay_formal(
        strong_stage, chaos, active_confirm, int(cfg.confirm_bars), immediate_confirm=True
    )
    inv_no_confirmation = replay_formal(
        inv_strong_stage, inv_chaos, inv_active_confirm, int(cfg.confirm_bars), immediate_confirm=True
    )

    immediate_chaos = replay_formal(
        strong_stage, chaos, active_confirm, int(cfg.confirm_bars), immediate_chaos_reset=True
    )
    inv_immediate_chaos = replay_formal(
        inv_strong_stage, inv_chaos, inv_active_confirm, int(cfg.confirm_bars), immediate_chaos_reset=True
    )

    confirmation_only = replay_formal(
        strong_stage, chaos, active_confirm, int(cfg.confirm_bars), retain_confirmed=False
    )
    inv_confirmation_only = replay_formal(
        inv_strong_stage, inv_chaos, inv_active_confirm, int(cfg.confirm_bars), retain_confirmed=False
    )

    stateless = strong_stage.copy()
    inv_stateless = inv_strong_stage.copy()

    replay_exact = bool(np.array_equal(original_replay, formal) and np.array_equal(inv_original_replay, inv_formal))

    attribution: dict[str, Any] = {}
    for name, mask in component_masks.items():
        overlap = strong_stage_mismatch & mask
        attribution[name] = {
            "component_mismatch_bars": int(np.sum(mask)),
            "strong_stage_mismatch_overlap": int(np.sum(overlap)),
            "share_of_strong_stage_mismatch": (
                float(np.sum(overlap) / np.sum(strong_stage_mismatch)) if np.any(strong_stage_mismatch) else 0.0
            ),
        }
    attribution["unexplained"] = {
        "strong_stage_mismatch_overlap": int(np.sum(unexplained_strong_stage)),
        "share_of_strong_stage_mismatch": (
            float(np.sum(unexplained_strong_stage) / np.sum(strong_stage_mismatch)) if np.any(strong_stage_mismatch) else 0.0
        ),
    }

    return {
        "bars": int(len(top)),
        "agreements": {
            "top_stage": stage_agreement(top, inv_top),
            "has_sharp": bool_agreement(has_sharp, inv_has_sharp),
            "dominant_threshold": bool_agreement(dominant_pass, inv_dominant_pass),
            "top_gap_threshold": bool_agreement(gap_pass, inv_gap_pass),
            "evidence_threshold": bool_agreement(evidence_pass, inv_evidence_pass),
            "candidate_conflict": bool_agreement(conflict, inv_conflict),
            "strong_candidate": bool_agreement(strong, inv_strong),
            "weak_candidate": bool_agreement(weak, inv_weak),
            "strong_stage": stage_agreement(strong_stage, inv_strong_stage),
            "candidate_display": stage_agreement(candidate_display, inv_candidate_display),
            "chaos": bool_agreement(chaos, inv_chaos),
            "coexist": bool_agreement(coexist, inv_coexist),
            "fast_switch": bool_agreement(fast, inv_fast),
            "active_confirm_bars": int_agreement(active_confirm, inv_active_confirm),
            "candidate_id": stage_agreement(candidate_id, inv_candidate_id),
            "candidate_bars": int_agreement(candidate_bars, inv_candidate_bars),
            "formal": stage_agreement(formal, inv_formal),
        },
        "evidence_strength_mae": float(np.nanmean(np.abs(evidence - inv_evidence))),
        "attribution": attribution,
        "episodes": {
            "candidate_display": episodes(candidate_mismatch),
            "strong_stage": episodes(strong_stage_mismatch),
            "formal": episodes(formal_mismatch),
        },
        "formal_state_carry": {
            "formal_mismatch_bars": int(np.sum(formal_mismatch)),
            "current_loop_input_mismatch_bars": int(np.sum(current_loop_input_mismatch)),
            "formal_mismatch_with_current_inputs_mirrored": int(np.sum(state_carry_formal)),
            "state_carry_share_of_formal_mismatch": (
                float(np.sum(state_carry_formal) / np.sum(formal_mismatch)) if np.any(formal_mismatch) else 0.0
            ),
            "formal_to_strong_stage_mismatch_amplification": (
                float(np.sum(formal_mismatch) / np.sum(strong_stage_mismatch))
                if np.any(strong_stage_mismatch)
                else (0.0 if not np.any(formal_mismatch) else float("inf"))
            ),
        },
        "replay_exact": replay_exact,
        "counterfactual_agreements": {
            "original": stage_agreement(original_replay, inv_original_replay),
            "fixed_confirm_no_fast_shortening": stage_agreement(fixed_replay, inv_fixed_replay),
            "no_confirmation_window": stage_agreement(no_confirmation, inv_no_confirmation),
            "immediate_chaos_reset": stage_agreement(immediate_chaos, inv_immediate_chaos),
            "confirmation_only_no_retained_regime": stage_agreement(confirmation_only, inv_confirmation_only),
            "stateless_strong_stage": stage_agreement(stateless, inv_stateless),
        },
    }


def weighted_agreement(pairs: dict[str, Any], key: str) -> float:
    total = sum(row["bars"] for row in pairs.values())
    if not total:
        return 1.0
    matched = sum(row["agreements"][key] * row["bars"] for row in pairs.values())
    return float(matched / total)


def weighted_counterfactual(pairs: dict[str, Any], key: str) -> float:
    total = sum(row["bars"] for row in pairs.values())
    if not total:
        return 1.0
    matched = sum(row["counterfactual_agreements"][key] * row["bars"] for row in pairs.values())
    return float(matched / total)


def build_report() -> dict[str, Any]:
    pairs = {name: analyze_pair(frame) for name, frame in phasea.load_frozen_pairs().items()}
    bars = sum(row["bars"] for row in pairs.values())

    agreement_keys = (
        "top_stage", "has_sharp", "dominant_threshold", "top_gap_threshold",
        "evidence_threshold", "candidate_conflict", "strong_candidate", "weak_candidate",
        "strong_stage", "candidate_display", "chaos", "coexist", "fast_switch",
        "active_confirm_bars", "candidate_id", "candidate_bars", "formal",
    )
    agreements = {key: weighted_agreement(pairs, key) for key in agreement_keys}

    replay_keys = (
        "original", "fixed_confirm_no_fast_shortening", "no_confirmation_window",
        "immediate_chaos_reset", "confirmation_only_no_retained_regime", "stateless_strong_stage",
    )
    counterfactual = {key: weighted_counterfactual(pairs, key) for key in replay_keys}

    strong_mismatch_total = sum(row["episodes"]["strong_stage"]["mismatch_bars"] for row in pairs.values())
    formal_mismatch_total = sum(row["episodes"]["formal"]["mismatch_bars"] for row in pairs.values())
    candidate_mismatch_total = sum(row["episodes"]["candidate_display"]["mismatch_bars"] for row in pairs.values())
    state_carry_total = sum(
        row["formal_state_carry"]["formal_mismatch_with_current_inputs_mirrored"] for row in pairs.values()
    )

    attribution: dict[str, Any] = {}
    for name in (
        "top_stage", "has_sharp", "dominant_threshold", "top_gap_threshold",
        "evidence_threshold", "candidate_conflict", "unexplained",
    ):
        overlap = sum(row["attribution"][name]["strong_stage_mismatch_overlap"] for row in pairs.values())
        attribution[name] = {
            "strong_stage_mismatch_overlap": int(overlap),
            "share_of_strong_stage_mismatch": float(overlap / strong_mismatch_total) if strong_mismatch_total else 0.0,
        }

    ranked_causes = sorted(
        (name for name in attribution if name != "unexplained"),
        key=lambda name: attribution[name]["strong_stage_mismatch_overlap"],
        reverse=True,
    )
    ranked_probes = sorted(
        (key for key in counterfactual if key != "original"),
        key=lambda key: counterfactual[key] - counterfactual["original"],
        reverse=True,
    )

    return {
        "schema_version": 1,
        "issue": 66,
        "phase": "C",
        "status": "PERSISTENCE_LOCALIZATION_REUSED_DATA_NO_PNL_NO_FORMULA_CHANGE",
        "bars": int(bars),
        "all_original_replays_exact": bool(all(row["replay_exact"] for row in pairs.values())),
        "agreements": agreements,
        "mismatch_bars": {
            "candidate_display": int(candidate_mismatch_total),
            "strong_stage": int(strong_mismatch_total),
            "formal": int(formal_mismatch_total),
        },
        "formal_mismatch_amplification": (
            float(formal_mismatch_total / strong_mismatch_total)
            if strong_mismatch_total
            else (0.0 if not formal_mismatch_total else float("inf"))
        ),
        "state_carry_formal_mismatch_bars": int(state_carry_total),
        "state_carry_share_of_formal_mismatch": (
            float(state_carry_total / formal_mismatch_total) if formal_mismatch_total else 0.0
        ),
        "strong_stage_mismatch_attribution": attribution,
        "ranked_current_bar_causes": ranked_causes,
        "counterfactual_agreements": counterfactual,
        "counterfactual_gain_vs_original": {
            key: float(value - counterfactual["original"]) for key, value in counterfactual.items() if key != "original"
        },
        "ranked_persistence_probes": ranked_probes,
        "mean_evidence_strength_mae": float(np.mean([row["evidence_strength_mae"] for row in pairs.values()])),
        "pairs": pairs,
    }


def pct(x: float) -> str:
    return f"{x * 100.0:.2f}%"


def render_markdown(r: dict[str, Any]) -> str:
    a = r["agreements"]
    lines = [
        "# Issue #66 Phase C — Candidate→Formal Persistence Localization",
        "",
        "Status: **reused frozen data / no PnL / no formula change**",
        "",
        f"B-7 Candidate display mirror: **{pct(a['candidate_display'])}**  ",
        f"B-7 strong-stage input mirror: **{pct(a['strong_stage'])}**  ",
        f"B-7 Formal mirror: **{pct(a['formal'])}**",
        "",
        "## Current-bar Candidate inputs",
        "",
        "| Input | Mirror agreement |",
        "|---|---:|",
        f"| Top stage | {pct(a['top_stage'])} |",
        f"| Probability valid / has_sharp | {pct(a['has_sharp'])} |",
        f"| Dominant threshold pass | {pct(a['dominant_threshold'])} |",
        f"| Top-gap threshold pass | {pct(a['top_gap_threshold'])} |",
        f"| Evidence threshold pass | {pct(a['evidence_threshold'])} |",
        f"| Candidate conflict | {pct(a['candidate_conflict'])} |",
        f"| Strong-candidate boolean | {pct(a['strong_candidate'])} |",
        f"| Strong-stage id | {pct(a['strong_stage'])} |",
        f"| Chaos | {pct(a['chaos'])} |",
        f"| Fast switch | {pct(a['fast_switch'])} |",
        f"| Active confirmation bars | {pct(a['active_confirm_bars'])} |",
        "",
        f"Mean evidence-strength reciprocal MAE: **{r['mean_evidence_strength_mae']:.6f}**",
        "",
        "### Strong-stage mismatch attribution (overlap, not mutually exclusive)",
        "",
        "| Rank | Current-bar cause | Mismatch overlap | Share of strong-stage mismatches |",
        "|---:|---|---:|---:|",
    ]
    labels = {
        "top_stage": "Top-stage mismatch",
        "has_sharp": "Probability-valid mismatch",
        "dominant_threshold": "Dominant-threshold mismatch",
        "top_gap_threshold": "Top-gap-threshold mismatch",
        "evidence_threshold": "Evidence-threshold mismatch",
        "candidate_conflict": "Candidate-conflict mismatch",
    }
    for rank, key in enumerate(r["ranked_current_bar_causes"], start=1):
        node = r["strong_stage_mismatch_attribution"][key]
        lines.append(
            f"| {rank} | {labels[key]} | {node['strong_stage_mismatch_overlap']} | {pct(node['share_of_strong_stage_mismatch'])} |"
        )
    unexplained = r["strong_stage_mismatch_attribution"]["unexplained"]
    lines += [
        "",
        f"Unexplained strong-stage mismatch bars: **{unexplained['strong_stage_mismatch_overlap']}**.",
        "",
        "## Persistence amplification",
        "",
        f"Candidate-display mismatch bars: **{r['mismatch_bars']['candidate_display']}**  ",
        f"Strong-stage input mismatch bars: **{r['mismatch_bars']['strong_stage']}**  ",
        f"Formal mismatch bars: **{r['mismatch_bars']['formal']}**  ",
        f"Formal / strong-stage mismatch amplification: **{r['formal_mismatch_amplification']:.2f}×**  ",
        f"Formal mismatch bars with current loop inputs already mirrored: **{r['state_carry_formal_mismatch_bars']}** ({pct(r['state_carry_share_of_formal_mismatch'])})",
        "",
        "## Counterfactual replay localization (diagnostic only)",
        "",
        f"Original replay reproduces stored Formal exactly: **{'YES' if r['all_original_replays_exact'] else 'NO'}**",
        "",
        "| Replay | Formal mirror | Gain vs original |",
        "|---|---:|---:|",
    ]
    replay_labels = {
        "original": "Original inertia loop",
        "fixed_confirm_no_fast_shortening": "Fixed confirm (no fast shortening)",
        "no_confirmation_window": "No confirmation window",
        "immediate_chaos_reset": "Immediate chaos reset",
        "confirmation_only_no_retained_regime": "Confirmation only / no retained regime",
        "stateless_strong_stage": "Stateless strong-stage",
    }
    for key in ("original",) + tuple(r["ranked_persistence_probes"]):
        value = r["counterfactual_agreements"][key]
        gain = 0.0 if key == "original" else r["counterfactual_gain_vs_original"][key]
        lines.append(f"| {replay_labels[key]} | {pct(value)} | {pct(gain)} |")

    lines += [
        "",
        "## Interpretation boundary",
        "",
        "Counterfactual replays do **not** authorize changing confirmation or persistence. If the generic loop is structurally symmetric under exact mirrored inputs, repair remaining current-bar Candidate inputs before changing the loop itself.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description="Issue #66 Phase C Candidate→Formal localization")
    ap.add_argument("--json", type=Path, required=True)
    ap.add_argument("--markdown", type=Path, required=True)
    args = ap.parse_args()
    report = build_report()
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.markdown.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({
        "all_original_replays_exact": report["all_original_replays_exact"],
        "agreements": report["agreements"],
        "mismatch_bars": report["mismatch_bars"],
        "formal_mismatch_amplification": report["formal_mismatch_amplification"],
        "state_carry_share_of_formal_mismatch": report["state_carry_share_of_formal_mismatch"],
        "ranked_current_bar_causes": report["ranked_current_bar_causes"],
        "counterfactual_agreements": report["counterfactual_agreements"],
    }, indent=2))


if __name__ == "__main__":
    main()
