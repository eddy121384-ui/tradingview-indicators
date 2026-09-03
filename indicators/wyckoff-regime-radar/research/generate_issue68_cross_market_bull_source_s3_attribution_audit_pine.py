#!/usr/bin/env python3
"""Generate Issue #68 FR10Y vs DE10Y Bull-source / S3 attribution Pine."""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_phase_b_lifecycle_pine as phase_b
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent
AUDIT_DECL = 'indicator("Chase Risk Radar｜Issue #68 Bull Source S3", shorttitle="ChaseRisk #68 S3", overlay=false, precision=2)'

BODY = r'''

// ============================================================================
// Issue #68 FR10Y vs DE10Y Bull-source / S3 Attribution Audit.
// Shared window: 2022-01-03 -> 2023-12-29, expected Bull yield regime.
// DISCOVERY ONLY. NO PNL. NO TUNING. FROZEN C-2.
// ============================================================================

groupIssue68S3 = "Issue #68｜Bull Source / S3 Attribution"
showIssue68S3Table = input.bool(true, "顯示 Bull Source / S3 統計表", group=groupIssue68S3)

issue68S3Ready = bar_index >= rankLen - 1
int issue68S3Start = timestamp(2022, 1, 3, 0, 0)
int issue68S3End = timestamp(2023, 12, 29, 23, 59)
bool issue68S3InWindow = issue68S3Ready and time >= issue68S3Start and time <= issue68S3End

f_issue68S3Avg(float s, int n) => n > 0 ? s / n : na
f_issue68S3Pct(int n, int d) => d > 0 ? 100.0 * n / d : na

float issue68BestBullVal = math.max(p2, p3)
int issue68BestBullId = p2 >= p3 ? 2 : 3
float issue68BestNonBullVal = p1
int issue68BestNonBullId = 1
if p4 > issue68BestNonBullVal
    issue68BestNonBullVal := p4
    issue68BestNonBullId := 4
if p5 > issue68BestNonBullVal
    issue68BestNonBullVal := p5
    issue68BestNonBullId := 5
if p6 > issue68BestNonBullVal
    issue68BestNonBullVal := p6
    issue68BestNonBullId := 6
float issue68BullMargin = issue68BestBullVal - issue68BestNonBullVal

var int issue68Bars = 0
var int issue68TopS1 = 0
var int issue68TopS2 = 0
var int issue68TopS3 = 0
var int issue68TopS4 = 0
var int issue68TopS5 = 0
var int issue68TopS6 = 0
var int issue68BullLeadS2 = 0
var int issue68BullLeadS3 = 0
var float issue68SumS2Gap = 0.0
var float issue68SumS3Gap = 0.0
var int issue68S2GapPass = 0
var int issue68S3GapPass = 0
var float issue68SumBullMargin = 0.0

var float issue68SumBullBg = 0.0
var float issue68SumRange = 0.0
var float issue68SumSupport = 0.0
var float issue68SumNoPanic = 0.0
var float issue68SumNoExhaust = 0.0
var float issue68SumReaccRaw = 0.0
var float issue68SumReaccGate = 0.0
var float issue68SumReaccEff = 0.0
var float issue68SumP2 = 0.0
var float issue68SumP3 = 0.0

if issue68S3InWindow
    issue68Bars += 1
    issue68TopS1 += topId == 1 ? 1 : 0
    issue68TopS2 += topId == 2 ? 1 : 0
    issue68TopS3 += topId == 3 ? 1 : 0
    issue68TopS4 += topId == 4 ? 1 : 0
    issue68TopS5 += topId == 5 ? 1 : 0
    issue68TopS6 += topId == 6 ? 1 : 0
    issue68BullLeadS2 += issue68BestBullId == 2 ? 1 : 0
    issue68BullLeadS3 += issue68BestBullId == 3 ? 1 : 0
    if topId == 2
        issue68SumS2Gap += topGap
        issue68S2GapPass += topGap >= topGapMin ? 1 : 0
    if topId == 3
        issue68SumS3Gap += topGap
        issue68S3GapPass += topGap >= topGapMin ? 1 : 0
    issue68SumBullMargin += issue68BullMargin

    issue68SumBullBg += bullBg
    issue68SumRange += rangeScore
    issue68SumSupport += supportHolding
    issue68SumNoPanic += 100.0 - panicHeatDn
    issue68SumNoExhaust += 100.0 - upsideExhaustion
    issue68SumReaccRaw += reaccRaw
    issue68SumReaccGate += reaccGate
    issue68SumReaccEff += reaccEff
    issue68SumP2 += p2
    issue68SumP3 += p3

int issue68BullTopBars = issue68TopS2 + issue68TopS3
float issue68TopS2Pct = f_issue68S3Pct(issue68TopS2, issue68Bars)
float issue68TopS3Pct = f_issue68S3Pct(issue68TopS3, issue68Bars)
float issue68BullTopPct = f_issue68S3Pct(issue68BullTopBars, issue68Bars)
float issue68BullLeadS2Pct = f_issue68S3Pct(issue68BullLeadS2, issue68Bars)
float issue68BullLeadS3Pct = f_issue68S3Pct(issue68BullLeadS3, issue68Bars)
float issue68S2AvgGap = f_issue68S3Avg(issue68SumS2Gap, issue68TopS2)
float issue68S3AvgGap = f_issue68S3Avg(issue68SumS3Gap, issue68TopS3)
float issue68S2GapPassPct = f_issue68S3Pct(issue68S2GapPass, issue68TopS2)
float issue68S3GapPassPct = f_issue68S3Pct(issue68S3GapPass, issue68TopS3)
float issue68AvgBullMargin = f_issue68S3Avg(issue68SumBullMargin, issue68Bars)

float issue68AvgBullBg = f_issue68S3Avg(issue68SumBullBg, issue68Bars)
float issue68AvgRange = f_issue68S3Avg(issue68SumRange, issue68Bars)
float issue68AvgSupport = f_issue68S3Avg(issue68SumSupport, issue68Bars)
float issue68AvgNoPanic = f_issue68S3Avg(issue68SumNoPanic, issue68Bars)
float issue68AvgNoExhaust = f_issue68S3Avg(issue68SumNoExhaust, issue68Bars)
float issue68AvgReaccRaw = f_issue68S3Avg(issue68SumReaccRaw, issue68Bars)
float issue68AvgReaccGate = f_issue68S3Avg(issue68SumReaccGate, issue68Bars)
float issue68AvgReaccEff = f_issue68S3Avg(issue68SumReaccEff, issue68Bars)
float issue68AvgP2 = f_issue68S3Avg(issue68SumP2, issue68Bars)
float issue68AvgP3 = f_issue68S3Avg(issue68SumP3, issue68Bars)

// Minimal plot-safe lanes: only three plots.
plot(issue68S3InWindow ? 3.0 : na, "EXPECTED Bull", color=colGreen, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68S3InWindow ? 2.0 : na, "Bull TOP source", color=topId == 2 ? colGreen : topId == 3 ? colYellow : colRed, linewidth=4, style=plot.style_linebr, display=display.pane)
plot(issue68S3InWindow ? 1.0 : na, "Bull margin sign", color=issue68BullMargin >= 0 ? colGreen : colRed, linewidth=4, style=plot.style_linebr, display=display.pane)

var table t = table.new(position.bottom_right, 4, 25, border_width=1)
if barstate.islast
    if showIssue68S3Table
        table.cell(t, 0, 0, "BULL SOURCE / S3", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 0, syminfo.ticker, bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 0, "2022-2023 BULL", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 0, str.tostring(issue68Bars) + " bars", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 1, "TOP SOURCE", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 1, 1, "SHARE", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 1, "AVG GAP", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 1, "GAP PASS", bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 2, "S2 Markup TOP", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 2, str.tostring(issue68TopS2Pct, "#.1") + "%", bgcolor=issue68TopS2 > 0 ? colGreen : colNeutral, text_color=color.white)
        table.cell(t, 2, 2, str.tostring(issue68S2AvgGap, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 2, str.tostring(issue68S2GapPassPct, "#.1") + "%", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 3, "S3 Reacc TOP", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 3, str.tostring(issue68TopS3Pct, "#.1") + "%", bgcolor=issue68TopS3 > 0 ? colGreen : colNeutral, text_color=color.white)
        table.cell(t, 2, 3, str.tostring(issue68S3AvgGap, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 3, str.tostring(issue68S3GapPassPct, "#.1") + "%", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 4, "Bull TOP total", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 4, str.tostring(issue68BullTopPct, "#.1") + "%", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 4, "S2+S3", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 4, "final TOP", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 5, "Bull sibling leader S2", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 5, str.tostring(issue68BullLeadS2Pct, "#.1") + "%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 5, "p2>=p3", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 5, "inside Bull", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 6, "Bull sibling leader S3", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 6, str.tostring(issue68BullLeadS3Pct, "#.1") + "%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 6, "p3>p2", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 6, "inside Bull", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 7, "Best Bull - best nonBull", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 7, str.tostring(issue68AvgBullMargin, "#.1"), bgcolor=issue68AvgBullMargin >= 0 ? colGreen : colRed, text_color=color.white)
        table.cell(t, 2, 7, "avg score", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 7, "global margin", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 8, "NON-BULL TOP", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 8, "SHARE", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 8, "ROLE", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 8, "COUNT", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 9, "S1 Acc", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 9, str.tostring(f_issue68S3Pct(issue68TopS1, issue68Bars), "#.1") + "%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 9, "Neutral", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 9, str.tostring(issue68TopS1), bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 10, "S4 Dist", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 10, str.tostring(f_issue68S3Pct(issue68TopS4, issue68Bars), "#.1") + "%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 10, "Neutral", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 10, str.tostring(issue68TopS4), bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 11, "S5 Markdown", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 11, str.tostring(f_issue68S3Pct(issue68TopS5, issue68Bars), "#.1") + "%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 11, "Bear", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 11, str.tostring(issue68TopS5), bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 12, "S6 Redist", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 12, str.tostring(f_issue68S3Pct(issue68TopS6, issue68Bars), "#.1") + "%", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 12, "Bear", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 12, str.tostring(issue68TopS6), bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 13, "S3 REACC ENGINE", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 1, 13, "AVG", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 13, "ROLE", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 3, 13, "FROZEN", bgcolor=colGreen, text_color=color.white)

        table.cell(t, 0, 14, "Bull background", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 14, str.tostring(issue68AvgBullBg, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 14, "RAW input", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 14, "20%", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 15, "Range score", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 15, str.tostring(issue68AvgRange, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 15, "RAW input", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 15, "20%", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 16, "Support holding", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 16, str.tostring(issue68AvgSupport, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 16, "RAW input", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 16, "25%", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 17, "No panicDn", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 17, str.tostring(issue68AvgNoPanic, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 17, "RAW input", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 17, "20%", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 18, "No upside exhaust", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 18, str.tostring(issue68AvgNoExhaust, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 18, "RAW input", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 18, "15%", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 19, "S3 Reacc RAW", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 19, str.tostring(issue68AvgReaccRaw, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 19, "raw", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 19, "smoothed", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 20, "S3 gate", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 20, str.tostring(issue68AvgReaccGate, "#.3"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 20, "0-1", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 20, "gate stack", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 21, "S3 effective", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 21, str.tostring(issue68AvgReaccEff, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 21, "eff", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 21, "post gate", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 22, "Avg p2 / p3", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 22, str.tostring(issue68AvgP2, "#.1") + " / " + str.tostring(issue68AvgP3, "#.1"), bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 22, "TOP probs", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 22, "S2 / S3", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 23, "MODE", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 23, "DISCOVERY", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 2, 23, "NO TUNING", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 3, 23, "FROZEN C-2", bgcolor=colNeutral, text_color=color.white)

        table.cell(t, 0, 24, "READ", bgcolor=colNeutral, text_color=color.white)
        table.cell(t, 1, 24, "Green=S2", bgcolor=colGreen, text_color=color.white)
        table.cell(t, 2, 24, "Yellow=S3", bgcolor=colYellow, text_color=color.white)
        table.cell(t, 3, 24, "Red=nonBull", bgcolor=colRed, text_color=color.white)
    else
        table.clear(t, 0, 0, 3, 24)
'''.strip()


def generate(source: Path) -> str:
    d1_text = phase_b.d1.generate(source)
    if d1_text.count(phase_b.D1_EXPORT_MARKER) != 1:
        raise RuntimeError("expected exactly one D1 parity export marker")
    core = d1_text.split(phase_b.D1_EXPORT_MARKER, 1)[0].rstrip()
    core = replace_once(core, phase_b.D1_INDICATOR_DECL, AUDIT_DECL)
    out = core + "\n\n" + BODY + "\n"
    required = (
        "Bull-source / S3 Attribution Audit",
        "S2 Markup TOP",
        "S3 Reacc TOP",
        "Best Bull - best nonBull",
        "S3 REACC ENGINE",
        "reaccGate",
        "Avg p2 / p3",
    )
    for token in required:
        if token not in out:
            raise RuntimeError(f"missing Bull-source / S3 token: {token}")
    if "strategy." in out:
        raise RuntimeError("strategy token leaked into Bull-source / S3 diagnostic")
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
