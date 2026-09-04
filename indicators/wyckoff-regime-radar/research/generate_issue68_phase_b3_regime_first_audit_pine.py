#!/usr/bin/env python3
"""Generate Issue #68 Phase B3 regime-first lifecycle audit Pine.

Reuses the runtime-validated Issue #66 C-2 Pine calculation core and appends the
preregistered regime-first desired-position state machine. No strategy orders,
ARM handshake, Early Fail, sizing, stops, targets, or PnL transport are present.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_phase_b_lifecycle_pine as phase_b
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 Regime-first v3 Audit", shorttitle="ChaseRisk #68 V3", overlay=false, precision=2)'

V3_BODY = r'''

// ============================================================================
// Issue #68 Phase B3 preregistered regime-first lifecycle v3.
// Semantic audit only. No strategy orders / PnL / ARM / Early Fail.
// ============================================================================

groupIssue68V3 = "Issue #68｜Regime-first v3 Audit"
showIssue68V3StageBg = input.bool(true, "顯示 Formal Stage 背景", group=groupIssue68V3)
showIssue68V3Events = input.bool(true, "顯示進出場事件", group=groupIssue68V3)
showIssue68V3BreakWitness = input.bool(false, "顯示 breakout witness（不參與進出）", group=groupIssue68V3)

issue68V3Ready = bar_index >= rankLen - 1

var int issue68V3Pos = 0
int issue68V3Before = issue68V3Pos

bool issue68V3EnterLong = false
bool issue68V3EnterShort = false
bool issue68V3ExitLong = false
bool issue68V3ExitShort = false
bool issue68V3FlipLongToShort = false
bool issue68V3FlipShortToLong = false
bool issue68V3HoldLongReacc = false
bool issue68V3HoldShortRedist = false

if issue68V3Ready
    int issue68V3Stage = formalId
    int issue68V3After = issue68V3Before

    if issue68V3Stage == 0
        issue68V3After := issue68V3Before
    else if issue68V3Stage == 1 or issue68V3Stage == 4
        issue68V3After := 0
    else if issue68V3Stage == 2
        issue68V3After := 1
    else if issue68V3Stage == 5
        issue68V3After := -1
    else if issue68V3Stage == 3
        issue68V3After := issue68V3Before == 1 ? 1 : 0
    else if issue68V3Stage == 6
        issue68V3After := issue68V3Before == -1 ? -1 : 0
    else
        issue68V3After := 0

    if issue68V3Before == 1 and issue68V3After == -1
        issue68V3FlipLongToShort := true
        issue68V3ExitLong := true
        issue68V3EnterShort := true
    else if issue68V3Before == -1 and issue68V3After == 1
        issue68V3FlipShortToLong := true
        issue68V3ExitShort := true
        issue68V3EnterLong := true
    else
        if issue68V3Before != 1 and issue68V3After == 1
            issue68V3EnterLong := true
        if issue68V3Before != -1 and issue68V3After == -1
            issue68V3EnterShort := true
        if issue68V3Before == 1 and issue68V3After != 1
            issue68V3ExitLong := true
        if issue68V3Before == -1 and issue68V3After != -1
            issue68V3ExitShort := true

    issue68V3HoldLongReacc := issue68V3Stage == 3 and issue68V3Before == 1 and issue68V3After == 1
    issue68V3HoldShortRedist := issue68V3Stage == 6 and issue68V3Before == -1 and issue68V3After == -1
    issue68V3Pos := issue68V3After
else
    issue68V3Pos := 0

// Audit pane: +1 Long / 0 Flat / -1 Short.
color issue68V3StageColor = formalId == 1 ? colAcc : formalId == 2 ? colMarkup : formalId == 3 ? colReacc : formalId == 4 ? colDist : formalId == 5 ? colMarkdown : formalId == 6 ? colRedist : colNeutral
bgcolor(showIssue68V3StageBg and issue68V3Ready ? color.new(issue68V3StageColor, 91) : na, title="Issue68 V3 Formal Stage")

hline(1.0, "Long", color=color.new(colGreen, 75), linestyle=hline.style_dotted)
hline(0.0, "Flat", color=color.new(colNeutral, 70), linestyle=hline.style_dotted)
hline(-1.0, "Short", color=color.new(colRed, 75), linestyle=hline.style_dotted)

color issue68V3PosColor = issue68V3Pos == 1 ? colGreen : issue68V3Pos == -1 ? colRed : colNeutral
plot(issue68V3Ready ? float(issue68V3Pos) : na, "Issue68 V3 desired position", color=issue68V3PosColor, linewidth=4, style=plot.style_stepline)

plotshape(showIssue68V3Events and issue68V3EnterLong ? 1.0 : na, title="Issue68 V3 Long entry", style=shape.triangleup, location=location.absolute, color=colGreen, size=size.small, text="L")
plotshape(showIssue68V3Events and issue68V3EnterShort ? -1.0 : na, title="Issue68 V3 Short entry", style=shape.triangledown, location=location.absolute, color=colRed, size=size.small, text="S")
plotshape(showIssue68V3Events and issue68V3ExitLong ? 0.72 : na, title="Issue68 V3 Long exit", style=shape.square, location=location.absolute, color=colNeutral, size=size.tiny, text="X")
plotshape(showIssue68V3Events and issue68V3ExitShort ? -0.72 : na, title="Issue68 V3 Short exit", style=shape.square, location=location.absolute, color=colNeutral, size=size.tiny, text="X")
plotshape(showIssue68V3Events and issue68V3FlipShortToLong ? 0.45 : na, title="Issue68 V3 Flip to long", style=shape.diamond, location=location.absolute, color=colGreen, size=size.tiny, text="FLIP")
plotshape(showIssue68V3Events and issue68V3FlipLongToShort ? -0.45 : na, title="Issue68 V3 Flip to short", style=shape.diamond, location=location.absolute, color=colRed, size=size.tiny, text="FLIP")

plotshape(showIssue68V3BreakWitness and rangeBreakUp ? 0.2 : na, title="Issue68 V3 Breakout witness", style=shape.circle, location=location.absolute, color=colBreakout, size=size.tiny, text="B")
plotshape(showIssue68V3BreakWitness and rangeBreakDn ? -0.2 : na, title="Issue68 V3 Breakdown witness", style=shape.circle, location=location.absolute, color=colBreakdown, size=size.tiny, text="B")

plot(float(formalId), "Issue68 V3 Formal Stage ID", display=display.data_window)
plot(float(issue68V3Pos), "Issue68 V3 desired position data", display=display.data_window)
plot(issue68V3HoldLongReacc ? 1.0 : 0.0, "Issue68 V3 hold-long-through-Stage3", display=display.data_window)
plot(issue68V3HoldShortRedist ? 1.0 : 0.0, "Issue68 V3 hold-short-through-Stage6", display=display.data_window)
'''.strip()


def generate(source: Path) -> str:
    d1_text = phase_b.d1.generate(source)
    if d1_text.count(phase_b.D1_EXPORT_MARKER) != 1:
        raise RuntimeError("expected exactly one D1 parity export marker")
    core = d1_text.split(phase_b.D1_EXPORT_MARKER, 1)[0].rstrip()
    core = replace_once(core, phase_b.D1_INDICATOR_DECL, AUDIT_DECL)
    out = core + "\n\n// Issue #66 C-2 runtime-validated price-only lineage.\n" + V3_BODY + "\n"

    required = (
        "Issue #66 C-2",
        'volumeMode = "Off"',
        'mtfMode = "Off"',
        'divMode = "Off"',
        "issue68V3Stage == 2",
        "issue68V3Stage == 5",
        "issue68V3Stage == 3",
        "issue68V3Stage == 6",
        "Issue68 V3 desired position",
    )
    for token in required:
        if token not in out:
            raise RuntimeError(f"missing v3 audit token: {token}")

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
            raise RuntimeError(f"forbidden v2/strategy/parity token leaked into v3 audit: {token}")
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
