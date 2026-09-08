#!/usr/bin/env python3
"""Generate Issue #68 S1 Acc vs S2 Markup RAW component-attribution Pine.

Discovery-only diagnostic. Reuses the frozen C-2 calculation core and changes no
classifier, Core, Exposure, or strategy semantics.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_phase_b_lifecycle_pine as phase_b
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 S1 vs S2 RAW Components", shorttitle="ChaseRisk #68 S1S2", overlay=false, precision=2)'

BODY = r'''

// ============================================================================
// Issue #68 Cross-Market S1-vs-S2 RAW Component Attribution — DISCOVERY ONLY.
// Shared window: 2022-01-03 -> 2023-12-29, expected Bull yield regime.
// NO PNL. NO TUNING. NO CLASSIFIER / CORE / EXPOSURE CHANGE.
// ============================================================================

groupIssue68S1S2 = "Issue #68｜S1 vs S2 RAW Components"
showIssue68S1S2Table = input.bool(true, "顯示 S1/S2 component 統計表", group=groupIssue68S1S2)

issue68S1S2Ready = bar_index >= rankLen - 1
int issue68S1S2Start = timestamp(2022, 1, 3, 0, 0)
int issue68S1S2End = timestamp(2023, 12, 29, 23, 59)
bool issue68S1S2InWindow = issue68S1S2Ready and time >= issue68S1S2Start and time <= issue68S1S2End

f_issue68S1S2Avg(float s, int n) => n > 0 ? s / n : na

var int issue68S1S2Bars = 0
var float sumBearMatTrace = 0.0
var float sumRange = 0.0
var float sumDownEx = 0.0
var float sumSupport = 0.0
var float sumLowVol = 0.0
var float sumAccRaw0 = 0.0
var float sumAccRaw = 0.0

var float sumBreakout = 0.0
var float sumHeat = 0.0
var float sumStructure = 0.0
var float sumMarkupExt = 0.0
var float sumMarkupCont = 0.0
var float sumAccTraceMarkup = 0.0
var float sumMarkupBase = 0.0
var float sumMarkupRaw0 = 0.0
var float sumMarkupRaw = 0.0

var float sumGap = 0.0
var int s2AboveS1Bars = 0
var int s1GeS2Run = 0
var int maxS1GeS2Run = 0

if issue68S1S2InWindow
    issue68S1S2Bars += 1

    sumBearMatTrace += bearMaturityTrace
    sumRange += rangeScore
    sumDownEx += downsideExhaustion
    sumSupport += supportHolding
    sumLowVol += lowVolScore
    sumAccRaw0 += accRaw0
    sumAccRaw += accRaw

    sumBreakout += breakoutScore
    sumHeat += heatUp
    sumStructure += structureStrong
    sumMarkupExt += markupExtensionScore
    sumMarkupCont += markupContinuationScore
    sumAccTraceMarkup += accTraceForMarkup
    sumMarkupBase += markupBaseRaw
    sumMarkupRaw0 += markupRaw0
    sumMarkupRaw += markupRaw

    float gap = markupRaw - accRaw
    sumGap += gap
    s2AboveS1Bars += gap > 0 ? 1 : 0
    if gap <= 0
        s1GeS2Run += 1
        maxS1GeS2Run := math.max(maxS1GeS2Run, s1GeS2Run)
    else
        s1GeS2Run := 0

float avgBearMatTrace = f_issue68S1S2Avg(sumBearMatTrace, issue68S1S2Bars)
float avgRange = f_issue68S1S2Avg(sumRange, issue68S1S2Bars)
float avgDownEx = f_issue68S1S2Avg(sumDownEx, issue68S1S2Bars)
float avgSupport = f_issue68S1S2Avg(sumSupport, issue68S1S2Bars)
float avgLowVol = f_issue68S1S2Avg(sumLowVol, issue68S1S2Bars)
float avgAccRaw0 = f_issue68S1S2Avg(sumAccRaw0, issue68S1S2Bars)
float avgAccRaw = f_issue68S1S2Avg(sumAccRaw, issue68S1S2Bars)

float avgBreakout = f_issue68S1S2Avg(sumBreakout, issue68S1S2Bars)
float avgHeat = f_issue68S1S2Avg(sumHeat, issue68S1S2Bars)
float avgStructure = f_issue68S1S2Avg(sumStructure, issue68S1S2Bars)
float avgMarkupExt = f_issue68S1S2Avg(sumMarkupExt, issue68S1S2Bars)
float avgMarkupCont = f_issue68S1S2Avg(sumMarkupCont, issue68S1S2Bars)
float avgAccTraceMarkup = f_issue68S1S2Avg(sumAccTraceMarkup, issue68S1S2Bars)
float avgMarkupBase = f_issue68S1S2Avg(sumMarkupBase, issue68S1S2Bars)
float avgMarkupRaw0 = f_issue68S1S2Avg(sumMarkupRaw0, issue68S1S2Bars)
float avgMarkupRaw = f_issue68S1S2Avg(sumMarkupRaw, issue68S1S2Bars)

float avgGap = f_issue68S1S2Avg(sumGap, issue68S1S2Bars)
float s2AboveS1Pct = issue68S1S2Bars > 0 ? 100.0 * s2AboveS1Bars / issue68S1S2Bars : na

// Plot-safe lanes only. Green = S2 > S1, gray = S1 >= S2.
plot(issue68S1S2InWindow ? 2.0 : na, "EXPECTED Bull", color=colGreen, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68S1S2InWindow ? 1.0 : na, "S2 vs S1 winner", color=markupRaw > accRaw ? colGreen : colNeutral, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68S1S2InWindow ? 0.0 : na, "S2-S1 gap sign", color=markupRaw > accRaw ? colGreen : colRed, linewidth=4, style=plot.style_linebr, display=display.pane)

var table t = table.new(position.bottom_right, 4, 20, border_width=1)
if barstate.islast
    if showIssue68S1S2Table
        table.cell(t, 0, 0, "S1 vs S2 ATTRIB", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 0, syminfo.ticker, bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 0, "2022-2023 BULL", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 0, str.tostring(issue68S1S2Bars) + " bars", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 1, "S1 ACC DRIVER", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 1, "AVG", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 1, "WEIGHT", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 1, "ROLE", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 2, "Bear maturity trace", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 2, str.tostring(avgBearMatTrace, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 2, "20%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 2, "S1+", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 0, 3, "Range score", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 3, str.tostring(avgRange, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 3, "20%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 3, "S1+", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 0, 4, "Down exhaustion", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 4, str.tostring(avgDownEx, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 4, "25%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 4, "S1+", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 0, 5, "Support holding", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 5, str.tostring(avgSupport, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 5, "25%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 5, "S1+", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 0, 6, "Low vol", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 6, str.tostring(avgLowVol, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 6, "10%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 6, "S1+", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 0, 7, "S1 RAW0 / RAW", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 7, str.tostring(avgAccRaw0, "#.1") + " / " + str.tostring(avgAccRaw, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 7, "—", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 7, "ACC", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 8, "S2 MARKUP DRIVER", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 1, 8, "AVG", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 8, "RAW0 wt", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 8, "ROLE", bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 9, "Breakout", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 1, 9, str.tostring(avgBreakout, "#.1"), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 9, "17%", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 9, "S2+", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 0, 10, "Heat up", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 1, 10, str.tostring(avgHeat, "#.1"), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 10, "17%", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 10, "S2+", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 0, 11, "Structure strong", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 1, 11, str.tostring(avgStructure, "#.1"), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 11, "17%", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 11, "S2+", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 0, 12, "Markup extension", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 1, 12, str.tostring(avgMarkupExt, "#.1"), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 12, "21.25%", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 12, "S2+", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 0, 13, "Markup continuation", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 1, 13, str.tostring(avgMarkupCont, "#.1"), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 13, "12.75%", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 13, "S2+", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 0, 14, "Acc trace -> Markup", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 1, 14, str.tostring(avgAccTraceMarkup, "#.1"), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 14, "15%", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 14, "S2+", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 0, 15, "S2 Base / RAW0 / RAW", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 1, 15, str.tostring(avgMarkupBase, "#.1") + " / " + str.tostring(avgMarkupRaw0, "#.1") + " / " + str.tostring(avgMarkupRaw, "#.1"), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 15, "—", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 15, "MARKUP", bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 16, "S2 - S1 GAP", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 16, str.tostring(avgGap, "#.1"), bgcolor=avgGap > 0 ? colGreen : colRed, text_color=color.white)
        table.cell(t, 2, 16, "AVG", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 16, "RAW", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 0, 17, "S2 > S1", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 17, str.tostring(s2AboveS1Pct, "#.1") + "%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 17, "bars", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 17, "RAW", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 0, 18, "MAX S1>=S2 RUN", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 18, str.tostring(maxS1GeS2Run), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 18, "bars", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 18, "RAW", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 0, 19, "MODE", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 19, "DISCOVERY", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 19, "NO TUNING", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 19, "FROZEN C-2", bgcolor=colNeutral, text_color=color.white)
    else
        table.clear(t, 0, 0, 3, 19)
'''.strip()


def generate(source: Path) -> str:
    d1_text = phase_b.d1.generate(source)
    if d1_text.count(phase_b.D1_EXPORT_MARKER) != 1:
        raise RuntimeError("expected exactly one D1 parity export marker")
    core = d1_text.split(phase_b.D1_EXPORT_MARKER, 1)[0].rstrip()
    core = replace_once(core, phase_b.D1_INDICATOR_DECL, AUDIT_DECL)
    out = core + "\n\n" + BODY + "\n"

    required = (
        "S1-vs-S2 RAW Component Attribution",
        "bearMaturityTrace",
        "downsideExhaustion",
        "supportHolding",
        "markupExtensionScore",
        "markupContinuationScore",
        "accTraceForMarkup",
        "markupBaseRaw",
        "markupRaw0",
        "S2 - S1 GAP",
    )
    for token in required:
        if token not in out:
            raise RuntimeError(f"missing S1-vs-S2 token: {token}")
    if "strategy." in out:
        raise RuntimeError("strategy token leaked into S1-vs-S2 diagnostic")
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
