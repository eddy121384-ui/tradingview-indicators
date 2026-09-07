#!/usr/bin/env python3
"""Generate Issue #68 DownEx current-context cross-market control Pine."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_support_invariant_slope_shadow_pine as base
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 DownEx Context Controls", shorttitle="ChaseRisk #68 CtxCtrl", overlay=false, precision=3)'

BODY = r'''

// ============================================================================
// Issue #68 DownEx Current-Context Cross-Market Controls.
// Frozen controls: JP10Y 2022-01-04..2024-12-30,
// US10Y 2020-08-04..2023-10-19, GB10Y 2022-01-03..2023-12-29.
// Expected regime: Bull yield. NO PNL. NO TUNING. PRODUCTION C-2 FROZEN.
// ============================================================================

groupIssue68Ctrl = "Issue #68｜DownEx Context Controls"
showIssue68CtrlTable = input.bool(true, "顯示 Context Control 表", group=groupIssue68Ctrl)

string issue68CtrlTicker = syminfo.tickerid
bool issue68CtrlJP = str.contains(issue68CtrlTicker, "JP10Y")
bool issue68CtrlUS = str.contains(issue68CtrlTicker, "US10Y")
bool issue68CtrlGB = str.contains(issue68CtrlTicker, "GB10Y")
bool issue68CtrlSupported = issue68CtrlJP or issue68CtrlUS or issue68CtrlGB

int issue68CtrlStart = issue68CtrlJP ? timestamp(2022, 1, 4, 0, 0) : issue68CtrlUS ? timestamp(2020, 8, 4, 0, 0) : issue68CtrlGB ? timestamp(2022, 1, 3, 0, 0) : na
int issue68CtrlEnd = issue68CtrlJP ? timestamp(2024, 12, 30, 23, 59) : issue68CtrlUS ? timestamp(2023, 10, 19, 23, 59) : issue68CtrlGB ? timestamp(2023, 12, 29, 23, 59) : na
string issue68CtrlName = issue68CtrlJP ? "JP10Y" : issue68CtrlUS ? "US10Y" : issue68CtrlGB ? "GB10Y" : "UNSUPPORTED"
bool issue68CtrlInWindow = issue68CtrlSupported and time >= issue68CtrlStart and time <= issue68CtrlEnd

f_issue68CtrlTop(float accX) =>
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

f_issue68CtrlBull(int id) => id == 2 or id == 3
f_issue68CtrlBear(int id) => id == 5 or id == 6
f_issue68CtrlNeutral(int id) => id == 1 or id == 4
f_issue68CtrlPct(int n, int d) => d > 0 ? 100.0 * n / d : na
f_issue68CtrlAvg(float s, int n) => n > 0 ? s / n : na
f_issue68CtrlFmt(float x) => na(x) ? "NA" : str.tostring(x, "#.##")
f_issue68CtrlFmtPct(int n, int d) => na(f_issue68CtrlPct(n, d)) ? "NA" : str.tostring(f_issue68CtrlPct(n, d), "#.##") + "%"

float issue68CtrlCurrentBearGate = f_gate(bearBg, 35.0, 75.0)
float issue68CtrlBoundDownGate = math.min(downsideExhaustionGate, issue68CtrlCurrentBearGate)
float issue68CtrlAccGate = rangeGate * bearBackgroundForAccGate * issue68CtrlBoundDownGate * supportHoldingGate * nonMarkdownContinuationGate
float issue68CtrlAccMult = accVolMult * accMtfMult * accDivMult
float issue68CtrlAccEff = accRaw * issue68CtrlAccGate * issue68CtrlAccMult

bool issue68CtrlValid = issue68CtrlInWindow and bar_index >= rankLen - 1 and not na(issue68CtrlAccEff) and not na(accEff) and not na(topId)
int issue68CtrlTopId = issue68CtrlValid ? f_issue68CtrlTop(issue68CtrlAccEff) : na

bool issue68CtrlProdBullNow = issue68CtrlValid and f_issue68CtrlBull(topId)
bool issue68CtrlProdBearNow = issue68CtrlValid and f_issue68CtrlBear(topId)
bool issue68CtrlProdNeutralNow = issue68CtrlValid and f_issue68CtrlNeutral(topId)
bool issue68CtrlCtxBullNow = issue68CtrlValid and f_issue68CtrlBull(issue68CtrlTopId)
bool issue68CtrlCtxBearNow = issue68CtrlValid and f_issue68CtrlBear(issue68CtrlTopId)
bool issue68CtrlCtxNeutralNow = issue68CtrlValid and f_issue68CtrlNeutral(issue68CtrlTopId)

var int issue68CtrlN = 0
var int issue68CtrlProdBull = 0
var int issue68CtrlProdBear = 0
var int issue68CtrlProdNeutral = 0
var int issue68CtrlCtxBull = 0
var int issue68CtrlCtxBear = 0
var int issue68CtrlCtxNeutral = 0
var int issue68CtrlProdS1 = 0
var int issue68CtrlCtxS1 = 0
var int issue68CtrlTopChanged = 0
var int issue68CtrlBullRetained = 0
var int issue68CtrlBullLost = 0
var int issue68CtrlBullGained = 0
var int issue68CtrlCtxBearRun = 0
var int issue68CtrlCtxBearRunMax = 0
var float issue68CtrlSumProdGate = 0.0
var float issue68CtrlSumCtxGate = 0.0
var int issue68CtrlCapN = 0

if issue68CtrlValid
    issue68CtrlN += 1
    issue68CtrlProdBull += issue68CtrlProdBullNow ? 1 : 0
    issue68CtrlProdBear += issue68CtrlProdBearNow ? 1 : 0
    issue68CtrlProdNeutral += issue68CtrlProdNeutralNow ? 1 : 0
    issue68CtrlCtxBull += issue68CtrlCtxBullNow ? 1 : 0
    issue68CtrlCtxBear += issue68CtrlCtxBearNow ? 1 : 0
    issue68CtrlCtxNeutral += issue68CtrlCtxNeutralNow ? 1 : 0
    issue68CtrlProdS1 += topId == 1 ? 1 : 0
    issue68CtrlCtxS1 += issue68CtrlTopId == 1 ? 1 : 0
    issue68CtrlTopChanged += issue68CtrlTopId != topId ? 1 : 0
    issue68CtrlBullRetained += issue68CtrlProdBullNow and issue68CtrlCtxBullNow ? 1 : 0
    issue68CtrlBullLost += issue68CtrlProdBullNow and not issue68CtrlCtxBullNow ? 1 : 0
    issue68CtrlBullGained += not issue68CtrlProdBullNow and issue68CtrlCtxBullNow ? 1 : 0
    issue68CtrlSumProdGate += accGate
    issue68CtrlSumCtxGate += issue68CtrlAccGate
    issue68CtrlCapN += downsideExhaustionGate > issue68CtrlCurrentBearGate ? 1 : 0

    if issue68CtrlCtxBearNow
        issue68CtrlCtxBearRun += 1
        issue68CtrlCtxBearRunMax := math.max(issue68CtrlCtxBearRunMax, issue68CtrlCtxBearRun)
    else
        issue68CtrlCtxBearRun := 0

float issue68CtrlProdBullPct = f_issue68CtrlPct(issue68CtrlProdBull, issue68CtrlN)
float issue68CtrlCtxBullPct = f_issue68CtrlPct(issue68CtrlCtxBull, issue68CtrlN)
float issue68CtrlBullDelta = issue68CtrlCtxBullPct - issue68CtrlProdBullPct
float issue68CtrlCtxBearPct = f_issue68CtrlPct(issue68CtrlCtxBear, issue68CtrlN)
bool issue68CtrlHardFail = issue68CtrlN > 0 and (issue68CtrlCtxBearPct > 50.0 or issue68CtrlCtxBearRunMax > 63)

plot(issue68CtrlInWindow ? 3.0 : na, "EXPECTED Bull control", color=colGreen, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68CtrlValid ? 2.0 : na, "PROD TOP", color=issue68CtrlProdBullNow ? colGreen : issue68CtrlProdBearNow ? colRed : colNeutral, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68CtrlValid ? 1.0 : na, "PROD+CTX TOP", color=issue68CtrlCtxBullNow ? colGreen : issue68CtrlCtxBearNow ? colRed : colNeutral, linewidth=4, style=plot.style_linebr, display=display.pane)

var table tCtrl = table.new(position.middle_right, 4, 17, border_width=1)
if barstate.islast
    if showIssue68CtrlTable
        table.cell(tCtrl, 0, 0, "CTX CONTROL", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 1, 0, issue68CtrlName, bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 2, 0, "PROD", bgcolor=colRed, text_color=color.white)
        table.cell(tCtrl, 3, 0, "PROD+CTX", bgcolor=colGreen, text_color=color.white)

        table.cell(tCtrl, 0, 1, "Population", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 1, 1, str.tostring(issue68CtrlN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 2, 1, issue68CtrlSupported ? "fixed window" : "unsupported", bgcolor=issue68CtrlSupported ? colNeutral : colRed, text_color=color.white)
        table.cell(tCtrl, 3, 1, "expected BULL", bgcolor=colGreen, text_color=color.white)

        table.cell(tCtrl, 0, 2, "Bull TOP", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 1, 2, "occupancy", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 2, 2, f_issue68CtrlFmtPct(issue68CtrlProdBull, issue68CtrlN), bgcolor=colRed, text_color=color.white)
        table.cell(tCtrl, 3, 2, f_issue68CtrlFmtPct(issue68CtrlCtxBull, issue68CtrlN), bgcolor=colGreen, text_color=color.white)

        table.cell(tCtrl, 0, 3, "Bear TOP", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 1, 3, "opposite", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 2, 3, f_issue68CtrlFmtPct(issue68CtrlProdBear, issue68CtrlN), bgcolor=colRed, text_color=color.white)
        table.cell(tCtrl, 3, 3, f_issue68CtrlFmtPct(issue68CtrlCtxBear, issue68CtrlN), bgcolor=colGreen, text_color=color.white)

        table.cell(tCtrl, 0, 4, "Neutral TOP", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 1, 4, "S1+S4", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 2, 4, f_issue68CtrlFmtPct(issue68CtrlProdNeutral, issue68CtrlN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 3, 4, f_issue68CtrlFmtPct(issue68CtrlCtxNeutral, issue68CtrlN), bgcolor=colNeutral, text_color=color.white)

        table.cell(tCtrl, 0, 5, "S1 TOP", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 1, 5, "Accumulation", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 2, 5, f_issue68CtrlFmtPct(issue68CtrlProdS1, issue68CtrlN), bgcolor=colRed, text_color=color.white)
        table.cell(tCtrl, 3, 5, f_issue68CtrlFmtPct(issue68CtrlCtxS1, issue68CtrlN), bgcolor=colGreen, text_color=color.white)

        table.cell(tCtrl, 0, 6, "Bull delta", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 1, 6, "CTX - PROD", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 2, 6, "—", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 3, 6, f_issue68CtrlFmt(issue68CtrlBullDelta) + " pp", bgcolor=issue68CtrlBullDelta >= 0 ? colGreen : colRed, text_color=color.white)

        table.cell(tCtrl, 0, 7, "Bull retained", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 1, 7, "of PROD Bull", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 2, 7, str.tostring(issue68CtrlProdBull), bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 3, 7, f_issue68CtrlFmtPct(issue68CtrlBullRetained, issue68CtrlProdBull), bgcolor=colGreen, text_color=color.white)

        table.cell(tCtrl, 0, 8, "Bull lost", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 1, 8, "Bull -> nonBull", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 2, 8, str.tostring(issue68CtrlBullLost), bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 3, 8, f_issue68CtrlFmtPct(issue68CtrlBullLost, issue68CtrlN), bgcolor=issue68CtrlBullLost == 0 ? colGreen : colRed, text_color=color.white)

        table.cell(tCtrl, 0, 9, "Bull gained", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 1, 9, "nonBull -> Bull", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 2, 9, str.tostring(issue68CtrlBullGained), bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 3, 9, f_issue68CtrlFmtPct(issue68CtrlBullGained, issue68CtrlN), bgcolor=colGreen, text_color=color.white)

        table.cell(tCtrl, 0, 10, "TOP changed", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 1, 10, "all changes", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 2, 10, "0%", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 3, 10, f_issue68CtrlFmtPct(issue68CtrlTopChanged, issue68CtrlN), bgcolor=colNeutral, text_color=color.white)

        table.cell(tCtrl, 0, 11, "S1 gate avg", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 1, 11, "prod / ctx", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 2, 11, f_issue68CtrlFmt(f_issue68CtrlAvg(issue68CtrlSumProdGate, issue68CtrlN)), bgcolor=colRed, text_color=color.white)
        table.cell(tCtrl, 3, 11, f_issue68CtrlFmt(f_issue68CtrlAvg(issue68CtrlSumCtxGate, issue68CtrlN)), bgcolor=colGreen, text_color=color.white)

        table.cell(tCtrl, 0, 12, "DownEx capped", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 1, 12, "share", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 2, 12, "—", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 3, 12, f_issue68CtrlFmtPct(issue68CtrlCapN, issue68CtrlN), bgcolor=colNeutral, text_color=color.white)

        table.cell(tCtrl, 0, 13, "Longest CTX Bear", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 1, 13, ">63 = hard fail", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 2, 13, "—", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 3, 13, str.tostring(issue68CtrlCtxBearRunMax) + " bars", bgcolor=issue68CtrlCtxBearRunMax > 63 ? colRed : colGreen, text_color=color.white)

        table.cell(tCtrl, 0, 14, "CTX hard semantic", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 1, 14, ">50% Bear OR >63 run", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 2, 14, "existing rule", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 3, 14, issue68CtrlHardFail ? "FAIL" : "NO HARD FAIL", bgcolor=issue68CtrlHardFail ? colRed : colGreen, text_color=color.white)

        table.cell(tCtrl, 0, 15, "READ", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 1, 15, "JP / US / GB", bgcolor=colGreen, text_color=color.white)
        table.cell(tCtrl, 2, 15, "NO TUNING", bgcolor=colRed, text_color=color.white)
        table.cell(tCtrl, 3, 15, "CONTROL", bgcolor=colGreen, text_color=color.white)

        table.cell(tCtrl, 0, 16, "NEXT", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 1, 16, "then true-S1 preserve", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 2, 16, "FROZEN C-2", bgcolor=colNeutral, text_color=color.white)
        table.cell(tCtrl, 3, 16, "NO PNL", bgcolor=colNeutral, text_color=color.white)
    else
        table.clear(tCtrl, 0, 0, 3, 16)
'''


def generate(source: Path) -> str:
    d1_text = base.phase_b.d1.generate(source)
    if d1_text.count(base.phase_b.D1_EXPORT_MARKER) != 1:
        raise RuntimeError("expected exactly one D1 parity export marker")
    core = d1_text.split(base.phase_b.D1_EXPORT_MARKER, 1)[0].rstrip()
    core = replace_once(core, base.phase_b.D1_INDICATOR_DECL, AUDIT_DECL)
    out = core + "\n\n" + BODY + "\n"
    for token in (
        "DownEx Current-Context Cross-Market Controls",
        "JP10Y",
        "US10Y",
        "GB10Y",
        "Bull retained",
        "CTX hard semantic",
        "then true-S1 preserve",
    ):
        if token not in out:
            raise RuntimeError(f"missing required audit token: {token}")
    if "strategy.entry" in out or "strategy.close" in out:
        raise RuntimeError("DownEx context control audit leaked strategy order logic")
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
