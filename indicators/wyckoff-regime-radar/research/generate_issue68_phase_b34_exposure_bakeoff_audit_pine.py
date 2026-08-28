#!/usr/bin/env python3
"""Generate Issue #68 Phase B3.4 no-PnL exposure-policy bakeoff audit Pine."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_phase_b_lifecycle_pine as phase_b
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 Exposure B3.4 Bakeoff", shorttitle="ChaseRisk #68 B34", overlay=false, precision=2)'

B34_BODY = r'''

// ============================================================================
// Issue #68 Phase B3.4 preregistered Exposure Policy Bakeoff.
// Core Bias is frozen B3.3 regime memory. Exposure candidates are NO-PNL.
// A = Formal trend family; B = Flat Action authorization;
// C = Flat Action entry + mirrored Pace defensive-flat state machine.
// ============================================================================

groupIssue68B34 = "Issue #68｜Exposure B3.4 Bakeoff"
showIssue68B34StageBg = input.bool(true, "顯示 Formal Stage 背景", group=groupIssue68B34)
showIssue68B34Bias = input.bool(true, "顯示 Core Bias lane", group=groupIssue68B34)
showIssue68B34A = input.bool(true, "顯示 A｜Formal trend-family", group=groupIssue68B34)
showIssue68B34B = input.bool(true, "顯示 B｜Flat Action authorization", group=groupIssue68B34)
showIssue68B34C = input.bool(true, "顯示 C｜Flat Action + Pace stateful", group=groupIssue68B34)

issue68B34Ready = bar_index >= rankLen - 1

// --- Frozen B3.3 Core Bias Memory ---
var int issue68B34Bias = 0
int issue68B34BiasBefore = issue68B34Bias
if issue68B34Ready
    int issue68B34Stage = formalId
    int issue68B34BiasAfter = issue68B34BiasBefore
    if issue68B34BiasBefore == 0
        if issue68B34Stage == 2
            issue68B34BiasAfter := 1
        else if issue68B34Stage == 5
            issue68B34BiasAfter := -1
        else
            issue68B34BiasAfter := 0
    else if issue68B34BiasBefore == 1
        issue68B34BiasAfter := issue68B34Stage == 5 or issue68B34Stage == 6 ? -1 : 1
    else if issue68B34BiasBefore == -1
        issue68B34BiasAfter := issue68B34Stage == 2 or issue68B34Stage == 3 ? 1 : -1
    issue68B34Bias := issue68B34BiasAfter
else
    issue68B34Bias := 0

// --- Candidate A: Formal trend-family exposure ---
int issue68B34A = 0
if issue68B34Ready
    if issue68B34Bias == 1 and (formalId == 2 or formalId == 3)
        issue68B34A := 1
    else if issue68B34Bias == -1 and (formalId == 5 or formalId == 6)
        issue68B34A := -1

// --- Candidate B: existing Flat Action authorization only ---
int issue68B34B = 0
if issue68B34Ready
    if issue68B34Bias == 1 and (flatActionLevel == 2 or flatActionLevel == 3)
        issue68B34B := 1
    else if issue68B34Bias == -1 and (flatActionLevel == 4 or flatActionLevel == 5)
        issue68B34B := -1

// --- Candidate C: Flat Action entry/re-entry + mirrored Pace defensive flat ---
bool issue68B34LongDefensive = paceCode == 0 or paceCode == 40 or paceCode == 70 or paceCode == 71 or paceCode == 75
bool issue68B34ShortDefensive = paceCode == 0 or paceCode == 15 or paceCode == 70 or paceCode == 71 or paceCode == 74
bool issue68B34LongEntryOk = flatActionLevel == 2 or flatActionLevel == 3
bool issue68B34ShortEntryOk = flatActionLevel == 4 or flatActionLevel == 5

var int issue68B34C = 0
int issue68B34CBefore = issue68B34C
int issue68B34CAfter = issue68B34CBefore
if issue68B34Ready
    if issue68B34Bias == 0
        issue68B34CAfter := 0
    else if issue68B34CBefore != 0 and issue68B34CBefore != issue68B34Bias
        // Bias reversal forces an observation bar; no direct executable flip.
        issue68B34CAfter := 0
    else if issue68B34CBefore == 0
        if issue68B34Bias == 1 and issue68B34LongEntryOk
            issue68B34CAfter := 1
        else if issue68B34Bias == -1 and issue68B34ShortEntryOk
            issue68B34CAfter := -1
        else
            issue68B34CAfter := 0
    else if issue68B34CBefore == 1
        issue68B34CAfter := issue68B34LongDefensive ? 0 : 1
    else if issue68B34CBefore == -1
        issue68B34CAfter := issue68B34ShortDefensive ? 0 : -1
    issue68B34C := issue68B34CAfter
else
    issue68B34C := 0

// Hard directional invariants: no candidate may oppose frozen Core Bias.
bool issue68B34ViolationA = (issue68B34A == 1 and issue68B34Bias != 1) or (issue68B34A == -1 and issue68B34Bias != -1)
bool issue68B34ViolationB = (issue68B34B == 1 and issue68B34Bias != 1) or (issue68B34B == -1 and issue68B34Bias != -1)
bool issue68B34ViolationC = (issue68B34C == 1 and issue68B34Bias != 1) or (issue68B34C == -1 and issue68B34Bias != -1)

// Cumulative semantic counters for Data Window only; not performance metrics.
var int issue68B34Bars = 0
var int issue68B34FlatA = 0
var int issue68B34FlatB = 0
var int issue68B34FlatC = 0
var int issue68B34TransitionsA = 0
var int issue68B34TransitionsB = 0
var int issue68B34TransitionsC = 0
if issue68B34Ready
    issue68B34Bars += 1
    issue68B34FlatA += issue68B34A == 0 ? 1 : 0
    issue68B34FlatB += issue68B34B == 0 ? 1 : 0
    issue68B34FlatC += issue68B34C == 0 ? 1 : 0
    if issue68B34Ready[1]
        issue68B34TransitionsA += issue68B34A != issue68B34A[1] ? 1 : 0
        issue68B34TransitionsB += issue68B34B != issue68B34B[1] ? 1 : 0
        issue68B34TransitionsC += issue68B34C != issue68B34C[1] ? 1 : 0

f_issue68B34Color(int x) => x == 1 ? colGreen : x == -1 ? colRed : colNeutral
f_issue68B34Lane(float center, int x) => center + float(x) * 0.32

color issue68B34StageColor = formalId == 1 ? colAcc : formalId == 2 ? colMarkup : formalId == 3 ? colReacc : formalId == 4 ? colDist : formalId == 5 ? colMarkdown : formalId == 6 ? colRedist : colNeutral
bgcolor(showIssue68B34StageBg and issue68B34Ready ? color.new(issue68B34StageColor, 92) : na, title="Issue68 B34 Formal Stage")

hline(3.0, "Core Bias lane center", color=color.new(colNeutral, 80), linestyle=hline.style_dotted)
hline(2.0, "A lane center", color=color.new(colNeutral, 80), linestyle=hline.style_dotted)
hline(1.0, "B lane center", color=color.new(colNeutral, 80), linestyle=hline.style_dotted)
hline(0.0, "C lane center", color=color.new(colNeutral, 80), linestyle=hline.style_dotted)

plot(showIssue68B34Bias and issue68B34Ready ? f_issue68B34Lane(3.0, issue68B34Bias) : na, "B3.3 Core Bias lane", color=f_issue68B34Color(issue68B34Bias), linewidth=4, style=plot.style_stepline)
plot(showIssue68B34A and issue68B34Ready ? f_issue68B34Lane(2.0, issue68B34A) : na, "A Formal-family exposure", color=f_issue68B34Color(issue68B34A), linewidth=4, style=plot.style_stepline)
plot(showIssue68B34B and issue68B34Ready ? f_issue68B34Lane(1.0, issue68B34B) : na, "B Flat-Action exposure", color=f_issue68B34Color(issue68B34B), linewidth=4, style=plot.style_stepline)
plot(showIssue68B34C and issue68B34Ready ? f_issue68B34Lane(0.0, issue68B34C) : na, "C Stateful exposure", color=f_issue68B34Color(issue68B34C), linewidth=4, style=plot.style_stepline)

plot(float(formalId), "B34 Formal Stage ID", display=display.data_window)
plot(float(issue68B34Bias), "B34 Core Bias", display=display.data_window)
plot(float(flatActionLevel), "B34 Flat Action Level", display=display.data_window)
plot(float(paceCode), "B34 Pace Code", display=display.data_window)
plot(float(issue68B34A), "B34 Exposure A", display=display.data_window)
plot(float(issue68B34B), "B34 Exposure B", display=display.data_window)
plot(float(issue68B34C), "B34 Exposure C", display=display.data_window)
plot(issue68B34Bars > 0 ? 100.0 * float(issue68B34FlatA) / float(issue68B34Bars) : na, "B34 A Flat share %", display=display.data_window)
plot(issue68B34Bars > 0 ? 100.0 * float(issue68B34FlatB) / float(issue68B34Bars) : na, "B34 B Flat share %", display=display.data_window)
plot(issue68B34Bars > 0 ? 100.0 * float(issue68B34FlatC) / float(issue68B34Bars) : na, "B34 C Flat share %", display=display.data_window)
plot(float(issue68B34TransitionsA), "B34 A transitions", display=display.data_window)
plot(float(issue68B34TransitionsB), "B34 B transitions", display=display.data_window)
plot(float(issue68B34TransitionsC), "B34 C transitions", display=display.data_window)
plot(issue68B34ViolationA ? 1.0 : 0.0, "B34 A bias violation", display=display.data_window)
plot(issue68B34ViolationB ? 1.0 : 0.0, "B34 B bias violation", display=display.data_window)
plot(issue68B34ViolationC ? 1.0 : 0.0, "B34 C bias violation", display=display.data_window)
'''.strip()


def generate(source: Path) -> str:
    d1_text = phase_b.d1.generate(source)
    if d1_text.count(phase_b.D1_EXPORT_MARKER) != 1:
        raise RuntimeError("expected exactly one D1 parity export marker")
    core = d1_text.split(phase_b.D1_EXPORT_MARKER, 1)[0].rstrip()
    core = replace_once(core, phase_b.D1_INDICATOR_DECL, AUDIT_DECL)
    out = core + "\n\n" + B34_BODY + "\n"

    required = (
        "Issue #66 C-2",
        'volumeMode = "Off"',
        'mtfMode = "Off"',
        'divMode = "Off"',
        "flatActionLevel",
        "paceCode",
        "A Formal-family exposure",
        "B Flat-Action exposure",
        "C Stateful exposure",
        "no direct executable flip",
        "issue68B34ViolationC",
    )
    for token in required:
        if token not in out:
            raise RuntimeError(f"missing B3.4 audit token: {token}")

    forbidden = (
        "strategy.",
        "issue68ArmedDir",
        "issue68EarlyFail",
        "LONG SETUP",
        "SHORT SETUP",
        "D1B|",
    )
    for token in forbidden:
        if token in out:
            raise RuntimeError(f"forbidden legacy/strategy/parity token leaked into B3.4 audit: {token}")
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
