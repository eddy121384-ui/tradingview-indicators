#!/usr/bin/env python3
"""Generate Issue #68 high-confidence lost Fresh semantic audit Pine."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_current_context_lost_fresh_subset_audit_pine as lf
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 HC Lost Semantics", shorttitle="ChaseRisk #68 HCLost", overlay=false, precision=3)'

BODY = r'''

// ============================================================================
// Issue #68 High-Confidence Lost Fresh Semantic Audit.
// Population = preregistered Fresh S1/S4 with production winner margin > 10.
// Compare retained vs lost under the frozen exact symmetric CTX intervention.
// No lookahead. No tuning. NO PNL. Production C-2 remains frozen.
// ============================================================================

groupIssue68HC = "Issue #68｜HC Lost Semantics"
showIssue68HCTable = input.bool(true, "顯示 HC Lost Semantics 表", group=groupIssue68HC)

f_issue68HCAvg(float s, int n) =>
    n > 0 ? s / n : na

f_issue68HCPct(int n, int d) =>
    d > 0 ? str.tostring(100.0 * n / d, "#.##") + "%" : "NA"

f_issue68HCFmt(float x) =>
    na(x) ? "NA" : str.tostring(x, "#.##")

bool issue68HCS1Keep = issue68S14FreshS1Retained and issue68LFS1Margin > 10.0
bool issue68HCS1Lost = issue68S14FreshS1Lost and issue68LFS1Margin > 10.0
bool issue68HCS4Keep = issue68S14FreshS4Retained and issue68LFS4Margin > 10.0
bool issue68HCS4Lost = issue68S14FreshS4Lost and issue68LFS4Margin > 10.0

float issue68HCS1TraceAdv = bearMaturityTrace - bearBg
float issue68HCS4TraceAdv = bullMaturityTrace - bullBg
float issue68HCS1HistGateGap = bearBackgroundForAccGate - issue68S1PCurrentBearGate
float issue68HCS4HistGateGap = bullBackgroundForDistGate - issue68S14CurrentBullGate

var int issue68HCS1KeepN = 0
var int issue68HCS1LostN = 0
var int issue68HCS4KeepN = 0
var int issue68HCS4LostN = 0

var float issue68HCS1KeepMarginSum = 0.0
var float issue68HCS1LostMarginSum = 0.0
var float issue68HCS4KeepMarginSum = 0.0
var float issue68HCS4LostMarginSum = 0.0
var float issue68HCS1KeepMarginMax = na
var float issue68HCS1LostMarginMax = na
var float issue68HCS4KeepMarginMax = na
var float issue68HCS4LostMarginMax = na

var float issue68HCS1KeepCurrentGateSum = 0.0
var float issue68HCS1LostCurrentGateSum = 0.0
var float issue68HCS4KeepCurrentGateSum = 0.0
var float issue68HCS4LostCurrentGateSum = 0.0
var float issue68HCS1KeepHistGateSum = 0.0
var float issue68HCS1LostHistGateSum = 0.0
var float issue68HCS4KeepHistGateSum = 0.0
var float issue68HCS4LostHistGateSum = 0.0
var float issue68HCS1KeepHistGapSum = 0.0
var float issue68HCS1LostHistGapSum = 0.0
var float issue68HCS4KeepHistGapSum = 0.0
var float issue68HCS4LostHistGapSum = 0.0

var float issue68HCS1KeepBgSum = 0.0
var float issue68HCS1LostBgSum = 0.0
var float issue68HCS4KeepBgSum = 0.0
var float issue68HCS4LostBgSum = 0.0
var float issue68HCS1KeepTraceSum = 0.0
var float issue68HCS1LostTraceSum = 0.0
var float issue68HCS4KeepTraceSum = 0.0
var float issue68HCS4LostTraceSum = 0.0
var float issue68HCS1KeepTraceAdvSum = 0.0
var float issue68HCS1LostTraceAdvSum = 0.0
var float issue68HCS4KeepTraceAdvSum = 0.0
var float issue68HCS4LostTraceAdvSum = 0.0
var int issue68HCS1KeepTraceLeadN = 0
var int issue68HCS1LostTraceLeadN = 0
var int issue68HCS4KeepTraceLeadN = 0
var int issue68HCS4LostTraceLeadN = 0

var float issue68HCS1KeepExGateSum = 0.0
var float issue68HCS1LostExGateSum = 0.0
var float issue68HCS4KeepExGateSum = 0.0
var float issue68HCS4LostExGateSum = 0.0
var float issue68HCS1KeepPressureSum = 0.0
var float issue68HCS1LostPressureSum = 0.0
var float issue68HCS4KeepPressureSum = 0.0
var float issue68HCS4LostPressureSum = 0.0

var float issue68HCS1KeepRawSum = 0.0
var float issue68HCS1LostRawSum = 0.0
var float issue68HCS4KeepRawSum = 0.0
var float issue68HCS4LostRawSum = 0.0
var float issue68HCS1KeepProdEffSum = 0.0
var float issue68HCS1LostProdEffSum = 0.0
var float issue68HCS4KeepProdEffSum = 0.0
var float issue68HCS4LostProdEffSum = 0.0
var float issue68HCS1KeepCtxEffSum = 0.0
var float issue68HCS1LostCtxEffSum = 0.0
var float issue68HCS4KeepCtxEffSum = 0.0
var float issue68HCS4LostCtxEffSum = 0.0

var float issue68HCS1KeepAgeSum = 0.0
var float issue68HCS1LostAgeSum = 0.0
var float issue68HCS4KeepAgeSum = 0.0
var float issue68HCS4LostAgeSum = 0.0
var float issue68HCS1KeepMoveSum = 0.0
var float issue68HCS1LostMoveSum = 0.0
var float issue68HCS4KeepMoveSum = 0.0
var float issue68HCS4LostMoveSum = 0.0

var int issue68HCS1LostBullN = 0
var int issue68HCS1LostNeutralN = 0
var int issue68HCS1LostBearN = 0
var int issue68HCS4LostBullN = 0
var int issue68HCS4LostNeutralN = 0
var int issue68HCS4LostBearN = 0

if issue68HCS1Keep
    issue68HCS1KeepN += 1
    issue68HCS1KeepMarginSum += issue68LFS1Margin
    issue68HCS1KeepMarginMax := na(issue68HCS1KeepMarginMax) ? issue68LFS1Margin : math.max(issue68HCS1KeepMarginMax, issue68LFS1Margin)
    issue68HCS1KeepCurrentGateSum += issue68S1PCurrentBearGate
    issue68HCS1KeepHistGateSum += bearBackgroundForAccGate
    issue68HCS1KeepHistGapSum += issue68HCS1HistGateGap
    issue68HCS1KeepBgSum += bearBg
    issue68HCS1KeepTraceSum += bearMaturityTrace
    issue68HCS1KeepTraceAdvSum += issue68HCS1TraceAdv
    issue68HCS1KeepTraceLeadN += bearMaturityTrace > bearBg ? 1 : 0
    issue68HCS1KeepExGateSum += downsideExhaustionGate
    issue68HCS1KeepPressureSum += issue68LFS1CapPressure
    issue68HCS1KeepRawSum += accRaw
    issue68HCS1KeepProdEffSum += accEff
    issue68HCS1KeepCtxEffSum += issue68S1PCtxAccEff
    issue68HCS1KeepAgeSum += issue68LFS1Age
    issue68HCS1KeepMoveSum += issue68LFAbs20Bp

if issue68HCS1Lost
    issue68HCS1LostN += 1
    issue68HCS1LostMarginSum += issue68LFS1Margin
    issue68HCS1LostMarginMax := na(issue68HCS1LostMarginMax) ? issue68LFS1Margin : math.max(issue68HCS1LostMarginMax, issue68LFS1Margin)
    issue68HCS1LostCurrentGateSum += issue68S1PCurrentBearGate
    issue68HCS1LostHistGateSum += bearBackgroundForAccGate
    issue68HCS1LostHistGapSum += issue68HCS1HistGateGap
    issue68HCS1LostBgSum += bearBg
    issue68HCS1LostTraceSum += bearMaturityTrace
    issue68HCS1LostTraceAdvSum += issue68HCS1TraceAdv
    issue68HCS1LostTraceLeadN += bearMaturityTrace > bearBg ? 1 : 0
    issue68HCS1LostExGateSum += downsideExhaustionGate
    issue68HCS1LostPressureSum += issue68LFS1CapPressure
    issue68HCS1LostRawSum += accRaw
    issue68HCS1LostProdEffSum += accEff
    issue68HCS1LostCtxEffSum += issue68S1PCtxAccEff
    issue68HCS1LostAgeSum += issue68LFS1Age
    issue68HCS1LostMoveSum += issue68LFAbs20Bp
    issue68HCS1LostBullN += (issue68S14Top == 2 or issue68S14Top == 3) ? 1 : 0
    issue68HCS1LostNeutralN += issue68S14Top == 4 ? 1 : 0
    issue68HCS1LostBearN += (issue68S14Top == 5 or issue68S14Top == 6) ? 1 : 0

if issue68HCS4Keep
    issue68HCS4KeepN += 1
    issue68HCS4KeepMarginSum += issue68LFS4Margin
    issue68HCS4KeepMarginMax := na(issue68HCS4KeepMarginMax) ? issue68LFS4Margin : math.max(issue68HCS4KeepMarginMax, issue68LFS4Margin)
    issue68HCS4KeepCurrentGateSum += issue68S14CurrentBullGate
    issue68HCS4KeepHistGateSum += bullBackgroundForDistGate
    issue68HCS4KeepHistGapSum += issue68HCS4HistGateGap
    issue68HCS4KeepBgSum += bullBg
    issue68HCS4KeepTraceSum += bullMaturityTrace
    issue68HCS4KeepTraceAdvSum += issue68HCS4TraceAdv
    issue68HCS4KeepTraceLeadN += bullMaturityTrace > bullBg ? 1 : 0
    issue68HCS4KeepExGateSum += upsideExhaustionGate
    issue68HCS4KeepPressureSum += issue68LFS4CapPressure
    issue68HCS4KeepRawSum += distRaw
    issue68HCS4KeepProdEffSum += distEff
    issue68HCS4KeepCtxEffSum += issue68S14CtxDistEff
    issue68HCS4KeepAgeSum += issue68LFS4Age
    issue68HCS4KeepMoveSum += issue68LFAbs20Bp

if issue68HCS4Lost
    issue68HCS4LostN += 1
    issue68HCS4LostMarginSum += issue68LFS4Margin
    issue68HCS4LostMarginMax := na(issue68HCS4LostMarginMax) ? issue68LFS4Margin : math.max(issue68HCS4LostMarginMax, issue68LFS4Margin)
    issue68HCS4LostCurrentGateSum += issue68S14CurrentBullGate
    issue68HCS4LostHistGateSum += bullBackgroundForDistGate
    issue68HCS4LostHistGapSum += issue68HCS4HistGateGap
    issue68HCS4LostBgSum += bullBg
    issue68HCS4LostTraceSum += bullMaturityTrace
    issue68HCS4LostTraceAdvSum += issue68HCS4TraceAdv
    issue68HCS4LostTraceLeadN += bullMaturityTrace > bullBg ? 1 : 0
    issue68HCS4LostExGateSum += upsideExhaustionGate
    issue68HCS4LostPressureSum += issue68LFS4CapPressure
    issue68HCS4LostRawSum += distRaw
    issue68HCS4LostProdEffSum += distEff
    issue68HCS4LostCtxEffSum += issue68S14CtxDistEff
    issue68HCS4LostAgeSum += issue68LFS4Age
    issue68HCS4LostMoveSum += issue68LFAbs20Bp
    issue68HCS4LostBullN += (issue68S14Top == 2 or issue68S14Top == 3) ? 1 : 0
    issue68HCS4LostNeutralN += issue68S14Top == 1 ? 1 : 0
    issue68HCS4LostBearN += (issue68S14Top == 5 or issue68S14Top == 6) ? 1 : 0

var table tHC = table.new(position.middle_right, 5, 19, border_width=1)
if barstate.islast
    if showIssue68HCTable
        table.cell(tHC, 0, 0, "HC LOST SEMANTICS", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 1, 0, "S1 HC KEEP", bgcolor=colGreen, text_color=color.white)
        table.cell(tHC, 2, 0, "S1 HC LOST", bgcolor=colRed, text_color=color.white)
        table.cell(tHC, 3, 0, "S4 HC KEEP", bgcolor=colGreen, text_color=color.white)
        table.cell(tHC, 4, 0, "S4 HC LOST", bgcolor=colRed, text_color=color.white)

        table.cell(tHC, 0, 1, "N", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 1, 1, str.tostring(issue68HCS1KeepN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 2, 1, str.tostring(issue68HCS1LostN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 3, 1, str.tostring(issue68HCS4KeepN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 4, 1, str.tostring(issue68HCS4LostN), bgcolor=colNeutral, text_color=color.white)

        table.cell(tHC, 0, 2, "Prod margin avg / max", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 1, 2, f_issue68HCFmt(f_issue68HCAvg(issue68HCS1KeepMarginSum, issue68HCS1KeepN)) + " / " + f_issue68HCFmt(issue68HCS1KeepMarginMax), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 2, 2, f_issue68HCFmt(f_issue68HCAvg(issue68HCS1LostMarginSum, issue68HCS1LostN)) + " / " + f_issue68HCFmt(issue68HCS1LostMarginMax), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 3, 2, f_issue68HCFmt(f_issue68HCAvg(issue68HCS4KeepMarginSum, issue68HCS4KeepN)) + " / " + f_issue68HCFmt(issue68HCS4KeepMarginMax), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 4, 2, f_issue68HCFmt(f_issue68HCAvg(issue68HCS4LostMarginSum, issue68HCS4LostN)) + " / " + f_issue68HCFmt(issue68HCS4LostMarginMax), bgcolor=colNeutral, text_color=color.white)

        table.cell(tHC, 0, 3, "Current gate avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 1, 3, f_issue68HCFmt(f_issue68HCAvg(issue68HCS1KeepCurrentGateSum, issue68HCS1KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 2, 3, f_issue68HCFmt(f_issue68HCAvg(issue68HCS1LostCurrentGateSum, issue68HCS1LostN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 3, 3, f_issue68HCFmt(f_issue68HCAvg(issue68HCS4KeepCurrentGateSum, issue68HCS4KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 4, 3, f_issue68HCFmt(f_issue68HCAvg(issue68HCS4LostCurrentGateSum, issue68HCS4LostN)), bgcolor=colNeutral, text_color=color.white)

        table.cell(tHC, 0, 4, "Historical bg gate avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 1, 4, f_issue68HCFmt(f_issue68HCAvg(issue68HCS1KeepHistGateSum, issue68HCS1KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 2, 4, f_issue68HCFmt(f_issue68HCAvg(issue68HCS1LostHistGateSum, issue68HCS1LostN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 3, 4, f_issue68HCFmt(f_issue68HCAvg(issue68HCS4KeepHistGateSum, issue68HCS4KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 4, 4, f_issue68HCFmt(f_issue68HCAvg(issue68HCS4LostHistGateSum, issue68HCS4LostN)), bgcolor=colNeutral, text_color=color.white)

        table.cell(tHC, 0, 5, "Hist-current gate gap", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 1, 5, f_issue68HCFmt(f_issue68HCAvg(issue68HCS1KeepHistGapSum, issue68HCS1KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 2, 5, f_issue68HCFmt(f_issue68HCAvg(issue68HCS1LostHistGapSum, issue68HCS1LostN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 3, 5, f_issue68HCFmt(f_issue68HCAvg(issue68HCS4KeepHistGapSum, issue68HCS4KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 4, 5, f_issue68HCFmt(f_issue68HCAvg(issue68HCS4LostHistGapSum, issue68HCS4LostN)), bgcolor=colNeutral, text_color=color.white)

        table.cell(tHC, 0, 6, "Current bg score avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 1, 6, f_issue68HCFmt(f_issue68HCAvg(issue68HCS1KeepBgSum, issue68HCS1KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 2, 6, f_issue68HCFmt(f_issue68HCAvg(issue68HCS1LostBgSum, issue68HCS1LostN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 3, 6, f_issue68HCFmt(f_issue68HCAvg(issue68HCS4KeepBgSum, issue68HCS4KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 4, 6, f_issue68HCFmt(f_issue68HCAvg(issue68HCS4LostBgSum, issue68HCS4LostN)), bgcolor=colNeutral, text_color=color.white)

        table.cell(tHC, 0, 7, "Maturity trace avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 1, 7, f_issue68HCFmt(f_issue68HCAvg(issue68HCS1KeepTraceSum, issue68HCS1KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 2, 7, f_issue68HCFmt(f_issue68HCAvg(issue68HCS1LostTraceSum, issue68HCS1LostN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 3, 7, f_issue68HCFmt(f_issue68HCAvg(issue68HCS4KeepTraceSum, issue68HCS4KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 4, 7, f_issue68HCFmt(f_issue68HCAvg(issue68HCS4LostTraceSum, issue68HCS4LostN)), bgcolor=colNeutral, text_color=color.white)

        table.cell(tHC, 0, 8, "Trace advantage avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 1, 8, f_issue68HCFmt(f_issue68HCAvg(issue68HCS1KeepTraceAdvSum, issue68HCS1KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 2, 8, f_issue68HCFmt(f_issue68HCAvg(issue68HCS1LostTraceAdvSum, issue68HCS1LostN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 3, 8, f_issue68HCFmt(f_issue68HCAvg(issue68HCS4KeepTraceAdvSum, issue68HCS4KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 4, 8, f_issue68HCFmt(f_issue68HCAvg(issue68HCS4LostTraceAdvSum, issue68HCS4LostN)), bgcolor=colNeutral, text_color=color.white)

        table.cell(tHC, 0, 9, "Trace > current share", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 1, 9, f_issue68HCPct(issue68HCS1KeepTraceLeadN, issue68HCS1KeepN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 2, 9, f_issue68HCPct(issue68HCS1LostTraceLeadN, issue68HCS1LostN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 3, 9, f_issue68HCPct(issue68HCS4KeepTraceLeadN, issue68HCS4KeepN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 4, 9, f_issue68HCPct(issue68HCS4LostTraceLeadN, issue68HCS4LostN), bgcolor=colNeutral, text_color=color.white)

        table.cell(tHC, 0, 10, "Exhaust gate avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 1, 10, f_issue68HCFmt(f_issue68HCAvg(issue68HCS1KeepExGateSum, issue68HCS1KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 2, 10, f_issue68HCFmt(f_issue68HCAvg(issue68HCS1LostExGateSum, issue68HCS1LostN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 3, 10, f_issue68HCFmt(f_issue68HCAvg(issue68HCS4KeepExGateSum, issue68HCS4KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 4, 10, f_issue68HCFmt(f_issue68HCAvg(issue68HCS4LostExGateSum, issue68HCS4LostN)), bgcolor=colNeutral, text_color=color.white)

        table.cell(tHC, 0, 11, "Cap pressure avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 1, 11, f_issue68HCFmt(f_issue68HCAvg(issue68HCS1KeepPressureSum, issue68HCS1KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 2, 11, f_issue68HCFmt(f_issue68HCAvg(issue68HCS1LostPressureSum, issue68HCS1LostN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 3, 11, f_issue68HCFmt(f_issue68HCAvg(issue68HCS4KeepPressureSum, issue68HCS4KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 4, 11, f_issue68HCFmt(f_issue68HCAvg(issue68HCS4LostPressureSum, issue68HCS4LostN)), bgcolor=colNeutral, text_color=color.white)

        table.cell(tHC, 0, 12, "Raw stage avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 1, 12, f_issue68HCFmt(f_issue68HCAvg(issue68HCS1KeepRawSum, issue68HCS1KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 2, 12, f_issue68HCFmt(f_issue68HCAvg(issue68HCS1LostRawSum, issue68HCS1LostN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 3, 12, f_issue68HCFmt(f_issue68HCAvg(issue68HCS4KeepRawSum, issue68HCS4KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 4, 12, f_issue68HCFmt(f_issue68HCAvg(issue68HCS4LostRawSum, issue68HCS4LostN)), bgcolor=colNeutral, text_color=color.white)

        table.cell(tHC, 0, 13, "Prod eff / CTX eff", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 1, 13, f_issue68HCFmt(f_issue68HCAvg(issue68HCS1KeepProdEffSum, issue68HCS1KeepN)) + " / " + f_issue68HCFmt(f_issue68HCAvg(issue68HCS1KeepCtxEffSum, issue68HCS1KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 2, 13, f_issue68HCFmt(f_issue68HCAvg(issue68HCS1LostProdEffSum, issue68HCS1LostN)) + " / " + f_issue68HCFmt(f_issue68HCAvg(issue68HCS1LostCtxEffSum, issue68HCS1LostN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 3, 13, f_issue68HCFmt(f_issue68HCAvg(issue68HCS4KeepProdEffSum, issue68HCS4KeepN)) + " / " + f_issue68HCFmt(f_issue68HCAvg(issue68HCS4KeepCtxEffSum, issue68HCS4KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 4, 13, f_issue68HCFmt(f_issue68HCAvg(issue68HCS4LostProdEffSum, issue68HCS4LostN)) + " / " + f_issue68HCFmt(f_issue68HCAvg(issue68HCS4LostCtxEffSum, issue68HCS4LostN)), bgcolor=colNeutral, text_color=color.white)

        table.cell(tHC, 0, 14, "Fresh age avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 1, 14, f_issue68HCFmt(f_issue68HCAvg(issue68HCS1KeepAgeSum, issue68HCS1KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 2, 14, f_issue68HCFmt(f_issue68HCAvg(issue68HCS1LostAgeSum, issue68HCS1LostN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 3, 14, f_issue68HCFmt(f_issue68HCAvg(issue68HCS4KeepAgeSum, issue68HCS4KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 4, 14, f_issue68HCFmt(f_issue68HCAvg(issue68HCS4LostAgeSum, issue68HCS4LostN)), bgcolor=colNeutral, text_color=color.white)

        table.cell(tHC, 0, 15, "|20D move| bp avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 1, 15, f_issue68HCFmt(f_issue68HCAvg(issue68HCS1KeepMoveSum, issue68HCS1KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 2, 15, f_issue68HCFmt(f_issue68HCAvg(issue68HCS1LostMoveSum, issue68HCS1LostN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 3, 15, f_issue68HCFmt(f_issue68HCAvg(issue68HCS4KeepMoveSum, issue68HCS4KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 4, 15, f_issue68HCFmt(f_issue68HCAvg(issue68HCS4LostMoveSum, issue68HCS4LostN)), bgcolor=colNeutral, text_color=color.white)

        table.cell(tHC, 0, 16, "HC LOST dest B/N/R", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 1, 16, "—", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 2, 16, str.tostring(issue68HCS1LostBullN) + "/" + str.tostring(issue68HCS1LostNeutralN) + "/" + str.tostring(issue68HCS1LostBearN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 3, 16, "—", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 4, 16, str.tostring(issue68HCS4LostBullN) + "/" + str.tostring(issue68HCS4LostNeutralN) + "/" + str.tostring(issue68HCS4LostBearN), bgcolor=colNeutral, text_color=color.white)

        table.cell(tHC, 0, 17, "READ", bgcolor=colGreen, text_color=color.white)
        table.cell(tHC, 1, 17, "HC retained anchor", bgcolor=colGreen, text_color=color.white)
        table.cell(tHC, 2, 17, "stale confidence?", bgcolor=colRed, text_color=color.white)
        table.cell(tHC, 3, 17, "HC retained mirror", bgcolor=colGreen, text_color=color.white)
        table.cell(tHC, 4, 17, "stale confidence?", bgcolor=colRed, text_color=color.white)

        table.cell(tHC, 0, 18, "MODE", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 1, 18, "DISCOVERY", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHC, 2, 18, "NO TUNING", bgcolor=colRed, text_color=color.white)
        table.cell(tHC, 3, 18, "EXACT MIRROR", bgcolor=colGreen, text_color=color.white)
        table.cell(tHC, 4, 18, "FROZEN C-2", bgcolor=colNeutral, text_color=color.white)
    else
        table.clear(tHC, 0, 0, 4, 18)
'''


def generate(source: Path) -> str:
    out = lf.generate(source)
    out = replace_once(out, lf.AUDIT_DECL, AUDIT_DECL)
    out = replace_once(
        out,
        'showIssue68LFTable = input.bool(true, "顯示 Lost-Fresh Anatomy 表", group=groupIssue68LF)',
        'showIssue68LFTable = input.bool(false, "顯示 Lost-Fresh Anatomy 表", group=groupIssue68LF)',
    )
    out = out.rstrip() + BODY + "\n"
    required = [
        "HC LOST SEMANTICS",
        "Trace advantage avg",
        "Trace > current share",
        "Historical bg gate avg",
        "Prod eff / CTX eff",
        "HC LOST dest B/N/R",
        "NO TUNING",
        "EXACT MIRROR",
    ]
    missing = [x for x in required if x not in out]
    if missing:
        raise RuntimeError(f"high-confidence lost audit contract missing: {missing}")
    if "strategy.entry" in out or "strategy.close" in out:
        raise RuntimeError("high-confidence lost audit leaked strategy order logic")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=HERE / SOURCE_RELATIVE)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    text = generate(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
