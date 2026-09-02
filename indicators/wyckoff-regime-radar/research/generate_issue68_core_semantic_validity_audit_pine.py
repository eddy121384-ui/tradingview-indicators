#!/usr/bin/env python3
"""Generate Issue #68 Core Semantic Validity Gate TradingView audit Pine.

This generator reuses the frozen B3.3 Core computation from the B3.4 lineage but
*does not* carry the B3.4 Exposure rendering/counters into the audit artifact.
That matters because hidden Pine plots still consume TradingView's 64-plot budget.

No C-2, B3.3 Core-memory, Exposure, or classifier parameter semantics are changed.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_phase_b34_exposure_bakeoff_audit_pine as b34
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent

OLD_DECL = b34.AUDIT_DECL
NEW_DECL = 'indicator("Chase Risk Radar｜Issue #68 Core Semantic Validity", shorttitle="ChaseRisk #68 CORE-GATE", overlay=false, precision=2)'

# Everything from Candidate A onward is Exposure/rendering material. B3.3 Core is
# fully computed immediately before this marker, so trimming here preserves Core
# semantics while removing A/B/C plots, fills, plotshapes, legends and data-window
# counters that are irrelevant to the Core validity gate.
B34_EXPOSURE_CUT_MARKER = "// --- Candidate A: Formal trend-family exposure ---"

CORE_GATE_BODY = r'''

// ============================================================================
// Issue #68 Core Semantic Validity Gate — CORE ONLY.
// NO-PNL. NO TUNING. Frozen B3.3 Core Bias only.
// FR10Y is discovery/burned. Other presets are preregistered validation windows.
// ============================================================================

groupIssue68CoreGate = "Issue #68｜Core Semantic Validity Gate"
issue68CoreGatePreset = input.string(
     "FR10Y｜2022-2023 Bull｜DISCOVERY",
     "固定語意窗口",
     options=[
         "FR10Y｜2022-2023 Bull｜DISCOVERY",
         "JGB10Y｜2022-2024 Bull｜VALIDATION",
         "US10Y｜2020-2023 Bull｜VALIDATION",
         "EURUSD｜2021-2022 Bear｜VALIDATION",
         "SPX｜2020-2021 Bull｜VALIDATION",
         "SPX｜2022 Bear｜VALIDATION"
     ],
     group=groupIssue68CoreGate)
showIssue68CoreGateMismatch = input.bool(true, "顯示 Core 反向紅點", group=groupIssue68CoreGate)
showIssue68CoreGateTable = input.bool(true, "顯示語意統計表", group=groupIssue68CoreGate)

int issue68CoreGateStart = na
int issue68CoreGateEnd = na
int issue68CoreGateExpected = 0
string issue68CoreGateRole = ""
string issue68CoreGateLabel = ""

if issue68CoreGatePreset == "FR10Y｜2022-2023 Bull｜DISCOVERY"
    issue68CoreGateStart := timestamp(2022, 1, 3, 0, 0)
    issue68CoreGateEnd := timestamp(2023, 12, 29, 23, 59)
    issue68CoreGateExpected := 1
    issue68CoreGateRole := "DISCOVERY"
    issue68CoreGateLabel := "FR10Y 2022-2023 Bull"
else if issue68CoreGatePreset == "JGB10Y｜2022-2024 Bull｜VALIDATION"
    issue68CoreGateStart := timestamp(2022, 1, 4, 0, 0)
    issue68CoreGateEnd := timestamp(2024, 12, 30, 23, 59)
    issue68CoreGateExpected := 1
    issue68CoreGateRole := "VALIDATION"
    issue68CoreGateLabel := "JGB10Y 2022-2024 Bull"
else if issue68CoreGatePreset == "US10Y｜2020-2023 Bull｜VALIDATION"
    issue68CoreGateStart := timestamp(2020, 8, 4, 0, 0)
    issue68CoreGateEnd := timestamp(2023, 10, 19, 23, 59)
    issue68CoreGateExpected := 1
    issue68CoreGateRole := "VALIDATION"
    issue68CoreGateLabel := "US10Y 2020-2023 Bull"
else if issue68CoreGatePreset == "EURUSD｜2021-2022 Bear｜VALIDATION"
    issue68CoreGateStart := timestamp(2021, 6, 1, 0, 0)
    issue68CoreGateEnd := timestamp(2022, 9, 28, 23, 59)
    issue68CoreGateExpected := -1
    issue68CoreGateRole := "VALIDATION"
    issue68CoreGateLabel := "EURUSD 2021-2022 Bear"
else if issue68CoreGatePreset == "SPX｜2020-2021 Bull｜VALIDATION"
    issue68CoreGateStart := timestamp(2020, 4, 1, 0, 0)
    issue68CoreGateEnd := timestamp(2021, 12, 31, 23, 59)
    issue68CoreGateExpected := 1
    issue68CoreGateRole := "VALIDATION"
    issue68CoreGateLabel := "SPX 2020-2021 Bull"
else
    issue68CoreGateStart := timestamp(2022, 1, 3, 0, 0)
    issue68CoreGateEnd := timestamp(2022, 10, 12, 23, 59)
    issue68CoreGateExpected := -1
    issue68CoreGateRole := "VALIDATION"
    issue68CoreGateLabel := "SPX 2022 Bear"

bool issue68CoreGateInWindow = issue68B34Ready and time >= issue68CoreGateStart and time <= issue68CoreGateEnd
bool issue68CoreGateAligned = issue68CoreGateInWindow and issue68B34Bias == issue68CoreGateExpected
bool issue68CoreGateOpposite = issue68CoreGateInWindow and issue68B34Bias == -issue68CoreGateExpected
bool issue68CoreGateNeutral = issue68CoreGateInWindow and issue68B34Bias == 0

var int issue68CoreGateBars = 0
var int issue68CoreGateAlignedBars = 0
var int issue68CoreGateOppositeBars = 0
var int issue68CoreGateNeutralBars = 0
var int issue68CoreGateFirstWindowBar = na
var int issue68CoreGateFirstAlignDelay = na
var int issue68CoreGateOppRun = 0
var int issue68CoreGateMaxOppRun = 0
var int issue68CoreGateTransitions = 0

if issue68CoreGateInWindow
    if na(issue68CoreGateFirstWindowBar)
        issue68CoreGateFirstWindowBar := bar_index
    issue68CoreGateBars += 1
    issue68CoreGateAlignedBars += issue68CoreGateAligned ? 1 : 0
    issue68CoreGateOppositeBars += issue68CoreGateOpposite ? 1 : 0
    issue68CoreGateNeutralBars += issue68CoreGateNeutral ? 1 : 0
    if issue68CoreGateAligned and na(issue68CoreGateFirstAlignDelay)
        issue68CoreGateFirstAlignDelay := bar_index - issue68CoreGateFirstWindowBar
    if issue68CoreGateOpposite
        issue68CoreGateOppRun += 1
        issue68CoreGateMaxOppRun := math.max(issue68CoreGateMaxOppRun, issue68CoreGateOppRun)
    else
        issue68CoreGateOppRun := 0
    if issue68CoreGateInWindow[1] and issue68B34Bias != issue68B34Bias[1]
        issue68CoreGateTransitions += 1

float issue68CoreGateAlignedPct = issue68CoreGateBars > 0 ? 100.0 * issue68CoreGateAlignedBars / issue68CoreGateBars : na
float issue68CoreGateOppositePct = issue68CoreGateBars > 0 ? 100.0 * issue68CoreGateOppositeBars / issue68CoreGateBars : na
float issue68CoreGateNeutralPct = issue68CoreGateBars > 0 ? 100.0 * issue68CoreGateNeutralBars / issue68CoreGateBars : na
bool issue68CoreGateHardFail = issue68CoreGateBars > 0 and (issue68CoreGateOppositePct > 50.0 or issue68CoreGateMaxOppRun > 63)
string issue68CoreGateStatus = issue68CoreGateRole == "DISCOVERY" ? (issue68CoreGateHardFail ? "DISCOVERY FAIL" : "DISCOVERY") : (issue68CoreGateHardFail ? "FAIL" : "PASS")

// Minimal plot-budget-safe visualization.
// EXPECTED is the upper stripe; CORE is the lower stripe. Dynamic color carries
// the semantic state, while fixed y-levels are layout coordinates only.
color issue68CoreGateExpectedColor = issue68CoreGateExpected == 1 ? colGreen : colRed
color issue68CoreGateCoreColor = issue68B34Bias == 1 ? colGreen : issue68B34Bias == -1 ? colRed : colNeutral
plot(issue68CoreGateInWindow ? 2.0 : na, "EXPECTED major regime", color=issue68CoreGateExpectedColor, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68CoreGateInWindow ? 1.0 : na, "CORE frozen B3.3", color=issue68CoreGateCoreColor, linewidth=4, style=plot.style_linebr, display=display.pane)
plotshape(showIssue68CoreGateMismatch and issue68CoreGateOpposite ? 0.0 : na, "CORE opposite expected", style=shape.circle, location=location.absolute, color=colRed, size=size.tiny)

// Table replaces seven Data Window plots; tables do not consume plot counts.
var table issue68CoreGateTable = table.new(position.bottom_right, 2, 10, border_width=1)
if barstate.islast
    if showIssue68CoreGateTable
        color issue68CoreGateStatusColor = issue68CoreGateHardFail ? colRed : colGreen
        table.cell(issue68CoreGateTable, 0, 0, "CORE SEMANTIC GATE", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68CoreGateTable, 1, 0, issue68CoreGateStatus, bgcolor=issue68CoreGateStatusColor, text_color=color.white)
        table.cell(issue68CoreGateTable, 0, 1, "Preset", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68CoreGateTable, 1, 1, issue68CoreGateLabel, bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68CoreGateTable, 0, 2, "Role / Chart", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68CoreGateTable, 1, 2, issue68CoreGateRole + " / " + syminfo.ticker, bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68CoreGateTable, 0, 3, "Expected", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68CoreGateTable, 1, 3, issue68CoreGateExpected == 1 ? "BULL / GREEN" : "BEAR / RED", bgcolor=issue68CoreGateExpectedColor, text_color=color.white)
        table.cell(issue68CoreGateTable, 0, 4, "Bars", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68CoreGateTable, 1, 4, str.tostring(issue68CoreGateBars), bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68CoreGateTable, 0, 5, "Aligned", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68CoreGateTable, 1, 5, str.tostring(issue68CoreGateAlignedPct, "#.0") + "%", bgcolor=colGreen, text_color=color.white)
        table.cell(issue68CoreGateTable, 0, 6, "Opposite", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68CoreGateTable, 1, 6, str.tostring(issue68CoreGateOppositePct, "#.0") + "%", bgcolor=issue68CoreGateOppositePct > 50.0 ? colRed : colNeutral, text_color=color.white)
        table.cell(issue68CoreGateTable, 0, 7, "First align delay", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68CoreGateTable, 1, 7, na(issue68CoreGateFirstAlignDelay) ? "NEVER" : str.tostring(issue68CoreGateFirstAlignDelay) + " bars", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68CoreGateTable, 0, 8, "Longest opposite", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68CoreGateTable, 1, 8, str.tostring(issue68CoreGateMaxOppRun) + " bars", bgcolor=issue68CoreGateMaxOppRun > 63 ? colRed : colNeutral, text_color=color.white)
        table.cell(issue68CoreGateTable, 0, 9, "Hard fail rule", bgcolor=colNeutral, text_color=color.white)
        table.cell(issue68CoreGateTable, 1, 9, ">50% opp OR >63 run", bgcolor=colNeutral, text_color=color.white)
    else
        table.clear(issue68CoreGateTable, 0, 0, 1, 9)
'''


def generate(source: Path) -> str:
    out = b34.generate(source)
    out = replace_once(out, OLD_DECL, NEW_DECL)

    cut_at = out.find(B34_EXPOSURE_CUT_MARKER)
    if cut_at < 0:
        raise RuntimeError("could not locate B3.4 Exposure cut marker")

    # Preserve the complete upstream classifier + B3.3 Core computation, then
    # discard every Exposure/rendering statement after it.
    out = out[:cut_at].rstrip() + "\n" + CORE_GATE_BODY + "\n"

    required = (
        "Issue #68 Core Semantic Validity Gate — CORE ONLY",
        "// --- Frozen B3.3 Core Bias Memory ---",
        "FR10Y｜2022-2023 Bull｜DISCOVERY",
        "JGB10Y｜2022-2024 Bull｜VALIDATION",
        "US10Y｜2020-2023 Bull｜VALIDATION",
        "EURUSD｜2021-2022 Bear｜VALIDATION",
        "SPX｜2020-2021 Bull｜VALIDATION",
        "SPX｜2022 Bear｜VALIDATION",
        "issue68CoreGateOppositePct > 50.0",
        "issue68CoreGateMaxOppRun > 63",
        "EXPECTED major regime",
        "CORE frozen B3.3",
        "CORE opposite expected",
    )
    for token in required:
        if token not in out:
            raise RuntimeError(f"missing Core semantic gate token: {token}")

    forbidden = (
        "strategy.",
        "// --- Candidate A:",
        "// --- Candidate B:",
        "// --- Candidate C:",
        "B34 Exposure A",
        "B34 Exposure B",
        "B34 Exposure C",
        "B34 A transitions",
        "B34 B transitions",
        "B34 C transitions",
        "issue68ArmedDir",
        "issue68EarlyFail",
        "LONG SETUP",
        "SHORT SETUP",
    )
    for token in forbidden:
        if token in out:
            raise RuntimeError(f"forbidden Exposure/lifecycle token leaked into Core semantic gate: {token}")

    # Conservative source-level safety guard. TradingView can charge extra plot
    # counts for dynamic series/colors, so keep the literal call count far below 64.
    literal_plot_calls = (
        out.count("plot(")
        + out.count("plotshape(")
        + out.count("plotchar(")
        + out.count("bgcolor(")
        + out.count("fill(")
        + out.count("barcolor(")
    )
    if literal_plot_calls > 42:
        raise RuntimeError(f"Core semantic gate literal plot-call budget too high: {literal_plot_calls}")
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
