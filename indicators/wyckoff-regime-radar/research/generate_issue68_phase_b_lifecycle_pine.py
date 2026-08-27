#!/usr/bin/env python3
"""Generate Issue #68 Phase-B lifecycle visual/performance Pine previews.

Both builds are mechanically derived from the runtime-validated Issue #66 D1
C-2 Pine calculation core.  They differ ONLY in the `strategy(...)`
declaration; the complete body after that declaration is byte-identical.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue66_phase_d1_parity_pine as d1
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once


HERE = Path(__file__).resolve().parent
D1_EXPORT_MARKER = "// === Issue #66 Phase D-1 parity export ==="
D1_INDICATOR_DECL = 'indicator("Chase Risk Radar｜Issue #66 C-2 Parity", shorttitle="ChaseRisk #66 C2 Parity", overlay=false, precision=1)'
DECL_PLACEHOLDER = "__ISSUE68_STRATEGY_DECLARATION__"

VISUAL_DECL = 'strategy("Chase Risk Radar｜Issue #68 Lifecycle Visual Review", shorttitle="ChaseRisk #68 LIFE", overlay=true, precision=5, pyramiding=0, default_qty_type=strategy.fixed, default_qty_value=1, commission_type=strategy.commission.percent, commission_value=0.02, process_orders_on_close=false, max_labels_count=500, max_lines_count=500)'
PERFORMANCE_DECL = 'strategy("Chase Risk Radar｜Issue #68 Lifecycle Performance Preview", shorttitle="ChaseRisk #68 PERF", overlay=true, precision=5, pyramiding=0, initial_capital=100000, default_qty_type=strategy.percent_of_equity, default_qty_value=100, commission_type=strategy.commission.percent, commission_value=0.02, process_orders_on_close=false, max_labels_count=500, max_lines_count=500)'


LIFECYCLE_BODY = r'''

// ============================================================================
// Issue #68 — frozen Issue #61 human-review-v2 lifecycle on repaired C-2 core
// Semantic preview only. Do not select rules from Strategy Tester PnL here.
//
// 1) Flat initial long: Stage 1 fresh breakout -> Stage 2 within confirmBars.
//    Short is the exact Stage 4 -> Stage 5 mirror.
// 2) Exact 1->2 / 4->5 transition-bar fresh break is accepted.
// 3) No arbitrary flat chase inside an already-running Stage 2 / 5.
// 4) Held long exits only on Formal 4/5/6; short only on Formal 1/2/3.
//    Formal 0 and same-side pauses survive.
// 5) Continuation breaks while holding are ADD? observations only.
// 6) Early Fail anchor is active only at entry ages 1..confirmBars.
// 7) After fail, a brand-new precursor setup is required.
// 8) process_orders_on_close=false preserves next-bar TradingView execution.
// ============================================================================

groupIssue68 = "Issue #68｜Lifecycle Semantic Review"
showIssue68StageBg = input.bool(true, "顯示 Formal Stage 背景", group=groupIssue68)
showIssue68FreshBreaks = input.bool(false, "顯示 fresh breakout / breakdown", group=groupIssue68)
showIssue68Arms = input.bool(true, "顯示 ARM 等待確認", group=groupIssue68)
showIssue68TradeMarks = input.bool(true, "顯示 LONG / SHORT / FAIL / EXIT", group=groupIssue68)
showIssue68Protection = input.bool(true, "顯示前三根 Early Fail 保護線", group=groupIssue68)
showIssue68AddCandidates = input.bool(false, "顯示趨勢中 ADD? candidate", group=groupIssue68)

issue68Ready = bar_index >= rankLen - 1

var int issue68Pos = 0
var int issue68ArmedDir = 0
var int issue68ArmedAt = na
var float issue68ArmedLevel = na
var float issue68EntryLevel = na
var int issue68EntryAge = -1

bool issue68ArmLong = false
bool issue68ArmShort = false
bool issue68EntryLong = false
bool issue68EntryShort = false
bool issue68EarlyFailLong = false
bool issue68EarlyFailShort = false
bool issue68OppositeExitLong = false
bool issue68OppositeExitShort = false
bool issue68AddLongCandidate = false
bool issue68AddShortCandidate = false

int issue68Before = issue68Pos

if issue68Ready
    int issue68Stage = formalId
    bool issue68ClosedThisBar = false

    // A held trade survives neutral/unresolved state and same-side pauses.
    if issue68Pos == 1 and (issue68Stage == 4 or issue68Stage == 5 or issue68Stage == 6)
        issue68Pos := 0
        issue68OppositeExitLong := true
        issue68ClosedThisBar := true
        issue68EntryLevel := na
        issue68EntryAge := -1
        issue68ArmedDir := 0
        issue68ArmedAt := na
        issue68ArmedLevel := na
    else if issue68Pos == -1 and (issue68Stage == 1 or issue68Stage == 2 or issue68Stage == 3)
        issue68Pos := 0
        issue68OppositeExitShort := true
        issue68ClosedThisBar := true
        issue68EntryLevel := na
        issue68EntryAge := -1
        issue68ArmedDir := 0
        issue68ArmedAt := na
        issue68ArmedLevel := na

    // Continuation breaks are information only; no base sizing change.
    if issue68Pos == 1 and issue68Stage == 2 and rangeBreakUp
        issue68AddLongCandidate := true
    if issue68Pos == -1 and issue68Stage == 5 and rangeBreakDn
        issue68AddShortCandidate := true

    // Early Fail is active only after entry, ages 1..confirmBars.
    bool issue68WasHolding = issue68Before == issue68Pos and issue68Pos != 0
    if issue68WasHolding and not na(issue68EntryLevel)
        issue68EntryAge += 1
        if issue68EntryAge <= confirmBars
            bool issue68Invalidated = (issue68Pos == 1 and close <= issue68EntryLevel) or (issue68Pos == -1 and close >= issue68EntryLevel)
            if issue68Invalidated
                issue68EarlyFailLong := issue68Pos == 1
                issue68EarlyFailShort := issue68Pos == -1
                issue68Pos := 0
                issue68ClosedThisBar := true
                issue68EntryLevel := na
                issue68EntryAge := -1
                issue68ArmedDir := 0
                issue68ArmedAt := na
                issue68ArmedLevel := na
        else
            issue68EntryLevel := na
            issue68EntryAge := -1

    // Resolve an existing precursor setup before considering a new one.
    if issue68Pos == 0 and not issue68ClosedThisBar and issue68ArmedDir != 0
        int issue68ArmAge = bar_index - issue68ArmedAt
        int issue68Target = issue68ArmedDir == 1 ? 2 : 5
        int issue68Precursor = issue68ArmedDir == 1 ? 1 : 4
        if issue68ArmAge <= confirmBars and issue68Stage == issue68Target
            issue68Pos := issue68ArmedDir
            issue68EntryLevel := issue68ArmedLevel
            issue68EntryAge := 0
            issue68EntryLong := issue68Pos == 1
            issue68EntryShort := issue68Pos == -1
            issue68ArmedDir := 0
            issue68ArmedAt := na
            issue68ArmedLevel := na
        else if issue68ArmAge > confirmBars or not (issue68Stage == issue68Precursor or issue68Stage == issue68Target)
            issue68ArmedDir := 0
            issue68ArmedAt := na
            issue68ArmedLevel := na

    // Start a NEW lifecycle only from precursor context. A fresh break in an
    // already-running target stage is not a flat chase entry.
    if issue68Pos == 0 and not issue68ClosedThisBar and issue68ArmedDir == 0
        bool issue68DirectTransitionLong = rangeBreakUp and issue68Stage == 2 and formalId[1] == 1
        bool issue68DirectTransitionShort = rangeBreakDn and issue68Stage == 5 and formalId[1] == 4
        if issue68DirectTransitionLong
            issue68Pos := 1
            issue68EntryLevel := rangeHighBreak
            issue68EntryAge := 0
            issue68EntryLong := true
        else if issue68DirectTransitionShort
            issue68Pos := -1
            issue68EntryLevel := rangeLowBreak
            issue68EntryAge := 0
            issue68EntryShort := true
        else if rangeBreakUp and issue68Stage == 1
            issue68ArmedDir := 1
            issue68ArmedAt := bar_index
            issue68ArmedLevel := rangeHighBreak
            issue68ArmLong := true
        else if rangeBreakDn and issue68Stage == 4
            issue68ArmedDir := -1
            issue68ArmedAt := bar_index
            issue68ArmedLevel := rangeLowBreak
            issue68ArmShort := true
else
    issue68Pos := 0
    issue68ArmedDir := 0
    issue68ArmedAt := na
    issue68ArmedLevel := na
    issue68EntryLevel := na
    issue68EntryAge := -1

// ----- TradingView orders ----------------------------------------------------
if issue68Ready
    if issue68Before == 1 and issue68Pos != 1
        strategy.close("Long", comment=issue68EarlyFailLong ? "EARLY FAIL" : "OPPOSITE REGIME")
    if issue68Before == -1 and issue68Pos != -1
        strategy.close("Short", comment=issue68EarlyFailShort ? "EARLY FAIL" : "OPPOSITE REGIME")
    if issue68Pos == 1 and issue68Before != 1
        strategy.entry("Long", strategy.long, comment="LONG SETUP")
    if issue68Pos == -1 and issue68Before != -1
        strategy.entry("Short", strategy.short, comment="SHORT SETUP")

// ----- Human semantic audit layer -------------------------------------------
color issue68StageColor = formalId == 1 ? colAcc : formalId == 2 ? colMarkup : formalId == 3 ? colReacc : formalId == 4 ? colDist : formalId == 5 ? colMarkdown : formalId == 6 ? colRedist : colNeutral
bgcolor(showIssue68StageBg and issue68Ready ? color.new(issue68StageColor, 90) : na, title="Issue68 Formal Stage")

plot(showIssue68FreshBreaks ? rangeHighBreak : na, "Issue68 prior range high", color=color.new(colBreakout, 65), linewidth=1, style=plot.style_linebr)
plot(showIssue68FreshBreaks ? rangeLowBreak : na, "Issue68 prior range low", color=color.new(colBreakdown, 65), linewidth=1, style=plot.style_linebr)
plot(showIssue68Protection and not na(issue68EntryLevel) ? issue68EntryLevel : na, "Issue68 Early Fail anchor", color=color.new(colOrange, 0), linewidth=2, style=plot.style_linebr)

plotshape(showIssue68FreshBreaks and rangeBreakUp, title="Issue68 Fresh breakout", style=shape.circle, location=location.belowbar, color=colBreakout, size=size.tiny, text="BRK")
plotshape(showIssue68FreshBreaks and rangeBreakDn, title="Issue68 Fresh breakdown", style=shape.circle, location=location.abovebar, color=colBreakdown, size=size.tiny, text="BRK")
plotshape(showIssue68Arms and issue68ArmLong, title="Issue68 Bull ARM", style=shape.diamond, location=location.belowbar, color=colYellow, size=size.tiny, text="ARM")
plotshape(showIssue68Arms and issue68ArmShort, title="Issue68 Bear ARM", style=shape.diamond, location=location.abovebar, color=colYellow, size=size.tiny, text="ARM")
plotshape(showIssue68AddCandidates and issue68AddLongCandidate, title="Issue68 Bull ADD?", style=shape.circle, location=location.belowbar, color=colBreakout, size=size.tiny, text="ADD?")
plotshape(showIssue68AddCandidates and issue68AddShortCandidate, title="Issue68 Bear ADD?", style=shape.circle, location=location.abovebar, color=colBreakdown, size=size.tiny, text="ADD?")
plotshape(showIssue68TradeMarks and issue68EntryLong, title="Issue68 Long entry", style=shape.triangleup, location=location.belowbar, color=colGreen, size=size.small, text="LONG")
plotshape(showIssue68TradeMarks and issue68EntryShort, title="Issue68 Short entry", style=shape.triangledown, location=location.abovebar, color=colRed, size=size.small, text="SHORT")
plotshape(showIssue68TradeMarks and issue68EarlyFailLong, title="Issue68 Long Early Fail", style=shape.xcross, location=location.belowbar, color=colOrange, size=size.small, text="FAIL")
plotshape(showIssue68TradeMarks and issue68EarlyFailShort, title="Issue68 Short Early Fail", style=shape.xcross, location=location.abovebar, color=colOrange, size=size.small, text="FAIL")
plotshape(showIssue68TradeMarks and issue68OppositeExitLong, title="Issue68 Long opposite exit", style=shape.square, location=location.belowbar, color=colNeutral, size=size.tiny, text="EXIT")
plotshape(showIssue68TradeMarks and issue68OppositeExitShort, title="Issue68 Short opposite exit", style=shape.square, location=location.abovebar, color=colNeutral, size=size.tiny, text="EXIT")

plot(float(formalId), "Issue68 Formal Stage ID", display=display.data_window)
plot(float(issue68Pos), "Issue68 Lifecycle desired position", display=display.data_window)
plot(float(issue68ArmedDir), "Issue68 ARM direction", display=display.data_window)
plot(float(issue68EntryAge), "Issue68 Early Fail age", display=display.data_window)
plot(issue68EntryLevel, "Issue68 Early Fail anchor value", display=display.data_window)
'''


def shared_body(source: Path) -> str:
    # Reuse the already runtime-validated D1 generator so C-2 Pine lineage and
    # forced price-only witness configuration cannot drift here.
    d1_text = d1.generate(source)
    if d1_text.count(D1_EXPORT_MARKER) != 1:
        raise RuntimeError("expected exactly one D1 parity-export marker")
    core = d1_text.split(D1_EXPORT_MARKER, 1)[0].rstrip()
    core = replace_once(core, D1_INDICATOR_DECL, DECL_PLACEHOLDER)
    out = core + LIFECYCLE_BODY + "\n"

    forbidden = ("PARITY formal_id", "screenshot parity checkpoints", "D1B|")
    for token in forbidden:
        if token in out:
            raise RuntimeError(f"Phase-B strategy leaked parity transport token: {token}")
    required = (
        "Issue #66 C-2",
        "volumeMode = \"Off\"",
        "mtfMode = \"Off\"",
        "divMode = \"Off\"",
        "issue68DirectTransitionLong",
        "issue68EarlyFailLong",
        "issue68OppositeExitLong",
        "strategy.entry(\"Long\"",
        "strategy.close(\"Short\"",
    )
    for token in required:
        if token not in out:
            raise RuntimeError(f"missing Phase-B required token: {token}")
    return out


def generate(source: Path, mode: str) -> str:
    body = shared_body(source)
    if mode == "visual":
        decl = VISUAL_DECL
    elif mode == "performance":
        decl = PERFORMANCE_DECL
    else:
        raise ValueError("mode must be visual or performance")
    return replace_once(body, DECL_PLACEHOLDER, decl)


def strip_declaration(text: str) -> str:
    """Return source with only the strategy declaration line removed."""
    lines = text.splitlines()
    indices = [i for i, line in enumerate(lines) if line.startswith("strategy(")]
    if len(indices) != 1:
        raise RuntimeError(f"expected exactly one strategy declaration, found {len(indices)}")
    del lines[indices[0]]
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def main() -> None:
    ap = argparse.ArgumentParser()
    default_source = HERE / SOURCE_RELATIVE
    ap.add_argument("--source", type=Path, default=default_source)
    ap.add_argument("--visual-output", type=Path, required=True)
    ap.add_argument("--performance-output", type=Path, required=True)
    args = ap.parse_args()

    visual = generate(args.source, "visual")
    performance = generate(args.source, "performance")
    if strip_declaration(visual) != strip_declaration(performance):
        raise RuntimeError("visual/performance strategy bodies differ")

    args.visual_output.parent.mkdir(parents=True, exist_ok=True)
    args.performance_output.parent.mkdir(parents=True, exist_ok=True)
    args.visual_output.write_text(visual, encoding="utf-8")
    args.performance_output.write_text(performance, encoding="utf-8")


if __name__ == "__main__":
    main()
