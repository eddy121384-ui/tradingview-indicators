#!/usr/bin/env python3
"""Generate Issue #68 B3.9 raw formulation attribution audit Pine."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_phase_b_lifecycle_pine as phase_b
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 B3.9 Raw Formulation", shorttitle="ChaseRisk #68 B39", overlay=false, precision=2)'

B39_BODY = r'''

// ============================================================================
// Issue #66 C-2 runtime-validated price-only lineage.
// Issue #68 B3.9 raw formulation attribution audit only.
// No classifier formula, weight, threshold, gate, persistence, Core Bias,
// Exposure, or strategy change.
// ============================================================================

groupIssue68B39 = "Issue #68｜B3.9 Raw Formulation"
issue68B39Direction = input.string("Bull", "審計方向", options=["Bull", "Bear"], group=groupIssue68B39)
showIssue68B39Legend = input.bool(true, "顯示右上角狀態表", group=groupIssue68B39)

issue68B39Ready = bar_index >= rankLen - 1
bool issue68B39Bull = issue68B39Direction == "Bull"

f_issue68B39PassColor(int x) => x == 1 ? colGreen : x == -1 ? colRed : colNeutral
f_issue68B39PassText(int x) => x == 1 ? "YES" : x == -1 ? "NO" : "N/A"
f_issue68B39BandColor(int x) => color.new(f_issue68B39PassColor(x), x == 0 ? 68 : 18)
f_issue68B39StageText(int id) => id == 1 ? "S1 Acc" : id == 2 ? "S2 Markup" : id == 3 ? "S3 Reacc" : id == 4 ? "S4 Dist" : id == 5 ? "S5 Markdown" : id == 6 ? "S6 Redist" : "N/A"

f_issue68B39RawWinner() =>
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

[issue68B39RawWinner, issue68B39RawWinnerValue] = f_issue68B39RawWinner()

float issue68B39FreshRaw = issue68B39Bull ? markupRaw : markdownRaw
float issue68B39ContinuationRaw = issue68B39Bull ? reaccRaw : redistRaw
int issue68B39FreshStage = issue68B39Bull ? 2 : 5
int issue68B39ContinuationStage = issue68B39Bull ? 3 : 6
float issue68B39TargetRaw = math.max(issue68B39FreshRaw, issue68B39ContinuationRaw)
int issue68B39TargetStage = issue68B39FreshRaw >= issue68B39ContinuationRaw ? issue68B39FreshStage : issue68B39ContinuationStage

// Four reciprocal competitor slots. Bull: S1,S4,S5,S6. Bear: S4,S1,S2,S3.
int issue68B39CompAStage = issue68B39Bull ? 1 : 4
int issue68B39CompBStage = issue68B39Bull ? 4 : 1
int issue68B39CompCStage = issue68B39Bull ? 5 : 2
int issue68B39CompDStage = issue68B39Bull ? 6 : 3
float issue68B39CompARaw = issue68B39Bull ? accRaw : distRaw
float issue68B39CompBRaw = issue68B39Bull ? distRaw : accRaw
float issue68B39CompCRaw = issue68B39Bull ? markdownRaw : markupRaw
float issue68B39CompDRaw = issue68B39Bull ? redistRaw : reaccRaw
float issue68B39CompMax = math.max(math.max(issue68B39CompARaw, issue68B39CompBRaw), math.max(issue68B39CompCRaw, issue68B39CompDRaw))

int issue68B39RawAdv = not issue68B39Ready ? 0 : (issue68B39TargetRaw > issue68B39CompMax ? 1 : -1)
int issue68B39FreshLead = not issue68B39Ready ? 0 : (issue68B39FreshRaw >= issue68B39ContinuationRaw ? 1 : -1)
int issue68B39VsCompA = not issue68B39Ready ? 0 : (issue68B39TargetRaw > issue68B39CompARaw ? 1 : -1)
int issue68B39VsCompB = not issue68B39Ready ? 0 : (issue68B39TargetRaw > issue68B39CompBRaw ? 1 : -1)
int issue68B39VsCompC = not issue68B39Ready ? 0 : (issue68B39TargetRaw > issue68B39CompCRaw ? 1 : -1)
int issue68B39VsCompD = not issue68B39Ready ? 0 : (issue68B39TargetRaw > issue68B39CompDRaw ? 1 : -1)
int issue68B39BreakEdge = not issue68B39Ready ? 0 : (issue68B39Bull ? (breakoutScore > explicitBreakdownScore ? 1 : -1) : (explicitBreakdownScore > breakoutScore ? 1 : -1))
int issue68B39StructureEdge = not issue68B39Ready ? 0 : (issue68B39Bull ? (structureStrong > structureWeak ? 1 : -1) : (structureWeak > structureStrong ? 1 : -1))

float issue68B39Half = 0.34
float cRawAdv = 7.0
float cFresh = 6.0
float cA = 5.0
float cB = 4.0
float cC = 3.0
float cD = 2.0
float cBreak = 1.0
float cStructure = 0.0

pRawAdvHi = plot(issue68B39Ready ? cRawAdv + issue68B39Half : na, "B39 RAW ADV top", color=color.new(colNeutral, 100), display=display.pane)
pRawAdvLo = plot(issue68B39Ready ? cRawAdv - issue68B39Half : na, "B39 RAW ADV bottom", color=color.new(colNeutral, 100), display=display.pane)
pFreshHi = plot(issue68B39Ready ? cFresh + issue68B39Half : na, "B39 FRESH TARGET top", color=color.new(colNeutral, 100), display=display.pane)
pFreshLo = plot(issue68B39Ready ? cFresh - issue68B39Half : na, "B39 FRESH TARGET bottom", color=color.new(colNeutral, 100), display=display.pane)
pAHi = plot(issue68B39Ready ? cA + issue68B39Half : na, "B39 COMP A top", color=color.new(colNeutral, 100), display=display.pane)
pALo = plot(issue68B39Ready ? cA - issue68B39Half : na, "B39 COMP A bottom", color=color.new(colNeutral, 100), display=display.pane)
pBHi = plot(issue68B39Ready ? cB + issue68B39Half : na, "B39 COMP B top", color=color.new(colNeutral, 100), display=display.pane)
pBLo = plot(issue68B39Ready ? cB - issue68B39Half : na, "B39 COMP B bottom", color=color.new(colNeutral, 100), display=display.pane)
pCHi = plot(issue68B39Ready ? cC + issue68B39Half : na, "B39 COMP C top", color=color.new(colNeutral, 100), display=display.pane)
pCLo = plot(issue68B39Ready ? cC - issue68B39Half : na, "B39 COMP C bottom", color=color.new(colNeutral, 100), display=display.pane)
pDHi = plot(issue68B39Ready ? cD + issue68B39Half : na, "B39 COMP D top", color=color.new(colNeutral, 100), display=display.pane)
pDLo = plot(issue68B39Ready ? cD - issue68B39Half : na, "B39 COMP D bottom", color=color.new(colNeutral, 100), display=display.pane)
pBreakHi = plot(issue68B39Ready ? cBreak + issue68B39Half : na, "B39 BREAK top", color=color.new(colNeutral, 100), display=display.pane)
pBreakLo = plot(issue68B39Ready ? cBreak - issue68B39Half : na, "B39 BREAK bottom", color=color.new(colNeutral, 100), display=display.pane)
pStructureHi = plot(issue68B39Ready ? cStructure + issue68B39Half : na, "B39 STRUCTURE top", color=color.new(colNeutral, 100), display=display.pane)
pStructureLo = plot(issue68B39Ready ? cStructure - issue68B39Half : na, "B39 STRUCTURE bottom", color=color.new(colNeutral, 100), display=display.pane)

fill(pRawAdvHi, pRawAdvLo, color=issue68B39Ready ? f_issue68B39BandColor(issue68B39RawAdv) : na, title="B39 RAW ADV band")
fill(pFreshHi, pFreshLo, color=issue68B39Ready ? f_issue68B39BandColor(issue68B39FreshLead) : na, title="B39 FRESH TARGET band")
fill(pAHi, pALo, color=issue68B39Ready ? f_issue68B39BandColor(issue68B39VsCompA) : na, title="B39 COMP A band")
fill(pBHi, pBLo, color=issue68B39Ready ? f_issue68B39BandColor(issue68B39VsCompB) : na, title="B39 COMP B band")
fill(pCHi, pCLo, color=issue68B39Ready ? f_issue68B39BandColor(issue68B39VsCompC) : na, title="B39 COMP C band")
fill(pDHi, pDLo, color=issue68B39Ready ? f_issue68B39BandColor(issue68B39VsCompD) : na, title="B39 COMP D band")
fill(pBreakHi, pBreakLo, color=issue68B39Ready ? f_issue68B39BandColor(issue68B39BreakEdge) : na, title="B39 BREAK band")
fill(pStructureHi, pStructureLo, color=issue68B39Ready ? f_issue68B39BandColor(issue68B39StructureEdge) : na, title="B39 STRUCTURE band")

var table issue68B39Legend = table.new(position.top_right, 2, 13, border_width=1)
if barstate.islast
    if showIssue68B39Legend
        table.cell(issue68B39Legend, 0, 0, "LAYER", text_color=color.white, bgcolor=color.new(colNeutral, 15))
        table.cell(issue68B39Legend, 1, 0, "NOW", text_color=color.white, bgcolor=color.new(colNeutral, 15))
        table.cell(issue68B39Legend, 0, 1, "TARGET｜審計方向", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B39Legend, 1, 1, issue68B39Direction, text_color=color.white, bgcolor=color.new(colNeutral, 15))
        table.cell(issue68B39Legend, 0, 2, "TARGET STAGE｜目標內部", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B39Legend, 1, 2, f_issue68B39StageText(issue68B39TargetStage), text_color=color.white, bgcolor=color.new(colNeutral, 15))
        table.cell(issue68B39Legend, 0, 3, "RAW WINNER｜原始冠軍", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B39Legend, 1, 3, f_issue68B39StageText(issue68B39RawWinner), text_color=color.white, bgcolor=color.new(colNeutral, 15))
        table.cell(issue68B39Legend, 0, 4, "RAW ADV｜目標 family 最高", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B39Legend, 1, 4, f_issue68B39PassText(issue68B39RawAdv), text_color=color.white, bgcolor=f_issue68B39PassColor(issue68B39RawAdv))
        table.cell(issue68B39Legend, 0, 5, "FRESH TARGET｜fresh > continuation", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B39Legend, 1, 5, f_issue68B39PassText(issue68B39FreshLead), text_color=color.white, bgcolor=f_issue68B39PassColor(issue68B39FreshLead))
        table.cell(issue68B39Legend, 0, 6, "> " + f_issue68B39StageText(issue68B39CompAStage), text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B39Legend, 1, 6, f_issue68B39PassText(issue68B39VsCompA), text_color=color.white, bgcolor=f_issue68B39PassColor(issue68B39VsCompA))
        table.cell(issue68B39Legend, 0, 7, "> " + f_issue68B39StageText(issue68B39CompBStage), text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B39Legend, 1, 7, f_issue68B39PassText(issue68B39VsCompB), text_color=color.white, bgcolor=f_issue68B39PassColor(issue68B39VsCompB))
        table.cell(issue68B39Legend, 0, 8, "> " + f_issue68B39StageText(issue68B39CompCStage), text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B39Legend, 1, 8, f_issue68B39PassText(issue68B39VsCompC), text_color=color.white, bgcolor=f_issue68B39PassColor(issue68B39VsCompC))
        table.cell(issue68B39Legend, 0, 9, "> " + f_issue68B39StageText(issue68B39CompDStage), text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B39Legend, 1, 9, f_issue68B39PassText(issue68B39VsCompD), text_color=color.white, bgcolor=f_issue68B39PassColor(issue68B39VsCompD))
        table.cell(issue68B39Legend, 0, 10, "BREAK｜突破方向", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B39Legend, 1, 10, f_issue68B39PassText(issue68B39BreakEdge), text_color=color.white, bgcolor=f_issue68B39PassColor(issue68B39BreakEdge))
        table.cell(issue68B39Legend, 0, 11, "STRUCTURE｜結構方向", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B39Legend, 1, 11, f_issue68B39PassText(issue68B39StructureEdge), text_color=color.white, bgcolor=f_issue68B39PassColor(issue68B39StructureEdge))
        table.cell(issue68B39Legend, 0, 12, "NOTE", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B39Legend, 1, 12, "綠=target贏｜紅=被壓", text_color=color.white, bgcolor=color.new(colNeutral, 15))
    else
        table.clear(issue68B39Legend, 0, 0, 1, 12)

plot(issue68B39TargetRaw, "B39 target family raw", display=display.data_window)
plot(issue68B39FreshRaw, "B39 fresh target raw", display=display.data_window)
plot(issue68B39ContinuationRaw, "B39 continuation target raw", display=display.data_window)
plot(float(issue68B39TargetStage), "B39 target substage", display=display.data_window)
plot(float(issue68B39RawWinner), "B39 exact raw winner stage", display=display.data_window)
plot(issue68B39TargetRaw - issue68B39CompARaw, "B39 target minus comp A", display=display.data_window)
plot(issue68B39TargetRaw - issue68B39CompBRaw, "B39 target minus comp B", display=display.data_window)
plot(issue68B39TargetRaw - issue68B39CompCRaw, "B39 target minus comp C", display=display.data_window)
plot(issue68B39TargetRaw - issue68B39CompDRaw, "B39 target minus comp D", display=display.data_window)
plot(breakoutScore - explicitBreakdownScore, "B39 break directional delta", display=display.data_window)
plot(structureStrong - structureWeak, "B39 structure directional delta", display=display.data_window)
'''.strip()


def generate(source: Path) -> str:
    d1_text = phase_b.d1.generate(source)
    if d1_text.count(phase_b.D1_EXPORT_MARKER) != 1:
        raise RuntimeError("expected exactly one D1 parity export marker")
    core = d1_text.split(phase_b.D1_EXPORT_MARKER, 1)[0].rstrip()
    core = replace_once(core, phase_b.D1_INDICATOR_DECL, AUDIT_DECL)
    out = core + "\n\n" + B39_BODY + "\n"
    required = (
        "Issue #66 C-2 runtime-validated price-only lineage",
        'volumeMode = "Off"',
        'mtfMode = "Off"',
        'divMode = "Off"',
        "B39 RAW ADV band",
        "B39 FRESH TARGET band",
        "B39 COMP A band",
        "B39 COMP B band",
        "B39 COMP C band",
        "B39 COMP D band",
        "B39 BREAK band",
        "B39 STRUCTURE band",
        "TARGET STAGE｜目標內部",
        "RAW WINNER｜原始冠軍",
    )
    for token in required:
        if token not in out:
            raise RuntimeError(f"missing B3.9 audit token: {token}")
    for token in ("strategy.", "issue68B34A", "issue68B34B", "issue68B34C", "D1B|"):
        if token in out:
            raise RuntimeError(f"forbidden token leaked into B3.9 audit: {token}")
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
