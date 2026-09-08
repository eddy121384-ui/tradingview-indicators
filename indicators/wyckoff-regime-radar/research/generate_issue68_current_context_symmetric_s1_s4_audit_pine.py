#!/usr/bin/env python3
"""Generate Issue #68 symmetric S1/S4 current-context preservation audit Pine."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_downex_current_context_fresh_s1_preserve_audit_pine as s1
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 Symmetric S1/S4 CTX", shorttitle="ChaseRisk #68 S1S4", overlay=false, precision=3)'

BODY = r'''

// ============================================================================
// Issue #68 Symmetric S1/S4 Current-Context Audit.
// Exact paired mirror: S1 DownEx x current Bear; S4 UpEx x current Bull.
// Fresh-S1 path<=0; Fresh-S4 path>=0. No lookahead. No tuning. NO PNL.
// PRODUCTION C-2 FROZEN.
// ============================================================================

groupIssue68S14 = "Issue #68｜Symmetric S1/S4 CTX"
showIssue68S14Table = input.bool(true, "顯示 Symmetric S1/S4 表", group=groupIssue68S14)

f_issue68S14Top(float accX, float distX) =>
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

float issue68S14CurrentBullGate = f_gate(bullBg, 35.0, 75.0)
float issue68S14BoundUpGate = math.min(upsideExhaustionGate, issue68S14CurrentBullGate)
float issue68S14CtxDistGate = rangeGate * bullBackgroundForDistGate * issue68S14BoundUpGate * resistanceHoldingGate * nonMarkupContinuationGate
float issue68S14DistMult = distVolMult * distMtfMult * distDivMult
float issue68S14CtxDistEff = distRaw * issue68S14CtxDistGate * issue68S14DistMult

bool issue68S14Valid = issue68S1PReady and not na(issue68S1PCtxAccEff) and not na(issue68S14CtxDistEff) and not na(topId) and not na(bearBg) and not na(bullBg) and not na(downsideExhaustion) and not na(upsideExhaustion)
int issue68S14Top = issue68S14Valid ? f_issue68S14Top(issue68S1PCtxAccEff, issue68S14CtxDistEff) : na

bool issue68S14ProdS1 = issue68S14Valid and topId == 1
bool issue68S14ProdS4 = issue68S14Valid and topId == 4
bool issue68S14FreshS1 = issue68S14ProdS1 and bearBg >= 35.0 and downsideExhaustion >= 35.0 and close - close[20] <= 0.0
bool issue68S14FreshS4 = issue68S14ProdS4 and bullBg >= 35.0 and upsideExhaustion >= 35.0 and close - close[20] >= 0.0
bool issue68S14OtherS1 = issue68S14ProdS1 and not issue68S14FreshS1
bool issue68S14OtherS4 = issue68S14ProdS4 and not issue68S14FreshS4

bool issue68S14FreshS1Retained = issue68S14FreshS1 and issue68S14Top == 1
bool issue68S14FreshS4Retained = issue68S14FreshS4 and issue68S14Top == 4
bool issue68S14FreshS1Lost = issue68S14FreshS1 and issue68S14Top != 1
bool issue68S14FreshS4Lost = issue68S14FreshS4 and issue68S14Top != 4
bool issue68S14OtherS1Removed = issue68S14OtherS1 and issue68S14Top != 1
bool issue68S14OtherS4Removed = issue68S14OtherS4 and issue68S14Top != 4

bool issue68S14FreshS1LostBull = issue68S14FreshS1Lost and (issue68S14Top == 2 or issue68S14Top == 3)
bool issue68S14FreshS1LostNeutral = issue68S14FreshS1Lost and issue68S14Top == 4
bool issue68S14FreshS1LostBear = issue68S14FreshS1Lost and (issue68S14Top == 5 or issue68S14Top == 6)
bool issue68S14FreshS4LostBull = issue68S14FreshS4Lost and (issue68S14Top == 2 or issue68S14Top == 3)
bool issue68S14FreshS4LostNeutral = issue68S14FreshS4Lost and issue68S14Top == 1
bool issue68S14FreshS4LostBear = issue68S14FreshS4Lost and (issue68S14Top == 5 or issue68S14Top == 6)

bool issue68S14CapBindS1 = issue68S14FreshS1 and downsideExhaustionGate > issue68S1PCurrentBearGate
bool issue68S14CapBindS4 = issue68S14FreshS4 and upsideExhaustionGate > issue68S14CurrentBullGate

bool issue68S14Changed = issue68S14Valid and issue68S14Top != topId
bool issue68S14EnterS1 = issue68S14Changed and topId != 1 and issue68S14Top == 1
bool issue68S14EnterS4 = issue68S14Changed and topId != 4 and issue68S14Top == 4
bool issue68S14ChangedBull = issue68S14Changed and (issue68S14Top == 2 or issue68S14Top == 3)
bool issue68S14ChangedNeutral = issue68S14Changed and (issue68S14Top == 1 or issue68S14Top == 4)
bool issue68S14ChangedBear = issue68S14Changed and (issue68S14Top == 5 or issue68S14Top == 6)

var int issue68S14ValidN = 0
var int issue68S14ProdS1N = 0
var int issue68S14ProdS4N = 0
var int issue68S14FreshS1N = 0
var int issue68S14FreshS4N = 0
var int issue68S14OtherS1N = 0
var int issue68S14OtherS4N = 0
var int issue68S14FreshS1RetainedN = 0
var int issue68S14FreshS4RetainedN = 0
var int issue68S14FreshS1LostN = 0
var int issue68S14FreshS4LostN = 0
var int issue68S14OtherS1RemovedN = 0
var int issue68S14OtherS4RemovedN = 0
var int issue68S14FreshS1LostBullN = 0
var int issue68S14FreshS1LostNeutralN = 0
var int issue68S14FreshS1LostBearN = 0
var int issue68S14FreshS4LostBullN = 0
var int issue68S14FreshS4LostNeutralN = 0
var int issue68S14FreshS4LostBearN = 0
var int issue68S14CapBindS1N = 0
var int issue68S14CapBindS4N = 0
var int issue68S14ChangedN = 0
var int issue68S14EnterS1N = 0
var int issue68S14EnterS4N = 0
var int issue68S14ChangedBullN = 0
var int issue68S14ChangedNeutralN = 0
var int issue68S14ChangedBearN = 0

var float issue68S14S1ProdGateSum = 0.0
var float issue68S14S1CtxGateSum = 0.0
var float issue68S14S1CurrentGateSum = 0.0
var float issue68S14S1ExGateSum = 0.0
var float issue68S14S1BgSum = 0.0
var float issue68S14S1ExSum = 0.0
var float issue68S14S4ProdGateSum = 0.0
var float issue68S14S4CtxGateSum = 0.0
var float issue68S14S4CurrentGateSum = 0.0
var float issue68S14S4ExGateSum = 0.0
var float issue68S14S4BgSum = 0.0
var float issue68S14S4ExSum = 0.0

var int issue68S14FreshS1Run = 0
var int issue68S14FreshS1RunMax = 0
var int issue68S14KeepS1Run = 0
var int issue68S14KeepS1RunMax = 0
var int issue68S14FreshS4Run = 0
var int issue68S14FreshS4RunMax = 0
var int issue68S14KeepS4Run = 0
var int issue68S14KeepS4RunMax = 0

if issue68S14Valid
    issue68S14ValidN += 1
    issue68S14ProdS1N += issue68S14ProdS1 ? 1 : 0
    issue68S14ProdS4N += issue68S14ProdS4 ? 1 : 0
    issue68S14FreshS1N += issue68S14FreshS1 ? 1 : 0
    issue68S14FreshS4N += issue68S14FreshS4 ? 1 : 0
    issue68S14OtherS1N += issue68S14OtherS1 ? 1 : 0
    issue68S14OtherS4N += issue68S14OtherS4 ? 1 : 0
    issue68S14FreshS1RetainedN += issue68S14FreshS1Retained ? 1 : 0
    issue68S14FreshS4RetainedN += issue68S14FreshS4Retained ? 1 : 0
    issue68S14FreshS1LostN += issue68S14FreshS1Lost ? 1 : 0
    issue68S14FreshS4LostN += issue68S14FreshS4Lost ? 1 : 0
    issue68S14OtherS1RemovedN += issue68S14OtherS1Removed ? 1 : 0
    issue68S14OtherS4RemovedN += issue68S14OtherS4Removed ? 1 : 0
    issue68S14FreshS1LostBullN += issue68S14FreshS1LostBull ? 1 : 0
    issue68S14FreshS1LostNeutralN += issue68S14FreshS1LostNeutral ? 1 : 0
    issue68S14FreshS1LostBearN += issue68S14FreshS1LostBear ? 1 : 0
    issue68S14FreshS4LostBullN += issue68S14FreshS4LostBull ? 1 : 0
    issue68S14FreshS4LostNeutralN += issue68S14FreshS4LostNeutral ? 1 : 0
    issue68S14FreshS4LostBearN += issue68S14FreshS4LostBear ? 1 : 0
    issue68S14CapBindS1N += issue68S14CapBindS1 ? 1 : 0
    issue68S14CapBindS4N += issue68S14CapBindS4 ? 1 : 0
    issue68S14ChangedN += issue68S14Changed ? 1 : 0
    issue68S14EnterS1N += issue68S14EnterS1 ? 1 : 0
    issue68S14EnterS4N += issue68S14EnterS4 ? 1 : 0
    issue68S14ChangedBullN += issue68S14ChangedBull ? 1 : 0
    issue68S14ChangedNeutralN += issue68S14ChangedNeutral ? 1 : 0
    issue68S14ChangedBearN += issue68S14ChangedBear ? 1 : 0

    if issue68S14FreshS1
        issue68S14S1ProdGateSum += accGate
        issue68S14S1CtxGateSum += issue68S1PCtxAccGate
        issue68S14S1CurrentGateSum += issue68S1PCurrentBearGate
        issue68S14S1ExGateSum += downsideExhaustionGate
        issue68S14S1BgSum += bearBg
        issue68S14S1ExSum += downsideExhaustion

    if issue68S14FreshS4
        issue68S14S4ProdGateSum += distGate
        issue68S14S4CtxGateSum += issue68S14CtxDistGate
        issue68S14S4CurrentGateSum += issue68S14CurrentBullGate
        issue68S14S4ExGateSum += upsideExhaustionGate
        issue68S14S4BgSum += bullBg
        issue68S14S4ExSum += upsideExhaustion

    if issue68S14FreshS1
        issue68S14FreshS1Run += 1
        issue68S14FreshS1RunMax := math.max(issue68S14FreshS1RunMax, issue68S14FreshS1Run)
    else
        issue68S14FreshS1Run := 0
    if issue68S14FreshS1Retained
        issue68S14KeepS1Run += 1
        issue68S14KeepS1RunMax := math.max(issue68S14KeepS1RunMax, issue68S14KeepS1Run)
    else
        issue68S14KeepS1Run := 0

    if issue68S14FreshS4
        issue68S14FreshS4Run += 1
        issue68S14FreshS4RunMax := math.max(issue68S14FreshS4RunMax, issue68S14FreshS4Run)
    else
        issue68S14FreshS4Run := 0
    if issue68S14FreshS4Retained
        issue68S14KeepS4Run += 1
        issue68S14KeepS4RunMax := math.max(issue68S14KeepS4RunMax, issue68S14KeepS4Run)
    else
        issue68S14KeepS4Run := 0

var table tS14 = table.new(position.middle_right, 5, 18, border_width=1)
if barstate.islast
    if showIssue68S14Table
        table.cell(tS14, 0, 0, "SYMMETRIC CTX", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 1, 0, syminfo.ticker, bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 2, 0, "S1 ACC", bgcolor=colGreen, text_color=color.white)
        table.cell(tS14, 3, 0, "S4 DIST", bgcolor=colRed, text_color=color.white)
        table.cell(tS14, 4, 0, "PAIRED", bgcolor=colNeutral, text_color=color.white)

        table.cell(tS14, 0, 1, "Valid bars", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 1, 1, str.tostring(issue68S14ValidN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 2, 1, "Bear/DownEx", bgcolor=colGreen, text_color=color.white)
        table.cell(tS14, 3, 1, "Bull/UpEx", bgcolor=colRed, text_color=color.white)
        table.cell(tS14, 4, 1, "NO LOOKAHEAD", bgcolor=colGreen, text_color=color.white)

        table.cell(tS14, 0, 2, "PROD TOP", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 2, 2, str.tostring(issue68S14ProdS1N), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 3, 2, str.tostring(issue68S14ProdS4N), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 4, 2, "baseline", bgcolor=colNeutral, text_color=color.white)

        table.cell(tS14, 0, 3, "Fresh", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 2, 3, str.tostring(issue68S14FreshS1N) + " / " + f_issue68S1PFmtPct(issue68S14FreshS1N, issue68S14ProdS1N), bgcolor=colGreen, text_color=color.white)
        table.cell(tS14, 3, 3, str.tostring(issue68S14FreshS4N) + " / " + f_issue68S1PFmtPct(issue68S14FreshS4N, issue68S14ProdS4N), bgcolor=colGreen, text_color=color.white)
        table.cell(tS14, 4, 3, "semantic anchors", bgcolor=colGreen, text_color=color.white)

        table.cell(tS14, 0, 4, "Fresh retained", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 2, 4, str.tostring(issue68S14FreshS1RetainedN) + " / " + f_issue68S1PFmtPct(issue68S14FreshS1RetainedN, issue68S14FreshS1N), bgcolor=colGreen, text_color=color.white)
        table.cell(tS14, 3, 4, str.tostring(issue68S14FreshS4RetainedN) + " / " + f_issue68S1PFmtPct(issue68S14FreshS4RetainedN, issue68S14FreshS4N), bgcolor=colGreen, text_color=color.white)
        table.cell(tS14, 4, 4, "selectivity", bgcolor=colGreen, text_color=color.white)

        table.cell(tS14, 0, 5, "Fresh lost", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 2, 5, str.tostring(issue68S14FreshS1LostN) + " / " + f_issue68S1PFmtPct(issue68S14FreshS1LostN, issue68S14FreshS1N), bgcolor=issue68S14FreshS1LostN == 0 ? colGreen : colRed, text_color=color.white)
        table.cell(tS14, 3, 5, str.tostring(issue68S14FreshS4LostN) + " / " + f_issue68S1PFmtPct(issue68S14FreshS4LostN, issue68S14FreshS4N), bgcolor=issue68S14FreshS4LostN == 0 ? colGreen : colRed, text_color=color.white)
        table.cell(tS14, 4, 5, "inspect", bgcolor=colNeutral, text_color=color.white)

        table.cell(tS14, 0, 6, "Other removed", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 2, 6, str.tostring(issue68S14OtherS1RemovedN) + " / " + f_issue68S1PFmtPct(issue68S14OtherS1RemovedN, issue68S14OtherS1N), bgcolor=colGreen, text_color=color.white)
        table.cell(tS14, 3, 6, str.tostring(issue68S14OtherS4RemovedN) + " / " + f_issue68S1PFmtPct(issue68S14OtherS4RemovedN, issue68S14OtherS4N), bgcolor=colGreen, text_color=color.white)
        table.cell(tS14, 4, 6, "stale contrast", bgcolor=colGreen, text_color=color.white)

        table.cell(tS14, 0, 7, "Fresh loss B/N/R", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 2, 7, str.tostring(issue68S14FreshS1LostBullN) + "/" + str.tostring(issue68S14FreshS1LostNeutralN) + "/" + str.tostring(issue68S14FreshS1LostBearN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 3, 7, str.tostring(issue68S14FreshS4LostBullN) + "/" + str.tostring(issue68S14FreshS4LostNeutralN) + "/" + str.tostring(issue68S14FreshS4LostBearN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 4, 7, "Bull/Neutral/Bear", bgcolor=colNeutral, text_color=color.white)

        table.cell(tS14, 0, 8, "Gate avg PROD>CTX", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 2, 8, f_issue68S1PFmt(f_issue68S1PAvg(issue68S14S1ProdGateSum, issue68S14FreshS1N)) + ">" + f_issue68S1PFmt(f_issue68S1PAvg(issue68S14S1CtxGateSum, issue68S14FreshS1N)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 3, 8, f_issue68S1PFmt(f_issue68S1PAvg(issue68S14S4ProdGateSum, issue68S14FreshS4N)) + ">" + f_issue68S1PFmt(f_issue68S1PAvg(issue68S14S4CtxGateSum, issue68S14FreshS4N)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 4, 8, "only exhaustion", bgcolor=colNeutral, text_color=color.white)

        table.cell(tS14, 0, 9, "Cap bind Fresh", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 2, 9, f_issue68S1PFmtPct(issue68S14CapBindS1N, issue68S14FreshS1N), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 3, 9, f_issue68S1PFmtPct(issue68S14CapBindS4N, issue68S14FreshS4N), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 4, 9, "breadth", bgcolor=colNeutral, text_color=color.white)

        table.cell(tS14, 0, 10, "CurrentGate / ExGate", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 2, 10, f_issue68S1PFmt(f_issue68S1PAvg(issue68S14S1CurrentGateSum, issue68S14FreshS1N)) + "/" + f_issue68S1PFmt(f_issue68S1PAvg(issue68S14S1ExGateSum, issue68S14FreshS1N)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 3, 10, f_issue68S1PFmt(f_issue68S1PAvg(issue68S14S4CurrentGateSum, issue68S14FreshS4N)) + "/" + f_issue68S1PFmt(f_issue68S1PAvg(issue68S14S4ExGateSum, issue68S14FreshS4N)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 4, 10, "current/exhaust", bgcolor=colNeutral, text_color=color.white)

        table.cell(tS14, 0, 11, "Bg / Exhaust score", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 2, 11, f_issue68S1PFmt(f_issue68S1PAvg(issue68S14S1BgSum, issue68S14FreshS1N)) + "/" + f_issue68S1PFmt(f_issue68S1PAvg(issue68S14S1ExSum, issue68S14FreshS1N)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 3, 11, f_issue68S1PFmt(f_issue68S1PAvg(issue68S14S4BgSum, issue68S14FreshS4N)) + "/" + f_issue68S1PFmt(f_issue68S1PAvg(issue68S14S4ExSum, issue68S14FreshS4N)), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 4, 11, "raw scores", bgcolor=colNeutral, text_color=color.white)

        table.cell(tS14, 0, 12, "Fresh run / retained", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 2, 12, str.tostring(issue68S14FreshS1RunMax) + "/" + str.tostring(issue68S14KeepS1RunMax), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 3, 12, str.tostring(issue68S14FreshS4RunMax) + "/" + str.tostring(issue68S14KeepS4RunMax), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 4, 12, "continuity", bgcolor=colNeutral, text_color=color.white)

        table.cell(tS14, 0, 13, "Global TOP changed", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 1, 13, str.tostring(issue68S14ChangedN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 2, 13, f_issue68S1PFmtPct(issue68S14ChangedN, issue68S14ValidN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 3, 13, "full history", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 4, 13, "churn", bgcolor=colNeutral, text_color=color.white)

        table.cell(tS14, 0, 14, "Enter S1 / S4", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 2, 14, str.tostring(issue68S14EnterS1N), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 3, 14, str.tostring(issue68S14EnterS4N), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 4, 14, "cross-release", bgcolor=colNeutral, text_color=color.white)

        table.cell(tS14, 0, 15, "Changed dest B/N/R", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 1, 15, str.tostring(issue68S14ChangedBullN) + "/" + str.tostring(issue68S14ChangedNeutralN) + "/" + str.tostring(issue68S14ChangedBearN), bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 4, 15, "Bull/Neutral/Bear", bgcolor=colNeutral, text_color=color.white)

        table.cell(tS14, 0, 16, "ALGEBRA", bgcolor=colGreen, text_color=color.white)
        table.cell(tS14, 2, 16, "min(DownEx,Bear)", bgcolor=colGreen, text_color=color.white)
        table.cell(tS14, 3, 16, "min(UpEx,Bull)", bgcolor=colGreen, text_color=color.white)
        table.cell(tS14, 4, 16, "EXACT MIRROR", bgcolor=colGreen, text_color=color.white)

        table.cell(tS14, 0, 17, "READ", bgcolor=colNeutral, text_color=color.white)
        table.cell(tS14, 2, 17, "Fresh keep?", bgcolor=colGreen, text_color=color.white)
        table.cell(tS14, 3, 17, "Fresh keep?", bgcolor=colGreen, text_color=color.white)
        table.cell(tS14, 4, 17, "NO TUNING", bgcolor=colRed, text_color=color.white)
    else
        table.clear(tS14, 0, 0, 4, 17)
'''


def generate(source: Path) -> str:
    out = s1.generate(source)
    out = replace_once(out, s1.AUDIT_DECL, AUDIT_DECL)
    out = replace_once(
        out,
        'showIssue68S1PTable = input.bool(true, "顯示 Fresh-S1 Preserve 表", group=groupIssue68S1P)',
        'showIssue68S1PTable = input.bool(false, "顯示 Fresh-S1 Preserve 表", group=groupIssue68S1P)',
    )
    out = out.rstrip() + BODY + "\n"
    required = [
        "min(downsideExhaustionGate, issue68S1PCurrentBearGate)",
        "math.min(upsideExhaustionGate, issue68S14CurrentBullGate)",
        "close - close[20] <= 0.0",
        "close - close[20] >= 0.0",
        "EXACT MIRROR",
        "Fresh retained",
        "Other removed",
    ]
    for token in required:
        if token not in out:
            raise RuntimeError(f"missing symmetric audit token: {token}")
    if "strategy.entry" in out or "strategy.close" in out:
        raise RuntimeError("symmetric audit leaked strategy order logic")
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
