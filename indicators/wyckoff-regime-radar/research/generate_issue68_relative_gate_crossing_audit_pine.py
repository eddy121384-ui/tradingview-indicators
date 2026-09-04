#!/usr/bin/env python3
"""Generate Issue #68 FR10Y vs DE10Y relative-gate crossing audit Pine."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_phase_b_lifecycle_pine as phase_b
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 Relative Gate Crossing", shorttitle="ChaseRisk #68 GateX", overlay=false, precision=3)'

BODY = r'''

// ============================================================================
// Issue #68 FR10Y vs DE10Y Relative-Gate Crossing Audit.
// Shared window: 2022-01-03 -> 2023-12-29, expected Bull yield regime.
// DISCOVERY ONLY. NO PNL. NO TUNING. FROZEN C-2.
// ============================================================================

groupIssue68RG = "Issue #68｜Relative Gate Crossing"
showIssue68RGTable = input.bool(true, "顯示 Relative Gate Crossing 表", group=groupIssue68RG)

issue68RGReady = bar_index >= rankLen - 1
int issue68RGStart = timestamp(2022, 1, 3, 0, 0)
int issue68RGEnd = timestamp(2023, 12, 29, 23, 59)
bool issue68RGInWindow = issue68RGReady and time >= issue68RGStart and time <= issue68RGEnd
bool issue68RGValid = issue68RGInWindow and not na(accRaw) and not na(markupRaw) and not na(accGate) and not na(markupGate) and not na(accEff) and not na(markupEff)
bool issue68RGRatioValid = issue68RGValid and accRaw > 0.0 and markupRaw > 0.0 and accGate > 0.0 and markupGate > 0.0

f_issue68RGAvg(float s, int n) => n > 0 ? s / n : na
f_issue68RGPct(int n, int d) => d > 0 ? 100.0 * n / d : na

f_issue68RGDomS1(int a, int b, int c, int d, int e) =>
    int best = a
    string name = "Range"
    if b > best
        best := b
        name := "Bear-bg"
    if c > best
        best := c
        name := "Down-exhaust"
    if d > best
        best := d
        name := "Support"
    if e > best
        best := e
        name := "Non-MD"
    int total = a + b + c + d + e
    name + " " + str.tostring(f_issue68RGPct(best, total), "#.1") + "%"

f_issue68RGDomS2(int a, int b, int c) =>
    int best = a
    string name = "Breakout"
    if b > best
        best := b
        name := "Extension"
    if c > best
        best := c
        name := "Continuation"
    int total = a + b + c
    name + " " + str.tostring(f_issue68RGPct(best, total), "#.1") + "%"

bool issue68RGRawS1LeadNow = issue68RGValid and accRaw >= markupRaw
bool issue68RGEffS2LeadNow = issue68RGValid and markupEff > accEff
bool issue68RGFlipNow = issue68RGRawS1LeadNow and issue68RGEffS2LeadNow

float issue68RGRequiredRatio = issue68RGRatioValid ? accRaw / markupRaw : na
float issue68RGObservedRatio = issue68RGRatioValid ? markupGate / accGate : na
float issue68RGGateSurplus = issue68RGRatioValid ? issue68RGObservedRatio - issue68RGRequiredRatio : na
bool issue68RGSurplusPositive = issue68RGRatioValid and issue68RGGateSurplus > 0.0
bool issue68RGAlgebraMismatch = issue68RGRatioValid and issue68RGRawS1LeadNow and (issue68RGSurplusPositive != issue68RGEffS2LeadNow)

int issue68RGS1Bind = 1
float issue68RGS1Min = rangeGate
if bearBackgroundForAccGate < issue68RGS1Min
    issue68RGS1Bind := 2
    issue68RGS1Min := bearBackgroundForAccGate
if downsideExhaustionGate < issue68RGS1Min
    issue68RGS1Bind := 3
    issue68RGS1Min := downsideExhaustionGate
if supportHoldingGate < issue68RGS1Min
    issue68RGS1Bind := 4
    issue68RGS1Min := supportHoldingGate
if nonMarkdownContinuationGate < issue68RGS1Min
    issue68RGS1Bind := 5
    issue68RGS1Min := nonMarkdownContinuationGate

int issue68RGS2Source = breakoutMarkupGate >= math.max(markupExtensionGate, markupContinuationGate) ? 1 : markupExtensionGate >= markupContinuationGate ? 2 : 3

var int issue68RGBars = 0
var int issue68RGRatioBars = 0
var int issue68RGRawS1Lead = 0
var int issue68RGEffS2Lead = 0
var int issue68RGFlip = 0
var int issue68RGSurplusPos = 0
var int issue68RGMismatch = 0

var float issue68RGSumRequired = 0.0
var float issue68RGSumObserved = 0.0
var float issue68RGSumSurplus = 0.0

var int issue68RGFlipRunsDone = 0
var int issue68RGFlipRunBarsDone = 0
var int issue68RGFlipRunNow = 0
var int issue68RGFlipRunMax = 0

var float issue68RGSumS1GateFlip = 0.0
var float issue68RGSumS2GateFlip = 0.0
var float issue68RGSumS1GateNoFlip = 0.0
var float issue68RGSumS2GateNoFlip = 0.0
var int issue68RGFlipPop = 0
var int issue68RGNoFlipPop = 0

var int issue68RGFlipS1Range = 0
var int issue68RGFlipS1BearBg = 0
var int issue68RGFlipS1DownEx = 0
var int issue68RGFlipS1Support = 0
var int issue68RGFlipS1NonMd = 0
var int issue68RGNoFlipS1Range = 0
var int issue68RGNoFlipS1BearBg = 0
var int issue68RGNoFlipS1DownEx = 0
var int issue68RGNoFlipS1Support = 0
var int issue68RGNoFlipS1NonMd = 0

var int issue68RGFlipS2Breakout = 0
var int issue68RGFlipS2Extension = 0
var int issue68RGFlipS2Continuation = 0
var int issue68RGNoFlipS2Breakout = 0
var int issue68RGNoFlipS2Extension = 0
var int issue68RGNoFlipS2Continuation = 0

if issue68RGValid
    issue68RGBars += 1
    issue68RGRawS1Lead += issue68RGRawS1LeadNow ? 1 : 0
    issue68RGEffS2Lead += issue68RGEffS2LeadNow ? 1 : 0
    issue68RGFlip += issue68RGFlipNow ? 1 : 0

    if issue68RGFlipNow
        issue68RGFlipRunNow += 1
        issue68RGFlipRunMax := math.max(issue68RGFlipRunMax, issue68RGFlipRunNow)
    else if issue68RGFlipRunNow > 0
        issue68RGFlipRunsDone += 1
        issue68RGFlipRunBarsDone += issue68RGFlipRunNow
        issue68RGFlipRunNow := 0

    if issue68RGRawS1LeadNow
        if issue68RGFlipNow
            issue68RGFlipPop += 1
            issue68RGSumS1GateFlip += accGate
            issue68RGSumS2GateFlip += markupGate
            issue68RGFlipS1Range += issue68RGS1Bind == 1 ? 1 : 0
            issue68RGFlipS1BearBg += issue68RGS1Bind == 2 ? 1 : 0
            issue68RGFlipS1DownEx += issue68RGS1Bind == 3 ? 1 : 0
            issue68RGFlipS1Support += issue68RGS1Bind == 4 ? 1 : 0
            issue68RGFlipS1NonMd += issue68RGS1Bind == 5 ? 1 : 0
            issue68RGFlipS2Breakout += issue68RGS2Source == 1 ? 1 : 0
            issue68RGFlipS2Extension += issue68RGS2Source == 2 ? 1 : 0
            issue68RGFlipS2Continuation += issue68RGS2Source == 3 ? 1 : 0
        else
            issue68RGNoFlipPop += 1
            issue68RGSumS1GateNoFlip += accGate
            issue68RGSumS2GateNoFlip += markupGate
            issue68RGNoFlipS1Range += issue68RGS1Bind == 1 ? 1 : 0
            issue68RGNoFlipS1BearBg += issue68RGS1Bind == 2 ? 1 : 0
            issue68RGNoFlipS1DownEx += issue68RGS1Bind == 3 ? 1 : 0
            issue68RGNoFlipS1Support += issue68RGS1Bind == 4 ? 1 : 0
            issue68RGNoFlipS1NonMd += issue68RGS1Bind == 5 ? 1 : 0
            issue68RGNoFlipS2Breakout += issue68RGS2Source == 1 ? 1 : 0
            issue68RGNoFlipS2Extension += issue68RGS2Source == 2 ? 1 : 0
            issue68RGNoFlipS2Continuation += issue68RGS2Source == 3 ? 1 : 0

if issue68RGRatioValid
    issue68RGRatioBars += 1
    issue68RGSumRequired += issue68RGRequiredRatio
    issue68RGSumObserved += issue68RGObservedRatio
    issue68RGSumSurplus += issue68RGGateSurplus
    issue68RGSurplusPos += issue68RGSurplusPositive ? 1 : 0
    issue68RGMismatch += issue68RGAlgebraMismatch ? 1 : 0

int issue68RGDisplayFlipRuns = issue68RGFlipRunsDone + (issue68RGFlipRunNow > 0 ? 1 : 0)
int issue68RGDisplayFlipRunBars = issue68RGFlipRunBarsDone + issue68RGFlipRunNow
float issue68RGAvgFlipRun = f_issue68RGAvg(float(issue68RGDisplayFlipRunBars), issue68RGDisplayFlipRuns)

float issue68RGAvgRequired = f_issue68RGAvg(issue68RGSumRequired, issue68RGRatioBars)
float issue68RGAvgObserved = f_issue68RGAvg(issue68RGSumObserved, issue68RGRatioBars)
float issue68RGAvgSurplus = f_issue68RGAvg(issue68RGSumSurplus, issue68RGRatioBars)
float issue68RGAvgS1GateFlip = f_issue68RGAvg(issue68RGSumS1GateFlip, issue68RGFlipPop)
float issue68RGAvgS2GateFlip = f_issue68RGAvg(issue68RGSumS2GateFlip, issue68RGFlipPop)
float issue68RGAvgS1GateNoFlip = f_issue68RGAvg(issue68RGSumS1GateNoFlip, issue68RGNoFlipPop)
float issue68RGAvgS2GateNoFlip = f_issue68RGAvg(issue68RGSumS2GateNoFlip, issue68RGNoFlipPop)

plot(issue68RGInWindow ? 3.0 : na, "EXPECTED Bull", color=colGreen, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68RGValid ? 2.0 : na, "RAW S1 to EFF S2 flip", color=issue68RGFlipNow ? colGreen : colRed, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68RGRatioValid ? 1.0 : na, "Relative gate surplus sign", color=issue68RGSurplusPositive ? colGreen : colRed, linewidth=4, style=plot.style_linebr, display=display.pane)

var table t = table.new(position.middle_right, 4, 18, border_width=1)
if barstate.islast
    if showIssue68RGTable
        table.cell(t, 0, 0, "RELATIVE GATE CROSSING", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 0, syminfo.ticker, bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 0, "2022-2023 BULL", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 0, str.tostring(issue68RGBars) + " bars", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 1, "CORE CROSSING", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 1, 1, "SHARE", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 1, "COUNT", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 1, "READ", bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 2, "RAW S1 >= S2", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 2, str.tostring(f_issue68RGPct(issue68RGRawS1Lead, issue68RGBars), "#.1") + "%", bgcolor=colRed, text_color=color.white)
        table.cell(t, 2, 2, str.tostring(issue68RGRawS1Lead), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 2, "start order", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 3, "EFF S2 > S1", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 3, str.tostring(f_issue68RGPct(issue68RGEffS2Lead, issue68RGBars), "#.1") + "%", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 3, str.tostring(issue68RGEffS2Lead), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 3, "post gate", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 4, "RAW S1 -> EFF S2", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 4, str.tostring(f_issue68RGPct(issue68RGFlip, issue68RGBars), "#.1") + "%", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 4, str.tostring(issue68RGFlip), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 4, "KEY FLIP", bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 5, "Gate surplus > 0", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 5, str.tostring(f_issue68RGPct(issue68RGSurplusPos, issue68RGRatioBars), "#.1") + "%", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 5, str.tostring(issue68RGSurplusPos), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 5, "ratio crossing", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 6, "Algebra mismatch", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 6, str.tostring(issue68RGMismatch), bgcolor=issue68RGMismatch == 0 ? colGreen : colRed, text_color=color.white)
        table.cell(t, 2, 6, str.tostring(issue68RGRatioBars) + " ratio bars", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 6, "must be 0", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 7, "RATIO ATTRIBUTION", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 1, 7, "AVG", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 7, "FORMULA", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 7, "MEANING", bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 8, "Required / observed", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 8, str.tostring(issue68RGAvgRequired, "#.3") + " / " + str.tostring(issue68RGAvgObserved, "#.3"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 8, "S1raw/S2raw | S2g/S1g", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 8, "cross if obs>req", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 9, "Avg gate surplus", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 9, str.tostring(issue68RGAvgSurplus, "#.3"), bgcolor=issue68RGAvgSurplus > 0 ? colGreen : colRed, text_color=color.white)
        table.cell(t, 2, 9, "observed-required", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 9, "relative edge", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 10, "FLIP RUNS", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 1, 10, "AVG / MAX", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 10, "RUNS", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 10, "PERSIST", bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 11, "RAW S1 -> EFF S2", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 11, str.tostring(issue68RGAvgFlipRun, "#.1") + " / " + str.tostring(issue68RGFlipRunMax), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 11, str.tostring(issue68RGDisplayFlipRuns), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 11, "bars", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 12, "CONDITIONAL GATES", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 1, 12, "FLIP / NO-FLIP", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 12, "ROLE", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 12, "ROOT", bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 13, "S1 gate avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 13, str.tostring(issue68RGAvgS1GateFlip, "#.3") + " / " + str.tostring(issue68RGAvgS1GateNoFlip, "#.3"), bgcolor=colRed, text_color=color.white)
        table.cell(t, 2, 13, "Acc gate", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 13, "suppression", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 14, "S2 gate avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 14, str.tostring(issue68RGAvgS2GateFlip, "#.3") + " / " + str.tostring(issue68RGAvgS2GateNoFlip, "#.3"), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 14, "Markup gate", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 14, "support", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 15, "S1 bottleneck", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 15, f_issue68RGDomS1(issue68RGFlipS1Range, issue68RGFlipS1BearBg, issue68RGFlipS1DownEx, issue68RGFlipS1Support, issue68RGFlipS1NonMd), bgcolor=colRed, text_color=color.white)
        table.cell(t, 2, 15, f_issue68RGDomS1(issue68RGNoFlipS1Range, issue68RGNoFlipS1BearBg, issue68RGNoFlipS1DownEx, issue68RGNoFlipS1Support, issue68RGNoFlipS1NonMd), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 15, "flip / no-flip", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 16, "S2 gate source", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 16, f_issue68RGDomS2(issue68RGFlipS2Breakout, issue68RGFlipS2Extension, issue68RGFlipS2Continuation), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 16, f_issue68RGDomS2(issue68RGNoFlipS2Breakout, issue68RGNoFlipS2Extension, issue68RGNoFlipS2Continuation), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 16, "flip / no-flip", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 17, "READ", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 17, "DE gate edge?", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 17, "NO TUNING", bgcolor=colRed, text_color=color.white)
        table.cell(t, 3, 17, "FROZEN C-2", bgcolor=colNeutral, text_color=color.white)
    else
        table.clear(t, 0, 0, 3, 17)
'''


def generate(source: Path) -> str:
    core = phase_b.shared_body(source)
    lines = core.splitlines()
    strategy_indices = [i for i, line in enumerate(lines) if line.startswith("strategy(")]
    if len(strategy_indices) != 1:
        raise RuntimeError(f"expected one strategy declaration, found {len(strategy_indices)}")
    lines[strategy_indices[0]] = AUDIT_DECL
    out = "\n".join(lines).rstrip() + BODY + "\n"
    for token in (
        "Relative-Gate Crossing Audit",
        "RAW S1 -> EFF S2",
        "Gate surplus > 0",
        "Algebra mismatch",
        "S1 bottleneck",
        "S2 gate source",
    ):
        if token not in out:
            raise RuntimeError(f"missing required audit token: {token}")
    if "strategy.entry" in out or "strategy.close" in out:
        raise RuntimeError("relative-gate audit leaked strategy order logic")
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
