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

    ma = rolling_sma(close, cfg.ma_len)
    atr_v = atr(high, low, close, cfg.atr_len)
    dist_atr = safe_div(close - ma, atr_v)

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
    maturity_ma = rolling_sma(close, cfg.maturity_ma_len)
    maturity_atr = atr(high, low, close, cfg.maturity_atr_len)
    maturity_dist_atr = safe_div(close - maturity_ma, maturity_atr)
    maturity_dist_rank = percentrank(maturity_dist_atr, cfg.rank_len)
    maturity_up = weighted(long_slope_rank, cfg.w_mat_slope, maturity_dist_rank, cfg.w_mat_dist)
    maturity_dn = weighted(100.0 - long_slope_rank, cfg.w_mat_slope, 100.0 - maturity_dist_rank, cfg.w_mat_dist)
    end_risk_up = safe_div(heat_up * maturity_up, 100.0)
    end_risk_dn = safe_div(panic_heat_dn * maturity_dn, 100.0)

    # Breakout / breakdown / low-vol exemption.
    atr_pct = safe_div(atr_v, close) * 100.0
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
    ma_cross_up = crossover(close, ma)
    ma_cross_dn = crossunder(close, ma)
    recent_break_up = recent(range_break_up | ma_cross_up, cfg.breakout_bars)
    recent_break_dn = recent(range_break_dn | ma_cross_dn, cfg.breakout_bars)
    recent_range_break_dn = recent(range_break_dn, cfg.breakout_bars)
    recent_ma_cross_dn = recent(ma_cross_dn, cfg.breakout_bars)

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
    range_width_atr = safe_div(range_width, atr_v)
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
    breakout_score = np.where(
        breakout_mode_up,
        100.0,
        np.where(recent_break_up, 70.0, np.where(close > ma, 35.0, 0.0)),
    )
    explicit_breakdown_score = np.where(
        breakdown_mode_dn,
        100.0,
        np.where(
            recent_range_break_dn,
            85.0,
            np.where(
                recent_ma_cross_dn & (panic_heat_dn >= cfg.orange_level) & (structure_weak >= 50.0),
                55.0,
                0.0,
            ),
        ),
    )

    # Absorption vs distribution layer: still price-only.
    abs_range_high = rolling_highest(high, cfg.absorb_len)
    abs_range_low = rolling_lowest(low, cfg.absorb_len)
    abs_range_mid = (abs_range_high + abs_range_low) / 2.0
    abs_range_width = abs_range_high - abs_range_low
    abs_range_pos = clamp(safe_div(close - abs_range_low, abs_range_width) * 100.0, 0.0, 100.0)
    prev_abs_low = rolling_lowest(shift(low), cfg.absorb_len)
    prev_abs_high = rolling_highest(shift(high), cfg.absorb_len)
    no_break_low_score = np.where(close > prev_abs_low, 100.0, 0.0)
    no_break_high_score = np.where(close < prev_abs_high, 100.0, 0.0)
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
    range_cont_up = np.where(sustained_above, 100.0, np.where(above_prev_range, 80.0, np.where(recent_break_up, 65.0, np.where(close > range_mid, 35.0, 0.0))))
    range_cont_dn = np.where(sustained_below, 100.0, np.where(below_prev_range, 80.0, np.where(recent_break_dn, 65.0, np.where(close < range_mid, 35.0, 0.0))))

    ma_spread_atr = safe_div(ma - maturity_ma, atr_v)
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
    acc_raw0 = weighted(bear_maturity_trace, 0.20, range_score, 0.20, downside_exhaustion, 0.25, support_holding, 0.25, low_vol_score, 0.10)
    acc_trace_for_markup = rolling_highest(acc_raw0, cfg.absorb_len)
    markup_base_raw = weighted(breakout_score, 0.20, heat_up, 0.20, structure_strong, 0.20, markup_extension_score, 0.25, markup_continuation_score, 0.15)
    markup_raw0 = weighted(markup_base_raw, 0.85, acc_trace_for_markup, 0.15)
    reacc_raw0 = weighted(bull_bg, 0.20, range_score, 0.20, support_holding, 0.25, 100.0 - panic_heat_dn, 0.20, 100.0 - upside_exhaustion, 0.15)
    dist_raw0 = weighted(bull_maturity_trace, 0.20, range_score, 0.20, upside_exhaustion, 0.25, resistance_holding, 0.25, bear_pressure_rising, 0.10)
    markdown_base_raw = weighted(explicit_breakdown_score, 0.20, panic_heat_dn, 0.20, structure_weak, 0.20, markdown_extension_score, 0.25, markdown_continuation_score, 0.15)
    dist_trace_for_markdown = rolling_highest(dist_raw0, cfg.absorb_len)
    markdown_raw0 = weighted(markdown_base_raw, 0.85, dist_trace_for_markdown, 0.15)
    rebound_failure = weighted(heat_up, 0.30, bear_structure, 0.45, 100.0 - bull_structure, 0.25)
    redist_raw0 = weighted(bear_bg, 0.20, range_score, 0.20, resistance_holding, 0.25, rebound_failure, 0.20, 100.0 - downside_exhaustion, 0.15)

    acc_raw = ema(clamp(acc_raw0, 0.0, 100.0), cfg.stage_smooth_len)
    markup_raw = ema(clamp(markup_raw0, 0.0, 100.0), cfg.stage_smooth_len)
    reacc_raw = ema(clamp(reacc_raw0, 0.0, 100.0), cfg.stage_smooth_len)
    dist_raw = ema(clamp(dist_raw0, 0.0, 100.0), cfg.stage_smooth_len)
    markdown_raw = ema(clamp(markdown_raw0, 0.0, 100.0), cfg.stage_smooth_len)
    redist_raw = ema(clamp(redist_raw0, 0.0, 100.0), cfg.stage_smooth_len)

    range_gate = gate(range_score, 35.0, 70.0)
    uptrend_gate = gate(bull_bg, 45.0, 80.0)
    downtrend_gate = gate(bear_bg, 45.0, 80.0)
    mature_bull_gate = gate(bull_maturity_trace, 60.0, 85.0)
    bear_background_acc_gate = gate(np.maximum(bear_bg, bear_maturity_trace), 35.0, 75.0)
    breakout_gate = np.where(breakout_mode_up, 1.0, np.where(recent_break_up, 0.85, gate(breakout_score, 30.0, 70.0)))
    explicit_breakdown_gate = np.where(breakdown_mode_dn, 1.0, np.where(recent_range_break_dn, 0.90, gate(explicit_breakdown_score, 50.0, 85.0)))
    structure_strong_gate = gate(structure_strong, 40.0, 100.0)
    structure_weak_gate = gate(structure_weak, 40.0, 100.0)
    rebound_failure_gate = gate(rebound_failure, 40.0, 80.0)
    non_end_up_gate = gate(non_end_risk_up, 35.0, 80.0)
    non_range_gate = gate(non_range_score, cfg.non_range_gate_start, cfg.non_range_gate_full)
    non_panic_gate = gate(non_panic_score, 50.0, 85.0)
    non_heat_gate = gate(non_heat_score, 50.0, 85.0)

    breakout_markup_gate = breakout_gate * structure_strong_gate * non_end_up_gate
    markup_extension_gate = uptrend_gate * structure_strong_gate * non_range_gate * gate(heat_up, 45.0, 80.0) * non_panic_gate * markup_extension_support
    markup_cont_gate = range_cont_up_gate * ma_bull_spread_gate * markup_cont_support * structure_strong_gate * gate(100.0 - np.maximum(upside_exhaustion, resistance_holding), 20.0, 70.0)
    breakdown_markdown_gate = explicit_breakdown_gate * gate(panic_heat_dn, 40.0, 80.0) * structure_weak_gate
    markdown_extension_gate = downtrend_gate * structure_weak_gate * non_range_gate * gate(panic_heat_dn, 45.0, 80.0) * non_heat_gate * markdown_extension_support
    markdown_cont_gate = range_cont_dn_gate * ma_bear_spread_gate * markdown_cont_support * structure_weak_gate * gate(100.0 - np.maximum(downside_exhaustion, support_holding), 20.0, 70.0)

    acc_gate = range_gate * bear_background_acc_gate * downside_exhaustion_gate * support_holding_gate * non_markdown_cont_gate
    markup_gate = np.maximum(np.maximum(breakout_markup_gate, markup_extension_gate), markup_cont_gate)
    reacc_gate = range_gate * uptrend_gate * support_holding_gate * non_distribution_gate * gate(100.0 - bear_pressure_rising, 25.0, 75.0) * non_markup_cont_gate
    dist_gate = range_gate * mature_bull_gate * upside_exhaustion_gate * resistance_holding_gate * non_markup_cont_gate
    markdown_gate = np.maximum(np.maximum(breakdown_markdown_gate, markdown_extension_gate), markdown_cont_gate)
    redist_gate = range_gate * downtrend_gate * resistance_holding_gate * rebound_failure_gate * non_absorption_gate * non_markdown_cont_gate

    acc_eff = acc_raw * acc_gate
    markup_eff = markup_raw * markup_gate
    reacc_eff = reacc_raw * reacc_gate
    dist_eff = dist_raw * dist_gate
    markdown_eff = markdown_raw * markdown_gate
    redist_eff = redist_raw * redist_gate
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

    # Evidence strength uses the price-only branch because all witnesses are off.
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
    evidence = weighted(eff_total_strength, 0.30, top_eff_strength, 0.25, top_gap_strength, 0.20, stage_support, 0.25)
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
    candidate_conflict |= (top_id == 1) & (resistance_holding >= cfg.absorb_threshold) & (rebound_failure_gate > 0.50) & ~markup_cont_override
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

    # Regime inertia: imperative loop mirrors Pine var state exactly.
    formal_id = np.zeros(n, dtype=int)
    candidate_id = np.zeros(n, dtype=int)
    candidate_bars_series = np.zeros(n, dtype=int)
    candidate_display_id = np.where(strong_candidate | weak_candidate, top_id, 0).astype(int)
    confirmed = 0
    candidate = 0
    candidate_bars = 0
    no_regime_bars = 0
    for i in range(n):
        if strong_candidate[i]:
            no_regime_bars = 0
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
            if chaos[i]:
                no_regime_bars += 1
                if no_regime_bars >= cfg.confirm_bars:
                    confirmed = 0
            else:
                no_regime_bars = 0
        formal_id[i] = confirmed
        candidate_id[i] = candidate
        candidate_bars_series[i] = candidate_bars

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
        "downside_exhaustion": downside_exhaustion,
        "upside_exhaustion": upside_exhaustion,
        "support_holding": support_holding,
        "resistance_holding": resistance_holding,
        "markup_extension_score": markup_extension_score,
        "markdown_extension_score": markdown_extension_score,
        "markup_continuation_score": markup_continuation_score,
        "markdown_continuation_score": markdown_continuation_score,
        "acc_raw": acc_raw,
        "markup_raw": markup_raw,
        "reacc_raw": reacc_raw,
        "dist_raw": dist_raw,
        "markdown_raw": markdown_raw,
        "redist_raw": redist_raw,
        "acc_gate": acc_gate,
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
