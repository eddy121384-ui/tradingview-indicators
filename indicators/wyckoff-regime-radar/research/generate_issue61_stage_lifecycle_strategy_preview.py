#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "pine" / "issue-61-v06-core-visual-source.pine"
OUTPUT = HERE / "generated" / "wyckoff-issue-61-stage-lifecycle-strategy-preview.pine"
CUT_MARKER = "// v0.3.8 Dashboard Label Semantics Layer"
OLD_DECL_PREFIX = 'indicator("Chase Risk Radar v0.6｜Transition Health Preview"'

STRATEGY_DECL = '''strategy("Chase Risk Radar v0.6｜Stage Lifecycle Strategy Preview", shorttitle="ChaseRisk v0.6 STRAT", overlay=true, precision=5, pyramiding=0, default_qty_type=strategy.fixed, default_qty_value=1, commission_type=strategy.commission.percent, commission_value=0.02, process_orders_on_close=false, max_labels_count=500, max_lines_count=500)'''

STRATEGY_BLOCK = r'''

// ============================================================================
// Issue #61 Stage-aware Position Lifecycle — TradingView human-review candidate
// This is deliberately NOT a scored/optimized production strategy yet.
// Goal: make the intended lifecycle visible so a human can confirm that the
// mechanical translation matches the trading idea before any new PnL study.
//
// Human-review v2 semantics:
// 1) Flat traders do NOT chase an already-running Stage 2 / 5 trend.
// 2) Initial long setup: Stage 1 fresh breakout -> Stage 2 within confirmBars.
//    Initial short setup mirrors Stage 4 fresh breakdown -> Stage 5.
//    A break on the exact 1->2 / 4->5 transition bar is also accepted.
// 3) Once in a trade, temporary loss of Stage 2 / 5 is NOT an automatic exit.
//    Long exits only on an explicit bearish family (4/5/6); short exits only
//    on an explicit bullish family (1/2/3). Formal 0 is treated as unresolved.
// 4) Fresh breaks while already holding are ADD CANDIDATES only; no sizing
//    change is executed in this preview.
// 5) Early breakout invalidation remains active for entry ages 1..confirmBars.
//    After an early fail, the strategy stays flat until a brand-new setup cycle.
// 6) process_orders_on_close=false keeps TradingView execution next-bar, closer
//    to the one-bar-lag accounting used by the Python research evaluators.
// ============================================================================

groupIssue61 = "Issue #61｜Strategy Preview"
showIssue61StageBg = input.bool(true, "顯示 Formal Stage 背景", group=groupIssue61)
showIssue61FreshBreaks = input.bool(false, "顯示 fresh breakout / breakdown", group=groupIssue61)
showIssue61Arms = input.bool(false, "顯示 ARM 等待確認", group=groupIssue61)
showIssue61TradeMarks = input.bool(false, "顯示額外進出場原因標記", group=groupIssue61)
showIssue61Protection = input.bool(false, "顯示前三根突破失效保護線", group=groupIssue61)
showIssue61AddCandidates = input.bool(false, "顯示趨勢中 ADD candidate", group=groupIssue61)

issue61Ready = bar_index >= rankLen - 1

var int issue61Pos = 0
var int issue61ArmedDir = 0
var int issue61ArmedAt = na
var float issue61ArmedLevel = na
var float issue61EntryLevel = na
var int issue61EntryAge = -1

bool issue61ArmLong = false
bool issue61ArmShort = false
bool issue61EntryLong = false
bool issue61EntryShort = false
bool issue61EarlyFailLong = false
bool issue61EarlyFailShort = false
bool issue61OppositeExitLong = false
bool issue61OppositeExitShort = false
bool issue61AddLongCandidate = false
bool issue61AddShortCandidate = false

int issue61Before = issue61Pos

if issue61Ready
    int issue61Stage = formalId
    bool issue61ClosedThisBar = false

    // A held trend survives neutral / unresolved periods and same-side pauses.
    // Exit only when the Formal state clearly enters the opposite family.
    if issue61Pos == 1 and (issue61Stage == 4 or issue61Stage == 5 or issue61Stage == 6)
        issue61Pos := 0
        issue61OppositeExitLong := true
        issue61ClosedThisBar := true
        issue61EntryLevel := na
        issue61EntryAge := -1
        issue61ArmedDir := 0
        issue61ArmedAt := na
        issue61ArmedLevel := na
    else if issue61Pos == -1 and (issue61Stage == 1 or issue61Stage == 2 or issue61Stage == 3)
        issue61Pos := 0
        issue61OppositeExitShort := true
        issue61ClosedThisBar := true
        issue61EntryLevel := na
        issue61EntryAge := -1
        issue61ArmedDir := 0
        issue61ArmedAt := na
        issue61ArmedLevel := na

    // Continuation breaks are information for future sizing research only.
    if issue61Pos == 1 and issue61Stage == 2 and rangeBreakUp
        issue61AddLongCandidate := true
    if issue61Pos == -1 and issue61Stage == 5 and rangeBreakDn
        issue61AddShortCandidate := true

    // Early failure protection is only active for the first confirmBars after
    // entry. It does not create an automatic same-trend re-entry path.
    bool issue61WasHolding = issue61Before == issue61Pos and issue61Pos != 0
    if issue61WasHolding and not na(issue61EntryLevel)
        issue61EntryAge += 1
        if issue61EntryAge <= confirmBars
            bool issue61Invalidated = (issue61Pos == 1 and close <= issue61EntryLevel) or (issue61Pos == -1 and close >= issue61EntryLevel)
            if issue61Invalidated
                issue61EarlyFailLong := issue61Pos == 1
                issue61EarlyFailShort := issue61Pos == -1
                issue61Pos := 0
                issue61ClosedThisBar := true
                issue61EntryLevel := na
                issue61EntryAge := -1
                issue61ArmedDir := 0
                issue61ArmedAt := na
                issue61ArmedLevel := na
        else
            issue61EntryLevel := na
            issue61EntryAge := -1

    // Resolve a previously armed Stage-1 / Stage-4 setup.
    if issue61Pos == 0 and not issue61ClosedThisBar and issue61ArmedDir != 0
        int issue61ArmAge = bar_index - issue61ArmedAt
        int issue61Target = issue61ArmedDir == 1 ? 2 : 5
        int issue61Precursor = issue61ArmedDir == 1 ? 1 : 4
        if issue61ArmAge <= confirmBars and issue61Stage == issue61Target
            issue61Pos := issue61ArmedDir
            issue61EntryLevel := issue61ArmedLevel
            issue61EntryAge := 0
            issue61EntryLong := issue61Pos == 1
            issue61EntryShort := issue61Pos == -1
            issue61ArmedDir := 0
            issue61ArmedAt := na
            issue61ArmedLevel := na
        else if issue61ArmAge > confirmBars or not (issue61Stage == issue61Precursor or issue61Stage == issue61Target)
            issue61ArmedDir := 0
            issue61ArmedAt := na
            issue61ArmedLevel := na

    // Start a NEW lifecycle only from the precursor stage. A fresh break inside
    // an already-running Stage 2 / 5 does not let a flat trader chase the trend.
    if issue61Pos == 0 and not issue61ClosedThisBar and issue61ArmedDir == 0
        bool issue61DirectTransitionLong = rangeBreakUp and issue61Stage == 2 and formalId[1] == 1
        bool issue61DirectTransitionShort = rangeBreakDn and issue61Stage == 5 and formalId[1] == 4
        if issue61DirectTransitionLong
            issue61Pos := 1
            issue61EntryLevel := rangeHighBreak
            issue61EntryAge := 0
            issue61EntryLong := true
        else if issue61DirectTransitionShort
            issue61Pos := -1
            issue61EntryLevel := rangeLowBreak
            issue61EntryAge := 0
            issue61EntryShort := true
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
    issue61Pos := 0
    issue61ArmedDir := 0
    issue61ArmedAt := na
    issue61ArmedLevel := na
    issue61EntryLevel := na
    issue61EntryAge := -1

// ----- Real TradingView orders ----------------------------------------------
// Orders generated at close are processed on the next bar because
// process_orders_on_close=false.
if issue61Ready
    if issue61Before == 1 and issue61Pos != 1
        strategy.close("Long", comment=issue61EarlyFailLong ? "EARLY FAIL" : "OPPOSITE REGIME")
    if issue61Before == -1 and issue61Pos != -1
        strategy.close("Short", comment=issue61EarlyFailShort ? "EARLY FAIL" : "OPPOSITE REGIME")
    if issue61Pos == 1 and issue61Before != 1
        strategy.entry("Long", strategy.long, comment="LONG SETUP")
    if issue61Pos == -1 and issue61Before != -1
        strategy.entry("Short", strategy.short, comment="SHORT SETUP")

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
plotshape(showIssue61AddCandidates and issue61AddLongCandidate, title="Bull add candidate", style=shape.circle, location=location.belowbar, color=colBreakout, size=size.tiny, text="ADD?")
plotshape(showIssue61AddCandidates and issue61AddShortCandidate, title="Bear add candidate", style=shape.circle, location=location.abovebar, color=colBreakdown, size=size.tiny, text="ADD?")

plotshape(showIssue61TradeMarks and issue61EntryLong, title="Long setup entry", style=shape.triangleup, location=location.belowbar, color=colGreen, size=size.small, text="LONG")
plotshape(showIssue61TradeMarks and issue61EntryShort, title="Short setup entry", style=shape.triangledown, location=location.abovebar, color=colRed, size=size.small, text="SHORT")
plotshape(showIssue61TradeMarks and issue61EarlyFailLong, title="Long early fail", style=shape.xcross, location=location.belowbar, color=colOrange, size=size.small, text="FAIL")
plotshape(showIssue61TradeMarks and issue61EarlyFailShort, title="Short early fail", style=shape.xcross, location=location.abovebar, color=colOrange, size=size.small, text="FAIL")
plotshape(showIssue61TradeMarks and issue61OppositeExitLong, title="Long opposite-regime exit", style=shape.square, location=location.belowbar, color=colNeutral, size=size.tiny, text="EXIT")
plotshape(showIssue61TradeMarks and issue61OppositeExitShort, title="Short opposite-regime exit", style=shape.square, location=location.abovebar, color=colNeutral, size=size.tiny, text="EXIT")

plot(formalId, "Formal Stage ID", display=display.data_window)
plot(issue61Pos, "Lifecycle desired position", display=display.data_window)
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
        "process_orders_on_close=false",
        "rangeBreakUp",
        "rangeBreakDn",
        "formalId",
        "issue61ArmLong",
        "issue61EarlyFailLong",
        "issue61OppositeExitLong",
        "issue61AddLongCandidate",
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
