#!/usr/bin/env python3
"""Generate Issue #68 B3.10 S5-vs-S2 local duel audit Pine."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_phase_b_lifecycle_pine as phase_b
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 B3.10 S5 vs S2 Duel", shorttitle="ChaseRisk #68 B310", overlay=false, precision=2)'

B310_BODY = r'''

// ============================================================================
// Issue #66 C-2 runtime-validated price-only lineage.
// Issue #68 B3.10 exact S2 Markup vs S5 Markdown raw0 duel audit only.
// No classifier formula, weight, threshold, gate, persistence, Core Bias,
// Exposure, or strategy change.
// ============================================================================

groupIssue68B310 = "Issue #68｜B3.10 S5 vs S2 Duel"
showIssue68B310Legend = input.bool(true, "顯示右上角狀態表", group=groupIssue68B310)
issue68B310Ready = bar_index >= rankLen - 1

f_issue68B310PassColor(int x) => x == 1 ? colGreen : x == -1 ? colRed : colNeutral
f_issue68B310PassText(int x) => x == 1 ? "S2" : x == -1 ? "S5" : "TIE"
f_issue68B310BandColor(int x) => color.new(f_issue68B310PassColor(x), x == 0 ? 68 : 18)

float issue68B310Break = 0.17 * (breakoutScore - explicitBreakdownScore)
float issue68B310Heat = 0.17 * (heatUp - panicHeatDn)
float issue68B310Structure = 0.17 * (structureStrong - structureWeak)
float issue68B310Extension = 0.2125 * (markupExtensionScore - markdownExtensionScore)
float issue68B310Continuation = 0.1275 * (markupContinuationScore - markdownContinuationScore)
float issue68B310Trace = 0.15 * (accTraceForMarkup - distTraceForMarkdown)
float issue68B310Direct = issue68B310Break + issue68B310Heat + issue68B310Structure + issue68B310Extension + issue68B310Continuation + issue68B310Trace

f_issue68B310Sign(float x) => not issue68B310Ready ? 0 : x > 0 ? 1 : x < 0 ? -1 : 0

int issue68B310RawEdge = f_issue68B310Sign(issue68B310Direct)
int issue68B310BreakEdge = f_issue68B310Sign(issue68B310Break)
int issue68B310HeatEdge = f_issue68B310Sign(issue68B310Heat)
int issue68B310StructureEdge = f_issue68B310Sign(issue68B310Structure)
int issue68B310ExtensionEdge = f_issue68B310Sign(issue68B310Extension)
int issue68B310ContinuationEdge = f_issue68B310Sign(issue68B310Continuation)
int issue68B310TraceEdge = f_issue68B310Sign(issue68B310Trace)

f_issue68B310LargestNegativeName() =>
    float v = issue68B310Break
    string name = "BREAK"
    if issue68B310Heat < v
        v := issue68B310Heat
        name := "HEAT"
    if issue68B310Structure < v
        v := issue68B310Structure
        name := "STRUCTURE"
    if issue68B310Extension < v
        v := issue68B310Extension
        name := "EXTENSION"
    if issue68B310Continuation < v
        v := issue68B310Continuation
        name := "CONT"
    if issue68B310Trace < v
        v := issue68B310Trace
        name := "TRACE"
    v < 0 ? name : "NONE"

float issue68B310Half = 0.34
float cRaw = 6.0
float cBreak = 5.0
float cHeat = 4.0
float cStructure = 3.0
float cExtension = 2.0
float cContinuation = 1.0
float cTrace = 0.0

pRawHi = plot(issue68B310Ready ? cRaw + issue68B310Half : na, "B310 S2>S5 RAW top", color=color.new(colNeutral, 100), display=display.pane)
pRawLo = plot(issue68B310Ready ? cRaw - issue68B310Half : na, "B310 S2>S5 RAW bottom", color=color.new(colNeutral, 100), display=display.pane)
pBreakHi = plot(issue68B310Ready ? cBreak + issue68B310Half : na, "B310 BREAK top", color=color.new(colNeutral, 100), display=display.pane)
pBreakLo = plot(issue68B310Ready ? cBreak - issue68B310Half : na, "B310 BREAK bottom", color=color.new(colNeutral, 100), display=display.pane)
pHeatHi = plot(issue68B310Ready ? cHeat + issue68B310Half : na, "B310 HEAT top", color=color.new(colNeutral, 100), display=display.pane)
pHeatLo = plot(issue68B310Ready ? cHeat - issue68B310Half : na, "B310 HEAT bottom", color=color.new(colNeutral, 100), display=display.pane)
pStructureHi = plot(issue68B310Ready ? cStructure + issue68B310Half : na, "B310 STRUCTURE top", color=color.new(colNeutral, 100), display=display.pane)
pStructureLo = plot(issue68B310Ready ? cStructure - issue68B310Half : na, "B310 STRUCTURE bottom", color=color.new(colNeutral, 100), display=display.pane)
pExtensionHi = plot(issue68B310Ready ? cExtension + issue68B310Half : na, "B310 EXTENSION top", color=color.new(colNeutral, 100), display=display.pane)
pExtensionLo = plot(issue68B310Ready ? cExtension - issue68B310Half : na, "B310 EXTENSION bottom", color=color.new(colNeutral, 100), display=display.pane)
pContinuationHi = plot(issue68B310Ready ? cContinuation + issue68B310Half : na, "B310 CONTINUATION top", color=color.new(colNeutral, 100), display=display.pane)
pContinuationLo = plot(issue68B310Ready ? cContinuation - issue68B310Half : na, "B310 CONTINUATION bottom", color=color.new(colNeutral, 100), display=display.pane)
pTraceHi = plot(issue68B310Ready ? cTrace + issue68B310Half : na, "B310 TRACE top", color=color.new(colNeutral, 100), display=display.pane)
pTraceLo = plot(issue68B310Ready ? cTrace - issue68B310Half : na, "B310 TRACE bottom", color=color.new(colNeutral, 100), display=display.pane)

fill(pRawHi, pRawLo, color=issue68B310Ready ? f_issue68B310BandColor(issue68B310RawEdge) : na, title="B310 S2>S5 RAW band")
fill(pBreakHi, pBreakLo, color=issue68B310Ready ? f_issue68B310BandColor(issue68B310BreakEdge) : na, title="B310 BREAK EDGE band")
fill(pHeatHi, pHeatLo, color=issue68B310Ready ? f_issue68B310BandColor(issue68B310HeatEdge) : na, title="B310 HEAT EDGE band")
fill(pStructureHi, pStructureLo, color=issue68B310Ready ? f_issue68B310BandColor(issue68B310StructureEdge) : na, title="B310 STRUCTURE EDGE band")
fill(pExtensionHi, pExtensionLo, color=issue68B310Ready ? f_issue68B310BandColor(issue68B310ExtensionEdge) : na, title="B310 EXTENSION EDGE band")
fill(pContinuationHi, pContinuationLo, color=issue68B310Ready ? f_issue68B310BandColor(issue68B310ContinuationEdge) : na, title="B310 CONTINUATION EDGE band")
fill(pTraceHi, pTraceLo, color=issue68B310Ready ? f_issue68B310BandColor(issue68B310TraceEdge) : na, title="B310 TRACE EDGE band")

var table issue68B310Legend = table.new(position.top_right, 2, 10, border_width=1)
if barstate.islast
    if showIssue68B310Legend
        table.cell(issue68B310Legend, 0, 0, "LAYER", text_color=color.white, bgcolor=color.new(colNeutral, 15))
        table.cell(issue68B310Legend, 1, 0, "NOW", text_color=color.white, bgcolor=color.new(colNeutral, 15))
        table.cell(issue68B310Legend, 0, 1, "RAW｜S2 vs S5", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B310Legend, 1, 1, f_issue68B310PassText(issue68B310RawEdge), text_color=color.white, bgcolor=f_issue68B310PassColor(issue68B310RawEdge))
        table.cell(issue68B310Legend, 0, 2, "BREAK", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B310Legend, 1, 2, f_issue68B310PassText(issue68B310BreakEdge), text_color=color.white, bgcolor=f_issue68B310PassColor(issue68B310BreakEdge))
        table.cell(issue68B310Legend, 0, 3, "HEAT", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B310Legend, 1, 3, f_issue68B310PassText(issue68B310HeatEdge), text_color=color.white, bgcolor=f_issue68B310PassColor(issue68B310HeatEdge))
        table.cell(issue68B310Legend, 0, 4, "STRUCTURE", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B310Legend, 1, 4, f_issue68B310PassText(issue68B310StructureEdge), text_color=color.white, bgcolor=f_issue68B310PassColor(issue68B310StructureEdge))
        table.cell(issue68B310Legend, 0, 5, "EXTENSION", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B310Legend, 1, 5, f_issue68B310PassText(issue68B310ExtensionEdge), text_color=color.white, bgcolor=f_issue68B310PassColor(issue68B310ExtensionEdge))
        table.cell(issue68B310Legend, 0, 6, "CONTINUATION", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B310Legend, 1, 6, f_issue68B310PassText(issue68B310ContinuationEdge), text_color=color.white, bgcolor=f_issue68B310PassColor(issue68B310ContinuationEdge))
        table.cell(issue68B310Legend, 0, 7, "TRACE", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B310Legend, 1, 7, f_issue68B310PassText(issue68B310TraceEdge), text_color=color.white, bgcolor=f_issue68B310PassColor(issue68B310TraceEdge))
        table.cell(issue68B310Legend, 0, 8, "LARGEST S5 EDGE", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B310Legend, 1, 8, f_issue68B310LargestNegativeName(), text_color=color.white, bgcolor=color.new(colNeutral, 15))
        table.cell(issue68B310Legend, 0, 9, "NOTE", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B310Legend, 1, 9, "綠=S2｜紅=S5", text_color=color.white, bgcolor=color.new(colNeutral, 15))
    else
        table.clear(issue68B310Legend, 0, 0, 1, 9)

plot(issue68B310Direct, "B310 S2-S5 raw0 reconstructed delta", display=display.data_window)
plot(issue68B310Break, "B310 break weighted edge", display=display.data_window)
plot(issue68B310Heat, "B310 heat weighted edge", display=display.data_window)
plot(issue68B310Structure, "B310 structure weighted edge", display=display.data_window)
plot(issue68B310Extension, "B310 extension weighted edge", display=display.data_window)
plot(issue68B310Continuation, "B310 continuation weighted edge", display=display.data_window)
plot(issue68B310Trace, "B310 trace weighted edge", display=display.data_window)
'''.strip()


def generate(source: Path) -> str:
    d1_text = phase_b.d1.generate(source)
    if d1_text.count(phase_b.D1_EXPORT_MARKER) != 1:
        raise RuntimeError("expected exactly one D1 parity export marker")
    core = d1_text.split(phase_b.D1_EXPORT_MARKER, 1)[0].rstrip()
    core = replace_once(core, phase_b.D1_INDICATOR_DECL, AUDIT_DECL)
    out = core + "\n\n" + B310_BODY + "\n"
    required = (
        "Issue #68 B3.10 exact S2 Markup vs S5 Markdown raw0 duel audit only",
        'volumeMode = "Off"',
        'mtfMode = "Off"',
        'divMode = "Off"',
        "B310 S2>S5 RAW band",
        "B310 BREAK EDGE band",
        "B310 HEAT EDGE band",
        "B310 STRUCTURE EDGE band",
        "B310 EXTENSION EDGE band",
        "B310 CONTINUATION EDGE band",
        "B310 TRACE EDGE band",
        "LARGEST S5 EDGE",
    )
    for token in required:
        if token not in out:
            raise RuntimeError(f"missing B3.10 audit token: {token}")
    for token in ("strategy.", "issue68B34A", "issue68B34B", "issue68B34C", "D1B|"):
        if token in out:
            raise RuntimeError(f"forbidden token leaked into B3.10 audit: {token}")
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
