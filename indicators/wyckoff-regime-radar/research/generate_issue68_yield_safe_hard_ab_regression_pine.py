#!/usr/bin/env python3
"""Generate Issue #68 yield-safe C-2 baseline vs HARD A/B regression Pine.

Both arms share the exact same yield-safe representation and production witness
stack. The A/B difference is reconstructed only at S1/S4 direct gate routing:
A uses uncapped exhaustion gates; B is the approved HARD candidate already
present in the generated production candidate.

No PnL, tuning, lookahead, stateful grace, or market-specific logic.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_yield_safe_hard_production_candidate_pine as ys
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

DECL_OLD = 'indicator("Chase Risk Market Regime Radar v0.5.2.1｜Non-functional Cleanup", shorttitle="ChaseRisk Radar v0.5.2.1", overlay=false, precision=1)'
DECL_NEW = 'indicator("Issue #68｜Yield-Safe HARD A/B Regression", shorttitle="#68 HARD A/B", overlay=false, precision=1)'
ANCHOR = '// Visuals'

BODY = r'''
// ============================================================================
// Issue #68 — Yield-Safe C-2 baseline vs exact HARD A/B regression.
// A = same yield-safe C-2 without current-context cap.
// B = exact production candidate already calculated above.
// NO PNL. NO TUNING. NO LOOKAHEAD. NO STATEFUL GRACE.
// ============================================================================

f_issue68ABTop(float accX, float distX) =>
    float best = accX
    int id = 1
    if markupEff > best
        best := markupEff
        id := 2
    if reaccEff > best
        best := reaccEff
        id := 3
    if distX > best
        best := distX
        id := 4
    if markdownEff > best
        best := markdownEff
        id := 5
    if redistEff > best
        best := redistEff
        id := 6
    id

// Reconstruct only the uncapped C-2 S1/S4 arm. All other effective scores are
// the exact HARD-candidate values and are invariant because HARD does not touch them.
issue68ABBaseAccGate = rangeGate * bearBackgroundForAccGate * downsideExhaustionGate * supportHoldingGate * nonMarkdownContinuationGate
issue68ABBaseDistGate = rangeGate * bullBackgroundForDistGate * upsideExhaustionGate * resistanceHoldingGate * nonMarkupContinuationGate
issue68ABBaseAccEff = accRaw * issue68ABBaseAccGate * accVolMult * accMtfMult * accDivMult
issue68ABBaseDistEff = distRaw * issue68ABBaseDistGate * distVolMult * distMtfMult * distDivMult

issue68ABReady = not na(issue68ABBaseAccEff) and not na(issue68ABBaseDistEff) and not na(accEff) and not na(distEff) and not na(topId)
issue68ABBaseTop = issue68ABReady ? f_issue68ABTop(issue68ABBaseAccEff, issue68ABBaseDistEff) : na
issue68ABHardTop = issue68ABReady ? topId : na

issue68ABBindS1 = issue68ABReady and currentBearGate < downsideExhaustionGate
issue68ABBindS4 = issue68ABReady and currentBullGate < upsideExhaustionGate
issue68ABChanged = issue68ABReady and issue68ABBaseTop != issue68ABHardTop
issue68ABNoBindParityViolation = issue68ABReady and not issue68ABBindS1 and not issue68ABBindS4 and issue68ABChanged
issue68ABS1MonotonicViolation = issue68ABReady and accEff > issue68ABBaseAccEff + 0.0000001
issue68ABS4MonotonicViolation = issue68ABReady and distEff > issue68ABBaseDistEff + 0.0000001

issue68ABRemoveS1 = issue68ABChanged and issue68ABBaseTop == 1 and issue68ABHardTop != 1
issue68ABRemoveS4 = issue68ABChanged and issue68ABBaseTop == 4 and issue68ABHardTop != 4
issue68ABEnterS1 = issue68ABChanged and issue68ABBaseTop != 1 and issue68ABHardTop == 1
issue68ABEnterS4 = issue68ABChanged and issue68ABBaseTop != 4 and issue68ABHardTop == 4
issue68ABToBull = issue68ABChanged and (issue68ABHardTop == 2 or issue68ABHardTop == 3)
issue68ABToBear = issue68ABChanged and (issue68ABHardTop == 5 or issue68ABHardTop == 6)
issue68ABToOppNeutral = issue68ABChanged and ((issue68ABBaseTop == 1 and issue68ABHardTop == 4) or (issue68ABBaseTop == 4 and issue68ABHardTop == 1))

var int issue68ABValidN = 0
var int issue68ABBindS1N = 0
var int issue68ABBindS4N = 0
var int issue68ABChangedN = 0
var int issue68ABRemoveS1N = 0
var int issue68ABRemoveS4N = 0
var int issue68ABEnterS1N = 0
var int issue68ABEnterS4N = 0
var int issue68ABToBullN = 0
var int issue68ABToBearN = 0
var int issue68ABToOppNeutralN = 0
var int issue68ABInvariantFailN = 0
var int issue68ABChangedRun = 0
var int issue68ABChangedRunMax = 0

if issue68ABReady
    issue68ABValidN += 1
    issue68ABBindS1N += issue68ABBindS1 ? 1 : 0
    issue68ABBindS4N += issue68ABBindS4 ? 1 : 0
    issue68ABChangedN += issue68ABChanged ? 1 : 0
    issue68ABRemoveS1N += issue68ABRemoveS1 ? 1 : 0
    issue68ABRemoveS4N += issue68ABRemoveS4 ? 1 : 0
    issue68ABEnterS1N += issue68ABEnterS1 ? 1 : 0
    issue68ABEnterS4N += issue68ABEnterS4 ? 1 : 0
    issue68ABToBullN += issue68ABToBull ? 1 : 0
    issue68ABToBearN += issue68ABToBear ? 1 : 0
    issue68ABToOppNeutralN += issue68ABToOppNeutral ? 1 : 0
    issue68ABInvariantFailN += (issue68ABNoBindParityViolation or issue68ABS1MonotonicViolation or issue68ABS4MonotonicViolation) ? 1 : 0

    if issue68ABChanged
        issue68ABChangedRun += 1
        issue68ABChangedRunMax := math.max(issue68ABChangedRunMax, issue68ABChangedRun)
    else
        issue68ABChangedRun := 0

var table issue68ABTable = table.new(position.top_left, 4, 13, border_width=1)
if barstate.islast
    table.cell(issue68ABTable, 0, 0, "#68 HARD A/B", bgcolor=colNeutral, text_color=color.white)
    table.cell(issue68ABTable, 1, 0, syminfo.ticker, bgcolor=colNeutral, text_color=color.white)
    table.cell(issue68ABTable, 2, 0, useYieldLevel ? "Yield Level" : "Price Log", bgcolor=colNeutral, text_color=color.white)
    table.cell(issue68ABTable, 3, 0, issue68ABInvariantFailN == 0 ? "INVARIANTS PASS" : "INVARIANT FAIL", bgcolor=issue68ABInvariantFailN == 0 ? colAcc : colMarkdown, text_color=color.white)

    table.cell(issue68ABTable, 0, 1, "Valid bars")
    table.cell(issue68ABTable, 1, 1, str.tostring(issue68ABValidN))
    table.cell(issue68ABTable, 0, 2, "Cap bind S1 / S4")
    table.cell(issue68ABTable, 1, 2, str.tostring(issue68ABBindS1N) + " / " + str.tostring(issue68ABBindS4N))
    table.cell(issue68ABTable, 0, 3, "TOP changed")
    table.cell(issue68ABTable, 1, 3, str.tostring(issue68ABChangedN))
    table.cell(issue68ABTable, 0, 4, "Baseline S1 removed")
    table.cell(issue68ABTable, 1, 4, str.tostring(issue68ABRemoveS1N))
    table.cell(issue68ABTable, 0, 5, "Baseline S4 removed")
    table.cell(issue68ABTable, 1, 5, str.tostring(issue68ABRemoveS4N))
    table.cell(issue68ABTable, 0, 6, "Cross-release enter S1/S4")
    table.cell(issue68ABTable, 1, 6, str.tostring(issue68ABEnterS1N) + " / " + str.tostring(issue68ABEnterS4N))
    table.cell(issue68ABTable, 0, 7, "Changed -> Bull family")
    table.cell(issue68ABTable, 1, 7, str.tostring(issue68ABToBullN))
    table.cell(issue68ABTable, 0, 8, "Changed -> Bear family")
    table.cell(issue68ABTable, 1, 8, str.tostring(issue68ABToBearN))
    table.cell(issue68ABTable, 0, 9, "S1 <-> S4 direct")
    table.cell(issue68ABTable, 1, 9, str.tostring(issue68ABToOppNeutralN))
    table.cell(issue68ABTable, 0, 10, "Max changed run")
    table.cell(issue68ABTable, 1, 10, str.tostring(issue68ABChangedRunMax))
    table.cell(issue68ABTable, 0, 11, "Current baseline / HARD")
    table.cell(issue68ABTable, 1, 11, str.tostring(issue68ABBaseTop) + " / " + str.tostring(issue68ABHardTop))
    table.cell(issue68ABTable, 0, 12, "Invariant fails")
    table.cell(issue68ABTable, 1, 12, str.tostring(issue68ABInvariantFailN), bgcolor=issue68ABInvariantFailN == 0 ? color.new(colAcc, 70) : color.new(colMarkdown, 40))

// Compact machine/visual channels. IDs: 1 Acc, 2 Markup, 3 Reacc, 4 Dist, 5 Markdown, 6 Redist.
plot(issue68ABBaseTop, "#68 A Baseline TOP", color=color.gray, linewidth=1)
plot(issue68ABHardTop, "#68 B HARD TOP", color=color.black, linewidth=2)
plot(issue68ABChanged ? 7.0 : na, "#68 TOP Changed", color=color.orange, linewidth=2, style=plot.style_circles)

'''


def generate(source_path: Path) -> str:
    hard_candidate, _ = ys.hard.generate(source_path)
    candidate = ys.apply_yield_safe_representation(hard_candidate)
    ys.validate(hard_candidate, candidate)

    candidate = replace_once(candidate, DECL_OLD, DECL_NEW)
    if candidate.count(ANCHOR) != 1:
        raise RuntimeError("expected one Visuals anchor")
    candidate = candidate.replace(ANCHOR, BODY + "\n" + ANCHOR, 1)

    required = (
        'issue68ABBaseAccGate = rangeGate * bearBackgroundForAccGate * downsideExhaustionGate',
        'issue68ABBaseDistGate = rangeGate * bullBackgroundForDistGate * upsideExhaustionGate',
        'issue68ABNoBindParityViolation',
        'issue68ABS1MonotonicViolation',
        'issue68ABS4MonotonicViolation',
        'plot(issue68ABBaseTop, "#68 A Baseline TOP"',
        'plot(issue68ABHardTop, "#68 B HARD TOP"',
        'autoYieldLevel = syminfo.type == "bond" and syminfo.currency == "NONE"',
        'ctxDownExGate = math.min(downsideExhaustionGate, currentBearGate)',
        'ctxUpExGate = math.min(upsideExhaustionGate, currentBullGate)',
    )
    for token in required:
        if token not in candidate:
            raise RuntimeError(f"A/B audit missing token: {token}")

    for forbidden in ('strategy.entry', 'strategy.close', 'STATEFUL CTX'):
        if forbidden in BODY:
            raise RuntimeError(f"forbidden A/B harness construct: {forbidden}")

    return candidate


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate Issue #68 yield-safe HARD A/B regression Pine")
    ap.add_argument("--source", type=Path, default=Path(__file__).resolve().parent / SOURCE_RELATIVE)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    text = generate(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    print(args.output)
    print("Issue #68 yield-safe HARD A/B regression generator PASS")


if __name__ == "__main__":
    main()
