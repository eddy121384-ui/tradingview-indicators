#!/usr/bin/env python3
"""Issue #66 Phase C v3: localize B-7 Candidate→Formal mismatch using the
actual inherited Issue #57 Phase-B stale-pressure persistence state machine.

Diagnostic only. No classifier or persistence formula is changed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

import diagnose_issue66_phase_c_persistence_localization as v1


def replay_phaseb_persistence(
    strong_stage: np.ndarray,
    candidate_display: np.ndarray,
    chaos: np.ndarray,
    coexist: np.ndarray,
    active_confirm_bars: np.ndarray,
    confirm_bars: int,
    *,
    immediate_confirm: bool = False,
    disable_weak_challenger_pressure: bool = False,
    disable_coexist_pressure: bool = False,
    stale_limit_override: int | None = None,
) -> dict[str, np.ndarray]:
    """Exact replay of generate_v06_phase_b_core.NEW_INERTIA_BLOCK.

    Optional switches are diagnostic-only counterfactuals.
    """
    n = len(strong_stage)
    formal = np.zeros(n, dtype=int)
    candidate_series = np.zeros(n, dtype=int)
    candidate_bars_series = np.zeros(n, dtype=int)
    stale_bars_series = np.zeros(n, dtype=int)
    stale_reason_series = np.zeros(n, dtype=int)

    confirmed = 0
    candidate = 0
    candidate_bars = 0
    stale_pressure_bars = 0
    stale_limit = int(stale_limit_override) if stale_limit_override is not None else int(confirm_bars) * 2

    for i in range(n):
        if int(strong_stage[i]) != 0:
            stale_pressure_bars = 0
            stale_reason = 0
            raw_id = int(strong_stage[i])
            if raw_id == candidate:
                candidate_bars += 1
            else:
                candidate = raw_id
                candidate_bars = 1
            if immediate_confirm or candidate_bars >= int(active_confirm_bars[i]):
                confirmed = candidate
        else:
            candidate = 0
            candidate_bars = 0
            display_id = int(candidate_display[i])
            weak_challenger = confirmed != 0 and display_id != 0 and display_id != confirmed
            coexist_pressure = confirmed != 0 and bool(coexist[i]) and display_id == 0

            if bool(chaos[i]) and confirmed != 0:
                stale_reason = 1
            elif weak_challenger and not disable_weak_challenger_pressure:
                stale_reason = 2
            elif coexist_pressure and not disable_coexist_pressure:
                stale_reason = 3
            else:
                stale_reason = 0

            if stale_reason != 0:
                stale_pressure_bars += 1
                if stale_pressure_bars >= stale_limit:
                    confirmed = 0
            else:
                stale_pressure_bars = 0

        formal[i] = confirmed
        candidate_series[i] = candidate
        candidate_bars_series[i] = candidate_bars
        stale_bars_series[i] = stale_pressure_bars
        stale_reason_series[i] = stale_reason

    return {
        "formal": formal,
        "candidate": candidate_series,
        "candidate_bars": candidate_bars_series,
        "stale_bars": stale_bars_series,
        "stale_reason": stale_reason_series,
    }


def _full_inputs(result, cfg) -> dict[str, np.ndarray]:
    top = v1.arr_int(result, "top_id")
    strong = v1.arr_bool(result, "strong_candidate")
    fast = v1.arr_bool(result, "fast_switch")
    return {
        "strong_stage": np.where(strong, top, 0).astype(int),
        "candidate_display": v1.arr_int(result, "candidate_display_id"),
        "chaos": v1.arr_bool(result, "chaos"),
        "coexist": v1.arr_bool(result, "coexist"),
        "active_confirm": np.where(fast, cfg.fast_switch_confirm_bars, cfg.confirm_bars).astype(int),
    }


def _run(inputs: dict[str, np.ndarray], cfg, **kwargs) -> dict[str, np.ndarray]:
    return replay_phaseb_persistence(
        inputs["strong_stage"],
        inputs["candidate_display"],
        inputs["chaos"],
        inputs["coexist"],
        inputs["active_confirm"],
        int(cfg.confirm_bars),
        **kwargs,
    )


def analyze_pair(frame) -> dict[str, Any]:
    # Reuse v1's current-bar Candidate attribution only; replace every persistence
    # replay/state-carry result with the actual inherited Phase-B state machine.
    base = v1.analyze_pair(frame)
    model, inverse, cfg, warmup = v1.load_pair(frame)
    sl = slice(warmup, None)
    left = _full_inputs(model, cfg)
    right = _full_inputs(inverse, cfg)

    stored_left = {
        "formal": v1.arr_int(model, "formal_id"),
        "candidate": v1.arr_int(model, "candidate_id"),
        "candidate_bars": v1.arr_int(model, "candidate_bars"),
        "stale_bars": v1.arr_int(model, "stale_pressure_bars"),
        "stale_reason": v1.arr_int(model, "stale_pressure_reason"),
    }
    stored_right = {
        "formal": v1.arr_int(inverse, "formal_id"),
        "candidate": v1.arr_int(inverse, "candidate_id"),
        "candidate_bars": v1.arr_int(inverse, "candidate_bars"),
        "stale_bars": v1.arr_int(inverse, "stale_pressure_bars"),
        "stale_reason": v1.arr_int(inverse, "stale_pressure_reason"),
    }

    replay_left = _run(left, cfg)
    replay_right = _run(right, cfg)
    exact_fields = {
        key: bool(np.array_equal(replay_left[key], stored_left[key]) and np.array_equal(replay_right[key], stored_right[key]))
        for key in stored_left
    }
    base["replay_exact"] = bool(all(exact_fields.values()))
    base["replay_exact_fields"] = exact_fields

    # Post-warmup current loop inputs and stored outputs.
    ls = {key: value[sl] for key, value in left.items()}
    rs = {key: value[sl] for key, value in right.items()}
    formal = stored_left["formal"][sl]
    inv_formal = stored_right["formal"][sl]
    formal_mismatch = v1.mismatch_stage(formal, inv_formal)

    current_input_masks = {
        "strong_stage": v1.mismatch_stage(ls["strong_stage"], rs["strong_stage"]),
        "candidate_display": v1.mismatch_stage(ls["candidate_display"], rs["candidate_display"]),
        "chaos": v1.mismatch_bool(ls["chaos"], rs["chaos"]),
        "coexist": v1.mismatch_bool(ls["coexist"], rs["coexist"]),
        "active_confirm_bars": v1.mismatch_int(ls["active_confirm"], rs["active_confirm"]),
    }
    any_input_mismatch = np.zeros(len(formal), dtype=bool)
    for mask in current_input_masks.values():
        any_input_mismatch |= mask
    state_carry = formal_mismatch & ~any_input_mismatch

    stale_reason = stored_left["stale_reason"][sl]
    inv_stale_reason = stored_right["stale_reason"][sl]
    stale_bars = stored_left["stale_bars"][sl]
    inv_stale_bars = stored_right["stale_bars"][sl]

    base["agreements"]["stale_pressure_reason"] = v1.int_agreement(stale_reason, inv_stale_reason)
    base["agreements"]["stale_pressure_bars"] = v1.int_agreement(stale_bars, inv_stale_bars)
    base["formal_state_carry"] = {
        "formal_mismatch_bars": int(np.sum(formal_mismatch)),
        "current_loop_input_mismatch_bars": int(np.sum(any_input_mismatch)),
        "formal_mismatch_with_current_inputs_mirrored": int(np.sum(state_carry)),
        "state_carry_share_of_formal_mismatch": float(np.sum(state_carry) / np.sum(formal_mismatch)) if np.any(formal_mismatch) else 0.0,
        "formal_to_strong_stage_mismatch_amplification": (
            float(np.sum(formal_mismatch) / np.sum(current_input_masks["strong_stage"]))
            if np.any(current_input_masks["strong_stage"])
            else (0.0 if not np.any(formal_mismatch) else float("inf"))
        ),
        "current_input_mismatch_bars_by_input": {key: int(np.sum(mask)) for key, mask in current_input_masks.items()},
    }

    # Diagnostic-only counterfactuals. Full history is always replayed; score after warmup.
    fixed_left = dict(left)
    fixed_right = dict(right)
    fixed = np.full(len(left["active_confirm"]), int(cfg.confirm_bars), dtype=int)
    fixed_left["active_confirm"] = fixed
    fixed_right["active_confirm"] = fixed

    probes = {
        "original": (replay_left, replay_right),
        "fixed_confirm_no_fast_shortening": (_run(fixed_left, cfg), _run(fixed_right, cfg)),
        "immediate_strong_confirmation": (_run(left, cfg, immediate_confirm=True), _run(right, cfg, immediate_confirm=True)),
        "chaos_only_stale_pressure": (
            _run(left, cfg, disable_weak_challenger_pressure=True, disable_coexist_pressure=True),
            _run(right, cfg, disable_weak_challenger_pressure=True, disable_coexist_pressure=True),
        ),
        "disable_weak_challenger_pressure": (
            _run(left, cfg, disable_weak_challenger_pressure=True),
            _run(right, cfg, disable_weak_challenger_pressure=True),
        ),
        "disable_coexist_pressure": (
            _run(left, cfg, disable_coexist_pressure=True),
            _run(right, cfg, disable_coexist_pressure=True),
        ),
        "immediate_stale_clear": (
            _run(left, cfg, stale_limit_override=1),
            _run(right, cfg, stale_limit_override=1),
        ),
    }
    counterfactual = {
        name: v1.stage_agreement(pair[0]["formal"][sl], pair[1]["formal"][sl])
        for name, pair in probes.items()
    }
    counterfactual["stateless_strong_stage"] = v1.stage_agreement(ls["strong_stage"], rs["strong_stage"])
    base["counterfactual_agreements"] = counterfactual
    return base


def _weighted(pairs: dict[str, Any], path: tuple[str, ...]) -> float:
    total = sum(row["bars"] for row in pairs.values())
    if total == 0:
        return 1.0
    value = 0.0
    for row in pairs.values():
        node: Any = row
        for key in path:
            node = node[key]
        value += float(node) * row["bars"]
    return float(value / total)


def build_report() -> dict[str, Any]:
    pairs = {name: analyze_pair(frame) for name, frame in v1.phasea.load_frozen_pairs().items()}
    agreement_keys = (
        "top_stage", "has_sharp", "dominant_threshold", "top_gap_threshold", "evidence_threshold",
        "candidate_conflict", "strong_candidate", "weak_candidate", "strong_stage", "candidate_display",
        "chaos", "coexist", "fast_switch", "active_confirm_bars", "candidate_id", "candidate_bars", "formal",
        "stale_pressure_reason", "stale_pressure_bars",
    )
    agreements = {key: _weighted(pairs, ("agreements", key)) for key in agreement_keys}

    strong_total = sum(row["episodes"]["strong_stage"]["mismatch_bars"] for row in pairs.values())
    candidate_total = sum(row["episodes"]["candidate_display"]["mismatch_bars"] for row in pairs.values())
    formal_total = sum(row["episodes"]["formal"]["mismatch_bars"] for row in pairs.values())
    state_carry_total = sum(row["formal_state_carry"]["formal_mismatch_with_current_inputs_mirrored"] for row in pairs.values())

    attribution: dict[str, Any] = {}
    for name in (
        "top_stage", "has_sharp", "dominant_threshold", "top_gap_threshold", "evidence_threshold", "candidate_conflict", "unexplained",
    ):
        overlap = sum(row["attribution"][name]["strong_stage_mismatch_overlap"] for row in pairs.values())
        attribution[name] = {
            "strong_stage_mismatch_overlap": int(overlap),
            "share_of_strong_stage_mismatch": float(overlap / strong_total) if strong_total else 0.0,
        }
    ranked_causes = sorted(
        [key for key in attribution if key != "unexplained"],
        key=lambda key: attribution[key]["strong_stage_mismatch_overlap"],
        reverse=True,
    )

    probe_keys = list(next(iter(pairs.values()))["counterfactual_agreements"].keys())
    counterfactual = {key: _weighted(pairs, ("counterfactual_agreements", key)) for key in probe_keys}
    gains = {key: value - counterfactual["original"] for key, value in counterfactual.items() if key != "original"}
    ranked_probes = sorted(gains, key=lambda key: gains[key], reverse=True)

    stale_input_mismatches: dict[str, int] = {}
    for row in pairs.values():
        for key, value in row["formal_state_carry"]["current_input_mismatch_bars_by_input"].items():
            stale_input_mismatches[key] = stale_input_mismatches.get(key, 0) + int(value)

    exact_fields = {
        key: bool(all(row["replay_exact_fields"][key] for row in pairs.values()))
        for key in next(iter(pairs.values()))["replay_exact_fields"]
    }

    return {
        "schema_version": 3,
        "issue": 66,
        "phase": "C",
        "status": "ACTUAL_PHASEB_STALE_PERSISTENCE_LOCALIZATION_REUSED_DATA_NO_PNL_NO_FORMULA_CHANGE",
        "diagnostic_revision": "v3_actual_issue57_phaseb_stale_pressure_contract",
        "all_original_replays_exact": bool(all(row["replay_exact"] for row in pairs.values())),
        "replay_exact_fields": exact_fields,
        "agreements": agreements,
        "mismatch_bars": {"candidate_display": int(candidate_total), "strong_stage": int(strong_total), "formal": int(formal_total)},
        "formal_mismatch_amplification": float(formal_total / strong_total) if strong_total else (0.0 if not formal_total else float("inf")),
        "state_carry_formal_mismatch_bars": int(state_carry_total),
        "state_carry_share_of_formal_mismatch": float(state_carry_total / formal_total) if formal_total else 0.0,
        "current_loop_input_mismatch_bars": stale_input_mismatches,
        "strong_stage_mismatch_attribution": attribution,
        "ranked_current_bar_causes": ranked_causes,
        "counterfactual_agreements": counterfactual,
        "counterfactual_gain_vs_original": gains,
        "ranked_persistence_probes": ranked_probes,
        "mean_evidence_strength_mae": float(np.mean([row["evidence_strength_mae"] for row in pairs.values()])),
        "pairs": pairs,
    }


def pct(x: float) -> str:
    return f"{x * 100.0:.2f}%"


def render_markdown(r: dict[str, Any]) -> str:
    a = r["agreements"]
    lines = [
        "# Issue #66 Phase C — Candidate→Formal Persistence Localization (v3)", "",
        "Status: **reused frozen data / no PnL / no formula change**", "",
        "Persistence contract: **actual inherited Issue #57 Phase-B stale-pressure state machine**", "",
        f"Exact replay of all five stored state series: **{'PASS' if r['all_original_replays_exact'] else 'FAIL'}**", "",
        "| State series | Exact replay |", "|---|---:|",
    ]
    labels = {"formal": "Formal id", "candidate": "Candidate id", "candidate_bars": "Candidate bars", "stale_bars": "Stale-pressure bars", "stale_reason": "Stale-pressure reason"}
    for key, label in labels.items():
        lines.append(f"| {label} | {'YES' if r['replay_exact_fields'][key] else 'NO'} |")
    lines += ["", "## Current-bar mirror inputs", "", "| Input | Mirror agreement |", "|---|---:|",
        f"| Top stage | {pct(a['top_stage'])} |",
        f"| Evidence threshold pass | {pct(a['evidence_threshold'])} |",
        f"| Candidate conflict | {pct(a['candidate_conflict'])} |",
        f"| Strong-stage id | {pct(a['strong_stage'])} |",
        f"| Candidate display id | {pct(a['candidate_display'])} |",
        f"| Chaos | {pct(a['chaos'])} |",
        f"| Coexist | {pct(a['coexist'])} |",
        f"| Fast switch | {pct(a['fast_switch'])} |",
        f"| Active confirm bars | {pct(a['active_confirm_bars'])} |",
        f"| Stale-pressure reason | {pct(a['stale_pressure_reason'])} |",
        f"| Stale-pressure bars | {pct(a['stale_pressure_bars'])} |",
        "", "## Candidate residual attribution", "",
        "| Rank | Cause | Strong-stage mismatch overlap | Share |", "|---:|---|---:|---:|",
    ]
    names = {"top_stage": "Top-stage mismatch", "has_sharp": "Probability-valid mismatch", "dominant_threshold": "Dominant threshold", "top_gap_threshold": "Top-gap threshold", "evidence_threshold": "Evidence threshold", "candidate_conflict": "Candidate conflict"}
    for i, key in enumerate(r["ranked_current_bar_causes"], 1):
        node = r["strong_stage_mismatch_attribution"][key]
        lines.append(f"| {i} | {names[key]} | {node['strong_stage_mismatch_overlap']} | {pct(node['share_of_strong_stage_mismatch'])} |")
    unexplained = r["strong_stage_mismatch_attribution"]["unexplained"]
    lines += ["", f"Unexplained strong-stage mismatch bars: **{unexplained['strong_stage_mismatch_overlap']}**.", "",
        "## Persistence amplification", "",
        f"Candidate-display mismatch bars: **{r['mismatch_bars']['candidate_display']}**  ",
        f"Strong-stage mismatch bars: **{r['mismatch_bars']['strong_stage']}**  ",
        f"Formal mismatch bars: **{r['mismatch_bars']['formal']}**  ",
        f"Formal / strong-stage mismatch amplification: **{r['formal_mismatch_amplification']:.2f}×**  ",
        f"Formal mismatch bars where all current persistence inputs are already mirrored: **{r['state_carry_formal_mismatch_bars']}** ({pct(r['state_carry_share_of_formal_mismatch'])})", "",
        "Current persistence-input mismatch bars: `" + ", ".join(f"{k}={v}" for k, v in r["current_loop_input_mismatch_bars"].items()) + "`", "",
        "## Counterfactual replay localization (diagnostic only)", "", "| Replay | Formal mirror | Gain vs original |", "|---|---:|---:|",
    ]
    probe_labels = {
        "original": "Original stale-pressure persistence",
        "fixed_confirm_no_fast_shortening": "Fixed confirm / no fast shortening",
        "immediate_strong_confirmation": "Immediate strong confirmation",
        "chaos_only_stale_pressure": "Chaos-only stale pressure",
        "disable_weak_challenger_pressure": "Disable weak-challenger pressure",
        "disable_coexist_pressure": "Disable coexist pressure",
        "immediate_stale_clear": "Immediate stale clear",
        "stateless_strong_stage": "Stateless strong-stage",
    }
    order = ["original"] + r["ranked_persistence_probes"]
    for key in order:
        val = r["counterfactual_agreements"][key]
        gain = 0.0 if key == "original" else r["counterfactual_gain_vs_original"][key]
        lines.append(f"| {probe_labels[key]} | {pct(val)} | {pct(gain)} |")
    lines += ["", "## Decision boundary", "",
        "No counterfactual is a proposed production change. If the full stale-pressure loop is structurally symmetric under exact mirrored inputs, repair the dominant residual input family before considering any persistence redesign.", ""]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description="Issue #66 Phase C v3 actual stale-pressure localization")
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
        "replay_exact_fields": report["replay_exact_fields"],
        "agreements": report["agreements"],
        "mismatch_bars": report["mismatch_bars"],
        "formal_mismatch_amplification": report["formal_mismatch_amplification"],
        "state_carry_share": report["state_carry_share_of_formal_mismatch"],
        "ranked_current_bar_causes": report["ranked_current_bar_causes"],
        "counterfactual_agreements": report["counterfactual_agreements"],
    }, indent=2))


if __name__ == "__main__":
    main()
