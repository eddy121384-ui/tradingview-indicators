#!/usr/bin/env python3
"""Generate Issue #68 B3.15 event-window / stale-memory TradingView audit."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_phase_b_lifecycle_pine as phase_b
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
DECL = 'indicator("Chase Risk Radar｜Issue #68 B3.15 Stale Memory", shorttitle="ChaseRisk #68 B315", overlay=false, precision=2)'

BODY = r'''

// Issue #68 B3.15 diagnostic only: event-window / stale old range-memory audit.
groupIssue68B315 = "Issue #68｜B3.15 Event Window / Stale Memory"
issue68B315Direction = input.string("Bull", "審計方向", options=["Bull", "Bear"], group=groupIssue68B315)
showIssue68B315Legend = input.bool(true, "顯示右上角狀態表", group=groupIssue68B315)
int issue68B315Dir = issue68B315Direction == "Bull" ? 1 : -1
bool issue68B315Ready = bar_index >= rankLen - 1

float issue68B315Break = 0.17 * (breakoutScore - explicitBreakdownScore)
float issue68B315Heat = 0.17 * (heatUp - panicHeatDn)
float issue68B315Structure = 0.17 * (structureStrong - structureWeak)
float issue68B315Extension = 0.2125 * (markupExtensionScore - markdownExtensionScore)
float issue68B315Continuation = 0.1275 * (markupContinuationScore - markdownContinuationScore)
float issue68B315Trace = 0.15 * (accTraceForMarkup - distTraceForMarkdown)
float issue68B315Direct = issue68B315Break + issue68B315Heat + issue68B315Structure + issue68B315Extension + issue68B315Continuation + issue68B315Trace

float issue68B315BreakO = issue68B315Dir * issue68B315Break
float issue68B315HeatO = issue68B315Dir * issue68B315Heat
float issue68B315StructureO = issue68B315Dir * issue68B315Structure
float issue68B315ExtensionO = issue68B315Dir * issue68B315Extension
float issue68B315ContinuationO = issue68B315Dir * issue68B315Continuation
float issue68B315TraceO = issue68B315Dir * issue68B315Trace
float issue68B315DirectO = issue68B315Dir * issue68B315Direct

bool issue68B315MaTargetSide = issue68B315Direction == "Bull" ? logPrice > maLog : logPrice < maLog
bool issue68B315OldRangeMem = issue68B315Direction == "Bull" ? nz(recentRangeBreakDnStrength, 0.0) > 0.0 : nz(recentRangeBreakUpStrength, 0.0) > 0.0
bool issue68B315NewRange = issue68B315Direction == "Bull" ? breakoutRangeEvidence > 0.0 : breakdownRangeEvidence > 0.0
bool issue68B315StaleOverlap = issue68B315MaTargetSide and issue68B315OldRangeMem
bool issue68B315BreakOldDuringOverlap = issue68B315StaleOverlap and issue68B315BreakO < 0.0
bool issue68B315MaFlip = issue68B315Ready and issue68B315MaTargetSide and not issue68B315MaTargetSide[1]

bool issue68B315Handoff = issue68B315Ready and issue68B315DirectO > 0 and issue68B315DirectO[1] <= 0
bool issue68B315BreakBlocker = issue68B315Handoff and issue68B315BreakO[1] <= issue68B315HeatO[1] and issue68B315BreakO[1] <= issue68B315StructureO[1] and issue68B315BreakO[1] <= issue68B315ExtensionO[1] and issue68B315BreakO[1] <= issue68B315ContinuationO[1] and issue68B315BreakO[1] <= issue68B315TraceO[1]

float issue68B315MaRunAge = issue68B315MaTargetSide ? math.max(nz(ta.barssince(not issue68B315MaTargetSide), 1) - 1, 0) : na

f_issue68B315YesNo(bool x) => x ? "YES" : "NO"
f_issue68B315StateColor(bool good) => good ? color.new(colGreen, 15) : color.new(colRed, 15)
f_issue68B315MemoryColor(bool active) => active ? color.new(colRed, 10) : color.new(colGreen, 20)
f_issue68B315BreakColor() => issue68B315BreakO > 0 ? color.new(colGreen, 15) : issue68B315BreakO < 0 ? color.new(colRed, 15) : color.new(colNeutral, 65)

float half = 0.34
float cBreak = 7.0
float cMa = 6.0
float cOldRange = 5.0
float cOverlap = 4.0
float cNewRange = 3.0
float cBreakOld = 2.0
float cMaFlip = 1.0
float cEvent = 0.0

pBreakHi = plot(issue68B315Ready ? cBreak + half : na, "B315 BREAK top", color=color.new(colNeutral,100))
pBreakLo = plot(issue68B315Ready ? cBreak - half : na, "B315 BREAK bottom", color=color.new(colNeutral,100))
pMaHi = plot(issue68B315Ready ? cMa + half : na, "B315 MA TARGET top", color=color.new(colNeutral,100))
pMaLo = plot(issue68B315Ready ? cMa - half : na, "B315 MA TARGET bottom", color=color.new(colNeutral,100))
pOldRangeHi = plot(issue68B315Ready ? cOldRange + half : na, "B315 OLD RANGE MEM top", color=color.new(colNeutral,100))
pOldRangeLo = plot(issue68B315Ready ? cOldRange - half : na, "B315 OLD RANGE MEM bottom", color=color.new(colNeutral,100))
pOverlapHi = plot(issue68B315Ready ? cOverlap + half : na, "B315 STALE OVERLAP top", color=color.new(colNeutral,100))
pOverlapLo = plot(issue68B315Ready ? cOverlap - half : na, "B315 STALE OVERLAP bottom", color=color.new(colNeutral,100))
pNewRangeHi = plot(issue68B315Ready ? cNewRange + half : na, "B315 NEW RANGE top", color=color.new(colNeutral,100))
pNewRangeLo = plot(issue68B315Ready ? cNewRange - half : na, "B315 NEW RANGE bottom", color=color.new(colNeutral,100))
pBreakOldHi = plot(issue68B315Ready ? cBreakOld + half : na, "B315 BREAK OLD OVERLAP top", color=color.new(colNeutral,100))
pBreakOldLo = plot(issue68B315Ready ? cBreakOld - half : na, "B315 BREAK OLD OVERLAP bottom", color=color.new(colNeutral,100))
pMaFlipHi = plot(issue68B315Ready ? cMaFlip + half : na, "B315 MA FLIP top", color=color.new(colNeutral,100))
pMaFlipLo = plot(issue68B315Ready ? cMaFlip - half : na, "B315 MA FLIP bottom", color=color.new(colNeutral,100))
pEventHi = plot(issue68B315Ready ? cEvent + half : na, "B315 BREAK BLOCKER top", color=color.new(colNeutral,100))
pEventLo = plot(issue68B315Ready ? cEvent - half : na, "B315 BREAK BLOCKER bottom", color=color.new(colNeutral,100))

fill(pBreakHi,pBreakLo,color=f_issue68B315BreakColor(),title="B315 BREAK EDGE band")
fill(pMaHi,pMaLo,color=f_issue68B315StateColor(issue68B315MaTargetSide),title="B315 MA TARGET SIDE band")
fill(pOldRangeHi,pOldRangeLo,color=f_issue68B315MemoryColor(issue68B315OldRangeMem),title="B315 OLD RANGE MEMORY band")
fill(pOverlapHi,pOverlapLo,color=issue68B315StaleOverlap ? color.new(color.yellow,8) : color.new(colNeutral,82),title="B315 STALE OVERLAP band")
fill(pNewRangeHi,pNewRangeLo,color=f_issue68B315StateColor(issue68B315NewRange),title="B315 NEW RANGE EVIDENCE band")
fill(pBreakOldHi,pBreakOldLo,color=issue68B315BreakOldDuringOverlap ? color.new(colRed,0) : color.new(colNeutral,82),title="B315 BREAK OLD DURING OVERLAP band")
fill(pMaFlipHi,pMaFlipLo,color=issue68B315MaFlip ? color.new(color.aqua,0) : color.new(colNeutral,82),title="B315 MA FLIP band")
fill(pEventHi,pEventLo,color=issue68B315BreakBlocker ? color.new(color.orange,0) : color.new(colNeutral,82),title="B315 BREAK FINAL BLOCKER band")

var table issue68B315Legend = table.new(position.top_right, 2, 9, border_width=1)
if barstate.islast
    if showIssue68B315Legend
        table.cell(issue68B315Legend,0,0,"LAYER",text_color=color.white,bgcolor=color.new(colNeutral,15))
        table.cell(issue68B315Legend,1,0,"NOW",text_color=color.white,bgcolor=color.new(colNeutral,15))
        table.cell(issue68B315Legend,0,1,"TARGET",text_color=color.white,bgcolor=color.new(colNeutral,45))
        table.cell(issue68B315Legend,1,1,issue68B315Direction,text_color=color.white,bgcolor=color.new(colNeutral,15))
        table.cell(issue68B315Legend,0,2,"MA SIDE",text_color=color.white,bgcolor=color.new(colNeutral,45))
        table.cell(issue68B315Legend,1,2,issue68B315MaTargetSide?"TARGET":"OLD",text_color=color.white,bgcolor=f_issue68B315StateColor(issue68B315MaTargetSide))
        table.cell(issue68B315Legend,0,3,"OLD RANGE MEM",text_color=color.white,bgcolor=color.new(colNeutral,45))
        table.cell(issue68B315Legend,1,3,issue68B315OldRangeMem?"ACTIVE":"CLEAR",text_color=color.white,bgcolor=f_issue68B315MemoryColor(issue68B315OldRangeMem))
        table.cell(issue68B315Legend,0,4,"STALE OVERLAP",text_color=color.white,bgcolor=color.new(colNeutral,45))
        table.cell(issue68B315Legend,1,4,f_issue68B315YesNo(issue68B315StaleOverlap),text_color=color.white,bgcolor=issue68B315StaleOverlap?color.new(color.yellow,8):color.new(colNeutral,55))
        table.cell(issue68B315Legend,0,5,"BREAK",text_color=color.white,bgcolor=color.new(colNeutral,45))
        table.cell(issue68B315Legend,1,5,issue68B315BreakO>0?"TARGET":"OLD",text_color=color.white,bgcolor=f_issue68B315BreakColor())
        table.cell(issue68B315Legend,0,6,"NEW RANGE",text_color=color.white,bgcolor=color.new(colNeutral,45))
        table.cell(issue68B315Legend,1,6,f_issue68B315YesNo(issue68B315NewRange),text_color=color.white,bgcolor=f_issue68B315StateColor(issue68B315NewRange))
        table.cell(issue68B315Legend,0,7,"MA RUN AGE",text_color=color.white,bgcolor=color.new(colNeutral,45))
        table.cell(issue68B315Legend,1,7,na(issue68B315MaRunAge)?"-":str.tostring(issue68B315MaRunAge,"#"),text_color=color.white,bgcolor=color.new(colNeutral,15))
        table.cell(issue68B315Legend,0,8,"READ",text_color=color.white,bgcolor=color.new(colNeutral,45))
        table.cell(issue68B315Legend,1,8,"黃=MA已翻但舊Range仍活｜紅=Break仍投舊側",text_color=color.white,bgcolor=color.new(colNeutral,15))
    else
        table.clear(issue68B315Legend,0,0,1,8)

plot(issue68B315Break,"B315 weighted Break edge",display=display.data_window)
plot(issue68B315MaRunAge,"B315 bars since MA target-side run began",display=display.data_window)
plot(issue68B315OldRangeMem?1:0,"B315 old range memory active",display=display.data_window)
plot(issue68B315NewRange?1:0,"B315 new range evidence active",display=display.data_window)
plot(issue68B315StaleOverlap?1:0,"B315 stale overlap",display=display.data_window)
plot(issue68B315BreakOldDuringOverlap?1:0,"B315 Break old during stale overlap",display=display.data_window)
'''.strip()


def generate(source: Path) -> str:
    d1_text = phase_b.d1.generate(source)
    if d1_text.count(phase_b.D1_EXPORT_MARKER) != 1:
        raise RuntimeError("expected exactly one D1 parity export marker")
    core = d1_text.split(phase_b.D1_EXPORT_MARKER, 1)[0].rstrip()
    core = replace_once(core, phase_b.D1_INDICATOR_DECL, DECL)
    out = core + "\n\n" + BODY + "\n"
    required = (
        "Issue #68 B3.15 diagnostic only",
        'volumeMode = "Off"',
        'mtfMode = "Off"',
        'divMode = "Off"',
        "B315 BREAK EDGE band",
        "B315 MA TARGET SIDE band",
        "B315 OLD RANGE MEMORY band",
        "B315 STALE OVERLAP band",
        "B315 BREAK OLD DURING OVERLAP band",
        "B315 BREAK FINAL BLOCKER band",
    )
    for token in required:
        if token not in out:
            raise RuntimeError(f"missing B3.15 audit token: {token}")
    for token in ("strategy.", "issue68B34A", "issue68B34B", "issue68B34C", "D1B|"):
        if token in out:
            raise RuntimeError(f"forbidden token leaked into B3.15 audit: {token}")
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
