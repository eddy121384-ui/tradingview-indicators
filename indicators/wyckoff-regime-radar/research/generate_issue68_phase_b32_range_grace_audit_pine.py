#!/usr/bin/env python3
"""Generate Issue #68 Phase B3.2 range-grace lifecycle audit Pine."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_phase_b_lifecycle_pine as phase_b
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 Range-Grace v3.2 Audit", shorttitle="ChaseRisk #68 V32", overlay=false, precision=2)'

V32_BODY = r'''

// ============================================================================
// Issue #68 Phase B3.2 preregistered range-grace lifecycle.
// Issue #66 C-2 runtime-validated classifier lineage; no classifier changes.
// Hold/exit semantic audit only. No strategy orders / PnL / sizing / stops.
// ============================================================================

groupIssue68V32 = "Issue #68｜Range-Grace v3.2 Audit"
showIssue68V32StageBg = input.bool(true, "顯示 Formal Stage 背景", group=groupIssue68V32)
showIssue68V32Events = input.bool(true, "顯示進出場事件", group=groupIssue68V32)
showIssue68V32Grace = input.bool(true, "顯示 Range Grace", group=groupIssue68V32)

issue68V32Ready = bar_index >= rankLen - 1

var int issue68V32Pos = 0
var int issue68V32Grace = 0
int issue68V32Before = issue68V32Pos
int issue68V32GraceBefore = issue68V32Grace

bool issue68V32EnterLong = false
bool issue68V32EnterShort = false
bool issue68V32ExitLong = false
bool issue68V32ExitShort = false
bool issue68V32FlipLongToShort = false
bool issue68V32FlipShortToLong = false
bool issue68V32RangeExitLong = false
bool issue68V32RangeExitShort = false
bool issue68V32GraceLong = false
bool issue68V32GraceShort = false

if issue68V32Ready
    int issue68V32Stage = formalId
    int issue68V32After = issue68V32Before
    int issue68V32GraceAfter = issue68V32GraceBefore

    if issue68V32Before == 0
        issue68V32GraceAfter := 0
        if issue68V32Stage == 2
            issue68V32After := 1
        else if issue68V32Stage == 5
            issue68V32After := -1
        else
            issue68V32After := 0
    else if issue68V32Before == 1
        if issue68V32Stage == 2 or issue68V32Stage == 3
            issue68V32After := 1
            issue68V32GraceAfter := 0
        else if issue68V32Stage == 5 or issue68V32Stage == 6
            issue68V32After := -1
            issue68V32GraceAfter := 0
        else if issue68V32Stage == 1 or issue68V32Stage == 4
            issue68V32GraceAfter := issue68V32GraceBefore + 1
            if issue68V32GraceAfter >= confirmBars
                issue68V32After := 0
                issue68V32GraceAfter := 0
                issue68V32RangeExitLong := true
            else
                issue68V32After := 1
                issue68V32GraceLong := true
        else if issue68V32Stage == 0
            issue68V32After := 1
            issue68V32GraceAfter := issue68V32GraceBefore
    else if issue68V32Before == -1
        if issue68V32Stage == 5 or issue68V32Stage == 6
            issue68V32After := -1
            issue68V32GraceAfter := 0
        else if issue68V32Stage == 2 or issue68V32Stage == 3
            issue68V32After := 1
            issue68V32GraceAfter := 0
        else if issue68V32Stage == 1 or issue68V32Stage == 4
            issue68V32GraceAfter := issue68V32GraceBefore + 1
            if issue68V32GraceAfter >= confirmBars
                issue68V32After := 0
                issue68V32GraceAfter := 0
                issue68V32RangeExitShort := true
            else
                issue68V32After := -1
                issue68V32GraceShort := true
        else if issue68V32Stage == 0
            issue68V32After := -1
            issue68V32GraceAfter := issue68V32GraceBefore

    if issue68V32Before == 1 and issue68V32After == -1
        issue68V32FlipLongToShort := true
        issue68V32ExitLong := true
        issue68V32EnterShort := true
    else if issue68V32Before == -1 and issue68V32After == 1
        issue68V32FlipShortToLong := true
        issue68V32ExitShort := true
        issue68V32EnterLong := true
    else
        if issue68V32Before != 1 and issue68V32After == 1
            issue68V32EnterLong := true
        if issue68V32Before != -1 and issue68V32After == -1
            issue68V32EnterShort := true
        if issue68V32Before == 1 and issue68V32After != 1
            issue68V32ExitLong := true
        if issue68V32Before == -1 and issue68V32After != -1
            issue68V32ExitShort := true

    issue68V32Pos := issue68V32After
    issue68V32Grace := issue68V32GraceAfter
else
    issue68V32Pos := 0
    issue68V32Grace := 0

color issue68V32StageColor = formalId == 1 ? colAcc : formalId == 2 ? colMarkup : formalId == 3 ? colReacc : formalId == 4 ? colDist : formalId == 5 ? colMarkdown : formalId == 6 ? colRedist : colNeutral
bgcolor(showIssue68V32StageBg and issue68V32Ready ? color.new(issue68V32StageColor, 91) : na, title="Issue68 V32 Formal Stage")

hline(1.0, "Long", color=color.new(colGreen, 75), linestyle=hline.style_dotted)
hline(0.0, "Flat", color=color.new(colNeutral, 70), linestyle=hline.style_dotted)
hline(-1.0, "Short", color=color.new(colRed, 75), linestyle=hline.style_dotted)

color issue68V32PosColor = issue68V32Pos == 1 ? colGreen : issue68V32Pos == -1 ? colRed : colNeutral
plot(issue68V32Ready ? float(issue68V32Pos) : na, "Issue68 V32 desired position", color=issue68V32PosColor, linewidth=4, style=plot.style_stepline)

plotshape(showIssue68V32Events and issue68V32EnterLong ? 1.0 : na, title="Issue68 V32 Long entry", style=shape.triangleup, location=location.absolute, color=colGreen, size=size.small, text="L")
plotshape(showIssue68V32Events and issue68V32EnterShort ? -1.0 : na, title="Issue68 V32 Short entry", style=shape.triangledown, location=location.absolute, color=colRed, size=size.small, text="S")
plotshape(showIssue68V32Events and issue68V32ExitLong ? 0.72 : na, title="Issue68 V32 Long exit", style=shape.square, location=location.absolute, color=colNeutral, size=size.tiny, text="X")
plotshape(showIssue68V32Events and issue68V32ExitShort ? -0.72 : na, title="Issue68 V32 Short exit", style=shape.square, location=location.absolute, color=colNeutral, size=size.tiny, text="X")
plotshape(showIssue68V32Grace and issue68V32GraceLong ? 0.50 : na, title="Issue68 V32 Long range grace", style=shape.circle, location=location.absolute, color=colBreakout, size=size.tiny, text="G")
plotshape(showIssue68V32Grace and issue68V32GraceShort ? -0.50 : na, title="Issue68 V32 Short range grace", style=shape.circle, location=location.absolute, color=colBreakout, size=size.tiny, text="G")
plotshape(showIssue68V32Events and issue68V32RangeExitLong ? 0.25 : na, title="Issue68 V32 Long range exit", style=shape.diamond, location=location.absolute, color=colNeutral, size=size.tiny, text="RX")
plotshape(showIssue68V32Events and issue68V32RangeExitShort ? -0.25 : na, title="Issue68 V32 Short range exit", style=shape.diamond, location=location.absolute, color=colNeutral, size=size.tiny, text="RX")

plot(float(formalId), "Issue68 V32 Formal Stage ID", display=display.data_window)
plot(float(issue68V32Pos), "Issue68 V32 desired position data", display=display.data_window)
plot(float(issue68V32Grace), "Issue68 V32 range grace bars", display=display.data_window)
'''.strip()


def generate(source: Path) -> str:
    d1_text = phase_b.d1.generate(source)
    if d1_text.count(phase_b.D1_EXPORT_MARKER) != 1:
        raise RuntimeError("expected exactly one D1 parity export marker")
    core = d1_text.split(phase_b.D1_EXPORT_MARKER, 1)[0].rstrip()
    core = replace_once(core, phase_b.D1_INDICATOR_DECL, AUDIT_DECL)
    out = core + "\n\n" + V32_BODY + "\n"

    required = (
        "Issue #66 C-2",
        'volumeMode = "Off"',
        'mtfMode = "Off"',
        'divMode = "Off"',
        "issue68V32GraceAfter >= confirmBars",
        "issue68V32Stage == 1 or issue68V32Stage == 4",
        "Issue68 V32 desired position",
        "Issue68 V32 range grace bars",
    )
    for token in required:
        if token not in out:
            raise RuntimeError(f"missing v3.2 audit token: {token}")

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
            raise RuntimeError(f"forbidden legacy/strategy/parity token leaked into v3.2 audit: {token}")
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
