#!/usr/bin/env python3
"""Generate Issue #68 final yield-safe C-2 vs HARD six-market regression audit.

A = yield-safe C-2 baseline without Issue #68 HARD caps.
B = exact yield-safe HARD production candidate.

The output keeps the full production candidate and adds a shadow A classifier /
lifecycle plus deterministic diagnostics. No strategy/PnL/tuning is introduced.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_hard_current_context_production_candidate_pine as hard
import generate_issue68_yield_safe_hard_production_candidate_pine as yield_safe
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

DECL_OLD = 'indicator("Chase Risk Market Regime Radar v0.5.2.1｜Non-functional Cleanup", shorttitle="ChaseRisk Radar v0.5.2.1", overlay=false, precision=1)'
DECL_NEW = 'indicator("Chase Risk Radar｜Issue #68 Yield-Safe HARD Regression", shorttitle="#68 HARD REG", overlay=false, precision=1)'

ANCHOR = '''formalId = confirmedId
candidateDisplayId = candidateDisplayRawId
secondaryId = hasSharp ? secondId : 0'''

AUDIT_BODY = r'''formalId = confirmedId
candidateDisplayId = candidateDisplayRawId
secondaryId = hasSharp ? secondId : 0

// ============================================================================
// Issue #68 Final Yield-Safe HARD Regression Audit
// A = yield-safe C-2 baseline, B = native yield-safe HARD candidate above.
// NO PNL. NO TUNING. NO LOOKAHEAD.
// ============================================================================
groupIssue68Regression = "Issue #68｜Final HARD Regression"
showIssue68RegressionTable = input.bool(true, "顯示 A/B Regression 表", group=groupIssue68Regression)
showIssue68RegressionLines = input.bool(true, "顯示 A/B TOP / Formal 線", group=groupIssue68Regression)

// Shadow A: exact C-2 S1/S4 direct eligibility without HARD current-context caps.
issue68BaseAccGate = rangeGate * bearBackgroundForAccGate * downsideExhaustionGate * supportHoldingGate * nonMarkdownContinuationGate
issue68BaseDistGate = rangeGate * bullBackgroundForDistGate * upsideExhaustionGate * resistanceHoldingGate * nonMarkupContinuationGate
issue68BaseAccEffBase = accRaw * issue68BaseAccGate
issue68BaseDistEffBase = distRaw * issue68BaseDistGate
issue68BaseAccEff = issue68BaseAccEffBase * accVolMult * accMtfMult * accDivMult
issue68BaseMarkupEff = markupEff
issue68BaseReaccEff = reaccEff
issue68BaseDistEff = issue68BaseDistEffBase * distVolMult * distMtfMult * distDivMult
issue68BaseMarkdownEff = markdownEff
issue68BaseRedistEff = redistEff

issue68BaseEffTotal = issue68BaseAccEff + issue68BaseMarkupEff + issue68BaseReaccEff + issue68BaseDistEff + issue68BaseMarkdownEff + issue68BaseRedistEff
issue68BaseHasEnoughEff = not na(issue68BaseEffTotal) and issue68BaseEffTotal > minEffTotal
issue68BaseAccSharp = math.pow(math.max(nz(issue68BaseAccEff), 0.0), regimeGamma)
issue68BaseMarkupSharp = math.pow(math.max(nz(issue68BaseMarkupEff), 0.0), regimeGamma)
issue68BaseReaccSharp = math.pow(math.max(nz(issue68BaseReaccEff), 0.0), regimeGamma)
issue68BaseDistSharp = math.pow(math.max(nz(issue68BaseDistEff), 0.0), regimeGamma)
issue68BaseMarkdownSharp = math.pow(math.max(nz(issue68BaseMarkdownEff), 0.0), regimeGamma)
issue68BaseRedistSharp = math.pow(math.max(nz(issue68BaseRedistEff), 0.0), regimeGamma)
issue68BaseSharpTotal = issue68BaseAccSharp + issue68BaseMarkupSharp + issue68BaseReaccSharp + issue68BaseDistSharp + issue68BaseMarkdownSharp + issue68BaseRedistSharp
issue68BaseHasSharp = issue68BaseHasEnoughEff and issue68BaseSharpTotal > 0.0
issue68BaseP1 = issue68BaseHasSharp ? issue68BaseAccSharp / issue68BaseSharpTotal * 100.0 : 0.0
issue68BaseP2 = issue68BaseHasSharp ? issue68BaseMarkupSharp / issue68BaseSharpTotal * 100.0 : 0.0
issue68BaseP3 = issue68BaseHasSharp ? issue68BaseReaccSharp / issue68BaseSharpTotal * 100.0 : 0.0
issue68BaseP4 = issue68BaseHasSharp ? issue68BaseDistSharp / issue68BaseSharpTotal * 100.0 : 0.0
issue68BaseP5 = issue68BaseHasSharp ? issue68BaseMarkdownSharp / issue68BaseSharpTotal * 100.0 : 0.0
issue68BaseP6 = issue68BaseHasSharp ? issue68BaseRedistSharp / issue68BaseSharpTotal * 100.0 : 0.0

float issue68BaseTopVal = issue68BaseP1
int issue68BaseTopId = 1
float issue68BaseSecondVal = -1.0
int issue68BaseSecondId = 0
if issue68BaseP2 > issue68BaseTopVal
    issue68BaseSecondVal := issue68BaseTopVal
    issue68BaseSecondId := issue68BaseTopId
    issue68BaseTopVal := issue68BaseP2
    issue68BaseTopId := 2
else if issue68BaseP2 > issue68BaseSecondVal
    issue68BaseSecondVal := issue68BaseP2
    issue68BaseSecondId := 2
if issue68BaseP3 > issue68BaseTopVal
    issue68BaseSecondVal := issue68BaseTopVal
    issue68BaseSecondId := issue68BaseTopId
    issue68BaseTopVal := issue68BaseP3
    issue68BaseTopId := 3
else if issue68BaseP3 > issue68BaseSecondVal
    issue68BaseSecondVal := issue68BaseP3
    issue68BaseSecondId := 3
if issue68BaseP4 > issue68BaseTopVal
    issue68BaseSecondVal := issue68BaseTopVal
    issue68BaseSecondId := issue68BaseTopId
    issue68BaseTopVal := issue68BaseP4
    issue68BaseTopId := 4
else if issue68BaseP4 > issue68BaseSecondVal
    issue68BaseSecondVal := issue68BaseP4
    issue68BaseSecondId := 4
if issue68BaseP5 > issue68BaseTopVal
    issue68BaseSecondVal := issue68BaseTopVal
    issue68BaseSecondId := issue68BaseTopId
    issue68BaseTopVal := issue68BaseP5
    issue68BaseTopId := 5
else if issue68BaseP5 > issue68BaseSecondVal
    issue68BaseSecondVal := issue68BaseP5
    issue68BaseSecondId := 5
if issue68BaseP6 > issue68BaseTopVal
    issue68BaseSecondVal := issue68BaseTopVal
    issue68BaseSecondId := issue68BaseTopId
    issue68BaseTopVal := issue68BaseP6
    issue68BaseTopId := 6
else if issue68BaseP6 > issue68BaseSecondVal
    issue68BaseSecondVal := issue68BaseP6
    issue68BaseSecondId := 6

issue68BaseTopGap = issue68BaseTopVal - issue68BaseSecondVal
issue68BaseMaxEff = math.max(math.max(math.max(issue68BaseAccEff, issue68BaseMarkupEff), math.max(issue68BaseReaccEff, issue68BaseDistEff)), math.max(issue68BaseMarkdownEff, issue68BaseRedistEff))
issue68BaseEffTotalStrength = f_gate(issue68BaseEffTotal, minEffTotal, evidenceEffFull) * 100.0
issue68BaseTopEffStrength = f_gate(issue68BaseMaxEff, 0.0, evidenceTopFull) * 100.0
issue68BaseTopGapStrength = f_gate(issue68BaseTopGap, topGapMin, 35.0) * 100.0
issue68BaseStageSupportStrength = issue68BaseTopId == 1 ? f_weighted2(downsideExhaustion, 0.50, supportHolding, 0.50) :
     issue68BaseTopId == 2 ? f_weighted3(markupExtensionScore, 0.45, markupContinuationScore, 0.35, math.max(breakoutScore, structureStrong), 0.20) :
     issue68BaseTopId == 3 ? f_weighted2(supportHolding, 0.50, 100.0 - upsideExhaustion, 0.50) :
     issue68BaseTopId == 4 ? f_weighted2(upsideExhaustion, 0.50, resistanceHolding, 0.50) :
     issue68BaseTopId == 5 ? f_weighted3(markdownExtensionScore, 0.45, markdownContinuationScore, 0.35, math.max(explicitBreakdownGate * 100.0, panicHeatDn), 0.20) :
     issue68BaseTopId == 6 ? f_weighted2(resistanceHolding, 0.50, 100.0 - downsideExhaustion, 0.50) : 0.0
issue68BaseVolumeSupportStrength = issue68BaseTopId == 1 ? volumeAbsorptionScore :
     issue68BaseTopId == 2 ? volumeBreakoutConfirmation :
     issue68BaseTopId == 3 ? f_weighted2(volumeAbsorptionScore, 0.50, 100.0 - volumeDistributionScore, 0.50) :
     issue68BaseTopId == 4 ? volumeDistributionScore :
     issue68BaseTopId == 5 ? volumeBreakdownConfirmation :
     issue68BaseTopId == 6 ? f_weighted2(volumeDistributionScore, 0.50, 100.0 - volumeAbsorptionScore, 0.50) : 0.0
issue68BaseMtfSupportStrength = issue68BaseTopId == 1 ? mtfAbsorptionScore :
     issue68BaseTopId == 2 ? mtfMarkupConfirmScore :
     issue68BaseTopId == 3 ? f_weighted2(mtfAbsorptionScore, 0.50, 100.0 - mtfDistributionScore, 0.50) :
     issue68BaseTopId == 4 ? mtfDistributionScore :
     issue68BaseTopId == 5 ? mtfMarkdownConfirmScore :
     issue68BaseTopId == 6 ? f_weighted2(mtfDistributionScore, 0.50, 100.0 - mtfAbsorptionScore, 0.50) : 0.0
issue68BaseWitnessSupportStrength = volumeActive and mtfActive ? f_weighted2(issue68BaseVolumeSupportStrength, volumeWeightApplied, issue68BaseMtfSupportStrength, mtfWeightApplied) : volumeActive ? issue68BaseVolumeSupportStrength : mtfActive ? issue68BaseMtfSupportStrength : 0.0
issue68BasePriceOnlyEvidenceStrength = f_weighted4(issue68BaseEffTotalStrength, 0.30, issue68BaseTopEffStrength, 0.25, issue68BaseTopGapStrength, 0.20, issue68BaseStageSupportStrength, 0.25)
issue68BaseEvidenceStrength = witnessActive ? f_weighted5(issue68BaseEffTotalStrength, 0.25, issue68BaseTopEffStrength, 0.20, issue68BaseTopGapStrength, 0.20, issue68BaseStageSupportStrength, 0.25, issue68BaseWitnessSupportStrength, 0.10) : issue68BasePriceOnlyEvidenceStrength
issue68BaseHasEvidence = not na(issue68BaseEvidenceStrength) and issue68BaseEvidenceStrength >= evidenceMin
issue68BaseHasHighEvidence = not na(issue68BaseEvidenceStrength) and issue68BaseEvidenceStrength >= evidenceHigh

issue68BaseLowStageDisputeGap = math.abs(issue68BaseP1 - issue68BaseP6)
issue68BaseHighStageDisputeGap = math.abs(issue68BaseP3 - issue68BaseP4)
issue68BaseTrendUpStageDisputeGap = math.abs(issue68BaseP2 - issue68BaseP4)
issue68BaseTrendDnStageDisputeGap = math.abs(issue68BaseP5 - issue68BaseP1)
issue68BaseLowStageDispute = rangeGate > 0.35 and downtrendGate > 0.25 and issue68BaseP1 >= stageDisputeMinWeight and issue68BaseP6 >= stageDisputeMinWeight and issue68BaseLowStageDisputeGap <= stageDisputeMaxGap
issue68BaseHighStageDispute = rangeGate > 0.35 and uptrendGate > 0.25 and issue68BaseP3 >= stageDisputeMinWeight and issue68BaseP4 >= stageDisputeMinWeight and issue68BaseHighStageDisputeGap <= stageDisputeMaxGap
issue68BaseTrendStageDispute = (markupExtensionScore >= trendExtThreshold and issue68BaseP2 >= stageDisputeMinWeight and issue68BaseP4 >= stageDisputeMinWeight and issue68BaseTrendUpStageDisputeGap <= stageDisputeMaxGap) or (markdownExtensionScore >= trendExtThreshold and issue68BaseP5 >= stageDisputeMinWeight and issue68BaseP1 >= stageDisputeMinWeight and issue68BaseTrendDnStageDisputeGap <= stageDisputeMaxGap)
issue68BaseCandidateConflict = (issue68BaseTopId == 6 and downsideExhaustion >= absorbThreshold and supportHolding >= absorbThreshold and not markdownContinuationOverride) or (issue68BaseTopId == 1 and resistanceHolding >= absorbThreshold and upsideExhaustion >= absorbThreshold and not markdownContinuationOverride) or (issue68BaseTopId == 4 and supportHolding >= absorbThreshold and downsideExhaustion >= absorbThreshold and not markupContinuationOverride) or (issue68BaseTopId == 3 and upsideExhaustion >= absorbThreshold and resistanceHolding >= absorbThreshold and not markupContinuationOverride) or (issue68BaseTopId == 2 and upsideExhaustion >= absorbThreshold and resistanceHolding >= absorbThreshold and not markupContinuationOverride) or (issue68BaseTopId == 5 and downsideExhaustion >= absorbThreshold and supportHolding >= absorbThreshold and not markdownContinuationOverride)
issue68BaseChaosRaw = not issue68BaseHasSharp or issue68BaseTopVal < dominantMin or (issue68BaseEvidenceStrength < 25.0 and issue68BaseTopVal < highConfidence)
issue68BaseCoexistRaw = (issue68BaseHasSharp and issue68BaseTopVal >= dominantMin and issue68BaseTopGap < topGapMin and issue68BaseEvidenceStrength >= 25.0) or issue68BaseLowStageDispute or issue68BaseHighStageDispute
issue68BaseWeakCandidateRaw = issue68BaseHasSharp and issue68BaseTopVal >= dominantMin and issue68BaseTopGap >= topGapMin and (not issue68BaseHasEvidence or issue68BaseCandidateConflict)
issue68BaseStrongCandidate = issue68BaseHasSharp and issue68BaseTopVal >= dominantMin and issue68BaseTopGap >= topGapMin and issue68BaseHasEvidence and not issue68BaseCandidateConflict
issue68BaseFastMarkupSwitch = issue68BaseStrongCandidate and issue68BaseTopId == 2 and issue68BaseTopVal >= fastSwitchWeight and issue68BaseTopGap >= fastSwitchGap and issue68BaseEvidenceStrength >= fastSwitchEvidence and markupContinuationScore >= fastSwitchExt and markupExtensionScore >= trendExtThreshold and close > ma and close > maturityMa
issue68BaseFastMarkdownSwitch = issue68BaseStrongCandidate and issue68BaseTopId == 5 and issue68BaseTopVal >= fastSwitchWeight and issue68BaseTopGap >= fastSwitchGap and issue68BaseEvidenceStrength >= fastSwitchEvidence and markdownContinuationScore >= fastSwitchExt and markdownExtensionScore >= trendExtThreshold and close < ma and close < maturityMa
issue68BaseActiveConfirmBars = (issue68BaseFastMarkupSwitch or issue68BaseFastMarkdownSwitch) ? fastSwitchConfirmBars : confirmBars
issue68BaseCandidateRawId = issue68BaseStrongCandidate ? issue68BaseTopId : 0
issue68BaseCandidateDisplayRawId = (issue68BaseStrongCandidate or issue68BaseWeakCandidateRaw) ? issue68BaseTopId : 0

var int issue68BaseConfirmedId = 0
var int issue68BaseCandidateId = 0
var int issue68BaseCandidateBars = 0
var int issue68BaseStalePressureBars = 0
int issue68BaseStalePressureReason = 0
issue68BaseStaleLimit = confirmBars * 2
if issue68BaseStrongCandidate
    issue68BaseStalePressureBars := 0
    issue68BaseStalePressureReason := 0
    if issue68BaseCandidateRawId == issue68BaseCandidateId
        issue68BaseCandidateBars += 1
    else
        issue68BaseCandidateId := issue68BaseCandidateRawId
        issue68BaseCandidateBars := 1
    if issue68BaseCandidateBars >= issue68BaseActiveConfirmBars
        issue68BaseConfirmedId := issue68BaseCandidateId
else
    issue68BaseCandidateId := 0
    issue68BaseCandidateBars := 0
    issue68BaseWeakChallenger = issue68BaseConfirmedId != 0 and issue68BaseCandidateDisplayRawId != 0 and issue68BaseCandidateDisplayRawId != issue68BaseConfirmedId
    issue68BaseCoexistPressure = issue68BaseConfirmedId != 0 and issue68BaseCoexistRaw and issue68BaseCandidateDisplayRawId == 0
    issue68BaseStalePressureReason := issue68BaseChaosRaw and issue68BaseConfirmedId != 0 ? 1 : issue68BaseWeakChallenger ? 2 : issue68BaseCoexistPressure ? 3 : 0
    if issue68BaseStalePressureReason != 0
        issue68BaseStalePressureBars += 1
        if issue68BaseStalePressureBars >= issue68BaseStaleLimit
            issue68BaseConfirmedId := 0
    else
        issue68BaseStalePressureBars := 0
issue68BaseFormalId = issue68BaseConfirmedId

// Deterministic invariant and cohort diagnostics.
issue68CapBindS1 = downsideExhaustionGate > currentBearGate
issue68CapBindS4 = upsideExhaustionGate > currentBullGate
issue68AnyCapBind = issue68CapBindS1 or issue68CapBindS4
issue68Ready = not na(accEff) and not na(distEff) and not na(issue68BaseAccEff) and not na(issue68BaseDistEff)
issue68MonotonicViolation = issue68Ready and (accEff > issue68BaseAccEff + 0.000001 or distEff > issue68BaseDistEff + 0.000001)
issue68NonBindTopParityViolation = issue68Ready and not issue68AnyCapBind and issue68BaseTopId != topId
issue68TopChanged = issue68Ready and issue68BaseTopId != topId
issue68FormalChanged = issue68Ready and issue68BaseFormalId != formalId
issue68BaseStaleS1 = issue68Ready and issue68BaseTopId == 1 and issue68CapBindS1
issue68BaseStaleS4 = issue68Ready and issue68BaseTopId == 4 and issue68CapBindS4
issue68StaleS1Corrected = issue68BaseStaleS1 and topId != 1
issue68StaleS4Corrected = issue68BaseStaleS4 and topId != 4
issue68BaseHighConfStaleS1 = issue68BaseStaleS1 and issue68BaseTopVal >= highConfidence and issue68BaseHasHighEvidence
issue68BaseHighConfStaleS4 = issue68BaseStaleS4 and issue68BaseTopVal >= highConfidence and issue68BaseHasHighEvidence
issue68HighConfStaleS1Corrected = issue68BaseHighConfStaleS1 and topId != 1
issue68HighConfStaleS4Corrected = issue68BaseHighConfStaleS4 and topId != 4
issue68FreshS1 = issue68Ready and issue68BaseTopId == 1 and bearBg >= 35.0 and downsideExhaustion >= 35.0 and close - close[20] <= 0.0
issue68FreshS4 = issue68Ready and issue68BaseTopId == 4 and bullBg >= 35.0 and upsideExhaustion >= 35.0 and close - close[20] >= 0.0
issue68FreshS1Retained = issue68FreshS1 and topId == 1
issue68FreshS4Retained = issue68FreshS4 and topId == 4

var int issue68ValidN = 0
var int issue68BindS1N = 0
var int issue68BindS4N = 0
var int issue68TopChangedN = 0
var int issue68FormalChangedN = 0
var int issue68MonoViolationN = 0
var int issue68NonBindViolationN = 0
var int issue68StaleS1N = 0
var int issue68StaleS4N = 0
var int issue68StaleS1CorrectedN = 0
var int issue68StaleS4CorrectedN = 0
var int issue68HighConfStaleS1N = 0
var int issue68HighConfStaleS4N = 0
var int issue68HighConfStaleS1CorrectedN = 0
var int issue68HighConfStaleS4CorrectedN = 0
var int issue68FreshS1N = 0
var int issue68FreshS4N = 0
var int issue68FreshS1RetainedN = 0
var int issue68FreshS4RetainedN = 0
var int issue68FormalDiffRun = 0
var int issue68FormalDiffRunMax = 0
if issue68Ready
    issue68ValidN += 1
    issue68BindS1N += issue68CapBindS1 ? 1 : 0
    issue68BindS4N += issue68CapBindS4 ? 1 : 0
    issue68TopChangedN += issue68TopChanged ? 1 : 0
    issue68FormalChangedN += issue68FormalChanged ? 1 : 0
    issue68MonoViolationN += issue68MonotonicViolation ? 1 : 0
    issue68NonBindViolationN += issue68NonBindTopParityViolation ? 1 : 0
    issue68StaleS1N += issue68BaseStaleS1 ? 1 : 0
    issue68StaleS4N += issue68BaseStaleS4 ? 1 : 0
    issue68StaleS1CorrectedN += issue68StaleS1Corrected ? 1 : 0
    issue68StaleS4CorrectedN += issue68StaleS4Corrected ? 1 : 0
    issue68HighConfStaleS1N += issue68BaseHighConfStaleS1 ? 1 : 0
    issue68HighConfStaleS4N += issue68BaseHighConfStaleS4 ? 1 : 0
    issue68HighConfStaleS1CorrectedN += issue68HighConfStaleS1Corrected ? 1 : 0
    issue68HighConfStaleS4CorrectedN += issue68HighConfStaleS4Corrected ? 1 : 0
    issue68FreshS1N += issue68FreshS1 ? 1 : 0
    issue68FreshS4N += issue68FreshS4 ? 1 : 0
    issue68FreshS1RetainedN += issue68FreshS1Retained ? 1 : 0
    issue68FreshS4RetainedN += issue68FreshS4Retained ? 1 : 0
    if issue68FormalChanged
        issue68FormalDiffRun += 1
        issue68FormalDiffRunMax := math.max(issue68FormalDiffRunMax, issue68FormalDiffRun)
    else
        issue68FormalDiffRun := 0

f_issue68Pct(int num, int den) => den > 0 ? str.tostring(100.0 * num / den, "#.0") + "%" : "n/a"
f_issue68Pair(int num, int den) => str.tostring(num) + " / " + str.tostring(den) + " (" + f_issue68Pct(num, den) + ")"

var table issue68RegTable = table.new(position.top_left, 4, 14, border_width=1)
if barstate.islast
    if showIssue68RegressionTable
        issue68InvPass = issue68MonoViolationN == 0 and issue68NonBindViolationN == 0
        table.cell(issue68RegTable, 0, 0, "ISSUE #68 HARD REG", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68RegTable, 1, 0, syminfo.ticker, bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68RegTable, 2, 0, useYieldLevel ? "Yield Level" : "Price Log", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68RegTable, 3, 0, issue68InvPass ? "INVARIANTS PASS" : "INVARIANTS FAIL", bgcolor=issue68InvPass ? colAcc : colMarkdown, text_color=color.white)
        table.cell(issue68RegTable, 0, 1, "Valid bars")
        table.cell(issue68RegTable, 1, 1, str.tostring(issue68ValidN))
        table.cell(issue68RegTable, 2, 1, "confirm/stale")
        table.cell(issue68RegTable, 3, 1, str.tostring(confirmBars) + " / " + str.tostring(staleLimit))
        table.cell(issue68RegTable, 0, 2, "Cap bind S1 / S4")
        table.cell(issue68RegTable, 1, 2, str.tostring(issue68BindS1N))
        table.cell(issue68RegTable, 2, 2, str.tostring(issue68BindS4N))
        table.cell(issue68RegTable, 3, 2, "exact 35/75")
        table.cell(issue68RegTable, 0, 3, "TOP changed")
        table.cell(issue68RegTable, 1, 3, str.tostring(issue68TopChangedN))
        table.cell(issue68RegTable, 2, 3, "Formal changed")
        table.cell(issue68RegTable, 3, 3, str.tostring(issue68FormalChangedN))
        table.cell(issue68RegTable, 0, 4, "Monotonic violations")
        table.cell(issue68RegTable, 1, 4, str.tostring(issue68MonoViolationN))
        table.cell(issue68RegTable, 2, 4, "Nonbind TOP violations")
        table.cell(issue68RegTable, 3, 4, str.tostring(issue68NonBindViolationN))
        table.cell(issue68RegTable, 0, 5, "Stale S1 corrected")
        table.cell(issue68RegTable, 1, 5, f_issue68Pair(issue68StaleS1CorrectedN, issue68StaleS1N))
        table.cell(issue68RegTable, 2, 5, "Stale S4 corrected")
        table.cell(issue68RegTable, 3, 5, f_issue68Pair(issue68StaleS4CorrectedN, issue68StaleS4N))
        table.cell(issue68RegTable, 0, 6, "HC stale S1 corrected")
        table.cell(issue68RegTable, 1, 6, f_issue68Pair(issue68HighConfStaleS1CorrectedN, issue68HighConfStaleS1N))
        table.cell(issue68RegTable, 2, 6, "HC stale S4 corrected")
        table.cell(issue68RegTable, 3, 6, f_issue68Pair(issue68HighConfStaleS4CorrectedN, issue68HighConfStaleS4N))
        table.cell(issue68RegTable, 0, 7, "Fresh S1 retained")
        table.cell(issue68RegTable, 1, 7, f_issue68Pair(issue68FreshS1RetainedN, issue68FreshS1N))
        table.cell(issue68RegTable, 2, 7, "Fresh S4 retained")
        table.cell(issue68RegTable, 3, 7, f_issue68Pair(issue68FreshS4RetainedN, issue68FreshS4N))
        table.cell(issue68RegTable, 0, 8, "Formal diff max run")
        table.cell(issue68RegTable, 1, 8, str.tostring(issue68FormalDiffRunMax))
        table.cell(issue68RegTable, 2, 8, "Review flag > staleLimit")
        table.cell(issue68RegTable, 3, 8, issue68FormalDiffRunMax > staleLimit ? "YES" : "NO")
        table.cell(issue68RegTable, 0, 9, "Now Base TOP/Formal")
        table.cell(issue68RegTable, 1, 9, str.tostring(issue68BaseTopId) + " / " + str.tostring(issue68BaseFormalId))
        table.cell(issue68RegTable, 2, 9, "Now HARD TOP/Formal")
        table.cell(issue68RegTable, 3, 9, str.tostring(topId) + " / " + str.tostring(formalId))
        table.cell(issue68RegTable, 0, 10, "Now cap S1/S4")
        table.cell(issue68RegTable, 1, 10, (issue68CapBindS1 ? "BIND" : "same") + " / " + (issue68CapBindS4 ? "BIND" : "same"))
        table.cell(issue68RegTable, 2, 10, "Bear/Bull gate")
        table.cell(issue68RegTable, 3, 10, str.tostring(currentBearGate, "#.00") + " / " + str.tostring(currentBullGate, "#.00"))
        table.cell(issue68RegTable, 0, 11, "Base S1/S4 eff")
        table.cell(issue68RegTable, 1, 11, str.tostring(issue68BaseAccEff, "#.0") + " / " + str.tostring(issue68BaseDistEff, "#.0"))
        table.cell(issue68RegTable, 2, 11, "HARD S1/S4 eff")
        table.cell(issue68RegTable, 3, 11, str.tostring(accEff, "#.0") + " / " + str.tostring(distEff, "#.0"))
        table.cell(issue68RegTable, 0, 12, "No PnL / no tuning")
        table.cell(issue68RegTable, 1, 12, "FROZEN")
        table.cell(issue68RegTable, 2, 12, "Representation")
        table.cell(issue68RegTable, 3, 12, "shared")
        table.cell(issue68RegTable, 0, 13, "Human focus")
        table.cell(issue68RegTable, 1, 13, "FR10Y 2021-24")
        table.cell(issue68RegTable, 2, 13, "Then 6 markets")
        table.cell(issue68RegTable, 3, 13, "1D")
    else
        table.clear(issue68RegTable)

plot(showIssue68RegressionLines ? issue68BaseTopId : na, "A C2 Baseline TOP", color=color.gray, linewidth=1, style=plot.style_stepline)
plot(showIssue68RegressionLines ? topId : na, "B HARD TOP", color=color.blue, linewidth=1, style=plot.style_stepline)
plot(showIssue68RegressionLines ? issue68BaseFormalId : na, "A C2 Baseline Formal", color=color.gray, linewidth=2, style=plot.style_stepline)
plot(showIssue68RegressionLines ? formalId : na, "B HARD Formal", color=color.purple, linewidth=2, style=plot.style_stepline)
'''

REQUIRED = (
    "issue68BaseAccGate = rangeGate * bearBackgroundForAccGate * downsideExhaustionGate",
    "issue68BaseDistGate = rangeGate * bullBackgroundForDistGate * upsideExhaustionGate",
    "issue68MonotonicViolation",
    "issue68NonBindTopParityViolation",
    "issue68BaseFormalId = issue68BaseConfirmedId",
    "issue68BaseHighConfStaleS1",
    "issue68FreshS1Retained",
    '"A C2 Baseline TOP"',
    '"B HARD Formal"',
)


def generate(source_path: Path) -> str:
    candidate, _ = yield_safe.generate(source_path)
    text = replace_once(candidate, DECL_OLD, DECL_NEW)
    text = replace_once(text, ANCHOR, AUDIT_BODY)

    for token in REQUIRED:
        if token not in text:
            raise RuntimeError(f"regression audit missing token: {token}")
    for token in (hard.CURRENT_BEAR, hard.CURRENT_BULL, hard.CTX_DOWN, hard.CTX_UP, hard.NEW_ACC_GATE, hard.NEW_DIST_GATE):
        if text.count(token) != 1:
            raise RuntimeError(f"HARD invariant changed in audit: {token}")
    if "strategy." in text or "strategy(" in text:
        raise RuntimeError("strategy/PnL logic leaked into regression audit")

    base_plots = len(hard.PLOT_CALL_RE.findall(candidate))
    audit_plots = len(hard.PLOT_CALL_RE.findall(text))
    if audit_plots != base_plots + 4:
        raise RuntimeError(f"unexpected audit plot footprint: production={base_plots}, audit={audit_plots}")
    if audit_plots >= 64:
        raise RuntimeError(f"audit exceeds TradingView plot ceiling: {audit_plots}")
    return text


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate Issue #68 yield-safe HARD six-market regression audit")
    ap.add_argument("--source", type=Path, default=Path(__file__).resolve().parent / SOURCE_RELATIVE)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    text = generate(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    print(args.output)
    print("Issue #68 yield-safe HARD regression audit static contract PASS")


if __name__ == "__main__":
    main()
