#!/usr/bin/env python3
"""Generate Issue #68 FR10Y vs DE10Y downside-exhaustion component audit Pine."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_phase_b_lifecycle_pine as phase_b
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 DownEx Components", shorttitle="ChaseRisk #68 DownEx", overlay=false, precision=3)'

BODY = r'''

// ============================================================================
// Issue #68 FR10Y vs DE10Y Downside-Exhaustion Component Audit.
// Shared window: 2022-01-03 -> 2023-12-29, expected Bull yield regime.
// DISCOVERY ONLY. NO PNL. NO TUNING. FROZEN C-2.
// ============================================================================

groupIssue68DX = "Issue #68｜Downside Exhaustion Components"
showIssue68DXTable = input.bool(true, "顯示 DownEx component 表", group=groupIssue68DX)

issue68DXReady = bar_index >= rankLen - 1
int issue68DXStart = timestamp(2022, 1, 3, 0, 0)
int issue68DXEnd = timestamp(2023, 12, 29, 23, 59)
bool issue68DXInWindow = issue68DXReady and time >= issue68DXStart and time <= issue68DXEnd
bool issue68DXValid = issue68DXInWindow and not na(accRaw) and not na(markupRaw) and not na(accEff) and not na(markupEff) and not na(downsideExhaustion) and not na(downsideExhaustionGate) and not na(noBreakLowScore) and not na(negSlopeDullScore) and not na(panicDullScore) and not na(lowVolScore) and not na(lowZoneStableScore)
bool issue68DXFlip = issue68DXValid and accRaw >= markupRaw and markupEff > accEff
bool issue68DXNoFlip = issue68DXValid and accRaw >= markupRaw and not (markupEff > accEff)

f_issue68DXAvg(float s, int n) => n > 0 ? s / n : na
f_issue68DXPct(int n, int d) => d > 0 ? 100.0 * n / d : na
f_issue68DXFmt(float x) => na(x) ? "NA" : str.tostring(x, "#.##")
f_issue68DXPctFmt(int n, int d) => d > 0 ? str.tostring(100.0 * n / d, "#.##") + "%" : "NA"

float issue68DXDefNoBreak = (100.0 - noBreakLowScore) * 0.30
float issue68DXDefNegSlope = (100.0 - negSlopeDullScore) * 0.25
float issue68DXDefPanic = (100.0 - panicDullScore) * 0.20
float issue68DXDefLowVol = (100.0 - lowVolScore) * 0.15
float issue68DXDefLowZone = (100.0 - lowZoneStableScore) * 0.10
float issue68DXDefSum = issue68DXDefNoBreak + issue68DXDefNegSlope + issue68DXDefPanic + issue68DXDefLowVol + issue68DXDefLowZone
float issue68DXReconErr = issue68DXValid ? math.abs(issue68DXDefSum - (100.0 - downsideExhaustion)) : na

f_issue68DXDom(float a, float b, float c, float d, float e) =>
    float best = a
    string name = "NoBreakLow"
    if b > best
        best := b
        name := "NegSlopeDull"
    if c > best
        best := c
        name := "PanicDull"
    if d > best
        best := d
        name := "LowVol"
    if e > best
        best := e
        name := "LowZoneStable"
    name + " " + f_issue68DXFmt(best)

var int issue68DXNAll = 0
var int issue68DXNFlip = 0
var int issue68DXNNoFlip = 0

var float issue68DXSumScoreAll = 0.0
var float issue68DXSumScoreFlip = 0.0
var float issue68DXSumScoreNoFlip = 0.0
var float issue68DXSumGateAll = 0.0
var float issue68DXSumGateFlip = 0.0
var float issue68DXSumGateNoFlip = 0.0

var float issue68DXSumNoBreakAll = 0.0
var float issue68DXSumNoBreakFlip = 0.0
var float issue68DXSumNoBreakNoFlip = 0.0
var float issue68DXSumNegSlopeAll = 0.0
var float issue68DXSumNegSlopeFlip = 0.0
var float issue68DXSumNegSlopeNoFlip = 0.0
var float issue68DXSumPanicAll = 0.0
var float issue68DXSumPanicFlip = 0.0
var float issue68DXSumPanicNoFlip = 0.0
var float issue68DXSumLowVolAll = 0.0
var float issue68DXSumLowVolFlip = 0.0
var float issue68DXSumLowVolNoFlip = 0.0
var float issue68DXSumLowZoneAll = 0.0
var float issue68DXSumLowZoneFlip = 0.0
var float issue68DXSumLowZoneNoFlip = 0.0

var float issue68DXSumDefNoBreakAll = 0.0
var float issue68DXSumDefNoBreakFlip = 0.0
var float issue68DXSumDefNoBreakNoFlip = 0.0
var float issue68DXSumDefNegSlopeAll = 0.0
var float issue68DXSumDefNegSlopeFlip = 0.0
var float issue68DXSumDefNegSlopeNoFlip = 0.0
var float issue68DXSumDefPanicAll = 0.0
var float issue68DXSumDefPanicFlip = 0.0
var float issue68DXSumDefPanicNoFlip = 0.0
var float issue68DXSumDefLowVolAll = 0.0
var float issue68DXSumDefLowVolFlip = 0.0
var float issue68DXSumDefLowVolNoFlip = 0.0
var float issue68DXSumDefLowZoneAll = 0.0
var float issue68DXSumDefLowZoneFlip = 0.0
var float issue68DXSumDefLowZoneNoFlip = 0.0

var int issue68DXBelow35All = 0
var int issue68DXBelow35Flip = 0
var int issue68DXBelow35NoFlip = 0
var int issue68DXMidAll = 0
var int issue68DXMidFlip = 0
var int issue68DXMidNoFlip = 0
var int issue68DXFullAll = 0
var int issue68DXFullFlip = 0
var int issue68DXFullNoFlip = 0

var float issue68DXMaxReconErr = 0.0
var int issue68DXFlipRunsDone = 0
var int issue68DXFlipRunNow = 0
var int issue68DXFlipRunMax = 0

if issue68DXValid
    issue68DXNAll += 1
    issue68DXSumScoreAll += downsideExhaustion
    issue68DXSumGateAll += downsideExhaustionGate
    issue68DXSumNoBreakAll += noBreakLowScore
    issue68DXSumNegSlopeAll += negSlopeDullScore
    issue68DXSumPanicAll += panicDullScore
    issue68DXSumLowVolAll += lowVolScore
    issue68DXSumLowZoneAll += lowZoneStableScore
    issue68DXSumDefNoBreakAll += issue68DXDefNoBreak
    issue68DXSumDefNegSlopeAll += issue68DXDefNegSlope
    issue68DXSumDefPanicAll += issue68DXDefPanic
    issue68DXSumDefLowVolAll += issue68DXDefLowVol
    issue68DXSumDefLowZoneAll += issue68DXDefLowZone
    issue68DXBelow35All += downsideExhaustion < 35.0 ? 1 : 0
    issue68DXMidAll += downsideExhaustion >= 35.0 and downsideExhaustion < absorbThreshold ? 1 : 0
    issue68DXFullAll += downsideExhaustion >= absorbThreshold ? 1 : 0
    issue68DXMaxReconErr := math.max(issue68DXMaxReconErr, issue68DXReconErr)

    if issue68DXFlip
        issue68DXNFlip += 1
        issue68DXFlipRunNow += 1
        issue68DXFlipRunMax := math.max(issue68DXFlipRunMax, issue68DXFlipRunNow)
        issue68DXSumScoreFlip += downsideExhaustion
        issue68DXSumGateFlip += downsideExhaustionGate
        issue68DXSumNoBreakFlip += noBreakLowScore
        issue68DXSumNegSlopeFlip += negSlopeDullScore
        issue68DXSumPanicFlip += panicDullScore
        issue68DXSumLowVolFlip += lowVolScore
        issue68DXSumLowZoneFlip += lowZoneStableScore
        issue68DXSumDefNoBreakFlip += issue68DXDefNoBreak
        issue68DXSumDefNegSlopeFlip += issue68DXDefNegSlope
        issue68DXSumDefPanicFlip += issue68DXDefPanic
        issue68DXSumDefLowVolFlip += issue68DXDefLowVol
        issue68DXSumDefLowZoneFlip += issue68DXDefLowZone
        issue68DXBelow35Flip += downsideExhaustion < 35.0 ? 1 : 0
        issue68DXMidFlip += downsideExhaustion >= 35.0 and downsideExhaustion < absorbThreshold ? 1 : 0
        issue68DXFullFlip += downsideExhaustion >= absorbThreshold ? 1 : 0
    else
        if issue68DXFlipRunNow > 0
            issue68DXFlipRunsDone += 1
            issue68DXFlipRunNow := 0
        if issue68DXNoFlip
            issue68DXNNoFlip += 1
            issue68DXSumScoreNoFlip += downsideExhaustion
            issue68DXSumGateNoFlip += downsideExhaustionGate
            issue68DXSumNoBreakNoFlip += noBreakLowScore
            issue68DXSumNegSlopeNoFlip += negSlopeDullScore
            issue68DXSumPanicNoFlip += panicDullScore
            issue68DXSumLowVolNoFlip += lowVolScore
            issue68DXSumLowZoneNoFlip += lowZoneStableScore
            issue68DXSumDefNoBreakNoFlip += issue68DXDefNoBreak
            issue68DXSumDefNegSlopeNoFlip += issue68DXDefNegSlope
            issue68DXSumDefPanicNoFlip += issue68DXDefPanic
            issue68DXSumDefLowVolNoFlip += issue68DXDefLowVol
            issue68DXSumDefLowZoneNoFlip += issue68DXDefLowZone
            issue68DXBelow35NoFlip += downsideExhaustion < 35.0 ? 1 : 0
            issue68DXMidNoFlip += downsideExhaustion >= 35.0 and downsideExhaustion < absorbThreshold ? 1 : 0
            issue68DXFullNoFlip += downsideExhaustion >= absorbThreshold ? 1 : 0

int issue68DXDisplayRuns = issue68DXFlipRunsDone + (issue68DXFlipRunNow > 0 ? 1 : 0)

float issue68DXAvgNoBreakAll = f_issue68DXAvg(issue68DXSumNoBreakAll, issue68DXNAll)
float issue68DXAvgNoBreakFlip = f_issue68DXAvg(issue68DXSumNoBreakFlip, issue68DXNFlip)
float issue68DXAvgNoBreakNoFlip = f_issue68DXAvg(issue68DXSumNoBreakNoFlip, issue68DXNNoFlip)
float issue68DXAvgNegSlopeAll = f_issue68DXAvg(issue68DXSumNegSlopeAll, issue68DXNAll)
float issue68DXAvgNegSlopeFlip = f_issue68DXAvg(issue68DXSumNegSlopeFlip, issue68DXNFlip)
float issue68DXAvgNegSlopeNoFlip = f_issue68DXAvg(issue68DXSumNegSlopeNoFlip, issue68DXNNoFlip)
float issue68DXAvgPanicAll = f_issue68DXAvg(issue68DXSumPanicAll, issue68DXNAll)
float issue68DXAvgPanicFlip = f_issue68DXAvg(issue68DXSumPanicFlip, issue68DXNFlip)
float issue68DXAvgPanicNoFlip = f_issue68DXAvg(issue68DXSumPanicNoFlip, issue68DXNNoFlip)
float issue68DXAvgLowVolAll = f_issue68DXAvg(issue68DXSumLowVolAll, issue68DXNAll)
float issue68DXAvgLowVolFlip = f_issue68DXAvg(issue68DXSumLowVolFlip, issue68DXNFlip)
float issue68DXAvgLowVolNoFlip = f_issue68DXAvg(issue68DXSumLowVolNoFlip, issue68DXNNoFlip)
float issue68DXAvgLowZoneAll = f_issue68DXAvg(issue68DXSumLowZoneAll, issue68DXNAll)
float issue68DXAvgLowZoneFlip = f_issue68DXAvg(issue68DXSumLowZoneFlip, issue68DXNFlip)
float issue68DXAvgLowZoneNoFlip = f_issue68DXAvg(issue68DXSumLowZoneNoFlip, issue68DXNNoFlip)

float issue68DXAvgDefNoBreakAll = f_issue68DXAvg(issue68DXSumDefNoBreakAll, issue68DXNAll)
float issue68DXAvgDefNoBreakFlip = f_issue68DXAvg(issue68DXSumDefNoBreakFlip, issue68DXNFlip)
float issue68DXAvgDefNoBreakNoFlip = f_issue68DXAvg(issue68DXSumDefNoBreakNoFlip, issue68DXNNoFlip)
float issue68DXAvgDefNegSlopeAll = f_issue68DXAvg(issue68DXSumDefNegSlopeAll, issue68DXNAll)
float issue68DXAvgDefNegSlopeFlip = f_issue68DXAvg(issue68DXSumDefNegSlopeFlip, issue68DXNFlip)
float issue68DXAvgDefNegSlopeNoFlip = f_issue68DXAvg(issue68DXSumDefNegSlopeNoFlip, issue68DXNNoFlip)
float issue68DXAvgDefPanicAll = f_issue68DXAvg(issue68DXSumDefPanicAll, issue68DXNAll)
float issue68DXAvgDefPanicFlip = f_issue68DXAvg(issue68DXSumDefPanicFlip, issue68DXNFlip)
float issue68DXAvgDefPanicNoFlip = f_issue68DXAvg(issue68DXSumDefPanicNoFlip, issue68DXNNoFlip)
float issue68DXAvgDefLowVolAll = f_issue68DXAvg(issue68DXSumDefLowVolAll, issue68DXNAll)
float issue68DXAvgDefLowVolFlip = f_issue68DXAvg(issue68DXSumDefLowVolFlip, issue68DXNFlip)
float issue68DXAvgDefLowVolNoFlip = f_issue68DXAvg(issue68DXSumDefLowVolNoFlip, issue68DXNNoFlip)
float issue68DXAvgDefLowZoneAll = f_issue68DXAvg(issue68DXSumDefLowZoneAll, issue68DXNAll)
float issue68DXAvgDefLowZoneFlip = f_issue68DXAvg(issue68DXSumDefLowZoneFlip, issue68DXNFlip)
float issue68DXAvgDefLowZoneNoFlip = f_issue68DXAvg(issue68DXSumDefLowZoneNoFlip, issue68DXNNoFlip)

string issue68DXDomAll = f_issue68DXDom(issue68DXAvgDefNoBreakAll, issue68DXAvgDefNegSlopeAll, issue68DXAvgDefPanicAll, issue68DXAvgDefLowVolAll, issue68DXAvgDefLowZoneAll)
string issue68DXDomFlip = f_issue68DXDom(issue68DXAvgDefNoBreakFlip, issue68DXAvgDefNegSlopeFlip, issue68DXAvgDefPanicFlip, issue68DXAvgDefLowVolFlip, issue68DXAvgDefLowZoneFlip)
string issue68DXDomNoFlip = f_issue68DXDom(issue68DXAvgDefNoBreakNoFlip, issue68DXAvgDefNegSlopeNoFlip, issue68DXAvgDefPanicNoFlip, issue68DXAvgDefLowVolNoFlip, issue68DXAvgDefLowZoneNoFlip)

color issue68DXBandColor = downsideExhaustion < 35.0 ? colRed : downsideExhaustion < absorbThreshold ? colYellow : colGreen
plot(issue68DXInWindow ? 3.0 : na, "EXPECTED Bull", color=colGreen, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68DXValid ? 2.0 : na, "RAW S1 to EFF S2 flip", color=issue68DXFlip ? colGreen : colRed, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68DXValid ? 1.0 : na, "DownEx score band", color=issue68DXBandColor, linewidth=4, style=plot.style_linebr, display=display.pane)

var table t = table.new(position.middle_right, 4, 18, border_width=1)
if barstate.islast
    if showIssue68DXTable
        table.cell(t, 0, 0, "DOWNEX COMPONENTS", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 0, "ALL", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 0, "FLIP", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 0, "NO-FLIP", bgcolor=colRed, text_color=color.white)

        table.cell(t, 0, 1, "Population", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 1, str.tostring(issue68DXNAll), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 1, str.tostring(issue68DXNFlip), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 1, str.tostring(issue68DXNNoFlip), bgcolor=colRed, text_color=color.white)

        table.cell(t, 0, 2, "DownEx score avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 2, f_issue68DXFmt(f_issue68DXAvg(issue68DXSumScoreAll, issue68DXNAll)), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 2, f_issue68DXFmt(f_issue68DXAvg(issue68DXSumScoreFlip, issue68DXNFlip)), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 2, f_issue68DXFmt(f_issue68DXAvg(issue68DXSumScoreNoFlip, issue68DXNNoFlip)), bgcolor=colRed, text_color=color.white)

        table.cell(t, 0, 3, "DownEx gate avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 3, f_issue68DXFmt(f_issue68DXAvg(issue68DXSumGateAll, issue68DXNAll)), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 3, f_issue68DXFmt(f_issue68DXAvg(issue68DXSumGateFlip, issue68DXNFlip)), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 3, f_issue68DXFmt(f_issue68DXAvg(issue68DXSumGateNoFlip, issue68DXNNoFlip)), bgcolor=colRed, text_color=color.white)

        table.cell(t, 0, 4, "RAW / weighted deficit", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 1, 4, "ALL", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 4, "FLIP", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 4, "NO-FLIP", bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 5, "NoBreakLow 30%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 5, f_issue68DXFmt(issue68DXAvgNoBreakAll) + " / " + f_issue68DXFmt(issue68DXAvgDefNoBreakAll), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 5, f_issue68DXFmt(issue68DXAvgNoBreakFlip) + " / " + f_issue68DXFmt(issue68DXAvgDefNoBreakFlip), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 5, f_issue68DXFmt(issue68DXAvgNoBreakNoFlip) + " / " + f_issue68DXFmt(issue68DXAvgDefNoBreakNoFlip), bgcolor=colRed, text_color=color.white)

        table.cell(t, 0, 6, "NegSlopeDull 25%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 6, f_issue68DXFmt(issue68DXAvgNegSlopeAll) + " / " + f_issue68DXFmt(issue68DXAvgDefNegSlopeAll), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 6, f_issue68DXFmt(issue68DXAvgNegSlopeFlip) + " / " + f_issue68DXFmt(issue68DXAvgDefNegSlopeFlip), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 6, f_issue68DXFmt(issue68DXAvgNegSlopeNoFlip) + " / " + f_issue68DXFmt(issue68DXAvgDefNegSlopeNoFlip), bgcolor=colRed, text_color=color.white)

        table.cell(t, 0, 7, "PanicDull 20%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 7, f_issue68DXFmt(issue68DXAvgPanicAll) + " / " + f_issue68DXFmt(issue68DXAvgDefPanicAll), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 7, f_issue68DXFmt(issue68DXAvgPanicFlip) + " / " + f_issue68DXFmt(issue68DXAvgDefPanicFlip), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 7, f_issue68DXFmt(issue68DXAvgPanicNoFlip) + " / " + f_issue68DXFmt(issue68DXAvgDefPanicNoFlip), bgcolor=colRed, text_color=color.white)

        table.cell(t, 0, 8, "LowVol 15%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 8, f_issue68DXFmt(issue68DXAvgLowVolAll) + " / " + f_issue68DXFmt(issue68DXAvgDefLowVolAll), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 8, f_issue68DXFmt(issue68DXAvgLowVolFlip) + " / " + f_issue68DXFmt(issue68DXAvgDefLowVolFlip), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 8, f_issue68DXFmt(issue68DXAvgLowVolNoFlip) + " / " + f_issue68DXFmt(issue68DXAvgDefLowVolNoFlip), bgcolor=colRed, text_color=color.white)

        table.cell(t, 0, 9, "LowZoneStable 10%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 9, f_issue68DXFmt(issue68DXAvgLowZoneAll) + " / " + f_issue68DXFmt(issue68DXAvgDefLowZoneAll), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 9, f_issue68DXFmt(issue68DXAvgLowZoneFlip) + " / " + f_issue68DXFmt(issue68DXAvgDefLowZoneFlip), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 9, f_issue68DXFmt(issue68DXAvgLowZoneNoFlip) + " / " + f_issue68DXFmt(issue68DXAvgDefLowZoneNoFlip), bgcolor=colRed, text_color=color.white)

        table.cell(t, 0, 10, "Largest deficit", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 10, issue68DXDomAll, bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 10, issue68DXDomFlip, bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 10, issue68DXDomNoFlip, bgcolor=colRed, text_color=color.white)

        table.cell(t, 0, 11, "SCORE BANDS", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 1, 11, "ALL", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 11, "FLIP", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 11, "NO-FLIP", bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 12, "DownEx < 35", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 12, f_issue68DXPctFmt(issue68DXBelow35All, issue68DXNAll), bgcolor=colRed, text_color=color.white)
        table.cell(t, 2, 12, f_issue68DXPctFmt(issue68DXBelow35Flip, issue68DXNFlip), bgcolor=colRed, text_color=color.white)
        table.cell(t, 3, 12, f_issue68DXPctFmt(issue68DXBelow35NoFlip, issue68DXNNoFlip), bgcolor=colRed, text_color=color.white)

        table.cell(t, 0, 13, "35 <= DownEx < full", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 13, f_issue68DXPctFmt(issue68DXMidAll, issue68DXNAll), bgcolor=colYellow, text_color=color.black)
        table.cell(t, 2, 13, f_issue68DXPctFmt(issue68DXMidFlip, issue68DXNFlip), bgcolor=colYellow, text_color=color.black)
        table.cell(t, 3, 13, f_issue68DXPctFmt(issue68DXMidNoFlip, issue68DXNNoFlip), bgcolor=colYellow, text_color=color.black)

        table.cell(t, 0, 14, "DownEx >= full", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 14, f_issue68DXPctFmt(issue68DXFullAll, issue68DXNAll), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 14, f_issue68DXPctFmt(issue68DXFullFlip, issue68DXNFlip), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 14, f_issue68DXPctFmt(issue68DXFullNoFlip, issue68DXNNoFlip), bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 15, "Recon max error", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 15, f_issue68DXFmt(issue68DXMaxReconErr), bgcolor=issue68DXMaxReconErr < 0.01 ? colGreen : colRed, text_color=color.white)
        table.cell(t, 2, 15, "must ~0", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 15, "deficits -> score", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 16, "Flip runs / max", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 16, str.tostring(issue68DXDisplayRuns) + " / " + str.tostring(issue68DXFlipRunMax), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 16, "context only", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 16, "NO SELECTION", bgcolor=colRed, text_color=color.white)

        table.cell(t, 0, 17, "READ", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 17, "Which deficit splits DE/FR?", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 17, "NO TUNING", bgcolor=colRed, text_color=color.white)
        table.cell(t, 3, 17, "FROZEN C-2", bgcolor=colNeutral, text_color=color.white)
    else
        table.clear(t, 0, 0, 3, 17)
'''.strip()


def generate(source: Path) -> str:
    d1_text = phase_b.d1.generate(source)
    if d1_text.count(phase_b.D1_EXPORT_MARKER) != 1:
        raise RuntimeError("expected exactly one D1 parity export marker")
    core = d1_text.split(phase_b.D1_EXPORT_MARKER, 1)[0].rstrip()
    core = replace_once(core, phase_b.D1_INDICATOR_DECL, AUDIT_DECL)
    out = core + "\n\n" + BODY + "\n"
    for token in (
        "Downside-Exhaustion Component Audit",
        "NoBreakLow 30%",
        "NegSlopeDull 25%",
        "PanicDull 20%",
        "LowVol 15%",
        "LowZoneStable 10%",
        "Recon max error",
    ):
        if token not in out:
            raise RuntimeError(f"missing required audit token: {token}")
    if "strategy.entry" in out or "strategy.close" in out:
        raise RuntimeError("downside-exhaustion audit leaked strategy order logic")
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
