#!/usr/bin/env python3
"""Generate Issue #68 FR10Y vs DE10Y compact S1 gate attribution Pine."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_phase_b_lifecycle_pine as phase_b
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 S1 Gate Compact", shorttitle="ChaseRisk #68 S1Gate", overlay=false, precision=2)'

BODY = r'''

// ============================================================================
// Issue #68 FR10Y vs DE10Y S1 Compact Gate Root Attribution Audit.
// Shared window: 2022-01-03 -> 2023-12-29, expected Bull yield regime.
// DISCOVERY ONLY. NO PNL. NO TUNING. FROZEN C-2.
// ============================================================================

groupIssue68S1Compact = "Issue #68｜S1 Compact Gate"
showIssue68S1CompactTable = input.bool(true, "顯示 S1 Compact Gate 表", group=groupIssue68S1Compact)

issue68S1CompactReady = bar_index >= rankLen - 1
int issue68S1CompactStart = timestamp(2022, 1, 3, 0, 0)
int issue68S1CompactEnd = timestamp(2023, 12, 29, 23, 59)
bool issue68S1CompactInWindow = issue68S1CompactReady and time >= issue68S1CompactStart and time <= issue68S1CompactEnd
bool issue68S1CompactValid = issue68S1CompactInWindow and not na(accRaw) and not na(accGate) and not na(accEff) and not na(markupRaw) and not na(markupGate) and not na(markupEff)

f_issue68S1CompactAvg(float s, int n) => n > 0 ? s / n : na
f_issue68S1CompactPct(int n, int d) => d > 0 ? 100.0 * n / d : na

var int issue68Bars = 0
var int issue68RawS2Lead = 0
var int issue68EffS2Lead = 0
var int issue68RawS2ToEffS1 = 0

var int issue68BindRange = 0
var int issue68BindBearBg = 0
var int issue68BindDownEx = 0
var int issue68BindSupport = 0
var int issue68BindNonMd = 0

var float issue68SumAccRaw = 0.0
var float issue68SumAccGate = 0.0
var float issue68SumAccEff = 0.0
var float issue68SumMarkupRaw = 0.0
var float issue68SumMarkupGate = 0.0
var float issue68SumMarkupEff = 0.0

var float issue68SumRangeGate = 0.0
var float issue68SumBearBgGate = 0.0
var float issue68SumDownExGate = 0.0
var float issue68SumSupportGate = 0.0
var float issue68SumNonMdGate = 0.0
var float issue68SumMinGate = 0.0

if issue68S1CompactValid
    issue68Bars += 1

    bool rawS2LeadNow = markupRaw > accRaw
    bool effS2LeadNow = markupEff > accEff
    issue68RawS2Lead += rawS2LeadNow ? 1 : 0
    issue68EffS2Lead += effS2LeadNow ? 1 : 0
    issue68RawS2ToEffS1 += rawS2LeadNow and not effS2LeadNow ? 1 : 0

    issue68SumAccRaw += accRaw
    issue68SumAccGate += accGate
    issue68SumAccEff += accEff
    issue68SumMarkupRaw += markupRaw
    issue68SumMarkupGate += markupGate
    issue68SumMarkupEff += markupEff

    issue68SumRangeGate += rangeGate
    issue68SumBearBgGate += bearBackgroundForAccGate
    issue68SumDownExGate += downsideExhaustionGate
    issue68SumSupportGate += supportHoldingGate
    issue68SumNonMdGate += nonMarkdownContinuationGate

    int bindId = 1
    float minGate = rangeGate
    if bearBackgroundForAccGate < minGate
        bindId := 2
        minGate := bearBackgroundForAccGate
    if downsideExhaustionGate < minGate
        bindId := 3
        minGate := downsideExhaustionGate
    if supportHoldingGate < minGate
        bindId := 4
        minGate := supportHoldingGate
    if nonMarkdownContinuationGate < minGate
        bindId := 5
        minGate := nonMarkdownContinuationGate

    issue68SumMinGate += minGate
    issue68BindRange += bindId == 1 ? 1 : 0
    issue68BindBearBg += bindId == 2 ? 1 : 0
    issue68BindDownEx += bindId == 3 ? 1 : 0
    issue68BindSupport += bindId == 4 ? 1 : 0
    issue68BindNonMd += bindId == 5 ? 1 : 0

float issue68AvgAccRaw = f_issue68S1CompactAvg(issue68SumAccRaw, issue68Bars)
float issue68AvgAccGate = f_issue68S1CompactAvg(issue68SumAccGate, issue68Bars)
float issue68AvgAccEff = f_issue68S1CompactAvg(issue68SumAccEff, issue68Bars)
float issue68AvgMarkupRaw = f_issue68S1CompactAvg(issue68SumMarkupRaw, issue68Bars)
float issue68AvgMarkupGate = f_issue68S1CompactAvg(issue68SumMarkupGate, issue68Bars)
float issue68AvgMarkupEff = f_issue68S1CompactAvg(issue68SumMarkupEff, issue68Bars)

float issue68AvgRangeGate = f_issue68S1CompactAvg(issue68SumRangeGate, issue68Bars)
float issue68AvgBearBgGate = f_issue68S1CompactAvg(issue68SumBearBgGate, issue68Bars)
float issue68AvgDownExGate = f_issue68S1CompactAvg(issue68SumDownExGate, issue68Bars)
float issue68AvgSupportGate = f_issue68S1CompactAvg(issue68SumSupportGate, issue68Bars)
float issue68AvgNonMdGate = f_issue68S1CompactAvg(issue68SumNonMdGate, issue68Bars)
float issue68AvgMinGate = f_issue68S1CompactAvg(issue68SumMinGate, issue68Bars)

float issue68RawS2LeadPct = f_issue68S1CompactPct(issue68RawS2Lead, issue68Bars)
float issue68EffS2LeadPct = f_issue68S1CompactPct(issue68EffS2Lead, issue68Bars)
float issue68RawS2ToEffS1Pct = f_issue68S1CompactPct(issue68RawS2ToEffS1, issue68Bars)

plot(issue68S1CompactInWindow ? 3.0 : na, "EXPECTED Bull", color=colGreen, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68S1CompactValid ? 2.0 : na, "EFF S2 vs S1", color=markupEff > accEff ? colGreen : colRed, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68S1CompactValid ? 1.0 : na, "RAW S2 to EFF S1 flip", color=markupRaw > accRaw and markupEff <= accEff ? colYellow : color.new(colNeutral, 75), linewidth=4, style=plot.style_linebr, display=display.pane)

var table t = table.new(position.bottom_right, 4, 17, border_width=1)
if barstate.islast
    if showIssue68S1CompactTable
        table.cell(t, 0, 0, "S1 COMPACT GATE", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 0, syminfo.ticker, bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 0, "2022-2023 BULL", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 0, str.tostring(issue68Bars) + " bars", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 1, "PIPELINE", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 1, 1, "AVG / SHARE", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 1, "ROLE", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 1, "READ", bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 2, "S1 RAW / gate / eff", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 2, str.tostring(issue68AvgAccRaw, "#.1") + " / " + str.tostring(issue68AvgAccGate, "#.3") + " / " + str.tostring(issue68AvgAccEff, "#.1"), bgcolor=colRed, text_color=color.white)
        table.cell(t, 2, 2, "Accumulation", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 2, "multiply", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 3, "S2 RAW / gate / eff", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 3, str.tostring(issue68AvgMarkupRaw, "#.1") + " / " + str.tostring(issue68AvgMarkupGate, "#.3") + " / " + str.tostring(issue68AvgMarkupEff, "#.1"), bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 3, "Markup ref", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 3, "reference", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 4, "RAW S2 > S1", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 4, str.tostring(issue68RawS2LeadPct, "#.1") + "%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 4, "pre gate", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 4, "ordering", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 5, "EFF S2 > S1", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 5, str.tostring(issue68EffS2LeadPct, "#.1") + "%", bgcolor=issue68EffS2LeadPct >= issue68RawS2LeadPct ? colGreen : colRed, text_color=color.white)
        table.cell(t, 2, 5, "post gate", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 5, "ordering", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 6, "RAW S2 -> EFF S1", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 6, str.tostring(issue68RawS2ToEffS1Pct, "#.1") + "% / " + str.tostring(issue68RawS2ToEffS1), bgcolor=issue68RawS2ToEffS1 > 0 ? colRed : colNeutral, text_color=color.white)
        table.cell(t, 2, 6, "gate flip", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 6, "key test", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 7, "S1 SUB-GATES", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 1, 7, "AVG", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 7, "BOTTLENECK %", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 7, "STACK", bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 8, "Range gate", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 8, str.tostring(issue68AvgRangeGate, "#.3"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 8, str.tostring(f_issue68S1CompactPct(issue68BindRange, issue68Bars), "#.1") + "%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 8, "range", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 9, "Bear-bg gate", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 9, str.tostring(issue68AvgBearBgGate, "#.3"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 9, str.tostring(f_issue68S1CompactPct(issue68BindBearBg, issue68Bars), "#.1") + "%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 9, "history", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 10, "Down-exhaust gate", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 10, str.tostring(issue68AvgDownExGate, "#.3"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 10, str.tostring(f_issue68S1CompactPct(issue68BindDownEx, issue68Bars), "#.1") + "%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 10, "exhaust", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 11, "Support gate", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 11, str.tostring(issue68AvgSupportGate, "#.3"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 11, str.tostring(f_issue68S1CompactPct(issue68BindSupport, issue68Bars), "#.1") + "%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 11, "support", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 12, "Non-MD cont gate", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 12, str.tostring(issue68AvgNonMdGate, "#.3"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 12, str.tostring(f_issue68S1CompactPct(issue68BindNonMd, issue68Bars), "#.1") + "%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 12, "anti-S5", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 13, "Avg minimum gate", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 13, str.tostring(issue68AvgMinGate, "#.3"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 13, "per-bar min", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 13, "bottleneck", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 14, "INTERPRET", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 1, 14, "FR vs DE", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 14, "NO TUNING", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 14, "FROZEN C-2", bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 15, "Focus", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 15, "higher S1 gate", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 15, "+ bottleneck share", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 15, "root attribution", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 16, "READ", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 16, "Green=S2 lead", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 16, "Red=S1 lead", bgcolor=colRed, text_color=color.white)
        table.cell(t, 3, 16, "Yellow=gate flip", bgcolor=colYellow, text_color=color.white)
    else
        table.clear(t, 0, 0, 3, 16)
'''.strip()


def generate(source: Path) -> str:
    d1_text = phase_b.d1.generate(source)
    if d1_text.count(phase_b.D1_EXPORT_MARKER) != 1:
        raise RuntimeError("expected exactly one D1 parity export marker")
    core = d1_text.split(phase_b.D1_EXPORT_MARKER, 1)[0].rstrip()
    core = replace_once(core, phase_b.D1_INDICATOR_DECL, AUDIT_DECL)
    out = core + "\n\n" + BODY + "\n"
    required = (
        "S1 Compact Gate Root Attribution Audit",
        "RAW S2 -> EFF S1",
        "S1 SUB-GATES",
        "BOTTLENECK %",
        "Avg minimum gate",
    )
    for token in required:
        if token not in out:
            raise RuntimeError(f"missing S1 compact gate token: {token}")
    if "strategy." in out:
        raise RuntimeError("strategy token leaked into S1 compact gate diagnostic")
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
