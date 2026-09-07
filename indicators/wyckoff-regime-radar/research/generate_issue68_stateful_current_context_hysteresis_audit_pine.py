#!/usr/bin/env python3
"""Generate Issue #68 stateful current-context hysteresis audit Pine."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_current_context_symmetric_s1_s4_audit_pine as sym
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 Stateful CTX", shorttitle="ChaseRisk #68 HYS", overlay=false, precision=3)'

BODY = r'''

// ============================================================================
// Issue #68 Stateful Current-Context Hysteresis Audit.
// Acquisition = exact symmetric HARD current-context TOP.
// Retention = at most confirmBars-1 consecutive HARD disagreements while
// production TOP still remains the held S1/S4 stage. Opposite HARD S1/S4
// switches immediately. No new threshold/lookback. NO PNL. C-2 FROZEN.
// ============================================================================

groupIssue68Hys = "Issue #68｜Stateful CTX Hysteresis"
showIssue68HysTable = input.bool(true, "顯示 Stateful CTX 表", group=groupIssue68Hys)

var int issue68HysHeldStage = 0
var int issue68HysMissBars = 0
int issue68HysTop = issue68S14Top

bool issue68HysProdLeftS1 = false
bool issue68HysProdLeftS4 = false

if issue68S14Valid
    // HARD S1/S4 is the only acquisition/refresh path.
    if issue68S14Top == 1 or issue68S14Top == 4
        issue68HysHeldStage := issue68S14Top
        issue68HysMissBars := 0
        issue68HysTop := issue68S14Top
    else if issue68HysHeldStage == 1
        // Historical memory cannot sustain S1 after production itself leaves S1.
        if topId != 1
            issue68HysProdLeftS1 := true
            issue68HysHeldStage := 0
            issue68HysMissBars := 0
            issue68HysTop := issue68S14Top
        else
            issue68HysMissBars += 1
            if issue68HysMissBars < confirmBars
                issue68HysTop := 1
            else
                issue68HysHeldStage := 0
                issue68HysMissBars := 0
                issue68HysTop := issue68S14Top
    else if issue68HysHeldStage == 4
        // Exact mirror for S4.
        if topId != 4
            issue68HysProdLeftS4 := true
            issue68HysHeldStage := 0
            issue68HysMissBars := 0
            issue68HysTop := issue68S14Top
        else
            issue68HysMissBars += 1
            if issue68HysMissBars < confirmBars
                issue68HysTop := 4
            else
                issue68HysHeldStage := 0
                issue68HysMissBars := 0
                issue68HysTop := issue68S14Top
    else
        issue68HysHeldStage := 0
        issue68HysMissBars := 0
        issue68HysTop := issue68S14Top

bool issue68HysHoldingS1 = issue68S14Valid and issue68HysTop == 1 and issue68S14Top != 1
bool issue68HysHoldingS4 = issue68S14Valid and issue68HysTop == 4 and issue68S14Top != 4
bool issue68HysFreshS1Retained = issue68S14FreshS1 and issue68HysTop == 1
bool issue68HysFreshS4Retained = issue68S14FreshS4 and issue68HysTop == 4
bool issue68HysOtherS1Removed = issue68S14OtherS1 and issue68HysTop != 1
bool issue68HysOtherS4Removed = issue68S14OtherS4 and issue68HysTop != 4
bool issue68HysFreshS1Rescued = issue68S14FreshS1 and issue68S14Top != 1 and issue68HysTop == 1
bool issue68HysFreshS4Rescued = issue68S14FreshS4 and issue68S14Top != 4 and issue68HysTop == 4
bool issue68HysOtherS1Reintro = issue68S14OtherS1 and issue68S14Top != 1 and issue68HysTop == 1
bool issue68HysOtherS4Reintro = issue68S14OtherS4 and issue68S14Top != 4 and issue68HysTop == 4
bool issue68HysStateChanged = issue68S14Valid and issue68HysTop != topId
bool issue68HysDiffHard = issue68S14Valid and issue68HysTop != issue68S14Top

var int issue68HysStateFreshS1RetainedN = 0
var int issue68HysStateFreshS4RetainedN = 0
var int issue68HysStateOtherS1RemovedN = 0
var int issue68HysStateOtherS4RemovedN = 0
var int issue68HysFreshS1RescuedN = 0
var int issue68HysFreshS4RescuedN = 0
var int issue68HysOtherS1ReintroN = 0
var int issue68HysOtherS4ReintroN = 0
var int issue68HysStateChangedN = 0
var int issue68HysDiffHardN = 0
var int issue68HysProdLeftS1N = 0
var int issue68HysProdLeftS4N = 0
var int issue68HysHardSwitchN = 0
var int issue68HysStateSwitchN = 0
var int issue68HysPrevHard = 0
var int issue68HysPrevState = 0
var int issue68HysHoldS1BarsN = 0
var int issue68HysHoldS4BarsN = 0
var int issue68HysHoldS1Run = 0
var int issue68HysHoldS4Run = 0
var int issue68HysHoldS1RunMax = 0
var int issue68HysHoldS4RunMax = 0

if issue68S14Valid
    issue68HysStateFreshS1RetainedN += issue68HysFreshS1Retained ? 1 : 0
    issue68HysStateFreshS4RetainedN += issue68HysFreshS4Retained ? 1 : 0
    issue68HysStateOtherS1RemovedN += issue68HysOtherS1Removed ? 1 : 0
    issue68HysStateOtherS4RemovedN += issue68HysOtherS4Removed ? 1 : 0
    issue68HysFreshS1RescuedN += issue68HysFreshS1Rescued ? 1 : 0
    issue68HysFreshS4RescuedN += issue68HysFreshS4Rescued ? 1 : 0
    issue68HysOtherS1ReintroN += issue68HysOtherS1Reintro ? 1 : 0
    issue68HysOtherS4ReintroN += issue68HysOtherS4Reintro ? 1 : 0
    issue68HysStateChangedN += issue68HysStateChanged ? 1 : 0
    issue68HysDiffHardN += issue68HysDiffHard ? 1 : 0
    issue68HysProdLeftS1N += issue68HysProdLeftS1 ? 1 : 0
    issue68HysProdLeftS4N += issue68HysProdLeftS4 ? 1 : 0

    if issue68HysPrevHard != 0 and issue68S14Top != issue68HysPrevHard
        issue68HysHardSwitchN += 1
    if issue68HysPrevState != 0 and issue68HysTop != issue68HysPrevState
        issue68HysStateSwitchN += 1
    issue68HysPrevHard := issue68S14Top
    issue68HysPrevState := issue68HysTop

    if issue68HysHoldingS1
        issue68HysHoldS1BarsN += 1
        issue68HysHoldS1Run += 1
        issue68HysHoldS1RunMax := math.max(issue68HysHoldS1RunMax, issue68HysHoldS1Run)
    else
        issue68HysHoldS1Run := 0
    if issue68HysHoldingS4
        issue68HysHoldS4BarsN += 1
        issue68HysHoldS4Run += 1
        issue68HysHoldS4RunMax := math.max(issue68HysHoldS4RunMax, issue68HysHoldS4Run)
    else
        issue68HysHoldS4Run := 0

var table tHys = table.new(position.middle_right, 5, 16, border_width=1)
if barstate.islast
    if showIssue68HysTable
        table.cell(tHys, 0, 0, "STATEFUL CTX", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHys, 1, 0, syminfo.ticker, bgcolor=colNeutral, text_color=color.white)
        table.cell(tHys, 2, 0, "HARD", bgcolor=colRed, text_color=color.white)
        table.cell(tHys, 3, 0, "STATE", bgcolor=colGreen, text_color=color.white)
        table.cell(tHys, 4, 0, "READ", bgcolor=colNeutral, text_color=color.white)

        table.cell(tHys, 0, 1, "Valid / confirmBars", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHys, 1, 1, str.tostring(issue68S14ValidN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHys, 2, 1, str.tostring(confirmBars), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHys, 3, 1, "max grace " + str.tostring(math.max(confirmBars - 1, 0)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHys, 4, 1, "existing horizon", bgcolor=colGreen, text_color=color.white)

        table.cell(tHys, 0, 2, "Fresh S1 retained", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHys, 2, 2, str.tostring(issue68S14FreshS1RetainedN) + " / " + f_issue68S1PFmtPct(issue68S14FreshS1RetainedN, issue68S14FreshS1N), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHys, 3, 2, str.tostring(issue68HysStateFreshS1RetainedN) + " / " + f_issue68S1PFmtPct(issue68HysStateFreshS1RetainedN, issue68S14FreshS1N), bgcolor=colGreen, text_color=color.white)
        table.cell(tHys, 4, 2, "preserve", bgcolor=colGreen, text_color=color.white)

        table.cell(tHys, 0, 3, "Fresh S4 retained", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHys, 2, 3, str.tostring(issue68S14FreshS4RetainedN) + " / " + f_issue68S1PFmtPct(issue68S14FreshS4RetainedN, issue68S14FreshS4N), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHys, 3, 3, str.tostring(issue68HysStateFreshS4RetainedN) + " / " + f_issue68S1PFmtPct(issue68HysStateFreshS4RetainedN, issue68S14FreshS4N), bgcolor=colGreen, text_color=color.white)
        table.cell(tHys, 4, 3, "mirror", bgcolor=colGreen, text_color=color.white)

        table.cell(tHys, 0, 4, "Other S1 removed", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHys, 2, 4, str.tostring(issue68S14OtherS1RemovedN) + " / " + f_issue68S1PFmtPct(issue68S14OtherS1RemovedN, issue68S14OtherS1N), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHys, 3, 4, str.tostring(issue68HysStateOtherS1RemovedN) + " / " + f_issue68S1PFmtPct(issue68HysStateOtherS1RemovedN, issue68S14OtherS1N), bgcolor=colGreen, text_color=color.white)
        table.cell(tHys, 4, 4, "stale cost", bgcolor=colNeutral, text_color=color.white)

        table.cell(tHys, 0, 5, "Other S4 removed", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHys, 2, 5, str.tostring(issue68S14OtherS4RemovedN) + " / " + f_issue68S1PFmtPct(issue68S14OtherS4RemovedN, issue68S14OtherS4N), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHys, 3, 5, str.tostring(issue68HysStateOtherS4RemovedN) + " / " + f_issue68S1PFmtPct(issue68HysStateOtherS4RemovedN, issue68S14OtherS4N), bgcolor=colGreen, text_color=color.white)
        table.cell(tHys, 4, 5, "mirror cost", bgcolor=colNeutral, text_color=color.white)

        table.cell(tHys, 0, 6, "Fresh rescue S1 / S4", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHys, 3, 6, str.tostring(issue68HysFreshS1RescuedN) + " / " + str.tostring(issue68HysFreshS4RescuedN), bgcolor=colGreen, text_color=color.white)
        table.cell(tHys, 4, 6, "HARD lost -> STATE keep", bgcolor=colGreen, text_color=color.white)

        table.cell(tHys, 0, 7, "Other reintro S1 / S4", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHys, 3, 7, str.tostring(issue68HysOtherS1ReintroN) + " / " + str.tostring(issue68HysOtherS4ReintroN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHys, 4, 7, "stale tradeoff", bgcolor=colRed, text_color=color.white)

        table.cell(tHys, 0, 8, "TOP changed vs PROD", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHys, 2, 8, str.tostring(issue68S14ChangedN) + " / " + f_issue68S1PFmtPct(issue68S14ChangedN, issue68S14ValidN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHys, 3, 8, str.tostring(issue68HysStateChangedN) + " / " + f_issue68S1PFmtPct(issue68HysStateChangedN, issue68S14ValidN), bgcolor=colGreen, text_color=color.white)
        table.cell(tHys, 4, 8, "global footprint", bgcolor=colNeutral, text_color=color.white)

        table.cell(tHys, 0, 9, "TOP switches", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHys, 2, 9, str.tostring(issue68HysHardSwitchN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHys, 3, 9, str.tostring(issue68HysStateSwitchN), bgcolor=colGreen, text_color=color.white)
        table.cell(tHys, 4, 9, "churn", bgcolor=colNeutral, text_color=color.white)

        table.cell(tHys, 0, 10, "Held bars S1 / S4", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHys, 3, 10, str.tostring(issue68HysHoldS1BarsN) + " / " + str.tostring(issue68HysHoldS4BarsN), bgcolor=colGreen, text_color=color.white)
        table.cell(tHys, 4, 10, "grace exposure", bgcolor=colNeutral, text_color=color.white)

        table.cell(tHys, 0, 11, "Max held run S1 / S4", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHys, 3, 11, str.tostring(issue68HysHoldS1RunMax) + " / " + str.tostring(issue68HysHoldS4RunMax), bgcolor=colGreen, text_color=color.white)
        table.cell(tHys, 4, 11, "must < confirmBars", bgcolor=colGreen, text_color=color.white)

        table.cell(tHys, 0, 12, "Prod-left release S1/S4", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHys, 3, 12, str.tostring(issue68HysProdLeftS1N) + " / " + str.tostring(issue68HysProdLeftS4N), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHys, 4, 12, "memory cannot revive", bgcolor=colGreen, text_color=color.white)

        table.cell(tHys, 0, 13, "STATE != HARD", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHys, 3, 13, str.tostring(issue68HysDiffHardN) + " / " + f_issue68S1PFmtPct(issue68HysDiffHardN, issue68S14ValidN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tHys, 4, 13, "hysteresis footprint", bgcolor=colNeutral, text_color=color.white)

        table.cell(tHys, 0, 14, "SEMANTIC", bgcolor=colGreen, text_color=color.white)
        table.cell(tHys, 2, 14, "acquire HARD", bgcolor=colGreen, text_color=color.white)
        table.cell(tHys, 3, 14, "release after confirmBars", bgcolor=colGreen, text_color=color.white)
        table.cell(tHys, 4, 14, "EXACT MIRROR", bgcolor=colGreen, text_color=color.white)

        table.cell(tHys, 0, 15, "READ", bgcolor=colNeutral, text_color=color.white)
        table.cell(tHys, 2, 15, "HARD baseline", bgcolor=colRed, text_color=color.white)
        table.cell(tHys, 3, 15, "Fresh gain vs stale cost?", bgcolor=colGreen, text_color=color.white)
        table.cell(tHys, 4, 15, "NO TUNING", bgcolor=colRed, text_color=color.white)
    else
        table.clear(tHys, 0, 0, 4, 15)
'''


def generate(source: Path) -> str:
    out = sym.generate(source)
    out = replace_once(out, sym.AUDIT_DECL, AUDIT_DECL)
    out = replace_once(
        out,
        'showIssue68S14Table = input.bool(true, "顯示 Symmetric S1/S4 表", group=groupIssue68S14)',
        'showIssue68S14Table = input.bool(false, "顯示 Symmetric S1/S4 表", group=groupIssue68S14)',
    )
    out = out.rstrip() + BODY + "\n"
    required = [
        "issue68HysMissBars < confirmBars",
        "topId != 1",
        "topId != 4",
        "Fresh rescue S1 / S4",
        "Other reintro S1 / S4",
        "TOP switches",
        "must < confirmBars",
        "EXACT MIRROR",
        "NO TUNING",
    ]
    for token in required:
        if token not in out:
            raise RuntimeError(f"missing stateful audit token: {token}")
    if "strategy.entry" in out or "strategy.close" in out:
        raise RuntimeError("stateful audit leaked strategy order logic")
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
