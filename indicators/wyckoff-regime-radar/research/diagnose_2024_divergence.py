#!/usr/bin/env python3
"""Trace the Python/Yahoo decision chain for the 2024-04-16 Issue #55 divergence.

This is diagnostic only. It intentionally does not alter model parameters or
claim parity. The output lines up with the focused TradingView/OANDA deep table,
inspects the binary previous-low test, and sweeps only the target bar close to
measure how discontinuously that threshold changes the frozen classification.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from compare_reference_feed import DEFAULT_TICKER, download_yahoo, normalize_ohlc
from price_only_core import PriceOnlyConfig, compute_price_only


TARGET = "2024-04-16"
DISPLAY_FIELDS = [
    "speed_rank",
    "accel_rank",
    "dist_rank",
    "heat_up",
    "panic_heat_dn",
    "maturity_up",
    "maturity_dn",
    "range_score",
    "upside_exhaustion",
    "resistance_holding",
    "dist_raw",
    "dist_gate",
    "dist_eff",
    "prob_dist",
    "top_gap",
    "evidence_strength",
    "downside_exhaustion",
    "support_holding",
    "markdown_extension_score",
    "markdown_continuation_score",
    "markdown_raw",
    "markdown_gate",
    "markdown_eff",
    "prob_markdown",
]
SENSITIVITY_PIP_DELTAS = [-8.0, -6.0, -4.0, -3.0, -2.5, -2.2, -2.15, -2.14, -2.1, -2.0, -1.0, 0.0, 1.0, 2.0]


def _number(value, *, percent_gate: bool = False):
    value = float(value)
    if not np.isfinite(value):
        return None
    if percent_gate:
        value *= 100.0
    return value


def _close_sensitivity_sweep(ohlc: pd.DataFrame, idx: int, cfg: PriceOnlyConfig, prev_abs_low: float | None) -> list[dict]:
    prefix = ohlc.iloc[: idx + 1].copy().reset_index(drop=True)
    base_close = float(prefix.loc[len(prefix) - 1, "close"])
    low = float(prefix.loc[len(prefix) - 1, "low"])
    high = float(prefix.loc[len(prefix) - 1, "high"])
    rows: list[dict] = []
    for delta_pips in SENSITIVITY_PIP_DELTAS:
        variant_close = base_close + delta_pips / 10_000.0
        if variant_close < low or variant_close > high:
            rows.append({"delta_pips": delta_pips, "status": "outside_original_high_low"})
            continue
        variant = prefix.copy()
        variant.loc[len(variant) - 1, "close"] = variant_close
        variant_result = compute_price_only(variant, cfg).iloc[-1]
        no_break = None if prev_abs_low is None else (100.0 if variant_close > prev_abs_low else 0.0)
        rows.append(
            {
                "delta_pips": delta_pips,
                "close": variant_close,
                "close_minus_prev_50bar_low_pips": None if prev_abs_low is None else (variant_close - prev_abs_low) * 10_000.0,
                "no_break_low_score": no_break,
                "downside_exhaustion": _number(variant_result["downside_exhaustion"]),
                "support_holding": _number(variant_result["support_holding"]),
                "markdown_continuation_score": _number(variant_result["markdown_continuation_score"]),
                "dist_gate_pct": _number(variant_result["dist_gate"], percent_gate=True),
                "markdown_gate_pct": _number(variant_result["markdown_gate"], percent_gate=True),
                "prob_dist": _number(variant_result["prob_dist"]),
                "prob_markdown": _number(variant_result["prob_markdown"]),
                "candidate": int(variant_result["candidate_display_id"]),
                "formal": int(variant_result["formal_id"]),
            }
        )
    return rows


def build_report(ticker: str, reference_path: Path, deep_reference_path: Path) -> dict:
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    deep_reference = json.loads(deep_reference_path.read_text(encoding="utf-8"))
    _, downloaded = download_yahoo(ticker)
    ohlc = normalize_ohlc(downloaded)
    cfg = PriceOnlyConfig()
    result = compute_price_only(ohlc, cfg)

    target = pd.Timestamp(TARGET).date()
    matches = result.index[result["date"] >= target].tolist()
    if not matches:
        raise ValueError(f"no Yahoo bar at or after {TARGET}")
    idx = matches[0]
    row = result.loc[idx]

    tv_ref = next(item for item in reference["rows"] if item["target_date"] == TARGET)
    values = {}
    for field in DISPLAY_FIELDS:
        values[field] = _number(row[field], percent_gate=field in {"dist_gate", "markdown_gate"})

    # Recreate the Pine primitive exactly: prevAbsLow = ta.lowest(low[1], absorbLen).
    low_series = pd.to_numeric(ohlc["low"], errors="coerce")
    prev_abs_low_series = low_series.shift(1).rolling(cfg.absorb_len, min_periods=cfg.absorb_len).min()
    abs_range_low_series = low_series.rolling(cfg.absorb_len, min_periods=cfg.absorb_len).min()
    high_series = pd.to_numeric(ohlc["high"], errors="coerce")
    abs_range_high_series = high_series.rolling(cfg.absorb_len, min_periods=cfg.absorb_len).max()

    prev_abs_low = _number(prev_abs_low_series.iloc[idx])
    abs_range_low = _number(abs_range_low_series.iloc[idx])
    abs_range_high = _number(abs_range_high_series.iloc[idx])
    public_close = _number(row["close"])
    if prev_abs_low is None or public_close is None:
        no_break_low_score = None
        close_minus_prev_low = None
        close_minus_prev_low_pips = None
    else:
        no_break_low_score = 100.0 if public_close > prev_abs_low else 0.0
        close_minus_prev_low = public_close - prev_abs_low
        close_minus_prev_low_pips = close_minus_prev_low * 10_000.0

    tv_support = float(deep_reference["values"]["support_holding"])
    # In either supportHolding branch, noBreakLowScore=100 contributes at least
    # 35 points and every other term is non-negative. TV observed 9.9, so the
    # OANDA primitive is logically forced to 0 without needing another screenshot.
    tv_no_break_low_forced_zero = tv_support < 35.0

    threshold_trace = {
        "pine_rule": "noBreakLowScore = close > prevAbsLow ? 100 : 0; prevAbsLow = lowest(low[1], 50)",
        "yahoo_prev_50bar_low": prev_abs_low,
        "yahoo_current_50bar_low": abs_range_low,
        "yahoo_current_50bar_high": abs_range_high,
        "yahoo_close": public_close,
        "yahoo_close_minus_prev_50bar_low": close_minus_prev_low,
        "yahoo_close_minus_prev_50bar_low_pips": close_minus_prev_low_pips,
        "yahoo_no_break_low_score": no_break_low_score,
        "tradingview_oanda_support_holding": tv_support,
        "tradingview_oanda_no_break_low_score_forced_zero": tv_no_break_low_forced_zero,
        "inference_reason": "supportHolding=9.9 is below the minimum possible value if noBreakLowScore were 100, because that binary term alone contributes at least 35 points and all remaining terms are non-negative.",
    }

    neighbor_fields = [
        "date",
        "close",
        "prob_dist",
        "prob_markdown",
        "dist_gate",
        "markdown_gate",
        "dist_eff",
        "markdown_eff",
        "candidate_display_id",
        "formal_id",
    ]
    start = max(0, idx - 3)
    stop = min(len(result), idx + 4)
    neighbors = []
    for neighbor_idx, neighbor in result.loc[start : stop - 1, neighbor_fields].iterrows():
        neighbor_prev_low = _number(prev_abs_low_series.iloc[neighbor_idx])
        neighbor_close = _number(neighbor["close"])
        neighbor_no_break = None
        if neighbor_prev_low is not None and neighbor_close is not None:
            neighbor_no_break = 100.0 if neighbor_close > neighbor_prev_low else 0.0
        neighbors.append(
            {
                "date": str(neighbor["date"]),
                "close": neighbor_close,
                "prev_50bar_low": neighbor_prev_low,
                "no_break_low_score": neighbor_no_break,
                "prob_dist": _number(neighbor["prob_dist"]),
                "prob_markdown": _number(neighbor["prob_markdown"]),
                "dist_gate_pct": _number(neighbor["dist_gate"], percent_gate=True),
                "markdown_gate_pct": _number(neighbor["markdown_gate"], percent_gate=True),
                "dist_eff": _number(neighbor["dist_eff"]),
                "markdown_eff": _number(neighbor["markdown_eff"]),
                "candidate": int(neighbor["candidate_display_id"]),
                "formal": int(neighbor["formal_id"]),
            }
        )

    binary_split_confirmed = bool(tv_no_break_low_forced_zero and no_break_low_score == 100.0)
    sensitivity = _close_sensitivity_sweep(ohlc, idx, cfg, prev_abs_low)

    return {
        "status": "diagnostic_cross_feed_only",
        "target_date": TARGET,
        "public_feed": "Yahoo Finance via yfinance",
        "ticker": ticker,
        "public_bar_date": str(row["date"]),
        "public_close": public_close,
        "tradingview_oanda_reference": {
            "actual_bar_date": tv_ref["actual_bar_date"],
            "close": tv_ref["close"],
            "prob_dist": tv_ref["prob_dist"],
            "prob_markdown": tv_ref["prob_markdown"],
            "top_gap": tv_ref["top_gap"],
            "evidence_strength": tv_ref["evidence_strength"],
            "candidate": tv_ref["candidate_display_id"],
            "formal": tv_ref["formal_id"],
        },
        "tradingview_oanda_deep_reference": deep_reference["values"],
        "python_yahoo_intermediate_values": values,
        "binary_previous_low_threshold_trace": threshold_trace,
        "binary_no_break_low_split_confirmed": binary_split_confirmed,
        "single_bar_close_sensitivity_sweep": sensitivity,
        "neighbor_window": neighbors,
        "boundary": "This isolates cross-feed threshold sensitivity; it does not prove full Pine/Python parity. The sensitivity sweep changes only the target Yahoo close for diagnosis and is not parameter tuning.",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    here = Path(__file__).resolve().parent
    parser.add_argument("--ticker", default=DEFAULT_TICKER)
    parser.add_argument(
        "--reference",
        type=Path,
        default=here / "fixtures" / "issue-55-oanda-eurusd-tv-checkpoints-v1.json",
    )
    parser.add_argument(
        "--deep-reference",
        type=Path,
        default=here / "fixtures" / "issue-55-oanda-eurusd-tv-2024-deep-v1.json",
    )
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_report(args.ticker, args.reference, args.deep_reference)
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
