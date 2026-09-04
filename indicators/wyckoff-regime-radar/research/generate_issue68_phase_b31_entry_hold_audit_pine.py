#!/usr/bin/env python3
"""Generate Issue #68 Phase B3.1 entry/hold separation audit Pine.

Reuses the runtime-validated Issue #66 C-2 Pine core. New entry requires aligned
Formal trend stage + existing C-2 strongCandidate. Holding remains Formal driven.
No strategy orders or PnL transport.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_phase_b_lifecycle_pine as phase_b
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 Entry/Hold v3.1 Audit", shorttitle="ChaseRisk #68 V31", overlay=false, precision=2)'

V31_BODY = r'''

// ============================================================================
// Issue #66 C-2 runtime-validated price-only lineage.
// Issue #68 Phase B3.1 preregistered Entry / Hold Separation.
// Strong decides whether a NEW position may enter; Formal decides whether an
// EXISTING position is held or exited. No new numeric threshold is introduced.
// Semantic audit only. No strategy orders / PnL / ARM / Early Fail.
// ============================================================================

groupIssue68V31 = "Issue #68｜Entry/Hold v3.1 Audit"
showIssue68V31StageBg = input.bool(true, "顯示 Formal Stage 背景", group=groupIssue68V31)
showIssue68V31Events = input.bool(true, "顯示進出場事件", group=groupIssue68V31)
showIssue68V31Blocked = input.bool(false, "顯示 Formal 2/5 但未獲 Strong 授權", group=groupIssue68V31)

issue68V31Ready = bar_index >= rankLen - 1

var int issue68V31Pos = 0
int issue68V31Before = issue68V31Pos
int issue68V31StrongStage = strongCandidate ? topId : 0

bool issue68V31EnterLong = false
bool issue68V31EnterShort = false
bool issue68V31ExitLong = false
bool issue68V31ExitShort = false
bool issue68V31FlipLongToShort = false
bool issue68V31FlipShortToLong = false
bool issue68V31BlockedLong = false
bool issue68V31BlockedShort = false
bool issue68V31HoldLongReacc = false
bool issue68V31HoldShortRedist = false

if issue68V31Ready
    int issue68V31Stage = formalId
    int issue68V31After = issue68V31Before

    if issue68V31Stage == 0
        issue68V31After := issue68V31Before
    else if issue68V31Stage == 1 or issue68V31Stage == 4
        issue68V31After := 0
    else if issue68V31Stage == 3
        issue68V31After := issue68V31Before == 1 ? 1 : 0
    else if issue68V31Stage == 6
        issue68V31After := issue68V31Before == -1 ? -1 : 0
    else if issue68V31Stage == 2
        if issue68V31Before == 1
            issue68V31After := 1
        else if issue68V31StrongStage == 2
            issue68V31After := 1
        else
            issue68V31After := 0
            issue68V31BlockedLong := true
    else if issue68V31Stage == 5
        if issue68V31Before == -1
            issue68V31After := -1
        else if issue68V31StrongStage == 5
            issue68V31After := -1
        else
            issue68V31After := 0
            issue68V31BlockedShort := true
    else
        issue68V31After := 0

    if issue68V31Before == 1 and issue68V31After == -1
        issue68V31FlipLongToShort := true
        issue68V31ExitLong := true
        issue68V31EnterShort := true
    else if issue68V31Before == -1 and issue68V31After == 1
        issue68V31FlipShortToLong := true
        issue68V31ExitShort := true
        issue68V31EnterLong := true
    else
        if issue68V31Before != 1 and issue68V31After == 1
            issue68V31EnterLong := true
        if issue68V31Before != -1 and issue68V31After == -1
            issue68V31EnterShort := true
        if issue68V31Before == 1 and issue68V31After != 1
            issue68V31ExitLong := true
        if issue68V31Before == -1 and issue68V31After != -1
            issue68V31ExitShort := true

    issue68V31HoldLongReacc := issue68V31Stage == 3 and issue68V31Before == 1 and issue68V31After == 1
    issue68V31HoldShortRedist := issue68V31Stage == 6 and issue68V31Before == -1 and issue68V31After == -1
    issue68V31Pos := issue68V31After
else
    issue68V31Pos := 0

// Audit pane: +1 Long / 0 Flat / -1 Short.
color issue68V31StageColor = formalId == 1 ? colAcc : formalId == 2 ? colMarkup : formalId == 3 ? colReacc : formalId == 4 ? colDist : formalId == 5 ? colMarkdown : formalId == 6 ? colRedist : colNeutral
bgcolor(showIssue68V31StageBg and issue68V31Ready ? color.new(issue68V31StageColor, 91) : na, title="Issue68 V31 Formal Stage")

hline(1.0, "Long", color=color.new(colGreen, 75), linestyle=hline.style_dotted)
hline(0.0, "Flat", color=color.new(colNeutral, 70), linestyle=hline.style_dotted)
hline(-1.0, "Short", color=color.new(colRed, 75), linestyle=hline.style_dotted)

color issue68V31PosColor = issue68V31Pos == 1 ? colGreen : issue68V31Pos == -1 ? colRed : colNeutral
plot(issue68V31Ready ? float(issue68V31Pos) : na, "Issue68 V31 desired position", color=issue68V31PosColor, linewidth=4, style=plot.style_stepline)

plotshape(showIssue68V31Events and issue68V31EnterLong ? 1.0 : na, title="Issue68 V31 Long entry", style=shape.triangleup, location=location.absolute, color=colGreen, size=size.small, text="L")
plotshape(showIssue68V31Events and issue68V31EnterShort ? -1.0 : na, title="Issue68 V31 Short entry", style=shape.triangledown, location=location.absolute, color=colRed, size=size.small, text="S")
plotshape(showIssue68V31Events and issue68V31ExitLong ? 0.72 : na, title="Issue68 V31 Long exit", style=shape.square, location=location.absolute, color=colNeutral, size=size.tiny, text="X")
plotshape(showIssue68V31Events and issue68V31ExitShort ? -0.72 : na, title="Issue68 V31 Short exit", style=shape.square, location=location.absolute, color=colNeutral, size=size.tiny, text="X")
plotshape(showIssue68V31Events and issue68V31FlipShortToLong ? 0.45 : na, title="Issue68 V31 Flip to long", style=shape.diamond, location=location.absolute, color=colGreen, size=size.tiny, text="FLIP")
plotshape(showIssue68V31Events and issue68V31FlipLongToShort ? -0.45 : na, title="Issue68 V31 Flip to short", style=shape.diamond, location=location.absolute, color=colRed, size=size.tiny, text="FLIP")

plotshape(showIssue68V31Blocked and issue68V31BlockedLong ? 0.2 : na, title="Issue68 V31 Blocked long", style=shape.circle, location=location.absolute, color=colYellow, size=size.tiny, text="B")
plotshape(showIssue68V31Blocked and issue68V31BlockedShort ? -0.2 : na, title="Issue68 V31 Blocked short", style=shape.circle, location=location.absolute, color=colYellow, size=size.tiny, text="B")

plot(float(formalId), "Issue68 V31 Formal Stage ID", display=display.data_window)
plot(float(issue68V31StrongStage), "Issue68 V31 Strong Stage ID", display=display.data_window)
plot(float(issue68V31Pos), "Issue68 V31 desired position data", display=display.data_window)
plot(issue68V31HoldLongReacc ? 1.0 : 0.0, "Issue68 V31 hold-long-through-Stage3", display=display.data_window)
plot(issue68V31HoldShortRedist ? 1.0 : 0.0, "Issue68 V31 hold-short-through-Stage6", display=display.data_window)
'''.strip()


def generate(source: Path) -> str:
    d1_text = phase_b.d1.generate(source)
    if d1_text.count(phase_b.D1_EXPORT_MARKER) != 1:
        raise RuntimeError("expected exactly one D1 parity export marker")
    core = d1_text.split(phase_b.D1_EXPORT_MARKER, 1)[0].rstrip()
    core = replace_once(core, phase_b.D1_INDICATOR_DECL, AUDIT_DECL)
    out = core + "\n\n" + V31_BODY + "\n"

    required = (
        "Issue #66 C-2 runtime-validated price-only lineage",
        "strongCandidate ? topId : 0",
        "issue68V31Stage == 2",
        "issue68V31Stage == 5",
        "issue68V31Before == 1",
        "issue68V31Before == -1",
        "Issue68 V31 desired position",
    )
    for token in required:
        if token not in out:
            raise RuntimeError(f"missing v3.1 audit token: {token}")

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
            raise RuntimeError(f"forbidden v2/strategy/parity token leaked into v3.1 audit: {token}")
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
