#!/usr/bin/env python3
"""Generate the scalable Issue #78 Python mirror of the frozen Issue #68 RC.

The implementation deliberately reuses the already runtime-validated Issue #66
C-2 Python price-only lineage, then adds only the production deltas that matter
for positive-price individual equities:

1. Issue #68 exact symmetric HARD current-context cap for Stage 1 / 4;
2. frozen production Volume Mode = Auto witness layer;
3. production evidence weighting when the volume witness is active.

MTF and Divergence are omitted from the Python executor because the frozen
production defaults are Observe Only, which gives them zero stage-bias weight.
A contract check makes that assumption explicit.

For OOS2 stocks representation is frozen to Price Log, so the Yield-Level branch
is intentionally outside this executable path.

This module is an engineering port. Pine remains the source of truth until the
runtime parity gate passes.
"""
from __future__ import annotations

import argparse
import sys
import types
from pathlib import Path

from generate_issue66_phase_c2_stage14_conflict_core import render_phase_c2_source

HERE = Path(__file__).resolve().parent

CONFIG_ANCHOR = '''    long_slope_rank_confirm: float = 70.0
'''
CONFIG_INSERT = '''    long_slope_rank_confirm: float = 70.0

    # Frozen production volume defaults from Issue #68 RC.
    volume_rank_len: int = 252
    volume_quality_len: int = 252
    volume_max_weight: float = 20.0
    volume_participation_threshold: float = 60.0
    volume_spike_threshold: float = 95.0
    volume_quality_min: float = 45.0
    volume_quality_full: float = 80.0
    effort_result_threshold: float = 60.0
    witness_max_total_weight: float = 25.0
'''

VOLUME_INPUT_ANCHOR = '''    n = len(out)

    # Core Calculation | heat.
'''
VOLUME_INPUT_INSERT = '''    n = len(out)
    volume = (
        pd.to_numeric(out["volume"], errors="coerce").to_numpy(float)
        if "volume" in out.columns
        else np.full(n, np.nan, dtype=float)
    )

    # Core Calculation | heat.
'''

VOLUME_LAYER_ANCHOR = '''    non_absorption_gate = gate(100.0 - downside_exhaustion, 25.0, 65.0)
    non_distribution_gate = gate(100.0 - upside_exhaustion, 25.0, 65.0)

    # Trend extension / continuation.
'''

VOLUME_LAYER_INSERT = '''    non_absorption_gate = gate(100.0 - downside_exhaustion, 25.0, 65.0)
    non_distribution_gate = gate(100.0 - upside_exhaustion, 25.0, 65.0)

    # Issue #78 / Issue #68 production Volume Mode = Auto witness layer.
    # Price action remains the main engine; volume only adds bounded evidence.
    vol_ok = np.isfinite(volume) & (volume > 0.0)
    vol_presence_score = np.where(vol_ok, 100.0, 0.0)
    vol_continuity_score = rolling_sma(np.where(vol_ok, 1.0, 0.0), cfg.volume_quality_len) * 100.0
    has_any_volume = np.isfinite(vol_continuity_score) & (vol_continuity_score > 5.0)

    volume_rank_raw = percentrank(volume, cfg.volume_rank_len)
    volume_participation_raw = clamp(np.nan_to_num(volume_rank_raw, nan=0.0), 0.0, 100.0)

    volume_sma = rolling_sma(volume, cfg.volume_quality_len)
    volume_stdev = rolling_std(volume, cfg.volume_quality_len)
    volume_cv = safe_div(volume_stdev, volume_sma)
    volume_cv_rank = percentrank(volume_cv, cfg.volume_rank_len)
    volume_stability_score = np.where(
        has_any_volume,
        clamp(100.0 - np.nan_to_num(volume_cv_rank, nan=100.0), 0.0, 100.0),
        0.0,
    )

    volume_cv_ok_low = gate(volume_cv, 0.01, 0.20) * 100.0
    volume_cv_ok_high = 100.0 - gate(volume_cv, 5.0, 12.0) * 100.0
    volume_distribution_reasonable_score = np.where(
        has_any_volume,
        np.minimum(volume_cv_ok_low, volume_cv_ok_high),
        0.0,
    )

    volume_spike_ratio = safe_div(volume, volume_sma)
    volume_spike_ratio_rank = percentrank(volume_spike_ratio, cfg.volume_rank_len)
    volume_spike_score = np.where(
        has_any_volume,
        clamp(np.nan_to_num(volume_spike_ratio_rank, nan=0.0), 0.0, 100.0),
        0.0,
    )
    volume_spike_pollution_penalty = gate(
        volume_spike_score, cfg.volume_spike_threshold, 100.0
    ) * 100.0
    non_spike_pollution_score = np.where(
        has_any_volume, 100.0 - volume_spike_pollution_penalty, 0.0
    )

    volume_quality_score = clamp(
        weighted(
            vol_presence_score, 0.25,
            vol_continuity_score, 0.25,
            volume_stability_score, 0.20,
            volume_distribution_reasonable_score, 0.20,
            non_spike_pollution_score, 0.10,
        ),
        0.0,
        100.0,
    )
    volume_auto_factor = gate(
        volume_quality_score, cfg.volume_quality_min, cfg.volume_quality_full
    )
    volume_weight_applied = np.where(
        has_any_volume,
        cfg.volume_max_weight / 100.0 * volume_auto_factor,
        0.0,
    )
    volume_active = volume_weight_applied > 0.0
    volume_participation = np.where(
        volume_active, volume_participation_raw, 0.0
    )

    price_up_atr = safe_div(np.maximum(close - shift(close), 0.0), atr_v)
    price_dn_atr = safe_div(np.maximum(shift(close) - close, 0.0), atr_v)
    up_progress_score = gate(price_up_atr, 0.0, 1.5) * 100.0
    down_progress_score = gate(price_dn_atr, 0.0, 1.5) * 100.0
    up_inefficiency_score = clamp(100.0 - up_progress_score, 0.0, 100.0)
    down_inefficiency_score = clamp(100.0 - down_progress_score, 0.0, 100.0)

    effort_result_up = np.where(
        volume_active,
        clamp(
            weighted(
                volume_participation, 0.30,
                no_break_high_score, 0.25,
                up_inefficiency_score, 0.20,
                resistance_holding, 0.15,
                upside_exhaustion, 0.10,
            ),
            0.0,
            100.0,
        ),
        0.0,
    )
    effort_result_down = np.where(
        volume_active,
        clamp(
            weighted(
                volume_participation, 0.30,
                no_break_low_score, 0.25,
                down_inefficiency_score, 0.20,
                support_holding, 0.15,
                downside_exhaustion, 0.10,
            ),
            0.0,
            100.0,
        ),
        0.0,
    )

    volume_absorption_score = np.where(
        volume_active,
        clamp(
            weighted(
                effort_result_down, 0.35,
                downside_exhaustion, 0.25,
                support_holding, 0.25,
                volume_participation, 0.15,
            ),
            0.0,
            100.0,
        ),
        0.0,
    )
    volume_distribution_score = np.where(
        volume_active,
        clamp(
            weighted(
                effort_result_up, 0.35,
                upside_exhaustion, 0.25,
                resistance_holding, 0.25,
                volume_participation, 0.15,
            ),
            0.0,
            100.0,
        ),
        0.0,
    )
    volume_breakout_confirmation = np.where(
        volume_active,
        clamp(
            weighted(
                breakout_score, 0.35,
                volume_participation, 0.25,
                up_progress_score, 0.25,
                100.0 - np.maximum(upside_exhaustion, resistance_holding), 0.15,
            ),
            0.0,
            100.0,
        ),
        0.0,
    )
    volume_breakdown_confirmation = np.where(
        volume_active,
        clamp(
            weighted(
                explicit_breakdown_score, 0.35,
                volume_participation, 0.25,
                down_progress_score, 0.25,
                100.0 - np.maximum(downside_exhaustion, support_holding), 0.15,
            ),
            0.0,
            100.0,
        ),
        0.0,
    )

    # Frozen witness cap. With MTF/divergence at Observe Only, only volume can
    # carry stage-bias weight; its 20% default is already below the 25% package cap.
    witness_cap = cfg.witness_max_total_weight / 100.0
    witness_scale = np.where(
        (volume_weight_applied > witness_cap) & (volume_weight_applied > 0.0),
        safe_div(witness_cap, volume_weight_applied),
        1.0,
    )
    volume_weight_governed = volume_weight_applied * witness_scale

    # Trend extension / continuation.
'''

HARD_GATE_OLD = '''    mature_bull_gate = gate(bull_maturity_trace, 60.0, 85.0)  # retained diagnostic compatibility

    # Issue #66 B-7: one direction-neutral background/maturity gate for Stage 1/4.
    def issue66_background_maturity_gate(background, maturity_trace):
        return gate(np.maximum(background, maturity_trace), 35.0, 75.0)

    bear_background_acc_gate = issue66_background_maturity_gate(bear_bg, bear_maturity_trace)
    bull_background_dist_gate = issue66_background_maturity_gate(bull_bg, bull_maturity_trace)
'''
HARD_GATE_NEW = HARD_GATE_OLD + '''    # Issue #68 HARD current-context cap — exact symmetric production candidate.
    current_bear_gate = gate(bear_bg, 35.0, 75.0)
    current_bull_gate = gate(bull_bg, 35.0, 75.0)
    ctx_down_ex_gate = np.minimum(downside_exhaustion_gate, current_bear_gate)
    ctx_up_ex_gate = np.minimum(upside_exhaustion_gate, current_bull_gate)
'''

ACC_GATE_OLD = '''    acc_gate = range_gate * bear_background_acc_gate * downside_exhaustion_gate * support_holding_gate * non_markdown_cont_gate'''
ACC_GATE_NEW = '''    acc_gate = range_gate * bear_background_acc_gate * ctx_down_ex_gate * support_holding_gate * non_markdown_cont_gate'''

DIST_GATE_OLD = '''    dist_gate = range_gate * bull_background_dist_gate * upside_exhaustion_gate * resistance_holding_gate * non_markup_cont_gate'''
DIST_GATE_NEW = '''    dist_gate = range_gate * bull_background_dist_gate * ctx_up_ex_gate * resistance_holding_gate * non_markup_cont_gate'''

EFFECTIVE_OLD = '''    acc_eff = acc_raw * acc_gate
    markup_eff = markup_raw * markup_gate
    reacc_eff = reacc_raw * reacc_gate
    dist_eff = dist_raw * dist_gate
    markdown_eff = markdown_raw * markdown_gate
    redist_eff = redist_raw * redist_gate
'''
EFFECTIVE_NEW = '''    # Issue #68 production volume witness multipliers.
    acc_vol_mult = 1.0 + volume_weight_governed * gate(
        volume_absorption_score, cfg.effort_result_threshold, 90.0
    )
    markup_vol_mult = 1.0 + volume_weight_governed * gate(
        volume_breakout_confirmation, cfg.effort_result_threshold, 90.0
    )
    reacc_vol_mult = 1.0 + volume_weight_governed * gate(
        np.maximum(volume_absorption_score, 100.0 - volume_distribution_score),
        50.0,
        90.0,
    ) * 0.50
    dist_vol_mult = 1.0 + volume_weight_governed * gate(
        volume_distribution_score, cfg.effort_result_threshold, 90.0
    )
    markdown_vol_mult = 1.0 + volume_weight_governed * gate(
        volume_breakdown_confirmation, cfg.effort_result_threshold, 90.0
    )
    redist_vol_mult = 1.0 + volume_weight_governed * gate(
        np.maximum(volume_distribution_score, 100.0 - volume_absorption_score),
        50.0,
        90.0,
    ) * 0.50

    acc_eff = acc_raw * acc_gate * acc_vol_mult
    markup_eff = markup_raw * markup_gate * markup_vol_mult
    reacc_eff = reacc_raw * reacc_gate * reacc_vol_mult
    dist_eff = dist_raw * dist_gate * dist_vol_mult
    markdown_eff = markdown_raw * markdown_gate * markdown_vol_mult
    redist_eff = redist_raw * redist_gate * redist_vol_mult
'''

EVIDENCE_COMMENT_OLD = '''    # Evidence strength uses the price-only branch because all witnesses are off.
'''
EVIDENCE_COMMENT_NEW = '''    # Issue #68 evidence strength uses the production volume witness when active.
'''

EVIDENCE_OLD = '''    evidence = weighted(eff_total_strength, 0.30, top_eff_strength, 0.25, top_gap_strength, 0.20, stage_support, 0.25)
'''
EVIDENCE_NEW = '''    volume_support = np.zeros(n, dtype=float)
    for i in range(n):
        if top_id[i] == 1:
            volume_support[i] = volume_absorption_score[i]
        elif top_id[i] == 2:
            volume_support[i] = volume_breakout_confirmation[i]
        elif top_id[i] == 3:
            volume_support[i] = weighted(
                volume_absorption_score[i], 0.50,
                100.0 - volume_distribution_score[i], 0.50,
            )
        elif top_id[i] == 4:
            volume_support[i] = volume_distribution_score[i]
        elif top_id[i] == 5:
            volume_support[i] = volume_breakdown_confirmation[i]
        elif top_id[i] == 6:
            volume_support[i] = weighted(
                volume_distribution_score[i], 0.50,
                100.0 - volume_absorption_score[i], 0.50,
            )

    price_only_evidence = weighted(
        eff_total_strength, 0.30,
        top_eff_strength, 0.25,
        top_gap_strength, 0.20,
        stage_support, 0.25,
    )
    volume_witness_active = volume_active
    evidence = np.where(
        volume_witness_active,
        weighted(
            eff_total_strength, 0.25,
            top_eff_strength, 0.20,
            top_gap_strength, 0.20,
            stage_support, 0.25,
            volume_support, 0.10,
        ),
        price_only_evidence,
    )
'''

DIAGNOSTIC_ANCHOR = '''        "range_score": range_score,
'''
DIAGNOSTIC_INSERT = '''        "sym_atr": sym_atr,
        "volume_quality_score": volume_quality_score,
        "volume_weight_applied": volume_weight_applied,
        "volume_weight_governed": volume_weight_governed,
        "volume_participation": volume_participation,
        "volume_absorption_score": volume_absorption_score,
        "volume_distribution_score": volume_distribution_score,
        "volume_breakout_confirmation": volume_breakout_confirmation,
        "volume_breakdown_confirmation": volume_breakdown_confirmation,
        "current_bear_gate": current_bear_gate,
        "current_bull_gate": current_bull_gate,
        "ctx_down_ex_gate": ctx_down_ex_gate,
        "ctx_up_ex_gate": ctx_up_ex_gate,
'''


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)


def render_issue78_rc_python_source() -> str:
    source = render_phase_c2_source()

    source = replace_once(source, CONFIG_ANCHOR, CONFIG_INSERT, "volume config")
    source = replace_once(source, VOLUME_INPUT_ANCHOR, VOLUME_INPUT_INSERT, "volume input")
    source = replace_once(source, VOLUME_LAYER_ANCHOR, VOLUME_LAYER_INSERT, "volume layer")
    source = replace_once(source, HARD_GATE_OLD, HARD_GATE_NEW, "HARD current-context block")
    source = replace_once(source, ACC_GATE_OLD, ACC_GATE_NEW, "HARD accumulation gate")
    source = replace_once(source, DIST_GATE_OLD, DIST_GATE_NEW, "HARD distribution gate")
    source = replace_once(source, EFFECTIVE_OLD, EFFECTIVE_NEW, "volume effective scores")
    source = replace_once(source, EVIDENCE_COMMENT_OLD, EVIDENCE_COMMENT_NEW, "evidence comment")
    source = replace_once(source, EVIDENCE_OLD, EVIDENCE_NEW, "volume evidence")
    source = replace_once(
        source,
        DIAGNOSTIC_ANCHOR,
        DIAGNOSTIC_ANCHOR + DIAGNOSTIC_INSERT,
        "diagnostic fields",
    )

    required = (
        "ISSUE #66 PHASE C-2",
        "candidate_conflict |= (top_id == 1) & (resistance_holding >= cfg.absorb_threshold) & (upside_exhaustion >= cfg.absorb_threshold)",
        "stale_pressure_bars",
        "ctx_down_ex_gate = np.minimum(downside_exhaustion_gate, current_bear_gate)",
        "ctx_up_ex_gate = np.minimum(upside_exhaustion_gate, current_bull_gate)",
        "volume_quality_score",
        "volume_weight_governed",
        "volume_breakout_confirmation",
        "volume_breakdown_confirmation",
        '"sym_atr": sym_atr',
    )
    for token in required:
        if token not in source:
            raise RuntimeError(f"Issue #78 Python RC source missing required token: {token}")

    # OOS2 is explicitly Price Log. MTF/Divergence are Observe Only in the
    # frozen production Pine and therefore intentionally absent here.
    forbidden = (
        "request.security_lower_tf",
        "strategy.entry",
        "strategy.close",
    )
    for token in forbidden:
        if token in source:
            raise RuntimeError(f"forbidden execution construct in Python RC mirror: {token}")

    header = '''# ISSUE #78 — PYTHON MIRROR OF FROZEN ISSUE #68 RC
# Source lineage: runtime-validated Issue #66 C-2 Python mirror
# + Issue #68 HARD current-context cap + frozen Auto-volume witness.
# Positive-price / Price-Log executor for Cross-Sectional OOS2.
# Pine remains source of truth until Issue #78 runtime parity passes.

'''
    return header + source


def load_issue78_rc_namespace() -> dict[str, object]:
    module_name = "wyckoff_issue78_rc_python_generated"
    module = types.ModuleType(module_name)
    module.__file__ = str(HERE / "generated" / "wyckoff-issue78-rc-python.py")
    module.__package__ = None
    sys.modules[module_name] = module
    exec(compile(render_issue78_rc_python_source(), module.__file__, "exec"), module.__dict__)
    return module.__dict__


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate Issue #78 scalable Python RC mirror")
    ap.add_argument(
        "--output",
        type=Path,
        default=HERE / "generated" / "wyckoff-issue78-rc-python.py",
    )
    args = ap.parse_args()
    source = render_issue78_rc_python_source()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(source, encoding="utf-8")
    print(args.output)
    print("Issue #78 Python RC mirror generation PASS")


if __name__ == "__main__":
    main()
