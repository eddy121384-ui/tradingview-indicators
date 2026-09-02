#!/usr/bin/env python3
"""Generate Issue #68 Core Semantic Validity Gate TradingView audit Pine.

This is a display/measurement wrapper around the frozen B3.4/B3.3 Core Bias
implementation. It does not modify C-2, B3.3 Core memory, Exposure semantics, or
any classifier parameter.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_phase_b34_exposure_bakeoff_audit_pine as b34
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent

OLD_DECL = b34.AUDIT_DECL
NEW_DECL = 'indicator("Chase Risk Radar｜Issue #68 Core Semantic Validity", shorttitle="ChaseRisk #68 CORE-GATE", overlay=false, precision=2)'

REPLACEMENTS = (
    (
        'showIssue68B34A = input.bool(true, "顯示 A｜Formal trend-family", group=groupIssue68B34)',
        'showIssue68B34A = input.bool(false, "顯示 A｜Formal trend-family（Core Gate 預設隱藏）", group=groupIssue68B34)',
    ),
    (
        'showIssue68B34B = input.bool(true, "顯示 B｜Flat Action authorization", group=groupIssue68B34)',
        'showIssue68B34B = input.bool(false, "顯示 B｜Flat Action authorization（Core Gate 預設隱藏）", group=groupIssue68B34)',
    ),
    (
        'showIssue68B34C = input.bool(true, "顯示 C｜Flat Action + Pace stateful", group=groupIssue68B34)',
        'showIssue68B34C = input.bool(false, "顯示 C｜Flat Action + Pace stateful（Core Gate 預設隱藏）", group=groupIssue68B34)',
    ),
    (
        'showIssue68B34Legend = input.bool(true, "顯示右上角狀態表", group=groupIssue68B34)',
        'showIssue68B34Legend = input.bool(false, "顯示舊 B3.4 狀態表（Core Gate 預設隱藏）", group=groupIssue68B34)',
    ),
)

CORE_GATE_BODY = r'''

// ============================================================================
// Issue #68 Core Semantic Validity Gate.
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
showIssue68CoreGateWindowBg = input.bool(true, "顯示固定窗口淡色背景", group=groupIssue68CoreGate)
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

// Expected regime band: visible only inside the preregistered window.
float issue68CoreGateExpectedCenter = 2.0
float issue68CoreGateExpectedHalf = 0.34
issue68CoreGateExpectedTop = plot(issue68CoreGateInWindow ? issue68CoreGateExpectedCenter + issue68CoreGateExpectedHalf : na, "CORE-GATE expected top", color=color.new(colNeutral, 100), display=display.pane)
issue68CoreGateExpectedBottom = plot(issue68CoreGateInWindow ? issue68CoreGateExpectedCenter - issue68CoreGateExpectedHalf : na, "CORE-GATE expected bottom", color=color.new(colNeutral, 100), display=display.pane)
fill(issue68CoreGateExpectedTop, issue68CoreGateExpectedBottom, color=issue68CoreGateInWindow ? color.new(issue68CoreGateExpected == 1 ? colGreen : colRed, 18) : na, title="EXPECTED major regime")

bgcolor(showIssue68CoreGateWindowBg and issue68CoreGateInWindow ? color.new(issue68CoreGateExpected == 1 ? colGreen : colRed, 96) : na, title="CORE-GATE fixed semantic window")
plotshape(showIssue68CoreGateMismatch and issue68CoreGateOpposite ? 1.0 : na, "CORE opposite expected", style=shape.circle, location=location.absolute, color=colRed, size=size.tiny)

plot(issue68CoreGateBars, "CORE-GATE bars", color=color.new(colNeutral, 100), display=display.data_window)
plot(issue68CoreGateAlignedPct, "CORE-GATE aligned pct", color=color.new(colGreen, 100), display=display.data_window)
plot(issue68CoreGateOppositePct, "CORE-GATE opposite pct", color=color.new(colRed, 100), display=display.data_window)
plot(issue68CoreGateNeutralPct, "CORE-GATE neutral pct", color=color.new(colNeutral, 100), display=display.data_window)
plot(issue68CoreGateFirstAlignDelay, "CORE-GATE first align delay bars", color=color.new(colNeutral, 100), display=display.data_window)
plot(issue68CoreGateMaxOppRun, "CORE-GATE longest opposite run", color=color.new(colRed, 100), display=display.data_window)
plot(issue68CoreGateTransitions, "CORE-GATE Core transitions", color=color.new(colNeutral, 100), display=display.data_window)

var table issue68CoreGateTable = table.new(position.bottom_right, 2, 10, border_width=1)
if barstate.islast and showIssue68CoreGateTable
    color issue68CoreGateStatusColor = issue68CoreGateHardFail ? colRed : colGreen
    table.cell(issue68CoreGateTable, 0, 0, "CORE SEMANTIC GATE", bgcolor=colNeutral, text_color=color.white)
    table.cell(issue68CoreGateTable, 1, 0, issue68CoreGateStatus, bgcolor=issue68CoreGateStatusColor, text_color=color.white)
    table.cell(issue68CoreGateTable, 0, 1, "Preset", bgcolor=colNeutral, text_color=color.white)
    table.cell(issue68CoreGateTable, 1, 1, issue68CoreGateLabel, bgcolor=colNeutral, text_color=color.white)
    table.cell(issue68CoreGateTable, 0, 2, "Role / Chart", bgcolor=colNeutral, text_color=color.white)
    table.cell(issue68CoreGateTable, 1, 2, issue68CoreGateRole + " / " + syminfo.ticker, bgcolor=colNeutral, text_color=color.white)
    table.cell(issue68CoreGateTable, 0, 3, "Expected", bgcolor=colNeutral, text_color=color.white)
    table.cell(issue68CoreGateTable, 1, 3, issue68CoreGateExpected == 1 ? "BULL / GREEN" : "BEAR / RED", bgcolor=issue68CoreGateExpected == 1 ? colGreen : colRed, text_color=color.white)
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
'''


def generate(source: Path) -> str:
    out = b34.generate(source)
    out = replace_once(out, OLD_DECL, NEW_DECL)
    for old, new in REPLACEMENTS:
        out = replace_once(out, old, new)

    banner_marker = 'groupIssue68B34 = "Issue #68｜Exposure B3.4 Bakeoff"'
    banner = """// ============================================================================
// Issue #68 Core Semantic Validity Gate wrapper.
// Exposure lanes remain mechanically present but are hidden by default.
// The gate judges frozen B3.3 Core only; no classifier or lifecycle semantics change.
// ============================================================================
""".strip()
    out = replace_once(out, banner_marker, banner + "\n\n" + banner_marker)
    out = out.rstrip() + "\n" + CORE_GATE_BODY + "\n"

    required = (
        "Issue #68 Core Semantic Validity Gate",
        "FR10Y｜2022-2023 Bull｜DISCOVERY",
        "JGB10Y｜2022-2024 Bull｜VALIDATION",
        "US10Y｜2020-2023 Bull｜VALIDATION",
        "EURUSD｜2021-2022 Bear｜VALIDATION",
        "SPX｜2022 Bear｜VALIDATION",
        "issue68CoreGateOppositePct > 50.0",
        "issue68CoreGateMaxOppRun > 63",
        "EXPECTED major regime",
        "CORE opposite expected",
        'showIssue68B34A = input.bool(false',
        'showIssue68B34B = input.bool(false',
        'showIssue68B34C = input.bool(false',
        'showIssue68B34Legend = input.bool(false',
    )
    for token in required:
        if token not in out:
            raise RuntimeError(f"missing Core semantic gate token: {token}")

    forbidden = (
        "strategy.",
        "issue68ArmedDir",
        "issue68EarlyFail",
        "LONG SETUP",
        "SHORT SETUP",
    )
    for token in forbidden:
        if token in out:
            raise RuntimeError(f"forbidden strategy/lifecycle token leaked into Core semantic gate: {token}")

    # Keep margin below TradingView's 64 plot-count budget. `plotshape` is also a plot count.
    estimated_plot_calls = out.count("plot(") + out.count("plotshape(") + out.count("bgcolor(")
    if estimated_plot_calls > 58:
        raise RuntimeError(f"Core semantic gate estimated plot budget too high: {estimated_plot_calls}")
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
