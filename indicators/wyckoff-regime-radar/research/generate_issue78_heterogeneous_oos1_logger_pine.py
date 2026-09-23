#!/usr/bin/env python3
"""Generate Issue #78 Heterogeneous OOS Challenge 1 daily forward logger.

This generator deliberately reuses the accepted Issue #76 forward-behavior
logger construction from the exact frozen Issue #68 RC source, then changes
only research identity/provenance and the preregistered allowed-feed whitelist.

Classifier semantics, representation logic, event lag, ATR scale, and exported
future-move fields remain unchanged.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue76_forward_behavior_logger_pine as base

OLD_DECL = 'indicator("Wyckoff Regime Radar｜Issue #76 Forward Behavior Logger", shorttitle="#76 Forward Logger", overlay=false, precision=1)'
NEW_DECL = 'indicator("Wyckoff Regime Radar｜Issue #78 Heterogeneous OOS1 Logger v3", shorttitle="#78 HET OOS1 v3", overlay=false, precision=1, calc_bars_count=10000)'

OLD_ALLOWED = 'issue76AllowedFeed = syminfo.tickerid == "OANDA:EURUSD" or syminfo.tickerid == "OANDA:GBPUSD" or syminfo.tickerid == "OANDA:USDJPY" or syminfo.tickerid == "TVC:US10Y" or syminfo.tickerid == "TVC:DE10Y" or syminfo.tickerid == "TVC:FR10Y" or syminfo.tickerid == "TVC:GB10Y" or syminfo.tickerid == "TVC:AU10Y" or syminfo.tickerid == "TVC:JP10Y"'
NEW_ALLOWED = 'issue76AllowedFeed = syminfo.tickerid == "TVC:SPX" or syminfo.tickerid == "NASDAQ:NDX" or syminfo.tickerid == "OANDA:XAUUSD" or syminfo.tickerid == "OANDA:XAGUSD" or syminfo.tickerid == "BITSTAMP:BTCUSD" or syminfo.tickerid == "BITSTAMP:ETHUSD"'

OLD_MARKER = '"ISSUE76|schema=1" +'
NEW_MARKER = '"ISSUE76|schema=1|cohort=HET_OOS1" +'


# Export-only memory safeguard.
# In the frozen Issue #68 RC, MTF defaults to "Observe Only", which forces
# mtfRawWeight to zero. The lower-timeframe arrays are therefore diagnostic-only
# and cannot affect stage scores/formalId. OOS1 v2 replaces just those eight
# array requests with empty arrays to avoid TradingView memory exhaustion on
# long-history feeds such as XAUUSD.
LIGHTWEIGHT_MTF_REPLACEMENTS = (
    ('ltfBearEffortArr0 = request.security_lower_tf(syminfo.tickerid, mtfLowerTf, f_ltfBearEffortBar(), ignore_invalid_timeframe=true)', 'ltfBearEffortArr0 = array.new_float(0)'),
    ('ltfBullEffortArr0 = request.security_lower_tf(syminfo.tickerid, mtfLowerTf, f_ltfBullEffortBar(), ignore_invalid_timeframe=true)', 'ltfBullEffortArr0 = array.new_float(0)'),
    ('ltfBearEffortArr1 = request.security_lower_tf(syminfo.tickerid, mtfFallbackTf1, f_ltfBearEffortBar(), ignore_invalid_timeframe=true)', 'ltfBearEffortArr1 = array.new_float(0)'),
    ('ltfBullEffortArr1 = request.security_lower_tf(syminfo.tickerid, mtfFallbackTf1, f_ltfBullEffortBar(), ignore_invalid_timeframe=true)', 'ltfBullEffortArr1 = array.new_float(0)'),
    ('ltfBearEffortArr2 = request.security_lower_tf(syminfo.tickerid, mtfFallbackTf2, f_ltfBearEffortBar(), ignore_invalid_timeframe=true)', 'ltfBearEffortArr2 = array.new_float(0)'),
    ('ltfBullEffortArr2 = request.security_lower_tf(syminfo.tickerid, mtfFallbackTf2, f_ltfBullEffortBar(), ignore_invalid_timeframe=true)', 'ltfBullEffortArr2 = array.new_float(0)'),
    ('ltfBearEffortArr3 = request.security_lower_tf(syminfo.tickerid, mtfFallbackTf3, f_ltfBearEffortBar(), ignore_invalid_timeframe=true)', 'ltfBearEffortArr3 = array.new_float(0)'),
    ('ltfBullEffortArr3 = request.security_lower_tf(syminfo.tickerid, mtfFallbackTf3, f_ltfBullEffortBar(), ignore_invalid_timeframe=true)', 'ltfBullEffortArr3 = array.new_float(0)'),
)

EXPECTED_FEEDS = (
    "TVC:SPX",
    "NASDAQ:NDX",
    "OANDA:XAUUSD",
    "OANDA:XAGUSD",
    "BITSTAMP:BTCUSD",
    "BITSTAMP:ETHUSD",
)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"{label} missing or duplicated")
    return text.replace(old, new, 1)


def generate(source: Path) -> str:
    candidate = base.generate(source)
    candidate = replace_once(candidate, OLD_DECL, NEW_DECL, "logger declaration")
    candidate = replace_once(candidate, OLD_ALLOWED, NEW_ALLOWED, "allowed-feed line")
    candidate = replace_once(candidate, OLD_MARKER, NEW_MARKER, "cohort marker")

    frozen_mtf_default = 'mtfMode = input.string("Observe Only"'
    if frozen_mtf_default not in candidate:
        raise RuntimeError("frozen MTF default drifted from Observe Only; lightweight OOS logger would be unsafe")
    for old, new in LIGHTWEIGHT_MTF_REPLACEMENTS:
        candidate = replace_once(candidate, old, new, "MTF observe-only request")

    # Diagnostic heartbeat is deliberately outside issue76Ready. It prints one
    # status line on the last confirmed historical bar so a silent ready-gate
    # failure can be diagnosed without changing any research row semantics.
    heartbeat_anchor = "if issue76LogEnabled and issue76Ready and barstate.isconfirmed"
    heartbeat = r'''if issue76LogEnabled and barstate.islast
    log.warning(
         "HET_OOS1_STATUS" +
         "|ticker=" + syminfo.tickerid +
         "|tf=" + timeframe.period +
         "|allowed=" + str.tostring(issue76AllowedFeed) +
         "|d1=" + str.tostring(issue76D1) +
         "|in_window=" + str.tostring(issue76InWindow) +
         "|formal=" + str.tostring(issue76EventFormal) +
         "|scale=" + str.tostring(issue76EventScale) +
         "|move20=" + str.tostring(issue76Move20) +
         "|rv20=" + str.tostring(issue76Rv20) +
         "|ready=" + str.tostring(issue76Ready))

'''
    candidate = replace_once(
        candidate,
        heartbeat_anchor,
        heartbeat + heartbeat_anchor,
        "OOS diagnostic heartbeat anchor",
    )

    # Reuse the accepted ISSUE76 schema intentionally so the same causal parser
    # and OHLC reconstruction can be used without a second implementation.
    for feed in EXPECTED_FEEDS:
        if f'syminfo.tickerid == "{feed}"' not in candidate:
            raise RuntimeError(f"missing preregistered feed {feed}")

    old_feeds = (
        "OANDA:EURUSD", "OANDA:GBPUSD", "OANDA:USDJPY",
        "TVC:US10Y", "TVC:DE10Y", "TVC:FR10Y",
        "TVC:GB10Y", "TVC:AU10Y", "TVC:JP10Y",
    )
    allowed_line = next(
        line for line in candidate.splitlines()
        if line.startswith("issue76AllowedFeed = ")
    )
    for feed in old_feeds:
        if feed in allowed_line:
            raise RuntimeError(f"discovery feed leaked into OOS whitelist: {feed}")

    required = (
        "issue76D1 = timeframe.isdaily and timeframe.multiplier == 1",
        "issue76EventFormal = formalId[20]",
        "issue76EventScale = symATR[20]",
        "issue76Move20 = f_issue76RawMove(close, issue76EventClose)",
        "ISSUE76|schema=1|cohort=HET_OOS1",
        "calc_bars_count=10000",
        'mtfMode = input.string("Observe Only"',
        "ltfBearEffortArr0 = array.new_float(0)",
    )
    for token in required:
        if token not in candidate:
            raise RuntimeError(f"generated OOS logger missing {token}")

    return candidate


def main() -> None:
    ap = argparse.ArgumentParser()
    default_source = Path(__file__).resolve().parents[1] / "src" / base.SOURCE_NAME
    default_output = (
        Path(__file__).resolve().parent
        / "generated"
        / "wyckoff-issue78-heterogeneous-oos1-forward-logger.pine"
    )
    ap.add_argument("--source", type=Path, default=default_source)
    ap.add_argument("--output", type=Path, default=default_output)
    args = ap.parse_args()

    text = generate(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    print(args.output)
    print("Issue #78 heterogeneous OOS1 logger generator PASS")


if __name__ == "__main__":
    main()
