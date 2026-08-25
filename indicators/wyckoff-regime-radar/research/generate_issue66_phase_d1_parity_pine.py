#!/usr/bin/env python3
"""Generate the Issue #66 Phase D-1 TradingView parity harness.

The harness is mechanically derived from the immutable v0.5.2.1 Pine source.
It applies the accepted Issue #57 v0.6 / Phase-B and Issue #66 B1-B7 / C2
price-only lineage, forces all auxiliary witnesses off, removes the production
visual/alert layer, and exposes Data Window fields for C-2 Pine↔Python parity.

This generator does not claim TradingView runtime parity by itself. Runtime
parity requires a CSV/checkpoint capture produced by TradingView.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from generate_price_only_parity_pine import (
    CHECKPOINT_TABLE,
    FROZEN_SOURCE_BLOB_SHA,
    SOURCE_RELATIVE,
    VISUAL_MARKER,
    git_blob_sha,
    replace_once,
)


ISSUE66_HELPERS = r'''
// === Issue #66 v0.6 continuous boundary primitives ===
f_issue66_softNoBreakLow(_close, _boundary, _atr) =>
    _scale = _atr * 0.25
    f_clamp(50.0 + 50.0 * f_safeDiv(_close - _boundary, _scale), 0.0, 100.0)

f_issue66_softNoBreakHigh(_close, _boundary, _atr) =>
    _scale = _atr * 0.25
    f_clamp(50.0 + 50.0 * f_safeDiv(_boundary - _close, _scale), 0.0, 100.0)

f_issue66_softAboveRange(_close, _boundary, _atr) =>
    100.0 - f_issue66_softNoBreakHigh(_close, _boundary, _atr)

f_issue66_softBelowRange(_close, _boundary, _atr) =>
    100.0 - f_issue66_softNoBreakLow(_close, _boundary, _atr)

f_issue66_softBreakAbove(_close, _boundary, _atr) =>
    _scale = _atr * 0.25
    f_clamp(100.0 * f_safeDiv(_close - _boundary, _scale), 0.0, 100.0)

f_issue66_softBreakBelow(_close, _boundary, _atr) =>
    _scale = _atr * 0.25
    f_clamp(100.0 * f_safeDiv(_boundary - _close, _scale), 0.0, 100.0)
'''.strip()

PARITY_PLOTS = r'''
// === Issue #66 Phase D-1 parity export ===
plot(speedRank, "PARITY speed_rank", display=display.data_window)
plot(accelRank, "PARITY accel_rank", display=display.data_window)
plot(distRank, "PARITY dist_rank", display=display.data_window)
plot(heatUp, "PARITY heat_up", display=display.data_window)
plot(panicHeatDn, "PARITY panic_heat_dn", display=display.data_window)
plot(maturityUp, "PARITY maturity_up", display=display.data_window)
plot(maturityDn, "PARITY maturity_dn", display=display.data_window)
plot(rangeScore, "PARITY range_score", display=display.data_window)
plot(downsideExhaustion, "PARITY downside_exhaustion", display=display.data_window)
plot(upsideExhaustion, "PARITY upside_exhaustion", display=display.data_window)
plot(supportHolding, "PARITY support_holding", display=display.data_window)
plot(resistanceHolding, "PARITY resistance_holding", display=display.data_window)
plot(markupExtensionScore, "PARITY markup_extension_score", display=display.data_window)
plot(markdownExtensionScore, "PARITY markdown_extension_score", display=display.data_window)
plot(markupContinuationScore, "PARITY markup_continuation_score", display=display.data_window)
plot(markdownContinuationScore, "PARITY markdown_continuation_score", display=display.data_window)
plot(accGate * 100.0, "PARITY acc_gate", display=display.data_window)
plot(markupGate * 100.0, "PARITY markup_gate", display=display.data_window)
plot(reaccGate * 100.0, "PARITY reacc_gate", display=display.data_window)
plot(distGate * 100.0, "PARITY dist_gate", display=display.data_window)
plot(markdownGate * 100.0, "PARITY markdown_gate", display=display.data_window)
plot(redistGate * 100.0, "PARITY redist_gate", display=display.data_window)
plot(probAcc, "PARITY prob_acc", display=display.data_window)
plot(probMarkup, "PARITY prob_markup", display=display.data_window)
plot(probReacc, "PARITY prob_reacc", display=display.data_window)
plot(probDist, "PARITY prob_dist", display=display.data_window)
plot(probMarkdown, "PARITY prob_markdown", display=display.data_window)
plot(probRedist, "PARITY prob_redist", display=display.data_window)
plot(float(topId), "PARITY top_id", display=display.data_window)
plot(topVal, "PARITY top_value", display=display.data_window)
plot(topGap, "PARITY top_gap", display=display.data_window)
plot(evidenceStrength, "PARITY evidence_strength", display=display.data_window)
plot(float(candidateDisplayId), "PARITY candidate_display_id", display=display.data_window)
plot(float(formalId), "PARITY formal_id", display=display.data_window)
plot(float(stalePressureBars), "PARITY stale_pressure_bars", display=display.data_window)
plot(float(stalePressureReason), "PARITY stale_pressure_reason", display=display.data_window)
'''.strip()


def apply_issue66_c2(text: str) -> str:
    """Apply source-anchored C-2 lineage replacements to frozen Pine."""

    # Issue #57 v0.6 helper primitives are injected next to the calculation core.
    core_anchor = "// Core Calculation｜即時熱度"
    text = replace_once(text, core_anchor, ISSUE66_HELPERS + "\n\n" + core_anchor)

    # Issue #66 B-1: reciprocal-safe representation.
    text = replace_once(
        text,
        '''ma      = ta.sma(close, maLen)\natr     = ta.atr(atrLen)\ndistATR = f_safeDiv(close - ma, atr)''',
        '''// Issue #66 B-1: geometric MA and log-space ATR representation.\nlogHigh = math.log(high > 0 ? high : na)\nlogLow  = math.log(low > 0 ? low : na)\nmaLog   = ta.sma(logPrice, maLen)\nma      = math.exp(maLog)\natr     = ta.atr(atrLen)  // retained for accepted v0.6 boundary primitives\nlogTR   = na(logPrice[1]) ? logHigh - logLow : math.max(logHigh - logLow, math.max(math.abs(logHigh - logPrice[1]), math.abs(logLow - logPrice[1])))\nsymATR  = ta.rma(logTR, atrLen)\ndistATR = f_safeDiv(logPrice - maLog, symATR)''',
    )
    text = replace_once(
        text,
        '''maturityMa       = ta.sma(close, maturityMaLen)\nmaturityAtr      = ta.atr(maturityAtrLen)\nmaturityDistATR  = f_safeDiv(close - maturityMa, maturityAtr)''',
        '''maturityMaLog    = ta.sma(logPrice, maturityMaLen)\nmaturityMa       = math.exp(maturityMaLog)\nmaturityAtr      = ta.atr(maturityAtrLen)  // retained diagnostic compatibility\nmaturitySymATR   = ta.rma(logTR, maturityAtrLen)\nmaturityDistATR  = f_safeDiv(logPrice - maturityMaLog, maturitySymATR)''',
    )
    text = replace_once(text, "atrPct     = f_safeDiv(atr, close) * 100.0", "atrPct     = symATR * 100.0")
    text = replace_once(
        text,
        '''maCrossUp      = ta.crossover(close, ma)\nmaCrossDn      = ta.crossunder(close, ma)''',
        '''maCrossUp      = ta.crossover(logPrice, maLog)\nmaCrossDn      = ta.crossunder(logPrice, maLog)''',
    )
    text = replace_once(
        text,
        "rangeWidthATR = f_safeDiv(rangeW, atr)",
        "rangeWidthLog = math.log(rangeHigh) - math.log(rangeLow)\nrangeWidthATR = f_safeDiv(rangeWidthLog, symATR)",
    )
    text = replace_once(
        text,
        "maSpreadATR = f_safeDiv(ma - maturityMa, atr)",
        "maSpreadATR = f_safeDiv(maLog - maturityMaLog, symATR)",
    )

    # Issue #57 v0.6: continuous structural-boundary evidence.
    text = replace_once(
        text,
        '''recentBreakUp = f_recent(rangeBreakUp or maCrossUp, breakoutBars)\nrecentBreakDn = f_recent(rangeBreakDn or maCrossDn, breakoutBars)\nrecentRangeBreakDn = f_recent(rangeBreakDn, breakoutBars)\nrecentMaCrossDn = f_recent(maCrossDn, breakoutBars)''',
        '''recentBreakUp = f_recent(rangeBreakUp or maCrossUp, breakoutBars)\nrecentBreakDn = f_recent(rangeBreakDn or maCrossDn, breakoutBars)\nrecentRangeBreakDn = f_recent(rangeBreakDn, breakoutBars)\nrecentMaCrossUp = f_recent(maCrossUp, breakoutBars)\nrecentMaCrossDn = f_recent(maCrossDn, breakoutBars)\nrangeBreakUpStrength = f_issue66_softBreakAbove(close, rangeHighBreak, atr)\nrangeBreakDnStrength = f_issue66_softBreakBelow(close, rangeLowBreak, atr)\nrecentRangeBreakUpStrength = ta.highest(rangeBreakUpStrength, breakoutBars)\nrecentRangeBreakDnStrength = ta.highest(rangeBreakDnStrength, breakoutBars)''',
    )
    text = replace_once(
        text,
        '''noBreakLowScore   = close > prevAbsLow ? 100.0 : 0.0\nnoBreakHighScore  = close < prevAbsHigh ? 100.0 : 0.0''',
        '''noBreakLowScore   = f_issue66_softNoBreakLow(close, prevAbsLow, atr)\nnoBreakHighScore  = f_issue66_softNoBreakHigh(close, prevAbsHigh, atr)''',
    )
    text = replace_once(
        text,
        '''barsSinceAboveRangeLost = ta.barssince(not abovePrevRange)\nbarsSinceBelowRangeLost = ta.barssince(not belowPrevRange)\nsustainedAboveRange = abovePrevRange and (continuationHoldBars <= 1 or (not na(barsSinceAboveRangeLost) and barsSinceAboveRangeLost >= continuationHoldBars - 1))\nsustainedBelowRange = belowPrevRange and (continuationHoldBars <= 1 or (not na(barsSinceBelowRangeLost) and barsSinceBelowRangeLost >= continuationHoldBars - 1))\n\nrangeContinuationUpScore = sustainedAboveRange ? 100.0 : abovePrevRange ? 80.0 : recentBreakUp ? 65.0 : close > rangeMid ? 35.0 : 0.0\nrangeContinuationDnScore = sustainedBelowRange ? 100.0 : belowPrevRange ? 80.0 : recentBreakDn ? 65.0 : close < rangeMid ? 35.0 : 0.0''',
        '''abovePrevRangeScore = f_issue66_softAboveRange(close, prevRangeHigh, atr)\nbelowPrevRangeScore = f_issue66_softBelowRange(close, prevRangeLow, atr)\nsustainedAboveRangeScore = ta.lowest(abovePrevRangeScore, continuationHoldBars)\nsustainedBelowRangeScore = ta.lowest(belowPrevRangeScore, continuationHoldBars)\nrangeBreakUpEvidence = nz(recentRangeBreakUpStrength, 0.0) * 0.65\nrangeBreakDnEvidence = nz(recentRangeBreakDnStrength, 0.0) * 0.65\nrangeContinuationUpBase = math.max(rangeBreakUpEvidence, recentMaCrossUp ? 65.0 : close > rangeMid ? 35.0 : 0.0)\nrangeContinuationDnBase = math.max(rangeBreakDnEvidence, recentMaCrossDn ? 65.0 : close < rangeMid ? 35.0 : 0.0)\nrangeContinuationUpScore = math.max(rangeContinuationUpBase, math.max(nz(abovePrevRangeScore, 0.0) * 0.80, nz(sustainedAboveRangeScore, 0.0)))\nrangeContinuationDnScore = math.max(rangeContinuationDnBase, math.max(nz(belowPrevRangeScore, 0.0) * 0.80, nz(sustainedBelowRangeScore, 0.0)))''',
    )

    # Issue #66 B-2: shared direction-neutral break evidence and score/100 gate.
    text = replace_once(
        text,
        '''breakoutScore = breakoutModeUp ? 100.0 : recentBreakUp ? 70.0 : close > ma ? 35.0 : 0.0\nexplicitBreakdownScore = breakdownModeDn ? 100.0 : recentRangeBreakDn ? 85.0 : (recentMaCrossDn and panicHeatDn >= orangeLevel and structureWeak >= 50.0 ? 55.0 : 0.0)''',
        '''breakoutRangeEvidence = f_clamp(nz(recentRangeBreakUpStrength, 0.0), 0.0, 100.0)\nbreakoutMaEvidence = recentMaCrossUp ? 70.0 : logPrice > maLog ? 35.0 : 0.0\nbreakoutScore = breakoutModeUp ? 100.0 : math.max(breakoutRangeEvidence, breakoutMaEvidence)\nbreakdownRangeEvidence = f_clamp(nz(recentRangeBreakDnStrength, 0.0), 0.0, 100.0)\nbreakdownMaEvidence = recentMaCrossDn ? 70.0 : logPrice < maLog ? 35.0 : 0.0\nexplicitBreakdownScore = breakdownModeDn ? 100.0 : math.max(breakdownRangeEvidence, breakdownMaEvidence)''',
    )
    text = replace_once(
        text,
        '''breakoutGate = breakoutModeUp ? 1.0 : recentBreakUp ? 0.85 : f_gate(breakoutScore, 30.0, 70.0)\nexplicitBreakdownGate = breakdownModeDn ? 1.0 : recentRangeBreakDn ? 0.90 : f_gate(explicitBreakdownScore, 50.0, 85.0)''',
        '''breakoutRecentRangeGate = f_clamp(breakoutRangeEvidence / 100.0, 0.0, 1.0)\nbreakoutMaGate = f_clamp(breakoutMaEvidence / 100.0, 0.0, 1.0)\nbreakoutRecentGate = math.max(breakoutRecentRangeGate, breakoutMaGate)\nbreakoutGate = f_clamp(breakoutScore / 100.0, 0.0, 1.0)\nexplicitRecentBreakdownGate = f_clamp(breakdownRangeEvidence / 100.0, 0.0, 1.0)\nexplicitBreakdownMaGate = f_clamp(breakdownMaEvidence / 100.0, 0.0, 1.0)\nexplicitBreakdownGate = f_clamp(explicitBreakdownScore / 100.0, 0.0, 1.0)''',
    )

    # Issue #66 B-3: mirrored fresh trend-entry gate.
    text = replace_once(
        text,
        "nonEndUpGate = f_gate(nonEndRiskUp, 35.0, 80.0)",
        "nonEndUpGate = f_gate(nonEndRiskUp, 35.0, 80.0)\nnonEndDnGate = f_gate(100.0 - endRiskDnRaw, 35.0, 80.0)",
    )
    text = replace_once(
        text,
        '''breakdownMarkdownGate =\n     explicitBreakdownGate *\n     f_gate(panicHeatDn, 40.0, 80.0) *\n     structureWeakGate''',
        '''breakdownMarkdownGate =\n     explicitBreakdownGate *\n     structureWeakGate *\n     nonEndDnGate''',
    )

    # Issue #66 B-5/B-6: Stage 3/6 and Stage 1/4 raw symmetry.
    text = replace_once(
        text,
        "redistRaw0 = f_weighted5(bearBg, 0.20, rangeScore, 0.20, resistanceHolding, 0.25, reboundFailure, 0.20, 100.0 - downsideExhaustion, 0.15)",
        "redistRaw0 = f_weighted5(bearBg, 0.20, rangeScore, 0.20, resistanceHolding, 0.25, 100.0 - heatUp, 0.20, 100.0 - downsideExhaustion, 0.15)",
    )
    text = replace_once(
        text,
        "distRaw0 = f_weighted5(bullMaturityTrace, 0.20, rangeScore, 0.20, upsideExhaustion, 0.25, resistanceHolding, 0.25, bearPressureRising, 0.10)",
        "distRaw0 = f_weighted5(bullMaturityTrace, 0.20, rangeScore, 0.20, upsideExhaustion, 0.25, resistanceHolding, 0.25, lowVolScore, 0.10)",
    )

    # Issue #66 B-7: mirrored Stage 1/4 background/maturity gate.
    text = replace_once(
        text,
        '''matureBullGate = f_gate(bullMaturityTrace, 60.0, 85.0)\nbearBackgroundForAccGate = f_gate(math.max(bearBg, bearMaturityTrace), 35.0, 75.0)''',
        '''matureBullGate = f_gate(bullMaturityTrace, 60.0, 85.0)  // retained diagnostic compatibility\nbearBackgroundForAccGate = f_gate(math.max(bearBg, bearMaturityTrace), 35.0, 75.0)\nbullBackgroundForDistGate = f_gate(math.max(bullBg, bullMaturityTrace), 35.0, 75.0)''',
    )
    text = replace_once(
        text,
        "distGate     = rangeGate * matureBullGate * upsideExhaustionGate * resistanceHoldingGate * nonMarkupContinuationGate",
        "distGate     = rangeGate * bullBackgroundForDistGate * upsideExhaustionGate * resistanceHoldingGate * nonMarkupContinuationGate",
    )

    # Issue #66 C-2: price-only reciprocal Stage-1/4 candidate-conflict rule.
    old_conflict = '''candidateConflict = (topId == 6 and ((downsideExhaustion >= absorbThreshold and supportHolding >= absorbThreshold) or volumeDemandClue or mtfDemandClue or strictBottomDivergence or softBottomDivergence) and not markdownContinuationOverride) or\n     (topId == 1 and ((resistanceHolding >= absorbThreshold and reboundFailureGate > 0.50) or volumeSupplyClue or mtfSupplyClue or strictTopDivergence or softTopDivergence) and not markupContinuationOverride) or\n     (topId == 4 and ((supportHolding >= absorbThreshold and downsideExhaustion >= absorbThreshold) or volumeDemandClue or mtfDemandClue or strictBottomDivergence or softBottomDivergence) and not markupContinuationOverride) or\n     (topId == 3 and ((upsideExhaustion >= absorbThreshold and resistanceHolding >= absorbThreshold) or volumeSupplyClue or mtfSupplyClue or strictTopDivergence or softTopDivergence) and not markupContinuationOverride) or\n     (topId == 2 and ((upsideExhaustion >= absorbThreshold and resistanceHolding >= absorbThreshold) or volumeSupplyClue or mtfSupplyClue or strictTopDivergence or softTopDivergence) and not markupContinuationOverride) or\n     (topId == 5 and ((downsideExhaustion >= absorbThreshold and supportHolding >= absorbThreshold) or volumeDemandClue or mtfDemandClue or strictBottomDivergence or softBottomDivergence) and not markdownContinuationOverride)'''
    new_conflict = '''candidateConflict = (topId == 6 and downsideExhaustion >= absorbThreshold and supportHolding >= absorbThreshold and not markdownContinuationOverride) or\n     (topId == 1 and resistanceHolding >= absorbThreshold and upsideExhaustion >= absorbThreshold and not markdownContinuationOverride) or\n     (topId == 4 and supportHolding >= absorbThreshold and downsideExhaustion >= absorbThreshold and not markupContinuationOverride) or\n     (topId == 3 and upsideExhaustion >= absorbThreshold and resistanceHolding >= absorbThreshold and not markupContinuationOverride) or\n     (topId == 2 and upsideExhaustion >= absorbThreshold and resistanceHolding >= absorbThreshold and not markupContinuationOverride) or\n     (topId == 5 and downsideExhaustion >= absorbThreshold and supportHolding >= absorbThreshold and not markdownContinuationOverride)'''
    text = replace_once(text, old_conflict, new_conflict)

    # Issue #57 Phase-B: stale-pressure persistence. The strong-candidate
    # confirmation path is unchanged; unsupported old Formal states decay at 2x.
    old_inertia = '''// Regime Inertia\n\nvar int confirmedId = 0\nvar int candidateId = 0\nvar int candidateBars = 0\nvar int noRegimeBars = 0\n\nif strongCandidate\n    noRegimeBars := 0\n    if candidateRawId == candidateId\n        candidateBars += 1\n    else\n        candidateId := candidateRawId\n        candidateBars := 1\n\n    if candidateBars >= activeConfirmBars\n        confirmedId := candidateId\nelse\n    candidateId := 0\n    candidateBars := 0\n    if chaosRaw\n        noRegimeBars += 1\n        if noRegimeBars >= confirmBars\n            confirmedId := 0\n    else\n        noRegimeBars := 0\n\nformalId = confirmedId\ncandidateDisplayId = (strongCandidate or weakCandidateRaw) ? topId : 0'''
    new_inertia = '''// Regime Inertia — Issue #57 Phase-B stale-pressure persistence\n\ncandidateDisplayRawId = (strongCandidate or weakCandidateRaw) ? topId : 0\nvar int confirmedId = 0\nvar int candidateId = 0\nvar int candidateBars = 0\nvar int stalePressureBars = 0\nint stalePressureReason = 0\nstaleLimit = confirmBars * 2\n\nif strongCandidate\n    stalePressureBars := 0\n    stalePressureReason := 0\n    if candidateRawId == candidateId\n        candidateBars += 1\n    else\n        candidateId := candidateRawId\n        candidateBars := 1\n\n    if candidateBars >= activeConfirmBars\n        confirmedId := candidateId\nelse\n    candidateId := 0\n    candidateBars := 0\n    weakChallenger = confirmedId != 0 and candidateDisplayRawId != 0 and candidateDisplayRawId != confirmedId\n    coexistPressure = confirmedId != 0 and coexistRaw and candidateDisplayRawId == 0\n    stalePressureReason := chaosRaw and confirmedId != 0 ? 1 : weakChallenger ? 2 : coexistPressure ? 3 : 0\n    if stalePressureReason != 0\n        stalePressureBars += 1\n        if stalePressureBars >= staleLimit\n            confirmedId := 0\n    else\n        stalePressureBars := 0\n\nformalId = confirmedId\ncandidateDisplayId = candidateDisplayRawId'''
    text = replace_once(text, old_inertia, new_inertia)

    return text


def generate(source_path: Path) -> str:
    raw = source_path.read_bytes()
    actual_blob = git_blob_sha(raw)
    if actual_blob != FROZEN_SOURCE_BLOB_SHA:
        raise RuntimeError(
            "frozen Pine source changed; refusing Issue #66 parity generation: "
            f"expected {FROZEN_SOURCE_BLOB_SHA}, got {actual_blob}"
        )

    text = raw.decode("utf-8")
    text = replace_once(
        text,
        'indicator("Chase Risk Market Regime Radar v0.5.2.1｜Non-functional Cleanup", shorttitle="ChaseRisk Radar v0.5.2.1", overlay=false, precision=1)',
        'indicator("Chase Risk Radar｜Issue #66 C-2 Parity", shorttitle="ChaseRisk #66 C2 Parity", overlay=false, precision=1)',
    )
    text = replace_once(
        text,
        'volumeMode = input.string("Auto", "Volume Mode", options=["Off", "Auto", "Force On", "Tick Volume Proxy"], group=groupVolume)',
        'volumeMode = "Off"  // Issue #66 forced price-only',
    )
    text = replace_once(
        text,
        'mtfMode = input.string("Observe Only", "MTF Mode", options=["Off", "Observe Only", "Auto", "Force On"], group=groupMTF)',
        'mtfMode = "Off"  // Issue #66 forced price-only',
    )
    text = replace_once(
        text,
        'divMode = input.string("Observe Only", "Divergence Mode", options=["Off", "Observe Only", "Auto"], group=groupDivergence)',
        'divMode = "Off"  // Issue #66 forced price-only',
    )
    text = replace_once(
        text,
        'witnessStageBiasMode = input.string("Balanced", "Witness Stage Bias Mode", options=["Conservative", "Balanced", "Aggressive"], group=groupWitness)',
        'witnessStageBiasMode = "Conservative"  // Issue #66 forced price-only',
    )

    text = apply_issue66_c2(text)
    if text.count(VISUAL_MARKER) != 1:
        raise RuntimeError("expected exactly one // Visuals marker")
    calculation_core, _ = text.split(VISUAL_MARKER, 1)
    return calculation_core.rstrip() + "\n\n" + PARITY_PLOTS + "\n\n" + CHECKPOINT_TABLE + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate Issue #66 C-2 Pine parity harness")
    default_source = Path(__file__).resolve().parent / SOURCE_RELATIVE
    ap.add_argument("--source", type=Path, default=default_source)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    generated = generate(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(generated, encoding="utf-8")


if __name__ == "__main__":
    main()
