#!/usr/bin/env python3
"""Generate Issue #68 B3.13 continuous Structure shadow TradingView audit."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_phase_b_lifecycle_pine as phase_b
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
DECL = 'indicator("Chase Risk Radar｜Issue #68 B3.13 Structure Shadow", shorttitle="ChaseRisk #68 B313", overlay=false, precision=2)'

BODY = r'''

// ============================================================================
// Issue #68 B3.13 diagnostic only.
// Single preregistered shadow replaces only the discrete S2-vs-S5 Structure
// edge with a continuous edge derived from existing distRank and
// maturityDistRank. Production C-2 is unchanged.
// ============================================================================
groupIssue68B313 = "Issue #68｜B3.13 Continuous Structure Shadow"
issue68B313Direction = input.string("Bull", "審計方向", options=["Bull", "Bear"], group=groupIssue68B313)
showIssue68B313Legend = input.bool(true, "顯示右上角狀態表", group=groupIssue68B313)
int issue68B313Dir = issue68B313Direction == "Bull" ? 1 : -1
bool issue68B313Ready = bar_index >= rankLen - 1

float issue68B313Break = 0.17 * (breakoutScore - explicitBreakdownScore)
float issue68B313Heat = 0.17 * (heatUp - panicHeatDn)
float issue68B313OldStructure = 0.17 * (structureStrong - structureWeak)
float issue68B313Extension = 0.2125 * (markupExtensionScore - markdownExtensionScore)
float issue68B313Continuation = 0.1275 * (markupContinuationScore - markdownContinuationScore)
float issue68B313Trace = 0.15 * (accTraceForMarkup - distTraceForMarkdown)
float issue68B313OldRaw = issue68B313Break + issue68B313Heat + issue68B313OldStructure + issue68B313Extension + issue68B313Continuation + issue68B313Trace
float issue68B313ContinuousStructureDelta = (distRank - 50.0) + (maturityDistRank - 50.0)
float issue68B313ContinuousStructure = 0.17 * issue68B313ContinuousStructureDelta
float issue68B313ShadowRaw = issue68B313OldRaw - issue68B313OldStructure + issue68B313ContinuousStructure

float issue68B313OldO = issue68B313Dir * issue68B313OldRaw
float issue68B313ShadowO = issue68B313Dir * issue68B313ShadowRaw
float issue68B313BreakO = issue68B313Dir * issue68B313Break
float issue68B313OldStructureO = issue68B313Dir * issue68B313OldStructure
float issue68B313ContinuousStructureO = issue68B313Dir * issue68B313ContinuousStructure

f_issue68B313Sign(float x) => not issue68B313Ready ? 0 : x > 0 ? 1 : x < 0 ? -1 : 0
f_issue68B313Color(int x) => x == 1 ? color.new(colGreen, 18) : x == -1 ? color.new(colRed, 18) : color.new(colNeutral, 68)
f_issue68B313Text(int x) => x == 1 ? "TARGET" : x == -1 ? "OLD SIDE" : "TIE"

int issue68B313OldSign = f_issue68B313Sign(issue68B313OldO)
int issue68B313ShadowSign = f_issue68B313Sign(issue68B313ShadowO)
int issue68B313BreakSign = f_issue68B313Sign(issue68B313BreakO)
int issue68B313OldStructureSign = f_issue68B313Sign(issue68B313OldStructureO)
int issue68B313ContinuousStructureSign = f_issue68B313Sign(issue68B313ContinuousStructureO)
int issue68B313Difference = not issue68B313Ready ? 0 : issue68B313ShadowO > 0 and issue68B313OldO <= 0 ? 1 : issue68B313OldO > 0 and issue68B313ShadowO <= 0 ? -1 : 0
bool issue68B313Handoff = issue68B313Ready and issue68B313OldO > 0 and issue68B313OldO[1] <= 0

float half = 0.34
float cOld = 6.0
float cShadow = 5.0
float cBreak = 4.0
float cOldStruct = 3.0
float cContStruct = 2.0
float cDiff = 1.0
float cHandoff = 0.0

pOldHi = plot(issue68B313Ready ? cOld + half : na, "B313 OLD RAW top", color=color.new(colNeutral, 100), display=display.pane)
pOldLo = plot(issue68B313Ready ? cOld - half : na, "B313 OLD RAW bottom", color=color.new(colNeutral, 100), display=display.pane)
pShadowHi = plot(issue68B313Ready ? cShadow + half : na, "B313 SHADOW RAW top", color=color.new(colNeutral, 100), display=display.pane)
pShadowLo = plot(issue68B313Ready ? cShadow - half : na, "B313 SHADOW RAW bottom", color=color.new(colNeutral, 100), display=display.pane)
pBreakHi = plot(issue68B313Ready ? cBreak + half : na, "B313 BREAK top", color=color.new(colNeutral, 100), display=display.pane)
pBreakLo = plot(issue68B313Ready ? cBreak - half : na, "B313 BREAK bottom", color=color.new(colNeutral, 100), display=display.pane)
pOldStructHi = plot(issue68B313Ready ? cOldStruct + half : na, "B313 OLD STRUCT top", color=color.new(colNeutral, 100), display=display.pane)
pOldStructLo = plot(issue68B313Ready ? cOldStruct - half : na, "B313 OLD STRUCT bottom", color=color.new(colNeutral, 100), display=display.pane)
pContStructHi = plot(issue68B313Ready ? cContStruct + half : na, "B313 CONT STRUCT top", color=color.new(colNeutral, 100), display=display.pane)
pContStructLo = plot(issue68B313Ready ? cContStruct - half : na, "B313 CONT STRUCT bottom", color=color.new(colNeutral, 100), display=display.pane)
pDiffHi = plot(issue68B313Ready ? cDiff + half : na, "B313 EARLY DELAY top", color=color.new(colNeutral, 100), display=display.pane)
pDiffLo = plot(issue68B313Ready ? cDiff - half : na, "B313 EARLY DELAY bottom", color=color.new(colNeutral, 100), display=display.pane)
pHandoffHi = plot(issue68B313Ready ? cHandoff + half : na, "B313 HANDOFF top", color=color.new(colNeutral, 100), display=display.pane)
pHandoffLo = plot(issue68B313Ready ? cHandoff - half : na, "B313 HANDOFF bottom", color=color.new(colNeutral, 100), display=display.pane)

fill(pOldHi, pOldLo, color=f_issue68B313Color(issue68B313OldSign), title="B313 OLD RAW band")
fill(pShadowHi, pShadowLo, color=f_issue68B313Color(issue68B313ShadowSign), title="B313 SHADOW RAW band")
fill(pBreakHi, pBreakLo, color=f_issue68B313Color(issue68B313BreakSign), title="B313 BREAK band")
fill(pOldStructHi, pOldStructLo, color=f_issue68B313Color(issue68B313OldStructureSign), title="B313 OLD STRUCTURE band")
fill(pContStructHi, pContStructLo, color=f_issue68B313Color(issue68B313ContinuousStructureSign), title="B313 CONTINUOUS STRUCTURE band")
fill(pDiffHi, pDiffLo, color=issue68B313Difference == 1 ? color.new(colGreen, 10) : issue68B313Difference == -1 ? color.new(colRed, 10) : color.new(colNeutral, 78), title="B313 EARLY DELAY band")
fill(pHandoffHi, pHandoffLo, color=issue68B313Handoff ? color.new(color.yellow, 0) : color.new(colNeutral, 82), title="B313 ORIGINAL HANDOFF band")

var table issue68B313Legend = table.new(position.top_right, 2, 9, border_width=1)
if barstate.islast
    if showIssue68B313Legend
        table.cell(issue68B313Legend, 0, 0, "LAYER", text_color=color.white, bgcolor=color.new(colNeutral, 15))
        table.cell(issue68B313Legend, 1, 0, "NOW", text_color=color.white, bgcolor=color.new(colNeutral, 15))
        table.cell(issue68B313Legend, 0, 1, "TARGET", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B313Legend, 1, 1, issue68B313Direction, text_color=color.white, bgcolor=color.new(colNeutral, 15))
        table.cell(issue68B313Legend, 0, 2, "OLD RAW", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B313Legend, 1, 2, f_issue68B313Text(issue68B313OldSign), text_color=color.white, bgcolor=f_issue68B313Color(issue68B313OldSign))
        table.cell(issue68B313Legend, 0, 3, "SHADOW RAW", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B313Legend, 1, 3, f_issue68B313Text(issue68B313ShadowSign), text_color=color.white, bgcolor=f_issue68B313Color(issue68B313ShadowSign))
        table.cell(issue68B313Legend, 0, 4, "BREAK", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B313Legend, 1, 4, f_issue68B313Text(issue68B313BreakSign), text_color=color.white, bgcolor=f_issue68B313Color(issue68B313BreakSign))
        table.cell(issue68B313Legend, 0, 5, "OLD STRUCT", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B313Legend, 1, 5, f_issue68B313Text(issue68B313OldStructureSign), text_color=color.white, bgcolor=f_issue68B313Color(issue68B313OldStructureSign))
        table.cell(issue68B313Legend, 0, 6, "CONT STRUCT", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B313Legend, 1, 6, f_issue68B313Text(issue68B313ContinuousStructureSign), text_color=color.white, bgcolor=f_issue68B313Color(issue68B313ContinuousStructureSign))
        table.cell(issue68B313Legend, 0, 7, "SHADOW DIFF", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B313Legend, 1, 7, issue68B313Difference == 1 ? "EARLIER" : issue68B313Difference == -1 ? "LATER" : "ALIGNED", text_color=color.white, bgcolor=issue68B313Difference == 1 ? colGreen : issue68B313Difference == -1 ? colRed : colNeutral)
        table.cell(issue68B313Legend, 0, 8, "NOTE", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B313Legend, 1, 8, "綠=shadow早｜紅=shadow晚", text_color=color.white, bgcolor=color.new(colNeutral, 15))
    else
        table.clear(issue68B313Legend, 0, 0, 1, 8)

plot(issue68B313OldRaw, "B313 old reconstructed raw delta", display=display.data_window)
plot(issue68B313ShadowRaw, "B313 shadow raw delta", display=display.data_window)
plot(issue68B313OldStructure, "B313 old Structure weighted edge", display=display.data_window)
plot(issue68B313ContinuousStructure, "B313 continuous Structure weighted edge", display=display.data_window)
'''.strip()


def generate(source: Path) -> str:
    d1_text = phase_b.d1.generate(source)
    if d1_text.count(phase_b.D1_EXPORT_MARKER) != 1:
        raise RuntimeError("expected exactly one D1 parity export marker")
    core = d1_text.split(phase_b.D1_EXPORT_MARKER, 1)[0].rstrip()
    core = replace_once(core, phase_b.D1_INDICATOR_DECL, DECL)
    out = core + "\n\n" + BODY + "\n"
    required = (
        "Issue #68 B3.13 diagnostic only",
        'volumeMode = "Off"',
        'mtfMode = "Off"',
        'divMode = "Off"',
        "B313 OLD RAW band",
        "B313 SHADOW RAW band",
        "B313 OLD STRUCTURE band",
        "B313 CONTINUOUS STRUCTURE band",
        "B313 EARLY DELAY band",
        "B313 ORIGINAL HANDOFF band",
        "distRank - 50.0",
        "maturityDistRank - 50.0",
    )
    for token in required:
        if token not in out:
            raise RuntimeError(f"missing B3.13 audit token: {token}")
    for token in ("strategy.", "issue68B34A", "issue68B34B", "issue68B34C", "D1B|"):
        if token in out:
            raise RuntimeError(f"forbidden token leaked into B3.13 audit: {token}")
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
