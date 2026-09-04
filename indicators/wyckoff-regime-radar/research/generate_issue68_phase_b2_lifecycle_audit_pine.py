#!/usr/bin/env python3
"""Generate the Issue #68 Phase-B2 lifecycle semantic-audit Pine indicator.

The audit indicator is mechanically derived from the Phase-B visual strategy.
It removes TradingView strategy orders and replaces the noisy price-overlay
review layer with a compact +1/0/-1 lifecycle pane. The lifecycle state machine
itself is not changed.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_phase_b_lifecycle_pine as phase_b
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once


HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 Lifecycle Semantic Audit", shorttitle="ChaseRisk #68 AUDIT", overlay=false, precision=2)'
ORDER_MARKER = "// TradingView orders; process_orders_on_close=false is set in the declaration."
VISUAL_MARKER = "// Human semantic audit layer."
AUDIT_MARKER = "// Phase B2 semantic audit pane."


AUDIT_LAYER = r'''
// Phase B2 semantic audit pane.
// No TradingView orders are emitted here. This pane visualizes the close-of-bar
// lifecycle decision clock only, so human review is not mixed with next-bar
// strategy execution markers.
color issue68AuditStageColor = formalId == 1 ? colAcc : formalId == 2 ? colMarkup : formalId == 3 ? colReacc : formalId == 4 ? colDist : formalId == 5 ? colMarkdown : formalId == 6 ? colRedist : colNeutral
bgcolor(showIssue68StageBg and issue68Ready ? color.new(issue68AuditStageColor, 91) : na, title="Issue68 Formal Stage")

hline(1.0, "Long", color=color.new(colGreen, 75), linestyle=hline.style_dotted)
hline(0.0, "Flat", color=color.new(colNeutral, 70), linestyle=hline.style_dotted)
hline(-1.0, "Short", color=color.new(colRed, 75), linestyle=hline.style_dotted)

issue68PosColor = issue68Pos == 1 ? colGreen : issue68Pos == -1 ? colRed : colNeutral
plot(issue68Ready ? float(issue68Pos) : na, "Issue68 desired position", color=issue68PosColor, linewidth=3, style=plot.style_stepline)
plot(issue68Ready and issue68ArmedDir != 0 ? float(issue68ArmedDir) * 0.5 : na, "Issue68 armed direction", color=colYellow, linewidth=1, style=plot.style_circles)

plotshape(showIssue68Arms and issue68ArmLong ? 0.5 : na, title="Issue68 Bull ARM", style=shape.diamond, location=location.absolute, color=colYellow, size=size.tiny, text="A")
plotshape(showIssue68Arms and issue68ArmShort ? -0.5 : na, title="Issue68 Bear ARM", style=shape.diamond, location=location.absolute, color=colYellow, size=size.tiny, text="A")

plotshape(showIssue68TradeMarks and issue68EntryLong ? 1.0 : na, title="Issue68 Long entry", style=shape.triangleup, location=location.absolute, color=colGreen, size=size.small, text="L")
plotshape(showIssue68TradeMarks and issue68EntryShort ? -1.0 : na, title="Issue68 Short entry", style=shape.triangledown, location=location.absolute, color=colRed, size=size.small, text="S")

plotshape(showIssue68TradeMarks and issue68EarlyFailLong ? 0.75 : na, title="Issue68 Long Early Fail", style=shape.xcross, location=location.absolute, color=colOrange, size=size.small, text="F")
plotshape(showIssue68TradeMarks and issue68EarlyFailShort ? -0.75 : na, title="Issue68 Short Early Fail", style=shape.xcross, location=location.absolute, color=colOrange, size=size.small, text="F")
plotshape(showIssue68TradeMarks and issue68OppositeExitLong ? 0.75 : na, title="Issue68 Long opposite exit", style=shape.square, location=location.absolute, color=colNeutral, size=size.tiny, text="X")
plotshape(showIssue68TradeMarks and issue68OppositeExitShort ? -0.75 : na, title="Issue68 Short opposite exit", style=shape.square, location=location.absolute, color=colNeutral, size=size.tiny, text="X")

plotshape(showIssue68AddCandidates and issue68AddLongCandidate ? 0.25 : na, title="Issue68 Bull ADD candidate", style=shape.circle, location=location.absolute, color=colBreakout, size=size.tiny, text="+")
plotshape(showIssue68AddCandidates and issue68AddShortCandidate ? -0.25 : na, title="Issue68 Bear ADD candidate", style=shape.circle, location=location.absolute, color=colBreakdown, size=size.tiny, text="+")

plot(float(formalId), "Issue68 Formal Stage ID", display=display.data_window)
plot(float(issue68Pos), "Issue68 Lifecycle desired position", display=display.data_window)
plot(float(issue68ArmedDir), "Issue68 ARM direction", display=display.data_window)
plot(float(issue68EntryAge), "Issue68 Early Fail age", display=display.data_window)
plot(issue68EntryLevel, "Issue68 Early Fail anchor value", display=display.data_window)
'''.strip()


def generate(source: Path) -> str:
    strategy_text = phase_b.generate(source, "visual")
    text = replace_once(strategy_text, phase_b.VISUAL_DECL, AUDIT_DECL)

    order_start = text.find(ORDER_MARKER)
    visual_start = text.find(VISUAL_MARKER)
    if order_start < 0 or visual_start < 0 or visual_start <= order_start:
        raise RuntimeError("Phase-B order/visual markers not found in expected order")

    # Preserve everything through the lifecycle state machine, drop TradingView
    # order calls and the old price-overlay review layer, then append the audit pane.
    text = text[:order_start].rstrip() + "\n\n" + AUDIT_LAYER + "\n"

    required = (
        "Issue #66 C-2 runtime-validated price-only lineage",
        "issue68Ready = bar_index >= rankLen - 1",
        "var int issue68Pos = 0",
        "issue68DirectTransitionLong",
        "issue68EarlyFailLong",
        "issue68OppositeExitShort",
        AUDIT_MARKER,
        'plot(issue68Ready ? float(issue68Pos) : na, "Issue68 desired position"',
        'location=location.absolute',
    )
    for token in required:
        if token not in text:
            raise RuntimeError(f"missing Phase-B2 required token: {token}")
    if "strategy." in text or text.startswith("strategy("):
        raise RuntimeError("Phase-B2 audit must not contain TradingView strategy orders")
    return text


def state_machine_segment(text: str, end_marker: str) -> str:
    start_token = "issue68Ready = bar_index >= rankLen - 1"
    start = text.find(start_token)
    end = text.find(end_marker)
    if start < 0 or end < 0 or end <= start:
        raise RuntimeError("unable to isolate Issue68 lifecycle state-machine segment")
    return text[start:end].rstrip() + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=HERE / SOURCE_RELATIVE)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    out = generate(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(out, encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
