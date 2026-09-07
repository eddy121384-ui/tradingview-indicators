#!/usr/bin/env python3
"""Generate Issue #68 HARD candidate with a yield-safe representation domain split.

The upstream full HARD candidate is generated mechanically first. This module
then changes only the Issue #66 B-1 representation family so bond-yield level
series can cross zero without invalidating log(price). Positive price assets
remain on the exact Issue #66 log-space path under Auto.
"""
from __future__ import annotations

import argparse
import difflib
from pathlib import Path

import generate_issue68_hard_current_context_production_candidate_pine as hard
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once


GROUP_OLD = 'groupHeat      = "參數｜即時熱度"'
GROUP_NEW = 'groupRepresentation = "參數｜資料表示"\n' + GROUP_OLD

HEAT_HEADER_OLD = '// === 即時熱度 ===\nspeedLen = input.int(20, "速度斜率天期", minval=2, group=groupHeat)'
HEAT_HEADER_NEW = '''// === 資料表示 ===
representationMode = input.string("Auto", "資料表示模式", options=["Auto", "Price Log", "Yield Level"], group=groupRepresentation)
// Auto：TradingView bond + currency NONE 視為殖利率 level series；其他資產保留 Issue #66 Price Log。

// === 即時熱度 ===
speedLen = input.int(20, "速度斜率天期", minval=2, group=groupHeat)'''

CORE_OLD = '''safeClose = close > 0 ? close : na
logPrice  = math.log(safeClose)
logRet    = math.log(safeClose / safeClose[1])
vol       = ta.stdev(logRet, volLen)

speedZ = f_slopeZ(logPrice, speedLen, vol)
shortZ = f_slopeZ(logPrice, shortLen, vol)
longZ  = f_slopeZ(logPrice, longLen, vol)
accelZ = shortZ - longZ

// Issue #66 B-1: geometric MA and log-space ATR representation.
logHigh = math.log(high > 0 ? high : na)
logLow  = math.log(low > 0 ? low : na)
maLog   = ta.sma(logPrice, maLen)
ma      = math.exp(maLog)
atr     = ta.atr(atrLen)  // retained for accepted v0.6 boundary primitives
logTR   = na(logPrice[1]) ? logHigh - logLow : math.max(logHigh - logLow, math.max(math.abs(logHigh - logPrice[1]), math.abs(logLow - logPrice[1])))
symATR  = ta.rma(logTR, atrLen)
distATR = f_safeDiv(logPrice - maLog, symATR)'''

CORE_NEW = '''// Issue #68 yield-safe representation domain split.
// Price Log preserves Issue #66 reciprocal-safe behavior for positive price assets.
// Yield Level supports zero/negative bond-yield datasets without log-domain NA.
autoYieldLevel = syminfo.type == "bond" and syminfo.currency == "NONE"
useYieldLevel = representationMode == "Yield Level" or (representationMode == "Auto" and autoYieldLevel)

safeClose = close > 0 ? close : na
logPrice  = math.log(safeClose)
logRet    = math.log(safeClose / safeClose[1])
levelRet  = close - close[1]
modelPrice = useYieldLevel ? close : logPrice
modelRet   = useYieldLevel ? levelRet : logRet
vol        = ta.stdev(modelRet, volLen)

speedZ = f_slopeZ(modelPrice, speedLen, vol)
shortZ = f_slopeZ(modelPrice, shortLen, vol)
longZ  = f_slopeZ(modelPrice, longLen, vol)
accelZ = shortZ - longZ

// Issue #66 Price Log path + Issue #68 Yield Level path.
logHigh = math.log(high > 0 ? high : na)
logLow  = math.log(low > 0 ? low : na)
maLog   = ta.sma(logPrice, maLen)
maLevel = ta.sma(close, maLen)
maModel = useYieldLevel ? maLevel : maLog
ma      = useYieldLevel ? maLevel : math.exp(maLog)
atr     = ta.atr(atrLen)  // retained for accepted v0.6 boundary primitives
logTR   = na(logPrice[1]) ? logHigh - logLow : math.max(logHigh - logLow, math.max(math.abs(logHigh - logPrice[1]), math.abs(logLow - logPrice[1])))
levelTR = na(close[1]) ? high - low : math.max(high - low, math.max(math.abs(high - close[1]), math.abs(low - close[1])))
modelTR = useYieldLevel ? levelTR : logTR
symATR  = ta.rma(modelTR, atrLen)
distATR = f_safeDiv(modelPrice - maModel, symATR)'''

MATURITY_OLD = '''maturitySlopeZ = f_slopeZ(logPrice, maturitySlopeLen, vol)
longSlopeRank  = ta.percentrank(maturitySlopeZ, rankLen)

maturityMaLog    = ta.sma(logPrice, maturityMaLen)
maturityMa       = math.exp(maturityMaLog)
maturityAtr      = ta.atr(maturityAtrLen)  // retained diagnostic compatibility
maturitySymATR   = ta.rma(logTR, maturityAtrLen)
maturityDistATR  = f_safeDiv(logPrice - maturityMaLog, maturitySymATR)'''

MATURITY_NEW = '''maturitySlopeZ = f_slopeZ(modelPrice, maturitySlopeLen, vol)
longSlopeRank  = ta.percentrank(maturitySlopeZ, rankLen)

maturityMaLog    = ta.sma(logPrice, maturityMaLen)
maturityMaLevel  = ta.sma(close, maturityMaLen)
maturityMaModel  = useYieldLevel ? maturityMaLevel : maturityMaLog
maturityMa       = useYieldLevel ? maturityMaLevel : math.exp(maturityMaLog)
maturityAtr      = ta.atr(maturityAtrLen)  // retained diagnostic compatibility
maturitySymATR   = ta.rma(modelTR, maturityAtrLen)
maturityDistATR  = f_safeDiv(modelPrice - maturityMaModel, maturitySymATR)'''

ATR_PCT_OLD = 'atrPct     = symATR * 100.0'
ATR_PCT_NEW = 'atrPct     = useYieldLevel ? symATR : symATR * 100.0'

MA_CROSS_OLD = '''maCrossUp      = ta.crossover(logPrice, maLog)
maCrossDn      = ta.crossunder(logPrice, maLog)'''
MA_CROSS_NEW = '''maCrossUp      = ta.crossover(modelPrice, maModel)
maCrossDn      = ta.crossunder(modelPrice, maModel)'''

RANGE_WIDTH_OLD = '''rangeW    = rangeHigh - rangeLow
rangeWidthLog = math.log(rangeHigh) - math.log(rangeLow)
rangeWidthATR = f_safeDiv(rangeWidthLog, symATR)'''
RANGE_WIDTH_NEW = '''rangeW    = rangeHigh - rangeLow
rangeWidthLog = math.log(rangeHigh) - math.log(rangeLow)
rangeWidthModel = useYieldLevel ? rangeW : rangeWidthLog
rangeWidthATR = f_safeDiv(rangeWidthModel, symATR)'''

BREAK_MA_OLD = '''breakoutMaEvidence = recentMaCrossUp ? 70.0 : logPrice > maLog ? 35.0 : 0.0
breakoutScore = breakoutModeUp ? 100.0 : math.max(breakoutRangeEvidence, breakoutMaEvidence)
breakdownRangeEvidence = f_clamp(nz(recentRangeBreakDnStrength, 0.0), 0.0, 100.0)
breakdownMaEvidence = recentMaCrossDn ? 70.0 : logPrice < maLog ? 35.0 : 0.0'''
BREAK_MA_NEW = '''breakoutMaEvidence = recentMaCrossUp ? 70.0 : modelPrice > maModel ? 35.0 : 0.0
breakoutScore = breakoutModeUp ? 100.0 : math.max(breakoutRangeEvidence, breakoutMaEvidence)
breakdownRangeEvidence = f_clamp(nz(recentRangeBreakDnStrength, 0.0), 0.0, 100.0)
breakdownMaEvidence = recentMaCrossDn ? 70.0 : modelPrice < maModel ? 35.0 : 0.0'''

MA_SPREAD_OLD = 'maSpreadATR = f_safeDiv(maLog - maturityMaLog, symATR)'
MA_SPREAD_NEW = 'maSpreadATR = f_safeDiv(maModel - maturityMaModel, symATR)'


def apply_yield_safe_representation(hard_candidate: str) -> str:
    text = replace_once(hard_candidate, GROUP_OLD, GROUP_NEW)
    text = replace_once(text, HEAT_HEADER_OLD, HEAT_HEADER_NEW)
    text = replace_once(text, CORE_OLD, CORE_NEW)
    text = replace_once(text, MATURITY_OLD, MATURITY_NEW)
    text = replace_once(text, ATR_PCT_OLD, ATR_PCT_NEW)
    text = replace_once(text, MA_CROSS_OLD, MA_CROSS_NEW)
    text = replace_once(text, RANGE_WIDTH_OLD, RANGE_WIDTH_NEW)
    text = replace_once(text, BREAK_MA_OLD, BREAK_MA_NEW)
    text = replace_once(text, MA_SPREAD_OLD, MA_SPREAD_NEW)
    return text


def validate(hard_candidate: str, candidate: str) -> None:
    required = (
        'representationMode = input.string("Auto", "資料表示模式", options=["Auto", "Price Log", "Yield Level"]',
        'autoYieldLevel = syminfo.type == "bond" and syminfo.currency == "NONE"',
        'useYieldLevel = representationMode == "Yield Level" or (representationMode == "Auto" and autoYieldLevel)',
        'modelPrice = useYieldLevel ? close : logPrice',
        'modelRet   = useYieldLevel ? levelRet : logRet',
        'maModel = useYieldLevel ? maLevel : maLog',
        'modelTR = useYieldLevel ? levelTR : logTR',
        'maturityMaModel  = useYieldLevel ? maturityMaLevel : maturityMaLog',
        'rangeWidthModel = useYieldLevel ? rangeW : rangeWidthLog',
        'currentBearGate = f_gate(bearBg, 35.0, 75.0)',
        'currentBullGate = f_gate(bullBg, 35.0, 75.0)',
        'ctxDownExGate = math.min(downsideExhaustionGate, currentBearGate)',
        'ctxUpExGate = math.min(upsideExhaustionGate, currentBullGate)',
        'accGate      = rangeGate * bearBackgroundForAccGate * ctxDownExGate * supportHoldingGate * nonMarkdownContinuationGate',
        'distGate     = rangeGate * bullBackgroundForDistGate * ctxUpExGate * resistanceHoldingGate * nonMarkupContinuationGate',
        'volumeMode = input.string("Auto", "Volume Mode"',
        'mtfMode = input.string("Observe Only", "MTF Mode"',
        'divMode = input.string("Observe Only", "Divergence Mode"',
        'request.security_lower_tf',
        '// Visuals',
        'alertcondition(formalChanged',
    )
    for token in required:
        if token not in candidate:
            raise RuntimeError(f"yield-safe candidate missing required token: {token}")

    # Auto routing must be static metadata only. Historical-price inference is forbidden.
    auto_line = 'autoYieldLevel = syminfo.type == "bond" and syminfo.currency == "NONE"'
    if candidate.count(auto_line) != 1:
        raise RuntimeError("Auto yield routing must appear exactly once")
    for forbidden in ('ta.lowest(close', 'ta.highest(close', 'close <= 0', 'close < 0', 'bar_index'):
        # bar_index exists elsewhere in production; restrict check to the added Auto definition region.
        if forbidden in auto_line:
            raise RuntimeError(f"path-dependent Auto routing forbidden: {forbidden}")

    # Representation repair must not touch the already-approved HARD routing.
    hard_tokens = (
        hard.CURRENT_BEAR,
        hard.CURRENT_BULL,
        hard.CTX_DOWN,
        hard.CTX_UP,
        hard.NEW_ACC_GATE,
        hard.NEW_DIST_GATE,
    )
    for token in hard_tokens:
        if hard_candidate.count(token) != candidate.count(token) or candidate.count(token) != 1:
            raise RuntimeError(f"HARD invariant changed by yield repair: {token}")

    # Plot-generating footprint must remain unchanged.
    if len(hard.PLOT_CALL_RE.findall(hard_candidate)) != len(hard.PLOT_CALL_RE.findall(candidate)):
        raise RuntimeError("plot-generating call footprint changed")

    # No research harness / strategy leakage.
    for forbidden in (
        'Issue #66 forced price-only',
        'PARITY prob_acc',
        'STATEFUL CTX',
        'strategy.entry',
        'strategy.close',
        'strategy(',
    ):
        if forbidden in candidate:
            raise RuntimeError(f"forbidden token in yield-safe candidate: {forbidden}")

    # Ensure direct downstream use of logPrice/maLog was removed from the B-1 consumers.
    forbidden_direct = (
        'f_slopeZ(logPrice, speedLen',
        'f_slopeZ(logPrice, maturitySlopeLen',
        'ta.crossover(logPrice, maLog)',
        'ta.crossunder(logPrice, maLog)',
        'logPrice > maLog ? 35.0',
        'logPrice < maLog ? 35.0',
        'f_safeDiv(maLog - maturityMaLog, symATR)',
        'f_safeDiv(rangeWidthLog, symATR)',
    )
    for token in forbidden_direct:
        if token in candidate:
            raise RuntimeError(f"unrouted log-only B-1 consumer remains: {token}")


def unified_diff_text(baseline: str, candidate: str) -> str:
    return "\n".join(
        difflib.unified_diff(
            baseline.splitlines(),
            candidate.splitlines(),
            fromfile="issue68-hard-production-candidate.pine",
            tofile="issue68-yield-safe-hard-production-candidate.pine",
            lineterm="",
        )
    ) + "\n"


def generate(source_path: Path) -> tuple[str, str]:
    hard_candidate, _ = hard.generate(source_path)
    candidate = apply_yield_safe_representation(hard_candidate)
    validate(hard_candidate, candidate)
    return candidate, unified_diff_text(hard_candidate, candidate)


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate Issue #68 yield-safe HARD production candidate")
    ap.add_argument("--source", type=Path, default=Path(__file__).resolve().parent / SOURCE_RELATIVE)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--diff-output", type=Path)
    args = ap.parse_args()

    candidate, diff_text = generate(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(candidate, encoding="utf-8")
    if args.diff_output is not None:
        args.diff_output.parent.mkdir(parents=True, exist_ok=True)
        args.diff_output.write_text(diff_text, encoding="utf-8")

    print(args.output)
    if args.diff_output is not None:
        print(args.diff_output)
    print("Issue #68 yield-safe HARD production-candidate static contract PASS")


if __name__ == "__main__":
    main()
