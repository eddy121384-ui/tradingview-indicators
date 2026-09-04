#!/usr/bin/env python3
"""Generate Issue #68 B3.7 TOP formation / ranking audit Pine."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_phase_b_lifecycle_pine as phase_b
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 B3.7 TOP Ranking", shorttitle="ChaseRisk #68 B37", overlay=false, precision=2)'

B37_BODY = r'''

// ============================================================================
// Issue #66 C-2 runtime-validated price-only lineage.
// Issue #68 B3.7 TOP formation / ranking audit only.
// No classifier threshold, persistence, Core Bias, Exposure, or strategy change.
// ============================================================================

groupIssue68B37 = "Issue #68｜B3.7 TOP Ranking"
issue68B37Direction = input.string("Bull", "審計方向", options=["Bull", "Bear"], group=groupIssue68B37)
showIssue68B37Legend = input.bool(true, "顯示右上角狀態表", group=groupIssue68B37)

issue68B37Ready = bar_index >= rankLen - 1
bool issue68B37Bull = issue68B37Direction == "Bull"
int issue68B37TargetSign = issue68B37Bull ? 1 : -1

f_issue68B37Dir(int stage) => stage == 2 or stage == 3 ? 1 : stage == 5 or stage == 6 ? -1 : 0
f_issue68B37Align(int dir) => dir == issue68B37TargetSign ? 1 : dir == 0 ? 0 : -1
f_issue68B37PassColor(int x) => x == 1 ? colGreen : x == -1 ? colRed : colNeutral
f_issue68B37PassText(int x) => x == 1 ? "YES" : x == -1 ? "NO" : "N/A"
f_issue68B37AlignText(int x) => x == 1 ? "ALIGNED" : x == -1 ? "OPPOSITE" : "NEUTRAL"
f_issue68B37BandColor(int x) => color.new(f_issue68B37PassColor(x), x == 0 ? 68 : 18)

float issue68B37TargetRaw = issue68B37Bull ? math.max(markupRaw, reaccRaw) : math.max(markdownRaw, redistRaw)
float issue68B37OtherRaw = issue68B37Bull ? math.max(math.max(accRaw, distRaw), math.max(markdownRaw, redistRaw)) : math.max(math.max(accRaw, distRaw), math.max(markupRaw, reaccRaw))
float issue68B37TargetEff = issue68B37Bull ? math.max(markupEff, reaccEff) : math.max(markdownEff, redistEff)
float issue68B37OtherEff = issue68B37Bull ? math.max(math.max(accEff, distEff), math.max(markdownEff, redistEff)) : math.max(math.max(accEff, distEff), math.max(markupEff, reaccEff))
float issue68B37PrecursorEff = issue68B37Bull ? accEff : distEff
float issue68B37OppRangeEff = issue68B37Bull ? distEff : accEff
float issue68B37OppTrendEff = issue68B37Bull ? math.max(markdownEff, redistEff) : math.max(markupEff, reaccEff)

bool issue68B37TargetTopBool = issue68B37Bull ? (topId == 2 or topId == 3) : (topId == 5 or topId == 6)
int issue68B37TargetTop = not issue68B37Ready ? 0 : (issue68B37TargetTopBool ? 1 : -1)
int issue68B37RawAdv = not issue68B37Ready ? 0 : (issue68B37TargetRaw > issue68B37OtherRaw ? 1 : -1)
int issue68B37PrecursorBlock = not issue68B37Ready ? 0 : (issue68B37PrecursorEff > issue68B37TargetEff ? -1 : 1)
int issue68B37OppRangeBlock = not issue68B37Ready ? 0 : (issue68B37OppRangeEff > issue68B37TargetEff ? -1 : 1)
int issue68B37OppTrendBlock = not issue68B37Ready ? 0 : (issue68B37OppTrendEff > issue68B37TargetEff ? -1 : 1)
int issue68B37FormalAlign = issue68B37Ready ? f_issue68B37Align(f_issue68B37Dir(formalId)) : 0

// Frozen B3.3 Core Bias Memory.
var int issue68B37Core = 0
int issue68B37CoreBefore = issue68B37Core
if issue68B37Ready
    int issue68B37CoreAfter = issue68B37CoreBefore
    if issue68B37CoreBefore == 0
        if formalId == 2
            issue68B37CoreAfter := 1
        else if formalId == 5
            issue68B37CoreAfter := -1
        else
            issue68B37CoreAfter := 0
    else if issue68B37CoreBefore == 1
        issue68B37CoreAfter := formalId == 5 or formalId == 6 ? -1 : 1
    else if issue68B37CoreBefore == -1
        issue68B37CoreAfter := formalId == 2 or formalId == 3 ? 1 : -1
    issue68B37Core := issue68B37CoreAfter
else
    issue68B37Core := 0
int issue68B37CoreAlign = issue68B37Ready ? f_issue68B37Align(issue68B37Core) : 0

float issue68B37Half = 0.34
float cTargetTop = 6.0
float cRawAdv = 5.0
float cPrecursor = 4.0
float cOppRange = 3.0
float cOppTrend = 2.0
float cFormal = 1.0
float cCore = 0.0

pTargetTopHi = plot(issue68B37Ready ? cTargetTop + issue68B37Half : na, "TARGET TOP top", color=color.new(colNeutral, 100), display=display.pane)
pTargetTopLo = plot(issue68B37Ready ? cTargetTop - issue68B37Half : na, "TARGET TOP bottom", color=color.new(colNeutral, 100), display=display.pane)
pRawAdvHi = plot(issue68B37Ready ? cRawAdv + issue68B37Half : na, "RAW ADV top", color=color.new(colNeutral, 100), display=display.pane)
pRawAdvLo = plot(issue68B37Ready ? cRawAdv - issue68B37Half : na, "RAW ADV bottom", color=color.new(colNeutral, 100), display=display.pane)
pPrecursorHi = plot(issue68B37Ready ? cPrecursor + issue68B37Half : na, "PRECURSOR BLOCK top", color=color.new(colNeutral, 100), display=display.pane)
pPrecursorLo = plot(issue68B37Ready ? cPrecursor - issue68B37Half : na, "PRECURSOR BLOCK bottom", color=color.new(colNeutral, 100), display=display.pane)
pOppRangeHi = plot(issue68B37Ready ? cOppRange + issue68B37Half : na, "OPP RANGE BLOCK top", color=color.new(colNeutral, 100), display=display.pane)
pOppRangeLo = plot(issue68B37Ready ? cOppRange - issue68B37Half : na, "OPP RANGE BLOCK bottom", color=color.new(colNeutral, 100), display=display.pane)
pOppTrendHi = plot(issue68B37Ready ? cOppTrend + issue68B37Half : na, "OPP TREND BLOCK top", color=color.new(colNeutral, 100), display=display.pane)
pOppTrendLo = plot(issue68B37Ready ? cOppTrend - issue68B37Half : na, "OPP TREND BLOCK bottom", color=color.new(colNeutral, 100), display=display.pane)
pFormalHi = plot(issue68B37Ready ? cFormal + issue68B37Half : na, "FORMAL ALIGN top", color=color.new(colNeutral, 100), display=display.pane)
pFormalLo = plot(issue68B37Ready ? cFormal - issue68B37Half : na, "FORMAL ALIGN bottom", color=color.new(colNeutral, 100), display=display.pane)
pCoreHi = plot(issue68B37Ready ? cCore + issue68B37Half : na, "CORE ALIGN top", color=color.new(colNeutral, 100), display=display.pane)
pCoreLo = plot(issue68B37Ready ? cCore - issue68B37Half : na, "CORE ALIGN bottom", color=color.new(colNeutral, 100), display=display.pane)

fill(pTargetTopHi, pTargetTopLo, color=issue68B37Ready ? f_issue68B37BandColor(issue68B37TargetTop) : na, title="TARGET TOP band")
fill(pRawAdvHi, pRawAdvLo, color=issue68B37Ready ? f_issue68B37BandColor(issue68B37RawAdv) : na, title="RAW ADV band")
fill(pPrecursorHi, pPrecursorLo, color=issue68B37Ready ? f_issue68B37BandColor(issue68B37PrecursorBlock) : na, title="PRECURSOR BLOCK band")
fill(pOppRangeHi, pOppRangeLo, color=issue68B37Ready ? f_issue68B37BandColor(issue68B37OppRangeBlock) : na, title="OPP RANGE BLOCK band")
fill(pOppTrendHi, pOppTrendLo, color=issue68B37Ready ? f_issue68B37BandColor(issue68B37OppTrendBlock) : na, title="OPP TREND BLOCK band")
fill(pFormalHi, pFormalLo, color=issue68B37Ready ? f_issue68B37BandColor(issue68B37FormalAlign) : na, title="FORMAL ALIGN band")
fill(pCoreHi, pCoreLo, color=issue68B37Ready ? f_issue68B37BandColor(issue68B37CoreAlign) : na, title="CORE ALIGN band")

var table issue68B37Legend = table.new(position.top_right, 2, 9, border_width=1)
if barstate.islast
    if showIssue68B37Legend
        table.cell(issue68B37Legend, 0, 0, "LAYER", text_color=color.white, bgcolor=color.new(colNeutral, 15))
        table.cell(issue68B37Legend, 1, 0, "NOW", text_color=color.white, bgcolor=color.new(colNeutral, 15))
        table.cell(issue68B37Legend, 0, 1, "TARGET｜審計方向", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B37Legend, 1, 1, issue68B37Direction, text_color=color.white, bgcolor=color.new(colNeutral, 15))
        table.cell(issue68B37Legend, 0, 2, "TARGET TOP｜目標為最高", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B37Legend, 1, 2, f_issue68B37PassText(issue68B37TargetTop), text_color=color.white, bgcolor=f_issue68B37PassColor(issue68B37TargetTop))
        table.cell(issue68B37Legend, 0, 3, "RAW ADV｜原始分數領先", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B37Legend, 1, 3, f_issue68B37PassText(issue68B37RawAdv), text_color=color.white, bgcolor=f_issue68B37PassColor(issue68B37RawAdv))
        table.cell(issue68B37Legend, 0, 4, "PRECURSOR｜前置 range 清除", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B37Legend, 1, 4, f_issue68B37PassText(issue68B37PrecursorBlock), text_color=color.white, bgcolor=f_issue68B37PassColor(issue68B37PrecursorBlock))
        table.cell(issue68B37Legend, 0, 5, "OPP RANGE｜反向 range 清除", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B37Legend, 1, 5, f_issue68B37PassText(issue68B37OppRangeBlock), text_color=color.white, bgcolor=f_issue68B37PassColor(issue68B37OppRangeBlock))
        table.cell(issue68B37Legend, 0, 6, "OPP TREND｜反向趨勢清除", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B37Legend, 1, 6, f_issue68B37PassText(issue68B37OppTrendBlock), text_color=color.white, bgcolor=f_issue68B37PassColor(issue68B37OppTrendBlock))
        table.cell(issue68B37Legend, 0, 7, "FORMAL｜正式對齊", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B37Legend, 1, 7, f_issue68B37AlignText(issue68B37FormalAlign), text_color=color.white, bgcolor=f_issue68B37PassColor(issue68B37FormalAlign))
        table.cell(issue68B37Legend, 0, 8, "CORE｜方向記憶對齊", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B37Legend, 1, 8, f_issue68B37AlignText(issue68B37CoreAlign), text_color=color.white, bgcolor=f_issue68B37PassColor(issue68B37CoreAlign))
    else
        table.clear(issue68B37Legend, 0, 0, 1, 8)

plot(issue68B37TargetRaw, "B37 target raw", display=display.data_window)
plot(issue68B37OtherRaw, "B37 other raw", display=display.data_window)
plot(issue68B37TargetRaw - issue68B37OtherRaw, "B37 raw margin", display=display.data_window)
plot(issue68B37TargetEff, "B37 target effective", display=display.data_window)
plot(issue68B37OtherEff, "B37 other effective", display=display.data_window)
plot(issue68B37TargetEff - issue68B37OtherEff, "B37 effective margin", display=display.data_window)
plot(float(topId), "B37 top id", display=display.data_window)
plot(float(formalId), "B37 formal id", display=display.data_window)
plot(float(issue68B37Core), "B37 core bias", display=display.data_window)
'''.strip()


def generate(source: Path) -> str:
    d1_text = phase_b.d1.generate(source)
    if d1_text.count(phase_b.D1_EXPORT_MARKER) != 1:
        raise RuntimeError("expected exactly one D1 parity export marker")
    core = d1_text.split(phase_b.D1_EXPORT_MARKER, 1)[0].rstrip()
    core = replace_once(core, phase_b.D1_INDICATOR_DECL, AUDIT_DECL)
    out = core + "\n\n" + B37_BODY + "\n"
    required = (
        "Issue #66 C-2 runtime-validated price-only lineage",
        'volumeMode = "Off"',
        'mtfMode = "Off"',
        'divMode = "Off"',
        "TARGET TOP band",
        "RAW ADV band",
        "PRECURSOR BLOCK band",
        "OPP RANGE BLOCK band",
        "OPP TREND BLOCK band",
        "issue68B37TargetRaw > issue68B37OtherRaw",
        "issue68B37PrecursorEff > issue68B37TargetEff",
    )
    for token in required:
        if token not in out:
            raise RuntimeError(f"missing B3.7 audit token: {token}")
    for token in ("strategy.", "issue68B34A", "issue68B34B", "issue68B34C", "D1B|"):
        if token in out:
            raise RuntimeError(f"forbidden token leaked into B3.7 audit: {token}")
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
