#!/usr/bin/env python3
"""Generate Issue #68 Phase B3.3 core-bias memory audit Pine."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_phase_b_lifecycle_pine as phase_b
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 Core Bias v3.3 Audit", shorttitle="ChaseRisk #68 V33", overlay=false, precision=2)'

V33_BODY = r'''

// ============================================================================
// Issue #68 Phase B3.3 preregistered core-bias memory.
// Issue #66 C-2 runtime-validated classifier lineage; no classifier changes.
// IMPORTANT: bias is regime memory, NOT executable desired exposure.
// ============================================================================

groupIssue68V33 = "Issue #68｜Core Bias v3.3 Audit"
showIssue68V33StageBg = input.bool(true, "顯示 Formal Stage 背景", group=groupIssue68V33)
showIssue68V33Events = input.bool(true, "顯示 Bias 建立 / 翻轉", group=groupIssue68V33)

issue68V33Ready = bar_index >= rankLen - 1

var int issue68V33Bias = 0
int issue68V33Before = issue68V33Bias
bool issue68V33EstBull = false
bool issue68V33EstBear = false
bool issue68V33FlipBullBear = false
bool issue68V33FlipBearBull = false

if issue68V33Ready
    int issue68V33Stage = formalId
    int issue68V33After = issue68V33Before

    if issue68V33Before == 0
        if issue68V33Stage == 2
            issue68V33After := 1
        else if issue68V33Stage == 5
            issue68V33After := -1
        else
            issue68V33After := 0
    else if issue68V33Before == 1
        issue68V33After := issue68V33Stage == 5 or issue68V33Stage == 6 ? -1 : 1
    else if issue68V33Before == -1
        issue68V33After := issue68V33Stage == 2 or issue68V33Stage == 3 ? 1 : -1

    issue68V33EstBull := issue68V33Before == 0 and issue68V33After == 1
    issue68V33EstBear := issue68V33Before == 0 and issue68V33After == -1
    issue68V33FlipBullBear := issue68V33Before == 1 and issue68V33After == -1
    issue68V33FlipBearBull := issue68V33Before == -1 and issue68V33After == 1
    issue68V33Bias := issue68V33After
else
    issue68V33Bias := 0

color issue68V33StageColor = formalId == 1 ? colAcc : formalId == 2 ? colMarkup : formalId == 3 ? colReacc : formalId == 4 ? colDist : formalId == 5 ? colMarkdown : formalId == 6 ? colRedist : colNeutral
bgcolor(showIssue68V33StageBg and issue68V33Ready ? color.new(issue68V33StageColor, 91) : na, title="Issue68 V33 Formal Stage")

hline(1.0, "Bull bias", color=color.new(colGreen, 75), linestyle=hline.style_dotted)
hline(0.0, "Unknown bias", color=color.new(colNeutral, 70), linestyle=hline.style_dotted)
hline(-1.0, "Bear bias", color=color.new(colRed, 75), linestyle=hline.style_dotted)

color issue68V33BiasColor = issue68V33Bias == 1 ? colGreen : issue68V33Bias == -1 ? colRed : colNeutral
plot(issue68V33Ready ? float(issue68V33Bias) : na, "Issue68 V33 core bias memory", color=issue68V33BiasColor, linewidth=5, style=plot.style_stepline)

plotshape(showIssue68V33Events and issue68V33EstBull ? 1.0 : na, title="Issue68 V33 Establish bull bias", style=shape.triangleup, location=location.absolute, color=colGreen, size=size.small, text="B+")
plotshape(showIssue68V33Events and issue68V33EstBear ? -1.0 : na, title="Issue68 V33 Establish bear bias", style=shape.triangledown, location=location.absolute, color=colRed, size=size.small, text="B-")
plotshape(showIssue68V33Events and issue68V33FlipBearBull ? 0.55 : na, title="Issue68 V33 Flip bear to bull", style=shape.diamond, location=location.absolute, color=colGreen, size=size.small, text="FLIP+")
plotshape(showIssue68V33Events and issue68V33FlipBullBear ? -0.55 : na, title="Issue68 V33 Flip bull to bear", style=shape.diamond, location=location.absolute, color=colRed, size=size.small, text="FLIP-")

plot(float(formalId), "Issue68 V33 Formal Stage ID", display=display.data_window)
plot(float(issue68V33Bias), "Issue68 V33 core bias data", display=display.data_window)
'''.strip()


def generate(source: Path) -> str:
    d1_text = phase_b.d1.generate(source)
    if d1_text.count(phase_b.D1_EXPORT_MARKER) != 1:
        raise RuntimeError("expected exactly one D1 parity export marker")
    core = d1_text.split(phase_b.D1_EXPORT_MARKER, 1)[0].rstrip()
    core = replace_once(core, phase_b.D1_INDICATOR_DECL, AUDIT_DECL)
    out = core + "\n\n" + V33_BODY + "\n"

    required = (
        "Issue #66 C-2",
        'volumeMode = "Off"',
        'mtfMode = "Off"',
        'divMode = "Off"',
        "issue68V33Stage == 5 or issue68V33Stage == 6 ? -1 : 1",
        "issue68V33Stage == 2 or issue68V33Stage == 3 ? 1 : -1",
        "Issue68 V33 core bias memory",
        "bias is regime memory, NOT executable desired exposure",
    )
    for token in required:
        if token not in out:
            raise RuntimeError(f"missing v3.3 audit token: {token}")

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
            raise RuntimeError(f"forbidden legacy/strategy/parity token leaked into v3.3 audit: {token}")
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
