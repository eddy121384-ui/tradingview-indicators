#!/usr/bin/env python3
"""Generate Issue #68 direct-vs-indirect DownEx S1 gate-channel audit."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_support_invariant_slope_shadow_pine as si
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 DownEx Gate Channels", shorttitle="ChaseRisk #68 GateChan", overlay=false, precision=3)'

BODY = r'''

// ============================================================================
// Issue #68 DownEx Gate-Channel Decomposition.
// Shared window: 2022-01-03 -> 2023-12-29, expected Bull yield regime.
// DIRECT = downsideExhaustionGate route.
// INDIRECT = markdownContinuationScore -> nonMarkdownContinuationGate route.
// DISCOVERY ONLY. NO PNL. NO TUNING. PRODUCTION C-2 FROZEN.
// ============================================================================

groupIssue68GC = "Issue #68｜DownEx Gate Channels"
showIssue68GCTable = input.bool(true, "顯示 DownEx Gate Channels 表", group=groupIssue68GC)

f_issue68GCTop(float accX) =>
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

float issue68GCBase = rangeGate * bearBackgroundForAccGate * supportHoldingGate
float issue68GCGateProd = issue68GCBase * downsideExhaustionGate * nonMarkdownContinuationGate
float issue68GCGateDirect = issue68GCBase * issue68SIDownExGate * nonMarkdownContinuationGate
float issue68GCGateIndirect = issue68GCBase * downsideExhaustionGate * issue68SINonMarkdownContinuationGate
float issue68GCGateBoth = issue68GCBase * issue68SIDownExGate * issue68SINonMarkdownContinuationGate

float issue68GCMult = accVolMult * accMtfMult * accDivMult
float issue68GCEffProd = accRaw * issue68GCGateProd * issue68GCMult
float issue68GCEffDirect = accRaw * issue68GCGateDirect * issue68GCMult
float issue68GCEffIndirect = accRaw * issue68GCGateIndirect * issue68GCMult
float issue68GCEffBoth = accRaw * issue68GCGateBoth * issue68GCMult

bool issue68GCValid = issue68SIValid and not na(issue68GCEffProd) and not na(issue68GCEffDirect) and not na(issue68GCEffIndirect) and not na(issue68GCEffBoth)

int issue68GCTopProd = issue68GCValid ? f_issue68GCTop(issue68GCEffProd) : na
int issue68GCTopDirect = issue68GCValid ? f_issue68GCTop(issue68GCEffDirect) : na
int issue68GCTopIndirect = issue68GCValid ? f_issue68GCTop(issue68GCEffIndirect) : na
int issue68GCTopBoth = issue68GCValid ? f_issue68GCTop(issue68GCEffBoth) : na

bool issue68GCBullProd = issue68GCValid and (issue68GCTopProd == 2 or issue68GCTopProd == 3)
bool issue68GCBullDirect = issue68GCValid and (issue68GCTopDirect == 2 or issue68GCTopDirect == 3)
bool issue68GCBullIndirect = issue68GCValid and (issue68GCTopIndirect == 2 or issue68GCTopIndirect == 3)
bool issue68GCBullBoth = issue68GCValid and (issue68GCTopBoth == 2 or issue68GCTopBoth == 3)

var int issue68GCN = 0
var float issue68GCSumGateProd = 0.0
var float issue68GCSumGateDirect = 0.0
var float issue68GCSumGateIndirect = 0.0
var float issue68GCSumGateBoth = 0.0
var float issue68GCSumEffProd = 0.0
var float issue68GCSumEffDirect = 0.0
var float issue68GCSumEffIndirect = 0.0
var float issue68GCSumEffBoth = 0.0

var int issue68GCS2OverProd = 0
var int issue68GCS2OverDirect = 0
var int issue68GCS2OverIndirect = 0
var int issue68GCS2OverBoth = 0
var int issue68GCS1TopProd = 0
var int issue68GCS1TopDirect = 0
var int issue68GCS1TopIndirect = 0
var int issue68GCS1TopBoth = 0
var int issue68GCBullTopProd = 0
var int issue68GCBullTopDirect = 0
var int issue68GCBullTopIndirect = 0
var int issue68GCBullTopBoth = 0
var int issue68GCTopChangedDirect = 0
var int issue68GCTopChangedIndirect = 0
var int issue68GCTopChangedBoth = 0

var float issue68GCSumProdDownGate = 0.0
var float issue68GCSumShadowDownGate = 0.0
var float issue68GCSumProdMdCont = 0.0
var float issue68GCSumShadowMdCont = 0.0
var float issue68GCSumProdNonMdGate = 0.0
var float issue68GCSumShadowNonMdGate = 0.0
var int issue68GCProdDownWinsMax = 0
var int issue68GCShadowDownWinsMax = 0

if issue68GCValid
    issue68GCN += 1
    issue68GCSumGateProd += issue68GCGateProd
    issue68GCSumGateDirect += issue68GCGateDirect
    issue68GCSumGateIndirect += issue68GCGateIndirect
    issue68GCSumGateBoth += issue68GCGateBoth
    issue68GCSumEffProd += issue68GCEffProd
    issue68GCSumEffDirect += issue68GCEffDirect
    issue68GCSumEffIndirect += issue68GCEffIndirect
    issue68GCSumEffBoth += issue68GCEffBoth

    issue68GCS2OverProd += markupEff > issue68GCEffProd ? 1 : 0
    issue68GCS2OverDirect += markupEff > issue68GCEffDirect ? 1 : 0
    issue68GCS2OverIndirect += markupEff > issue68GCEffIndirect ? 1 : 0
    issue68GCS2OverBoth += markupEff > issue68GCEffBoth ? 1 : 0

    issue68GCS1TopProd += issue68GCTopProd == 1 ? 1 : 0
    issue68GCS1TopDirect += issue68GCTopDirect == 1 ? 1 : 0
    issue68GCS1TopIndirect += issue68GCTopIndirect == 1 ? 1 : 0
    issue68GCS1TopBoth += issue68GCTopBoth == 1 ? 1 : 0

    issue68GCBullTopProd += issue68GCBullProd ? 1 : 0
    issue68GCBullTopDirect += issue68GCBullDirect ? 1 : 0
    issue68GCBullTopIndirect += issue68GCBullIndirect ? 1 : 0
    issue68GCBullTopBoth += issue68GCBullBoth ? 1 : 0

    issue68GCTopChangedDirect += issue68GCTopDirect != issue68GCTopProd ? 1 : 0
    issue68GCTopChangedIndirect += issue68GCTopIndirect != issue68GCTopProd ? 1 : 0
    issue68GCTopChangedBoth += issue68GCTopBoth != issue68GCTopProd ? 1 : 0

    issue68GCSumProdDownGate += downsideExhaustionGate
    issue68GCSumShadowDownGate += issue68SIDownExGate
    issue68GCSumProdMdCont += markdownContinuationScore
    issue68GCSumShadowMdCont += issue68SIMarkdownContinuationScore
    issue68GCSumProdNonMdGate += nonMarkdownContinuationGate
    issue68GCSumShadowNonMdGate += issue68SINonMarkdownContinuationGate
    issue68GCProdDownWinsMax += downsideExhaustion > supportHolding ? 1 : 0
    issue68GCShadowDownWinsMax += issue68SIDownEx > supportHolding ? 1 : 0

float issue68GCAvgGateProd = f_issue68SIAvg(issue68GCSumGateProd, issue68GCN)
float issue68GCAvgGateDirect = f_issue68SIAvg(issue68GCSumGateDirect, issue68GCN)
float issue68GCAvgGateIndirect = f_issue68SIAvg(issue68GCSumGateIndirect, issue68GCN)
float issue68GCAvgGateBoth = f_issue68SIAvg(issue68GCSumGateBoth, issue68GCN)
float issue68GCAvgEffProd = f_issue68SIAvg(issue68GCSumEffProd, issue68GCN)
float issue68GCAvgEffDirect = f_issue68SIAvg(issue68GCSumEffDirect, issue68GCN)
float issue68GCAvgEffIndirect = f_issue68SIAvg(issue68GCSumEffIndirect, issue68GCN)
float issue68GCAvgEffBoth = f_issue68SIAvg(issue68GCSumEffBoth, issue68GCN)

float issue68GCDirectContribution = issue68GCAvgEffDirect - issue68GCAvgEffProd
float issue68GCIndirectContribution = issue68GCAvgEffIndirect - issue68GCAvgEffProd
float issue68GCTotalContribution = issue68GCAvgEffBoth - issue68GCAvgEffProd
float issue68GCInteraction = issue68GCTotalContribution - issue68GCDirectContribution - issue68GCIndirectContribution

plot(issue68SIInWindow ? 3.0 : na, "EXPECTED Bull", color=colGreen, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68GCValid ? 2.0 : na, "DIRECT-only S2>S1", color=markupEff > issue68GCEffDirect ? colGreen : colRed, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68GCValid ? 1.0 : na, "INDIRECT-only S2>S1", color=markupEff > issue68GCEffIndirect ? colGreen : colRed, linewidth=4, style=plot.style_linebr, display=display.pane)

var table tGC = table.new(position.middle_right, 5, 18, border_width=1)
if barstate.islast
    if showIssue68GCTable
        table.cell(tGC, 0, 0, "DOWNEX GATE CHANNELS", bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 1, 0, "PROD", bgcolor=colRed, text_color=color.white)
        table.cell(tGC, 2, 0, "DIRECT", bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 3, 0, "INDIRECT", bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 4, 0, "BOTH", bgcolor=colGreen, text_color=color.white)

        table.cell(tGC, 0, 1, "Population", bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 1, 1, str.tostring(issue68GCN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 2, 1, "same", bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 3, 1, "same", bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 4, 1, "same", bgcolor=colNeutral, text_color=color.white)

        table.cell(tGC, 0, 2, "S1 gate avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 1, 2, f_issue68SIFmt(issue68GCAvgGateProd), bgcolor=colRed, text_color=color.white)
        table.cell(tGC, 2, 2, f_issue68SIFmt(issue68GCAvgGateDirect), bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 3, 2, f_issue68SIFmt(issue68GCAvgGateIndirect), bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 4, 2, f_issue68SIFmt(issue68GCAvgGateBoth), bgcolor=colGreen, text_color=color.white)

        table.cell(tGC, 0, 3, "S1 EFF avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 1, 3, f_issue68SIFmt(issue68GCAvgEffProd), bgcolor=colRed, text_color=color.white)
        table.cell(tGC, 2, 3, f_issue68SIFmt(issue68GCAvgEffDirect), bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 3, 3, f_issue68SIFmt(issue68GCAvgEffIndirect), bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 4, 3, f_issue68SIFmt(issue68GCAvgEffBoth), bgcolor=colGreen, text_color=color.white)

        table.cell(tGC, 0, 4, "S2 EFF > S1", bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 1, 4, f_issue68SIFmtPct(issue68GCS2OverProd, issue68GCN), bgcolor=colRed, text_color=color.white)
        table.cell(tGC, 2, 4, f_issue68SIFmtPct(issue68GCS2OverDirect, issue68GCN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 3, 4, f_issue68SIFmtPct(issue68GCS2OverIndirect, issue68GCN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 4, 4, f_issue68SIFmtPct(issue68GCS2OverBoth, issue68GCN), bgcolor=colGreen, text_color=color.white)

        table.cell(tGC, 0, 5, "S1 TOP", bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 1, 5, f_issue68SIFmtPct(issue68GCS1TopProd, issue68GCN), bgcolor=colRed, text_color=color.white)
        table.cell(tGC, 2, 5, f_issue68SIFmtPct(issue68GCS1TopDirect, issue68GCN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 3, 5, f_issue68SIFmtPct(issue68GCS1TopIndirect, issue68GCN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 4, 5, f_issue68SIFmtPct(issue68GCS1TopBoth, issue68GCN), bgcolor=colGreen, text_color=color.white)

        table.cell(tGC, 0, 6, "Bull TOP", bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 1, 6, f_issue68SIFmtPct(issue68GCBullTopProd, issue68GCN), bgcolor=colRed, text_color=color.white)
        table.cell(tGC, 2, 6, f_issue68SIFmtPct(issue68GCBullTopDirect, issue68GCN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 3, 6, f_issue68SIFmtPct(issue68GCBullTopIndirect, issue68GCN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 4, 6, f_issue68SIFmtPct(issue68GCBullTopBoth, issue68GCN), bgcolor=colGreen, text_color=color.white)

        table.cell(tGC, 0, 7, "TOP changed", bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 1, 7, "0%", bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 2, 7, f_issue68SIFmtPct(issue68GCTopChangedDirect, issue68GCN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 3, 7, f_issue68SIFmtPct(issue68GCTopChangedIndirect, issue68GCN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 4, 7, f_issue68SIFmtPct(issue68GCTopChangedBoth, issue68GCN), bgcolor=colGreen, text_color=color.white)

        table.cell(tGC, 0, 8, "CHANNEL INPUTS", bgcolor=colGreen, text_color=color.white)
        table.cell(tGC, 1, 8, "PROD", bgcolor=colGreen, text_color=color.white)
        table.cell(tGC, 2, 8, "SHADOW", bgcolor=colGreen, text_color=color.white)
        table.cell(tGC, 3, 8, "DELTA", bgcolor=colGreen, text_color=color.white)
        table.cell(tGC, 4, 8, "ROLE", bgcolor=colGreen, text_color=color.white)

        float issue68GCProdDownGateAvg = f_issue68SIAvg(issue68GCSumProdDownGate, issue68GCN)
        float issue68GCShadowDownGateAvg = f_issue68SIAvg(issue68GCSumShadowDownGate, issue68GCN)
        float issue68GCProdMdContAvg = f_issue68SIAvg(issue68GCSumProdMdCont, issue68GCN)
        float issue68GCShadowMdContAvg = f_issue68SIAvg(issue68GCSumShadowMdCont, issue68GCN)
        float issue68GCProdNonMdAvg = f_issue68SIAvg(issue68GCSumProdNonMdGate, issue68GCN)
        float issue68GCShadowNonMdAvg = f_issue68SIAvg(issue68GCSumShadowNonMdGate, issue68GCN)

        table.cell(tGC, 0, 9, "DownEx gate", bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 1, 9, f_issue68SIFmt(issue68GCProdDownGateAvg), bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 2, 9, f_issue68SIFmt(issue68GCShadowDownGateAvg), bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 3, 9, f_issue68SIFmt(issue68GCShadowDownGateAvg - issue68GCProdDownGateAvg), bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 4, 9, "DIRECT", bgcolor=colNeutral, text_color=color.white)

        table.cell(tGC, 0, 10, "Markdown cont score", bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 1, 10, f_issue68SIFmt(issue68GCProdMdContAvg), bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 2, 10, f_issue68SIFmt(issue68GCShadowMdContAvg), bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 3, 10, f_issue68SIFmt(issue68GCShadowMdContAvg - issue68GCProdMdContAvg), bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 4, 10, "INDIRECT mid", bgcolor=colNeutral, text_color=color.white)

        table.cell(tGC, 0, 11, "Non-MD gate", bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 1, 11, f_issue68SIFmt(issue68GCProdNonMdAvg), bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 2, 11, f_issue68SIFmt(issue68GCShadowNonMdAvg), bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 3, 11, f_issue68SIFmt(issue68GCShadowNonMdAvg - issue68GCProdNonMdAvg), bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 4, 11, "INDIRECT gate", bgcolor=colNeutral, text_color=color.white)

        table.cell(tGC, 0, 12, "DownEx > Support", bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 1, 12, f_issue68SIFmtPct(issue68GCProdDownWinsMax, issue68GCN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 2, 12, f_issue68SIFmtPct(issue68GCShadowDownWinsMax, issue68GCN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 3, 12, "max() active", bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 4, 12, "indirect exposure", bgcolor=colNeutral, text_color=color.white)

        table.cell(tGC, 0, 13, "DECOMPOSITION", bgcolor=colGreen, text_color=color.white)
        table.cell(tGC, 1, 13, "DIRECT", bgcolor=colGreen, text_color=color.white)
        table.cell(tGC, 2, 13, "INDIRECT", bgcolor=colGreen, text_color=color.white)
        table.cell(tGC, 3, 13, "INTERACTION", bgcolor=colGreen, text_color=color.white)
        table.cell(tGC, 4, 13, "TOTAL", bgcolor=colGreen, text_color=color.white)

        table.cell(tGC, 0, 14, "Delta avg S1 EFF", bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 1, 14, f_issue68SIFmt(issue68GCDirectContribution), bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 2, 14, f_issue68SIFmt(issue68GCIndirectContribution), bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 3, 14, f_issue68SIFmt(issue68GCInteraction), bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 4, 14, f_issue68SIFmt(issue68GCTotalContribution), bgcolor=colGreen, text_color=color.white)

        table.cell(tGC, 0, 15, "READ", bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 1, 15, "direct gate?", bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 2, 15, "continuation?", bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 3, 15, "interaction?", bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 4, 15, "NO TUNING", bgcolor=colRed, text_color=color.white)

        table.cell(tGC, 0, 16, "MODE", bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 1, 16, "DISCOVERY", bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 2, 16, "S1 RAW FROZEN", bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 3, 16, "OTHERS PROD", bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 4, 16, "FROZEN C-2", bgcolor=colNeutral, text_color=color.white)

        table.cell(tGC, 0, 17, "TARGET", bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 1, 17, "FR10Y", bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 2, 17, "vs", bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 3, 17, "DE10Y", bgcolor=colNeutral, text_color=color.white)
        table.cell(tGC, 4, 17, "2022-23", bgcolor=colNeutral, text_color=color.white)
    else
        table.clear(tGC, 0, 0, 4, 17)
'''


def generate(source: Path) -> str:
    d1_text = si.phase_b.d1.generate(source)
    if d1_text.count(si.phase_b.D1_EXPORT_MARKER) != 1:
        raise RuntimeError("expected exactly one D1 parity export marker")
    core = d1_text.split(si.phase_b.D1_EXPORT_MARKER, 1)[0].rstrip()
    core = replace_once(core, si.phase_b.D1_INDICATOR_DECL, AUDIT_DECL)

    si_body = si.BODY.replace(
        'showIssue68SITable = input.bool(true, "顯示 Support-Invariant Shadow 表", group=groupIssue68SI)',
        'showIssue68SITable = input.bool(false, "顯示 Support-Invariant Shadow 表", group=groupIssue68SI)',
    )
    out = core + "\n\n" + si_body + "\n" + BODY + "\n"

    for token in (
        "DownEx Gate-Channel Decomposition",
        "DIRECT",
        "INDIRECT",
        "DownEx > Support",
        "Delta avg S1 EFF",
        "S1 RAW FROZEN",
    ):
        if token not in out:
            raise RuntimeError(f"missing required gate-channel token: {token}")
    if "strategy.entry" in out or "strategy.close" in out:
        raise RuntimeError("gate-channel audit leaked strategy order logic")
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
