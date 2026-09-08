#!/usr/bin/env python3
"""Generate Issue #68 downside-exhaustion routing decomposition Pine."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_support_invariant_slope_shadow_pine as si
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 DownEx Routing Decomposition", shorttitle="ChaseRisk #68 DownEx Route", overlay=false, precision=3)'

BODY = r'''

// ============================================================================
// Issue #68 Downside-Exhaustion Routing Decomposition.
// Shared window: 2022-01-03 -> 2023-12-29, expected Bull yield regime.
// DISCOVERY ONLY. NO PNL. NO TUNING. PRODUCTION C-2 FROZEN.
// ============================================================================

groupIssue68Route = "Issue #68｜DownEx Routing Decomposition"
showIssue68RouteTable = input.bool(true, "顯示 DownEx Routing 表", group=groupIssue68Route)

f_issue68RouteTop(float accX) =>
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

float issue68RouteProdAccEff = accEff
float issue68RouteRawOnlyAccEff = issue68SIAccRaw * accGate * accVolMult * accMtfMult * accDivMult
float issue68RouteGateOnlyAccEff = accRaw * issue68SIAccGate * accVolMult * accMtfMult * accDivMult
float issue68RouteBothAccEff = issue68SIAccRaw * issue68SIAccGate * accVolMult * accMtfMult * accDivMult

bool issue68RouteValid = issue68SIValid and not na(issue68RouteRawOnlyAccEff) and not na(issue68RouteGateOnlyAccEff) and not na(issue68RouteBothAccEff)

int issue68RouteTopProd = topId
int issue68RouteTopRaw = issue68RouteValid ? f_issue68RouteTop(issue68RouteRawOnlyAccEff) : na
int issue68RouteTopGate = issue68RouteValid ? f_issue68RouteTop(issue68RouteGateOnlyAccEff) : na
int issue68RouteTopBoth = issue68RouteValid ? f_issue68RouteTop(issue68RouteBothAccEff) : na

bool issue68RouteBullProd = issue68RouteValid and (issue68RouteTopProd == 2 or issue68RouteTopProd == 3)
bool issue68RouteBullRaw = issue68RouteValid and (issue68RouteTopRaw == 2 or issue68RouteTopRaw == 3)
bool issue68RouteBullGate = issue68RouteValid and (issue68RouteTopGate == 2 or issue68RouteTopGate == 3)
bool issue68RouteBullBoth = issue68RouteValid and (issue68RouteTopBoth == 2 or issue68RouteTopBoth == 3)

var int issue68RouteN = 0
var float issue68RouteSumProdEff = 0.0
var float issue68RouteSumRawEff = 0.0
var float issue68RouteSumGateEff = 0.0
var float issue68RouteSumBothEff = 0.0
var float issue68RouteSumProdRaw = 0.0
var float issue68RouteSumShadowRaw = 0.0
var float issue68RouteSumProdGate = 0.0
var float issue68RouteSumShadowGate = 0.0

var int issue68RouteS2OverProd = 0
var int issue68RouteS2OverRaw = 0
var int issue68RouteS2OverGate = 0
var int issue68RouteS2OverBoth = 0
var int issue68RouteS1TopProd = 0
var int issue68RouteS1TopRaw = 0
var int issue68RouteS1TopGate = 0
var int issue68RouteS1TopBoth = 0
var int issue68RouteBullTopProd = 0
var int issue68RouteBullTopRaw = 0
var int issue68RouteBullTopGate = 0
var int issue68RouteBullTopBoth = 0
var int issue68RouteTopChangedRaw = 0
var int issue68RouteTopChangedGate = 0
var int issue68RouteTopChangedBoth = 0

if issue68RouteValid
    issue68RouteN += 1
    issue68RouteSumProdEff += issue68RouteProdAccEff
    issue68RouteSumRawEff += issue68RouteRawOnlyAccEff
    issue68RouteSumGateEff += issue68RouteGateOnlyAccEff
    issue68RouteSumBothEff += issue68RouteBothAccEff
    issue68RouteSumProdRaw += accRaw
    issue68RouteSumShadowRaw += issue68SIAccRaw
    issue68RouteSumProdGate += accGate
    issue68RouteSumShadowGate += issue68SIAccGate

    issue68RouteS2OverProd += markupEff > issue68RouteProdAccEff ? 1 : 0
    issue68RouteS2OverRaw += markupEff > issue68RouteRawOnlyAccEff ? 1 : 0
    issue68RouteS2OverGate += markupEff > issue68RouteGateOnlyAccEff ? 1 : 0
    issue68RouteS2OverBoth += markupEff > issue68RouteBothAccEff ? 1 : 0

    issue68RouteS1TopProd += issue68RouteTopProd == 1 ? 1 : 0
    issue68RouteS1TopRaw += issue68RouteTopRaw == 1 ? 1 : 0
    issue68RouteS1TopGate += issue68RouteTopGate == 1 ? 1 : 0
    issue68RouteS1TopBoth += issue68RouteTopBoth == 1 ? 1 : 0

    issue68RouteBullTopProd += issue68RouteBullProd ? 1 : 0
    issue68RouteBullTopRaw += issue68RouteBullRaw ? 1 : 0
    issue68RouteBullTopGate += issue68RouteBullGate ? 1 : 0
    issue68RouteBullTopBoth += issue68RouteBullBoth ? 1 : 0

    issue68RouteTopChangedRaw += issue68RouteTopRaw != issue68RouteTopProd ? 1 : 0
    issue68RouteTopChangedGate += issue68RouteTopGate != issue68RouteTopProd ? 1 : 0
    issue68RouteTopChangedBoth += issue68RouteTopBoth != issue68RouteTopProd ? 1 : 0

float issue68RouteAvgProdEff = f_issue68SIAvg(issue68RouteSumProdEff, issue68RouteN)
float issue68RouteAvgRawEff = f_issue68SIAvg(issue68RouteSumRawEff, issue68RouteN)
float issue68RouteAvgGateEff = f_issue68SIAvg(issue68RouteSumGateEff, issue68RouteN)
float issue68RouteAvgBothEff = f_issue68SIAvg(issue68RouteSumBothEff, issue68RouteN)
float issue68RouteRawContribution = issue68RouteAvgRawEff - issue68RouteAvgProdEff
float issue68RouteGateContribution = issue68RouteAvgGateEff - issue68RouteAvgProdEff
float issue68RouteTotal = issue68RouteAvgBothEff - issue68RouteAvgProdEff
float issue68RouteInteraction = issue68RouteTotal - issue68RouteRawContribution - issue68RouteGateContribution

plot(issue68SIInWindow ? 3.0 : na, "EXPECTED Bull", color=colGreen, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68RouteValid ? 2.0 : na, "RAW-only S2>S1", color=markupEff > issue68RouteRawOnlyAccEff ? colGreen : colRed, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68RouteValid ? 1.0 : na, "Gate-only S2>S1", color=markupEff > issue68RouteGateOnlyAccEff ? colGreen : colRed, linewidth=4, style=plot.style_linebr, display=display.pane)

var table tRoute = table.new(position.middle_right, 5, 15, border_width=1)
if barstate.islast
    if showIssue68RouteTable
        table.cell(tRoute, 0, 0, "DOWNEX ROUTING", bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 1, 0, "PROD", bgcolor=colRed, text_color=color.white)
        table.cell(tRoute, 2, 0, "RAW-ONLY", bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 3, 0, "GATE-ONLY", bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 4, 0, "BOTH", bgcolor=colGreen, text_color=color.white)

        table.cell(tRoute, 0, 1, "Population", bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 1, 1, str.tostring(issue68RouteN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 2, 1, "same", bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 3, 1, "same", bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 4, 1, "same", bgcolor=colNeutral, text_color=color.white)

        table.cell(tRoute, 0, 2, "S1 EFF avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 1, 2, f_issue68SIFmt(issue68RouteAvgProdEff), bgcolor=colRed, text_color=color.white)
        table.cell(tRoute, 2, 2, f_issue68SIFmt(issue68RouteAvgRawEff), bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 3, 2, f_issue68SIFmt(issue68RouteAvgGateEff), bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 4, 2, f_issue68SIFmt(issue68RouteAvgBothEff), bgcolor=colGreen, text_color=color.white)

        table.cell(tRoute, 0, 3, "Delta S1 EFF", bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 1, 3, "0", bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 2, 3, f_issue68SIFmt(issue68RouteRawContribution), bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 3, 3, f_issue68SIFmt(issue68RouteGateContribution), bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 4, 3, f_issue68SIFmt(issue68RouteTotal), bgcolor=colGreen, text_color=color.white)

        table.cell(tRoute, 0, 4, "S2 EFF > S1", bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 1, 4, f_issue68SIFmtPct(issue68RouteS2OverProd, issue68RouteN), bgcolor=colRed, text_color=color.white)
        table.cell(tRoute, 2, 4, f_issue68SIFmtPct(issue68RouteS2OverRaw, issue68RouteN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 3, 4, f_issue68SIFmtPct(issue68RouteS2OverGate, issue68RouteN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 4, 4, f_issue68SIFmtPct(issue68RouteS2OverBoth, issue68RouteN), bgcolor=colGreen, text_color=color.white)

        table.cell(tRoute, 0, 5, "S1 TOP", bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 1, 5, f_issue68SIFmtPct(issue68RouteS1TopProd, issue68RouteN), bgcolor=colRed, text_color=color.white)
        table.cell(tRoute, 2, 5, f_issue68SIFmtPct(issue68RouteS1TopRaw, issue68RouteN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 3, 5, f_issue68SIFmtPct(issue68RouteS1TopGate, issue68RouteN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 4, 5, f_issue68SIFmtPct(issue68RouteS1TopBoth, issue68RouteN), bgcolor=colGreen, text_color=color.white)

        table.cell(tRoute, 0, 6, "Bull TOP", bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 1, 6, f_issue68SIFmtPct(issue68RouteBullTopProd, issue68RouteN), bgcolor=colRed, text_color=color.white)
        table.cell(tRoute, 2, 6, f_issue68SIFmtPct(issue68RouteBullTopRaw, issue68RouteN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 3, 6, f_issue68SIFmtPct(issue68RouteBullTopGate, issue68RouteN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 4, 6, f_issue68SIFmtPct(issue68RouteBullTopBoth, issue68RouteN), bgcolor=colGreen, text_color=color.white)

        table.cell(tRoute, 0, 7, "TOP changed", bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 1, 7, "0%", bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 2, 7, f_issue68SIFmtPct(issue68RouteTopChangedRaw, issue68RouteN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 3, 7, f_issue68SIFmtPct(issue68RouteTopChangedGate, issue68RouteN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 4, 7, f_issue68SIFmtPct(issue68RouteTopChangedBoth, issue68RouteN), bgcolor=colGreen, text_color=color.white)

        table.cell(tRoute, 0, 8, "ROUTING INPUTS", bgcolor=colGreen, text_color=color.white)
        table.cell(tRoute, 1, 8, "PROD", bgcolor=colGreen, text_color=color.white)
        table.cell(tRoute, 2, 8, "SHADOW", bgcolor=colGreen, text_color=color.white)
        table.cell(tRoute, 3, 8, "ROLE", bgcolor=colGreen, text_color=color.white)
        table.cell(tRoute, 4, 8, "READ", bgcolor=colGreen, text_color=color.white)

        table.cell(tRoute, 0, 9, "S1 RAW avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 1, 9, f_issue68SIFmt(f_issue68SIAvg(issue68RouteSumProdRaw, issue68RouteN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 2, 9, f_issue68SIFmt(f_issue68SIAvg(issue68RouteSumShadowRaw, issue68RouteN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 3, 9, "evidence", bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 4, 9, "RAW route", bgcolor=colNeutral, text_color=color.white)

        table.cell(tRoute, 0, 10, "S1 gate avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 1, 10, f_issue68SIFmt(f_issue68SIAvg(issue68RouteSumProdGate, issue68RouteN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 2, 10, f_issue68SIFmt(f_issue68SIAvg(issue68RouteSumShadowGate, issue68RouteN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 3, 10, "multiplier", bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 4, 10, "Gate route", bgcolor=colNeutral, text_color=color.white)

        table.cell(tRoute, 0, 11, "DECOMPOSITION", bgcolor=colGreen, text_color=color.white)
        table.cell(tRoute, 1, 11, "RAW", bgcolor=colGreen, text_color=color.white)
        table.cell(tRoute, 2, 11, "GATE", bgcolor=colGreen, text_color=color.white)
        table.cell(tRoute, 3, 11, "INTERACTION", bgcolor=colGreen, text_color=color.white)
        table.cell(tRoute, 4, 11, "TOTAL", bgcolor=colGreen, text_color=color.white)

        table.cell(tRoute, 0, 12, "Delta avg S1 EFF", bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 1, 12, f_issue68SIFmt(issue68RouteRawContribution), bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 2, 12, f_issue68SIFmt(issue68RouteGateContribution), bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 3, 12, f_issue68SIFmt(issue68RouteInteraction), bgcolor=math.abs(issue68RouteInteraction) > math.abs(issue68RouteRawContribution) and math.abs(issue68RouteInteraction) > math.abs(issue68RouteGateContribution) ? colRed : colNeutral, text_color=color.white)
        table.cell(tRoute, 4, 12, f_issue68SIFmt(issue68RouteTotal), bgcolor=colGreen, text_color=color.white)

        table.cell(tRoute, 0, 13, "READ", bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 1, 13, "RAW semantic?", bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 2, 13, "Gate amplify?", bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 3, 13, "double-route?", bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 4, 13, "NO TUNING", bgcolor=colRed, text_color=color.white)

        table.cell(tRoute, 0, 14, "MODE", bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 1, 14, "DISCOVERY", bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 2, 14, "S1 ONLY", bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 3, 14, "FROZEN OTHERS", bgcolor=colNeutral, text_color=color.white)
        table.cell(tRoute, 4, 14, "FROZEN C-2", bgcolor=colNeutral, text_color=color.white)
    else
        table.clear(tRoute, 0, 0, 4, 14)
'''


def generate(source: Path) -> str:
    out = si.generate(source)
    out = replace_once(out, si.AUDIT_DECL, AUDIT_DECL)
    out = replace_once(
        out,
        'showIssue68SITable = input.bool(true, "顯示 Support-Invariant Shadow 表", group=groupIssue68SI)',
        'showIssue68SITable = input.bool(false, "顯示 Support-Invariant Shadow 表", group=groupIssue68SI)',
    )
    out = out.rstrip() + BODY + "\n"
    for token in (
        "Downside-Exhaustion Routing Decomposition",
        "RAW-ONLY",
        "GATE-ONLY",
        "Delta avg S1 EFF",
        "double-route?",
        "S1 ONLY",
    ):
        if token not in out:
            raise RuntimeError(f"missing required routing token: {token}")
    if "strategy.entry" in out or "strategy.close" in out:
        raise RuntimeError("routing decomposition leaked strategy order logic")
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
