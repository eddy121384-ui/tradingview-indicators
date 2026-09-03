#!/usr/bin/env python3
"""Generate Issue #68 cross-market RAW family competition attribution Pine.

Discovery-only diagnostic. Reuses the frozen C-2 calculation core and changes no
classifier, Core, Exposure, or strategy semantics.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_phase_b_lifecycle_pine as phase_b
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 RAW Family Competition", shorttitle="ChaseRisk #68 RAWFAM", overlay=false, precision=2)'

RAW_FAMILY_BODY = r'''

// ============================================================================
// Issue #68 Cross-Market RAW Family Competition Attribution — DISCOVERY ONLY.
// Shared window: 2022-01-03 -> 2023-12-29, expected Bull yield regime.
// NO PNL. NO TUNING. NO CLASSIFIER / CORE / EXPOSURE CHANGE.
// ============================================================================

groupIssue68RawFam = "Issue #68｜RAW Family Competition"
showIssue68RawFamTable = input.bool(true, "顯示 RAW competition 統計表", group=groupIssue68RawFam)

issue68RawFamReady = bar_index >= rankLen - 1
int issue68RawFamStart = timestamp(2022, 1, 3, 0, 0)
int issue68RawFamEnd = timestamp(2023, 12, 29, 23, 59)
bool issue68RawFamInWindow = issue68RawFamReady and time >= issue68RawFamStart and time <= issue68RawFamEnd

f_issue68RawFamWinner() =>
    float v = accRaw
    int id = 1
    if markupRaw > v
        v := markupRaw
        id := 2
    if reaccRaw > v
        v := reaccRaw
        id := 3
    if distRaw > v
        v := distRaw
        id := 4
    if markdownRaw > v
        v := markdownRaw
        id := 5
    if redistRaw > v
        id := 6
    id

f_issue68RawFamDir(int id) => id == 2 or id == 3 ? 1 : id == 5 or id == 6 ? -1 : 0
f_issue68RawFamDirColor(int d) => d == 1 ? colGreen : d == -1 ? colRed : colNeutral
f_issue68RawFamPct(int n, int d) => d > 0 ? 100.0 * n / d : na
f_issue68RawFamAvg(float s, int d) => d > 0 ? s / d : na

int issue68RawFamWinner = f_issue68RawFamWinner()
int issue68RawFamDir = f_issue68RawFamDir(issue68RawFamWinner)

var int issue68RawFamBars = 0
var int issue68RawFamWin1 = 0
var int issue68RawFamWin2 = 0
var int issue68RawFamWin3 = 0
var int issue68RawFamWin4 = 0
var int issue68RawFamWin5 = 0
var int issue68RawFamWin6 = 0
var float issue68RawFamSum1 = 0.0
var float issue68RawFamSum2 = 0.0
var float issue68RawFamSum3 = 0.0
var float issue68RawFamSum4 = 0.0
var float issue68RawFamSum5 = 0.0
var float issue68RawFamSum6 = 0.0
var int issue68RawFamBullWins = 0
var int issue68RawFamNeutralWins = 0
var int issue68RawFamBearWins = 0
var float issue68RawFamBullMaxSum = 0.0
var float issue68RawFamNeutralMaxSum = 0.0
var float issue68RawFamBearMaxSum = 0.0
var float issue68RawFamBullMarginSum = 0.0

if issue68RawFamInWindow
    issue68RawFamBars += 1
    issue68RawFamWin1 += issue68RawFamWinner == 1 ? 1 : 0
    issue68RawFamWin2 += issue68RawFamWinner == 2 ? 1 : 0
    issue68RawFamWin3 += issue68RawFamWinner == 3 ? 1 : 0
    issue68RawFamWin4 += issue68RawFamWinner == 4 ? 1 : 0
    issue68RawFamWin5 += issue68RawFamWinner == 5 ? 1 : 0
    issue68RawFamWin6 += issue68RawFamWinner == 6 ? 1 : 0

    issue68RawFamSum1 += accRaw
    issue68RawFamSum2 += markupRaw
    issue68RawFamSum3 += reaccRaw
    issue68RawFamSum4 += distRaw
    issue68RawFamSum5 += markdownRaw
    issue68RawFamSum6 += redistRaw

    float bullMax = math.max(markupRaw, reaccRaw)
    float neutralMax = math.max(accRaw, distRaw)
    float bearMax = math.max(markdownRaw, redistRaw)
    float nonBullMax = math.max(neutralMax, bearMax)

    issue68RawFamBullWins += issue68RawFamDir == 1 ? 1 : 0
    issue68RawFamNeutralWins += issue68RawFamDir == 0 ? 1 : 0
    issue68RawFamBearWins += issue68RawFamDir == -1 ? 1 : 0
    issue68RawFamBullMaxSum += bullMax
    issue68RawFamNeutralMaxSum += neutralMax
    issue68RawFamBearMaxSum += bearMax
    issue68RawFamBullMarginSum += bullMax - nonBullMax

float issue68RawFamWinPct1 = f_issue68RawFamPct(issue68RawFamWin1, issue68RawFamBars)
float issue68RawFamWinPct2 = f_issue68RawFamPct(issue68RawFamWin2, issue68RawFamBars)
float issue68RawFamWinPct3 = f_issue68RawFamPct(issue68RawFamWin3, issue68RawFamBars)
float issue68RawFamWinPct4 = f_issue68RawFamPct(issue68RawFamWin4, issue68RawFamBars)
float issue68RawFamWinPct5 = f_issue68RawFamPct(issue68RawFamWin5, issue68RawFamBars)
float issue68RawFamWinPct6 = f_issue68RawFamPct(issue68RawFamWin6, issue68RawFamBars)

float issue68RawFamAvg1 = f_issue68RawFamAvg(issue68RawFamSum1, issue68RawFamBars)
float issue68RawFamAvg2 = f_issue68RawFamAvg(issue68RawFamSum2, issue68RawFamBars)
float issue68RawFamAvg3 = f_issue68RawFamAvg(issue68RawFamSum3, issue68RawFamBars)
float issue68RawFamAvg4 = f_issue68RawFamAvg(issue68RawFamSum4, issue68RawFamBars)
float issue68RawFamAvg5 = f_issue68RawFamAvg(issue68RawFamSum5, issue68RawFamBars)
float issue68RawFamAvg6 = f_issue68RawFamAvg(issue68RawFamSum6, issue68RawFamBars)

float issue68RawFamBullWinPct = f_issue68RawFamPct(issue68RawFamBullWins, issue68RawFamBars)
float issue68RawFamNeutralWinPct = f_issue68RawFamPct(issue68RawFamNeutralWins, issue68RawFamBars)
float issue68RawFamBearWinPct = f_issue68RawFamPct(issue68RawFamBearWins, issue68RawFamBars)
float issue68RawFamBullMaxAvg = f_issue68RawFamAvg(issue68RawFamBullMaxSum, issue68RawFamBars)
float issue68RawFamNeutralMaxAvg = f_issue68RawFamAvg(issue68RawFamNeutralMaxSum, issue68RawFamBars)
float issue68RawFamBearMaxAvg = f_issue68RawFamAvg(issue68RawFamBearMaxSum, issue68RawFamBars)
float issue68RawFamBullMarginAvg = f_issue68RawFamAvg(issue68RawFamBullMarginSum, issue68RawFamBars)

// Two plot-safe lanes only. Table carries the detailed six-stage statistics.
plot(issue68RawFamInWindow ? 2.0 : na, "EXPECTED Bull", color=colGreen, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68RawFamInWindow ? 1.0 : na, "RAW family winner", color=f_issue68RawFamDirColor(issue68RawFamDir), linewidth=4, style=plot.style_linebr, display=display.pane)

var table issue68RawFamTable = table.new(position.bottom_right, 4, 12, border_width=1)
if barstate.islast
    if showIssue68RawFamTable
        table.cell(issue68RawFamTable, 0, 0, "RAW FAMILY ATTRIB", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68RawFamTable, 1, 0, syminfo.ticker, bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68RawFamTable, 2, 0, "2022-2023 BULL", bgcolor=colGreen, text_color=color.white)
        table.cell(issue68RawFamTable, 3, 0, str.tostring(issue68RawFamBars) + " bars", bgcolor=colNeutral, text_color=color.white)

        table.cell(issue68RawFamTable, 0, 1, "STAGE / FAMILY", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68RawFamTable, 1, 1, "WIN %", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68RawFamTable, 2, 1, "AVG RAW", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68RawFamTable, 3, 1, "ROLE", bgcolor=colNeutral, text_color=color.white)

        table.cell(issue68RawFamTable, 0, 2, "S1 Acc", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68RawFamTable, 1, 2, str.tostring(issue68RawFamWinPct1, "#.0") + "%", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68RawFamTable, 2, 2, str.tostring(issue68RawFamAvg1, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68RawFamTable, 3, 2, "NEUTRAL", bgcolor=colNeutral, text_color=color.white)

        table.cell(issue68RawFamTable, 0, 3, "S2 Markup", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68RawFamTable, 1, 3, str.tostring(issue68RawFamWinPct2, "#.0") + "%", bgcolor=colGreen, text_color=color.white)
        table.cell(issue68RawFamTable, 2, 3, str.tostring(issue68RawFamAvg2, "#.1"), bgcolor=colGreen, text_color=color.white)
        table.cell(issue68RawFamTable, 3, 3, "BULL", bgcolor=colGreen, text_color=color.white)

        table.cell(issue68RawFamTable, 0, 4, "S3 Reacc", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68RawFamTable, 1, 4, str.tostring(issue68RawFamWinPct3, "#.0") + "%", bgcolor=colGreen, text_color=color.white)
        table.cell(issue68RawFamTable, 2, 4, str.tostring(issue68RawFamAvg3, "#.1"), bgcolor=colGreen, text_color=color.white)
        table.cell(issue68RawFamTable, 3, 4, "BULL", bgcolor=colGreen, text_color=color.white)

        table.cell(issue68RawFamTable, 0, 5, "S4 Dist", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68RawFamTable, 1, 5, str.tostring(issue68RawFamWinPct4, "#.0") + "%", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68RawFamTable, 2, 5, str.tostring(issue68RawFamAvg4, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68RawFamTable, 3, 5, "NEUTRAL", bgcolor=colNeutral, text_color=color.white)

        table.cell(issue68RawFamTable, 0, 6, "S5 Markdown", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68RawFamTable, 1, 6, str.tostring(issue68RawFamWinPct5, "#.0") + "%", bgcolor=colRed, text_color=color.white)
        table.cell(issue68RawFamTable, 2, 6, str.tostring(issue68RawFamAvg5, "#.1"), bgcolor=colRed, text_color=color.white)
        table.cell(issue68RawFamTable, 3, 6, "BEAR", bgcolor=colRed, text_color=color.white)

        table.cell(issue68RawFamTable, 0, 7, "S6 Redist", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68RawFamTable, 1, 7, str.tostring(issue68RawFamWinPct6, "#.0") + "%", bgcolor=colRed, text_color=color.white)
        table.cell(issue68RawFamTable, 2, 7, str.tostring(issue68RawFamAvg6, "#.1"), bgcolor=colRed, text_color=color.white)
        table.cell(issue68RawFamTable, 3, 7, "BEAR", bgcolor=colRed, text_color=color.white)

        table.cell(issue68RawFamTable, 0, 8, "BULL family", bgcolor=colGreen, text_color=color.white)
        table.cell(issue68RawFamTable, 1, 8, str.tostring(issue68RawFamBullWinPct, "#.0") + "%", bgcolor=colGreen, text_color=color.white)
        table.cell(issue68RawFamTable, 2, 8, str.tostring(issue68RawFamBullMaxAvg, "#.1"), bgcolor=colGreen, text_color=color.white)
        table.cell(issue68RawFamTable, 3, 8, "MAX S2/S3", bgcolor=colGreen, text_color=color.white)

        table.cell(issue68RawFamTable, 0, 9, "NEUTRAL family", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68RawFamTable, 1, 9, str.tostring(issue68RawFamNeutralWinPct, "#.0") + "%", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68RawFamTable, 2, 9, str.tostring(issue68RawFamNeutralMaxAvg, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68RawFamTable, 3, 9, "MAX S1/S4", bgcolor=colNeutral, text_color=color.white)

        table.cell(issue68RawFamTable, 0, 10, "BEAR family", bgcolor=colRed, text_color=color.white)
        table.cell(issue68RawFamTable, 1, 10, str.tostring(issue68RawFamBearWinPct, "#.0") + "%", bgcolor=colRed, text_color=color.white)
        table.cell(issue68RawFamTable, 2, 10, str.tostring(issue68RawFamBearMaxAvg, "#.1"), bgcolor=colRed, text_color=color.white)
        table.cell(issue68RawFamTable, 3, 10, "MAX S5/S6", bgcolor=colRed, text_color=color.white)

        table.cell(issue68RawFamTable, 0, 11, "BULL MARGIN", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68RawFamTable, 1, 11, "AVG", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68RawFamTable, 2, 11, str.tostring(issue68RawFamBullMarginAvg, "#.1"), bgcolor=issue68RawFamBullMarginAvg >= 0 ? colGreen : colRed, text_color=color.white)
        table.cell(issue68RawFamTable, 3, 11, "Bull - best nonBull", bgcolor=colNeutral, text_color=color.white)
    else
        table.clear(issue68RawFamTable, 0, 0, 3, 11)
'''.strip()


def generate(source: Path) -> str:
    d1_text = phase_b.d1.generate(source)
    if d1_text.count(phase_b.D1_EXPORT_MARKER) != 1:
        raise RuntimeError("expected exactly one D1 parity export marker")
    core = d1_text.split(phase_b.D1_EXPORT_MARKER, 1)[0].rstrip()
    core = replace_once(core, phase_b.D1_INDICATOR_DECL, AUDIT_DECL)
    out = core + "\n\n" + RAW_FAMILY_BODY + "\n"

    required = (
        "Cross-Market RAW Family Competition Attribution",
        "f_issue68RawFamWinner",
        "accRaw",
        "markupRaw",
        "reaccRaw",
        "distRaw",
        "markdownRaw",
        "redistRaw",
        "BULL MARGIN",
        "RAW family winner",
    )
    for token in required:
        if token not in out:
            raise RuntimeError(f"missing RAW family attribution token: {token}")

    forbidden = (
        "strategy.",
        "issue68B34A",
        "issue68B34B",
        "issue68B34C",
        "LONG SETUP",
        "SHORT SETUP",
    )
    for token in forbidden:
        if token in out:
            raise RuntimeError(f"forbidden lifecycle/strategy token leaked: {token}")

    # This audit intentionally adds only two plot() calls on top of the calculation core.
    if RAW_FAMILY_BODY.count("plot(") != 2:
        raise RuntimeError("RAW family audit plot budget changed")
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
