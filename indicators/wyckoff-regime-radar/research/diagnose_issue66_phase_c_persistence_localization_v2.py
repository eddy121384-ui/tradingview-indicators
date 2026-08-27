#!/usr/bin/env python3
"""Issue #66 Phase C v2: correct replay initialization across warmup.

The first diagnostic correctly localized current-bar mismatches but replayed the
inertia shell from zero at the post-warmup slice. Formal state can already exist
before that slice. This wrapper preserves every original decomposition and only
recomputes counterfactual replays across the full history before scoring the
post-warmup region.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

import diagnose_issue66_phase_c_persistence_localization as v1


ORIGINAL_ANALYZE_PAIR = v1.analyze_pair


def analyze_pair(frame) -> dict[str, Any]:
    out = ORIGINAL_ANALYZE_PAIR(frame)
    model, inverse, cfg, warmup = v1.load_pair(frame)
    sl = slice(warmup, None)

    top_full = v1.arr_int(model, "top_id")
    inv_top_full = v1.arr_int(inverse, "top_id")
    strong_full = v1.arr_bool(model, "strong_candidate")
    inv_strong_full = v1.arr_bool(inverse, "strong_candidate")
    chaos_full = v1.arr_bool(model, "chaos")
    inv_chaos_full = v1.arr_bool(inverse, "chaos")
    fast_full = v1.arr_bool(model, "fast_switch")
    inv_fast_full = v1.arr_bool(inverse, "fast_switch")

    strong_stage_full = np.where(strong_full, top_full, 0).astype(int)
    inv_strong_stage_full = np.where(inv_strong_full, inv_top_full, 0).astype(int)
    active_full = np.where(fast_full, cfg.fast_switch_confirm_bars, cfg.confirm_bars).astype(int)
    inv_active_full = np.where(inv_fast_full, cfg.fast_switch_confirm_bars, cfg.confirm_bars).astype(int)

    formal = v1.arr_int(model, "formal_id")[sl]
    inv_formal = v1.arr_int(inverse, "formal_id")[sl]

    def replay_pair(**kwargs):
        left = v1.replay_formal(
            strong_stage_full,
            chaos_full,
            active_full,
            int(cfg.confirm_bars),
            **kwargs,
        )[sl]
        right = v1.replay_formal(
            inv_strong_stage_full,
            inv_chaos_full,
            inv_active_full,
            int(cfg.confirm_bars),
            **kwargs,
        )[sl]
        return left, right

    original, inv_original = replay_pair()

    fixed_full = np.full(len(strong_stage_full), int(cfg.confirm_bars), dtype=int)
    fixed_left = v1.replay_formal(
        strong_stage_full, chaos_full, fixed_full, int(cfg.confirm_bars)
    )[sl]
    fixed_right = v1.replay_formal(
        inv_strong_stage_full, inv_chaos_full, fixed_full, int(cfg.confirm_bars)
    )[sl]

    no_confirmation, inv_no_confirmation = replay_pair(immediate_confirm=True)
    immediate_chaos, inv_immediate_chaos = replay_pair(immediate_chaos_reset=True)
    confirmation_only, inv_confirmation_only = replay_pair(retain_confirmed=False)

    stateless = strong_stage_full[sl]
    inv_stateless = inv_strong_stage_full[sl]

    out["replay_exact"] = bool(
        np.array_equal(original, formal) and np.array_equal(inv_original, inv_formal)
    )
    out["counterfactual_agreements"] = {
        "original": v1.stage_agreement(original, inv_original),
        "fixed_confirm_no_fast_shortening": v1.stage_agreement(fixed_left, fixed_right),
        "no_confirmation_window": v1.stage_agreement(no_confirmation, inv_no_confirmation),
        "immediate_chaos_reset": v1.stage_agreement(immediate_chaos, inv_immediate_chaos),
        "confirmation_only_no_retained_regime": v1.stage_agreement(
            confirmation_only, inv_confirmation_only
        ),
        "stateless_strong_stage": v1.stage_agreement(stateless, inv_stateless),
    }
    return out


def build_report() -> dict[str, Any]:
    old = v1.analyze_pair
    v1.analyze_pair = analyze_pair
    try:
        report = v1.build_report()
    finally:
        v1.analyze_pair = old
    report["diagnostic_revision"] = "v2_full_history_replay_before_warmup_scoring"
    return report


def render_markdown(report: dict[str, Any]) -> str:
    text = v1.render_markdown(report)
    marker = "Status: **reused frozen data / no PnL / no formula change**"
    replacement = marker + "\n\nReplay revision: **v2 — full-history state replay before warmup scoring**"
    return text.replace(marker, replacement, 1)


def main() -> None:
    ap = argparse.ArgumentParser(description="Issue #66 Phase C v2 persistence localization")
    ap.add_argument("--json", type=Path, required=True)
    ap.add_argument("--markdown", type=Path, required=True)
    args = ap.parse_args()
    report = build_report()
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    args.markdown.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({
        "diagnostic_revision": report["diagnostic_revision"],
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
