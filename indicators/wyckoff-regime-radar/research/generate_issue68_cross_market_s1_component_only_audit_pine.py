#!/usr/bin/env python3
"""Generate Issue #68 S1 Accumulation component-only attribution Pine.

Discovery-only diagnostic. Reuses the frozen C-2 calculation core and changes no
classifier, Core, Exposure, or strategy semantics.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_phase_b_lifecycle_pine as phase_b
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 S1 Component Only", shorttitle="ChaseRisk #68 S1ONLY", overlay=false, precision=2)'

BODY = r'''

// ============================================================================
// Issue #68 Cross-Market S1 Accumulation Component-Only Attribution.
// Shared window: 2022-01-03 -> 2023-12-29, expected Bull yield regime.
// DISCOVERY ONLY. NO PNL. NO TUNING. FROZEN C-2.
// ============================================================================

groupIssue68S1Only = "Issue #68｜S1 Component Only"
showIssue68S1OnlyTable = input.bool(true, "顯示 S1 component 統計表", group=groupIssue68S1Only)

issue68S1OnlyReady = bar_index >= rankLen - 1
int issue68S1OnlyStart = timestamp(2022, 1, 3, 0, 0)
int issue68S1OnlyEnd = timestamp(2023, 12, 29, 23, 59)
bool issue68S1OnlyInWindow = issue68S1OnlyReady and time >= issue68S1OnlyStart and time <= issue68S1OnlyEnd

f_issue68S1OnlyAvg(float s, int n) => n > 0 ? s / n : na

var int issue68S1OnlyBars = 0
var float sumBearMatTrace = 0.0
var float sumRange = 0.0
var float sumDownEx = 0.0
var float sumSupport = 0.0
var float sumLowVol = 0.0
var float sumAccRaw0 = 0.0
var float sumAccRaw = 0.0
var float sumMarkupRaw = 0.0
var float sumAccMinusMarkup = 0.0

if issue68S1OnlyInWindow
    issue68S1OnlyBars += 1
    sumBearMatTrace += bearMaturityTrace
    sumRange += rangeScore
    sumDownEx += downsideExhaustion
    sumSupport += supportHolding
    sumLowVol += lowVolScore
    sumAccRaw0 += accRaw0
    sumAccRaw += accRaw
    sumMarkupRaw += markupRaw
    sumAccMinusMarkup += accRaw - markupRaw

float avgBearMatTrace = f_issue68S1OnlyAvg(sumBearMatTrace, issue68S1OnlyBars)
float avgRange = f_issue68S1OnlyAvg(sumRange, issue68S1OnlyBars)
float avgDownEx = f_issue68S1OnlyAvg(sumDownEx, issue68S1OnlyBars)
float avgSupport = f_issue68S1OnlyAvg(sumSupport, issue68S1OnlyBars)
float avgLowVol = f_issue68S1OnlyAvg(sumLowVol, issue68S1OnlyBars)
float avgAccRaw0 = f_issue68S1OnlyAvg(sumAccRaw0, issue68S1OnlyBars)
float avgAccRaw = f_issue68S1OnlyAvg(sumAccRaw, issue68S1OnlyBars)
float avgMarkupRaw = f_issue68S1OnlyAvg(sumMarkupRaw, issue68S1OnlyBars)
float avgAccMinusMarkup = f_issue68S1OnlyAvg(sumAccMinusMarkup, issue68S1OnlyBars)

float ptsBearMatTrace = avgBearMatTrace * 0.20
float ptsRange = avgRange * 0.20
float ptsDownEx = avgDownEx * 0.25
float ptsSupport = avgSupport * 0.25
float ptsLowVol = avgLowVol * 0.10
float ptsReconstructed = ptsBearMatTrace + ptsRange + ptsDownEx + ptsSupport + ptsLowVol
float reconstructionError = ptsReconstructed - avgAccRaw0

// Two plot-safe lanes only.
plot(issue68S1OnlyInWindow ? 2.0 : na, "EXPECTED Bull", color=colGreen, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68S1OnlyInWindow ? 1.0 : na, "S1 vs S2", color=accRaw >= markupRaw ? colRed : colGreen, linewidth=4, style=plot.style_linebr, display=display.pane)

var table t = table.new(position.bottom_right, 4, 11, border_width=1)
if barstate.islast
    if showIssue68S1OnlyTable
        table.cell(t, 0, 0, "S1 COMPONENT ATTRIB", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 0, syminfo.ticker, bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 0, "2022-2023 BULL", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 0, str.tostring(issue68S1OnlyBars) + " bars", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 1, "S1 DRIVER", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 1, "AVG", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 1, "WEIGHT", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 1, "WEIGHTED PTS", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 2, "Bear maturity trace", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 2, str.tostring(avgBearMatTrace, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 2, "20%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 2, str.tostring(ptsBearMatTrace, "#.1"), bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 3, "Range score", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 3, str.tostring(avgRange, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 3, "20%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 3, str.tostring(ptsRange, "#.1"), bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 4, "Down exhaustion", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 4, str.tostring(avgDownEx, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 4, "25%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 4, str.tostring(ptsDownEx, "#.1"), bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 5, "Support holding", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 5, str.tostring(avgSupport, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 5, "25%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 5, str.tostring(ptsSupport, "#.1"), bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 6, "Low vol", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 6, str.tostring(avgLowVol, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 6, "10%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 6, str.tostring(ptsLowVol, "#.1"), bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 7, "S1 RAW0 / RAW", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 7, str.tostring(avgAccRaw0, "#.1") + " / " + str.tostring(avgAccRaw, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 7, "RECON", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 7, str.tostring(ptsReconstructed, "#.1"), bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 8, "Recon error", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 8, str.tostring(reconstructionError, "#.3"), bgcolor=math.abs(reconstructionError) < 0.01 ? colGreen : colRed, text_color=color.white)
        table.cell(t, 2, 8, "AVG", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 8, "RAW0", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 9, "S2 Markup RAW", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 1, 9, str.tostring(avgMarkupRaw, "#.1"), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 9, "S1-S2", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 9, str.tostring(avgAccMinusMarkup, "#.1"), bgcolor=avgAccMinusMarkup > 0 ? colRed : colGreen, text_color=color.white)

        table.cell(t, 0, 10, "MODE", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 10, "DISCOVERY", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 10, "NO TUNING", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 10, "FROZEN C-2", bgcolor=colNeutral, text_color=color.white)
    else
        table.clear(t, 0, 0, 3, 10)
'''.strip()


def generate(source: Path) -> str:
    d1_text = phase_b.d1.generate(source)
    if d1_text.count(phase_b.D1_EXPORT_MARKER) != 1:
        raise RuntimeError("expected exactly one D1 parity export marker")
    core = d1_text.split(phase_b.D1_EXPORT_MARKER, 1)[0].rstrip()
    core = replace_once(core, phase_b.D1_INDICATOR_DECL, AUDIT_DECL)
    out = core + "\n\n" + BODY + "\n"

    required = (
        "S1 Accumulation Component-Only Attribution",
        "bearMaturityTrace",
        "rangeScore",
        "downsideExhaustion",
        "supportHolding",
        "lowVolScore",
        "WEIGHTED PTS",
        "Recon error",
        "S2 Markup RAW",
    )
    for token in required:
        if token not in out:
            raise RuntimeError(f"missing S1-only token: {token}")
    if "strategy." in out:
        raise RuntimeError("strategy token leaked into S1-only diagnostic")
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
