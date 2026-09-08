#!/usr/bin/env python3
"""Generate Issue #68 support-invariant slope-dulling shadow Pine."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_phase_b_lifecycle_pine as phase_b
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 Support-Invariant Slope Shadow", shorttitle="ChaseRisk #68 SI Slope", overlay=false, precision=3)'

BODY = r'''

// ============================================================================
// Issue #68 Support-Invariant Slope-Dulling Shadow.
// Shared window: 2022-01-03 -> 2023-12-29, expected Bull yield regime.
// DISCOVERY ONLY. NO PNL. NO TUNING. PRODUCTION C-2 FROZEN.
// ============================================================================

groupIssue68SI = "Issue #68｜Support-Invariant Slope Shadow"
showIssue68SITable = input.bool(true, "顯示 Support-Invariant Shadow 表", group=groupIssue68SI)

int issue68SIStart = timestamp(2022, 1, 3, 0, 0)
int issue68SIEnd = timestamp(2023, 12, 29, 23, 59)
bool issue68SIInWindow = time >= issue68SIStart and time <= issue68SIEnd

f_issue68SIBpSlope() =>
    float regNow = ta.linreg(close, speedLen, 0)
    float regPrev = ta.linreg(close, speedLen, 1)
    (regNow - regPrev) * speedLen * 100.0

f_issue68SIAvg(float s, int n) => n > 0 ? s / n : na
f_issue68SIPct(int n, int d) => d > 0 ? 100.0 * n / d : na
f_issue68SIFmt(float x) => na(x) ? "NA" : str.tostring(x, "#.##")
f_issue68SIFmtPct(int n, int d) => d > 0 ? str.tostring(100.0 * n / d, "#.##") + "%" : "NA"

// --- Full-support slope rank and reciprocal slope-dulling pair ---
float issue68SIBpSlope20 = f_issue68SIBpSlope()
float issue68SIBpRankFull = ta.percentrank(issue68SIBpSlope20, rankLen)
float issue68SINegDull = not na(issue68SIBpRankFull) ? f_gate(issue68SIBpRankFull, 15.0, 55.0) * 100.0 : na
float issue68SIPosDull = not na(issue68SIBpRankFull) ? f_gate(100.0 - issue68SIBpRankFull, 15.0, 55.0) * 100.0 : na

// --- Shared FR/DE reference, diagnostic only; never enters the classifier shadow ---
float issue68SIFrBp = request.security("TVC:FR10Y", timeframe.period, f_issue68SIBpSlope())
float issue68SIDeBp = request.security("TVC:DE10Y", timeframe.period, f_issue68SIBpSlope())
float issue68SIFrMean = ta.sma(issue68SIFrBp, rankLen)
float issue68SIDeMean = ta.sma(issue68SIDeBp, rankLen)
float issue68SIFrMeanSq = ta.sma(issue68SIFrBp * issue68SIFrBp, rankLen)
float issue68SIDeMeanSq = ta.sma(issue68SIDeBp * issue68SIDeBp, rankLen)
float issue68SIPooledMean = (issue68SIFrMean + issue68SIDeMean) * 0.5
float issue68SIPooledMeanSq = (issue68SIFrMeanSq + issue68SIDeMeanSq) * 0.5
float issue68SIPooledVar = math.max(issue68SIPooledMeanSq - issue68SIPooledMean * issue68SIPooledMean, 0.0)
float issue68SIPooledStd = math.sqrt(issue68SIPooledVar)
float issue68SICommonZ = not na(issue68SIPooledStd) and issue68SIPooledStd > 0.0 ? (issue68SIBpSlope20 - issue68SIPooledMean) / issue68SIPooledStd : na

// --- Symmetric exhaustion shadows ---
float issue68SIDownEx = f_clamp(f_weighted5(noBreakLowScore, 0.30, issue68SINegDull, 0.25, panicDullScore, 0.20, lowVolScore, 0.15, lowZoneStableScore, 0.10), 0.0, 100.0)
float issue68SIUpEx = f_clamp(f_weighted5(noBreakHighScore, 0.30, issue68SIPosDull, 0.25, heatDullScore, 0.20, lowVolScore, 0.15, highZoneStableScore, 0.10), 0.0, 100.0)
float issue68SIDownExGate = f_gate(issue68SIDownEx, 35.0, absorbThreshold)
float issue68SIUpExGate = f_gate(issue68SIUpEx, 35.0, absorbThreshold)
float issue68SINonAbsorptionGate = f_gate(100.0 - issue68SIDownEx, 25.0, 65.0)
float issue68SINonDistributionGate = f_gate(100.0 - issue68SIUpEx, 25.0, 65.0)

// --- Continuation shadows because exhaustion enters both reciprocal paths ---
float issue68SIMarkupContinuationScore = f_clamp(f_weighted5(rangeContinuationUpScore, 0.30, maBullSpreadScore, 0.25, markupExtensionScore, 0.25, 100.0 - math.max(issue68SIUpEx, resistanceHolding), 0.10, structureStrong, 0.10), 0.0, 100.0)
float issue68SIMarkdownContinuationScore = f_clamp(f_weighted5(rangeContinuationDnScore, 0.30, maBearSpreadScore, 0.25, markdownExtensionScore, 0.25, 100.0 - math.max(issue68SIDownEx, supportHolding), 0.10, structureWeak, 0.10), 0.0, 100.0)
float issue68SINonMarkupContinuationGate = f_gate(100.0 - issue68SIMarkupContinuationScore, 15.0, 60.0)
float issue68SINonMarkdownContinuationGate = f_gate(100.0 - issue68SIMarkdownContinuationScore, 15.0, 60.0)
float issue68SIMarkupContinuationGate = rangeContinuationUpGate * maBullSpreadGate * markupContinuationSupport * structureStrongGate * f_gate(100.0 - math.max(issue68SIUpEx, resistanceHolding), 20.0, 70.0)
float issue68SIMarkdownContinuationGate = rangeContinuationDnGate * maBearSpreadGate * markdownContinuationSupport * structureWeakGate * f_gate(100.0 - math.max(issue68SIDownEx, supportHolding), 20.0, 70.0)

// --- Mechanically propagate every direct RAW dependency ---
float issue68SIAccRaw0 = f_weighted5(bearMaturityTrace, 0.20, rangeScore, 0.20, issue68SIDownEx, 0.25, supportHolding, 0.25, lowVolScore, 0.10)
float issue68SIAccTraceForMarkup = ta.highest(issue68SIAccRaw0, absorbLen)
float issue68SIMarkupBaseRaw = f_weighted5(breakoutScore, 0.20, heatUp, 0.20, structureStrong, 0.20, markupExtensionScore, 0.25, issue68SIMarkupContinuationScore, 0.15)
float issue68SIMarkupRaw0 = f_weighted2(issue68SIMarkupBaseRaw, 0.85, issue68SIAccTraceForMarkup, 0.15)
float issue68SIReaccRaw0 = f_weighted5(bullBg, 0.20, rangeScore, 0.20, supportHolding, 0.25, 100.0 - panicHeatDn, 0.20, 100.0 - issue68SIUpEx, 0.15)
float issue68SIDistRaw0 = f_weighted5(bullMaturityTrace, 0.20, rangeScore, 0.20, issue68SIUpEx, 0.25, resistanceHolding, 0.25, lowVolScore, 0.10)
float issue68SIMarkdownBaseRaw = f_weighted5(explicitBreakdownScore, 0.20, panicHeatDn, 0.20, structureWeak, 0.20, markdownExtensionScore, 0.25, issue68SIMarkdownContinuationScore, 0.15)
float issue68SIDistTraceForMarkdown = ta.highest(issue68SIDistRaw0, absorbLen)
float issue68SIMarkdownRaw0 = f_weighted2(issue68SIMarkdownBaseRaw, 0.85, issue68SIDistTraceForMarkdown, 0.15)
float issue68SIRedistRaw0 = f_weighted5(bearBg, 0.20, rangeScore, 0.20, resistanceHolding, 0.25, 100.0 - heatUp, 0.20, 100.0 - issue68SIDownEx, 0.15)

float issue68SIAccRaw = f_smooth(f_clamp(issue68SIAccRaw0, 0.0, 100.0), stageSmoothLen)
float issue68SIMarkupRaw = f_smooth(f_clamp(issue68SIMarkupRaw0, 0.0, 100.0), stageSmoothLen)
float issue68SIReaccRaw = f_smooth(f_clamp(issue68SIReaccRaw0, 0.0, 100.0), stageSmoothLen)
float issue68SIDistRaw = f_smooth(f_clamp(issue68SIDistRaw0, 0.0, 100.0), stageSmoothLen)
float issue68SIMarkdownRaw = f_smooth(f_clamp(issue68SIMarkdownRaw0, 0.0, 100.0), stageSmoothLen)
float issue68SIRedistRaw = f_smooth(f_clamp(issue68SIRedistRaw0, 0.0, 100.0), stageSmoothLen)

// --- Mechanically propagate every direct Gate dependency ---
float issue68SIAccGate = rangeGate * bearBackgroundForAccGate * issue68SIDownExGate * supportHoldingGate * issue68SINonMarkdownContinuationGate
float issue68SIMarkupGate = math.max(math.max(breakoutMarkupGate, markupExtensionGate), issue68SIMarkupContinuationGate)
float issue68SIReaccGate = rangeGate * uptrendGate * supportHoldingGate * issue68SINonDistributionGate * f_gate(100.0 - bearPressureRising, 25.0, 75.0) * issue68SINonMarkupContinuationGate
float issue68SIDistGate = rangeGate * bullBackgroundForDistGate * issue68SIUpExGate * resistanceHoldingGate * issue68SINonMarkupContinuationGate
float issue68SIMarkdownGate = math.max(math.max(breakdownMarkdownGate, markdownExtensionGate), issue68SIMarkdownContinuationGate)
float issue68SIRedistGate = rangeGate * downtrendGate * resistanceHoldingGate * reboundFailureGate * issue68SINonAbsorptionGate * issue68SINonMarkdownContinuationGate

float issue68SIAccEff = issue68SIAccRaw * issue68SIAccGate * accVolMult * accMtfMult * accDivMult
float issue68SIMarkupEff = issue68SIMarkupRaw * issue68SIMarkupGate * markupVolMult * markupMtfMult
float issue68SIReaccEff = issue68SIReaccRaw * issue68SIReaccGate * reaccVolMult * reaccMtfMult
float issue68SIDistEff = issue68SIDistRaw * issue68SIDistGate * distVolMult * distMtfMult * distDivMult
float issue68SIMarkdownEff = issue68SIMarkdownRaw * issue68SIMarkdownGate * markdownVolMult * markdownMtfMult
float issue68SIRedistEff = issue68SIRedistRaw * issue68SIRedistGate * redistVolMult * redistMtfMult

// TOP ordering can be compared on effective scores because gamma is common and monotonic.
float issue68SITopEff = issue68SIAccEff
int issue68SITopId = 1
if issue68SIMarkupEff > issue68SITopEff
    issue68SITopEff := issue68SIMarkupEff
    issue68SITopId := 2
if issue68SIReaccEff > issue68SITopEff
    issue68SITopEff := issue68SIReaccEff
    issue68SITopId := 3
if issue68SIDistEff > issue68SITopEff
    issue68SITopEff := issue68SIDistEff
    issue68SITopId := 4
if issue68SIMarkdownEff > issue68SITopEff
    issue68SITopEff := issue68SIMarkdownEff
    issue68SITopId := 5
if issue68SIRedistEff > issue68SITopEff
    issue68SITopEff := issue68SIRedistEff
    issue68SITopId := 6

bool issue68SIValid = issue68SIInWindow and not na(issue68SIBpRankFull) and not na(speedRank) and not na(issue68SIAccEff) and not na(issue68SIMarkupEff)
bool issue68SIProdS2OverS1 = issue68SIValid and markupEff > accEff
bool issue68SIShadowS2OverS1 = issue68SIValid and issue68SIMarkupEff > issue68SIAccEff
bool issue68SIProdBullTop = issue68SIValid and (topId == 2 or topId == 3)
bool issue68SIShadowBullTop = issue68SIValid and (issue68SITopId == 2 or issue68SITopId == 3)
bool issue68SITopChanged = issue68SIValid and topId != issue68SITopId

var int issue68SIN = 0
var int issue68SIProdS2OverS1N = 0
var int issue68SIShadowS2OverS1N = 0
var int issue68SIProdS1TopN = 0
var int issue68SIShadowS1TopN = 0
var int issue68SIProdS2TopN = 0
var int issue68SIShadowS2TopN = 0
var int issue68SIProdBullTopN = 0
var int issue68SIShadowBullTopN = 0
var int issue68SITopChangedN = 0

var float issue68SISumSpeedRank = 0.0
var float issue68SISumBpRank = 0.0
var float issue68SISumProdNegDull = 0.0
var float issue68SISumShadowNegDull = 0.0
var float issue68SISumProdDownEx = 0.0
var float issue68SISumShadowDownEx = 0.0
var float issue68SISumProdAccRaw = 0.0
var float issue68SISumShadowAccRaw = 0.0
var float issue68SISumProdMarkupRaw = 0.0
var float issue68SISumShadowMarkupRaw = 0.0
var float issue68SISumProdAccEff = 0.0
var float issue68SISumShadowAccEff = 0.0
var float issue68SISumProdMarkupEff = 0.0
var float issue68SISumShadowMarkupEff = 0.0
var float issue68SISumCommonZ = 0.0
var int issue68SICommonZN = 0

if issue68SIValid
    issue68SIN += 1
    issue68SIProdS2OverS1N += issue68SIProdS2OverS1 ? 1 : 0
    issue68SIShadowS2OverS1N += issue68SIShadowS2OverS1 ? 1 : 0
    issue68SIProdS1TopN += topId == 1 ? 1 : 0
    issue68SIShadowS1TopN += issue68SITopId == 1 ? 1 : 0
    issue68SIProdS2TopN += topId == 2 ? 1 : 0
    issue68SIShadowS2TopN += issue68SITopId == 2 ? 1 : 0
    issue68SIProdBullTopN += issue68SIProdBullTop ? 1 : 0
    issue68SIShadowBullTopN += issue68SIShadowBullTop ? 1 : 0
    issue68SITopChangedN += issue68SITopChanged ? 1 : 0
    issue68SISumSpeedRank += speedRank
    issue68SISumBpRank += issue68SIBpRankFull
    issue68SISumProdNegDull += negSlopeDullScore
    issue68SISumShadowNegDull += issue68SINegDull
    issue68SISumProdDownEx += downsideExhaustion
    issue68SISumShadowDownEx += issue68SIDownEx
    issue68SISumProdAccRaw += accRaw
    issue68SISumShadowAccRaw += issue68SIAccRaw
    issue68SISumProdMarkupRaw += markupRaw
    issue68SISumShadowMarkupRaw += issue68SIMarkupRaw
    issue68SISumProdAccEff += accEff
    issue68SISumShadowAccEff += issue68SIAccEff
    issue68SISumProdMarkupEff += markupEff
    issue68SISumShadowMarkupEff += issue68SIMarkupEff
    if not na(issue68SICommonZ)
        issue68SISumCommonZ += issue68SICommonZ
        issue68SICommonZN += 1

plot(issue68SIInWindow ? 3.0 : na, "Expected Bull window", color=colGreen, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68SIValid ? 2.0 : na, "Production TOP", color=topId == 2 or topId == 3 ? colGreen : colRed, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68SIValid ? 1.0 : na, "Support-invariant shadow TOP", color=issue68SITopId == 2 or issue68SITopId == 3 ? colGreen : colRed, linewidth=4, style=plot.style_linebr, display=display.pane)

var table t = table.new(position.middle_right, 4, 18, border_width=1)
if barstate.islast
    if showIssue68SITable
        table.cell(t, 0, 0, "SUPPORT-INVARIANT SHADOW", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 0, syminfo.ticker, bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 0, "PROD", bgcolor=colRed, text_color=color.white)
        table.cell(t, 3, 0, "SHADOW", bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 1, "Population", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 1, str.tostring(issue68SIN), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 1, "log support", bgcolor=colRed, text_color=color.white)
        table.cell(t, 3, 1, "full bp support", bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 2, "Slope rank avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 2, "speedRank / bpRank", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 2, f_issue68SIFmt(f_issue68SIAvg(issue68SISumSpeedRank, issue68SIN)), bgcolor=colRed, text_color=color.white)
        table.cell(t, 3, 2, f_issue68SIFmt(f_issue68SIAvg(issue68SISumBpRank, issue68SIN)), bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 3, "NegSlopeDull avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 3, "same 15/55 gate", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 3, f_issue68SIFmt(f_issue68SIAvg(issue68SISumProdNegDull, issue68SIN)), bgcolor=colRed, text_color=color.white)
        table.cell(t, 3, 3, f_issue68SIFmt(f_issue68SIAvg(issue68SISumShadowNegDull, issue68SIN)), bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 4, "DownEx avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 4, "production / shadow", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 4, f_issue68SIFmt(f_issue68SIAvg(issue68SISumProdDownEx, issue68SIN)), bgcolor=colRed, text_color=color.white)
        table.cell(t, 3, 4, f_issue68SIFmt(f_issue68SIAvg(issue68SISumShadowDownEx, issue68SIN)), bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 5, "S1 RAW avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 5, "Acc", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 5, f_issue68SIFmt(f_issue68SIAvg(issue68SISumProdAccRaw, issue68SIN)), bgcolor=colRed, text_color=color.white)
        table.cell(t, 3, 5, f_issue68SIFmt(f_issue68SIAvg(issue68SISumShadowAccRaw, issue68SIN)), bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 6, "S2 RAW avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 6, "Markup", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 6, f_issue68SIFmt(f_issue68SIAvg(issue68SISumProdMarkupRaw, issue68SIN)), bgcolor=colRed, text_color=color.white)
        table.cell(t, 3, 6, f_issue68SIFmt(f_issue68SIAvg(issue68SISumShadowMarkupRaw, issue68SIN)), bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 7, "S1 EFF avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 7, "Acc", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 7, f_issue68SIFmt(f_issue68SIAvg(issue68SISumProdAccEff, issue68SIN)), bgcolor=colRed, text_color=color.white)
        table.cell(t, 3, 7, f_issue68SIFmt(f_issue68SIAvg(issue68SISumShadowAccEff, issue68SIN)), bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 8, "S2 EFF avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 8, "Markup", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 8, f_issue68SIFmt(f_issue68SIAvg(issue68SISumProdMarkupEff, issue68SIN)), bgcolor=colRed, text_color=color.white)
        table.cell(t, 3, 8, f_issue68SIFmt(f_issue68SIAvg(issue68SISumShadowMarkupEff, issue68SIN)), bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 9, "S2 EFF > S1", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 9, "pairwise occupancy", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 9, f_issue68SIFmtPct(issue68SIProdS2OverS1N, issue68SIN), bgcolor=colRed, text_color=color.white)
        table.cell(t, 3, 9, f_issue68SIFmtPct(issue68SIShadowS2OverS1N, issue68SIN), bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 10, "S1 TOP", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 10, "global TOP", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 10, f_issue68SIFmtPct(issue68SIProdS1TopN, issue68SIN), bgcolor=colRed, text_color=color.white)
        table.cell(t, 3, 10, f_issue68SIFmtPct(issue68SIShadowS1TopN, issue68SIN), bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 11, "S2 TOP", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 11, "global TOP", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 11, f_issue68SIFmtPct(issue68SIProdS2TopN, issue68SIN), bgcolor=colRed, text_color=color.white)
        table.cell(t, 3, 11, f_issue68SIFmtPct(issue68SIShadowS2TopN, issue68SIN), bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 12, "Bull TOP", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 12, "S2 + S3", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 12, f_issue68SIFmtPct(issue68SIProdBullTopN, issue68SIN), bgcolor=colRed, text_color=color.white)
        table.cell(t, 3, 12, f_issue68SIFmtPct(issue68SIShadowBullTopN, issue68SIN), bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 13, "TOP changed", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 13, "prod != shadow", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 13, "—", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 13, f_issue68SIFmtPct(issue68SITopChangedN, issue68SIN), bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 14, "COMMON REF", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 1, 14, "FR+DE pooled", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 14, "diagnostic", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 14, "NOT CLASSIFIER", bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 15, "Common bp z avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 15, f_issue68SIFmt(f_issue68SIAvg(issue68SISumCommonZ, issue68SICommonZN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 15, str.tostring(issue68SICommonZN) + " bars", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 15, "shared reference", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 16, "INTERPRET", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 16, "Converge?", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 16, "Both improve?", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 16, "or both S1-heavy?", bgcolor=colRed, text_color=color.white)

        table.cell(t, 0, 17, "READ", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 17, "NO TUNING", bgcolor=colRed, text_color=color.white)
        table.cell(t, 2, 17, "FROZEN C-2", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 17, "SHADOW ONLY", bgcolor=colGreen, text_color=color.white)
    else
        table.clear(t, 0, 0, 3, 17)
'''


def generate(source: Path) -> str:
    d1_text = phase_b.d1.generate(source)
    if d1_text.count(phase_b.D1_EXPORT_MARKER) != 1:
        raise RuntimeError("expected exactly one D1 parity export marker")
    core = d1_text.split(phase_b.D1_EXPORT_MARKER, 1)[0].rstrip()
    core = replace_once(core, phase_b.D1_INDICATOR_DECL, AUDIT_DECL)
    out = core + "\n\n" + BODY + "\n"
    for token in (
        "Support-Invariant Slope-Dulling Shadow",
        "bpSlopeRankFull",
        "Support-invariant shadow TOP",
        "S2 EFF > S1",
        "Common bp z avg",
        "SHADOW ONLY",
    ):
        if token not in out:
            raise RuntimeError(f"missing required audit token: {token}")
    if "strategy.entry" in out or "strategy.close" in out:
        raise RuntimeError("support-invariant shadow leaked strategy order logic")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=HERE / SOURCE_RELATIVE)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    text = generate(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
