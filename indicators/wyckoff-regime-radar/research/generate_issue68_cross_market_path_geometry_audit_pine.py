#!/usr/bin/env python3
"""Generate Issue #68 FR10Y vs DE10Y path-geometry / transformation audit Pine.

Discovery-only diagnostic. Reuses the frozen C-2 calculation core and changes no
classifier, Core, Exposure, lifecycle, or strategy semantics.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_phase_b_lifecycle_pine as phase_b
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 Path Geometry", shorttitle="ChaseRisk #68 PATH", overlay=false, precision=2)'

BODY = r'''

// ============================================================================
// Issue #68 FR10Y vs DE10Y Path-Geometry / Transformation Audit.
// Shared window: 2022-01-03 -> 2023-12-29, expected Bull yield regime.
// DISCOVERY ONLY. NO PNL. NO TUNING. FROZEN C-2.
// ============================================================================

groupIssue68Path = "Issue #68｜FR-DE Path Geometry"
showIssue68PathTable = input.bool(true, "顯示 Path Geometry 統計表", group=groupIssue68Path)

issue68PathReady = bar_index >= rankLen - 1
int issue68PathStart = timestamp(2022, 1, 3, 0, 0)
int issue68PathEnd = timestamp(2023, 12, 29, 23, 59)
bool issue68PathInWindow = issue68PathReady and time >= issue68PathStart and time <= issue68PathEnd

f_issue68PathAvg(float s, int n) => n > 0 ? s / n : na
f_issue68PathPct(int n, int d) => d > 0 ? 100.0 * n / d : na

// --------------------------------------------------------------------------
// Raw market-path geometry. Yield charts are in percentage-point units:
// 0.01 percentage point = 1 bp, hence *100 for bp conversion.
// --------------------------------------------------------------------------
float issue68D1 = ta.change(close)
float issue68AbsD1 = math.abs(issue68D1)
float issue68Move20 = close - close[20]
float issue68Move60 = close - close[60]
float issue68Path20 = ta.sma(issue68AbsD1, 20) * 20.0
float issue68Path60 = ta.sma(issue68AbsD1, 60) * 60.0
float issue68Eff20 = issue68Path20 > 0.0 ? math.abs(issue68Move20) / issue68Path20 : na
float issue68Eff60 = issue68Path60 > 0.0 ? math.abs(issue68Move60) / issue68Path60 : na
float issue68Range20Bp = (ta.highest(high, 20) - ta.lowest(low, 20)) * 100.0
float issue68Atr20 = ta.atr(20)
float issue68Move20Atr = issue68Atr20 > 0.0 ? issue68Move20 / issue68Atr20 : na
int issue68Dir = issue68D1 > 0.0 ? 1 : issue68D1 < 0.0 ? -1 : 0
int issue68PrevDir = issue68D1[1] > 0.0 ? 1 : issue68D1[1] < 0.0 ? -1 : 0
bool issue68DirComparable = issue68Dir != 0 and issue68PrevDir != 0
bool issue68DirFlip = issue68DirComparable and issue68Dir != issue68PrevDir

bool issue68BullTop = issue68PathInWindow and (topId == 2 or topId == 3)
bool issue68BullGapPass = issue68BullTop and topGap >= topGapMin

var int issue68Bars = 0
var float issue68SumAbs1Bp = 0.0
var float issue68SumMove20Bp = 0.0
var float issue68SumAbsMove20Bp = 0.0
var int issue68Move20Positive = 0
var float issue68SumMove60Bp = 0.0
var float issue68SumAbsMove60Bp = 0.0
var float issue68SumEff20 = 0.0
var float issue68SumEff60 = 0.0
var float issue68SumRange20Bp = 0.0
var float issue68SumMove20Atr = 0.0
var int issue68DirComparableBars = 0
var int issue68DirFlipBars = 0

var float issue68SumHeat = 0.0
var float issue68SumMarkupExt = 0.0
var float issue68SumMarkupCont = 0.0
var float issue68SumRangeScore = 0.0
var float issue68SumAccRaw = 0.0
var float issue68SumMarkupRaw = 0.0
var float issue68SumS2S1 = 0.0
var int issue68BullTopBars = 0
var float issue68SumBullTopGap = 0.0
var int issue68BullGapPassBars = 0

if issue68PathInWindow
    issue68Bars += 1
    issue68SumAbs1Bp += issue68AbsD1 * 100.0
    issue68SumMove20Bp += issue68Move20 * 100.0
    issue68SumAbsMove20Bp += math.abs(issue68Move20) * 100.0
    issue68Move20Positive += issue68Move20 > 0.0 ? 1 : 0
    issue68SumMove60Bp += issue68Move60 * 100.0
    issue68SumAbsMove60Bp += math.abs(issue68Move60) * 100.0
    issue68SumEff20 += issue68Eff20
    issue68SumEff60 += issue68Eff60
    issue68SumRange20Bp += issue68Range20Bp
    issue68SumMove20Atr += issue68Move20Atr
    if issue68DirComparable
        issue68DirComparableBars += 1
        issue68DirFlipBars += issue68DirFlip ? 1 : 0

    issue68SumHeat += heatUp
    issue68SumMarkupExt += markupExtensionScore
    issue68SumMarkupCont += markupContinuationScore
    issue68SumRangeScore += rangeScore
    issue68SumAccRaw += accRaw
    issue68SumMarkupRaw += markupRaw
    issue68SumS2S1 += markupRaw - accRaw

    if issue68BullTop
        issue68BullTopBars += 1
        issue68SumBullTopGap += topGap
        issue68BullGapPassBars += issue68BullGapPass ? 1 : 0

float issue68AvgAbs1Bp = f_issue68PathAvg(issue68SumAbs1Bp, issue68Bars)
float issue68AvgMove20Bp = f_issue68PathAvg(issue68SumMove20Bp, issue68Bars)
float issue68AvgAbsMove20Bp = f_issue68PathAvg(issue68SumAbsMove20Bp, issue68Bars)
float issue68Move20PositivePct = f_issue68PathPct(issue68Move20Positive, issue68Bars)
float issue68AvgMove60Bp = f_issue68PathAvg(issue68SumMove60Bp, issue68Bars)
float issue68AvgAbsMove60Bp = f_issue68PathAvg(issue68SumAbsMove60Bp, issue68Bars)
float issue68AvgEff20 = f_issue68PathAvg(issue68SumEff20, issue68Bars)
float issue68AvgEff60 = f_issue68PathAvg(issue68SumEff60, issue68Bars)
float issue68AvgRange20Bp = f_issue68PathAvg(issue68SumRange20Bp, issue68Bars)
float issue68AvgMove20Atr = f_issue68PathAvg(issue68SumMove20Atr, issue68Bars)
float issue68DirFlipPct = f_issue68PathPct(issue68DirFlipBars, issue68DirComparableBars)

float issue68AvgHeat = f_issue68PathAvg(issue68SumHeat, issue68Bars)
float issue68AvgMarkupExt = f_issue68PathAvg(issue68SumMarkupExt, issue68Bars)
float issue68AvgMarkupCont = f_issue68PathAvg(issue68SumMarkupCont, issue68Bars)
float issue68AvgRangeScore = f_issue68PathAvg(issue68SumRangeScore, issue68Bars)
float issue68AvgAccRaw = f_issue68PathAvg(issue68SumAccRaw, issue68Bars)
float issue68AvgMarkupRaw = f_issue68PathAvg(issue68SumMarkupRaw, issue68Bars)
float issue68AvgS2S1 = f_issue68PathAvg(issue68SumS2S1, issue68Bars)
float issue68BullTopPct = f_issue68PathPct(issue68BullTopBars, issue68Bars)
float issue68AvgBullTopGap = f_issue68PathAvg(issue68SumBullTopGap, issue68BullTopBars)
float issue68BullGapPassPct = f_issue68PathPct(issue68BullGapPassBars, issue68BullTopBars)

// Minimal plot-safe lanes.
plot(issue68PathInWindow ? 3.0 : na, "EXPECTED Bull", color=colGreen, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68PathInWindow ? 2.0 : na, "20D move direction", color=issue68Move20 > 0 ? colGreen : colRed, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68PathInWindow ? 1.0 : na, "S2-S1 sign", color=markupRaw > accRaw ? colGreen : colRed, linewidth=4, style=plot.style_linebr, display=display.pane)

var table t = table.new(position.bottom_right, 4, 23, border_width=1)
if barstate.islast
    if showIssue68PathTable
        table.cell(t, 0, 0, "PATH GEOMETRY", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 0, syminfo.ticker, bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 0, "2022-2023 BULL", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 0, str.tostring(issue68Bars) + " bars", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 1, "RAW MARKET PATH", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 1, "AVG / SHARE", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 1, "UNIT", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 1, "READ", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 2, "Abs 1D move", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 2, str.tostring(issue68AvgAbs1Bp, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 2, "bp", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 2, "daily amplitude", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 3, "20D net move", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 3, str.tostring(issue68AvgMove20Bp, "#.1"), bgcolor=issue68AvgMove20Bp >= 0 ? colGreen : colRed, text_color=color.white)
        table.cell(t, 2, 3, "bp", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 3, "signed trend", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 4, "Abs 20D move", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 4, str.tostring(issue68AvgAbsMove20Bp, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 4, "bp", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 4, "20D amplitude", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 5, "20D positive", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 5, str.tostring(issue68Move20PositivePct, "#.1") + "%", bgcolor=issue68Move20PositivePct >= 50 ? colGreen : colRed, text_color=color.white)
        table.cell(t, 2, 5, "share", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 5, "direction persistence", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 6, "60D net move", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 6, str.tostring(issue68AvgMove60Bp, "#.1"), bgcolor=issue68AvgMove60Bp >= 0 ? colGreen : colRed, text_color=color.white)
        table.cell(t, 2, 6, "bp", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 6, "signed trend", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 7, "Abs 60D move", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 7, str.tostring(issue68AvgAbsMove60Bp, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 7, "bp", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 7, "60D amplitude", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 8, "20D efficiency", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 8, str.tostring(issue68AvgEff20, "#.3"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 8, "0-1", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 8, "straightness", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 9, "60D efficiency", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 9, str.tostring(issue68AvgEff60, "#.3"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 9, "0-1", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 9, "straightness", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 10, "20D high-low range", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 10, str.tostring(issue68AvgRange20Bp, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 10, "bp", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 10, "local span", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 11, "20D move / ATR20", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 11, str.tostring(issue68AvgMove20Atr, "#.2"), bgcolor=issue68AvgMove20Atr >= 0 ? colGreen : colRed, text_color=color.white)
        table.cell(t, 2, 11, "xATR", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 11, "normalized trend", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 12, "Daily direction flips", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 12, str.tostring(issue68DirFlipPct, "#.1") + "%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 12, "share", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 12, "choppiness", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 13, "FROZEN MODEL VIEW", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 1, 13, "AVG / SHARE", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 13, "UNIT", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 13, "ROLE", bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 14, "Heat up", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 14, str.tostring(issue68AvgHeat, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 14, "score", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 14, "S2 driver", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 15, "Markup extension", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 15, str.tostring(issue68AvgMarkupExt, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 15, "score", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 15, "S2 driver", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 16, "Markup continuation", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 16, str.tostring(issue68AvgMarkupCont, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 16, "score", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 16, "S2 driver", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 17, "Range score", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 17, str.tostring(issue68AvgRangeScore, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 17, "score", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 17, "S1 driver", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 18, "S1 / S2 RAW", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 18, str.tostring(issue68AvgAccRaw, "#.1") + " / " + str.tostring(issue68AvgMarkupRaw, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 18, "score", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 18, "competition", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 19, "S2 - S1", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 19, str.tostring(issue68AvgS2S1, "#.1"), bgcolor=issue68AvgS2S1 > 0 ? colGreen : colRed, text_color=color.white)
        table.cell(t, 2, 19, "score", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 19, "RAW gap", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 20, "Bull TOP occupancy", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 20, str.tostring(issue68BullTopPct, "#.1") + "%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 20, "share", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 20, "TOP stage", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 21, "Bull TOP avg gap", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 21, str.tostring(issue68AvgBullTopGap, "#.1"), bgcolor=issue68AvgBullTopGap >= topGapMin ? colGreen : colRed, text_color=color.white)
        table.cell(t, 2, 21, "score", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 21, "gap quality", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 22, "Bull TOP gap pass", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 22, str.tostring(issue68BullGapPassPct, "#.1") + "%", bgcolor=issue68BullGapPassPct >= 50 ? colGreen : colRed, text_color=color.white)
        table.cell(t, 2, 22, "share", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 22, "NO TUNING", bgcolor=colNeutral, text_color=color.white)
    else
        table.clear(t, 0, 0, 3, 22)
'''.strip()


def generate(source: Path) -> str:
    d1_text = phase_b.d1.generate(source)
    if d1_text.count(phase_b.D1_EXPORT_MARKER) != 1:
        raise RuntimeError("expected exactly one D1 parity export marker")
    core = d1_text.split(phase_b.D1_EXPORT_MARKER, 1)[0].rstrip()
    core = replace_once(core, phase_b.D1_INDICATOR_DECL, AUDIT_DECL)
    out = core + "\n\n" + BODY + "\n"

    required = (
        "Path-Geometry / Transformation Audit",
        "issue68Eff20",
        "Daily direction flips",
        "heatUp",
        "markupExtensionScore",
        "rangeScore",
        "Bull TOP avg gap",
    )
    for token in required:
        if token not in out:
            raise RuntimeError(f"missing path-geometry token: {token}")
    if "strategy." in out:
        raise RuntimeError("strategy token leaked into path-geometry diagnostic")
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
