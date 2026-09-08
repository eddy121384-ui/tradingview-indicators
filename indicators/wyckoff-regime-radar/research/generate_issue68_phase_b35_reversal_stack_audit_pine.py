#!/usr/bin/env python3
"""Generate Issue #68 B3.5 TOP/STRONG/FORMAL/CORE reversal-stack audit Pine."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_phase_b_lifecycle_pine as phase_b
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 B3.5 Reversal Stack", shorttitle="ChaseRisk #68 B35", overlay=false, precision=2)'

B35_BODY = r'''

// ============================================================================
// Issue #66 C-2 runtime-validated price-only lineage.
// Issue #68 Phase B3.5 preregistered reversal-stack forensic.
// No classifier, persistence, B3.3 bias, exposure, or strategy semantics changed.
// TOP -> STRONG -> FORMAL -> CORE localizes reversal latency; no performance use.
// ============================================================================

groupIssue68B35 = "Issue #68｜B3.5 Reversal Stack"
showIssue68B35Top = input.bool(true, "顯示 TOP｜當下最高權重趨勢方向", group=groupIssue68B35)
showIssue68B35Strong = input.bool(true, "顯示 STRONG｜強候選趨勢方向", group=groupIssue68B35)
showIssue68B35Formal = input.bool(true, "顯示 FORMAL｜正式趨勢方向", group=groupIssue68B35)
showIssue68B35Core = input.bool(true, "顯示 CORE｜B3.3 大方向記憶", group=groupIssue68B35)
showIssue68B35Marks = input.bool(false, "輔助｜顯示 CORE 翻向標記", group=groupIssue68B35)
showIssue68B35Legend = input.bool(true, "顯示右上角狀態表", group=groupIssue68B35)

issue68B35Ready = bar_index >= rankLen - 1

f_issue68B35TrendDir(int stage) => stage == 2 or stage == 3 ? 1 : stage == 5 or stage == 6 ? -1 : 0
f_issue68B35Color(int x) => x == 1 ? colGreen : x == -1 ? colRed : colNeutral
f_issue68B35Text(int x) => x == 1 ? "BULL" : x == -1 ? "BEAR" : "NEUTRAL"
f_issue68B35BandColor(int x) => color.new(f_issue68B35Color(x), x == 0 ? 68 : 18)

int issue68B35Top = issue68B35Ready ? f_issue68B35TrendDir(topId) : 0
int issue68B35Strong = issue68B35Ready and strongCandidate ? issue68B35Top : 0
int issue68B35Formal = issue68B35Ready ? f_issue68B35TrendDir(formalId) : 0

// Frozen B3.3 Core Bias Memory: byte-for-byte semantic translation of the accepted state machine.
var int issue68B35Core = 0
int issue68B35CoreBefore = issue68B35Core
bool issue68B35FlipUp = false
bool issue68B35FlipDn = false
if issue68B35Ready
    int issue68B35CoreAfter = issue68B35CoreBefore
    if issue68B35CoreBefore == 0
        if formalId == 2
            issue68B35CoreAfter := 1
        else if formalId == 5
            issue68B35CoreAfter := -1
        else
            issue68B35CoreAfter := 0
    else if issue68B35CoreBefore == 1
        issue68B35CoreAfter := formalId == 5 or formalId == 6 ? -1 : 1
    else if issue68B35CoreBefore == -1
        issue68B35CoreAfter := formalId == 2 or formalId == 3 ? 1 : -1
    issue68B35FlipUp := issue68B35CoreBefore == -1 and issue68B35CoreAfter == 1
    issue68B35FlipDn := issue68B35CoreBefore == 1 and issue68B35CoreAfter == -1
    issue68B35Core := issue68B35CoreAfter
else
    issue68B35Core := 0

// Hard forensic invariant: once opposite Formal trend family exists, Core flips on the same bar.
bool issue68B35CoreFormalViolation = (issue68B35Core == 1 and issue68B35CoreBefore == -1 and issue68B35Formal != 1) or (issue68B35Core == -1 and issue68B35CoreBefore == 1 and issue68B35Formal != -1)

float issue68B35Half = 0.34
float issue68B35TopCenter = 3.0
float issue68B35StrongCenter = 2.0
float issue68B35FormalCenter = 1.0
float issue68B35CoreCenter = 0.0

issue68B35TopHi = plot(showIssue68B35Top and issue68B35Ready ? issue68B35TopCenter + issue68B35Half : na, "TOP band top", color=color.new(colNeutral, 100), display=display.pane)
issue68B35TopLo = plot(showIssue68B35Top and issue68B35Ready ? issue68B35TopCenter - issue68B35Half : na, "TOP band bottom", color=color.new(colNeutral, 100), display=display.pane)
issue68B35StrongHi = plot(showIssue68B35Strong and issue68B35Ready ? issue68B35StrongCenter + issue68B35Half : na, "STRONG band top", color=color.new(colNeutral, 100), display=display.pane)
issue68B35StrongLo = plot(showIssue68B35Strong and issue68B35Ready ? issue68B35StrongCenter - issue68B35Half : na, "STRONG band bottom", color=color.new(colNeutral, 100), display=display.pane)
issue68B35FormalHi = plot(showIssue68B35Formal and issue68B35Ready ? issue68B35FormalCenter + issue68B35Half : na, "FORMAL band top", color=color.new(colNeutral, 100), display=display.pane)
issue68B35FormalLo = plot(showIssue68B35Formal and issue68B35Ready ? issue68B35FormalCenter - issue68B35Half : na, "FORMAL band bottom", color=color.new(colNeutral, 100), display=display.pane)
issue68B35CoreHi = plot(showIssue68B35Core and issue68B35Ready ? issue68B35CoreCenter + issue68B35Half : na, "CORE band top", color=color.new(colNeutral, 100), display=display.pane)
issue68B35CoreLo = plot(showIssue68B35Core and issue68B35Ready ? issue68B35CoreCenter - issue68B35Half : na, "CORE band bottom", color=color.new(colNeutral, 100), display=display.pane)

fill(issue68B35TopHi, issue68B35TopLo, color=showIssue68B35Top and issue68B35Ready ? f_issue68B35BandColor(issue68B35Top) : na, title="TOP direction band")
fill(issue68B35StrongHi, issue68B35StrongLo, color=showIssue68B35Strong and issue68B35Ready ? f_issue68B35BandColor(issue68B35Strong) : na, title="STRONG direction band")
fill(issue68B35FormalHi, issue68B35FormalLo, color=showIssue68B35Formal and issue68B35Ready ? f_issue68B35BandColor(issue68B35Formal) : na, title="FORMAL direction band")
fill(issue68B35CoreHi, issue68B35CoreLo, color=showIssue68B35Core and issue68B35Ready ? f_issue68B35BandColor(issue68B35Core) : na, title="CORE direction memory band")

plotshape(showIssue68B35Marks and issue68B35FlipUp ? issue68B35CoreCenter : na, "CORE flip bullish", style=shape.labelup, location=location.absolute, color=colGreen, text="FLIP+", textcolor=color.white, size=size.tiny)
plotshape(showIssue68B35Marks and issue68B35FlipDn ? issue68B35CoreCenter : na, "CORE flip bearish", style=shape.labeldown, location=location.absolute, color=colRed, text="FLIP-", textcolor=color.white, size=size.tiny)

var table issue68B35Legend = table.new(position.top_right, 2, 5, border_width=1)
if barstate.islast
    if showIssue68B35Legend
        table.cell(issue68B35Legend, 0, 0, "LAYER", text_color=color.white, bgcolor=color.new(colNeutral, 15), text_size=size.small)
        table.cell(issue68B35Legend, 1, 0, "NOW", text_color=color.white, bgcolor=color.new(colNeutral, 15), text_size=size.small)
        table.cell(issue68B35Legend, 0, 1, "TOP｜最高權重", text_color=color.white, bgcolor=color.new(colNeutral, 45), text_size=size.small)
        table.cell(issue68B35Legend, 1, 1, f_issue68B35Text(issue68B35Top), text_color=color.white, bgcolor=f_issue68B35Color(issue68B35Top), text_size=size.small)
        table.cell(issue68B35Legend, 0, 2, "STRONG｜強候選", text_color=color.white, bgcolor=color.new(colNeutral, 45), text_size=size.small)
        table.cell(issue68B35Legend, 1, 2, f_issue68B35Text(issue68B35Strong), text_color=color.white, bgcolor=f_issue68B35Color(issue68B35Strong), text_size=size.small)
        table.cell(issue68B35Legend, 0, 3, "FORMAL｜正式", text_color=color.white, bgcolor=color.new(colNeutral, 45), text_size=size.small)
        table.cell(issue68B35Legend, 1, 3, f_issue68B35Text(issue68B35Formal), text_color=color.white, bgcolor=f_issue68B35Color(issue68B35Formal), text_size=size.small)
        table.cell(issue68B35Legend, 0, 4, "CORE｜方向記憶", text_color=color.white, bgcolor=color.new(colNeutral, 45), text_size=size.small)
        table.cell(issue68B35Legend, 1, 4, f_issue68B35Text(issue68B35Core), text_color=color.white, bgcolor=f_issue68B35Color(issue68B35Core), text_size=size.small)
    else
        table.clear(issue68B35Legend, 0, 0, 1, 4)

plot(float(issue68B35Top), "B35 TOP direction", display=display.data_window)
plot(float(issue68B35Strong), "B35 STRONG direction", display=display.data_window)
plot(float(issue68B35Formal), "B35 FORMAL direction", display=display.data_window)
plot(float(issue68B35Core), "B35 CORE direction", display=display.data_window)
plot(float(candidateBars), "B35 candidate bars", display=display.data_window)
plot(float(activeConfirmBars), "B35 active confirm bars", display=display.data_window)
plot(candidateConflict ? 1.0 : 0.0, "B35 candidate conflict", display=display.data_window)
plot(issue68B35CoreFormalViolation ? 1.0 : 0.0, "B35 Formal-to-Core invariant violation", display=display.data_window)
'''.strip()


def generate(source: Path) -> str:
    d1_text = phase_b.d1.generate(source)
    if d1_text.count(phase_b.D1_EXPORT_MARKER) != 1:
        raise RuntimeError("expected exactly one D1 parity export marker")
    core = d1_text.split(phase_b.D1_EXPORT_MARKER, 1)[0].rstrip()
    core = replace_once(core, phase_b.D1_INDICATOR_DECL, AUDIT_DECL)
    out = core + "\n\n" + B35_BODY + "\n"

    required = (
        "Issue #66 C-2 runtime-validated price-only lineage",
        'volumeMode = "Off"',
        'mtfMode = "Off"',
        'divMode = "Off"',
        "TOP -> STRONG -> FORMAL -> CORE",
        "TOP direction band",
        "STRONG direction band",
        "FORMAL direction band",
        "CORE direction memory band",
        "formalId == 5 or formalId == 6 ? -1 : 1",
        "formalId == 2 or formalId == 3 ? 1 : -1",
    )
    for token in required:
        if token not in out:
            raise RuntimeError(f"missing B3.5 audit token: {token}")

    forbidden = (
        "strategy.",
        "issue68B34A",
        "issue68B34B",
        "issue68B34C",
        "LONG SETUP",
        "SHORT SETUP",
        "D1B|",
    )
    for token in forbidden:
        if token in out:
            raise RuntimeError(f"forbidden strategy/exposure/parity token leaked into B3.5 audit: {token}")
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
