#!/usr/bin/env python3
"""Generate Issue #68 B3.14 Break evidence-memory TradingView audit."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_phase_b_lifecycle_pine as phase_b
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
DECL = 'indicator("Chase Risk Radar｜Issue #68 B3.14 Break Memory", shorttitle="ChaseRisk #68 B314", overlay=false, precision=2)'

BODY = r'''

// Issue #68 B3.14 diagnostic only: Break source / recent-event memory audit.
groupIssue68B314 = "Issue #68｜B3.14 Break Evidence Memory"
issue68B314Direction = input.string("Bull", "審計方向", options=["Bull", "Bear"], group=groupIssue68B314)
showIssue68B314Legend = input.bool(true, "顯示右上角狀態表", group=groupIssue68B314)
int issue68B314Dir = issue68B314Direction == "Bull" ? 1 : -1
bool issue68B314Ready = bar_index >= rankLen - 1

float issue68B314Break = 0.17 * (breakoutScore - explicitBreakdownScore)
float issue68B314Heat = 0.17 * (heatUp - panicHeatDn)
float issue68B314Structure = 0.17 * (structureStrong - structureWeak)
float issue68B314Extension = 0.2125 * (markupExtensionScore - markdownExtensionScore)
float issue68B314Continuation = 0.1275 * (markupContinuationScore - markdownContinuationScore)
float issue68B314Trace = 0.15 * (accTraceForMarkup - distTraceForMarkdown)
float issue68B314Direct = issue68B314Break + issue68B314Heat + issue68B314Structure + issue68B314Extension + issue68B314Continuation + issue68B314Trace

float issue68B314BreakO = issue68B314Dir * issue68B314Break
float issue68B314HeatO = issue68B314Dir * issue68B314Heat
float issue68B314StructureO = issue68B314Dir * issue68B314Structure
float issue68B314ExtensionO = issue68B314Dir * issue68B314Extension
float issue68B314ContinuationO = issue68B314Dir * issue68B314Continuation
float issue68B314TraceO = issue68B314Dir * issue68B314Trace
float issue68B314DirectO = issue68B314Dir * issue68B314Direct

bool issue68B314OldRangeMem = issue68B314Direction == "Bull" ? nz(recentRangeBreakDnStrength, 0.0) > 0.0 : nz(recentRangeBreakUpStrength, 0.0) > 0.0
bool issue68B314OldMaMem = issue68B314Direction == "Bull" ? recentMaCrossDn : recentMaCrossUp
bool issue68B314NewRange = issue68B314Direction == "Bull" ? breakoutRangeEvidence > 0.0 : breakdownRangeEvidence > 0.0
bool issue68B314NewMa = issue68B314Direction == "Bull" ? breakoutMaEvidence > 0.0 : breakdownMaEvidence > 0.0
bool issue68B314MaTargetSide = issue68B314Direction == "Bull" ? logPrice > maLog : logPrice < maLog
float issue68B314TargetRange = issue68B314Direction == "Bull" ? breakoutRangeEvidence : breakdownRangeEvidence
float issue68B314TargetMa = issue68B314Direction == "Bull" ? breakoutMaEvidence : breakdownMaEvidence
float issue68B314OldRange = issue68B314Direction == "Bull" ? breakdownRangeEvidence : breakoutRangeEvidence
float issue68B314OldMa = issue68B314Direction == "Bull" ? breakdownMaEvidence : breakoutMaEvidence
bool issue68B314TargetMode = issue68B314Direction == "Bull" ? breakoutModeUp : breakdownModeDn
bool issue68B314OldMode = issue68B314Direction == "Bull" ? breakdownModeDn : breakoutModeUp

f_issue68B314Source(bool mode, float r, float m) => mode ? "MODE" : r > m ? "RANGE" : m > r ? "MA" : r > 0 ? "TIE" : "NONE"
f_issue68B314YesNo(bool x) => x ? "YES" : "NO"
f_issue68B314BoolColor(bool good) => good ? color.new(colGreen, 15) : color.new(colRed, 15)
f_issue68B314OldMemColor(bool active) => active ? color.new(colRed, 10) : color.new(colGreen, 20)
f_issue68B314BreakColor() => issue68B314BreakO > 0 ? color.new(colGreen, 15) : issue68B314BreakO < 0 ? color.new(colRed, 15) : color.new(colNeutral, 65)

bool issue68B314Handoff = issue68B314Ready and issue68B314DirectO > 0 and issue68B314DirectO[1] <= 0
bool issue68B314BreakBlocker = issue68B314Handoff and issue68B314BreakO[1] <= issue68B314HeatO[1] and issue68B314BreakO[1] <= issue68B314StructureO[1] and issue68B314BreakO[1] <= issue68B314ExtensionO[1] and issue68B314BreakO[1] <= issue68B314ContinuationO[1] and issue68B314BreakO[1] <= issue68B314TraceO[1]

float half = 0.34
float cBreak = 6.0
float cOldRange = 5.0
float cOldMa = 4.0
float cNewRange = 3.0
float cNewMa = 2.0
float cMaSide = 1.0
float cEvent = 0.0

pBreakHi = plot(issue68B314Ready ? cBreak + half : na, "B314 BREAK top", color=color.new(colNeutral,100))
pBreakLo = plot(issue68B314Ready ? cBreak - half : na, "B314 BREAK bottom", color=color.new(colNeutral,100))
pOldRangeHi = plot(issue68B314Ready ? cOldRange + half : na, "B314 OLD RANGE MEM top", color=color.new(colNeutral,100))
pOldRangeLo = plot(issue68B314Ready ? cOldRange - half : na, "B314 OLD RANGE MEM bottom", color=color.new(colNeutral,100))
pOldMaHi = plot(issue68B314Ready ? cOldMa + half : na, "B314 OLD MA MEM top", color=color.new(colNeutral,100))
pOldMaLo = plot(issue68B314Ready ? cOldMa - half : na, "B314 OLD MA MEM bottom", color=color.new(colNeutral,100))
pNewRangeHi = plot(issue68B314Ready ? cNewRange + half : na, "B314 NEW RANGE top", color=color.new(colNeutral,100))
pNewRangeLo = plot(issue68B314Ready ? cNewRange - half : na, "B314 NEW RANGE bottom", color=color.new(colNeutral,100))
pNewMaHi = plot(issue68B314Ready ? cNewMa + half : na, "B314 NEW MA top", color=color.new(colNeutral,100))
pNewMaLo = plot(issue68B314Ready ? cNewMa - half : na, "B314 NEW MA bottom", color=color.new(colNeutral,100))
pMaSideHi = plot(issue68B314Ready ? cMaSide + half : na, "B314 MA SIDE top", color=color.new(colNeutral,100))
pMaSideLo = plot(issue68B314Ready ? cMaSide - half : na, "B314 MA SIDE bottom", color=color.new(colNeutral,100))
pEventHi = plot(issue68B314Ready ? cEvent + half : na, "B314 BREAK BLOCKER top", color=color.new(colNeutral,100))
pEventLo = plot(issue68B314Ready ? cEvent - half : na, "B314 BREAK BLOCKER bottom", color=color.new(colNeutral,100))

fill(pBreakHi,pBreakLo,color=f_issue68B314BreakColor(),title="B314 BREAK EDGE band")
fill(pOldRangeHi,pOldRangeLo,color=f_issue68B314OldMemColor(issue68B314OldRangeMem),title="B314 OLD RANGE MEMORY band")
fill(pOldMaHi,pOldMaLo,color=f_issue68B314OldMemColor(issue68B314OldMaMem),title="B314 OLD MA MEMORY band")
fill(pNewRangeHi,pNewRangeLo,color=f_issue68B314BoolColor(issue68B314NewRange),title="B314 NEW RANGE EVIDENCE band")
fill(pNewMaHi,pNewMaLo,color=f_issue68B314BoolColor(issue68B314NewMa),title="B314 NEW MA EVIDENCE band")
fill(pMaSideHi,pMaSideLo,color=f_issue68B314BoolColor(issue68B314MaTargetSide),title="B314 CURRENT MA SIDE band")
fill(pEventHi,pEventLo,color=issue68B314BreakBlocker ? color.new(color.yellow,0) : color.new(colNeutral,82),title="B314 BREAK FINAL BLOCKER band")

var table issue68B314Legend = table.new(position.top_right, 2, 10, border_width=1)
if barstate.islast
    if showIssue68B314Legend
        table.cell(issue68B314Legend,0,0,"LAYER",text_color=color.white,bgcolor=color.new(colNeutral,15))
        table.cell(issue68B314Legend,1,0,"NOW",text_color=color.white,bgcolor=color.new(colNeutral,15))
        table.cell(issue68B314Legend,0,1,"TARGET",text_color=color.white,bgcolor=color.new(colNeutral,45))
        table.cell(issue68B314Legend,1,1,issue68B314Direction,text_color=color.white,bgcolor=color.new(colNeutral,15))
        table.cell(issue68B314Legend,0,2,"BREAK",text_color=color.white,bgcolor=color.new(colNeutral,45))
        table.cell(issue68B314Legend,1,2,issue68B314BreakO>0?"TARGET":"OLD",text_color=color.white,bgcolor=f_issue68B314BreakColor())
        table.cell(issue68B314Legend,0,3,"OLD RANGE MEM",text_color=color.white,bgcolor=color.new(colNeutral,45))
        table.cell(issue68B314Legend,1,3,issue68B314OldRangeMem?"ACTIVE":"CLEAR",text_color=color.white,bgcolor=f_issue68B314OldMemColor(issue68B314OldRangeMem))
        table.cell(issue68B314Legend,0,4,"OLD MA MEM",text_color=color.white,bgcolor=color.new(colNeutral,45))
        table.cell(issue68B314Legend,1,4,issue68B314OldMaMem?"ACTIVE":"CLEAR",text_color=color.white,bgcolor=f_issue68B314OldMemColor(issue68B314OldMaMem))
        table.cell(issue68B314Legend,0,5,"NEW RANGE",text_color=color.white,bgcolor=color.new(colNeutral,45))
        table.cell(issue68B314Legend,1,5,f_issue68B314YesNo(issue68B314NewRange),text_color=color.white,bgcolor=f_issue68B314BoolColor(issue68B314NewRange))
        table.cell(issue68B314Legend,0,6,"NEW MA",text_color=color.white,bgcolor=color.new(colNeutral,45))
        table.cell(issue68B314Legend,1,6,f_issue68B314YesNo(issue68B314NewMa),text_color=color.white,bgcolor=f_issue68B314BoolColor(issue68B314NewMa))
        table.cell(issue68B314Legend,0,7,"MA SIDE",text_color=color.white,bgcolor=color.new(colNeutral,45))
        table.cell(issue68B314Legend,1,7,issue68B314MaTargetSide?"TARGET":"OLD",text_color=color.white,bgcolor=f_issue68B314BoolColor(issue68B314MaTargetSide))
        table.cell(issue68B314Legend,0,8,"NEW SRC / OLD SRC",text_color=color.white,bgcolor=color.new(colNeutral,45))
        table.cell(issue68B314Legend,1,8,f_issue68B314Source(issue68B314TargetMode,issue68B314TargetRange,issue68B314TargetMa)+" / "+f_issue68B314Source(issue68B314OldMode,issue68B314OldRange,issue68B314OldMa),text_color=color.white,bgcolor=color.new(colNeutral,15))
        table.cell(issue68B314Legend,0,9,"NOTE",text_color=color.white,bgcolor=color.new(colNeutral,45))
        table.cell(issue68B314Legend,1,9,"舊記憶紅=仍活著｜新證據綠=已建立",text_color=color.white,bgcolor=color.new(colNeutral,15))
    else
        table.clear(issue68B314Legend,0,0,1,9)

plot(issue68B314Break,"B314 weighted Break edge",display=display.data_window)
plot(issue68B314TargetRange,"B314 target range evidence",display=display.data_window)
plot(issue68B314OldRange,"B314 old range evidence",display=display.data_window)
plot(issue68B314TargetMa,"B314 target MA evidence",display=display.data_window)
plot(issue68B314OldMa,"B314 old MA evidence",display=display.data_window)
'''.strip()


def generate(source: Path) -> str:
    d1_text = phase_b.d1.generate(source)
    if d1_text.count(phase_b.D1_EXPORT_MARKER) != 1:
        raise RuntimeError("expected exactly one D1 parity export marker")
    core = d1_text.split(phase_b.D1_EXPORT_MARKER, 1)[0].rstrip()
    core = replace_once(core, phase_b.D1_INDICATOR_DECL, DECL)
    out = core + "\n\n" + BODY + "\n"
    required = (
        "Issue #68 B3.14 diagnostic only",
        'volumeMode = "Off"',
        'mtfMode = "Off"',
        'divMode = "Off"',
        "B314 BREAK EDGE band",
        "B314 OLD RANGE MEMORY band",
        "B314 NEW RANGE EVIDENCE band",
        "B314 CURRENT MA SIDE band",
        "B314 BREAK FINAL BLOCKER band",
    )
    for token in required:
        if token not in out:
            raise RuntimeError(f"missing B3.14 audit token: {token}")
    for token in ("strategy.", "issue68B34A", "issue68B34B", "issue68B34C", "D1B|"):
        if token in out:
            raise RuntimeError(f"forbidden token leaked into B3.14 audit: {token}")
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
