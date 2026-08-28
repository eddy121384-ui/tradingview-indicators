#!/usr/bin/env python3
"""Generate Issue #68 B3.6 Strong formation blockage audit Pine."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_phase_b_lifecycle_pine as phase_b
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 B3.6 Strong Blockage", shorttitle="ChaseRisk #68 B36", overlay=false, precision=2)'

B36_BODY = r'''

// ============================================================================
// Issue #66 C-2 runtime-validated price-only lineage.
// Issue #68 B3.6 Strong formation blockage audit only.
// No classifier threshold, persistence, Core Bias, Exposure, or strategy change.
// ============================================================================

groupIssue68B36 = "Issue #68｜B3.6 Strong Blockage"
showIssue68B36Legend = input.bool(true, "顯示右上角狀態表", group=groupIssue68B36)

issue68B36Ready = bar_index >= rankLen - 1
f_issue68B36TrendDir(int stage) => stage == 2 or stage == 3 ? 1 : stage == 5 or stage == 6 ? -1 : 0
f_issue68B36DirColor(int x) => x == 1 ? colGreen : x == -1 ? colRed : colNeutral
f_issue68B36DirText(int x) => x == 1 ? "BULL" : x == -1 ? "BEAR" : "NEUTRAL"
f_issue68B36GateColor(int x) => x == 1 ? colGreen : x == -1 ? colRed : colNeutral
f_issue68B36GateText(int x) => x == 1 ? "PASS" : x == -1 ? "BLOCK" : "N/A"
f_issue68B36BandColor(int x, bool directional) => color.new(directional ? f_issue68B36DirColor(x) : f_issue68B36GateColor(x), x == 0 ? 68 : 18)

int issue68B36Top = issue68B36Ready ? f_issue68B36TrendDir(topId) : 0
bool issue68B36TrendTop = issue68B36Top != 0
int issue68B36Strong = issue68B36Ready and strongCandidate ? issue68B36Top : 0
int issue68B36DomGap = not issue68B36TrendTop ? 0 : (topVal >= dominantMin and topGap >= topGapMin ? 1 : -1)
int issue68B36Evidence = not issue68B36TrendTop ? 0 : (evidenceStrength >= evidenceMin ? 1 : -1)
int issue68B36ConflictFree = not issue68B36TrendTop ? 0 : (not candidateConflict ? 1 : -1)
int issue68B36Formal = issue68B36Ready ? f_issue68B36TrendDir(formalId) : 0

// Frozen B3.3 Core Bias Memory.
var int issue68B36Core = 0
int issue68B36CoreBefore = issue68B36Core
if issue68B36Ready
    int issue68B36CoreAfter = issue68B36CoreBefore
    if issue68B36CoreBefore == 0
        if formalId == 2
            issue68B36CoreAfter := 1
        else if formalId == 5
            issue68B36CoreAfter := -1
        else
            issue68B36CoreAfter := 0
    else if issue68B36CoreBefore == 1
        issue68B36CoreAfter := formalId == 5 or formalId == 6 ? -1 : 1
    else if issue68B36CoreBefore == -1
        issue68B36CoreAfter := formalId == 2 or formalId == 3 ? 1 : -1
    issue68B36Core := issue68B36CoreAfter
else
    issue68B36Core := 0

float issue68B36Half = 0.34
float cTop = 6.0
float cStrong = 5.0
float cDomGap = 4.0
float cEvidence = 3.0
float cConflict = 2.0
float cFormal = 1.0
float cCore = 0.0

pTopHi = plot(issue68B36Ready ? cTop + issue68B36Half : na, "TOP top", color=color.new(colNeutral, 100), display=display.pane)
pTopLo = plot(issue68B36Ready ? cTop - issue68B36Half : na, "TOP bottom", color=color.new(colNeutral, 100), display=display.pane)
pStrongHi = plot(issue68B36Ready ? cStrong + issue68B36Half : na, "STRONG top", color=color.new(colNeutral, 100), display=display.pane)
pStrongLo = plot(issue68B36Ready ? cStrong - issue68B36Half : na, "STRONG bottom", color=color.new(colNeutral, 100), display=display.pane)
pDomGapHi = plot(issue68B36Ready ? cDomGap + issue68B36Half : na, "DOM GAP top", color=color.new(colNeutral, 100), display=display.pane)
pDomGapLo = plot(issue68B36Ready ? cDomGap - issue68B36Half : na, "DOM GAP bottom", color=color.new(colNeutral, 100), display=display.pane)
pEvidenceHi = plot(issue68B36Ready ? cEvidence + issue68B36Half : na, "EVIDENCE top", color=color.new(colNeutral, 100), display=display.pane)
pEvidenceLo = plot(issue68B36Ready ? cEvidence - issue68B36Half : na, "EVIDENCE bottom", color=color.new(colNeutral, 100), display=display.pane)
pConflictHi = plot(issue68B36Ready ? cConflict + issue68B36Half : na, "CONFLICT top", color=color.new(colNeutral, 100), display=display.pane)
pConflictLo = plot(issue68B36Ready ? cConflict - issue68B36Half : na, "CONFLICT bottom", color=color.new(colNeutral, 100), display=display.pane)
pFormalHi = plot(issue68B36Ready ? cFormal + issue68B36Half : na, "FORMAL top", color=color.new(colNeutral, 100), display=display.pane)
pFormalLo = plot(issue68B36Ready ? cFormal - issue68B36Half : na, "FORMAL bottom", color=color.new(colNeutral, 100), display=display.pane)
pCoreHi = plot(issue68B36Ready ? cCore + issue68B36Half : na, "CORE top", color=color.new(colNeutral, 100), display=display.pane)
pCoreLo = plot(issue68B36Ready ? cCore - issue68B36Half : na, "CORE bottom", color=color.new(colNeutral, 100), display=display.pane)

fill(pTopHi, pTopLo, color=issue68B36Ready ? f_issue68B36BandColor(issue68B36Top, true) : na, title="TOP direction band")
fill(pStrongHi, pStrongLo, color=issue68B36Ready ? f_issue68B36BandColor(issue68B36Strong, true) : na, title="STRONG direction band")
fill(pDomGapHi, pDomGapLo, color=issue68B36Ready ? f_issue68B36BandColor(issue68B36DomGap, false) : na, title="DOM GAP gate band")
fill(pEvidenceHi, pEvidenceLo, color=issue68B36Ready ? f_issue68B36BandColor(issue68B36Evidence, false) : na, title="EVIDENCE gate band")
fill(pConflictHi, pConflictLo, color=issue68B36Ready ? f_issue68B36BandColor(issue68B36ConflictFree, false) : na, title="CONFLICT FREE gate band")
fill(pFormalHi, pFormalLo, color=issue68B36Ready ? f_issue68B36BandColor(issue68B36Formal, true) : na, title="FORMAL direction band")
fill(pCoreHi, pCoreLo, color=issue68B36Ready ? f_issue68B36BandColor(issue68B36Core, true) : na, title="CORE direction memory band")

var table issue68B36Legend = table.new(position.top_right, 2, 8, border_width=1)
if barstate.islast
    if showIssue68B36Legend
        table.cell(issue68B36Legend, 0, 0, "LAYER", text_color=color.white, bgcolor=color.new(colNeutral, 15))
        table.cell(issue68B36Legend, 1, 0, "NOW", text_color=color.white, bgcolor=color.new(colNeutral, 15))
        table.cell(issue68B36Legend, 0, 1, "TOP｜最高權重", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B36Legend, 1, 1, f_issue68B36DirText(issue68B36Top), text_color=color.white, bgcolor=f_issue68B36DirColor(issue68B36Top))
        table.cell(issue68B36Legend, 0, 2, "STRONG｜強候選", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B36Legend, 1, 2, f_issue68B36DirText(issue68B36Strong), text_color=color.white, bgcolor=f_issue68B36DirColor(issue68B36Strong))
        table.cell(issue68B36Legend, 0, 3, "DOM+GAP｜主導/差距", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B36Legend, 1, 3, f_issue68B36GateText(issue68B36DomGap), text_color=color.white, bgcolor=f_issue68B36GateColor(issue68B36DomGap))
        table.cell(issue68B36Legend, 0, 4, "EVID｜證據", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B36Legend, 1, 4, f_issue68B36GateText(issue68B36Evidence), text_color=color.white, bgcolor=f_issue68B36GateColor(issue68B36Evidence))
        table.cell(issue68B36Legend, 0, 5, "CONFLICT｜無衝突", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B36Legend, 1, 5, f_issue68B36GateText(issue68B36ConflictFree), text_color=color.white, bgcolor=f_issue68B36GateColor(issue68B36ConflictFree))
        table.cell(issue68B36Legend, 0, 6, "FORMAL｜正式", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B36Legend, 1, 6, f_issue68B36DirText(issue68B36Formal), text_color=color.white, bgcolor=f_issue68B36DirColor(issue68B36Formal))
        table.cell(issue68B36Legend, 0, 7, "CORE｜方向記憶", text_color=color.white, bgcolor=color.new(colNeutral, 45))
        table.cell(issue68B36Legend, 1, 7, f_issue68B36DirText(issue68B36Core), text_color=color.white, bgcolor=f_issue68B36DirColor(issue68B36Core))
    else
        table.clear(issue68B36Legend, 0, 0, 1, 7)

plot(float(issue68B36Top), "B36 TOP direction", display=display.data_window)
plot(float(issue68B36Strong), "B36 STRONG direction", display=display.data_window)
plot(float(issue68B36DomGap), "B36 DOM GAP gate", display=display.data_window)
plot(float(issue68B36Evidence), "B36 EVIDENCE gate", display=display.data_window)
plot(float(issue68B36ConflictFree), "B36 CONFLICT FREE gate", display=display.data_window)
plot(float(issue68B36Formal), "B36 FORMAL direction", display=display.data_window)
plot(float(issue68B36Core), "B36 CORE direction", display=display.data_window)
plot(topVal, "B36 top value", display=display.data_window)
plot(topGap, "B36 top gap", display=display.data_window)
plot(evidenceStrength, "B36 evidence strength", display=display.data_window)
plot(candidateConflict ? 1.0 : 0.0, "B36 candidate conflict", display=display.data_window)
plot(float(candidateBars), "B36 candidate bars", display=display.data_window)
'''.strip()


def generate(source: Path) -> str:
    d1_text = phase_b.d1.generate(source)
    if d1_text.count(phase_b.D1_EXPORT_MARKER) != 1:
        raise RuntimeError("expected exactly one D1 parity export marker")
    core = d1_text.split(phase_b.D1_EXPORT_MARKER, 1)[0].rstrip()
    core = replace_once(core, phase_b.D1_INDICATOR_DECL, AUDIT_DECL)
    out = core + "\n\n" + B36_BODY + "\n"
    required = (
        "Issue #66 C-2 runtime-validated price-only lineage",
        'volumeMode = "Off"',
        'mtfMode = "Off"',
        'divMode = "Off"',
        "DOM GAP gate band",
        "EVIDENCE gate band",
        "CONFLICT FREE gate band",
        "FORMAL direction band",
        "CORE direction memory band",
        "topVal >= dominantMin and topGap >= topGapMin",
        "evidenceStrength >= evidenceMin",
        "not candidateConflict",
    )
    for token in required:
        if token not in out:
            raise RuntimeError(f"missing B3.6 audit token: {token}")
    for token in ("strategy.", "issue68B34A", "issue68B34B", "issue68B34C", "D1B|"):
        if token in out:
            raise RuntimeError(f"forbidden token leaked into B3.6 audit: {token}")
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
