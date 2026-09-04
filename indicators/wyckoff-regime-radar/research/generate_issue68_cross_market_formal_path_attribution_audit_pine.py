#!/usr/bin/env python3
"""Generate Issue #68 cross-market RAW→TOP→STRONG→FORMAL attribution Pine.

Discovery-only diagnostic. Reuses the frozen C-2 classifier lineage and adds no
classifier/lifecycle/strategy semantics.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_phase_b_lifecycle_pine as phase_b
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 Cross-Market Formal Path", shorttitle="ChaseRisk #68 PATH", overlay=false, precision=2)'

PATH_BODY = r'''

// ============================================================================
// Issue #68 Cross-Market Formal-Path Attribution — DISCOVERY ONLY.
// Frozen path: RAW -> TOP -> STRONG -> FORMAL.
// Shared 2022-01-03 -> 2023-12-29 Bull yield-regime window.
// NO PNL. NO TUNING. NO CLASSIFIER / CORE / EXPOSURE CHANGE.
// ============================================================================

groupIssue68Path = "Issue #68｜Cross-Market Formal Path"
showIssue68PathTable = input.bool(true, "顯示路徑統計表", group=groupIssue68Path)

issue68PathReady = bar_index >= rankLen - 1
int issue68PathStart = timestamp(2022, 1, 3, 0, 0)
int issue68PathEnd = timestamp(2023, 12, 29, 23, 59)
bool issue68PathInWindow = issue68PathReady and time >= issue68PathStart and time <= issue68PathEnd

f_issue68PathDir(int stage) => stage == 2 or stage == 3 ? 1 : stage == 5 or stage == 6 ? -1 : 0
f_issue68PathColor(int x) => x == 1 ? colGreen : x == -1 ? colRed : colNeutral
f_issue68PathText(int x) => x == 1 ? "BULL" : x == -1 ? "BEAR" : "NEUTRAL"

// Exact strict-greater RAW winner, preserving Stage1 -> Stage6 tie priority.
f_issue68PathRawWinner() =>
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
        v := redistRaw
        id := 6
    id

int issue68PathRawId = f_issue68PathRawWinner()
int issue68PathRaw = issue68PathReady ? f_issue68PathDir(issue68PathRawId) : 0
int issue68PathTop = issue68PathReady ? f_issue68PathDir(topId) : 0
int issue68PathStrong = issue68PathReady and strongCandidate ? issue68PathTop : 0
int issue68PathFormal = issue68PathReady ? f_issue68PathDir(formalId) : 0

// Discovery-window counters. These describe classifier semantics only.
var int issue68PathBars = 0
var int issue68PathFirstBar = na

var int issue68PathRawBull = 0
var int issue68PathRawBear = 0
var int issue68PathRawFirstBull = na
var int issue68PathRawNonBullRun = 0
var int issue68PathRawMaxNonBull = 0

var int issue68PathTopBull = 0
var int issue68PathTopBear = 0
var int issue68PathTopFirstBull = na
var int issue68PathTopNonBullRun = 0
var int issue68PathTopMaxNonBull = 0

var int issue68PathStrongBull = 0
var int issue68PathStrongBear = 0
var int issue68PathStrongFirstBull = na
var int issue68PathStrongNonBullRun = 0
var int issue68PathStrongMaxNonBull = 0

var int issue68PathFormalBull = 0
var int issue68PathFormalBear = 0
var int issue68PathFormalFirstBull = na
var int issue68PathFormalNonBullRun = 0
var int issue68PathFormalMaxNonBull = 0

if issue68PathInWindow
    if na(issue68PathFirstBar)
        issue68PathFirstBar := bar_index
    issue68PathBars += 1

    issue68PathRawBull += issue68PathRaw == 1 ? 1 : 0
    issue68PathRawBear += issue68PathRaw == -1 ? 1 : 0
    if issue68PathRaw == 1 and na(issue68PathRawFirstBull)
        issue68PathRawFirstBull := bar_index - issue68PathFirstBar
    if issue68PathRaw != 1
        issue68PathRawNonBullRun += 1
        issue68PathRawMaxNonBull := math.max(issue68PathRawMaxNonBull, issue68PathRawNonBullRun)
    else
        issue68PathRawNonBullRun := 0

    issue68PathTopBull += issue68PathTop == 1 ? 1 : 0
    issue68PathTopBear += issue68PathTop == -1 ? 1 : 0
    if issue68PathTop == 1 and na(issue68PathTopFirstBull)
        issue68PathTopFirstBull := bar_index - issue68PathFirstBar
    if issue68PathTop != 1
        issue68PathTopNonBullRun += 1
        issue68PathTopMaxNonBull := math.max(issue68PathTopMaxNonBull, issue68PathTopNonBullRun)
    else
        issue68PathTopNonBullRun := 0

    issue68PathStrongBull += issue68PathStrong == 1 ? 1 : 0
    issue68PathStrongBear += issue68PathStrong == -1 ? 1 : 0
    if issue68PathStrong == 1 and na(issue68PathStrongFirstBull)
        issue68PathStrongFirstBull := bar_index - issue68PathFirstBar
    if issue68PathStrong != 1
        issue68PathStrongNonBullRun += 1
        issue68PathStrongMaxNonBull := math.max(issue68PathStrongMaxNonBull, issue68PathStrongNonBullRun)
    else
        issue68PathStrongNonBullRun := 0

    issue68PathFormalBull += issue68PathFormal == 1 ? 1 : 0
    issue68PathFormalBear += issue68PathFormal == -1 ? 1 : 0
    if issue68PathFormal == 1 and na(issue68PathFormalFirstBull)
        issue68PathFormalFirstBull := bar_index - issue68PathFirstBar
    if issue68PathFormal != 1
        issue68PathFormalNonBullRun += 1
        issue68PathFormalMaxNonBull := math.max(issue68PathFormalMaxNonBull, issue68PathFormalNonBullRun)
    else
        issue68PathFormalNonBullRun := 0

float issue68PathRawBullPct = issue68PathBars > 0 ? 100.0 * issue68PathRawBull / issue68PathBars : na
float issue68PathRawBearPct = issue68PathBars > 0 ? 100.0 * issue68PathRawBear / issue68PathBars : na
float issue68PathTopBullPct = issue68PathBars > 0 ? 100.0 * issue68PathTopBull / issue68PathBars : na
float issue68PathTopBearPct = issue68PathBars > 0 ? 100.0 * issue68PathTopBear / issue68PathBars : na
float issue68PathStrongBullPct = issue68PathBars > 0 ? 100.0 * issue68PathStrongBull / issue68PathBars : na
float issue68PathStrongBearPct = issue68PathBars > 0 ? 100.0 * issue68PathStrongBear / issue68PathBars : na
float issue68PathFormalBullPct = issue68PathBars > 0 ? 100.0 * issue68PathFormalBull / issue68PathBars : na
float issue68PathFormalBearPct = issue68PathBars > 0 ? 100.0 * issue68PathFormalBear / issue68PathBars : na

// Minimal plot-safe stripes. Upper expected stripe is always Bull within window.
plot(issue68PathInWindow ? 5.0 : na, "EXPECTED Bull", color=colGreen, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68PathInWindow ? 4.0 : na, "RAW path", color=f_issue68PathColor(issue68PathRaw), linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68PathInWindow ? 3.0 : na, "TOP path", color=f_issue68PathColor(issue68PathTop), linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68PathInWindow ? 2.0 : na, "STRONG path", color=f_issue68PathColor(issue68PathStrong), linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68PathInWindow ? 1.0 : na, "FORMAL path", color=f_issue68PathColor(issue68PathFormal), linewidth=4, style=plot.style_linebr, display=display.pane)

var table issue68PathTable = table.new(position.bottom_right, 5, 7, border_width=1)
if barstate.islast
    if showIssue68PathTable
        table.cell(issue68PathTable, 0, 0, "FORMAL-PATH ATTRIB", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68PathTable, 1, 0, syminfo.ticker, bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68PathTable, 2, 0, "2022-2023 BULL", bgcolor=colGreen, text_color=color.white)
        table.cell(issue68PathTable, 3, 0, "DISCOVERY", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68PathTable, 4, 0, str.tostring(issue68PathBars) + " bars", bgcolor=colNeutral, text_color=color.white)

        table.cell(issue68PathTable, 0, 1, "LAYER", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68PathTable, 1, 1, "BULL %", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68PathTable, 2, 1, "BEAR %", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68PathTable, 3, 1, "FIRST BULL", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68PathTable, 4, 1, "MAX NON-BULL", bgcolor=colNeutral, text_color=color.white)

        table.cell(issue68PathTable, 0, 2, "RAW", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68PathTable, 1, 2, str.tostring(issue68PathRawBullPct, "#.0") + "%", bgcolor=colGreen, text_color=color.white)
        table.cell(issue68PathTable, 2, 2, str.tostring(issue68PathRawBearPct, "#.0") + "%", bgcolor=colRed, text_color=color.white)
        table.cell(issue68PathTable, 3, 2, na(issue68PathRawFirstBull) ? "NEVER" : str.tostring(issue68PathRawFirstBull), bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68PathTable, 4, 2, str.tostring(issue68PathRawMaxNonBull), bgcolor=colNeutral, text_color=color.white)

        table.cell(issue68PathTable, 0, 3, "TOP", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68PathTable, 1, 3, str.tostring(issue68PathTopBullPct, "#.0") + "%", bgcolor=colGreen, text_color=color.white)
        table.cell(issue68PathTable, 2, 3, str.tostring(issue68PathTopBearPct, "#.0") + "%", bgcolor=colRed, text_color=color.white)
        table.cell(issue68PathTable, 3, 3, na(issue68PathTopFirstBull) ? "NEVER" : str.tostring(issue68PathTopFirstBull), bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68PathTable, 4, 3, str.tostring(issue68PathTopMaxNonBull), bgcolor=colNeutral, text_color=color.white)

        table.cell(issue68PathTable, 0, 4, "STRONG", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68PathTable, 1, 4, str.tostring(issue68PathStrongBullPct, "#.0") + "%", bgcolor=colGreen, text_color=color.white)
        table.cell(issue68PathTable, 2, 4, str.tostring(issue68PathStrongBearPct, "#.0") + "%", bgcolor=colRed, text_color=color.white)
        table.cell(issue68PathTable, 3, 4, na(issue68PathStrongFirstBull) ? "NEVER" : str.tostring(issue68PathStrongFirstBull), bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68PathTable, 4, 4, str.tostring(issue68PathStrongMaxNonBull), bgcolor=colNeutral, text_color=color.white)

        table.cell(issue68PathTable, 0, 5, "FORMAL", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68PathTable, 1, 5, str.tostring(issue68PathFormalBullPct, "#.0") + "%", bgcolor=colGreen, text_color=color.white)
        table.cell(issue68PathTable, 2, 5, str.tostring(issue68PathFormalBearPct, "#.0") + "%", bgcolor=colRed, text_color=color.white)
        table.cell(issue68PathTable, 3, 5, na(issue68PathFormalFirstBull) ? "NEVER" : str.tostring(issue68PathFormalFirstBull), bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68PathTable, 4, 5, str.tostring(issue68PathFormalMaxNonBull), bgcolor=colNeutral, text_color=color.white)

        table.cell(issue68PathTable, 0, 6, "NOW", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68PathTable, 1, 6, "RAW " + f_issue68PathText(issue68PathRaw), bgcolor=f_issue68PathColor(issue68PathRaw), text_color=color.white)
        table.cell(issue68PathTable, 2, 6, "TOP " + f_issue68PathText(issue68PathTop), bgcolor=f_issue68PathColor(issue68PathTop), text_color=color.white)
        table.cell(issue68PathTable, 3, 6, "STR " + f_issue68PathText(issue68PathStrong), bgcolor=f_issue68PathColor(issue68PathStrong), text_color=color.white)
        table.cell(issue68PathTable, 4, 6, "FORM " + f_issue68PathText(issue68PathFormal), bgcolor=f_issue68PathColor(issue68PathFormal), text_color=color.white)
    else
        table.clear(issue68PathTable, 0, 0, 4, 6)
'''.strip()


def generate(source: Path) -> str:
    d1_text = phase_b.d1.generate(source)
    if d1_text.count(phase_b.D1_EXPORT_MARKER) != 1:
        raise RuntimeError("expected exactly one D1 parity export marker")
    core = d1_text.split(phase_b.D1_EXPORT_MARKER, 1)[0].rstrip()
    core = replace_once(core, phase_b.D1_INDICATOR_DECL, AUDIT_DECL)
    out = core + "\n\n" + PATH_BODY + "\n"

    required = (
        "Cross-Market Formal-Path Attribution",
        "f_issue68PathRawWinner",
        "accRaw",
        "markupRaw",
        "reaccRaw",
        "distRaw",
        "markdownRaw",
        "redistRaw",
        "topId",
        "strongCandidate",
        "formalId",
        "RAW path",
        "TOP path",
        "STRONG path",
        "FORMAL path",
        "MAX NON-BULL",
    )
    for token in required:
        if token not in out:
            raise RuntimeError(f"missing cross-market path token: {token}")

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
            raise RuntimeError(f"forbidden strategy/Exposure token leaked into path audit: {token}")

    # Keep the new diagnostic itself extremely small; the frozen upstream script
    # already has its own rendering. Five added plots leave a large safety margin.
    if PATH_BODY.count("plot(") != 5:
        raise RuntimeError("cross-market path audit must add exactly five plots")
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
