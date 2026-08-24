#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "pine" / "issue-61-v06-core-visual-source.pine"
OUTPUT = HERE / "generated" / "wyckoff-issue-61-stage-lifecycle-strategy-preview.pine"
CUT_MARKER = "// v0.3.8 Dashboard Label Semantics Layer"
OLD_DECL_PREFIX = 'indicator("Chase Risk Radar v0.6｜Transition Health Preview"'

STRATEGY_DECL = '''strategy("Chase Risk Radar v0.6｜Stage Lifecycle Strategy Preview", shorttitle="ChaseRisk v0.6 STRAT", overlay=true, precision=5, pyramiding=0, default_qty_type=strategy.fixed, default_qty_value=1, commission_type=strategy.commission.percent, commission_value=0.02, process_orders_on_close=true, max_labels_count=500, max_lines_count=500)'''

STRATEGY_BLOCK = r'''

// ============================================================================
// Issue #61 Stage-aware Position Lifecycle — TradingView visual audit strategy
// This block mirrors the frozen Python research semantics. It is intentionally
// NOT an optimized production strategy. Use it to inspect where the research
// engine really enters, exits, arms, fails, and stays flat.
// Clean-review defaults keep diagnostic clutter off; turn layers on only when
// investigating a specific trade.
// ============================================================================

groupIssue61 = "Issue #61｜Strategy Preview"
showIssue61StageBg = input.bool(true, "顯示 Formal Stage 背景", group=groupIssue61)
showIssue61FreshBreaks = input.bool(false, "顯示 fresh breakout / breakdown", group=groupIssue61)
showIssue61Arms = input.bool(false, "顯示 ARM 等待確認", group=groupIssue61)
showIssue61TradeMarks = input.bool(false, "顯示額外進出場原因標記", group=groupIssue61)
showIssue61Protection = input.bool(false, "顯示前三根突破失效保護線", group=groupIssue61)

issue61Ready = bar_index >= rankLen - 1

// ----- Frozen base lifecycle --------------------------------------------------
var int issue61BasePos = 0
var int issue61ArmedDir = 0
var int issue61ArmedAt = na
var float issue61ArmedLevel = na

bool issue61ArmLong = false
bool issue61ArmShort = false
bool issue61BaseEntryLong = false
bool issue61BaseEntryShort = false
bool issue61BaseExitLong = false
bool issue61BaseExitShort = false
float issue61BaseNewEntryAnchor = na

int issue61BaseBefore = issue61BasePos

if issue61Ready
    int issue61Stage = formalId

    if issue61BasePos == 1 and not (issue61Stage == 2 or issue61Stage == 3)
        issue61BasePos := 0
        issue61BaseExitLong := true
    else if issue61BasePos == -1 and not (issue61Stage == 5 or issue61Stage == 6)
        issue61BasePos := 0
        issue61BaseExitShort := true

    if issue61ArmedDir != 0
        int issue61ArmAge = bar_index - issue61ArmedAt
        int issue61Target = issue61ArmedDir == 1 ? 2 : 5
        int issue61Precursor = issue61ArmedDir == 1 ? 1 : 4
        if issue61ArmAge <= confirmBars and issue61Stage == issue61Target
            if issue61BasePos == 0
                issue61BasePos := issue61ArmedDir
                issue61BaseNewEntryAnchor := issue61ArmedLevel
                issue61BaseEntryLong := issue61ArmedDir == 1
                issue61BaseEntryShort := issue61ArmedDir == -1
            issue61ArmedDir := 0
            issue61ArmedAt := na
            issue61ArmedLevel := na
        else if issue61ArmAge > confirmBars or not (issue61Stage == issue61Precursor or issue61Stage == issue61Target)
            issue61ArmedDir := 0
            issue61ArmedAt := na
            issue61ArmedLevel := na

    if issue61BasePos == 0
        if rangeBreakUp and issue61Stage == 2
            issue61BasePos := 1
            issue61BaseNewEntryAnchor := rangeHighBreak
            issue61BaseEntryLong := true
            issue61ArmedDir := 0
            issue61ArmedAt := na
            issue61ArmedLevel := na
        else if rangeBreakDn and issue61Stage == 5
            issue61BasePos := -1
            issue61BaseNewEntryAnchor := rangeLowBreak
            issue61BaseEntryShort := true
            issue61ArmedDir := 0
            issue61ArmedAt := na
            issue61ArmedLevel := na
        else if rangeBreakUp and issue61Stage == 1
            issue61ArmedDir := 1
            issue61ArmedAt := bar_index
            issue61ArmedLevel := rangeHighBreak
            issue61ArmLong := true
        else if rangeBreakDn and issue61Stage == 4
            issue61ArmedDir := -1
            issue61ArmedAt := bar_index
            issue61ArmedLevel := rangeLowBreak
            issue61ArmShort := true
else
    issue61BasePos := 0
    issue61ArmedDir := 0
    issue61ArmedAt := na
    issue61ArmedLevel := na

// ----- Frozen Phase-E early breakout invalidation overlay -------------------
var int issue61ManagedPos = 0
var float issue61EntryLevel = na
var int issue61EntryAge = -1
var int issue61StoppedDir = 0
var int issue61PrevBasePos = 0

bool issue61ManagedEntryLong = false
bool issue61ManagedEntryShort = false
bool issue61ReentryLong = false
bool issue61ReentryShort = false
bool issue61EarlyFailLong = false
bool issue61EarlyFailShort = false
bool issue61RegimeExitLong = false
bool issue61RegimeExitShort = false

int issue61ManagedBefore = issue61ManagedPos

if issue61Ready
    int issue61BaseDir = issue61BasePos

    if issue61BaseDir != issue61PrevBasePos
        issue61StoppedDir := 0
        if issue61BaseDir == 0
            issue61RegimeExitLong := issue61ManagedBefore == 1
            issue61RegimeExitShort := issue61ManagedBefore == -1
            issue61ManagedPos := 0
            issue61EntryLevel := na
            issue61EntryAge := -1
        else
            issue61ManagedPos := issue61BaseDir
            issue61EntryLevel := issue61BaseNewEntryAnchor
            issue61EntryAge := 0
            issue61ManagedEntryLong := issue61BaseDir == 1
            issue61ManagedEntryShort := issue61BaseDir == -1
    else if issue61BaseDir != 0 and issue61StoppedDir == issue61BaseDir
        bool issue61MatchingFresh = (issue61BaseDir == 1 and formalId == 2 and rangeBreakUp) or (issue61BaseDir == -1 and formalId == 5 and rangeBreakDn)
        if issue61MatchingFresh
            issue61ManagedPos := issue61BaseDir
            issue61StoppedDir := 0
            issue61EntryLevel := issue61BaseDir == 1 ? rangeHighBreak : rangeLowBreak
            issue61EntryAge := 0
            issue61ReentryLong := issue61BaseDir == 1
            issue61ReentryShort := issue61BaseDir == -1
        else
            issue61ManagedPos := 0
    else if issue61BaseDir == 0
        issue61ManagedPos := 0
        issue61EntryLevel := na
        issue61EntryAge := -1
        issue61StoppedDir := 0

    bool issue61WasHolding = issue61ManagedBefore == issue61ManagedPos and issue61ManagedPos != 0
    if issue61WasHolding and not na(issue61EntryLevel)
        issue61EntryAge += 1
        if issue61EntryAge <= confirmBars
            bool issue61Invalidated = (issue61ManagedPos == 1 and close <= issue61EntryLevel) or (issue61ManagedPos == -1 and close >= issue61EntryLevel)
            if issue61Invalidated
                issue61StoppedDir := issue61ManagedPos
                issue61EarlyFailLong := issue61ManagedPos == 1
                issue61EarlyFailShort := issue61ManagedPos == -1
                issue61ManagedPos := 0
                issue61EntryLevel := na
                issue61EntryAge := -1
        else
            issue61EntryLevel := na
            issue61EntryAge := -1

    issue61PrevBasePos := issue61BaseDir
else
    issue61ManagedPos := 0
    issue61EntryLevel := na
    issue61EntryAge := -1
    issue61StoppedDir := 0
    issue61PrevBasePos := 0

// ----- Real TradingView orders ----------------------------------------------
if issue61Ready
    if issue61ManagedBefore == 1 and issue61ManagedPos != 1
        strategy.close("Long", comment=issue61EarlyFailLong ? "EARLY FAIL" : "REGIME EXIT")
    if issue61ManagedBefore == -1 and issue61ManagedPos != -1
        strategy.close("Short", comment=issue61EarlyFailShort ? "EARLY FAIL" : "REGIME EXIT")
    if issue61ManagedPos == 1 and issue61ManagedBefore != 1
        strategy.entry("Long", strategy.long, comment=issue61ReentryLong ? "RE-LONG" : "LONG")
    if issue61ManagedPos == -1 and issue61ManagedBefore != -1
        strategy.entry("Short", strategy.short, comment=issue61ReentryShort ? "RE-SHORT" : "SHORT")

// ----- Visual audit layer ----------------------------------------------------
color issue61StageColor = formalId == 1 ? colAcc : formalId == 2 ? colMarkup : formalId == 3 ? colReacc : formalId == 4 ? colDist : formalId == 5 ? colMarkdown : formalId == 6 ? colRedist : colNeutral
bgcolor(showIssue61StageBg and issue61Ready ? color.new(issue61StageColor, 88) : na, title="Issue61 Formal Stage")

plot(showIssue61FreshBreaks ? rangeHighBreak : na, "20-bar prior high", color=color.new(colBreakout, 72), linewidth=1, style=plot.style_linebr)
plot(showIssue61FreshBreaks ? rangeLowBreak : na, "20-bar prior low", color=color.new(colBreakdown, 72), linewidth=1, style=plot.style_linebr)
plot(showIssue61Protection and not na(issue61EntryLevel) ? issue61EntryLevel : na, "Early invalidation level", color=color.new(colOrange, 0), linewidth=2, style=plot.style_linebr)

plotshape(showIssue61FreshBreaks and rangeBreakUp, title="Fresh breakout", style=shape.circle, location=location.belowbar, color=colBreakout, size=size.tiny, text="BRK")
plotshape(showIssue61FreshBreaks and rangeBreakDn, title="Fresh breakdown", style=shape.circle, location=location.abovebar, color=colBreakdown, size=size.tiny, text="BRK")
plotshape(showIssue61Arms and issue61ArmLong, title="Bull ARM", style=shape.diamond, location=location.belowbar, color=colYellow, size=size.tiny, text="ARM")
plotshape(showIssue61Arms and issue61ArmShort, title="Bear ARM", style=shape.diamond, location=location.abovebar, color=colYellow, size=size.tiny, text="ARM")

plotshape(showIssue61TradeMarks and issue61ManagedEntryLong, title="Long entry", style=shape.triangleup, location=location.belowbar, color=colGreen, size=size.small, text="LONG")
plotshape(showIssue61TradeMarks and issue61ManagedEntryShort, title="Short entry", style=shape.triangledown, location=location.abovebar, color=colRed, size=size.small, text="SHORT")
plotshape(showIssue61TradeMarks and issue61ReentryLong, title="Long re-entry", style=shape.triangleup, location=location.belowbar, color=colGreen, size=size.tiny, text="RE")
plotshape(showIssue61TradeMarks and issue61ReentryShort, title="Short re-entry", style=shape.triangledown, location=location.abovebar, color=colRed, size=size.tiny, text="RE")
plotshape(showIssue61TradeMarks and issue61EarlyFailLong, title="Long early fail", style=shape.xcross, location=location.belowbar, color=colOrange, size=size.small, text="FAIL")
plotshape(showIssue61TradeMarks and issue61EarlyFailShort, title="Short early fail", style=shape.xcross, location=location.abovebar, color=colOrange, size=size.small, text="FAIL")
plotshape(showIssue61TradeMarks and issue61RegimeExitLong, title="Long regime exit", style=shape.square, location=location.belowbar, color=colNeutral, size=size.tiny, text="EXIT")
plotshape(showIssue61TradeMarks and issue61RegimeExitShort, title="Short regime exit", style=shape.square, location=location.abovebar, color=colNeutral, size=size.tiny, text="EXIT")

plot(formalId, "Formal Stage ID", display=display.data_window)
plot(issue61BasePos, "Base lifecycle desired position", display=display.data_window)
plot(issue61ManagedPos, "Managed desired position", display=display.data_window)
plot(issue61ArmedDir, "ARM direction", display=display.data_window)
plot(issue61EntryAge, "Early invalidation age", display=display.data_window)
plot(issue61EntryLevel, "Early invalidation anchor", display=display.data_window)
'''


def build() -> str:
    text = SOURCE.read_text(encoding="utf-8")
    if CUT_MARKER not in text:
        raise RuntimeError(f"missing cut marker: {CUT_MARKER}")
    lines = text.splitlines()
    decl_index = next((i for i, line in enumerate(lines) if line.startswith(OLD_DECL_PREFIX)), None)
    if decl_index is None:
        raise RuntimeError("source indicator declaration not found")
    lines[decl_index] = STRATEGY_DECL
    text = "\n".join(lines) + "\n"
    core = text.split(CUT_MARKER, 1)[0].rstrip()
    out = core + STRATEGY_BLOCK + "\n"

    required = (
        "strategy(\"Chase Risk Radar v0.6｜Stage Lifecycle Strategy Preview\"",
        "rangeBreakUp",
        "rangeBreakDn",
        "formalId",
        "issue61ArmLong",
        "issue61EarlyFailLong",
        "strategy.entry(\"Long\"",
        "strategy.entry(\"Short\"",
        "strategy.close(\"Long\"",
        "strategy.close(\"Short\"",
    )
    for token in required:
        if token not in out:
            raise RuntimeError(f"missing generated token: {token}")
    if CUT_MARKER in out:
        raise RuntimeError("visual dashboard tail was not removed")
    return out


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(build(), encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
