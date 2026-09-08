#!/usr/bin/env python3
"""Generate Issue #68 DownEx current-context Fresh-S1 preservation audit Pine."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue66_phase_d1_parity_pine as d1
import generate_issue68_phase_b_lifecycle_pine as phase_b
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 Fresh-S1 Preserve", shorttitle="ChaseRisk #68 S1Keep", overlay=false, precision=3)'

BODY = r'''

// ============================================================================
// Issue #68 DownEx Current-Context Fresh-S1 Preserve Audit.
// No hand-picked event window. No lookahead. No tuning.
// Fresh-S1 = PROD S1 TOP + current bearBg>=35 + DownEx>=35 + 20D path<=0.
// The 35 bounds are existing production gate lower bounds; 20D is sign-only.
// PRODUCTION C-2 FROZEN. NO PNL.
// ============================================================================

groupIssue68S1P = "Issue #68｜Fresh-S1 Preserve"
showIssue68S1PTable = input.bool(true, "顯示 Fresh-S1 Preserve 表", group=groupIssue68S1P)

f_issue68S1PTop(float accX) =>
    float best = accX
    int id = 1
    if markupEff > best
        best := markupEff
        id := 2
    if reaccEff > best
        best := reaccEff
        id := 3
    if distEff > best
        best := distEff
        id := 4
    if markdownEff > best
        best := markdownEff
        id := 5
    if redistEff > best
        best := redistEff
        id := 6
    id

f_issue68S1PPct(int n, int d) => d > 0 ? 100.0 * n / d : na
f_issue68S1PAvg(float s, int n) => n > 0 ? s / n : na
f_issue68S1PFmt(float x) => na(x) ? "NA" : str.tostring(x, "#.##")
f_issue68S1PFmtPct(int n, int d) => d > 0 ? str.tostring(100.0 * n / d, "#.##") + "%" : "NA"

bool issue68S1PReady = bar_index >= rankLen - 1 and not na(close[20])
float issue68S1PCurrentBearGate = f_gate(bearBg, 35.0, 75.0)
float issue68S1PBoundDownGate = math.min(downsideExhaustionGate, issue68S1PCurrentBearGate)
float issue68S1PCtxAccGate = rangeGate * bearBackgroundForAccGate * issue68S1PBoundDownGate * supportHoldingGate * nonMarkdownContinuationGate
float issue68S1PAccMult = accVolMult * accMtfMult * accDivMult
float issue68S1PCtxAccEff = accRaw * issue68S1PCtxAccGate * issue68S1PAccMult

bool issue68S1PValid = issue68S1PReady and not na(issue68S1PCtxAccEff) and not na(topId) and not na(bearBg) and not na(downsideExhaustion)
int issue68S1PCtxTop = issue68S1PValid ? f_issue68S1PTop(issue68S1PCtxAccEff) : na

bool issue68S1PProdS1 = issue68S1PValid and topId == 1
bool issue68S1PPathNotRising = issue68S1PValid and close - close[20] <= 0.0
bool issue68S1PFresh = issue68S1PProdS1 and bearBg >= 35.0 and downsideExhaustion >= 35.0 and issue68S1PPathNotRising
bool issue68S1POther = issue68S1PProdS1 and not issue68S1PFresh
bool issue68S1PRetained = issue68S1PFresh and issue68S1PCtxTop == 1
bool issue68S1PLost = issue68S1PFresh and issue68S1PCtxTop != 1
bool issue68S1PLostBull = issue68S1PLost and (issue68S1PCtxTop == 2 or issue68S1PCtxTop == 3)
bool issue68S1PLostNeutral = issue68S1PLost and issue68S1PCtxTop == 4
bool issue68S1PLostBear = issue68S1PLost and (issue68S1PCtxTop == 5 or issue68S1PCtxTop == 6)
bool issue68S1POtherRemoved = issue68S1POther and issue68S1PCtxTop != 1
bool issue68S1PCapBindFresh = issue68S1PFresh and downsideExhaustionGate > issue68S1PCurrentBearGate

var int issue68S1PValidN = 0
var int issue68S1PProdS1N = 0
var int issue68S1PFreshN = 0
var int issue68S1POtherN = 0
var int issue68S1PRetainedN = 0
var int issue68S1PLostN = 0
var int issue68S1PLostBullN = 0
var int issue68S1PLostNeutralN = 0
var int issue68S1PLostBearN = 0
var int issue68S1POtherRemovedN = 0
var int issue68S1PCapBindFreshN = 0

var float issue68S1PSumProdGateFresh = 0.0
var float issue68S1PSumCtxGateFresh = 0.0
var float issue68S1PSumCurrentBearFresh = 0.0
var float issue68S1PSumDownGateFresh = 0.0
var float issue68S1PSumBearBgFresh = 0.0
var float issue68S1PSumDownScoreFresh = 0.0
var float issue68S1PSum20DMoveFresh = 0.0

var int issue68S1PFreshRun = 0
var int issue68S1PFreshMaxRun = 0
var int issue68S1PRetainRun = 0
var int issue68S1PRetainMaxRun = 0

if issue68S1PValid
    issue68S1PValidN += 1
    issue68S1PProdS1N += issue68S1PProdS1 ? 1 : 0
    issue68S1PFreshN += issue68S1PFresh ? 1 : 0
    issue68S1POtherN += issue68S1POther ? 1 : 0
    issue68S1PRetainedN += issue68S1PRetained ? 1 : 0
    issue68S1PLostN += issue68S1PLost ? 1 : 0
    issue68S1PLostBullN += issue68S1PLostBull ? 1 : 0
    issue68S1PLostNeutralN += issue68S1PLostNeutral ? 1 : 0
    issue68S1PLostBearN += issue68S1PLostBear ? 1 : 0
    issue68S1POtherRemovedN += issue68S1POtherRemoved ? 1 : 0
    issue68S1PCapBindFreshN += issue68S1PCapBindFresh ? 1 : 0

    if issue68S1PFresh
        issue68S1PSumProdGateFresh += accGate
        issue68S1PSumCtxGateFresh += issue68S1PCtxAccGate
        issue68S1PSumCurrentBearFresh += issue68S1PCurrentBearGate
        issue68S1PSumDownGateFresh += downsideExhaustionGate
        issue68S1PSumBearBgFresh += bearBg
        issue68S1PSumDownScoreFresh += downsideExhaustion
        issue68S1PSum20DMoveFresh += close - close[20]

    if issue68S1PFresh
        issue68S1PFreshRun += 1
        issue68S1PFreshMaxRun := math.max(issue68S1PFreshMaxRun, issue68S1PFreshRun)
    else
        issue68S1PFreshRun := 0

    if issue68S1PRetained
        issue68S1PRetainRun += 1
        issue68S1PRetainMaxRun := math.max(issue68S1PRetainMaxRun, issue68S1PRetainRun)
    else
        issue68S1PRetainRun := 0

float issue68S1PFreshRetention = f_issue68S1PPct(issue68S1PRetainedN, issue68S1PFreshN)
float issue68S1POtherRemoval = f_issue68S1PPct(issue68S1POtherRemovedN, issue68S1POtherN)

plot(issue68S1PFresh ? 3.0 : na, "Fresh-S1 semantic anchor", color=colGreen, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68S1PFresh ? 2.0 : na, "Fresh-S1 retained/lost", color=issue68S1PRetained ? colGreen : colRed, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68S1POther ? 1.0 : na, "Other PROD-S1 removed/kept", color=issue68S1POtherRemoved ? colGreen : colNeutral, linewidth=3, style=plot.style_linebr, display=display.pane)

var table tS1P = table.new(position.middle_right, 5, 17, border_width=1)
if barstate.islast
    if showIssue68S1PTable
        table.cell(tS1P, 0, 0, "FRESH-S1 PRESERVE", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 1, 0, syminfo.ticker, bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 2, 0, "PROD", bgcolor=colRed, text_color=color.white)
        table.cell(tS1P, 3, 0, "PROD+CTX", bgcolor=colGreen, text_color=color.white)
        table.cell(tS1P, 4, 0, "NO LOOKAHEAD", bgcolor=colGreen, text_color=color.white)

        table.cell(tS1P, 0, 1, "POPULATION", bgcolor=colGreen, text_color=color.white)
        table.cell(tS1P, 1, 1, "COUNT", bgcolor=colGreen, text_color=color.white)
        table.cell(tS1P, 2, 1, "SHARE", bgcolor=colGreen, text_color=color.white)
        table.cell(tS1P, 3, 1, "CTX RESULT", bgcolor=colGreen, text_color=color.white)
        table.cell(tS1P, 4, 1, "READ", bgcolor=colGreen, text_color=color.white)

        table.cell(tS1P, 0, 2, "Valid bars", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 1, 2, str.tostring(issue68S1PValidN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 2, 2, "after warmup", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 3, 2, "same", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 4, 2, "full history", bgcolor=colNeutral, text_color=color.white)

        table.cell(tS1P, 0, 3, "PROD S1 TOP", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 1, 3, str.tostring(issue68S1PProdS1N), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 2, 3, f_issue68S1PFmtPct(issue68S1PProdS1N, issue68S1PValidN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 3, 3, "baseline", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 4, 3, "S1 only", bgcolor=colNeutral, text_color=color.white)

        table.cell(tS1P, 0, 4, "Fresh-S1", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 1, 4, str.tostring(issue68S1PFreshN), bgcolor=colGreen, text_color=color.white)
        table.cell(tS1P, 2, 4, f_issue68S1PFmtPct(issue68S1PFreshN, issue68S1PProdS1N), bgcolor=colGreen, text_color=color.white)
        table.cell(tS1P, 3, 4, "current downside", bgcolor=colGreen, text_color=color.white)
        table.cell(tS1P, 4, 4, "anchor", bgcolor=colGreen, text_color=color.white)

        table.cell(tS1P, 0, 5, "Other PROD-S1", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 1, 5, str.tostring(issue68S1POtherN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 2, 5, f_issue68S1PFmtPct(issue68S1POtherN, issue68S1PProdS1N), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 3, 5, "contrast", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 4, 5, "possibly stale", bgcolor=colNeutral, text_color=color.white)

        table.cell(tS1P, 0, 6, "PRESERVATION", bgcolor=colGreen, text_color=color.white)
        table.cell(tS1P, 1, 6, "COUNT", bgcolor=colGreen, text_color=color.white)
        table.cell(tS1P, 2, 6, "SHARE", bgcolor=colGreen, text_color=color.white)
        table.cell(tS1P, 3, 6, "DEST", bgcolor=colGreen, text_color=color.white)
        table.cell(tS1P, 4, 6, "READ", bgcolor=colGreen, text_color=color.white)

        table.cell(tS1P, 0, 7, "Fresh retained S1", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 1, 7, str.tostring(issue68S1PRetainedN), bgcolor=colGreen, text_color=color.white)
        table.cell(tS1P, 2, 7, f_issue68S1PFmtPct(issue68S1PRetainedN, issue68S1PFreshN), bgcolor=colGreen, text_color=color.white)
        table.cell(tS1P, 3, 7, "S1", bgcolor=colGreen, text_color=color.white)
        table.cell(tS1P, 4, 7, "must inspect", bgcolor=colNeutral, text_color=color.white)

        table.cell(tS1P, 0, 8, "Fresh lost", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 1, 8, str.tostring(issue68S1PLostN), bgcolor=issue68S1PLostN == 0 ? colGreen : colRed, text_color=color.white)
        table.cell(tS1P, 2, 8, f_issue68S1PFmtPct(issue68S1PLostN, issue68S1PFreshN), bgcolor=issue68S1PLostN == 0 ? colGreen : colRed, text_color=color.white)
        table.cell(tS1P, 3, 8, "B/N/R " + str.tostring(issue68S1PLostBullN) + "/" + str.tostring(issue68S1PLostNeutralN) + "/" + str.tostring(issue68S1PLostBearN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 4, 8, "Bull/Neutral/Bear", bgcolor=colNeutral, text_color=color.white)

        table.cell(tS1P, 0, 9, "Other S1 removed", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 1, 9, str.tostring(issue68S1POtherRemovedN), bgcolor=colGreen, text_color=color.white)
        table.cell(tS1P, 2, 9, f_issue68S1PFmtPct(issue68S1POtherRemovedN, issue68S1POtherN), bgcolor=colGreen, text_color=color.white)
        table.cell(tS1P, 3, 9, "non-S1", bgcolor=colGreen, text_color=color.white)
        table.cell(tS1P, 4, 9, "selectivity", bgcolor=colNeutral, text_color=color.white)

        table.cell(tS1P, 0, 10, "FRESH INPUTS", bgcolor=colGreen, text_color=color.white)
        table.cell(tS1P, 1, 10, "PROD", bgcolor=colGreen, text_color=color.white)
        table.cell(tS1P, 2, 10, "CTX", bgcolor=colGreen, text_color=color.white)
        table.cell(tS1P, 3, 10, "BIND", bgcolor=colGreen, text_color=color.white)
        table.cell(tS1P, 4, 10, "SEMANTIC", bgcolor=colGreen, text_color=color.white)

        table.cell(tS1P, 0, 11, "S1 gate avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 1, 11, f_issue68S1PFmt(f_issue68S1PAvg(issue68S1PSumProdGateFresh, issue68S1PFreshN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 2, 11, f_issue68S1PFmt(f_issue68S1PAvg(issue68S1PSumCtxGateFresh, issue68S1PFreshN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 3, 11, f_issue68S1PFmtPct(issue68S1PCapBindFreshN, issue68S1PFreshN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 4, 11, "cap share", bgcolor=colNeutral, text_color=color.white)

        table.cell(tS1P, 0, 12, "BearGate / DownExGate", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 1, 12, f_issue68S1PFmt(f_issue68S1PAvg(issue68S1PSumCurrentBearFresh, issue68S1PFreshN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 2, 12, f_issue68S1PFmt(f_issue68S1PAvg(issue68S1PSumDownGateFresh, issue68S1PFreshN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 3, 12, "current / exhaust", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 4, 12, "eligibility", bgcolor=colNeutral, text_color=color.white)

        table.cell(tS1P, 0, 13, "BearBg / DownEx score", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 1, 13, f_issue68S1PFmt(f_issue68S1PAvg(issue68S1PSumBearBgFresh, issue68S1PFreshN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 2, 13, f_issue68S1PFmt(f_issue68S1PAvg(issue68S1PSumDownScoreFresh, issue68S1PFreshN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 3, 13, "raw scores", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 4, 13, "existing >=35", bgcolor=colNeutral, text_color=color.white)

        table.cell(tS1P, 0, 14, "20D move avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 1, 14, f_issue68S1PFmt(f_issue68S1PAvg(issue68S1PSum20DMoveFresh, issue68S1PFreshN)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 2, 14, "yield units", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 3, 14, "<= 0", bgcolor=colGreen, text_color=color.white)
        table.cell(tS1P, 4, 14, "no rise", bgcolor=colNeutral, text_color=color.white)

        table.cell(tS1P, 0, 15, "Fresh run / retained", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 1, 15, str.tostring(issue68S1PFreshMaxRun), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 2, 15, str.tostring(issue68S1PRetainMaxRun), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 3, 15, "max bars", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 4, 15, "continuity", bgcolor=colNeutral, text_color=color.white)

        table.cell(tS1P, 0, 16, "READ", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS1P, 1, 16, "Fresh keep?", bgcolor=colGreen, text_color=color.white)
        table.cell(tS1P, 2, 16, "Other remove?", bgcolor=colGreen, text_color=color.white)
        table.cell(tS1P, 3, 16, "NO TUNING", bgcolor=colRed, text_color=color.white)
        table.cell(tS1P, 4, 16, "FROZEN C-2", bgcolor=colNeutral, text_color=color.white)
    else
        table.clear(tS1P, 0, 0, 4, 16)
'''


def generate(source: Path) -> str:
    text = d1.generate(source)
    if text.count(phase_b.D1_EXPORT_MARKER) != 1:
        raise RuntimeError("expected exactly one D1 parity-export marker")
    core = text.split(phase_b.D1_EXPORT_MARKER, 1)[0].rstrip()
    core = replace_once(core, phase_b.D1_INDICATOR_DECL, AUDIT_DECL)
    out = core + BODY + "\n"
    for token in (
        "Fresh-S1 semantic anchor",
        "Fresh retained S1",
        "Other S1 removed",
        "BearGate / DownExGate",
        "NO LOOKAHEAD",
    ):
        if token not in out:
            raise RuntimeError(f"missing Fresh-S1 audit token: {token}")
    if "strategy.entry" in out or "strategy.close" in out:
        raise RuntimeError("Fresh-S1 audit leaked strategy order logic")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=HERE / SOURCE_RELATIVE)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    text = generate(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
