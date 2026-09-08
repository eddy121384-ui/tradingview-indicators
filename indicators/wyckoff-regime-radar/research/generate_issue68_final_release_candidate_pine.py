#!/usr/bin/env python3
"""Generate the clean Issue #68 release-candidate Pine source.

The RC is built deterministically from the frozen v0.5.2.1 source through the
accepted Issue #66 C-2 lineage, the Issue #68 exact symmetric HARD current-
context repair, the yield-safe representation split, and approved presentation
defaults.

The generator deliberately does NOT assign a new semantic version. Issue #66
accepted C-2 as a downstream baseline but did not authorize v0.6/v0.5.3 naming.
Final semantic versioning is deferred until Eddy authorizes production.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_yield_safe_hard_production_candidate_pine as ys
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

DECL_OLD = 'indicator("Chase Risk Market Regime Radar v0.5.2.1｜Non-functional Cleanup", shorttitle="ChaseRisk Radar v0.5.2.1", overlay=false, precision=1)'
DECL_NEW = 'indicator("Chase Risk Market Regime Radar｜Issue #68 RC", shorttitle="ChaseRisk Radar #68 RC", overlay=false, precision=1)'

HEADER_OLD = '''// Chase Risk Market Regime Radar v0.5.2.1
// Non-functional cleanup of v0.5.2: calculations, inputs, plots, dashboard, and alert logic are unchanged.
// Price action remains the primary engine; Volume, MTF, and Divergence remain auxiliary witnesses.
// Six stage values are relative weights, not statistical probabilities. Risk warnings are not reversal signals.'''

HEADER_NEW = '''// Chase Risk Market Regime Radar — Issue #68 release candidate.
// Lineage: frozen v0.5.2.1 + accepted Issue #66 C-2 + Issue #68 yield-safe representation + exact symmetric HARD current-context cap.
// Release-candidate label only: no new semantic version is assigned before explicit production authorization.
// Price action remains the primary engine; Volume, MTF, and Divergence remain auxiliary witnesses.
// Six stage values are relative weights, not statistical probabilities. Risk warnings are not reversal signals.'''


def generate(source_path: Path) -> str:
    candidate, _ = ys.generate(source_path)

    rc = replace_once(candidate, DECL_OLD, DECL_NEW)
    rc = replace_once(rc, HEADER_OLD, HEADER_NEW)

    # Exact-clean-source contract: apart from RC identification comments/title,
    # the output must round-trip byte-for-byte to the validated yield-safe HARD
    # production candidate.
    roundtrip = replace_once(rc, DECL_NEW, DECL_OLD)
    roundtrip = replace_once(roundtrip, HEADER_NEW, HEADER_OLD)
    if roundtrip != candidate:
        raise RuntimeError("RC differs from validated yield-safe HARD candidate outside identification header")

    required = (
        'representationMode = input.string("Auto", "資料表示模式", options=["Auto", "Price Log", "Yield Level"]',
        'autoYieldLevel = syminfo.type == "bond" and syminfo.currency == "NONE"',
        'currentBearGate = f_gate(bearBg, 35.0, 75.0)',
        'currentBullGate = f_gate(bullBg, 35.0, 75.0)',
        'ctxDownExGate = math.min(downsideExhaustionGate, currentBearGate)',
        'ctxUpExGate = math.min(upsideExhaustionGate, currentBullGate)',
        'accGate      = rangeGate * bearBackgroundForAccGate * ctxDownExGate * supportHoldingGate * nonMarkdownContinuationGate',
        'distGate     = rangeGate * bullBackgroundForDistGate * ctxUpExGate * resistanceHoldingGate * nonMarkupContinuationGate',
        'plot(showDownRiskLine ? endRiskDn : na, "下跌末段恐慌風險", color=dnColor, linewidth=2, linestyle=plot.linestyle_dashed)',
        'colAcc      = input.color(color.rgb(110, 190, 135), "吸籌顏色", group=groupColors)',
        'colMarkup   = input.color(color.rgb(30, 130, 75), "拉升顏色", group=groupColors)',
        'colReacc    = input.color(color.rgb(90, 175, 225), "再吸籌顏色", group=groupColors)',
        'colDist     = input.color(color.rgb(240, 205, 80), "派發顏色", group=groupColors)',
        'colMarkdown = input.color(color.rgb(220, 50, 47), "崩跌顏色", group=groupColors)',
        'colRedist   = input.color(color.rgb(245, 140, 45), "再出貨顏色", group=groupColors)',
        'volumeMode = input.string("Auto", "Volume Mode"',
        'mtfMode = input.string("Observe Only", "MTF Mode"',
        'divMode = input.string("Observe Only", "Divergence Mode"',
        'request.security_lower_tf',
        '// Visuals',
        'alertcondition(formalChanged',
    )
    for token in required:
        if token not in rc:
            raise RuntimeError(f"final RC missing required token: {token}")

    forbidden = (
        '#68 HARD A/B',
        'issue68AB',
        '#68 A Baseline TOP',
        '#68 B HARD TOP',
        'TOP Changed',
        'strategy.entry',
        'strategy.close',
        'strategy(',
        'STATEFUL CTX',
    )
    for token in forbidden:
        if token in rc:
            raise RuntimeError(f"research/audit leakage in final RC: {token}")

    return rc


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate clean Issue #68 release-candidate Pine")
    ap.add_argument("--source", type=Path, default=Path(__file__).resolve().parent / SOURCE_RELATIVE)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    text = generate(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    print(args.output)
    print("Issue #68 final release-candidate static contract PASS")


if __name__ == "__main__":
    main()
