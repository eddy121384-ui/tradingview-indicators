#!/usr/bin/env python3
"""Generate Issue #68 B3.8 raw feature attribution audit Pine."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_phase_b_lifecycle_pine as phase_b
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 B3.8 Raw Attribution", shorttitle="ChaseRisk #68 B38", overlay=false, precision=2)'

B38_BODY = r'''

// ============================================================================
// Issue #66 C-2 runtime-validated price-only lineage.
// Issue #68 B3.8 raw feature attribution audit only.
// No classifier weight, threshold, gate, persistence, Core Bias, Exposure, or strategy change.
// ============================================================================

groupIssue68B38 = "Issue #68｜B3.8 Raw Attribution"
issue68B38Direction = input.string("Bull", "審計方向", options=["Bull", "Bear"], group=groupIssue68B38)
showIssue68B38Legend = input.bool(true, "顯示右上角狀態表", group=groupIssue68B38)

issue68B38Ready = bar_index >= rankLen - 1
bool issue68B38Bull = issue68B38Direction == "Bull"

f_issue68B38PassColor(int x) => x == 1 ? colGreen : x == -1 ? colRed : colNeutral
f_issue68B38PassText(int x) => x == 1 ? "YES" : x == -1 ? "NO" : "N/A"
f_issue68B38BandColor(int x) => color.new(f_issue68B38PassColor(x), x == 0 ? 68 : 18)
f_issue68B38StageText(int id) => id == 1 ? "S1 Acc" : id == 2 ? "S2 Markup" : id == 3 ? "S3 Reacc" : id == 4 ? "S4 Dist" : id == 5 ? "S5 Markdown" : id == 6 ? "S6 Redist" : "N/A"

// Strict-greater Stage1->Stage6 priority, matching the classifier's TOP tie order.
f_issue68B38RawWinner() =>
    float v = accRaw
    int id = 1
    if markupRaw > v
        v := markupRaw
        id := 2
    if reaccRaw > v
        v := reaccRaw
        id := 3
    if distRaw > v
        v := distRaw
        id := 4
    if markdownRaw > v
        v := markdownRaw
        id := 5
    if redistRaw > v
        v := redistRaw
        id := 6
    [id, v]

[issue68B38RawWinner, issue68B38RawWinnerValue] = f_issue68B38RawWinner()
float issue68B38TargetRaw = issue68B38Bull ? math.max(markupRaw, reaccRaw) : math.max(markdownRaw, redistRaw)
float issue68B38RangeRaw = math.max(accRaw, distRaw)
float issue68B38OppTrendRaw = issue68B38Bull ? math.max(markdownRaw, redistRaw) : math.max(markupRaw, reaccRaw)

int issue68B38RawAdv = not issue68B38Ready ? 0 : (issue68B38TargetRaw > math.max(issue68B38RangeRaw, issue68B38OppTrendRaw) ? 1 : -1)
int issue68B38VsRange = not issue68B38Ready ? 0 : (issue68B38TargetRaw > issue68B38RangeRaw ? 1 : -1)
int issue68B38VsOppTrend = not issue68B38Ready ? 0 : (issue68B38TargetRaw > issue68B38OppTrendRaw ? 1 : -1)

// Exact mirrored Stage2-vs-Stage5 directional input edges. No threshold: only side-vs-mirror comparison.
int issue68B38BreakEdge = not issue68B38Ready ? 0 : (issue68B38Bull ? (breakoutScore > explicitBreakdownScore ? 1 : -1) : (explicitBreakdownScore > breakoutScore ? 1 : -1))
int issue68B38HeatEdge = not issue68B38Ready ? 0 : (issue68B38Bull ? (heatUp > panicHeatDn ? 1 : -1) : (panicHeatDn > heatUp ? 1 : -1))
int issue68B38StructureEdge = not issue68B38Ready ? 0 : (issue68B38Bull ? (structureStrong > structureWeak ? 1 : -1) : (structureWeak > structureStrong ? 1 : -1))
int issue68B38ExtensionEdge = not issue68B38Ready ? 0 : (issue68B38Bull ? (markupExtensionScore > markdownExtensionScore ? 1 : -1) : (markdownExtensionScore > markupExtensionScore ? 1 : -1))
int issue68B38ContinuationEdge = not issue68B38Ready ? 0 : (issue68B38Bull ? (markupContinuationScore > markdownContinuationScore ? 1 : -1) : (markdownContinuationScore > markupContinuationScore ? 1 : -1))
int issue68B38TraceEdge = not issue68B38Ready ? 0 : (issue68B38Bull ? (accTraceForMarkup > distTraceForMarkdown ? 1 : -1) : (distTraceForMarkdown > accTraceForMarkup ? 1 : -1))

float issue68B38Half = 0.34
float cRawAdv = 8.0
float cRange = 7.0
float cOppTrend = 6.0
float cBreak = 5.0
float cHeat = 4.0
float cStructure = 3.0
float cExtension = 2.0
float cContinuation = 1.0
float cTrace = 0.0

pRawAdvHi = plot(issue68B38Ready ? cRawAdv + issue68B38Half : na, "RAW ADV top", color=color.new(colNeutral, 100), display=display.pane)
pRawAdvLo = plot(issue68B38Ready ? cRawAdv - issue68B38Half : na, "RAW ADV bottom", color=color.new(colNeutral, 100), display=display.pane)
pRangeHi = plot(issue68B38Ready ? cRange + issue68B38Half : na, "TARGET RANGE top", color=color.new(colNeutral, 100), display=display.pane)
pRangeLo = plot(issue68B38Ready ? cRange - issue68B38Half : na, "TARGET RANGE bottom", color=color.new(colNeutral, 100), display=display.pane)
pOppHi = plot(issue68B38Ready ? cOppTrend + issue68B38Half : na, "TARGET OPP TREND top", color=color.new(colNeutral, 100), display=display.pane)
pOppLo = plot(issue68B38Ready ? cOppTrend - issue68B38Half : na, "TARGET OPP TREND bottom", color=color.new(colNeutral, 100), display=display.pane)
pBreakHi = plot(issue68B38Ready ? cBreak + issue68B38Half : na, "BREAK EDGE top", color=color.new(colNeutral, 100), display=display.pane)
pBreakLo = plot(issue68B38Ready ? cBreak - issue68B38Half : na, "BREAK EDGE bottom", color=color.new(colNeutral, 100), display=display.pane)
pHeatHi = plot(issue68B38Ready ? cHeat + issue68B38Half : na, "HEAT EDGE top", color=color.new(colNeutral, 100), display=display.pane)
pHeatLo = plot(issue68B38Ready ? cHeat - issue68B38Half : na, "HEAT EDGE bottom", color=color.new(colNeutral, 100), display=display.pane)
pStructureHi = plot(issue68B38Ready ? cStructure + issue68B38Half : na, "STRUCTURE EDGE top", color=color.new(colNeutral, 100), display=display.pane)
pStructureLo = plot(issue68B38Ready ? cStructure - issue68B38Half : na, "STRUCTURE EDGE bottom", color=color.new(colNeutral, 100), display=display.pane)
pExtensionHi = plot(issue68B38Ready ? cExtension + issue68B38Half : na, "EXTENSION EDGE top", color=color.new(colNeutral, 100), display=display.pane)
pExtensionLo = plot(issue68B38Ready ? cExtension - issue68B38Half : na, "EXTENSION EDGE bottom", color=color.new(colNeutral, 100), display=display.pane)
pContinuationHi = plot(issue68B38Ready ? cContinuation + issue68B38Half : na, "CONTINUATION EDGE top", color=color.new(colNeutral, 100), display=display.pane)
pContinuationLo = plot(issue68B38Ready ? cContinuation - issue68B38Half : na, "CONTINUATION EDGE bottom", color=color.new(colNeutral, 100), display=display.pane)
pTraceHi = plot(issue68B38Ready ? cTrace + issue68B38Half : na, "TRACE EDGE top", color=color.new(colNeutral, 100), display=display.pane)
pTraceLo = plot(issue68B38Ready ? cTrace - issue68B38Half : na, "TRACE EDGE bottom", color=color.new(colNeutral, 100), display=display.pane)

fill(pRawAdvHi, pRawAdvLo, color=issue68B38Ready ? f_issue68B38BandColor(issue68B38RawAdv) : na, title="RAW ADV band")
fill(pRangeHi, pRangeLo, color=issue68B38Ready ? f_issue68B38BandColor(issue68B38VsRange) : na, title="TARGET RANGE band")
fill(pOppHi, pOppLo, color=issue68B38Ready ? f_issue68B38BandColor(issue68B38VsOppTrend) : na, title="TARGET OPP TREND band")
fill(pBreakHi, pBreakLo, color=issue68B38Ready ? f_issue68B38BandColor(issue68B38BreakEdge) : na, title="BREAK EDGE band")
fill(pHeatHi, pHeatLo, color=issue68B38Ready ? f_issue68B38BandColor(issue68B38HeatEdge) : na, title="HEAT EDGE band")
fill(pStructureHi, pStructureLo, color=issue68B38Ready ? f_issue68B38BandColor(issue68B38StructureEdge) : na, title="STRUCTURE EDGE band")
fill(pExtensionHi, pExtensionLo, color=issue68B38Ready ? f_issue68B38BandColor(issue68B38ExtensionEdge) : na, title="EXTENSION EDGE band")
fill(pContinuationHi, pContinuationLo, color=issue68B38Ready ? f_issue68B38BandColor(issue68B38ContinuationEdge) : na, title="CONTINUATION EDGE band")
fill(pTraceHi, pTraceLo, color=issue68B38Ready ? f_issue68B38BandColor(issue68B38TraceEdge) : na, title="TRACE EDGE band")

var table issue68B38Legend = table.new(position.top_right, 2, 12, border_width=1)
if barstate.islast
    if showIssue68B38Legend
        table.cell(issue68B38Legend, 0, 0, "LAYER", text_color=color.white, bgcolor=color.new(colNeutral, 15))
        table.cell(issue68B38Legend, 1, 0, "NOW", text_color=color.white, bgcolor=color.new(colNeutral, 15))
        table.cell(issue68B38Legend, 0, 1, "TARGET｜審計方向", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B38Legend, 1, 1, issue68B38Direction, text_color=color.white, bgcolor=color.new(colNeutral, 15))
        table.cell(issue68B38Legend, 0, 2, "RAW WINNER｜原始冠軍", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B38Legend, 1, 2, f_issue68B38StageText(issue68B38RawWinner), text_color=color.white, bgcolor=color.new(colNeutral, 15))
        table.cell(issue68B38Legend, 0, 3, "RAW ADV｜目標 raw 最高", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B38Legend, 1, 3, f_issue68B38PassText(issue68B38RawAdv), text_color=color.white, bgcolor=f_issue68B38PassColor(issue68B38RawAdv))
        table.cell(issue68B38Legend, 0, 4, "> RANGE｜打贏 S1/S4", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B38Legend, 1, 4, f_issue68B38PassText(issue68B38VsRange), text_color=color.white, bgcolor=f_issue68B38PassColor(issue68B38VsRange))
        table.cell(issue68B38Legend, 0, 5, "> OPP TREND｜打贏反向趨勢", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B38Legend, 1, 5, f_issue68B38PassText(issue68B38VsOppTrend), text_color=color.white, bgcolor=f_issue68B38PassColor(issue68B38VsOppTrend))
        table.cell(issue68B38Legend, 0, 6, "BREAK｜突破證據", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B38Legend, 1, 6, f_issue68B38PassText(issue68B38BreakEdge), text_color=color.white, bgcolor=f_issue68B38PassColor(issue68B38BreakEdge))
        table.cell(issue68B38Legend, 0, 7, "HEAT｜方向熱度", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B38Legend, 1, 7, f_issue68B38PassText(issue68B38HeatEdge), text_color=color.white, bgcolor=f_issue68B38PassColor(issue68B38HeatEdge))
        table.cell(issue68B38Legend, 0, 8, "STRUCTURE｜結構", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B38Legend, 1, 8, f_issue68B38PassText(issue68B38StructureEdge), text_color=color.white, bgcolor=f_issue68B38PassColor(issue68B38StructureEdge))
        table.cell(issue68B38Legend, 0, 9, "EXTENSION｜趨勢延伸", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B38Legend, 1, 9, f_issue68B38PassText(issue68B38ExtensionEdge), text_color=color.white, bgcolor=f_issue68B38PassColor(issue68B38ExtensionEdge))
        table.cell(issue68B38Legend, 0, 10, "CONT｜整理後延續", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B38Legend, 1, 10, f_issue68B38PassText(issue68B38ContinuationEdge), text_color=color.white, bgcolor=f_issue68B38PassColor(issue68B38ContinuationEdge))
        table.cell(issue68B38Legend, 0, 11, "TRACE｜前置 Acc/Dist", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B38Legend, 1, 11, f_issue68B38PassText(issue68B38TraceEdge), text_color=color.white, bgcolor=f_issue68B38PassColor(issue68B38TraceEdge))
    else
        table.clear(issue68B38Legend, 0, 0, 1, 11)

plot(issue68B38TargetRaw, "B38 target raw", display=display.data_window)
plot(issue68B38RangeRaw, "B38 range raw", display=display.data_window)
plot(issue68B38OppTrendRaw, "B38 opposite trend raw", display=display.data_window)
plot(float(issue68B38RawWinner), "B38 raw winner stage", display=display.data_window)
plot(accRaw, "B38 S1 raw", display=display.data_window)
plot(markupRaw, "B38 S2 raw", display=display.data_window)
plot(reaccRaw, "B38 S3 raw", display=display.data_window)
plot(distRaw, "B38 S4 raw", display=display.data_window)
plot(markdownRaw, "B38 S5 raw", display=display.data_window)
plot(redistRaw, "B38 S6 raw", display=display.data_window)
plot(breakoutScore - explicitBreakdownScore, "B38 break directional delta", display=display.data_window)
plot(heatUp - panicHeatDn, "B38 heat directional delta", display=display.data_window)
plot(structureStrong - structureWeak, "B38 structure directional delta", display=display.data_window)
plot(markupExtensionScore - markdownExtensionScore, "B38 extension directional delta", display=display.data_window)
plot(markupContinuationScore - markdownContinuationScore, "B38 continuation directional delta", display=display.data_window)
plot(accTraceForMarkup - distTraceForMarkdown, "B38 trace directional delta", display=display.data_window)
'''.strip()


def generate(source: Path) -> str:
    d1_text = phase_b.d1.generate(source)
    if d1_text.count(phase_b.D1_EXPORT_MARKER) != 1:
        raise RuntimeError("expected exactly one D1 parity export marker")
    core = d1_text.split(phase_b.D1_EXPORT_MARKER, 1)[0].rstrip()
    core = replace_once(core, phase_b.D1_INDICATOR_DECL, AUDIT_DECL)
    out = core + "\n\n" + B38_BODY + "\n"
    required = (
        "Issue #66 C-2 runtime-validated price-only lineage",
        'volumeMode = "Off"',
        'mtfMode = "Off"',
        'divMode = "Off"',
        "RAW ADV band",
        "TARGET RANGE band",
        "TARGET OPP TREND band",
        "BREAK EDGE band",
        "HEAT EDGE band",
        "STRUCTURE EDGE band",
        "EXTENSION EDGE band",
        "CONTINUATION EDGE band",
        "TRACE EDGE band",
        "accTraceForMarkup > distTraceForMarkdown",
    )
    for token in required:
        if token not in out:
            raise RuntimeError(f"missing B3.8 audit token: {token}")
    for token in ("strategy.", "issue68B34A", "issue68B34B", "issue68B34C", "D1B|"):
        if token in out:
            raise RuntimeError(f"forbidden token leaked into B3.8 audit: {token}")
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
