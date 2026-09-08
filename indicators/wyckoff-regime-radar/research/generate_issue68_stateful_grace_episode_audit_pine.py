#!/usr/bin/env python3
"""Generate Issue #68 stateful grace-episode outcome audit Pine."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_stateful_current_context_hysteresis_audit_pine as hys
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 Grace Episodes", shorttitle="ChaseRisk #68 EP", overlay=false, precision=3)'

BODY = r'''

// ============================================================================
// Issue #68 Stateful Grace-Episode Outcome Audit.
// Episode start = STATE holds S1/S4 while HARD disagrees and PROD still remains
// the same held stage. Outcomes: RECOVER / TIMEOUT / PROD EXIT / OPPOSITE.
// Anchor class is frozen on episode entry: FRESH vs OTHER. NO LOOKAHEAD.
// Existing confirmBars only. Exact S1/S4 mirror. NO PNL. C-2 FROZEN.
// ============================================================================

groupIssue68Ep = "Issue #68｜Stateful Grace Episodes"
showIssue68EpTable = input.bool(true, "顯示 Grace Episode 表", group=groupIssue68Ep)

f_issue68EpIdx(int stage, int kind) =>
    stage == 1 ? (kind == 1 ? 0 : 1) : (kind == 1 ? 2 : 3)

f_issue68EpPct(int n, int d) =>
    d > 0 ? str.tostring(100.0 * n / d, "#.##") + "%" : "NA"

f_issue68EpAvg(int total, int n) =>
    n > 0 ? str.tostring(1.0 * total / n, "#.##") : "NA"

var int issue68EpStage = 0
var int issue68EpKind = 0 // 1=Fresh, 2=Other
var int issue68EpHeldBars = 0

var issue68EpN = array.new_int(4, 0)
var issue68EpRecoverN = array.new_int(4, 0)
var issue68EpTimeoutN = array.new_int(4, 0)
var issue68EpProdExitN = array.new_int(4, 0)
var issue68EpOppositeN = array.new_int(4, 0)
var issue68EpHeldSum = array.new_int(4, 0)
var issue68EpHeldMax = array.new_int(4, 0)

if issue68S14Valid
    // First resolve an episode that was already active before this bar.
    if issue68EpStage != 0
        int issue68EpIdxNow = f_issue68EpIdx(issue68EpStage, issue68EpKind)
        bool issue68EpStillHolding = issue68EpStage == 1 ? issue68HysHoldingS1 : issue68HysHoldingS4
        if issue68EpStillHolding
            issue68EpHeldBars += 1
        else
            bool issue68EpRecovered = issue68S14Top == issue68EpStage
            bool issue68EpOpposite = (issue68EpStage == 1 and issue68S14Top == 4) or (issue68EpStage == 4 and issue68S14Top == 1)
            bool issue68EpProdExited = not issue68EpRecovered and not issue68EpOpposite and topId != issue68EpStage
            bool issue68EpTimedOut = not issue68EpRecovered and not issue68EpOpposite and not issue68EpProdExited

            if issue68EpRecovered
                array.set(issue68EpRecoverN, issue68EpIdxNow, array.get(issue68EpRecoverN, issue68EpIdxNow) + 1)
            else if issue68EpOpposite
                array.set(issue68EpOppositeN, issue68EpIdxNow, array.get(issue68EpOppositeN, issue68EpIdxNow) + 1)
            else if issue68EpProdExited
                array.set(issue68EpProdExitN, issue68EpIdxNow, array.get(issue68EpProdExitN, issue68EpIdxNow) + 1)
            else if issue68EpTimedOut
                array.set(issue68EpTimeoutN, issue68EpIdxNow, array.get(issue68EpTimeoutN, issue68EpIdxNow) + 1)

            array.set(issue68EpHeldSum, issue68EpIdxNow, array.get(issue68EpHeldSum, issue68EpIdxNow) + issue68EpHeldBars)
            array.set(issue68EpHeldMax, issue68EpIdxNow, math.max(array.get(issue68EpHeldMax, issue68EpIdxNow), issue68EpHeldBars))
            issue68EpStage := 0
            issue68EpKind := 0
            issue68EpHeldBars := 0

    // Then allow this bar to open a new episode. This preserves chronology and
    // never re-labels an anchor from later information.
    if issue68EpStage == 0
        if issue68HysHoldingS1
            issue68EpStage := 1
            issue68EpKind := issue68S14FreshS1 ? 1 : 2
            issue68EpHeldBars := 1
            int issue68EpIdxS1 = f_issue68EpIdx(issue68EpStage, issue68EpKind)
            array.set(issue68EpN, issue68EpIdxS1, array.get(issue68EpN, issue68EpIdxS1) + 1)
        else if issue68HysHoldingS4
            issue68EpStage := 4
            issue68EpKind := issue68S14FreshS4 ? 1 : 2
            issue68EpHeldBars := 1
            int issue68EpIdxS4 = f_issue68EpIdx(issue68EpStage, issue68EpKind)
            array.set(issue68EpN, issue68EpIdxS4, array.get(issue68EpN, issue68EpIdxS4) + 1)

int issue68EpActiveIdx = issue68EpStage != 0 ? f_issue68EpIdx(issue68EpStage, issue68EpKind) : -1

var table tEp = table.new(position.middle_right, 6, 15, border_width=1)
if barstate.islast
    if showIssue68EpTable
        table.cell(tEp, 0, 0, "GRACE EPISODES", bgcolor=colNeutral, text_color=color.white)
        table.cell(tEp, 1, 0, "S1 FRESH", bgcolor=colGreen, text_color=color.white)
        table.cell(tEp, 2, 0, "S1 OTHER", bgcolor=colNeutral, text_color=color.white)
        table.cell(tEp, 3, 0, "S4 FRESH", bgcolor=colGreen, text_color=color.white)
        table.cell(tEp, 4, 0, "S4 OTHER", bgcolor=colNeutral, text_color=color.white)
        table.cell(tEp, 5, 0, "READ", bgcolor=colNeutral, text_color=color.white)

        for i = 0 to 3
            int n = array.get(issue68EpN, i)
            int rec = array.get(issue68EpRecoverN, i)
            int tout = array.get(issue68EpTimeoutN, i)
            int pexit = array.get(issue68EpProdExitN, i)
            int opp = array.get(issue68EpOppositeN, i)
            int comp = rec + tout + pexit + opp
            int hsum = array.get(issue68EpHeldSum, i)
            int hmax = array.get(issue68EpHeldMax, i)
            int col = i + 1
            table.cell(tEp, col, 1, str.tostring(n), bgcolor=colNeutral, text_color=color.white)
            table.cell(tEp, col, 2, str.tostring(comp), bgcolor=colNeutral, text_color=color.white)
            table.cell(tEp, col, 3, str.tostring(rec) + " / " + f_issue68EpPct(rec, comp), bgcolor=colGreen, text_color=color.white)
            table.cell(tEp, col, 4, str.tostring(tout) + " / " + f_issue68EpPct(tout, comp), bgcolor=colNeutral, text_color=color.white)
            table.cell(tEp, col, 5, str.tostring(pexit) + " / " + f_issue68EpPct(pexit, comp), bgcolor=colNeutral, text_color=color.white)
            table.cell(tEp, col, 6, str.tostring(opp) + " / " + f_issue68EpPct(opp, comp), bgcolor=colNeutral, text_color=color.white)
            table.cell(tEp, col, 7, f_issue68EpAvg(hsum, comp), bgcolor=colNeutral, text_color=color.white)
            table.cell(tEp, col, 8, str.tostring(hmax), bgcolor=hmax < confirmBars ? colGreen : colRed, text_color=color.white)
            table.cell(tEp, col, 9, issue68EpActiveIdx == i ? "1" : "0", bgcolor=issue68EpActiveIdx == i ? colNeutral : colGreen, text_color=color.white)

        table.cell(tEp, 0, 1, "Episodes", bgcolor=colNeutral, text_color=color.white)
        table.cell(tEp, 0, 2, "Completed", bgcolor=colNeutral, text_color=color.white)
        table.cell(tEp, 0, 3, "RECOVER", bgcolor=colGreen, text_color=color.white)
        table.cell(tEp, 0, 4, "TIMEOUT", bgcolor=colNeutral, text_color=color.white)
        table.cell(tEp, 0, 5, "PROD EXIT", bgcolor=colNeutral, text_color=color.white)
        table.cell(tEp, 0, 6, "OPPOSITE", bgcolor=colNeutral, text_color=color.white)
        table.cell(tEp, 0, 7, "Avg held bars", bgcolor=colNeutral, text_color=color.white)
        table.cell(tEp, 0, 8, "Max held bars", bgcolor=colNeutral, text_color=color.white)
        table.cell(tEp, 0, 9, "ACTIVE at end", bgcolor=colNeutral, text_color=color.white)

        int s1FreshComp = array.get(issue68EpRecoverN, 0) + array.get(issue68EpTimeoutN, 0) + array.get(issue68EpProdExitN, 0) + array.get(issue68EpOppositeN, 0)
        int s1OtherComp = array.get(issue68EpRecoverN, 1) + array.get(issue68EpTimeoutN, 1) + array.get(issue68EpProdExitN, 1) + array.get(issue68EpOppositeN, 1)
        int s4FreshComp = array.get(issue68EpRecoverN, 2) + array.get(issue68EpTimeoutN, 2) + array.get(issue68EpProdExitN, 2) + array.get(issue68EpOppositeN, 2)
        int s4OtherComp = array.get(issue68EpRecoverN, 3) + array.get(issue68EpTimeoutN, 3) + array.get(issue68EpProdExitN, 3) + array.get(issue68EpOppositeN, 3)
        int s1Comp = s1FreshComp + s1OtherComp
        int s4Comp = s4FreshComp + s4OtherComp
        int s1Rec = array.get(issue68EpRecoverN, 0) + array.get(issue68EpRecoverN, 1)
        int s4Rec = array.get(issue68EpRecoverN, 2) + array.get(issue68EpRecoverN, 3)

        table.cell(tEp, 0, 10, "Pooled recover", bgcolor=colGreen, text_color=color.white)
        table.cell(tEp, 1, 10, "S1 " + f_issue68EpPct(s1Rec, s1Comp), bgcolor=s1Comp > 0 and 2 * s1Rec > s1Comp ? colGreen : colRed, text_color=color.white)
        table.cell(tEp, 3, 10, "S4 " + f_issue68EpPct(s4Rec, s4Comp), bgcolor=s4Comp > 0 and 2 * s4Rec > s4Comp ? colGreen : colRed, text_color=color.white)
        table.cell(tEp, 5, 10, ">50% required", bgcolor=colNeutral, text_color=color.white)

        float s1FreshRecPct = s1FreshComp > 0 ? 100.0 * array.get(issue68EpRecoverN, 0) / s1FreshComp : na
        float s1OtherRecPct = s1OtherComp > 0 ? 100.0 * array.get(issue68EpRecoverN, 1) / s1OtherComp : na
        float s4FreshRecPct = s4FreshComp > 0 ? 100.0 * array.get(issue68EpRecoverN, 2) / s4FreshComp : na
        float s4OtherRecPct = s4OtherComp > 0 ? 100.0 * array.get(issue68EpRecoverN, 3) / s4OtherComp : na
        bool s1FreshGeOther = not na(s1FreshRecPct) and not na(s1OtherRecPct) and s1FreshRecPct >= s1OtherRecPct
        bool s4FreshGeOther = not na(s4FreshRecPct) and not na(s4OtherRecPct) and s4FreshRecPct >= s4OtherRecPct

        table.cell(tEp, 0, 11, "Fresh >= Other recover", bgcolor=colGreen, text_color=color.white)
        table.cell(tEp, 1, 11, na(s1FreshRecPct) ? "NA" : str.tostring(s1FreshRecPct, "#.##") + "%", bgcolor=s1FreshGeOther ? colGreen : colRed, text_color=color.white)
        table.cell(tEp, 2, 11, na(s1OtherRecPct) ? "NA" : str.tostring(s1OtherRecPct, "#.##") + "%", bgcolor=colNeutral, text_color=color.white)
        table.cell(tEp, 3, 11, na(s4FreshRecPct) ? "NA" : str.tostring(s4FreshRecPct, "#.##") + "%", bgcolor=s4FreshGeOther ? colGreen : colRed, text_color=color.white)
        table.cell(tEp, 4, 11, na(s4OtherRecPct) ? "NA" : str.tostring(s4OtherRecPct, "#.##") + "%", bgcolor=colNeutral, text_color=color.white)
        table.cell(tEp, 5, 11, "anchor quality", bgcolor=colNeutral, text_color=color.white)

        bool maxContractOk = array.get(issue68EpHeldMax, 0) < confirmBars and array.get(issue68EpHeldMax, 1) < confirmBars and array.get(issue68EpHeldMax, 2) < confirmBars and array.get(issue68EpHeldMax, 3) < confirmBars
        table.cell(tEp, 0, 12, "Lifecycle contract", bgcolor=colGreen, text_color=color.white)
        table.cell(tEp, 1, 12, "confirmBars=" + str.tostring(confirmBars), bgcolor=colNeutral, text_color=color.white)
        table.cell(tEp, 3, 12, maxContractOk ? "PASS" : "FAIL", bgcolor=maxContractOk ? colGreen : colRed, text_color=color.white)
        table.cell(tEp, 5, 12, "max < confirmBars", bgcolor=colNeutral, text_color=color.white)

        table.cell(tEp, 0, 13, "SEMANTIC", bgcolor=colGreen, text_color=color.white)
        table.cell(tEp, 1, 13, "bridge noise?", bgcolor=colGreen, text_color=color.white)
        table.cell(tEp, 2, 13, "delay exit?", bgcolor=colNeutral, text_color=color.white)
        table.cell(tEp, 3, 13, "EXACT MIRROR", bgcolor=colGreen, text_color=color.white)
        table.cell(tEp, 5, 13, "NO LOOKAHEAD", bgcolor=colGreen, text_color=color.white)

        table.cell(tEp, 0, 14, "READ", bgcolor=colNeutral, text_color=color.white)
        table.cell(tEp, 1, 14, "RECOVER >50%?", bgcolor=colGreen, text_color=color.white)
        table.cell(tEp, 2, 14, "Fresh >= Other?", bgcolor=colGreen, text_color=color.white)
        table.cell(tEp, 3, 14, "NO TUNING", bgcolor=colRed, text_color=color.white)
        table.cell(tEp, 5, 14, "FROZEN C-2", bgcolor=colNeutral, text_color=color.white)
    else
        table.clear(tEp, 0, 0, 5, 14)
'''


def generate(source: Path) -> str:
    out = hys.generate(source)
    out = replace_once(out, hys.AUDIT_DECL, AUDIT_DECL)
    out = replace_once(
        out,
        'showIssue68HysTable = input.bool(true, "顯示 Stateful CTX 表", group=groupIssue68Hys)',
        'showIssue68HysTable = input.bool(false, "顯示 Stateful CTX 表", group=groupIssue68Hys)',
    )
    out = out.rstrip() + BODY + "\n"
    required = [
        "GRACE EPISODES",
        "RECOVER",
        "TIMEOUT",
        "PROD EXIT",
        "OPPOSITE",
        "ACTIVE at end",
        "Pooled recover",
        "Fresh >= Other recover",
        "max < confirmBars",
        "NO LOOKAHEAD",
        "EXACT MIRROR",
        "NO TUNING",
    ]
    for token in required:
        if token not in out:
            raise RuntimeError(f"missing grace-episode audit token: {token}")
    if "strategy.entry" in out or "strategy.close" in out:
        raise RuntimeError("grace-episode audit leaked strategy order logic")
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
