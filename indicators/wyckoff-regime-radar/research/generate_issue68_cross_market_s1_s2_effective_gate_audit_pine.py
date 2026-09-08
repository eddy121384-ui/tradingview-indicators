#!/usr/bin/env python3
"""Generate Issue #68 FR10Y vs DE10Y S1/S2 effective-gate attribution Pine."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_phase_b_lifecycle_pine as phase_b
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 S1-S2 Gate", shorttitle="ChaseRisk #68 S1S2", overlay=false, precision=2)'

BODY = r'''

// ============================================================================
// Issue #68 FR10Y vs DE10Y S1/S2 Effective-Gate Attribution Audit.
// Shared window: 2022-01-03 -> 2023-12-29, expected Bull yield regime.
// DISCOVERY ONLY. NO PNL. NO TUNING. FROZEN C-2.
// ============================================================================

groupIssue68S1S2Gate = "Issue #68｜S1-S2 Effective Gate"
showIssue68S1S2GateTable = input.bool(true, "顯示 S1-S2 Gate 統計表", group=groupIssue68S1S2Gate)

issue68S1S2Ready = bar_index >= rankLen - 1
int issue68S1S2Start = timestamp(2022, 1, 3, 0, 0)
int issue68S1S2End = timestamp(2023, 12, 29, 23, 59)
bool issue68S1S2InWindow = issue68S1S2Ready and time >= issue68S1S2Start and time <= issue68S1S2End
bool issue68S1S2PairValid = issue68S1S2InWindow and not na(accRaw) and not na(markupRaw) and not na(accEff) and not na(markupEff)

f_issue68S1S2Avg(float s, int n) => n > 0 ? s / n : na
f_issue68S1S2Pct(int n, int d) => d > 0 ? 100.0 * n / d : na

float issue68RawMargin = markupRaw - accRaw
float issue68EffMargin = markupEff - accEff
float issue68ProbMargin = p2 - p1
bool issue68RawS2LeadNow = issue68S1S2PairValid and markupRaw > accRaw
bool issue68EffS2LeadNow = issue68S1S2PairValid and markupEff > accEff

float issue68PairLinearTotal = nz(accEff) + nz(markupEff)
float issue68PairLinearP2 = issue68PairLinearTotal > 0.0 ? nz(markupEff) / issue68PairLinearTotal * 100.0 : na
float issue68PairSharpTotal = nz(accSharp) + nz(markupSharp)
float issue68PairSharpP2 = issue68PairSharpTotal > 0.0 ? nz(markupSharp) / issue68PairSharpTotal * 100.0 : na
float issue68PairSharpGap = not na(issue68PairSharpP2) ? math.abs(2.0 * issue68PairSharpP2 - 100.0) : na

int issue68S2GateSource = breakoutMarkupGate >= math.max(markupExtensionGate, markupContinuationGate) ? 1 : markupExtensionGate >= markupContinuationGate ? 2 : 3

var int issue68Bars = 0
var int issue68PairBars = 0
var int issue68TopS1 = 0
var int issue68TopS2 = 0
var int issue68RawS2Lead = 0
var int issue68EffS2Lead = 0
var int issue68RawS2ToEffS1 = 0
var int issue68RawS1ToEffS2 = 0
var int issue68EffS2OtherTop = 0
var int issue68S2GateBreakout = 0
var int issue68S2GateExtension = 0
var int issue68S2GateContinuation = 0

var float issue68SumAccRaw = 0.0
var float issue68SumAccGate = 0.0
var float issue68SumAccEff = 0.0
var float issue68SumRangeGate = 0.0
var float issue68SumBearBgAccGate = 0.0
var float issue68SumDownExhaustGate = 0.0
var float issue68SumSupportGate = 0.0
var float issue68SumNonMdContGate = 0.0

var float issue68SumMarkupRaw = 0.0
var float issue68SumMarkupGate = 0.0
var float issue68SumMarkupEff = 0.0
var float issue68SumBreakoutMarkupGate = 0.0
var float issue68SumMarkupExtensionGate = 0.0
var float issue68SumMarkupContinuationGate = 0.0

var float issue68SumRawMargin = 0.0
var float issue68SumEffMargin = 0.0
var float issue68SumProbMargin = 0.0
var float issue68SumPairLinearP2 = 0.0
var float issue68SumPairSharpP2 = 0.0
var float issue68SumPairSharpGap = 0.0

if issue68S1S2InWindow
    issue68Bars += 1
    issue68TopS1 += topId == 1 ? 1 : 0
    issue68TopS2 += topId == 2 ? 1 : 0

if issue68S1S2PairValid
    issue68PairBars += 1
    issue68RawS2Lead += issue68RawS2LeadNow ? 1 : 0
    issue68EffS2Lead += issue68EffS2LeadNow ? 1 : 0
    issue68RawS2ToEffS1 += issue68RawS2LeadNow and not issue68EffS2LeadNow ? 1 : 0
    issue68RawS1ToEffS2 += not issue68RawS2LeadNow and issue68EffS2LeadNow ? 1 : 0
    issue68EffS2OtherTop += issue68EffS2LeadNow and topId != 2 ? 1 : 0

    issue68S2GateBreakout += issue68S2GateSource == 1 ? 1 : 0
    issue68S2GateExtension += issue68S2GateSource == 2 ? 1 : 0
    issue68S2GateContinuation += issue68S2GateSource == 3 ? 1 : 0

    issue68SumAccRaw += accRaw
    issue68SumAccGate += accGate
    issue68SumAccEff += accEff
    issue68SumRangeGate += rangeGate
    issue68SumBearBgAccGate += bearBackgroundForAccGate
    issue68SumDownExhaustGate += downsideExhaustionGate
    issue68SumSupportGate += supportHoldingGate
    issue68SumNonMdContGate += nonMarkdownContinuationGate

    issue68SumMarkupRaw += markupRaw
    issue68SumMarkupGate += markupGate
    issue68SumMarkupEff += markupEff
    issue68SumBreakoutMarkupGate += breakoutMarkupGate
    issue68SumMarkupExtensionGate += markupExtensionGate
    issue68SumMarkupContinuationGate += markupContinuationGate

    issue68SumRawMargin += issue68RawMargin
    issue68SumEffMargin += issue68EffMargin
    issue68SumProbMargin += issue68ProbMargin
    issue68SumPairLinearP2 += nz(issue68PairLinearP2)
    issue68SumPairSharpP2 += nz(issue68PairSharpP2)
    issue68SumPairSharpGap += nz(issue68PairSharpGap)

float issue68TopS1Pct = f_issue68S1S2Pct(issue68TopS1, issue68Bars)
float issue68TopS2Pct = f_issue68S1S2Pct(issue68TopS2, issue68Bars)
float issue68RawS2LeadPct = f_issue68S1S2Pct(issue68RawS2Lead, issue68PairBars)
float issue68EffS2LeadPct = f_issue68S1S2Pct(issue68EffS2Lead, issue68PairBars)
float issue68RawS2ToEffS1Pct = f_issue68S1S2Pct(issue68RawS2ToEffS1, issue68PairBars)
float issue68RawS1ToEffS2Pct = f_issue68S1S2Pct(issue68RawS1ToEffS2, issue68PairBars)
float issue68EffS2OtherTopPct = f_issue68S1S2Pct(issue68EffS2OtherTop, issue68PairBars)
float issue68S2GateBreakoutPct = f_issue68S1S2Pct(issue68S2GateBreakout, issue68PairBars)
float issue68S2GateExtensionPct = f_issue68S1S2Pct(issue68S2GateExtension, issue68PairBars)
float issue68S2GateContinuationPct = f_issue68S1S2Pct(issue68S2GateContinuation, issue68PairBars)

float issue68AvgAccRaw = f_issue68S1S2Avg(issue68SumAccRaw, issue68PairBars)
float issue68AvgAccGate = f_issue68S1S2Avg(issue68SumAccGate, issue68PairBars)
float issue68AvgAccEff = f_issue68S1S2Avg(issue68SumAccEff, issue68PairBars)
float issue68AvgRangeGate = f_issue68S1S2Avg(issue68SumRangeGate, issue68PairBars)
float issue68AvgBearBgAccGate = f_issue68S1S2Avg(issue68SumBearBgAccGate, issue68PairBars)
float issue68AvgDownExhaustGate = f_issue68S1S2Avg(issue68SumDownExhaustGate, issue68PairBars)
float issue68AvgSupportGate = f_issue68S1S2Avg(issue68SumSupportGate, issue68PairBars)
float issue68AvgNonMdContGate = f_issue68S1S2Avg(issue68SumNonMdContGate, issue68PairBars)

float issue68AvgMarkupRaw = f_issue68S1S2Avg(issue68SumMarkupRaw, issue68PairBars)
float issue68AvgMarkupGate = f_issue68S1S2Avg(issue68SumMarkupGate, issue68PairBars)
float issue68AvgMarkupEff = f_issue68S1S2Avg(issue68SumMarkupEff, issue68PairBars)
float issue68AvgBreakoutMarkupGate = f_issue68S1S2Avg(issue68SumBreakoutMarkupGate, issue68PairBars)
float issue68AvgMarkupExtensionGate = f_issue68S1S2Avg(issue68SumMarkupExtensionGate, issue68PairBars)
float issue68AvgMarkupContinuationGate = f_issue68S1S2Avg(issue68SumMarkupContinuationGate, issue68PairBars)

float issue68AvgRawMargin = f_issue68S1S2Avg(issue68SumRawMargin, issue68PairBars)
float issue68AvgEffMargin = f_issue68S1S2Avg(issue68SumEffMargin, issue68PairBars)
float issue68AvgProbMargin = f_issue68S1S2Avg(issue68SumProbMargin, issue68PairBars)
float issue68AvgPairLinearP2 = f_issue68S1S2Avg(issue68SumPairLinearP2, issue68PairBars)
float issue68AvgPairSharpP2 = f_issue68S1S2Avg(issue68SumPairSharpP2, issue68PairBars)
float issue68AvgPairSharpGap = f_issue68S1S2Avg(issue68SumPairSharpGap, issue68PairBars)

plot(issue68S1S2InWindow ? 3.0 : na, "EXPECTED Bull", color=colGreen, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68S1S2PairValid ? 2.0 : na, "S2 vs S1 effective leader", color=issue68EffS2LeadNow ? colGreen : colRed, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68S1S2InWindow ? 1.0 : na, "Global TOP S2", color=topId == 2 ? colGreen : topId == 1 ? colRed : colYellow, linewidth=4, style=plot.style_linebr, display=display.pane)

var table t = table.new(position.bottom_right, 4, 30, border_width=1)
if barstate.islast
    if showIssue68S1S2GateTable
        table.cell(t, 0, 0, "S1-S2 EFFECTIVE GATE", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 0, syminfo.ticker, bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 0, "2022-2023 BULL", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 0, str.tostring(issue68PairBars) + " pair bars", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 1, "ORDER / FLIPS", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 1, 1, "SHARE", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 1, "MEANING", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 1, "FROZEN", bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 2, "S1 global TOP", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 2, str.tostring(issue68TopS1Pct, "#.1") + "%", bgcolor=colRed, text_color=color.white)
        table.cell(t, 2, 2, "final TOP", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 2, str.tostring(issue68TopS1), bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 3, "S2 global TOP", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 3, str.tostring(issue68TopS2Pct, "#.1") + "%", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 3, "final TOP", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 3, str.tostring(issue68TopS2), bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 4, "RAW S2 > S1", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 4, str.tostring(issue68RawS2LeadPct, "#.1") + "%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 4, "pre gate", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 4, "ordering", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 5, "EFF S2 > S1", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 5, str.tostring(issue68EffS2LeadPct, "#.1") + "%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 5, "post gate", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 5, "ordering", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 6, "RAW S2 -> EFF S1", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 6, str.tostring(issue68RawS2ToEffS1Pct, "#.1") + "%", bgcolor=issue68RawS2ToEffS1 > 0 ? colRed : colNeutral, text_color=color.white)
        table.cell(t, 2, 6, "gate suppress S2", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 6, str.tostring(issue68RawS2ToEffS1), bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 7, "RAW S1 -> EFF S2", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 7, str.tostring(issue68RawS1ToEffS2Pct, "#.1") + "%", bgcolor=issue68RawS1ToEffS2 > 0 ? colGreen : colNeutral, text_color=color.white)
        table.cell(t, 2, 7, "gate rescue S2", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 7, str.tostring(issue68RawS1ToEffS2), bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 8, "EFF S2 lead, other TOP", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 8, str.tostring(issue68EffS2OtherTopPct, "#.1") + "%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 8, "3rd-stage steal", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 8, str.tostring(issue68EffS2OtherTop), bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 9, "Avg RAW / EFF margin", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 9, str.tostring(issue68AvgRawMargin, "#.1") + " / " + str.tostring(issue68AvgEffMargin, "#.1"), bgcolor=issue68AvgEffMargin >= 0 ? colGreen : colRed, text_color=color.white)
        table.cell(t, 2, 9, "S2-S1", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 9, "pre/post gate", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 10, "Avg p2-p1", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 10, str.tostring(issue68AvgProbMargin, "#.1"), bgcolor=issue68AvgProbMargin >= 0 ? colGreen : colRed, text_color=color.white)
        table.cell(t, 2, 10, "post gamma", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 10, "gap only", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 11, "S1 ACC PIPE", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 1, 11, "AVG", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 11, "ROLE", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 11, "STACK", bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 12, "S1 RAW / gate / eff", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 12, str.tostring(issue68AvgAccRaw, "#.1") + " / " + str.tostring(issue68AvgAccGate, "#.3") + " / " + str.tostring(issue68AvgAccEff, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 12, "pipeline", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 12, "multiply", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 13, "S1 range gate", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 13, str.tostring(issue68AvgRangeGate, "#.3"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 13, "acc gate", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 13, "range", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 14, "S1 bear-bg gate", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 14, str.tostring(issue68AvgBearBgAccGate, "#.3"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 14, "acc gate", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 14, "history", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 15, "S1 down-exhaust gate", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 15, str.tostring(issue68AvgDownExhaustGate, "#.3"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 15, "acc gate", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 15, "exhaust", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 16, "S1 support gate", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 16, str.tostring(issue68AvgSupportGate, "#.3"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 16, "acc gate", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 16, "support", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 17, "S1 non-MD cont gate", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 17, str.tostring(issue68AvgNonMdContGate, "#.3"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 17, "acc gate", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 17, "anti-S5", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 18, "S2 MARKUP PIPE", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 1, 18, "AVG", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 18, "ROLE", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 18, "MAX PATH", bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 19, "S2 RAW / gate / eff", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 19, str.tostring(issue68AvgMarkupRaw, "#.1") + " / " + str.tostring(issue68AvgMarkupGate, "#.3") + " / " + str.tostring(issue68AvgMarkupEff, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 19, "pipeline", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 19, "RAW*maxGate", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 20, "S2 breakout gate", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 20, str.tostring(issue68AvgBreakoutMarkupGate, "#.3"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 20, "sub-gate", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 20, str.tostring(issue68S2GateBreakoutPct, "#.1") + "% wins", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 21, "S2 extension gate", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 21, str.tostring(issue68AvgMarkupExtensionGate, "#.3"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 21, "sub-gate", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 21, str.tostring(issue68S2GateExtensionPct, "#.1") + "% wins", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 22, "S2 continuation gate", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 22, str.tostring(issue68AvgMarkupContinuationGate, "#.3"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 22, "sub-gate", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 22, str.tostring(issue68S2GateContinuationPct, "#.1") + "% wins", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 23, "PAIRWISE S1/S2", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 1, 23, "AVG", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 23, "ROLE", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 23, "MATH", bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 24, "Linear pair p2", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 24, str.tostring(issue68AvgPairLinearP2, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 24, "eff share", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 24, "gamma=1 shadow", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 25, "Sharp pair p2", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 25, str.tostring(issue68AvgPairSharpP2, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 25, "eff^gamma", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 25, "frozen gamma", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 26, "Sharp pair gap", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 26, str.tostring(issue68AvgPairSharpGap, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 26, "abs p2-p1", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 26, "gap amplify", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 27, "ORDER INVARIANCE", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 27, "EFF -> gamma", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 27, "monotonic", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 27, "TOP unchanged", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 28, "MODE", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 28, "DISCOVERY", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 28, "NO TUNING", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 28, "FROZEN C-2", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 29, "READ", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 29, "Green=S2", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 29, "Red=S1", bgcolor=colRed, text_color=color.white)
        table.cell(t, 3, 29, "Yellow=other", bgcolor=colYellow, text_color=color.white)
    else
        table.clear(t, 0, 0, 3, 29)
'''.strip()


def generate(source: Path) -> str:
    d1_text = phase_b.d1.generate(source)
    if d1_text.count(phase_b.D1_EXPORT_MARKER) != 1:
        raise RuntimeError("expected exactly one D1 parity export marker")
    core = d1_text.split(phase_b.D1_EXPORT_MARKER, 1)[0].rstrip()
    core = replace_once(core, phase_b.D1_INDICATOR_DECL, AUDIT_DECL)
    out = core + "\n\n" + BODY + "\n"
    required = (
        "S1/S2 Effective-Gate Attribution Audit",
        "RAW S2 -> EFF S1",
        "S1 ACC PIPE",
        "S2 MARKUP PIPE",
        "S2 continuation gate",
        "ORDER INVARIANCE",
    )
    for token in required:
        if token not in out:
            raise RuntimeError(f"missing S1/S2 effective-gate token: {token}")
    if "strategy." in out:
        raise RuntimeError("strategy token leaked into S1/S2 effective-gate diagnostic")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=HERE / SOURCE_RELATIVE)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    text = generate(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
