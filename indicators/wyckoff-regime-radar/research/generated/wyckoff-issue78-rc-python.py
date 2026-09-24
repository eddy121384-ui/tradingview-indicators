# ISSUE #78 — PYTHON MIRROR OF FROZEN ISSUE #68 RC
# Source lineage: runtime-validated Issue #66 C-2 Python mirror
# + Issue #68 HARD current-context cap + frozen Auto-volume witness.
# Positive-price / Price-Log executor for Cross-Sectional OOS2.
# Pine remains source of truth until Issue #78 runtime parity passes.

# ISSUE #66 PHASE C-2 — STAGE 1/4 CANDIDATE-CONFLICT SYMMETRY
# Parent: accepted Issue #66 Phase B-7 core.
# Delta only: Stage-1 conflict mirrors canonical Stage-4 exhaustion/holding/continuation pattern.
# Numeric classifier layers, other conflict clauses, Candidate thresholds, and persistence are unchanged.

# ISSUE #66 PHASE B-7 — STAGE 1/4 GATE SYMMETRY REPAIR
# Parent: accepted Issue #66 Phase B-6 core.
# Delta only: Stage-1/Stage-4 background/maturity gate uses one mirrored primitive.
# Raw stages, other gates, break evidence, persistence, thresholds, and strategy are unchanged.

# ISSUE #66 PHASE B-6 — STAGE 1/4 RAW SYMMETRY REPAIR
# Parent: accepted Issue #66 Phase B-5 core.
# Delta only: Acc/Dist raw final component shares direction-neutral quiet-range context.
# All other raw components, gates, break evidence, persistence, thresholds, and strategy are unchanged.

# ISSUE #66 PHASE B-5 — STAGE 3/6 RAW SYMMETRY REPAIR
# Parent: accepted Issue #66 Phase B-3 core.
# Delta only: Reacc/Redist raw fourth component shares non-opposite-heat primitive.
# All other raw components, gates, break evidence, persistence, thresholds, and strategy are unchanged.

# ISSUE #66 PHASE B-3 — DIRECTION-NEUTRAL TREND-ENTRY GATE
# Parent: Issue #66 Phase B-2 break-evidence core.
# Delta only: Stage-2/Stage-5 fresh-entry gates share break * structure * non-end.
# Raw stages, break evidence, extension/continuation, other gates, persistence, and strategy are unchanged.

# ISSUE #66 PHASE B-2 — DIRECTION-NEUTRAL BREAK EVIDENCE
# Parent: Issue #66 Phase B-1 reciprocal-safe representation core.
# Delta only: breakout/breakdown evidence and directly-derived gate share one primitive.
# Stage formulas/gates, continuation/extension, persistence, and strategy logic are unchanged.

# ISSUE #66 PHASE B-1 — RECIPROCAL-SAFE REPRESENTATION
# Parent: frozen v0.6 Phase-B research core.
# Delta only: geometric/log MA representation, log-space ATR distances/volatility,
# reciprocal-safe MA crosses, range-width scale, and MA-spread scale.
# Directional heuristics, stage formulas/gates, persistence, and strategy logic are unchanged.

# PHASE B PERSISTENCE REDESIGN — Issue #57
# Parent: mechanically generated v0.6 Phase-A core.
# Frozen rule: unsupported Formal states decay to neutral after 2x confirmBars; weak challengers are not promoted.

# GENERATED EXPERIMENTAL CORE — Issue #57 / v0.6 Phase A
# Mechanical delta from frozen v0.5.2.1 research mirror:
#   1) noBreakLowScore/noBreakHighScore: binary cliffs -> continuous ATR-scaled scores
#   2) 50-bar prior-range continuation: boolean 65/80/100 cliff -> continuous hold strength
#   3) 20-bar range-break evidence: one-tick event -> one-sided ATR-scaled strength
#   4) range-break downstream gates: boolean 0.85/0.90 jumps -> strength-scaled gates
# MA-cross evidence remains frozen; state count/persistence/witnesses/trading rules are unchanged.
# Additional emitted columns are diagnostics only; they do not change calculations.

#!/usr/bin/env python3
"""Frozen v0.5.2.1 price-only Wyckoff Regime Radar research mirror.

Scope is intentionally narrow: OHLC price/structure calculations, six stage
scores, evidence, candidate logic, fast switching, and confirmed formal state.
Volume, MTF, Divergence, UI, alerts, and trading rules are excluded.

Do not use this module for economic claims until fixed TradingView checkpoints
show acceptable Pine↔Python parity.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from .v06_boundary_scores import (
        soft_above_range_score,
        soft_below_range_score,
        soft_break_above_score,
        soft_break_below_score,
        soft_hold_strength,
        soft_no_break_high_score,
        soft_no_break_low_score,
    )
except ImportError:  # direct script execution / generated-module execution
    from v06_boundary_scores import (  # type: ignore
        soft_above_range_score,
        soft_below_range_score,
        soft_break_above_score,
        soft_break_below_score,
        soft_hold_strength,
        soft_no_break_high_score,
        soft_no_break_low_score,
    )

try:
    from .pine_math import (
        atr,
        barssince,
        clamp,
        crossover,
        crossunder,
        ema,
        gate,
        percentrank,
        recent,
        rolling_highest,
        rolling_lowest,
        rolling_sma,
        rolling_std,
        safe_div,
        shift,
        slope_z,
        weighted,
    )
except ImportError:  # direct script execution
    from pine_math import (  # type: ignore
        atr,
        barssince,
        clamp,
        crossover,
        crossunder,
        ema,
        gate,
        percentrank,
        recent,
        rolling_highest,
        rolling_lowest,
        rolling_sma,
        rolling_std,
        safe_div,
        shift,
        slope_z,
        weighted,
    )


STAGE_NAMES = {
    0: "No clear regime",
    1: "Accumulation",
    2: "Markup",
    3: "Re-accumulation",
    4: "Distribution",
    5: "Markdown",
    6: "Re-distribution",
}


@dataclass(frozen=True)
class PriceOnlyConfig:
    # Heat / trend / range defaults copied from Pine v0.5.2.1.
    speed_len: int = 20
    short_len: int = 10
    long_len: int = 60
    vol_len: int = 60
    ma_len: int = 50
    atr_len: int = 20
    rank_len: int = 756

    maturity_slope_len: int = 120
    maturity_ma_len: int = 200
    maturity_atr_len: int = 60

    range_len: int = 50
    breakout_bars: int = 20
    low_vol_level: float = 25.0
    use_breakout_exemption: bool = True

    absorb_len: int = 50
    absorb_threshold: float = 60.0

    trend_ext_threshold: float = 60.0
    non_range_gate_start: float = 40.0
    non_range_gate_full: float = 75.0
    continuation_hold_bars: int = 2
    fast_switch_weight: float = 85.0
    fast_switch_gap: float = 25.0
    fast_switch_evidence: float = 50.0
    fast_switch_ext: float = 70.0
    fast_switch_confirm_bars: int = 1

    stage_smooth_len: int = 3
    regime_gamma: float = 2.0
    dominant_min: float = 30.0
    top_gap_min: float = 8.0
    high_confidence: float = 50.0
    evidence_min: float = 35.0
    evidence_high: float = 65.0
    evidence_eff_full: float = 40.0
    evidence_top_full: float = 15.0
    confirm_bars: int = 3
    min_eff_total: float = 3.0
    stage_dispute_min_weight: float = 20.0
    stage_dispute_max_gap: float = 15.0

    w_speed: float = 0.50
    w_accel: float = 0.25
    w_dist: float = 0.25
    w_mat_slope: float = 0.50
    w_mat_dist: float = 0.50

    yellow_level: float = 70.0
    orange_level: float = 85.0
    red_level: float = 95.0
    high_heat_confirm: float = 85.0
    speed_rank_confirm: float = 85.0
    maturity_confirm: float = 75.0
    long_slope_rank_confirm: float = 70.0

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


def _top_two(probabilities: np.ndarray):
    """Match Pine's strict-greater tie priority R1→R6."""
    n = probabilities.shape[0]
    top_id = np.ones(n, dtype=int)
    second_id = np.zeros(n, dtype=int)
    top_value = np.zeros(n, dtype=float)
    second_value = np.full(n, -1.0, dtype=float)
    for i in range(n):
        row = np.nan_to_num(probabilities[i], nan=0.0)
        tv = row[0]
        tid = 1
        sv = -1.0
        sid = 0
        for stage in range(2, 7):
            value = row[stage - 1]
            if value > tv:
                sv, sid = tv, tid
                tv, tid = value, stage
            elif value > sv:
                sv, sid = value, stage
        top_id[i] = tid
        second_id[i] = sid
        top_value[i] = tv
        second_value[i] = sv
    return top_id, top_value, second_id, second_value


def compute_price_only(frame: pd.DataFrame, config: PriceOnlyConfig | None = None) -> pd.DataFrame:
    cfg = config or PriceOnlyConfig()
    missing = {"open", "high", "low", "close"}.difference(frame.columns)
    if missing:
        raise ValueError(f"missing OHLC columns: {sorted(missing)}")

    out = frame.copy().reset_index(drop=True)
    if out.empty:
        return out

    open_ = pd.to_numeric(out["open"], errors="coerce").to_numpy(float)
    high = pd.to_numeric(out["high"], errors="coerce").to_numpy(float)
    low = pd.to_numeric(out["low"], errors="coerce").to_numpy(float)
    close = pd.to_numeric(out["close"], errors="coerce").to_numpy(float)
    n = len(out)
    volume = (
        pd.to_numeric(out["volume"], errors="coerce").to_numpy(float)
        if "volume" in out.columns
        else np.full(n, np.nan, dtype=float)
    )

    # Core Calculation | heat.
    safe_close = np.where(close > 0.0, close, np.nan)
    log_price = np.log(safe_close)
    log_ret = np.full(n, np.nan, dtype=float)
    log_ret[1:] = np.log(safe_close[1:] / safe_close[:-1])
    vol = rolling_std(log_ret, cfg.vol_len)

    speed_z = slope_z(log_price, cfg.speed_len, vol)
    short_z = slope_z(log_price, cfg.short_len, vol)
    long_z = slope_z(log_price, cfg.long_len, vol)
    accel_z = short_z - long_z

    # Issue #66 B-1 representation: geometric MA + reciprocal-invariant log ATR.
    log_high = np.log(np.where(high > 0.0, high, np.nan))
    log_low = np.log(np.where(low > 0.0, low, np.nan))
    ma_log = rolling_sma(log_price, cfg.ma_len)
    ma = np.exp(ma_log)
    atr_v = atr(high, low, close, cfg.atr_len)  # retained for frozen v0.6 boundary primitives
    sym_atr = atr(log_high, log_low, log_price, cfg.atr_len)
    dist_atr = safe_div(log_price - ma_log, sym_atr)

    speed_rank = percentrank(speed_z, cfg.rank_len)
    accel_rank = percentrank(accel_z, cfg.rank_len)
    dist_rank = percentrank(dist_atr, cfg.rank_len)
    heat_up = weighted(speed_rank, cfg.w_speed, accel_rank, cfg.w_accel, dist_rank, cfg.w_dist)
    panic_heat_dn = weighted(
        100.0 - speed_rank,
        cfg.w_speed,
        100.0 - accel_rank,
        cfg.w_accel,
        100.0 - dist_rank,
        cfg.w_dist,
    )

    # Trend maturity / end risk.
    maturity_slope_z = slope_z(log_price, cfg.maturity_slope_len, vol)
    long_slope_rank = percentrank(maturity_slope_z, cfg.rank_len)
    maturity_ma_log = rolling_sma(log_price, cfg.maturity_ma_len)
    maturity_ma = np.exp(maturity_ma_log)
    maturity_atr = atr(high, low, close, cfg.maturity_atr_len)  # retained diagnostic compatibility
    maturity_sym_atr = atr(log_high, log_low, log_price, cfg.maturity_atr_len)
    maturity_dist_atr = safe_div(log_price - maturity_ma_log, maturity_sym_atr)
    maturity_dist_rank = percentrank(maturity_dist_atr, cfg.rank_len)
    maturity_up = weighted(long_slope_rank, cfg.w_mat_slope, maturity_dist_rank, cfg.w_mat_dist)
    maturity_dn = weighted(100.0 - long_slope_rank, cfg.w_mat_slope, 100.0 - maturity_dist_rank, cfg.w_mat_dist)
    end_risk_up = safe_div(heat_up * maturity_up, 100.0)
    end_risk_dn = safe_div(panic_heat_dn * maturity_dn, 100.0)

    # Breakout / breakdown / low-vol exemption.
    atr_pct = sym_atr * 100.0
    atr_pct_rank = percentrank(atr_pct, cfg.rank_len)
    low_vol_recent_base = rolling_lowest(shift(atr_pct_rank), cfg.breakout_bars)
    low_vol_recent = np.isfinite(low_vol_recent_base) & (low_vol_recent_base <= cfg.low_vol_level)

    range_high_break = rolling_highest(shift(high), cfg.breakout_bars)
    range_low_break = rolling_lowest(shift(low), cfg.breakout_bars)
    range_break_up = (
        np.isfinite(range_high_break)
        & (close > range_high_break)
        & (shift(close) <= shift(range_high_break))
    )
    range_break_dn = (
        np.isfinite(range_low_break)
        & (close < range_low_break)
        & (shift(close) >= shift(range_low_break))
    )
    ma_cross_up = crossover(log_price, ma_log)
    ma_cross_dn = crossunder(log_price, ma_log)
    recent_break_up = recent(range_break_up | ma_cross_up, cfg.breakout_bars)
    recent_break_dn = recent(range_break_dn | ma_cross_dn, cfg.breakout_bars)
    recent_range_break_dn = recent(range_break_dn, cfg.breakout_bars)
    recent_ma_cross_up = recent(ma_cross_up, cfg.breakout_bars)
    recent_ma_cross_dn = recent(ma_cross_dn, cfg.breakout_bars)
    range_break_up_strength = soft_break_above_score(close, range_high_break, atr_v)
    range_break_dn_strength = soft_break_below_score(close, range_low_break, atr_v)
    recent_range_break_up_strength = rolling_highest(range_break_up_strength, cfg.breakout_bars)
    recent_range_break_dn_strength = rolling_highest(range_break_dn_strength, cfg.breakout_bars)

    breakout_mode_up = (
        (heat_up >= cfg.orange_level)
        & (maturity_up < cfg.maturity_confirm)
        & low_vol_recent
        & recent_break_up
    )
    breakdown_mode_dn = (
        (panic_heat_dn >= cfg.orange_level)
        & (maturity_dn < cfg.maturity_confirm)
        & low_vol_recent
        & recent_break_dn
    )
    if not cfg.use_breakout_exemption:
        breakout_mode_up[:] = False
        breakdown_mode_dn[:] = False

    # Range score / structure.
    range_high = rolling_highest(high, cfg.range_len)
    range_low = rolling_lowest(low, cfg.range_len)
    range_mid = (range_high + range_low) / 2.0
    range_width = range_high - range_low
    range_width_log = np.log(range_high) - np.log(range_low)
    range_width_atr = safe_div(range_width_log, sym_atr)
    range_width_rank = percentrank(range_width_atr, cfg.rank_len)
    abs_speed_rank = percentrank(np.abs(speed_z), cfg.rank_len)
    low_slope_score = 100.0 - abs_speed_rank
    low_vol_score = 100.0 - atr_pct_rank
    narrow_score = 100.0 - range_width_rank
    range_score = clamp(weighted(low_slope_score, 0.40, low_vol_score, 0.30, narrow_score, 0.30), 0.0, 100.0)

    bull_structure = np.where(close > ma, 50.0, 0.0) + np.where(close > maturity_ma, 50.0, 0.0)
    bear_structure = np.where(close < ma, 50.0, 0.0) + np.where(close < maturity_ma, 50.0, 0.0)
    bull_bg = weighted(maturity_up, 0.70, bull_structure, 0.30)
    bear_bg = weighted(maturity_dn, 0.70, bear_structure, 0.30)

    heat_trace = rolling_highest(end_risk_up, cfg.range_len)
    panic_trace = rolling_highest(end_risk_dn, cfg.range_len)
    heat_cooling = np.where(heat_trace > cfg.orange_level, clamp(heat_trace - end_risk_up, 0.0, 100.0), 0.0)
    panic_cooling = np.where(panic_trace > cfg.orange_level, clamp(panic_trace - end_risk_dn, 0.0, 100.0), 0.0)
    bull_maturity_trace = rolling_highest(maturity_up, cfg.range_len)
    bear_maturity_trace = rolling_highest(maturity_dn, cfg.range_len)
    bear_pressure_rising = weighted(panic_heat_dn, 0.45, bear_structure, 0.35, 100.0 - speed_rank, 0.20)

    non_end_risk_up = 100.0 - end_risk_up
    structure_strong = bull_structure
    structure_weak = bear_structure
    # Issue #66 B-2: one direction-neutral break-evidence primitive.
    # The existing 0-100 range-break strength is used directly. MA evidence uses
    # the inherited generic tiers (recent cross=70, directional MA side=35).
    def issue66_break_evidence(recent_range_strength, recent_ma_cross, directional_side, mode):
        range_component = clamp(np.nan_to_num(recent_range_strength, nan=0.0), 0.0, 100.0)
        ma_component = np.where(recent_ma_cross, 70.0, np.where(directional_side, 35.0, 0.0))
        score = np.where(mode, 100.0, np.maximum(range_component, ma_component))
        gate_value = clamp(score / 100.0, 0.0, 1.0)
        return range_component, ma_component, score, gate_value

    breakout_range_evidence, breakout_ma_evidence, breakout_score, issue66_breakout_gate = issue66_break_evidence(
        recent_range_break_up_strength,
        recent_ma_cross_up,
        log_price > ma_log,
        breakout_mode_up,
    )
    breakdown_range_evidence, breakdown_ma_evidence, explicit_breakdown_score, issue66_breakdown_gate = issue66_break_evidence(
        recent_range_break_dn_strength,
        recent_ma_cross_dn,
        log_price < ma_log,
        breakdown_mode_dn,
    )

    # Absorption vs distribution layer: still price-only.
    abs_range_high = rolling_highest(high, cfg.absorb_len)
    abs_range_low = rolling_lowest(low, cfg.absorb_len)
    abs_range_mid = (abs_range_high + abs_range_low) / 2.0
    abs_range_width = abs_range_high - abs_range_low
    abs_range_pos = clamp(safe_div(close - abs_range_low, abs_range_width) * 100.0, 0.0, 100.0)
    prev_abs_low = rolling_lowest(shift(low), cfg.absorb_len)
    prev_abs_high = rolling_highest(shift(high), cfg.absorb_len)
    no_break_low_score = soft_no_break_low_score(close, prev_abs_low, atr_v)
    no_break_high_score = soft_no_break_high_score(close, prev_abs_high, atr_v)
    neg_slope_dull_score = gate(speed_rank, 15.0, 55.0) * 100.0
    pos_slope_dull_score = gate(100.0 - speed_rank, 15.0, 55.0) * 100.0
    panic_dull_score = weighted(100.0 - panic_heat_dn, 0.55, panic_cooling, 0.45)
    heat_dull_score = weighted(100.0 - heat_up, 0.55, heat_cooling, 0.45)
    low_zone_stable = weighted(100.0 - abs_range_pos, 0.50, no_break_low_score, 0.50)
    high_zone_stable = weighted(abs_range_pos, 0.50, no_break_high_score, 0.50)
    downside_exhaustion = clamp(
        weighted(
            no_break_low_score,
            0.30,
            neg_slope_dull_score,
            0.25,
            panic_dull_score,
            0.20,
            low_vol_score,
            0.15,
            low_zone_stable,
            0.10,
        ),
        0.0,
        100.0,
    )
    upside_exhaustion = clamp(
        weighted(
            no_break_high_score,
            0.30,
            pos_slope_dull_score,
            0.25,
            heat_dull_score,
            0.20,
            low_vol_score,
            0.15,
            high_zone_stable,
            0.10,
        ),
        0.0,
        100.0,
    )

    support_probe = low <= abs_range_low + abs_range_width * 0.35
    support_reclaim = np.where(
        close > abs_range_mid,
        100.0,
        np.where(close > ma, 70.0, np.where(close > abs_range_low + abs_range_width * 0.35, 45.0, 0.0)),
    )
    panic_not_continue = 100.0 - panic_heat_dn
    support_holding = clamp(
        np.where(
            support_probe,
            weighted(no_break_low_score, 0.35, support_reclaim, 0.25, panic_not_continue, 0.25, low_zone_stable, 0.15),
            weighted(no_break_low_score, 0.45, panic_not_continue, 0.35, low_zone_stable, 0.20),
        ),
        0.0,
        100.0,
    )

    resistance_probe = high >= abs_range_high - abs_range_width * 0.35
    resistance_reject = np.where(
        close < abs_range_mid,
        100.0,
        np.where(close < ma, 70.0, np.where(close < abs_range_high - abs_range_width * 0.35, 45.0, 0.0)),
    )
    heat_not_continue = 100.0 - heat_up
    resistance_holding = clamp(
        np.where(
            resistance_probe,
            weighted(no_break_high_score, 0.35, resistance_reject, 0.25, heat_not_continue, 0.25, high_zone_stable, 0.15),
            weighted(no_break_high_score, 0.45, heat_not_continue, 0.35, high_zone_stable, 0.20),
        ),
        0.0,
        100.0,
    )

    downside_exhaustion_gate = gate(downside_exhaustion, 35.0, cfg.absorb_threshold)
    upside_exhaustion_gate = gate(upside_exhaustion, 35.0, cfg.absorb_threshold)
    support_holding_gate = gate(support_holding, 35.0, cfg.absorb_threshold)
    resistance_holding_gate = gate(resistance_holding, 35.0, cfg.absorb_threshold)
    non_absorption_gate = gate(100.0 - downside_exhaustion, 25.0, 65.0)
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
    non_range_score = 100.0 - range_score
    non_panic_score = 100.0 - panic_heat_dn
    non_heat_score = 100.0 - heat_up
    markup_extension_score = clamp(
        weighted(bull_bg, 0.25, structure_strong, 0.25, non_range_score, 0.20, heat_up, 0.20, non_panic_score, 0.10),
        0.0,
        100.0,
    )
    markdown_extension_score = clamp(
        weighted(bear_bg, 0.25, structure_weak, 0.25, non_range_score, 0.20, panic_heat_dn, 0.20, non_heat_score, 0.10),
        0.0,
        100.0,
    )
    markup_extension_support = gate(markup_extension_score, 35.0, cfg.trend_ext_threshold)
    markdown_extension_support = gate(markdown_extension_score, 35.0, cfg.trend_ext_threshold)

    prev_range_high = rolling_highest(shift(high), cfg.range_len)
    prev_range_low = rolling_lowest(shift(low), cfg.range_len)
    above_prev_range = np.isfinite(prev_range_high) & (close > prev_range_high)
    below_prev_range = np.isfinite(prev_range_low) & (close < prev_range_low)
    bars_since_above_lost = barssince(~above_prev_range)
    bars_since_below_lost = barssince(~below_prev_range)
    sustained_above = above_prev_range & (
        (cfg.continuation_hold_bars <= 1)
        | (np.isfinite(bars_since_above_lost) & (bars_since_above_lost >= cfg.continuation_hold_bars - 1))
    )
    sustained_below = below_prev_range & (
        (cfg.continuation_hold_bars <= 1)
        | (np.isfinite(bars_since_below_lost) & (bars_since_below_lost >= cfg.continuation_hold_bars - 1))
    )
    above_prev_range_score = soft_above_range_score(close, prev_range_high, atr_v)
    below_prev_range_score = soft_below_range_score(close, prev_range_low, atr_v)
    sustained_above_score = soft_hold_strength(above_prev_range_score, cfg.continuation_hold_bars)
    sustained_below_score = soft_hold_strength(below_prev_range_score, cfg.continuation_hold_bars)
    range_break_up_evidence = np.nan_to_num(recent_range_break_up_strength, nan=0.0) * 0.65
    range_break_dn_evidence = np.nan_to_num(recent_range_break_dn_strength, nan=0.0) * 0.65
    range_cont_up_base = np.maximum(
        range_break_up_evidence,
        np.where(recent_ma_cross_up, 65.0, np.where(close > range_mid, 35.0, 0.0)),
    )
    range_cont_dn_base = np.maximum(
        range_break_dn_evidence,
        np.where(recent_ma_cross_dn, 65.0, np.where(close < range_mid, 35.0, 0.0)),
    )
    range_cont_up = np.maximum(
        range_cont_up_base,
        np.maximum(
            np.nan_to_num(above_prev_range_score, nan=0.0) * 0.80,
            np.nan_to_num(sustained_above_score, nan=0.0),
        ),
    )
    range_cont_dn = np.maximum(
        range_cont_dn_base,
        np.maximum(
            np.nan_to_num(below_prev_range_score, nan=0.0) * 0.80,
            np.nan_to_num(sustained_below_score, nan=0.0),
        ),
    )

    ma_spread_atr = safe_div(ma_log - maturity_ma_log, sym_atr)
    ma_spread_expanding_up = ma_spread_atr > shift(ma_spread_atr)
    ma_spread_expanding_dn = ma_spread_atr < shift(ma_spread_atr)
    ma_bull_spread = clamp(
        weighted(
            np.where(ma > maturity_ma, 100.0, 0.0),
            0.35,
            np.where(ma > shift(ma), 100.0, 0.0),
            0.25,
            np.where(maturity_ma >= shift(maturity_ma), 100.0, 0.0),
            0.15,
            np.where(ma_spread_expanding_up, 100.0, 0.0),
            0.25,
        ),
        0.0,
        100.0,
    )
    ma_bear_spread = clamp(
        weighted(
            np.where(ma < maturity_ma, 100.0, 0.0),
            0.35,
            np.where(ma < shift(ma), 100.0, 0.0),
            0.25,
            np.where(maturity_ma <= shift(maturity_ma), 100.0, 0.0),
            0.15,
            np.where(ma_spread_expanding_dn, 100.0, 0.0),
            0.25,
        ),
        0.0,
        100.0,
    )
    markup_continuation_score = clamp(
        weighted(
            range_cont_up,
            0.30,
            ma_bull_spread,
            0.25,
            markup_extension_score,
            0.25,
            100.0 - np.maximum(upside_exhaustion, resistance_holding),
            0.10,
            structure_strong,
            0.10,
        ),
        0.0,
        100.0,
    )
    markdown_continuation_score = clamp(
        weighted(
            range_cont_dn,
            0.30,
            ma_bear_spread,
            0.25,
            markdown_extension_score,
            0.25,
            100.0 - np.maximum(downside_exhaustion, support_holding),
            0.10,
            structure_weak,
            0.10,
        ),
        0.0,
        100.0,
    )

    range_cont_up_gate = gate(range_cont_up, 55.0, 90.0)
    range_cont_dn_gate = gate(range_cont_dn, 55.0, 90.0)
    ma_bull_spread_gate = gate(ma_bull_spread, 50.0, 85.0)
    ma_bear_spread_gate = gate(ma_bear_spread, 50.0, 85.0)
    markup_cont_support = gate(markup_continuation_score, 45.0, cfg.trend_ext_threshold)
    markdown_cont_support = gate(markdown_continuation_score, 45.0, cfg.trend_ext_threshold)
    non_markup_cont_gate = gate(100.0 - markup_continuation_score, 15.0, 60.0)
    non_markdown_cont_gate = gate(100.0 - markdown_continuation_score, 15.0, 60.0)

    # Six raw scores and stage gates.
    # Issue #66 B-6: shared reciprocal Stage-1/Stage-4 quiet-range context.
    issue66_quiet_range_context = low_vol_score
    acc_raw0 = weighted(bear_maturity_trace, 0.20, range_score, 0.20, downside_exhaustion, 0.25, support_holding, 0.25, issue66_quiet_range_context, 0.10)
    acc_trace_for_markup = rolling_highest(acc_raw0, cfg.absorb_len)
    markup_base_raw = weighted(breakout_score, 0.20, heat_up, 0.20, structure_strong, 0.20, markup_extension_score, 0.25, markup_continuation_score, 0.15)
    markup_raw0 = weighted(markup_base_raw, 0.85, acc_trace_for_markup, 0.15)
    # Issue #66 B-5: shared reciprocal Stage-3/Stage-6 counter-pressure primitive.
    def issue66_non_opposite_heat(opposite_heat):
        return 100.0 - opposite_heat

    reacc_raw0 = weighted(bull_bg, 0.20, range_score, 0.20, support_holding, 0.25, issue66_non_opposite_heat(panic_heat_dn), 0.20, 100.0 - upside_exhaustion, 0.15)
    dist_raw0 = weighted(bull_maturity_trace, 0.20, range_score, 0.20, upside_exhaustion, 0.25, resistance_holding, 0.25, issue66_quiet_range_context, 0.10)
    markdown_base_raw = weighted(explicit_breakdown_score, 0.20, panic_heat_dn, 0.20, structure_weak, 0.20, markdown_extension_score, 0.25, markdown_continuation_score, 0.15)
    dist_trace_for_markdown = rolling_highest(dist_raw0, cfg.absorb_len)
    markdown_raw0 = weighted(markdown_base_raw, 0.85, dist_trace_for_markdown, 0.15)
    rebound_failure = weighted(heat_up, 0.30, bear_structure, 0.45, 100.0 - bull_structure, 0.25)
    redist_raw0 = weighted(bear_bg, 0.20, range_score, 0.20, resistance_holding, 0.25, issue66_non_opposite_heat(heat_up), 0.20, 100.0 - downside_exhaustion, 0.15)

    acc_raw = ema(clamp(acc_raw0, 0.0, 100.0), cfg.stage_smooth_len)
    markup_raw = ema(clamp(markup_raw0, 0.0, 100.0), cfg.stage_smooth_len)
    reacc_raw = ema(clamp(reacc_raw0, 0.0, 100.0), cfg.stage_smooth_len)
    dist_raw = ema(clamp(dist_raw0, 0.0, 100.0), cfg.stage_smooth_len)
    markdown_raw = ema(clamp(markdown_raw0, 0.0, 100.0), cfg.stage_smooth_len)
    redist_raw = ema(clamp(redist_raw0, 0.0, 100.0), cfg.stage_smooth_len)

    range_gate = gate(range_score, 35.0, 70.0)
    uptrend_gate = gate(bull_bg, 45.0, 80.0)
    downtrend_gate = gate(bear_bg, 45.0, 80.0)
    mature_bull_gate = gate(bull_maturity_trace, 60.0, 85.0)  # retained diagnostic compatibility

    # Issue #66 B-7: one direction-neutral background/maturity gate for Stage 1/4.
    def issue66_background_maturity_gate(background, maturity_trace):
        return gate(np.maximum(background, maturity_trace), 35.0, 75.0)

    bear_background_acc_gate = issue66_background_maturity_gate(bear_bg, bear_maturity_trace)
    bull_background_dist_gate = issue66_background_maturity_gate(bull_bg, bull_maturity_trace)
    # Issue #68 HARD current-context cap — exact symmetric production candidate.
    current_bear_gate = gate(bear_bg, 35.0, 75.0)
    current_bull_gate = gate(bull_bg, 35.0, 75.0)
    ctx_down_ex_gate = np.minimum(downside_exhaustion_gate, current_bear_gate)
    ctx_up_ex_gate = np.minimum(upside_exhaustion_gate, current_bull_gate)
    # Diagnostic component gates are retained as mirrored decompositions of the
    # shared primitive. The classifier-facing gates are exactly score / 100.
    breakout_recent_range_gate = clamp(breakout_range_evidence / 100.0, 0.0, 1.0)
    breakout_ma_gate = clamp(breakout_ma_evidence / 100.0, 0.0, 1.0)
    breakout_recent_gate = np.maximum(breakout_recent_range_gate, breakout_ma_gate)
    breakout_gate = issue66_breakout_gate
    explicit_recent_breakdown_gate = clamp(breakdown_range_evidence / 100.0, 0.0, 1.0)
    explicit_breakdown_ma_gate = clamp(breakdown_ma_evidence / 100.0, 0.0, 1.0)
    explicit_breakdown_gate = issue66_breakdown_gate
    structure_strong_gate = gate(structure_strong, 40.0, 100.0)
    structure_weak_gate = gate(structure_weak, 40.0, 100.0)
    rebound_failure_gate = gate(rebound_failure, 40.0, 80.0)
    non_end_up_gate = gate(non_end_risk_up, 35.0, 80.0)
    non_end_dn_gate = gate(100.0 - end_risk_dn, 35.0, 80.0)
    non_range_gate = gate(non_range_score, cfg.non_range_gate_start, cfg.non_range_gate_full)
    non_panic_gate = gate(non_panic_score, 50.0, 85.0)
    non_heat_gate = gate(non_heat_score, 50.0, 85.0)

    # Issue #66 B-3: one direction-neutral fresh trend-entry gate.
    def issue66_trend_entry_gate(break_gate, structure_gate, non_end_gate):
        return break_gate * structure_gate * non_end_gate

    breakout_markup_gate = issue66_trend_entry_gate(breakout_gate, structure_strong_gate, non_end_up_gate)
    markup_extension_gate = uptrend_gate * structure_strong_gate * non_range_gate * gate(heat_up, 45.0, 80.0) * non_panic_gate * markup_extension_support
    markup_cont_gate = range_cont_up_gate * ma_bull_spread_gate * markup_cont_support * structure_strong_gate * gate(100.0 - np.maximum(upside_exhaustion, resistance_holding), 20.0, 70.0)
    breakdown_markdown_gate = issue66_trend_entry_gate(explicit_breakdown_gate, structure_weak_gate, non_end_dn_gate)
    markdown_extension_gate = downtrend_gate * structure_weak_gate * non_range_gate * gate(panic_heat_dn, 45.0, 80.0) * non_heat_gate * markdown_extension_support
    markdown_cont_gate = range_cont_dn_gate * ma_bear_spread_gate * markdown_cont_support * structure_weak_gate * gate(100.0 - np.maximum(downside_exhaustion, support_holding), 20.0, 70.0)

    acc_gate = range_gate * bear_background_acc_gate * ctx_down_ex_gate * support_holding_gate * non_markdown_cont_gate
    markup_gate = np.maximum(np.maximum(breakout_markup_gate, markup_extension_gate), markup_cont_gate)
    reacc_gate = range_gate * uptrend_gate * support_holding_gate * non_distribution_gate * gate(100.0 - bear_pressure_rising, 25.0, 75.0) * non_markup_cont_gate
    dist_gate = range_gate * bull_background_dist_gate * ctx_up_ex_gate * resistance_holding_gate * non_markup_cont_gate
    markdown_gate = np.maximum(np.maximum(breakdown_markdown_gate, markdown_extension_gate), markdown_cont_gate)
    redist_gate = range_gate * downtrend_gate * resistance_holding_gate * rebound_failure_gate * non_absorption_gate * non_markdown_cont_gate

    # Issue #68 production volume witness multipliers.
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
    effective = np.column_stack([acc_eff, markup_eff, reacc_eff, dist_eff, markdown_eff, redist_eff])

    # Pine uses direct addition, so any NA component keeps effTotal NA.
    eff_total = effective.sum(axis=1)
    has_enough_eff = np.isfinite(eff_total) & (eff_total > cfg.min_eff_total)
    sharp = np.power(np.maximum(np.nan_to_num(effective, nan=0.0), 0.0), cfg.regime_gamma)
    sharp_total = sharp.sum(axis=1)
    has_sharp = has_enough_eff & (sharp_total > 0.0)
    probabilities = np.full_like(sharp, np.nan)
    probabilities[has_sharp] = sharp[has_sharp] / sharp_total[has_sharp, None] * 100.0

    top_id, top_value, second_id, second_value = _top_two(probabilities)
    top_gap = top_value - second_value

    # Issue #68 evidence strength uses the production volume witness when active.
    max_eff = np.max(effective, axis=1)
    eff_total_strength = gate(eff_total, cfg.min_eff_total, cfg.evidence_eff_full) * 100.0
    top_eff_strength = gate(max_eff, 0.0, cfg.evidence_top_full) * 100.0
    top_gap_strength = gate(top_gap, cfg.top_gap_min, 35.0) * 100.0
    stage_support = np.full(n, np.nan, dtype=float)
    for i in range(n):
        if top_id[i] == 1:
            stage_support[i] = weighted(downside_exhaustion[i], 0.50, support_holding[i], 0.50)
        elif top_id[i] == 2:
            stage_support[i] = weighted(markup_extension_score[i], 0.45, markup_continuation_score[i], 0.35, max(breakout_score[i], structure_strong[i]), 0.20)
        elif top_id[i] == 3:
            stage_support[i] = weighted(support_holding[i], 0.50, 100.0 - upside_exhaustion[i], 0.50)
        elif top_id[i] == 4:
            stage_support[i] = weighted(upside_exhaustion[i], 0.50, resistance_holding[i], 0.50)
        elif top_id[i] == 5:
            stage_support[i] = weighted(markdown_extension_score[i], 0.45, markdown_continuation_score[i], 0.35, max(explicit_breakdown_gate[i] * 100.0, panic_heat_dn[i]), 0.20)
        elif top_id[i] == 6:
            stage_support[i] = weighted(resistance_holding[i], 0.50, 100.0 - downside_exhaustion[i], 0.50)
    volume_support = np.zeros(n, dtype=float)
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
    has_evidence = np.isfinite(evidence) & (evidence >= cfg.evidence_min)
    has_high_evidence = np.isfinite(evidence) & (evidence >= cfg.evidence_high)

    # Price-only conflict logic: witness clauses are intentionally absent.
    p1, p2, p3, p4, p5, p6 = [np.nan_to_num(probabilities[:, i], nan=0.0) for i in range(6)]
    low_stage_dispute = (
        (range_gate > 0.35)
        & (downtrend_gate > 0.25)
        & (p1 >= cfg.stage_dispute_min_weight)
        & (p6 >= cfg.stage_dispute_min_weight)
        & (np.abs(p1 - p6) <= cfg.stage_dispute_max_gap)
    )
    high_stage_dispute = (
        (range_gate > 0.35)
        & (uptrend_gate > 0.25)
        & (p3 >= cfg.stage_dispute_min_weight)
        & (p4 >= cfg.stage_dispute_min_weight)
        & (np.abs(p3 - p4) <= cfg.stage_dispute_max_gap)
    )
    trend_stage_dispute = (
        (markup_extension_score >= cfg.trend_ext_threshold)
        & (p2 >= cfg.stage_dispute_min_weight)
        & (p4 >= cfg.stage_dispute_min_weight)
        & (np.abs(p2 - p4) <= cfg.stage_dispute_max_gap)
    ) | (
        (markdown_extension_score >= cfg.trend_ext_threshold)
        & (p5 >= cfg.stage_dispute_min_weight)
        & (p1 >= cfg.stage_dispute_min_weight)
        & (np.abs(p5 - p1) <= cfg.stage_dispute_max_gap)
    )

    markup_cont_override = (
        (markup_continuation_score >= cfg.trend_ext_threshold)
        & (markup_extension_score >= cfg.trend_ext_threshold)
        & (ma_bull_spread >= 55.0)
    )
    markdown_cont_override = (
        (markdown_continuation_score >= cfg.trend_ext_threshold)
        & (markdown_extension_score >= cfg.trend_ext_threshold)
        & (ma_bear_spread >= 55.0)
    )

    candidate_conflict = np.zeros(n, dtype=bool)
    candidate_conflict |= (top_id == 6) & (downside_exhaustion >= cfg.absorb_threshold) & (support_holding >= cfg.absorb_threshold) & ~markdown_cont_override
    # Issue #66 C-2: Stage 1 is the reciprocal mirror of canonical Stage 4 conflict.
    candidate_conflict |= (top_id == 1) & (resistance_holding >= cfg.absorb_threshold) & (upside_exhaustion >= cfg.absorb_threshold) & ~markdown_cont_override
    candidate_conflict |= (top_id == 4) & (support_holding >= cfg.absorb_threshold) & (downside_exhaustion >= cfg.absorb_threshold) & ~markup_cont_override
    candidate_conflict |= (top_id == 3) & (upside_exhaustion >= cfg.absorb_threshold) & (resistance_holding >= cfg.absorb_threshold) & ~markup_cont_override
    candidate_conflict |= (top_id == 2) & (upside_exhaustion >= cfg.absorb_threshold) & (resistance_holding >= cfg.absorb_threshold) & ~markup_cont_override
    candidate_conflict |= (top_id == 5) & (downside_exhaustion >= cfg.absorb_threshold) & (support_holding >= cfg.absorb_threshold) & ~markdown_cont_override

    chaos = (~has_sharp) | (top_value < cfg.dominant_min) | ((evidence < 25.0) & (top_value < cfg.high_confidence))
    coexist = (
        has_sharp
        & (top_value >= cfg.dominant_min)
        & (top_gap < cfg.top_gap_min)
        & (evidence >= 25.0)
    ) | low_stage_dispute | high_stage_dispute
    weak_candidate = has_sharp & (top_value >= cfg.dominant_min) & (top_gap >= cfg.top_gap_min) & ((~has_evidence) | candidate_conflict)
    strong_candidate = has_sharp & (top_value >= cfg.dominant_min) & (top_gap >= cfg.top_gap_min) & has_evidence & (~candidate_conflict)

    fast_markup = (
        strong_candidate
        & (top_id == 2)
        & (top_value >= cfg.fast_switch_weight)
        & (top_gap >= cfg.fast_switch_gap)
        & (evidence >= cfg.fast_switch_evidence)
        & (markup_continuation_score >= cfg.fast_switch_ext)
        & (markup_extension_score >= cfg.trend_ext_threshold)
        & (close > ma)
        & (close > maturity_ma)
    )
    fast_markdown = (
        strong_candidate
        & (top_id == 5)
        & (top_value >= cfg.fast_switch_weight)
        & (top_gap >= cfg.fast_switch_gap)
        & (evidence >= cfg.fast_switch_evidence)
        & (markdown_continuation_score >= cfg.fast_switch_ext)
        & (markdown_extension_score >= cfg.trend_ext_threshold)
        & (close < ma)
        & (close < maturity_ma)
    )
    fast_switch = fast_markup | fast_markdown
    active_confirm_bars = np.where(fast_switch, cfg.fast_switch_confirm_bars, cfg.confirm_bars)

    # Phase B persistence redesign: preserve strong-candidate confirmation,
    # but let an unsupported old Formal state decay to neutral after 2x the
    # existing confirm_bars horizon. Weak challengers are never promoted directly.
    formal_id = np.zeros(n, dtype=int)
    candidate_id = np.zeros(n, dtype=int)
    candidate_bars_series = np.zeros(n, dtype=int)
    candidate_display_id = np.where(strong_candidate | weak_candidate, top_id, 0).astype(int)
    stale_pressure_bars_series = np.zeros(n, dtype=int)
    stale_pressure_reason_series = np.zeros(n, dtype=int)
    confirmed = 0
    candidate = 0
    candidate_bars = 0
    stale_pressure_bars = 0
    stale_limit = cfg.confirm_bars * 2
    for i in range(n):
        if strong_candidate[i]:
            stale_pressure_bars = 0
            stale_reason = 0
            raw_id = int(top_id[i])
            if raw_id == candidate:
                candidate_bars += 1
            else:
                candidate = raw_id
                candidate_bars = 1
            if candidate_bars >= int(active_confirm_bars[i]):
                confirmed = candidate
        else:
            candidate = 0
            candidate_bars = 0
            display_id = int(candidate_display_id[i])
            weak_challenger = confirmed != 0 and display_id != 0 and display_id != confirmed
            coexist_pressure = confirmed != 0 and bool(coexist[i]) and display_id == 0
            if bool(chaos[i]) and confirmed != 0:
                stale_reason = 1
            elif weak_challenger:
                stale_reason = 2
            elif coexist_pressure:
                stale_reason = 3
            else:
                stale_reason = 0

            if stale_reason != 0:
                stale_pressure_bars += 1
                if stale_pressure_bars >= stale_limit:
                    confirmed = 0
            else:
                stale_pressure_bars = 0

        formal_id[i] = confirmed
        candidate_id[i] = candidate
        candidate_bars_series[i] = candidate_bars
        stale_pressure_bars_series[i] = stale_pressure_bars
        stale_pressure_reason_series[i] = stale_reason

    diagnostics = {
        "speed_rank": speed_rank,
        "accel_rank": accel_rank,
        "dist_rank": dist_rank,
        "heat_up": heat_up,
        "panic_heat_dn": panic_heat_dn,
        "maturity_up": maturity_up,
        "maturity_dn": maturity_dn,
        "end_risk_up": end_risk_up,
        "end_risk_dn": end_risk_dn,
        "range_score": range_score,
        "sym_atr": sym_atr,
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
        "issue66_b1_ma_log": ma_log,
        "issue66_b1_maturity_ma_log": maturity_ma_log,
        "issue66_b1_sym_atr": sym_atr,
        "issue66_b1_maturity_sym_atr": maturity_sym_atr,
        "issue66_b1_dist_atr": dist_atr,
        "issue66_b1_maturity_dist_atr": maturity_dist_atr,
        "issue66_b1_atr_pct": atr_pct,
        "issue66_b1_range_width_atr": range_width_atr,
        "issue66_b1_ma_spread_atr": ma_spread_atr,
        "no_break_low_score": no_break_low_score,
        "no_break_high_score": no_break_high_score,
        "prev_range_high": prev_range_high,
        "prev_range_low": prev_range_low,
        "above_prev_range": above_prev_range.astype(float),
        "below_prev_range": below_prev_range.astype(float),
        "above_prev_range_score": above_prev_range_score,
        "below_prev_range_score": below_prev_range_score,
        "sustained_above_score": sustained_above_score,
        "sustained_below_score": sustained_below_score,
        "range_high_break": range_high_break,
        "range_low_break": range_low_break,
        "range_break_up": range_break_up.astype(float),
        "range_break_dn": range_break_dn.astype(float),
        "range_break_up_strength": range_break_up_strength,
        "range_break_dn_strength": range_break_dn_strength,
        "recent_range_break_up_strength": recent_range_break_up_strength,
        "recent_range_break_dn_strength": recent_range_break_dn_strength,
        "ma_cross_up": ma_cross_up.astype(float),
        "ma_cross_dn": ma_cross_dn.astype(float),
        "recent_break_up": recent_break_up.astype(float),
        "recent_break_dn": recent_break_dn.astype(float),
        "recent_range_break_dn": recent_range_break_dn.astype(float),
        "recent_ma_cross_up": recent_ma_cross_up.astype(float),
        "recent_ma_cross_dn": recent_ma_cross_dn.astype(float),
        "breakout_mode_up": breakout_mode_up.astype(float),
        "breakdown_mode_dn": breakdown_mode_dn.astype(float),
        "range_cont_up": range_cont_up,
        "range_cont_dn": range_cont_dn,
        "breakout_score": breakout_score,
        "issue66_b2_breakout_range_component": breakout_range_evidence,
        "issue66_b2_breakdown_range_component": breakdown_range_evidence,
        "issue66_b2_breakout_ma_component": breakout_ma_evidence,
        "issue66_b2_breakdown_ma_component": breakdown_ma_evidence,
        "issue66_b2_breakout_gate": breakout_gate,
        "issue66_b2_breakdown_gate": explicit_breakdown_gate,
        "explicit_breakdown_score": explicit_breakdown_score,
        "breakout_recent_range_gate": breakout_recent_range_gate,
        "breakout_ma_gate": breakout_ma_gate,
        "breakout_recent_gate": breakout_recent_gate,
        "explicit_recent_breakdown_gate": explicit_recent_breakdown_gate,
        "explicit_breakdown_ma_gate": explicit_breakdown_ma_gate,
        "breakout_gate": breakout_gate,
        "explicit_breakdown_gate": explicit_breakdown_gate,
        "range_cont_up_gate": range_cont_up_gate,
        "range_cont_dn_gate": range_cont_dn_gate,
        "markup_continuation_score": markup_continuation_score,
        "markdown_continuation_score": markdown_continuation_score,
        "breakout_markup_gate": breakout_markup_gate,
        "issue66_b3_non_end_up_gate": non_end_up_gate,
        "issue66_b3_non_end_dn_gate": non_end_dn_gate,
        "issue66_b3_markup_entry_gate": breakout_markup_gate,
        "issue66_b3_markdown_entry_gate": breakdown_markdown_gate,
        "breakdown_markdown_gate": breakdown_markdown_gate,
        "markup_cont_gate": markup_cont_gate,
        "markdown_cont_gate": markdown_cont_gate,
        "markup_gate": markup_gate,
        "markdown_gate": markdown_gate,
        "downside_exhaustion": downside_exhaustion,
        "upside_exhaustion": upside_exhaustion,
        "support_holding": support_holding,
        "resistance_holding": resistance_holding,
        "markup_extension_score": markup_extension_score,
        "markdown_extension_score": markdown_extension_score,
        "markup_continuation_score": markup_continuation_score,
        "markdown_continuation_score": markdown_continuation_score,
        "acc_raw": acc_raw,
        "issue66_b6_quiet_range_context": issue66_quiet_range_context,
        "markup_raw": markup_raw,
        "reacc_raw": reacc_raw,
        "issue66_b5_reacc_non_opposite_heat": issue66_non_opposite_heat(panic_heat_dn),
        "issue66_b5_redist_non_opposite_heat": issue66_non_opposite_heat(heat_up),
        "dist_raw": dist_raw,
        "markdown_raw": markdown_raw,
        "redist_raw": redist_raw,
        "acc_gate": acc_gate,
        "issue66_b7_bear_background_acc_gate": bear_background_acc_gate,
        "issue66_b7_bull_background_dist_gate": bull_background_dist_gate,
        "markup_gate": markup_gate,
        "reacc_gate": reacc_gate,
        "dist_gate": dist_gate,
        "markdown_gate": markdown_gate,
        "redist_gate": redist_gate,
        "acc_eff": acc_eff,
        "markup_eff": markup_eff,
        "reacc_eff": reacc_eff,
        "dist_eff": dist_eff,
        "markdown_eff": markdown_eff,
        "redist_eff": redist_eff,
        "prob_acc": probabilities[:, 0],
        "prob_markup": probabilities[:, 1],
        "prob_reacc": probabilities[:, 2],
        "prob_dist": probabilities[:, 3],
        "prob_markdown": probabilities[:, 4],
        "prob_redist": probabilities[:, 5],
        "top_id": top_id,
        "top_value": top_value,
        "second_id": second_id,
        "top_gap": top_gap,
        "evidence_strength": evidence,
        "has_high_evidence": has_high_evidence,
        "low_stage_dispute": low_stage_dispute,
        "high_stage_dispute": high_stage_dispute,
        "trend_stage_dispute": trend_stage_dispute,
        "candidate_conflict": candidate_conflict,
        "chaos": chaos,
        "coexist": coexist,
        "weak_candidate": weak_candidate,
        "strong_candidate": strong_candidate,
        "fast_switch": fast_switch,
        "candidate_id": candidate_id,
        "candidate_bars": candidate_bars_series,
        "candidate_display_id": candidate_display_id,
        "formal_id": formal_id,
        "stale_pressure_bars": stale_pressure_bars_series,
        "stale_pressure_reason": stale_pressure_reason_series,
    }
    for name, values in diagnostics.items():
        out[name] = values
    out["candidate_stage"] = [STAGE_NAMES[int(stage)] for stage in candidate_display_id]
    out["formal_stage"] = [STAGE_NAMES[int(stage)] for stage in formal_id]
    return out


def load_ohlc(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    lower = {column.lower(): column for column in frame.columns}
    missing = [name for name in ("open", "high", "low", "close") if name not in lower]
    if missing:
        raise ValueError(f"input must contain OHLC columns; missing {missing}")
    rename = {lower[name]: name for name in ("open", "high", "low", "close")}
    for date_name in ("date", "datetime", "time"):
        if date_name in lower:
            rename[lower[date_name]] = "date"
            break
    return frame.rename(columns=rename)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run frozen Wyckoff v0.5.2.1 price-only mirror")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = compute_price_only(load_ohlc(args.input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)


if __name__ == "__main__":
    main()
