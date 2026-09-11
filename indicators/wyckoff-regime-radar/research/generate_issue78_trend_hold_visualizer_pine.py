#!/usr/bin/env python3
"""Generate the Issue #78 TradingView research visualizer from the frozen #68 RC.

The classifier is copied mechanically from the frozen production-research source.
Only indicator identity/default dashboard visibility and an appended research-only
visualization layer are changed. No classifier threshold, weight, gate, witness,
or lifecycle logic is altered.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "indicators/wyckoff-regime-radar/src/chase-risk-market-regime-radar-issue68-rc.pine"
DEFAULT_OUTPUT = ROOT / "indicators/wyckoff-regime-radar/research/generated/wyckoff-issue78-trend-hold-visualizer.pine"
EXPECTED_BLOB_SHA = "e5c3fd2622841a6d3f97bdda4b9d0a6378ebda55"

OLD_DECL = 'indicator("Chase Risk Market Regime Radar｜Issue #68 RC", shorttitle="ChaseRisk Radar #68 RC", overlay=false, precision=1)'
NEW_DECL = 'indicator("Chase Risk Trend Hold Lab｜Issue #78", shorttitle="Trend Hold Lab #78", overlay=false, precision=1)'
OLD_TABLE_DEFAULT = 'showTable        = input.bool(true, "顯示 Dashboard", group=groupDisplay)'
NEW_TABLE_DEFAULT = 'showTable        = input.bool(false, "顯示原始 Dashboard", group=groupDisplay)'
ANCHOR = "\n// Visuals\n"

INJECTION = r'''

// ============================================================================
// Issue #78 research-only Trend Hold Lab visualizer
// ----------------------------------------------------------------------------
// Discovery aid only. This layer does NOT change formalId or any classifier
// semantics. It visualizes the already-preregistered giveback buckets and the
// Gentle / Balanced damage-latch exposure ladders from Issue #78.
// Exposure shown on bar t is the target for the NEXT bar t -> t+1.
// ============================================================================

groupIssue78 = "研究｜Issue #78 趨勢持有視覺化"
issue78Show = input.bool(true, "顯示 Issue #78 Trend Hold Lab", group=groupIssue78)
issue78PlotMode = input.string("Both", "顯示曝險梯", options=["Gentle + Latch", "Balanced + Latch", "Both"], group=groupIssue78)
issue78ShowEvents = input.bool(true, "顯示減倉 / 加回事件", group=groupIssue78)
issue78ShowPanel = input.bool(true, "顯示研究面板", group=groupIssue78)
issue78GentleColor = input.color(color.rgb(80, 180, 255), "Gentle 線色", group=groupIssue78)
issue78BalancedColor = input.color(color.rgb(255, 170, 40), "Balanced 線色", group=groupIssue78)

f_issue78Bucket(float g) =>
    na(g) ? -1 : g < 0.5 ? 0 : g < 1.0 ? 1 : g < 2.0 ? 2 : g < 4.0 ? 3 : 4

f_issue78BucketText(int b) =>
    b == 0 ? "健康｜<0.5 ATR" :
     b == 1 ? "輕微受損｜0.5–1 ATR" :
     b == 2 ? "受損｜1–2 ATR" :
     b == 3 ? "明顯受損｜2–4 ATR" :
     b == 4 ? "嚴重受損｜4+ ATR" : "非趨勢階段"

f_issue78GentleTarget(int b) =>
    b <= 0 ? 1.00 : b == 1 ? 1.00 : b == 2 ? 0.75 : b == 3 ? 0.50 : 0.25

f_issue78BalancedTarget(int b) =>
    b <= 0 ? 1.00 : b == 1 ? 0.75 : b == 2 ? 0.50 : b == 3 ? 0.25 : 0.00

issue78TrendActive = formalId == 2 or formalId == 5
issue78Direction = formalId == 2 ? 1 : formalId == 5 ? -1 : 0
issue78NewEpisode = issue78TrendActive and formalId != formalId[1]

var float issue78EntryScale = na
var float issue78Extreme = na
var int issue78Age = 0
var float issue78GentleLatch = 0.0
var float issue78BalancedLatch = 0.0

bool issue78NewFavorableExtreme = false
float issue78Giveback = na
int issue78Bucket = -1

if issue78NewEpisode
    issue78EntryScale := symATR
    issue78Extreme := modelPrice
    issue78Age := 0
    issue78GentleLatch := 1.0
    issue78BalancedLatch := 1.0
else if issue78TrendActive
    issue78Age += 1
    issue78NewFavorableExtreme := formalId == 2 ? modelPrice > issue78Extreme : modelPrice < issue78Extreme
    if issue78NewFavorableExtreme
        issue78Extreme := modelPrice
        issue78GentleLatch := 1.0
        issue78BalancedLatch := 1.0
else
    issue78EntryScale := na
    issue78Extreme := na
    issue78Age := 0
    issue78GentleLatch := 0.0
    issue78BalancedLatch := 0.0

if issue78TrendActive and not na(issue78EntryScale) and issue78EntryScale > 0 and not na(issue78Extreme)
    issue78Giveback := formalId == 2 ? math.max(issue78Extreme - modelPrice, 0.0) / issue78EntryScale : math.max(modelPrice - issue78Extreme, 0.0) / issue78EntryScale
    issue78Bucket := f_issue78Bucket(issue78Giveback)
    issue78GentleTarget = f_issue78GentleTarget(issue78Bucket)
    issue78BalancedTarget = f_issue78BalancedTarget(issue78Bucket)
    if issue78GentleTarget < issue78GentleLatch
        issue78GentleLatch := issue78GentleTarget
    if issue78BalancedTarget < issue78BalancedLatch
        issue78BalancedLatch := issue78BalancedTarget

issue78GentleSigned = issue78TrendActive ? issue78Direction * issue78GentleLatch * 100.0 : 0.0
issue78BalancedSigned = issue78TrendActive ? issue78Direction * issue78BalancedLatch * 100.0 : 0.0

issue78GentleDerisk = issue78TrendActive and not issue78NewEpisode and issue78GentleLatch < nz(issue78GentleLatch[1], issue78GentleLatch)
issue78BalancedDerisk = issue78TrendActive and not issue78NewEpisode and issue78BalancedLatch < nz(issue78BalancedLatch[1], issue78BalancedLatch)
issue78GentleRerisk = issue78TrendActive and not issue78NewEpisode and issue78GentleLatch > nz(issue78GentleLatch[1], issue78GentleLatch)
issue78BalancedRerisk = issue78TrendActive and not issue78NewEpisode and issue78BalancedLatch > nz(issue78BalancedLatch[1], issue78BalancedLatch)
issue78AnyDerisk = issue78GentleDerisk or issue78BalancedDerisk
issue78AnyRerisk = issue78GentleRerisk or issue78BalancedRerisk

issue78ShowGentle = issue78Show and (issue78PlotMode == "Gentle + Latch" or issue78PlotMode == "Both")
issue78ShowBalanced = issue78Show and (issue78PlotMode == "Balanced + Latch" or issue78PlotMode == "Both")

plot(issue78ShowGentle ? issue78GentleSigned : na, "#78 Gentle + Latch｜下一根目標曝險 %", color=issue78GentleColor, linewidth=3, style=plot.style_stepline)
plot(issue78ShowBalanced ? issue78BalancedSigned : na, "#78 Balanced + Latch｜下一根目標曝險 %", color=issue78BalancedColor, linewidth=2, style=plot.style_stepline)
hline(-100, "#78 Full Short", color=color.new(color.gray, 80), linestyle=hline.style_dotted)

plotshape(issue78Show and issue78ShowEvents and issue78AnyDerisk, title="#78 De-risk", text="減", style=shape.triangledown, location=location.top, color=color.new(color.orange, 0), textcolor=color.white, size=size.tiny)
plotshape(issue78Show and issue78ShowEvents and issue78AnyRerisk, title="#78 Re-risk", text="加", style=shape.triangleup, location=location.bottom, color=color.new(color.aqua, 0), textcolor=color.black, size=size.tiny)
plotshape(issue78Show and issue78ShowEvents and issue78NewEpisode, title="#78 Trend episode start", text="趨", style=shape.circle, location=location.absolute, color=formalId == 2 ? color.new(color.green, 0) : color.new(color.red, 0), textcolor=color.white, size=size.tiny)

var table issue78Dash = table.new(position.bottom_right, 2, 9, border_width=1)
if barstate.islast
    table.clear(issue78Dash, 0, 0, 1, 8)
    if issue78Show and issue78ShowPanel
        issue78PanelBg = color.new(color.rgb(40, 40, 40), 12)
        issue78StateColor = issue78TrendActive ? f_stageColor(formalId) : color.new(color.gray, 25)
        issue78DirText = formalId == 2 ? "正方向｜拉升" : formalId == 5 ? "負方向｜崩跌" : "等待｜非主要趨勢"
        issue78LatchText = not issue78TrendActive ? "—" : issue78NewFavorableExtreme ? "重新證明｜恢復 Full" : (issue78GentleLatch < 1.0 or issue78BalancedLatch < 1.0) ? "受損鎖定｜等新極值" : "健康｜Full"
        table.cell(issue78Dash, 0, 0, "Issue #78 Trend Hold Lab", text_color=color.white, bgcolor=color.new(color.rgb(25, 25, 25), 0))
        table.cell(issue78Dash, 1, 0, "研究用｜非交易訊號", text_color=color.yellow, bgcolor=color.new(color.rgb(25, 25, 25), 0))
        table.cell(issue78Dash, 0, 1, "正式環境", text_color=color.white, bgcolor=issue78PanelBg)
        table.cell(issue78Dash, 1, 1, issue78DirText, text_color=color.white, bgcolor=issue78StateColor)
        table.cell(issue78Dash, 0, 2, "Regime Age", text_color=color.white, bgcolor=issue78PanelBg)
        table.cell(issue78Dash, 1, 2, issue78TrendActive ? str.tostring(issue78Age) + " bars" : "—", text_color=color.white, bgcolor=issue78PanelBg)
        table.cell(issue78Dash, 0, 3, "距 Regime 極值回吐", text_color=color.white, bgcolor=issue78PanelBg)
        table.cell(issue78Dash, 1, 3, issue78TrendActive ? str.tostring(issue78Giveback, "#.##") + " ATR" : "—", text_color=color.white, bgcolor=issue78PanelBg)
        table.cell(issue78Dash, 0, 4, "Trend Health", text_color=color.white, bgcolor=issue78PanelBg)
        table.cell(issue78Dash, 1, 4, f_issue78BucketText(issue78Bucket), text_color=color.white, bgcolor=issue78PanelBg)
        table.cell(issue78Dash, 0, 5, "Gentle + Latch", text_color=issue78GentleColor, bgcolor=issue78PanelBg)
        table.cell(issue78Dash, 1, 5, str.tostring(issue78GentleSigned, "#.0") + "% next", text_color=issue78GentleColor, bgcolor=issue78PanelBg)
        table.cell(issue78Dash, 0, 6, "Balanced + Latch", text_color=issue78BalancedColor, bgcolor=issue78PanelBg)
        table.cell(issue78Dash, 1, 6, str.tostring(issue78BalancedSigned, "#.0") + "% next", text_color=issue78BalancedColor, bgcolor=issue78PanelBg)
        table.cell(issue78Dash, 0, 7, "Damage Latch", text_color=color.white, bgcolor=issue78PanelBg)
        table.cell(issue78Dash, 1, 7, issue78LatchText, text_color=color.white, bgcolor=issue78PanelBg)
        table.cell(issue78Dash, 0, 8, "規則", text_color=color.white, bgcolor=issue78PanelBg)
        table.cell(issue78Dash, 1, 8, "減倉快｜新極值才加回", text_color=color.white, bgcolor=issue78PanelBg)
'''


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def generate(output: Path) -> None:
    raw = SOURCE.read_bytes()
    actual = git_blob_sha(raw)
    if actual != EXPECTED_BLOB_SHA:
        raise SystemExit(f"frozen source drift: expected {EXPECTED_BLOB_SHA}, got {actual}")
    source = raw.decode("utf-8")
    if source.count(OLD_DECL) != 1:
        raise SystemExit("indicator declaration anchor missing or duplicated")
    if source.count(OLD_TABLE_DEFAULT) != 1:
        raise SystemExit("dashboard default anchor missing or duplicated")
    if source.count(ANCHOR) != 1:
        raise SystemExit("visual anchor missing or duplicated")

    source = source.replace(OLD_DECL, NEW_DECL, 1)
    source = source.replace(OLD_TABLE_DEFAULT, NEW_TABLE_DEFAULT, 1)
    source = source.replace(ANCHOR, INJECTION + ANCHOR, 1)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(source, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    generate(args.output)
    print(args.output)


if __name__ == "__main__":
    main()
