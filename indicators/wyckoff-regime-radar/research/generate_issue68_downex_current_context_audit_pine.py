#!/usr/bin/env python3
"""Generate Issue #68 DownEx current-bear-context counterfactual audit Pine."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_support_invariant_slope_shadow_pine as si
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 DownEx Current Context", shorttitle="ChaseRisk #68 DownExCtx", overlay=false, precision=3)'
SI_PLOT_MARKER = 'plot(issue68SIInWindow ? 3.0 : na, "Expected Bull window"'

BODY = r'''

// ============================================================================
// Issue #68 DownEx Current-Context Counterfactual.
// Shared discovery window: 2022-01-03 -> 2023-12-29, expected Bull yield regime.
// No thresholds or weights changed. Current context uses bearBg with the same
// 35/75 bounds as production bearBackgroundForAccGate.
// DISCOVERY ONLY. NO PNL. NO TUNING. PRODUCTION C-2 FROZEN.
// ============================================================================

groupIssue68CC = "Issue #68｜DownEx Current Context"
showIssue68CCTable = input.bool(true, "顯示 DownEx Current Context 表", group=groupIssue68CC)

f_issue68CCTopProd(float accX) =>
    float best = accX
    int id = 1
    if markupEff > best
        best := markupEff
        id := 2
    if reaccEff > best
        best := reaccEff
        id := 3
    if distEff > best
        best := distEff
        id := 4
    if markdownEff > best
        best := markdownEff
        id := 5
    if redistEff > best
        best := redistEff
        id := 6
    id

f_issue68CCTopSI(float accX) =>
    float best = accX
    int id = 1
    if issue68SIMarkupEff > best
        best := issue68SIMarkupEff
        id := 2
    if issue68SIReaccEff > best
        best := issue68SIReaccEff
        id := 3
    if issue68SIDistEff > best
        best := issue68SIDistEff
        id := 4
    if issue68SIMarkdownEff > best
        best := issue68SIMarkdownEff
        id := 5
    if issue68SIRedistEff > best
        best := issue68SIRedistEff
        id := 6
    id

// Current bearish context: exact existing 35/75 gate bounds, but current bearBg
// only; no bearMaturityTrace max-memory is allowed into this context signal.
float issue68CCCurrentBearGate = f_gate(bearBg, 35.0, 75.0)
float issue68CCProdBoundDownGate = math.min(downsideExhaustionGate, issue68CCCurrentBearGate)
float issue68CCSIBoundDownGate = math.min(issue68SIDownExGate, issue68CCCurrentBearGate)

float issue68CCProdCtxAccGate = rangeGate * bearBackgroundForAccGate * issue68CCProdBoundDownGate * supportHoldingGate * nonMarkdownContinuationGate
float issue68CCSICtxAccGate = rangeGate * bearBackgroundForAccGate * issue68CCSIBoundDownGate * supportHoldingGate * issue68SINonMarkdownContinuationGate

float issue68CCAccMult = accVolMult * accMtfMult * accDivMult
float issue68CCProdCtxAccEff = accRaw * issue68CCProdCtxAccGate * issue68CCAccMult
float issue68CCSICtxAccEff = issue68SIAccRaw * issue68CCSICtxAccGate * issue68CCAccMult

bool issue68CCValid = issue68SIValid and not na(issue68CCCurrentBearGate) and not na(issue68CCProdCtxAccEff) and not na(issue68CCSICtxAccEff)
int issue68CCProdCtxTop = issue68CCValid ? f_issue68CCTopProd(issue68CCProdCtxAccEff) : na
int issue68CCSICtxTop = issue68CCValid ? f_issue68CCTopSI(issue68CCSICtxAccEff) : na

bool issue68CCProdBull = issue68CCValid and (topId == 2 or topId == 3)
bool issue68CCProdCtxBull = issue68CCValid and (issue68CCProdCtxTop == 2 or issue68CCProdCtxTop == 3)
bool issue68CCSIBull = issue68CCValid and (issue68SITopId == 2 or issue68SITopId == 3)
bool issue68CCSICtxBull = issue68CCValid and (issue68CCSICtxTop == 2 or issue68CCSICtxTop == 3)

var int issue68CCN = 0
var float issue68CCSumCurrentBearGate = 0.0
var float issue68CCSumProdBgGate = 0.0
var float issue68CCSumTraceAdv = 0.0
var int issue68CCTraceAdvN = 0
var int issue68CCProdCapN = 0
var int issue68CCSICapN = 0

var float issue68CCSumProdGate = 0.0
var float issue68CCSumProdCtxGate = 0.0
var float issue68CCSumSIGate = 0.0
var float issue68CCSumSICtxGate = 0.0
var float issue68CCSumProdEff = 0.0
var float issue68CCSumProdCtxEff = 0.0
var float issue68CCSumSIEff = 0.0
var float issue68CCSumSICtxEff = 0.0
var float issue68CCSumProdDownGate = 0.0
var float issue68CCSumProdBoundDownGate = 0.0
var float issue68CCSumSIDownGate = 0.0
var float issue68CCSumSIBoundDownGate = 0.0

var int issue68CCProdS2Over = 0
var int issue68CCProdCtxS2Over = 0
var int issue68CCSIS2Over = 0
var int issue68CCSICtxS2Over = 0
var int issue68CCProdS1Top = 0
var int issue68CCProdCtxS1Top = 0
var int issue68CCSIS1Top = 0
var int issue68CCSICtxS1Top = 0
var int issue68CCProdBullTop = 0
var int issue68CCProdCtxBullTop = 0
var int issue68CCSIBullTop = 0
var int issue68CCSICtxBullTop = 0
var int issue68CCProdCtxTopChanged = 0
var int issue68CCSICtxTopChanged = 0

if issue68CCValid
    issue68CCN += 1
    issue68CCSumCurrentBearGate += issue68CCCurrentBearGate
    issue68CCSumProdBgGate += bearBackgroundForAccGate
    float traceAdv = bearBackgroundForAccGate - issue68CCCurrentBearGate
    issue68CCSumTraceAdv += traceAdv
    issue68CCTraceAdvN += traceAdv > 0.0 ? 1 : 0
    issue68CCProdCapN += downsideExhaustionGate > issue68CCCurrentBearGate ? 1 : 0
    issue68CCSICapN += issue68SIDownExGate > issue68CCCurrentBearGate ? 1 : 0

    issue68CCSumProdGate += accGate
    issue68CCSumProdCtxGate += issue68CCProdCtxAccGate
    issue68CCSumSIGate += issue68SIAccGate
    issue68CCSumSICtxGate += issue68CCSICtxAccGate
    issue68CCSumProdEff += accEff
    issue68CCSumProdCtxEff += issue68CCProdCtxAccEff
    issue68CCSumSIEff += issue68SIAccEff
    issue68CCSumSICtxEff += issue68CCSICtxAccEff
    issue68CCSumProdDownGate += downsideExhaustionGate
    issue68CCSumProdBoundDownGate += issue68CCProdBoundDownGate
    issue68CCSumSIDownGate += issue68SIDownExGate
    issue68CCSumSIBoundDownGate += issue68CCSIBoundDownGate

    issue68CCProdS2Over += markupEff > accEff ? 1 : 0
    issue68CCProdCtxS2Over += markupEff > issue68CCProdCtxAccEff ? 1 : 0
    issue68CCSIS2Over += issue68SIMarkupEff > issue68SIAccEff ? 1 : 0
    issue68CCSICtxS2Over += issue68SIMarkupEff > issue68CCSICtxAccEff ? 1 : 0

    issue68CCProdS1Top += topId == 1 ? 1 : 0
    issue68CCProdCtxS1Top += issue68CCProdCtxTop == 1 ? 1 : 0
    issue68CCSIS1Top += issue68SITopId == 1 ? 1 : 0
    issue68CCSICtxS1Top += issue68CCSICtxTop == 1 ? 1 : 0

    issue68CCProdBullTop += issue68CCProdBull ? 1 : 0
    issue68CCProdCtxBullTop += issue68CCProdCtxBull ? 1 : 0
    issue68CCSIBullTop += issue68CCSIBull ? 1 : 0
    issue68CCSICtxBullTop += issue68CCSICtxBull ? 1 : 0

    issue68CCProdCtxTopChanged += issue68CCProdCtxTop != topId ? 1 : 0
    issue68CCSICtxTopChanged += issue68CCSICtxTop != issue68SITopId ? 1 : 0

plot(issue68SIInWindow ? 3.0 : na, "EXPECTED Bull", color=colGreen, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68CCValid ? 2.0 : na, "PROD+CTX TOP", color=issue68CCProdCtxBull ? colGreen : colRed, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68CCValid ? 1.0 : na, "SI+CTX TOP", color=issue68CCSICtxBull ? colGreen : colRed, linewidth=4, style=plot.style_linebr, display=display.pane)

var table tCC = table.new(position.middle_right, 5, 16, border_width=1)
if barstate.islast
    if showIssue68CCTable
        table.cell(tCC, 0, 0, "DOWNEX CURRENT CONTEXT", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 1, 0, "PROD", bgcolor=colRed, text_color=color.white)
        table.cell(tCC, 2, 0, "PROD+CTX", bgcolor=colGreen, text_color=color.white)
        table.cell(tCC, 3, 0, "SI", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 4, 0, "SI+CTX", bgcolor=colGreen, text_color=color.white)

        table.cell(tCC, 0, 1, "Population", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 1, 1, str.tostring(issue68CCN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 2, 1, "same", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 3, 1, "same", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 4, 1, "same", bgcolor=colNeutral, text_color=color.white)

        table.cell(tCC, 0, 2, "S1 gate avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 1, 2, f_issue68SIFmt(f_issue68SIAvg(issue68CCSumProdGate, issue68CCN)), bgcolor=colRed, text_color=color.white)
        table.cell(tCC, 2, 2, f_issue68SIFmt(f_issue68SIAvg(issue68CCSumProdCtxGate, issue68CCN)), bgcolor=colGreen, text_color=color.white)
        table.cell(tCC, 3, 2, f_issue68SIFmt(f_issue68SIAvg(issue68CCSumSIGate, issue68CCN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 4, 2, f_issue68SIFmt(f_issue68SIAvg(issue68CCSumSICtxGate, issue68CCN)), bgcolor=colGreen, text_color=color.white)

        table.cell(tCC, 0, 3, "S1 EFF avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 1, 3, f_issue68SIFmt(f_issue68SIAvg(issue68CCSumProdEff, issue68CCN)), bgcolor=colRed, text_color=color.white)
        table.cell(tCC, 2, 3, f_issue68SIFmt(f_issue68SIAvg(issue68CCSumProdCtxEff, issue68CCN)), bgcolor=colGreen, text_color=color.white)
        table.cell(tCC, 3, 3, f_issue68SIFmt(f_issue68SIAvg(issue68CCSumSIEff, issue68CCN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 4, 3, f_issue68SIFmt(f_issue68SIAvg(issue68CCSumSICtxEff, issue68CCN)), bgcolor=colGreen, text_color=color.white)

        table.cell(tCC, 0, 4, "S2 EFF > S1", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 1, 4, f_issue68SIFmtPct(issue68CCProdS2Over, issue68CCN), bgcolor=colRed, text_color=color.white)
        table.cell(tCC, 2, 4, f_issue68SIFmtPct(issue68CCProdCtxS2Over, issue68CCN), bgcolor=colGreen, text_color=color.white)
        table.cell(tCC, 3, 4, f_issue68SIFmtPct(issue68CCSIS2Over, issue68CCN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 4, 4, f_issue68SIFmtPct(issue68CCSICtxS2Over, issue68CCN), bgcolor=colGreen, text_color=color.white)

        table.cell(tCC, 0, 5, "S1 TOP", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 1, 5, f_issue68SIFmtPct(issue68CCProdS1Top, issue68CCN), bgcolor=colRed, text_color=color.white)
        table.cell(tCC, 2, 5, f_issue68SIFmtPct(issue68CCProdCtxS1Top, issue68CCN), bgcolor=colGreen, text_color=color.white)
        table.cell(tCC, 3, 5, f_issue68SIFmtPct(issue68CCSIS1Top, issue68CCN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 4, 5, f_issue68SIFmtPct(issue68CCSICtxS1Top, issue68CCN), bgcolor=colGreen, text_color=color.white)

        table.cell(tCC, 0, 6, "Bull TOP", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 1, 6, f_issue68SIFmtPct(issue68CCProdBullTop, issue68CCN), bgcolor=colRed, text_color=color.white)
        table.cell(tCC, 2, 6, f_issue68SIFmtPct(issue68CCProdCtxBullTop, issue68CCN), bgcolor=colGreen, text_color=color.white)
        table.cell(tCC, 3, 6, f_issue68SIFmtPct(issue68CCSIBullTop, issue68CCN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 4, 6, f_issue68SIFmtPct(issue68CCSICtxBullTop, issue68CCN), bgcolor=colGreen, text_color=color.white)

        table.cell(tCC, 0, 7, "TOP changed", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 1, 7, "0%", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 2, 7, f_issue68SIFmtPct(issue68CCProdCtxTopChanged, issue68CCN), bgcolor=colGreen, text_color=color.white)
        table.cell(tCC, 3, 7, "0%", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 4, 7, f_issue68SIFmtPct(issue68CCSICtxTopChanged, issue68CCN), bgcolor=colGreen, text_color=color.white)

        table.cell(tCC, 0, 8, "CONTEXT DIAGNOSTICS", bgcolor=colGreen, text_color=color.white)
        table.cell(tCC, 1, 8, "AVG", bgcolor=colGreen, text_color=color.white)
        table.cell(tCC, 2, 8, "SHARE", bgcolor=colGreen, text_color=color.white)
        table.cell(tCC, 3, 8, "READ", bgcolor=colGreen, text_color=color.white)
        table.cell(tCC, 4, 8, "FROZEN", bgcolor=colGreen, text_color=color.white)

        table.cell(tCC, 0, 9, "Current bear gate", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 1, 9, f_issue68SIFmt(f_issue68SIAvg(issue68CCSumCurrentBearGate, issue68CCN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 2, 9, "gate(bearBg,35,75)", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 3, 9, "current only", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 4, 9, "same bounds", bgcolor=colNeutral, text_color=color.white)

        table.cell(tCC, 0, 10, "Prod bg / trace adv", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 1, 10, f_issue68SIFmt(f_issue68SIAvg(issue68CCSumProdBgGate, issue68CCN)) + " / " + f_issue68SIFmt(f_issue68SIAvg(issue68CCSumTraceAdv, issue68CCN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 2, 10, f_issue68SIFmtPct(issue68CCTraceAdvN, issue68CCN), bgcolor=colRed, text_color=color.white)
        table.cell(tCC, 3, 10, "trace > current", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 4, 10, "no tuning", bgcolor=colNeutral, text_color=color.white)

        table.cell(tCC, 0, 11, "DownEx gate avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 1, 11, f_issue68SIFmt(f_issue68SIAvg(issue68CCSumProdDownGate, issue68CCN)), bgcolor=colRed, text_color=color.white)
        table.cell(tCC, 2, 11, f_issue68SIFmt(f_issue68SIAvg(issue68CCSumProdBoundDownGate, issue68CCN)), bgcolor=colGreen, text_color=color.white)
        table.cell(tCC, 3, 11, f_issue68SIFmt(f_issue68SIAvg(issue68CCSumSIDownGate, issue68CCN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 4, 11, f_issue68SIFmt(f_issue68SIAvg(issue68CCSumSIBoundDownGate, issue68CCN)), bgcolor=colGreen, text_color=color.white)

        table.cell(tCC, 0, 12, "DownEx capped", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 1, 12, "—", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 2, 12, f_issue68SIFmtPct(issue68CCProdCapN, issue68CCN), bgcolor=colGreen, text_color=color.white)
        table.cell(tCC, 3, 12, "—", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 4, 12, f_issue68SIFmtPct(issue68CCSICapN, issue68CCN), bgcolor=colGreen, text_color=color.white)

        table.cell(tCC, 0, 13, "INTERPRET", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 1, 13, "Does FR improve?", bgcolor=colGreen, text_color=color.white)
        table.cell(tCC, 2, 13, "DE survives?", bgcolor=colGreen, text_color=color.white)
        table.cell(tCC, 3, 13, "SI collapse fixed?", bgcolor=colGreen, text_color=color.white)
        table.cell(tCC, 4, 13, "then controls", bgcolor=colGreen, text_color=color.white)

        table.cell(tCC, 0, 14, "MODE", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 1, 14, "DISCOVERY", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 2, 14, "NO TUNING", bgcolor=colRed, text_color=color.white)
        table.cell(tCC, 3, 14, "NO PNL", bgcolor=colRed, text_color=color.white)
        table.cell(tCC, 4, 14, "FROZEN C-2", bgcolor=colNeutral, text_color=color.white)

        table.cell(tCC, 0, 15, "READ", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 1, 15, "Green=CTX", bgcolor=colGreen, text_color=color.white)
        table.cell(tCC, 2, 15, "Red=PROD", bgcolor=colRed, text_color=color.white)
        table.cell(tCC, 3, 15, "SI=bp shadow", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCC, 4, 15, "CTX=min cap", bgcolor=colGreen, text_color=color.white)
    else
        table.clear(tCC, 0, 0, 4, 15)
'''


def generate(source: Path) -> str:
    base = si.generate(source)
    if base.count(SI_PLOT_MARKER) != 1:
        raise RuntimeError("expected one support-invariant plot marker")
    core = base.split(SI_PLOT_MARKER, 1)[0].rstrip()
    core = replace_once(core, si.AUDIT_DECL, AUDIT_DECL)
    out = core + "\n\n" + BODY + "\n"
    for token in (
        "DownEx Current-Context Counterfactual",
        "currentBearContextGate",
        "PROD+CTX",
        "SI+CTX",
        "DownEx capped",
        "CTX=min cap",
    ):
        if token not in out:
            raise RuntimeError(f"missing required audit token: {token}")
    if "strategy.entry" in out or "strategy.close" in out:
        raise RuntimeError("DownEx current-context audit leaked strategy order logic")
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
