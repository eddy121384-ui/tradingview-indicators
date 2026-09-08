#!/usr/bin/env python3
"""Generate Issue #68 lost-fresh subset anatomy audit Pine."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_current_context_symmetric_s1_s4_audit_pine as s14
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 Lost-Fresh Anatomy", shorttitle="ChaseRisk #68 LostFresh", overlay=false, precision=3)'

BODY = r'''

// ============================================================================
// Issue #68 Lost-Fresh Subset Anatomy Audit.
// Frozen symmetric current-context intervention. No lookahead. No tuning. NO PNL.
// Compare Fresh retained vs Fresh lost; do not alter production C-2.
// ============================================================================

groupIssue68LF = "Issue #68｜Lost-Fresh Anatomy"
showIssue68LFTable = input.bool(true, "顯示 Lost-Fresh Anatomy 表", group=groupIssue68LF)

f_issue68LFAvg(float s, int n) =>
    n > 0 ? s / n : na

f_issue68LFPct(int n, int d) =>
    d > 0 ? str.tostring(100.0 * n / d, "#.##") + "%" : "NA"

f_issue68LFFmt(float x) =>
    na(x) ? "NA" : str.tostring(x, "#.##")

float issue68LFS1Runner = math.max(markupEff, math.max(reaccEff, math.max(distEff, math.max(markdownEff, redistEff))))
float issue68LFS4Runner = math.max(accEff, math.max(markupEff, math.max(reaccEff, math.max(markdownEff, redistEff))))
float issue68LFS1Margin = accEff - issue68LFS1Runner
float issue68LFS4Margin = distEff - issue68LFS4Runner
float issue68LFAbs20Bp = math.abs(close - close[20]) * 100.0
float issue68LFS1CapPressure = downsideExhaustionGate - issue68S1PCurrentBearGate
float issue68LFS4CapPressure = upsideExhaustionGate - issue68S14CurrentBullGate

var int issue68LFS1Age = 0
var int issue68LFS4Age = 0
if issue68S14FreshS1
    issue68LFS1Age += 1
else
    issue68LFS1Age := 0
if issue68S14FreshS4
    issue68LFS4Age += 1
else
    issue68LFS4Age := 0

// Four frozen subsets: S1 retained/lost, S4 retained/lost.
var int issue68LFS1KeepN = 0
var int issue68LFS1LostN = 0
var int issue68LFS4KeepN = 0
var int issue68LFS4LostN = 0

var float issue68LFS1KeepMarginSum = 0.0
var float issue68LFS1LostMarginSum = 0.0
var float issue68LFS4KeepMarginSum = 0.0
var float issue68LFS4LostMarginSum = 0.0
var float issue68LFS1KeepCurrentSum = 0.0
var float issue68LFS1LostCurrentSum = 0.0
var float issue68LFS4KeepCurrentSum = 0.0
var float issue68LFS4LostCurrentSum = 0.0
var float issue68LFS1KeepExGateSum = 0.0
var float issue68LFS1LostExGateSum = 0.0
var float issue68LFS4KeepExGateSum = 0.0
var float issue68LFS4LostExGateSum = 0.0
var float issue68LFS1KeepPressureSum = 0.0
var float issue68LFS1LostPressureSum = 0.0
var float issue68LFS4KeepPressureSum = 0.0
var float issue68LFS4LostPressureSum = 0.0
var float issue68LFS1KeepBgSum = 0.0
var float issue68LFS1LostBgSum = 0.0
var float issue68LFS4KeepBgSum = 0.0
var float issue68LFS4LostBgSum = 0.0
var float issue68LFS1KeepExSum = 0.0
var float issue68LFS1LostExSum = 0.0
var float issue68LFS4KeepExSum = 0.0
var float issue68LFS4LostExSum = 0.0
var float issue68LFS1KeepMoveSum = 0.0
var float issue68LFS1LostMoveSum = 0.0
var float issue68LFS4KeepMoveSum = 0.0
var float issue68LFS4LostMoveSum = 0.0
var float issue68LFS1KeepAgeSum = 0.0
var float issue68LFS1LostAgeSum = 0.0
var float issue68LFS4KeepAgeSum = 0.0
var float issue68LFS4LostAgeSum = 0.0

var int issue68LFS1KeepBindN = 0
var int issue68LFS1LostBindN = 0
var int issue68LFS4KeepBindN = 0
var int issue68LFS4LostBindN = 0
var int issue68LFS1KeepLE5N = 0
var int issue68LFS1LostLE5N = 0
var int issue68LFS4KeepLE5N = 0
var int issue68LFS4LostLE5N = 0
var int issue68LFS1KeepGT10N = 0
var int issue68LFS1LostGT10N = 0
var int issue68LFS4KeepGT10N = 0
var int issue68LFS4LostGT10N = 0

var float issue68LFS1KeepMaxMargin = na
var float issue68LFS1LostMaxMargin = na
var float issue68LFS4KeepMaxMargin = na
var float issue68LFS4LostMaxMargin = na

if issue68S14FreshS1Retained
    issue68LFS1KeepN += 1
    issue68LFS1KeepMarginSum += issue68LFS1Margin
    issue68LFS1KeepCurrentSum += issue68S1PCurrentBearGate
    issue68LFS1KeepExGateSum += downsideExhaustionGate
    issue68LFS1KeepPressureSum += issue68LFS1CapPressure
    issue68LFS1KeepBgSum += bearBg
    issue68LFS1KeepExSum += downsideExhaustion
    issue68LFS1KeepMoveSum += issue68LFAbs20Bp
    issue68LFS1KeepAgeSum += issue68LFS1Age
    issue68LFS1KeepBindN += issue68S14CapBindS1 ? 1 : 0
    issue68LFS1KeepLE5N += issue68LFS1Margin <= 5.0 ? 1 : 0
    issue68LFS1KeepGT10N += issue68LFS1Margin > 10.0 ? 1 : 0
    issue68LFS1KeepMaxMargin := na(issue68LFS1KeepMaxMargin) ? issue68LFS1Margin : math.max(issue68LFS1KeepMaxMargin, issue68LFS1Margin)

if issue68S14FreshS1Lost
    issue68LFS1LostN += 1
    issue68LFS1LostMarginSum += issue68LFS1Margin
    issue68LFS1LostCurrentSum += issue68S1PCurrentBearGate
    issue68LFS1LostExGateSum += downsideExhaustionGate
    issue68LFS1LostPressureSum += issue68LFS1CapPressure
    issue68LFS1LostBgSum += bearBg
    issue68LFS1LostExSum += downsideExhaustion
    issue68LFS1LostMoveSum += issue68LFAbs20Bp
    issue68LFS1LostAgeSum += issue68LFS1Age
    issue68LFS1LostBindN += issue68S14CapBindS1 ? 1 : 0
    issue68LFS1LostLE5N += issue68LFS1Margin <= 5.0 ? 1 : 0
    issue68LFS1LostGT10N += issue68LFS1Margin > 10.0 ? 1 : 0
    issue68LFS1LostMaxMargin := na(issue68LFS1LostMaxMargin) ? issue68LFS1Margin : math.max(issue68LFS1LostMaxMargin, issue68LFS1Margin)

if issue68S14FreshS4Retained
    issue68LFS4KeepN += 1
    issue68LFS4KeepMarginSum += issue68LFS4Margin
    issue68LFS4KeepCurrentSum += issue68S14CurrentBullGate
    issue68LFS4KeepExGateSum += upsideExhaustionGate
    issue68LFS4KeepPressureSum += issue68LFS4CapPressure
    issue68LFS4KeepBgSum += bullBg
    issue68LFS4KeepExSum += upsideExhaustion
    issue68LFS4KeepMoveSum += issue68LFAbs20Bp
    issue68LFS4KeepAgeSum += issue68LFS4Age
    issue68LFS4KeepBindN += issue68S14CapBindS4 ? 1 : 0
    issue68LFS4KeepLE5N += issue68LFS4Margin <= 5.0 ? 1 : 0
    issue68LFS4KeepGT10N += issue68LFS4Margin > 10.0 ? 1 : 0
    issue68LFS4KeepMaxMargin := na(issue68LFS4KeepMaxMargin) ? issue68LFS4Margin : math.max(issue68LFS4KeepMaxMargin, issue68LFS4Margin)

if issue68S14FreshS4Lost
    issue68LFS4LostN += 1
    issue68LFS4LostMarginSum += issue68LFS4Margin
    issue68LFS4LostCurrentSum += issue68S14CurrentBullGate
    issue68LFS4LostExGateSum += upsideExhaustionGate
    issue68LFS4LostPressureSum += issue68LFS4CapPressure
    issue68LFS4LostBgSum += bullBg
    issue68LFS4LostExSum += upsideExhaustion
    issue68LFS4LostMoveSum += issue68LFAbs20Bp
    issue68LFS4LostAgeSum += issue68LFS4Age
    issue68LFS4LostBindN += issue68S14CapBindS4 ? 1 : 0
    issue68LFS4LostLE5N += issue68LFS4Margin <= 5.0 ? 1 : 0
    issue68LFS4LostGT10N += issue68LFS4Margin > 10.0 ? 1 : 0
    issue68LFS4LostMaxMargin := na(issue68LFS4LostMaxMargin) ? issue68LFS4Margin : math.max(issue68LFS4LostMaxMargin, issue68LFS4Margin)

color issue68LFS1LostColor = issue68S14FreshS1LostBull ? colGreen : issue68S14FreshS1LostBear ? colRed : colNeutral
color issue68LFS4LostColor = issue68S14FreshS4LostBull ? colGreen : issue68S14FreshS4LostBear ? colRed : colNeutral
plot(issue68S14FreshS1Lost ? 2.0 : na, "Lost Fresh S1", color=issue68LFS1LostColor, style=plot.style_circles, linewidth=3)
plot(issue68S14FreshS4Lost ? 1.0 : na, "Lost Fresh S4", color=issue68LFS4LostColor, style=plot.style_circles, linewidth=3)

var table tLF = table.new(position.middle_right, 5, 17, border_width=1)
if barstate.islast
    if showIssue68LFTable
        table.cell(tLF, 0, 0, "LOST-FRESH ANATOMY", bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 1, 0, "S1 KEEP", bgcolor=colGreen, text_color=color.white)
        table.cell(tLF, 2, 0, "S1 LOST", bgcolor=colRed, text_color=color.white)
        table.cell(tLF, 3, 0, "S4 KEEP", bgcolor=colGreen, text_color=color.white)
        table.cell(tLF, 4, 0, "S4 LOST", bgcolor=colRed, text_color=color.white)

        table.cell(tLF, 0, 1, "N", bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 1, 1, str.tostring(issue68LFS1KeepN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 2, 1, str.tostring(issue68LFS1LostN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 3, 1, str.tostring(issue68LFS4KeepN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 4, 1, str.tostring(issue68LFS4LostN), bgcolor=colNeutral, text_color=color.white)

        table.cell(tLF, 0, 2, "Prod margin avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 1, 2, f_issue68LFFmt(f_issue68LFAvg(issue68LFS1KeepMarginSum, issue68LFS1KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 2, 2, f_issue68LFFmt(f_issue68LFAvg(issue68LFS1LostMarginSum, issue68LFS1LostN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 3, 2, f_issue68LFFmt(f_issue68LFAvg(issue68LFS4KeepMarginSum, issue68LFS4KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 4, 2, f_issue68LFFmt(f_issue68LFAvg(issue68LFS4LostMarginSum, issue68LFS4LostN)), bgcolor=colNeutral, text_color=color.white)

        table.cell(tLF, 0, 3, "Margin <=5", bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 1, 3, f_issue68LFPct(issue68LFS1KeepLE5N, issue68LFS1KeepN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 2, 3, f_issue68LFPct(issue68LFS1LostLE5N, issue68LFS1LostN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 3, 3, f_issue68LFPct(issue68LFS4KeepLE5N, issue68LFS4KeepN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 4, 3, f_issue68LFPct(issue68LFS4LostLE5N, issue68LFS4LostN), bgcolor=colNeutral, text_color=color.white)

        table.cell(tLF, 0, 4, "Margin >10", bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 1, 4, f_issue68LFPct(issue68LFS1KeepGT10N, issue68LFS1KeepN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 2, 4, f_issue68LFPct(issue68LFS1LostGT10N, issue68LFS1LostN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 3, 4, f_issue68LFPct(issue68LFS4KeepGT10N, issue68LFS4KeepN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 4, 4, f_issue68LFPct(issue68LFS4LostGT10N, issue68LFS4LostN), bgcolor=colNeutral, text_color=color.white)

        table.cell(tLF, 0, 5, "Current gate avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 1, 5, f_issue68LFFmt(f_issue68LFAvg(issue68LFS1KeepCurrentSum, issue68LFS1KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 2, 5, f_issue68LFFmt(f_issue68LFAvg(issue68LFS1LostCurrentSum, issue68LFS1LostN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 3, 5, f_issue68LFFmt(f_issue68LFAvg(issue68LFS4KeepCurrentSum, issue68LFS4KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 4, 5, f_issue68LFFmt(f_issue68LFAvg(issue68LFS4LostCurrentSum, issue68LFS4LostN)), bgcolor=colNeutral, text_color=color.white)

        table.cell(tLF, 0, 6, "Exhaust gate avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 1, 6, f_issue68LFFmt(f_issue68LFAvg(issue68LFS1KeepExGateSum, issue68LFS1KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 2, 6, f_issue68LFFmt(f_issue68LFAvg(issue68LFS1LostExGateSum, issue68LFS1LostN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 3, 6, f_issue68LFFmt(f_issue68LFAvg(issue68LFS4KeepExGateSum, issue68LFS4KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 4, 6, f_issue68LFFmt(f_issue68LFAvg(issue68LFS4LostExGateSum, issue68LFS4LostN)), bgcolor=colNeutral, text_color=color.white)

        table.cell(tLF, 0, 7, "Cap pressure avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 1, 7, f_issue68LFFmt(f_issue68LFAvg(issue68LFS1KeepPressureSum, issue68LFS1KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 2, 7, f_issue68LFFmt(f_issue68LFAvg(issue68LFS1LostPressureSum, issue68LFS1LostN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 3, 7, f_issue68LFFmt(f_issue68LFAvg(issue68LFS4KeepPressureSum, issue68LFS4KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 4, 7, f_issue68LFFmt(f_issue68LFAvg(issue68LFS4LostPressureSum, issue68LFS4LostN)), bgcolor=colNeutral, text_color=color.white)

        table.cell(tLF, 0, 8, "Bg score avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 1, 8, f_issue68LFFmt(f_issue68LFAvg(issue68LFS1KeepBgSum, issue68LFS1KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 2, 8, f_issue68LFFmt(f_issue68LFAvg(issue68LFS1LostBgSum, issue68LFS1LostN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 3, 8, f_issue68LFFmt(f_issue68LFAvg(issue68LFS4KeepBgSum, issue68LFS4KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 4, 8, f_issue68LFFmt(f_issue68LFAvg(issue68LFS4LostBgSum, issue68LFS4LostN)), bgcolor=colNeutral, text_color=color.white)

        table.cell(tLF, 0, 9, "Exhaust score avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 1, 9, f_issue68LFFmt(f_issue68LFAvg(issue68LFS1KeepExSum, issue68LFS1KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 2, 9, f_issue68LFFmt(f_issue68LFAvg(issue68LFS1LostExSum, issue68LFS1LostN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 3, 9, f_issue68LFFmt(f_issue68LFAvg(issue68LFS4KeepExSum, issue68LFS4KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 4, 9, f_issue68LFFmt(f_issue68LFAvg(issue68LFS4LostExSum, issue68LFS4LostN)), bgcolor=colNeutral, text_color=color.white)

        table.cell(tLF, 0, 10, "|20D move| bp avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 1, 10, f_issue68LFFmt(f_issue68LFAvg(issue68LFS1KeepMoveSum, issue68LFS1KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 2, 10, f_issue68LFFmt(f_issue68LFAvg(issue68LFS1LostMoveSum, issue68LFS1LostN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 3, 10, f_issue68LFFmt(f_issue68LFAvg(issue68LFS4KeepMoveSum, issue68LFS4KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 4, 10, f_issue68LFFmt(f_issue68LFAvg(issue68LFS4LostMoveSum, issue68LFS4LostN)), bgcolor=colNeutral, text_color=color.white)

        table.cell(tLF, 0, 11, "Fresh age avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 1, 11, f_issue68LFFmt(f_issue68LFAvg(issue68LFS1KeepAgeSum, issue68LFS1KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 2, 11, f_issue68LFFmt(f_issue68LFAvg(issue68LFS1LostAgeSum, issue68LFS1LostN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 3, 11, f_issue68LFFmt(f_issue68LFAvg(issue68LFS4KeepAgeSum, issue68LFS4KeepN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 4, 11, f_issue68LFFmt(f_issue68LFAvg(issue68LFS4LostAgeSum, issue68LFS4LostN)), bgcolor=colNeutral, text_color=color.white)

        table.cell(tLF, 0, 12, "Cap bind share", bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 1, 12, f_issue68LFPct(issue68LFS1KeepBindN, issue68LFS1KeepN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 2, 12, f_issue68LFPct(issue68LFS1LostBindN, issue68LFS1LostN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 3, 12, f_issue68LFPct(issue68LFS4KeepBindN, issue68LFS4KeepN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 4, 12, f_issue68LFPct(issue68LFS4LostBindN, issue68LFS4LostN), bgcolor=colNeutral, text_color=color.white)

        table.cell(tLF, 0, 13, "Lost dest B/N/R", bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 1, 13, "—", bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 2, 13, str.tostring(issue68S14FreshS1LostBullN) + "/" + str.tostring(issue68S14FreshS1LostNeutralN) + "/" + str.tostring(issue68S14FreshS1LostBearN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 3, 13, "—", bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 4, 13, str.tostring(issue68S14FreshS4LostBullN) + "/" + str.tostring(issue68S14FreshS4LostNeutralN) + "/" + str.tostring(issue68S14FreshS4LostBearN), bgcolor=colNeutral, text_color=color.white)

        table.cell(tLF, 0, 14, "Max prod margin", bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 1, 14, f_issue68LFFmt(issue68LFS1KeepMaxMargin), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 2, 14, f_issue68LFFmt(issue68LFS1LostMaxMargin), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 3, 14, f_issue68LFFmt(issue68LFS4KeepMaxMargin), bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 4, 14, f_issue68LFFmt(issue68LFS4LostMaxMargin), bgcolor=colNeutral, text_color=color.white)

        table.cell(tLF, 0, 15, "READ", bgcolor=colGreen, text_color=color.white)
        table.cell(tLF, 1, 15, "Retained anchor", bgcolor=colGreen, text_color=color.white)
        table.cell(tLF, 2, 15, "Lost anatomy?", bgcolor=colRed, text_color=color.white)
        table.cell(tLF, 3, 15, "Retained mirror", bgcolor=colGreen, text_color=color.white)
        table.cell(tLF, 4, 15, "Lost anatomy?", bgcolor=colRed, text_color=color.white)

        table.cell(tLF, 0, 16, "MODE", bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 1, 16, "DISCOVERY", bgcolor=colNeutral, text_color=color.white)
        table.cell(tLF, 2, 16, "NO TUNING", bgcolor=colRed, text_color=color.white)
        table.cell(tLF, 3, 16, "EXACT MIRROR", bgcolor=colGreen, text_color=color.white)
        table.cell(tLF, 4, 16, "FROZEN C-2", bgcolor=colNeutral, text_color=color.white)
    else
        table.clear(tLF, 0, 0, 4, 16)
'''


def generate(source: Path) -> str:
    out = s14.generate(source)
    out = replace_once(out, s14.AUDIT_DECL, AUDIT_DECL)
    out = replace_once(
        out,
        'showIssue68S14Table = input.bool(true, "顯示 Symmetric S1/S4 表", group=groupIssue68S14)',
        'showIssue68S14Table = input.bool(false, "顯示 Symmetric S1/S4 表", group=groupIssue68S14)',
    )
    out = out.rstrip() + BODY + "\n"
    required = [
        "LOST-FRESH ANATOMY",
        "Prod margin avg",
        "Cap pressure avg",
        "Fresh age avg",
        "Lost dest B/N/R",
        "NO TUNING",
        "EXACT MIRROR",
    ]
    missing = [x for x in required if x not in out]
    if missing:
        raise RuntimeError(f"lost-fresh audit contract missing: {missing}")
    if "strategy.entry" in out or "strategy.close" in out:
        raise RuntimeError("lost-fresh audit leaked strategy order logic")
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
