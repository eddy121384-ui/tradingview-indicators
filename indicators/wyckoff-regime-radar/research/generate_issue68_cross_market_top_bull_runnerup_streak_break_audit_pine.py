#!/usr/bin/env python3
"""Generate Issue #68 TOP-Bull runner-up / Strong streak-break attribution Pine.

Discovery-only diagnostic. Reuses the frozen C-2 calculation core and changes no
classifier, Core, Exposure, lifecycle, or strategy semantics.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_phase_b_lifecycle_pine as phase_b
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 Bull Runner-Up / Streak Break", shorttitle="ChaseRisk #68 RUNNER", overlay=false, precision=2)'

BODY = r'''

// ============================================================================
// Issue #68 TOP-Bull Runner-Up / Strong Streak-Break Attribution.
// Shared window: 2022-01-03 -> 2023-12-29, expected Bull yield regime.
// DISCOVERY ONLY. NO PNL. NO TUNING. FROZEN C-2.
// ============================================================================

groupIssue68Runner = "Issue #68｜TOP Bull Runner-Up / Streak Break"
showIssue68RunnerTable = input.bool(true, "顯示 Runner-Up / Streak Break 統計表", group=groupIssue68Runner)

issue68RunnerReady = bar_index >= rankLen - 1
int issue68RunnerStart = timestamp(2022, 1, 3, 0, 0)
int issue68RunnerEnd = timestamp(2023, 12, 29, 23, 59)
bool issue68RunnerInWindow = issue68RunnerReady and time >= issue68RunnerStart and time <= issue68RunnerEnd
bool issue68TopBull = issue68RunnerInWindow and (topId == 2 or topId == 3)
bool issue68GapFail = issue68TopBull and topGap < topGapMin
bool issue68StrongBull = issue68TopBull and strongCandidate
bool issue68PrevStrongBull = issue68StrongBull[1]
bool issue68StrongBreak = issue68RunnerInWindow and issue68PrevStrongBull and not issue68StrongBull

f_issue68Pct(int n, int d) => d > 0 ? 100.0 * n / d : na
f_issue68Avg(float s, int n) => n > 0 ? s / n : na
f_issue68StageName(int id) => id == 1 ? "S1 Acc" : id == 2 ? "S2 Markup" : id == 3 ? "S3 Reacc" : id == 4 ? "S4 Dist" : id == 5 ? "S5 Markdown" : id == 6 ? "S6 Redist" : "None"

// Streak-break reason, mutually exclusive and preserving frozen Strong conjunction order.
int issue68BreakReason = 0
if issue68StrongBreak
    issue68BreakReason := not (topId == 2 or topId == 3) ? 1 : not hasSharp ? 2 : topVal < dominantMin ? 3 : topGap < topGapMin ? 4 : not hasEvidence ? 5 : candidateConflict ? 6 : 7

// Runner-up counters: S1..S6.
var int[] issue68RunnerCount = array.new_int(6, 0)
var int[] issue68RunnerGapFailCount = array.new_int(6, 0)
var float[] issue68RunnerGapSum = array.new_float(6, 0.0)

var int issue68WindowBars = 0
var int issue68TopBullBars = 0
var int issue68GapFailBars = 0
var int issue68RunnerBullSibling = 0
var int issue68RunnerNeutral = 0
var int issue68RunnerBear = 0

var int issue68StrongBullBars = 0
var int issue68StrongRun = 0
var int issue68StrongMaxRun = 0
var int issue68StrongBreaks = 0
var int issue68BreakTopLost = 0
var int issue68BreakSharp = 0
var int issue68BreakDominant = 0
var int issue68BreakGap = 0
var int issue68BreakEvidence = 0
var int issue68BreakConflict = 0
var int issue68BreakOther = 0
var int issue68FormalBullAcquire = 0

bool issue68FormalBullNow = formalId == 2 or formalId == 3
bool issue68FormalBullPrev = formalId[1] == 2 or formalId[1] == 3

if issue68RunnerInWindow
    issue68WindowBars += 1

    if issue68TopBull
        issue68TopBullBars += 1
        issue68GapFailBars += issue68GapFail ? 1 : 0
        if secondId >= 1 and secondId <= 6
            int idx = secondId - 1
            array.set(issue68RunnerCount, idx, array.get(issue68RunnerCount, idx) + 1)
            array.set(issue68RunnerGapSum, idx, array.get(issue68RunnerGapSum, idx) + topGap)
            if issue68GapFail
                array.set(issue68RunnerGapFailCount, idx, array.get(issue68RunnerGapFailCount, idx) + 1)
        issue68RunnerBullSibling += (secondId == 2 or secondId == 3) ? 1 : 0
        issue68RunnerNeutral += (secondId == 1 or secondId == 4) ? 1 : 0
        issue68RunnerBear += (secondId == 5 or secondId == 6) ? 1 : 0

    if issue68StrongBull
        issue68StrongBullBars += 1
        issue68StrongRun += 1
        issue68StrongMaxRun := math.max(issue68StrongMaxRun, issue68StrongRun)
    else
        issue68StrongRun := 0

    if issue68StrongBreak
        issue68StrongBreaks += 1
        issue68BreakTopLost += issue68BreakReason == 1 ? 1 : 0
        issue68BreakSharp += issue68BreakReason == 2 ? 1 : 0
        issue68BreakDominant += issue68BreakReason == 3 ? 1 : 0
        issue68BreakGap += issue68BreakReason == 4 ? 1 : 0
        issue68BreakEvidence += issue68BreakReason == 5 ? 1 : 0
        issue68BreakConflict += issue68BreakReason == 6 ? 1 : 0
        issue68BreakOther += issue68BreakReason == 7 ? 1 : 0

    if issue68FormalBullNow and not issue68FormalBullPrev
        issue68FormalBullAcquire += 1

// Minimal plot-safe lanes.
plot(issue68RunnerInWindow ? 3.0 : na, "EXPECTED Bull", color=colGreen, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68TopBull ? 2.0 : na, "TOP Bull gap status", color=issue68GapFail ? colRed : colGreen, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68StrongBreak ? 1.0 : na, "Strong Bull streak break", color=color.orange, linewidth=4, style=plot.style_circles, display=display.pane)

var table t = table.new(position.bottom_right, 6, 20, border_width=1)
if barstate.islast
    if showIssue68RunnerTable
        table.cell(t, 0, 0, "TOP BULL RUNNER-UP", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 0, syminfo.ticker, bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 0, "2022-2023 BULL", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 0, "TOP Bull " + str.tostring(issue68TopBullBars), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 4, 0, "GapFail " + str.tostring(issue68GapFailBars), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 5, 0, "FROZEN C-2", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 1, "RUNNER-UP", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 1, "COUNT", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 1, "ALL SHARE", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 1, "AVG GAP", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 4, 1, "GAPFAIL N", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 5, 1, "GAPFAIL SHARE", bgcolor=colNeutral, text_color=color.white)

        for i = 0 to 5
            int n = array.get(issue68RunnerCount, i)
            int gf = array.get(issue68RunnerGapFailCount, i)
            float avgGap = f_issue68Avg(array.get(issue68RunnerGapSum, i), n)
            int row = i + 2
            table.cell(t, 0, row, f_issue68StageName(i + 1), bgcolor=colNeutral, text_color=color.white)
            table.cell(t, 1, row, str.tostring(n), bgcolor=colNeutral, text_color=color.white)
            table.cell(t, 2, row, str.tostring(f_issue68Pct(n, issue68TopBullBars), "#.1") + "%", bgcolor=colNeutral, text_color=color.white)
            table.cell(t, 3, row, str.tostring(avgGap, "#.1"), bgcolor=avgGap >= topGapMin ? colGreen : colRed, text_color=color.white)
            table.cell(t, 4, row, str.tostring(gf), bgcolor=gf > 0 ? colRed : colNeutral, text_color=color.white)
            table.cell(t, 5, row, str.tostring(f_issue68Pct(gf, issue68GapFailBars), "#.1") + "%", bgcolor=gf > 0 ? colRed : colNeutral, text_color=color.white)

        table.cell(t, 0, 8, "RUNNER FAMILY", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 8, "Bull sibling", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 8, str.tostring(f_issue68Pct(issue68RunnerBullSibling, issue68TopBullBars), "#.1") + "%", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 8, "Neutral", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 4, 8, str.tostring(f_issue68Pct(issue68RunnerNeutral, issue68TopBullBars), "#.1") + "%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 5, 8, "Bear " + str.tostring(f_issue68Pct(issue68RunnerBear, issue68TopBullBars), "#.1") + "%", bgcolor=colRed, text_color=color.white)

        table.cell(t, 0, 9, "STREAK BREAK", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 9, "Strong bars", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 9, str.tostring(issue68StrongBullBars), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 9, "Max run", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 4, 9, str.tostring(issue68StrongMaxRun), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 5, 9, "Breaks " + str.tostring(issue68StrongBreaks), bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 10, "BREAK REASON", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 10, "COUNT", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 10, "SHARE", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 10, "BREAK REASON", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 4, 10, "COUNT", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 5, 10, "SHARE", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 11, "TOP leaves Bull", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 11, str.tostring(issue68BreakTopLost), bgcolor=issue68BreakTopLost > 0 ? colRed : colNeutral, text_color=color.white)
        table.cell(t, 2, 11, str.tostring(f_issue68Pct(issue68BreakTopLost, issue68StrongBreaks), "#.1") + "%", bgcolor=issue68BreakTopLost > 0 ? colRed : colNeutral, text_color=color.white)
        table.cell(t, 3, 11, "Gap fails", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 4, 11, str.tostring(issue68BreakGap), bgcolor=issue68BreakGap > 0 ? colRed : colNeutral, text_color=color.white)
        table.cell(t, 5, 11, str.tostring(f_issue68Pct(issue68BreakGap, issue68StrongBreaks), "#.1") + "%", bgcolor=issue68BreakGap > 0 ? colRed : colNeutral, text_color=color.white)

        table.cell(t, 0, 12, "Sharp fails", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 12, str.tostring(issue68BreakSharp), bgcolor=issue68BreakSharp > 0 ? colRed : colNeutral, text_color=color.white)
        table.cell(t, 2, 12, str.tostring(f_issue68Pct(issue68BreakSharp, issue68StrongBreaks), "#.1") + "%", bgcolor=issue68BreakSharp > 0 ? colRed : colNeutral, text_color=color.white)
        table.cell(t, 3, 12, "Evidence fails", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 4, 12, str.tostring(issue68BreakEvidence), bgcolor=issue68BreakEvidence > 0 ? colRed : colNeutral, text_color=color.white)
        table.cell(t, 5, 12, str.tostring(f_issue68Pct(issue68BreakEvidence, issue68StrongBreaks), "#.1") + "%", bgcolor=issue68BreakEvidence > 0 ? colRed : colNeutral, text_color=color.white)

        table.cell(t, 0, 13, "Dominant fails", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 13, str.tostring(issue68BreakDominant), bgcolor=issue68BreakDominant > 0 ? colRed : colNeutral, text_color=color.white)
        table.cell(t, 2, 13, str.tostring(f_issue68Pct(issue68BreakDominant, issue68StrongBreaks), "#.1") + "%", bgcolor=issue68BreakDominant > 0 ? colRed : colNeutral, text_color=color.white)
        table.cell(t, 3, 13, "Conflict", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 4, 13, str.tostring(issue68BreakConflict), bgcolor=issue68BreakConflict > 0 ? colRed : colNeutral, text_color=color.white)
        table.cell(t, 5, 13, str.tostring(f_issue68Pct(issue68BreakConflict, issue68StrongBreaks), "#.1") + "%", bgcolor=issue68BreakConflict > 0 ? colRed : colNeutral, text_color=color.white)

        table.cell(t, 0, 14, "Other", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 14, str.tostring(issue68BreakOther), bgcolor=issue68BreakOther > 0 ? colRed : colNeutral, text_color=color.white)
        table.cell(t, 2, 14, str.tostring(f_issue68Pct(issue68BreakOther, issue68StrongBreaks), "#.1") + "%", bgcolor=issue68BreakOther > 0 ? colRed : colNeutral, text_color=color.white)
        table.cell(t, 3, 14, "Formal Bull acquire", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 4, 14, str.tostring(issue68FormalBullAcquire), bgcolor=issue68FormalBullAcquire > 0 ? colGreen : colRed, text_color=color.white)
        table.cell(t, 5, 14, "NO TUNING", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 15, "READ", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 15, "Red lane = gap fail", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 15, "Orange dot = streak break", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 15, "DISCOVERY", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 4, 15, "NO PNL", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 5, 15, "FROZEN C-2", bgcolor=colNeutral, text_color=color.white)
    else
        table.clear(t, 0, 0, 5, 19)
'''.strip()


def generate(source: Path) -> str:
    d1_text = phase_b.d1.generate(source)
    if d1_text.count(phase_b.D1_EXPORT_MARKER) != 1:
        raise RuntimeError("expected exactly one D1 parity export marker")
    core = d1_text.split(phase_b.D1_EXPORT_MARKER, 1)[0].rstrip()
    core = replace_once(core, phase_b.D1_INDICATOR_DECL, AUDIT_DECL)
    out = core + "\n\n" + BODY + "\n"

    required = (
        "TOP-Bull Runner-Up / Strong Streak-Break Attribution",
        "secondId",
        "topGapMin",
        "issue68RunnerGapFailCount",
        "TOP leaves Bull",
        "Formal Bull acquire",
        "NO TUNING",
    )
    for token in required:
        if token not in out:
            raise RuntimeError(f"missing runner-up audit token: {token}")

    forbidden = ("strategy.", "issue68B34A", "issue68B34B", "issue68B34C")
    for token in forbidden:
        if token in out:
            raise RuntimeError(f"forbidden token leaked into runner-up audit: {token}")
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=HERE / SOURCE_RELATIVE)
    parser.add_argument("--output", type=Path, default=HERE / "generated/wyckoff-issue68-cross-market-top-bull-runnerup-streak-break-audit.pine")
    args = parser.parse_args()
    text = generate(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
