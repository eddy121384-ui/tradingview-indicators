#!/usr/bin/env python3
"""Generate Issue #68 TOP Bull -> Strong gate attribution Pine.

Discovery-only diagnostic. Reuses the frozen C-2 calculation core and changes no
classifier, Core, Exposure, lifecycle, or strategy semantics.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_phase_b_lifecycle_pine as phase_b
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 TOP Bull Strong Gate", shorttitle="ChaseRisk #68 TBSTR", overlay=false, precision=2)'

BODY = r'''

// ============================================================================
// Issue #68 Cross-Market TOP Bull -> Strong Gate Attribution.
// Shared window: 2022-01-03 -> 2023-12-29, expected Bull yield regime.
// DISCOVERY ONLY. NO PNL. NO TUNING. FROZEN C-2.
// ============================================================================

groupIssue68TopStrong = "Issue #68｜TOP Bull -> Strong Gate"
showIssue68TopStrongTable = input.bool(true, "顯示 TOP Bull -> Strong 統計表", group=groupIssue68TopStrong)

issue68TopStrongReady = bar_index >= rankLen - 1
int issue68TopStrongStart = timestamp(2022, 1, 3, 0, 0)
int issue68TopStrongEnd = timestamp(2023, 12, 29, 23, 59)
bool issue68TopStrongInWindow = issue68TopStrongReady and time >= issue68TopStrongStart and time <= issue68TopStrongEnd
bool issue68TopBull = issue68TopStrongInWindow and (topId == 2 or topId == 3)
bool issue68StrongBull = issue68TopBull and strongCandidate

bool issue68GateSharp = hasSharp
bool issue68GateDominant = topVal >= dominantMin
bool issue68GateGap = topGap >= topGapMin
bool issue68GateEvidence = hasEvidence
bool issue68GateConflictClear = not candidateConflict

// Mutually-exclusive first blocker, preserving production conjunction order.
int issue68FirstBlocker = not issue68GateSharp ? 1 : not issue68GateDominant ? 2 : not issue68GateGap ? 3 : not issue68GateEvidence ? 4 : not issue68GateConflictClear ? 5 : 0

bool issue68FormalBullNow = formalId == 2 or formalId == 3
bool issue68FormalBullPrev = formalId[1] == 2 or formalId[1] == 3
bool issue68FormalBullAcquire = issue68TopStrongInWindow and issue68FormalBullNow and not issue68FormalBullPrev

f_issue68Avg(float s, int n) => n > 0 ? s / n : na
f_issue68Pct(int n, int d) => d > 0 ? 100.0 * n / d : na

var int issue68WindowBars = 0
var int issue68WindowFirstBar = na
var int issue68TopBullBars = 0
var int issue68TopS2Bars = 0
var int issue68TopS3Bars = 0
var int issue68StrongPassBars = 0

var float issue68SumTopVal = 0.0
var float issue68SumTopGap = 0.0
var float issue68SumEvidence = 0.0
var float issue68SumStageSupport = 0.0
var float issue68SumTopValMargin = 0.0
var float issue68SumTopGapMargin = 0.0
var float issue68SumEvidenceMargin = 0.0

var int issue68PassSharp = 0
var int issue68PassDominant = 0
var int issue68PassGap = 0
var int issue68PassEvidence = 0
var int issue68PassConflictClear = 0

var int issue68FailSharp = 0
var int issue68FailDominant = 0
var int issue68FailGap = 0
var int issue68FailEvidence = 0
var int issue68FailConflict = 0

var int issue68FastSwitchBars = 0
var float issue68SumActiveConfirmBars = 0.0
var int issue68StrongBullRun = 0
var int issue68StrongBullMaxRun = 0
var int issue68FormalBullAcqCount = 0
var int issue68FirstFormalBullAcq = na

if issue68TopStrongInWindow
    if na(issue68WindowFirstBar)
        issue68WindowFirstBar := bar_index
    issue68WindowBars += 1

    if issue68FormalBullAcquire
        issue68FormalBullAcqCount += 1
        if na(issue68FirstFormalBullAcq)
            issue68FirstFormalBullAcq := bar_index - issue68WindowFirstBar

    if issue68TopBull
        issue68TopBullBars += 1
        issue68TopS2Bars += topId == 2 ? 1 : 0
        issue68TopS3Bars += topId == 3 ? 1 : 0
        issue68StrongPassBars += strongCandidate ? 1 : 0

        issue68SumTopVal += topVal
        issue68SumTopGap += topGap
        issue68SumEvidence += evidenceStrength
        issue68SumStageSupport += stageSupportStrength
        issue68SumTopValMargin += topVal - dominantMin
        issue68SumTopGapMargin += topGap - topGapMin
        issue68SumEvidenceMargin += evidenceStrength - evidenceMin

        issue68PassSharp += issue68GateSharp ? 1 : 0
        issue68PassDominant += issue68GateDominant ? 1 : 0
        issue68PassGap += issue68GateGap ? 1 : 0
        issue68PassEvidence += issue68GateEvidence ? 1 : 0
        issue68PassConflictClear += issue68GateConflictClear ? 1 : 0

        issue68FailSharp += issue68FirstBlocker == 1 ? 1 : 0
        issue68FailDominant += issue68FirstBlocker == 2 ? 1 : 0
        issue68FailGap += issue68FirstBlocker == 3 ? 1 : 0
        issue68FailEvidence += issue68FirstBlocker == 4 ? 1 : 0
        issue68FailConflict += issue68FirstBlocker == 5 ? 1 : 0

    if issue68StrongBull
        issue68StrongBullRun += 1
        issue68StrongBullMaxRun := math.max(issue68StrongBullMaxRun, issue68StrongBullRun)
        issue68FastSwitchBars += fastSwitchActive ? 1 : 0
        issue68SumActiveConfirmBars += activeConfirmBars
    else
        issue68StrongBullRun := 0

float issue68TopS2Pct = f_issue68Pct(issue68TopS2Bars, issue68TopBullBars)
float issue68TopS3Pct = f_issue68Pct(issue68TopS3Bars, issue68TopBullBars)
float issue68StrongPassPct = f_issue68Pct(issue68StrongPassBars, issue68TopBullBars)
float issue68AvgTopVal = f_issue68Avg(issue68SumTopVal, issue68TopBullBars)
float issue68AvgTopGap = f_issue68Avg(issue68SumTopGap, issue68TopBullBars)
float issue68AvgEvidence = f_issue68Avg(issue68SumEvidence, issue68TopBullBars)
float issue68AvgStageSupport = f_issue68Avg(issue68SumStageSupport, issue68TopBullBars)
float issue68AvgTopValMargin = f_issue68Avg(issue68SumTopValMargin, issue68TopBullBars)
float issue68AvgTopGapMargin = f_issue68Avg(issue68SumTopGapMargin, issue68TopBullBars)
float issue68AvgEvidenceMargin = f_issue68Avg(issue68SumEvidenceMargin, issue68TopBullBars)
float issue68FastSwitchPct = f_issue68Pct(issue68FastSwitchBars, issue68StrongPassBars)
float issue68AvgConfirmBars = f_issue68Avg(issue68SumActiveConfirmBars, issue68StrongPassBars)

// Minimal plot-safe lanes.
plot(issue68TopStrongInWindow ? 3.0 : na, "EXPECTED Bull", color=colGreen, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68TopBull ? 2.0 : na, "TOP Bull gate result", color=strongCandidate ? colGreen : colRed, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68FormalBullAcquire ? 1.0 : na, "Formal Bull acquire", color=color.aqua, linewidth=4, style=plot.style_circles, display=display.pane)

var table t = table.new(position.bottom_right, 6, 16, border_width=1)
if barstate.islast
    if showIssue68TopStrongTable
        table.cell(t, 0, 0, "TOP BULL -> STRONG", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 0, syminfo.ticker, bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 0, "2022-2023 BULL", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 0, "DISCOVERY", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 4, 0, str.tostring(issue68WindowBars) + " bars", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 5, 0, "FROZEN C-2", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 1, "TOP Bull bars", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 1, str.tostring(issue68TopBullBars), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 1, "S2 " + str.tostring(issue68TopS2Pct, "#.1") + "%", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 1, "S3 " + str.tostring(issue68TopS3Pct, "#.1") + "%", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 4, 1, "STRONG PASS", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 5, 1, str.tostring(issue68StrongPassPct, "#.1") + "%", bgcolor=issue68StrongPassPct >= 50.0 ? colGreen : colRed, text_color=color.white)

        table.cell(t, 0, 2, "GATE / METRIC", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 2, "AVG", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 2, "REF", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 2, "AVG MARGIN", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 4, 2, "PASS %", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 5, 2, "FIRST FAIL", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 3, "hasSharp", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 3, "—", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 3, "true", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 3, "—", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 4, 3, str.tostring(f_issue68Pct(issue68PassSharp, issue68TopBullBars), "#.1") + "%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 5, 3, str.tostring(issue68FailSharp), bgcolor=issue68FailSharp > 0 ? colRed : colNeutral, text_color=color.white)

        table.cell(t, 0, 4, "Top value", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 4, str.tostring(issue68AvgTopVal, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 4, str.tostring(dominantMin, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 4, str.tostring(issue68AvgTopValMargin, "#.1"), bgcolor=issue68AvgTopValMargin >= 0 ? colGreen : colRed, text_color=color.white)
        table.cell(t, 4, 4, str.tostring(f_issue68Pct(issue68PassDominant, issue68TopBullBars), "#.1") + "%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 5, 4, str.tostring(issue68FailDominant), bgcolor=issue68FailDominant > 0 ? colRed : colNeutral, text_color=color.white)

        table.cell(t, 0, 5, "Top gap", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 5, str.tostring(issue68AvgTopGap, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 5, str.tostring(topGapMin, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 5, str.tostring(issue68AvgTopGapMargin, "#.1"), bgcolor=issue68AvgTopGapMargin >= 0 ? colGreen : colRed, text_color=color.white)
        table.cell(t, 4, 5, str.tostring(f_issue68Pct(issue68PassGap, issue68TopBullBars), "#.1") + "%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 5, 5, str.tostring(issue68FailGap), bgcolor=issue68FailGap > 0 ? colRed : colNeutral, text_color=color.white)

        table.cell(t, 0, 6, "Evidence", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 6, str.tostring(issue68AvgEvidence, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 6, str.tostring(evidenceMin, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 6, str.tostring(issue68AvgEvidenceMargin, "#.1"), bgcolor=issue68AvgEvidenceMargin >= 0 ? colGreen : colRed, text_color=color.white)
        table.cell(t, 4, 6, str.tostring(f_issue68Pct(issue68PassEvidence, issue68TopBullBars), "#.1") + "%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 5, 6, str.tostring(issue68FailEvidence), bgcolor=issue68FailEvidence > 0 ? colRed : colNeutral, text_color=color.white)

        table.cell(t, 0, 7, "Stage support", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 7, str.tostring(issue68AvgStageSupport, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 7, "evidence input", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 7, "—", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 4, 7, "—", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 5, 7, "—", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 8, "Conflict clear", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 8, "—", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 8, "true", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 8, "—", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 4, 8, str.tostring(f_issue68Pct(issue68PassConflictClear, issue68TopBullBars), "#.1") + "%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 5, 8, str.tostring(issue68FailConflict), bgcolor=issue68FailConflict > 0 ? colRed : colNeutral, text_color=color.white)

        table.cell(t, 0, 9, "FIRST FAIL TOTALS", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 9, "Sharp " + str.tostring(issue68FailSharp), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 9, "Dom " + str.tostring(issue68FailDominant), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 9, "Gap " + str.tostring(issue68FailGap), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 4, 9, "Evid " + str.tostring(issue68FailEvidence), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 5, 9, "Conflict " + str.tostring(issue68FailConflict), bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 10, "CONFIRM CONTEXT", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 10, "VALUE", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 10, "NOTE", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 10, "", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 4, 10, "", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 5, 10, "", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 11, "Strong Bull bars", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 11, str.tostring(issue68StrongPassBars), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 11, str.tostring(issue68StrongPassPct, "#.1") + "% of TOP Bull", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 12, "Fast switch", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 12, str.tostring(issue68FastSwitchPct, "#.1") + "%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 12, "of Strong Bull", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 13, "Avg confirm bars", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 13, str.tostring(issue68AvgConfirmBars, "#.2"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 13, "activeConfirmBars", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 14, "Max Strong run", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 14, str.tostring(issue68StrongBullMaxRun), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 14, "consecutive bars", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 15, "Formal Bull acquire", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 15, str.tostring(issue68FormalBullAcqCount), bgcolor=issue68FormalBullAcqCount > 0 ? colGreen : colRed, text_color=color.white)
        table.cell(t, 2, 15, na(issue68FirstFormalBullAcq) ? "FIRST NEVER" : "FIRST " + str.tostring(issue68FirstFormalBullAcq), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 15, "NO TUNING", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 4, 15, "NO PNL", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 5, 15, "DISCOVERY", bgcolor=colNeutral, text_color=color.white)
    else
        table.clear(t, 0, 0, 5, 15)
'''.strip()


def generate(source: Path) -> str:
    d1_text = phase_b.d1.generate(source)
    if d1_text.count(phase_b.D1_EXPORT_MARKER) != 1:
        raise RuntimeError("expected exactly one D1 parity export marker")
    core = d1_text.split(phase_b.D1_EXPORT_MARKER, 1)[0].rstrip()
    core = replace_once(core, phase_b.D1_INDICATOR_DECL, AUDIT_DECL)
    out = core + "\n\n" + BODY + "\n"

    required = (
        "TOP Bull -> Strong Gate Attribution",
        "strongCandidate",
        "topVal",
        "topGap",
        "evidenceStrength",
        "candidateConflict",
        "activeConfirmBars",
        "fastSwitchActive",
        "Formal Bull acquire",
        "FIRST FAIL TOTALS",
    )
    for token in required:
        if token not in out:
            raise RuntimeError(f"missing TOP-Bull strong-gate token: {token}")
    if "strategy." in out:
        raise RuntimeError("strategy token leaked into TOP-Bull strong-gate diagnostic")
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
