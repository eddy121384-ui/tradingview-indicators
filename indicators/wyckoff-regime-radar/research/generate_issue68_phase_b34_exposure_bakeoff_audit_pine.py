#!/usr/bin/env python3
"""Generate Issue #68 Phase B3.4 no-PnL exposure-policy bakeoff audit Pine."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_phase_b_lifecycle_pine as phase_b
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 Exposure B3.4 Bakeoff", shorttitle="ChaseRisk #68 B34", overlay=false, precision=2)'

B34_BODY = r'''

// ============================================================================
// Issue #66 C-2 runtime-validated price-only lineage.
// Issue #68 Phase B3.4 preregistered Exposure Policy Bakeoff.
// Core Bias is frozen B3.3 regime memory. Exposure candidates are NO-PNL.
// A = Formal trend family; B = Flat Action authorization;
// C = Flat Action entry + mirrored Pace defensive-flat state machine.
// Human-readable audit UI only: band rendering does not change A/B/C semantics.
// ============================================================================

groupIssue68B34 = "Issue #68｜Exposure B3.4 Bakeoff"
showIssue68B34StageBg = input.bool(false, "輔助｜顯示極淡 Formal Stage 背景", group=groupIssue68B34)
showIssue68B34Bias = input.bool(true, "顯示 CORE｜大方向記憶", group=groupIssue68B34)
showIssue68B34A = input.bool(true, "顯示 A｜Formal trend-family", group=groupIssue68B34)
showIssue68B34B = input.bool(true, "顯示 B｜Flat Action authorization", group=groupIssue68B34)
showIssue68B34C = input.bool(true, "顯示 C｜Flat Action + Pace stateful", group=groupIssue68B34)
showIssue68B34Marks = input.bool(false, "輔助｜顯示 L/S/F 切換標記", group=groupIssue68B34)
showIssue68B34Legend = input.bool(true, "顯示右上角狀態表", group=groupIssue68B34)

issue68B34Ready = bar_index >= rankLen - 1

// --- Frozen B3.3 Core Bias Memory ---
var int issue68B34Bias = 0
int issue68B34BiasBefore = issue68B34Bias
if issue68B34Ready
    int issue68B34Stage = formalId
    int issue68B34BiasAfter = issue68B34BiasBefore
    if issue68B34BiasBefore == 0
        if issue68B34Stage == 2
            issue68B34BiasAfter := 1
        else if issue68B34Stage == 5
            issue68B34BiasAfter := -1
        else
            issue68B34BiasAfter := 0
    else if issue68B34BiasBefore == 1
        issue68B34BiasAfter := issue68B34Stage == 5 or issue68B34Stage == 6 ? -1 : 1
    else if issue68B34BiasBefore == -1
        issue68B34BiasAfter := issue68B34Stage == 2 or issue68B34Stage == 3 ? 1 : -1
    issue68B34Bias := issue68B34BiasAfter
else
    issue68B34Bias := 0

// --- Candidate A: Formal trend-family exposure ---
int issue68B34A = 0
if issue68B34Ready
    if issue68B34Bias == 1 and (formalId == 2 or formalId == 3)
        issue68B34A := 1
    else if issue68B34Bias == -1 and (formalId == 5 or formalId == 6)
        issue68B34A := -1

// --- Candidate B: existing Flat Action authorization only ---
int issue68B34B = 0
if issue68B34Ready
    if issue68B34Bias == 1 and (flatActionLevel == 2 or flatActionLevel == 3)
        issue68B34B := 1
    else if issue68B34Bias == -1 and (flatActionLevel == 4 or flatActionLevel == 5)
        issue68B34B := -1

// --- Candidate C: Flat Action entry/re-entry + mirrored Pace defensive flat ---
bool issue68B34LongDefensive = paceCode == 0 or paceCode == 40 or paceCode == 70 or paceCode == 71 or paceCode == 75
bool issue68B34ShortDefensive = paceCode == 0 or paceCode == 15 or paceCode == 70 or paceCode == 71 or paceCode == 74
bool issue68B34LongEntryOk = flatActionLevel == 2 or flatActionLevel == 3
bool issue68B34ShortEntryOk = flatActionLevel == 4 or flatActionLevel == 5

var int issue68B34C = 0
int issue68B34CBefore = issue68B34C
int issue68B34CAfter = issue68B34CBefore
if issue68B34Ready
    if issue68B34Bias == 0
        issue68B34CAfter := 0
    else if issue68B34CBefore != 0 and issue68B34CBefore != issue68B34Bias
        // Bias reversal forces an observation bar; no direct executable flip.
        issue68B34CAfter := 0
    else if issue68B34CBefore == 0
        if issue68B34Bias == 1 and issue68B34LongEntryOk
            issue68B34CAfter := 1
        else if issue68B34Bias == -1 and issue68B34ShortEntryOk
            issue68B34CAfter := -1
        else
            issue68B34CAfter := 0
    else if issue68B34CBefore == 1
        issue68B34CAfter := issue68B34LongDefensive ? 0 : 1
    else if issue68B34CBefore == -1
        issue68B34CAfter := issue68B34ShortDefensive ? 0 : -1
    issue68B34C := issue68B34CAfter
else
    issue68B34C := 0

// Hard directional invariants: no candidate may oppose frozen Core Bias.
bool issue68B34ViolationA = (issue68B34A == 1 and issue68B34Bias != 1) or (issue68B34A == -1 and issue68B34Bias != -1)
bool issue68B34ViolationB = (issue68B34B == 1 and issue68B34Bias != 1) or (issue68B34B == -1 and issue68B34Bias != -1)
bool issue68B34ViolationC = (issue68B34C == 1 and issue68B34Bias != 1) or (issue68B34C == -1 and issue68B34Bias != -1)

// Cumulative semantic counters for Data Window only; not performance metrics.
var int issue68B34Bars = 0
var int issue68B34FlatA = 0
var int issue68B34FlatB = 0
var int issue68B34FlatC = 0
var int issue68B34TransitionsA = 0
var int issue68B34TransitionsB = 0
var int issue68B34TransitionsC = 0
if issue68B34Ready
    issue68B34Bars += 1
    issue68B34FlatA += issue68B34A == 0 ? 1 : 0
    issue68B34FlatB += issue68B34B == 0 ? 1 : 0
    issue68B34FlatC += issue68B34C == 0 ? 1 : 0
    if issue68B34Ready[1]
        issue68B34TransitionsA += issue68B34A != issue68B34A[1] ? 1 : 0
        issue68B34TransitionsB += issue68B34B != issue68B34B[1] ? 1 : 0
        issue68B34TransitionsC += issue68B34C != issue68B34C[1] ? 1 : 0

// ============================================================================
// Human-readable audit rendering.
// Green = Long / bullish bias, gray = Flat / Observe, red = Short / bearish bias.
// Lane y-levels are layout coordinates only and have no financial meaning.
// ============================================================================
f_issue68B34Color(int x) => x == 1 ? colGreen : x == -1 ? colRed : colNeutral
f_issue68B34StateText(int x) => x == 1 ? "LONG" : x == -1 ? "SHORT" : "FLAT"
f_issue68B34BandColor(int x) => color.new(f_issue68B34Color(x), x == 0 ? 68 : 18)

float issue68B34LaneHalf = 0.34
float issue68B34CoreCenter = 3.0
float issue68B34ACenter = 2.0
float issue68B34BCenter = 1.0
float issue68B34CCenter = 0.0

color issue68B34StageColor = formalId == 1 ? colAcc : formalId == 2 ? colMarkup : formalId == 3 ? colReacc : formalId == 4 ? colDist : formalId == 5 ? colMarkdown : formalId == 6 ? colRedist : colNeutral
bgcolor(showIssue68B34StageBg and issue68B34Ready ? color.new(issue68B34StageColor, 96) : na, title="Issue68 B34 Formal Stage")

// Invisible band boundaries. The fills are the primary audit visualization.
issue68B34CoreTop = plot(showIssue68B34Bias and issue68B34Ready ? issue68B34CoreCenter + issue68B34LaneHalf : na, "CORE band top", color=color.new(colNeutral, 100), display=display.pane)
issue68B34CoreBottom = plot(showIssue68B34Bias and issue68B34Ready ? issue68B34CoreCenter - issue68B34LaneHalf : na, "CORE band bottom", color=color.new(colNeutral, 100), display=display.pane)
issue68B34ATop = plot(showIssue68B34A and issue68B34Ready ? issue68B34ACenter + issue68B34LaneHalf : na, "A band top", color=color.new(colNeutral, 100), display=display.pane)
issue68B34ABottom = plot(showIssue68B34A and issue68B34Ready ? issue68B34ACenter - issue68B34LaneHalf : na, "A band bottom", color=color.new(colNeutral, 100), display=display.pane)
issue68B34BTop = plot(showIssue68B34B and issue68B34Ready ? issue68B34BCenter + issue68B34LaneHalf : na, "B band top", color=color.new(colNeutral, 100), display=display.pane)
issue68B34BBottom = plot(showIssue68B34B and issue68B34Ready ? issue68B34BCenter - issue68B34LaneHalf : na, "B band bottom", color=color.new(colNeutral, 100), display=display.pane)
issue68B34CTop = plot(showIssue68B34C and issue68B34Ready ? issue68B34CCenter + issue68B34LaneHalf : na, "C band top", color=color.new(colNeutral, 100), display=display.pane)
issue68B34CBottom = plot(showIssue68B34C and issue68B34Ready ? issue68B34CCenter - issue68B34LaneHalf : na, "C band bottom", color=color.new(colNeutral, 100), display=display.pane)

fill(issue68B34CoreTop, issue68B34CoreBottom, color=showIssue68B34Bias and issue68B34Ready ? f_issue68B34BandColor(issue68B34Bias) : na, title="CORE Bias band")
fill(issue68B34ATop, issue68B34ABottom, color=showIssue68B34A and issue68B34Ready ? f_issue68B34BandColor(issue68B34A) : na, title="A Formal-family exposure")
fill(issue68B34BTop, issue68B34BBottom, color=showIssue68B34B and issue68B34Ready ? f_issue68B34BandColor(issue68B34B) : na, title="B Flat-Action exposure")
fill(issue68B34CTop, issue68B34CBottom, color=showIssue68B34C and issue68B34Ready ? f_issue68B34BandColor(issue68B34C) : na, title="C Stateful exposure")

// Optional transition marks. Off by default so the first-look audit remains clean.
bool issue68B34BiasChanged = issue68B34Ready and issue68B34Ready[1] and issue68B34Bias != issue68B34Bias[1]
bool issue68B34AChanged = issue68B34Ready and issue68B34Ready[1] and issue68B34A != issue68B34A[1]
bool issue68B34BChanged = issue68B34Ready and issue68B34Ready[1] and issue68B34B != issue68B34B[1]
bool issue68B34CChanged = issue68B34Ready and issue68B34Ready[1] and issue68B34C != issue68B34C[1]

plotshape(showIssue68B34Marks and showIssue68B34Bias and issue68B34BiasChanged and issue68B34Bias == 1 ? issue68B34CoreCenter : na, "CORE -> LONG", style=shape.labelup, location=location.absolute, color=colGreen, text="L", textcolor=color.white, size=size.tiny)
plotshape(showIssue68B34Marks and showIssue68B34Bias and issue68B34BiasChanged and issue68B34Bias == -1 ? issue68B34CoreCenter : na, "CORE -> SHORT", style=shape.labeldown, location=location.absolute, color=colRed, text="S", textcolor=color.white, size=size.tiny)
plotshape(showIssue68B34Marks and showIssue68B34Bias and issue68B34BiasChanged and issue68B34Bias == 0 ? issue68B34CoreCenter : na, "CORE -> FLAT", style=shape.circle, location=location.absolute, color=colNeutral, text="F", textcolor=color.white, size=size.tiny)

plotshape(showIssue68B34Marks and showIssue68B34A and issue68B34AChanged and issue68B34A == 1 ? issue68B34ACenter : na, "A -> LONG", style=shape.labelup, location=location.absolute, color=colGreen, text="L", textcolor=color.white, size=size.tiny)
plotshape(showIssue68B34Marks and showIssue68B34A and issue68B34AChanged and issue68B34A == -1 ? issue68B34ACenter : na, "A -> SHORT", style=shape.labeldown, location=location.absolute, color=colRed, text="S", textcolor=color.white, size=size.tiny)
plotshape(showIssue68B34Marks and showIssue68B34A and issue68B34AChanged and issue68B34A == 0 ? issue68B34ACenter : na, "A -> FLAT", style=shape.circle, location=location.absolute, color=colNeutral, text="F", textcolor=color.white, size=size.tiny)

plotshape(showIssue68B34Marks and showIssue68B34B and issue68B34BChanged and issue68B34B == 1 ? issue68B34BCenter : na, "B -> LONG", style=shape.labelup, location=location.absolute, color=colGreen, text="L", textcolor=color.white, size=size.tiny)
plotshape(showIssue68B34Marks and showIssue68B34B and issue68B34BChanged and issue68B34B == -1 ? issue68B34BCenter : na, "B -> SHORT", style=shape.labeldown, location=location.absolute, color=colRed, text="S", textcolor=color.white, size=size.tiny)
plotshape(showIssue68B34Marks and showIssue68B34B and issue68B34BChanged and issue68B34B == 0 ? issue68B34BCenter : na, "B -> FLAT", style=shape.circle, location=location.absolute, color=colNeutral, text="F", textcolor=color.white, size=size.tiny)

plotshape(showIssue68B34Marks and showIssue68B34C and issue68B34CChanged and issue68B34C == 1 ? issue68B34CCenter : na, "C -> LONG", style=shape.labelup, location=location.absolute, color=colGreen, text="L", textcolor=color.white, size=size.tiny)
plotshape(showIssue68B34Marks and showIssue68B34C and issue68B34CChanged and issue68B34C == -1 ? issue68B34CCenter : na, "C -> SHORT", style=shape.labeldown, location=location.absolute, color=colRed, text="S", textcolor=color.white, size=size.tiny)
plotshape(showIssue68B34Marks and showIssue68B34C and issue68B34CChanged and issue68B34C == 0 ? issue68B34CCenter : na, "C -> FLAT", style=shape.circle, location=location.absolute, color=colNeutral, text="F", textcolor=color.white, size=size.tiny)

// Compact current-state legend. Historical reading comes from the four color bands.
var table issue68B34Legend = table.new(position.top_right, 2, 5, border_width=1)
if barstate.islast
    if showIssue68B34Legend
        table.cell(issue68B34Legend, 0, 0, "LANE", text_color=color.white, bgcolor=color.new(colNeutral, 15), text_size=size.small)
        table.cell(issue68B34Legend, 1, 0, "NOW", text_color=color.white, bgcolor=color.new(colNeutral, 15), text_size=size.small)
        table.cell(issue68B34Legend, 0, 1, "CORE｜方向記憶", text_color=color.white, bgcolor=color.new(colNeutral, 45), text_size=size.small)
        table.cell(issue68B34Legend, 1, 1, f_issue68B34StateText(issue68B34Bias), text_color=color.white, bgcolor=f_issue68B34Color(issue68B34Bias), text_size=size.small)
        table.cell(issue68B34Legend, 0, 2, "A｜Formal", text_color=color.white, bgcolor=color.new(colNeutral, 45), text_size=size.small)
        table.cell(issue68B34Legend, 1, 2, f_issue68B34StateText(issue68B34A), text_color=color.white, bgcolor=f_issue68B34Color(issue68B34A), text_size=size.small)
        table.cell(issue68B34Legend, 0, 3, "B｜Flat Action", text_color=color.white, bgcolor=color.new(colNeutral, 45), text_size=size.small)
        table.cell(issue68B34Legend, 1, 3, f_issue68B34StateText(issue68B34B), text_color=color.white, bgcolor=f_issue68B34Color(issue68B34B), text_size=size.small)
        table.cell(issue68B34Legend, 0, 4, "C｜Stateful", text_color=color.white, bgcolor=color.new(colNeutral, 45), text_size=size.small)
        table.cell(issue68B34Legend, 1, 4, f_issue68B34StateText(issue68B34C), text_color=color.white, bgcolor=f_issue68B34Color(issue68B34C), text_size=size.small)
    else
        table.clear(issue68B34Legend, 0, 0, 1, 4)

plot(float(formalId), "B34 Formal Stage ID", display=display.data_window)
plot(float(issue68B34Bias), "B34 Core Bias", display=display.data_window)
plot(float(flatActionLevel), "B34 Flat Action Level", display=display.data_window)
plot(float(paceCode), "B34 Pace Code", display=display.data_window)
plot(float(issue68B34A), "B34 Exposure A", display=display.data_window)
plot(float(issue68B34B), "B34 Exposure B", display=display.data_window)
plot(float(issue68B34C), "B34 Exposure C", display=display.data_window)
plot(issue68B34Bars > 0 ? 100.0 * float(issue68B34FlatA) / float(issue68B34Bars) : na, "B34 A Flat share %", display=display.data_window)
plot(issue68B34Bars > 0 ? 100.0 * float(issue68B34FlatB) / float(issue68B34Bars) : na, "B34 B Flat share %", display=display.data_window)
plot(issue68B34Bars > 0 ? 100.0 * float(issue68B34FlatC) / float(issue68B34Bars) : na, "B34 C Flat share %", display=display.data_window)
plot(float(issue68B34TransitionsA), "B34 A transitions", display=display.data_window)
plot(float(issue68B34TransitionsB), "B34 B transitions", display=display.data_window)
plot(float(issue68B34TransitionsC), "B34 C transitions", display=display.data_window)
plot(issue68B34ViolationA ? 1.0 : 0.0, "B34 A bias violation", display=display.data_window)
plot(issue68B34ViolationB ? 1.0 : 0.0, "B34 B bias violation", display=display.data_window)
plot(issue68B34ViolationC ? 1.0 : 0.0, "B34 C bias violation", display=display.data_window)
'''.strip()


def generate(source: Path) -> str:
    d1_text = phase_b.d1.generate(source)
    if d1_text.count(phase_b.D1_EXPORT_MARKER) != 1:
        raise RuntimeError("expected exactly one D1 parity export marker")
    core = d1_text.split(phase_b.D1_EXPORT_MARKER, 1)[0].rstrip()
    core = replace_once(core, phase_b.D1_INDICATOR_DECL, AUDIT_DECL)
    out = core + "\n\n" + B34_BODY + "\n"

    required = (
        "Issue #66 C-2",
        'volumeMode = "Off"',
        'mtfMode = "Off"',
        'divMode = "Off"',
        "flatActionLevel",
        "paceCode",
        "A Formal-family exposure",
        "B Flat-Action exposure",
        "C Stateful exposure",
        "no direct executable flip",
        "issue68B34ViolationC",
        "Human-readable audit rendering",
        "CORE Bias band",
        "showIssue68B34Marks = input.bool(false",
        "showIssue68B34StageBg = input.bool(false",
        "table.new(position.top_right, 2, 5",
    )
    for token in required:
        if token not in out:
            raise RuntimeError(f"missing B3.4 audit token: {token}")

    forbidden = (
        "strategy.",
        "issue68ArmedDir",
        "issue68EarlyFail",
        "LONG SETUP",
        "SHORT SETUP",
        "D1B|",
        "plot.style_stepline",
    )
    for token in forbidden:
        if token in out:
            raise RuntimeError(f"forbidden legacy/strategy/parity/UI token leaked into B3.4 audit: {token}")
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
