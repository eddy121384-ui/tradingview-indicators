#!/usr/bin/env python3
"""Generate Issue #68 FR10Y vs DE10Y RAW margin-distribution audit Pine."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_phase_b_lifecycle_pine as phase_b
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 RAW Margin Dist", shorttitle="ChaseRisk #68 RAWDist", overlay=false, precision=2)'

BODY = r'''

// ============================================================================
// Issue #68 FR10Y vs DE10Y RAW Margin Distribution Audit.
// Shared window: 2022-01-03 -> 2023-12-29, expected Bull yield regime.
// DISCOVERY ONLY. NO PNL. NO TUNING. FROZEN C-2.
// ============================================================================

groupIssue68RawDist = "Issue #68｜RAW Margin Distribution"
showIssue68RawDistTable = input.bool(true, "顯示 RAW Margin Distribution 表", group=groupIssue68RawDist)

issue68RawDistReady = bar_index >= rankLen - 1
int issue68RawDistStart = timestamp(2022, 1, 3, 0, 0)
int issue68RawDistEnd = timestamp(2023, 12, 29, 23, 59)
bool issue68RawDistInWindow = issue68RawDistReady and time >= issue68RawDistStart and time <= issue68RawDistEnd
bool issue68RawDistValid = issue68RawDistInWindow and not na(accRaw) and not na(markupRaw)

f_issue68RawDistAvg(float s, int n) => n > 0 ? s / n : na
f_issue68RawDistPct(int n, int d) => d > 0 ? 100.0 * n / d : na

float issue68RawMargin = markupRaw - accRaw
int issue68RawLeader = issue68RawMargin > 0.0 ? 1 : -1

var int issue68Bars = 0
var int issue68S2LeadBars = 0
var int issue68S1LeadBars = 0

var int issue68BinM20 = 0
var int issue68BinM20M10 = 0
var int issue68BinM10Zero = 0
var int issue68BinZeroP10 = 0
var int issue68BinP10P20 = 0
var int issue68BinP20 = 0

var float issue68SumMargin = 0.0
var float issue68SumAbsMargin = 0.0
var float issue68SumPosMargin = 0.0
var float issue68SumNegMargin = 0.0
var float issue68SumMarkupOnS2Lead = 0.0
var float issue68SumAccOnS2Lead = 0.0
var float issue68SumMarkupOnS1Lead = 0.0
var float issue68SumAccOnS1Lead = 0.0

var int issue68RunLeader = 0
var int issue68RunLen = 0
var int issue68MaxS2Run = 0
var int issue68MaxS1Run = 0
var int issue68DoneS2Runs = 0
var int issue68DoneS1Runs = 0
var int issue68DoneS2RunBars = 0
var int issue68DoneS1RunBars = 0
var int issue68LeaderFlips = 0

if issue68RawDistValid
    issue68Bars += 1
    issue68SumMargin += issue68RawMargin
    issue68SumAbsMargin += math.abs(issue68RawMargin)

    if issue68RawLeader == 1
        issue68S2LeadBars += 1
        issue68SumPosMargin += issue68RawMargin
        issue68SumMarkupOnS2Lead += markupRaw
        issue68SumAccOnS2Lead += accRaw
    else
        issue68S1LeadBars += 1
        issue68SumNegMargin += issue68RawMargin
        issue68SumMarkupOnS1Lead += markupRaw
        issue68SumAccOnS1Lead += accRaw

    if issue68RawMargin <= -20.0
        issue68BinM20 += 1
    else if issue68RawMargin <= -10.0
        issue68BinM20M10 += 1
    else if issue68RawMargin <= 0.0
        issue68BinM10Zero += 1
    else if issue68RawMargin < 10.0
        issue68BinZeroP10 += 1
    else if issue68RawMargin < 20.0
        issue68BinP10P20 += 1
    else
        issue68BinP20 += 1

    if issue68RunLeader == 0
        issue68RunLeader := issue68RawLeader
        issue68RunLen := 1
    else if issue68RawLeader == issue68RunLeader
        issue68RunLen += 1
    else
        if issue68RunLeader == 1
            issue68DoneS2Runs += 1
            issue68DoneS2RunBars += issue68RunLen
        else
            issue68DoneS1Runs += 1
            issue68DoneS1RunBars += issue68RunLen
        issue68LeaderFlips += 1
        issue68RunLeader := issue68RawLeader
        issue68RunLen := 1

    if issue68RunLeader == 1
        issue68MaxS2Run := math.max(issue68MaxS2Run, issue68RunLen)
    else
        issue68MaxS1Run := math.max(issue68MaxS1Run, issue68RunLen)

int issue68DisplayS2Runs = issue68DoneS2Runs + (issue68RunLeader == 1 and issue68RunLen > 0 ? 1 : 0)
int issue68DisplayS1Runs = issue68DoneS1Runs + (issue68RunLeader == -1 and issue68RunLen > 0 ? 1 : 0)
int issue68DisplayS2RunBars = issue68DoneS2RunBars + (issue68RunLeader == 1 ? issue68RunLen : 0)
int issue68DisplayS1RunBars = issue68DoneS1RunBars + (issue68RunLeader == -1 ? issue68RunLen : 0)

float issue68S2LeadPct = f_issue68RawDistPct(issue68S2LeadBars, issue68Bars)
float issue68S1LeadPct = f_issue68RawDistPct(issue68S1LeadBars, issue68Bars)
float issue68AvgMargin = f_issue68RawDistAvg(issue68SumMargin, issue68Bars)
float issue68AvgAbsMargin = f_issue68RawDistAvg(issue68SumAbsMargin, issue68Bars)
float issue68AvgPosMargin = f_issue68RawDistAvg(issue68SumPosMargin, issue68S2LeadBars)
float issue68AvgNegMargin = f_issue68RawDistAvg(issue68SumNegMargin, issue68S1LeadBars)
float issue68AvgS2Run = f_issue68RawDistAvg(float(issue68DisplayS2RunBars), issue68DisplayS2Runs)
float issue68AvgS1Run = f_issue68RawDistAvg(float(issue68DisplayS1RunBars), issue68DisplayS1Runs)

float issue68AvgMarkupOnS2Lead = f_issue68RawDistAvg(issue68SumMarkupOnS2Lead, issue68S2LeadBars)
float issue68AvgAccOnS2Lead = f_issue68RawDistAvg(issue68SumAccOnS2Lead, issue68S2LeadBars)
float issue68AvgMarkupOnS1Lead = f_issue68RawDistAvg(issue68SumMarkupOnS1Lead, issue68S1LeadBars)
float issue68AvgAccOnS1Lead = f_issue68RawDistAvg(issue68SumAccOnS1Lead, issue68S1LeadBars)

plot(issue68RawDistInWindow ? 3.0 : na, "EXPECTED Bull", color=colGreen, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68RawDistValid ? 2.0 : na, "RAW S2 vs S1 leader", color=issue68RawLeader == 1 ? colGreen : colRed, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68RawDistValid ? 1.0 : na, "RAW margin band", color=math.abs(issue68RawMargin) < 10.0 ? colYellow : issue68RawLeader == 1 ? colGreen : colRed, linewidth=4, style=plot.style_linebr, display=display.pane)

var table t = table.new(position.bottom_right, 4, 22, border_width=1)
if barstate.islast
    if showIssue68RawDistTable
        table.cell(t, 0, 0, "RAW MARGIN DIST", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 0, syminfo.ticker, bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 0, "2022-2023 BULL", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 0, str.tostring(issue68Bars) + " bars", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 1, "LEAD / MARGIN", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 1, 1, "VALUE", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 1, "ROLE", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 1, "READ", bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 2, "S2 RAW lead", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 2, str.tostring(issue68S2LeadPct, "#.1") + "%", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 2, "occupancy", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 2, "Markup>S1", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 3, "S1 RAW lead", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 3, str.tostring(issue68S1LeadPct, "#.1") + "%", bgcolor=colRed, text_color=color.white)
        table.cell(t, 2, 3, "occupancy", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 3, "Acc>=S2", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 4, "Avg S2-S1 margin", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 4, str.tostring(issue68AvgMargin, "#.1"), bgcolor=issue68AvgMargin >= 0 ? colGreen : colRed, text_color=color.white)
        table.cell(t, 2, 4, "all bars", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 4, "signed avg", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 5, "Avg |margin|", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 5, str.tostring(issue68AvgAbsMargin, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 5, "all bars", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 5, "separation", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 6, "Avg margin when S2 leads", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 6, str.tostring(issue68AvgPosMargin, "#.1"), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 6, "conditional", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 6, "S2 spike size", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 7, "Avg margin when S1 leads", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 7, str.tostring(issue68AvgNegMargin, "#.1"), bgcolor=colRed, text_color=color.white)
        table.cell(t, 2, 7, "conditional", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 7, "S1 edge size", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 8, "RUN STRUCTURE", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 1, 8, "AVG / MAX", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 8, "RUNS", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 8, "PERSIST", bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 9, "S2-leading runs", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 9, str.tostring(issue68AvgS2Run, "#.1") + " / " + str.tostring(issue68MaxS2Run), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 9, str.tostring(issue68DisplayS2Runs), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 9, "avg/max bars", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 10, "S1-leading runs", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 10, str.tostring(issue68AvgS1Run, "#.1") + " / " + str.tostring(issue68MaxS1Run), bgcolor=colRed, text_color=color.white)
        table.cell(t, 2, 10, str.tostring(issue68DisplayS1Runs), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 10, "avg/max bars", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 11, "Leader flips", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 11, str.tostring(issue68LeaderFlips), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 11, "sign changes", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 11, "churn", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 12, "FIXED RAW BINS", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 1, 12, "SHARE", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 12, "S2-S1", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 12, "DESCRIPTIVE", bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 13, "<= -20", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 13, str.tostring(f_issue68RawDistPct(issue68BinM20, issue68Bars), "#.1") + "%", bgcolor=colRed, text_color=color.white)
        table.cell(t, 2, 13, "clear S1", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 13, "no tuning", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 14, "(-20,-10] / (-10,0]", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 14, str.tostring(f_issue68RawDistPct(issue68BinM20M10, issue68Bars), "#.1") + "% / " + str.tostring(f_issue68RawDistPct(issue68BinM10Zero, issue68Bars), "#.1") + "%", bgcolor=colRed, text_color=color.white)
        table.cell(t, 2, 14, "S1 bands", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 14, "near at right", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 15, "(0,10) / [10,20)", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 15, str.tostring(f_issue68RawDistPct(issue68BinZeroP10, issue68Bars), "#.1") + "% / " + str.tostring(f_issue68RawDistPct(issue68BinP10P20, issue68Bars), "#.1") + "%", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 15, "S2 bands", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 15, "near at left", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 16, ">= 20", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 16, str.tostring(f_issue68RawDistPct(issue68BinP20, issue68Bars), "#.1") + "%", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 16, "clear S2", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 16, "no tuning", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 17, "CONDITIONAL LEVELS", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 1, 17, "S2 RAW / S1 RAW", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 17, "WHEN", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 17, "WHY", bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 18, "On S2-leading bars", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 18, str.tostring(issue68AvgMarkupOnS2Lead, "#.1") + " / " + str.tostring(issue68AvgAccOnS2Lead, "#.1"), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 18, "S2>S1", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 18, "spike anatomy", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 19, "On S1-leading bars", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 19, str.tostring(issue68AvgMarkupOnS1Lead, "#.1") + " / " + str.tostring(issue68AvgAccOnS1Lead, "#.1"), bgcolor=colRed, text_color=color.white)
        table.cell(t, 2, 19, "S1>=S2", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 19, "persistent anatomy", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 20, "MODE", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 20, "DISCOVERY", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 20, "NO TUNING", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 20, "FROZEN C-2", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 21, "READ", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 21, "Green=S2", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 21, "Red=S1", bgcolor=colRed, text_color=color.white)
        table.cell(t, 3, 21, "Yellow=|margin|<10", bgcolor=colYellow, text_color=color.white)
    else
        table.clear(t, 0, 0, 3, 21)
'''.strip()


def generate(source: Path) -> str:
    d1_text = phase_b.d1.generate(source)
    if d1_text.count(phase_b.D1_EXPORT_MARKER) != 1:
        raise RuntimeError("expected exactly one D1 parity export marker")
    core = d1_text.split(phase_b.D1_EXPORT_MARKER, 1)[0].rstrip()
    core = replace_once(core, phase_b.D1_INDICATOR_DECL, AUDIT_DECL)
    out = core + "\n\n" + BODY + "\n"
    required = (
        "RAW Margin Distribution Audit",
        "S2 RAW lead",
        "S1-leading runs",
        "FIXED RAW BINS",
        "CONDITIONAL LEVELS",
    )
    for token in required:
        if token not in out:
            raise RuntimeError(f"missing RAW margin distribution token: {token}")
    if "strategy." in out:
        raise RuntimeError("strategy token leaked into RAW margin diagnostic")
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
