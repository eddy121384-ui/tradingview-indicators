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
// Discovery aid only. This layer does NOT change formalId or classifier
// semantics. It combines the preregistered Participation Ramp with the frozen
// Damage-Latch de-risk/re-risk layer. Exposure shown on bar t is the target for
// the NEXT bar t -> t+1.
// ============================================================================

groupIssue78 = "研究｜Issue #78 趨勢持有視覺化"
issue78Show = input.bool(true, "顯示 Issue #78 Trend Hold Lab", group=groupIssue78)
issue78ParticipationMode = input.string("Excursion-Proof", "Participation Ramp", options=["Full-at-entry", "Persistence", "Excursion-Proof"], group=groupIssue78)
issue78DamageMode = input.string("Gentle + Latch", "Damage 管理", options=["Gentle + Latch", "Balanced + Latch"], group=groupIssue78)
issue78ShowEvents = input.bool(true, "顯示試單 / 加碼 / 減倉事件", group=groupIssue78)
issue78ShowPanel = input.bool(true, "顯示研究面板", group=groupIssue78)
issue78ShowComponents = input.bool(false, "顯示 Participation / Damage 元件線", group=groupIssue78)
issue78TargetColor = input.color(color.rgb(70, 180, 255), "最終曝險線色", group=groupIssue78)
issue78PartColor = input.color(color.rgb(80, 210, 130), "Participation 線色", group=groupIssue78)
issue78DamageColor = input.color(color.rgb(255, 170, 40), "Damage 線色", group=groupIssue78)

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

f_issue78PersistenceCap(int age) =>
    age < 5 ? 0.25 : age < 10 ? 0.50 : age < 20 ? 0.75 : 1.00

f_issue78ProofCap(float mfe) =>
    mfe < 0.5 ? 0.25 : mfe < 1.0 ? 0.50 : mfe < 2.0 ? 0.75 : 1.00

f_issue78PartText(float cap) =>
    cap <= 0.25 ? "Probe 25%" : cap <= 0.50 ? "Build 50%" : cap <= 0.75 ? "Confirmed 75%" : "Full 100%"

issue78TrendActive = formalId == 2 or formalId == 5
issue78Direction = formalId == 2 ? 1 : formalId == 5 ? -1 : 0
issue78NewEpisode = issue78TrendActive and formalId != formalId[1]

var float issue78EntryScale = na
var float issue78EntryPrice = na
var float issue78Extreme = na
var float issue78Mfe = 0.0
var int issue78Age = 0
var float issue78GentleLatch = 0.0
var float issue78BalancedLatch = 0.0

bool issue78NewFavorableExtreme = false
float issue78Giveback = na
int issue78Bucket = -1

if issue78NewEpisode
    issue78EntryScale := symATR
    issue78EntryPrice := modelPrice
    issue78Extreme := modelPrice
    issue78Mfe := 0.0
    issue78Age := 0
    issue78GentleLatch := 1.0
    issue78BalancedLatch := 1.0
else if issue78TrendActive
    issue78Age += 1
    if not na(issue78EntryScale) and issue78EntryScale > 0 and not na(issue78EntryPrice)
        issue78FavorableFromEntry = issue78Direction == 1 ? (modelPrice - issue78EntryPrice) / issue78EntryScale : (issue78EntryPrice - modelPrice) / issue78EntryScale
        issue78Mfe := math.max(issue78Mfe, math.max(issue78FavorableFromEntry, 0.0))
    issue78NewFavorableExtreme := formalId == 2 ? modelPrice > issue78Extreme : modelPrice < issue78Extreme
    if issue78NewFavorableExtreme
        issue78Extreme := modelPrice
        issue78GentleLatch := 1.0
        issue78BalancedLatch := 1.0
else
    issue78EntryScale := na
    issue78EntryPrice := na
    issue78Extreme := na
    issue78Mfe := 0.0
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

issue78FullCap = issue78TrendActive ? 1.0 : 0.0
issue78PersistenceCap = issue78TrendActive ? f_issue78PersistenceCap(issue78Age) : 0.0
issue78ProofCap = issue78TrendActive ? f_issue78ProofCap(issue78Mfe) : 0.0
issue78ParticipationCap = issue78ParticipationMode == "Persistence" ? issue78PersistenceCap : issue78ParticipationMode == "Excursion-Proof" ? issue78ProofCap : issue78FullCap
issue78DamageCap = issue78DamageMode == "Balanced + Latch" ? issue78BalancedLatch : issue78GentleLatch
issue78Target = issue78TrendActive ? math.min(issue78ParticipationCap, issue78DamageCap) : 0.0

issue78TargetSigned = issue78Direction * issue78Target * 100.0
issue78PartSigned = issue78Direction * issue78ParticipationCap * 100.0
issue78DamageSigned = issue78Direction * issue78DamageCap * 100.0

issue78Add = issue78TrendActive and not issue78NewEpisode and issue78Target > nz(issue78Target[1], issue78Target)
issue78Reduce = issue78TrendActive and not issue78NewEpisode and issue78Target < nz(issue78Target[1], issue78Target)
issue78ReachedFull = issue78TrendActive and issue78Target >= 1.0 and nz(issue78Target[1], 0.0) < 1.0

plot(issue78Show ? issue78TargetSigned : na, "#78 目標曝險 %", color=issue78TargetColor, linewidth=3, style=plot.style_stepline)
plot(issue78Show and issue78ShowComponents ? issue78PartSigned : na, "#78 Participation Cap %", color=color.new(issue78PartColor, 10), linewidth=1, style=plot.style_stepline)
plot(issue78Show and issue78ShowComponents ? issue78DamageSigned : na, "#78 Damage Cap %", color=color.new(issue78DamageColor, 10), linewidth=1, style=plot.style_stepline)
hline(100, "#78 Full Long", color=color.new(color.gray, 85), linestyle=hline.style_dotted)
hline(0, "#78 Flat", color=color.new(color.gray, 88), linestyle=hline.style_dotted)
hline(-100, "#78 Full Short", color=color.new(color.gray, 85), linestyle=hline.style_dotted)

plotshape(issue78Show and issue78ShowEvents and issue78NewEpisode, title="#78 Probe start", text="試", style=shape.circle, location=location.absolute, color=formalId == 2 ? color.new(color.green, 0) : color.new(color.red, 0), textcolor=color.white, size=size.tiny)
plotshape(issue78Show and issue78ShowEvents and issue78Add and not issue78ReachedFull, title="#78 Add", text="加", style=shape.triangleup, location=location.bottom, color=color.new(color.aqua, 0), textcolor=color.black, size=size.tiny)
plotshape(issue78Show and issue78ShowEvents and issue78ReachedFull, title="#78 Full", text="滿", style=shape.triangleup, location=location.bottom, color=color.new(color.lime, 0), textcolor=color.black, size=size.tiny)
plotshape(issue78Show and issue78ShowEvents and issue78Reduce, title="#78 Reduce", text="減", style=shape.triangledown, location=location.top, color=color.new(color.orange, 0), textcolor=color.white, size=size.tiny)

var table issue78Dash = table.new(position.bottom_right, 2, 9, border_width=1)
if barstate.islast
    table.clear(issue78Dash, 0, 0, 1, 8)
    if issue78Show and issue78ShowPanel
        issue78PanelBg = color.new(color.rgb(40, 40, 40), 12)
        issue78StateColor = issue78TrendActive ? f_stageColor(formalId) : color.new(color.gray, 25)
        issue78DirText = formalId == 2 ? "拉升｜多方向" : formalId == 5 ? "崩跌｜空方向" : "等待｜非主要趨勢"
        issue78RuleText = issue78ParticipationMode + " × " + issue78DamageMode
        table.cell(issue78Dash, 0, 0, "Issue #78 Position Lifecycle", text_color=color.white, bgcolor=color.new(color.rgb(25, 25, 25), 0))
        table.cell(issue78Dash, 1, 0, "研究用｜非交易訊號", text_color=color.yellow, bgcolor=color.new(color.rgb(25, 25, 25), 0))
        table.cell(issue78Dash, 0, 1, "正式環境", text_color=color.white, bgcolor=issue78PanelBg)
        table.cell(issue78Dash, 1, 1, issue78DirText, text_color=color.white, bgcolor=issue78StateColor)
        table.cell(issue78Dash, 0, 2, "Age / MFE", text_color=color.white, bgcolor=issue78PanelBg)
        table.cell(issue78Dash, 1, 2, issue78TrendActive ? str.tostring(issue78Age) + " bars｜" + str.tostring(issue78Mfe, "#.##") + " ATR" : "—", text_color=color.white, bgcolor=issue78PanelBg)
        table.cell(issue78Dash, 0, 3, "Trend Health", text_color=color.white, bgcolor=issue78PanelBg)
        table.cell(issue78Dash, 1, 3, f_issue78BucketText(issue78Bucket), text_color=color.white, bgcolor=issue78PanelBg)
        table.cell(issue78Dash, 0, 4, "Participation", text_color=issue78PartColor, bgcolor=issue78PanelBg)
        table.cell(issue78Dash, 1, 4, issue78TrendActive ? f_issue78PartText(issue78ParticipationCap) : "—", text_color=issue78PartColor, bgcolor=issue78PanelBg)
        table.cell(issue78Dash, 0, 5, "Damage Cap", text_color=issue78DamageColor, bgcolor=issue78PanelBg)
        table.cell(issue78Dash, 1, 5, issue78TrendActive ? str.tostring(issue78DamageCap * 100.0, "#.0") + "%" : "—", text_color=issue78DamageColor, bgcolor=issue78PanelBg)
        table.cell(issue78Dash, 0, 6, "下一根目標曝險", text_color=issue78TargetColor, bgcolor=issue78PanelBg)
        table.cell(issue78Dash, 1, 6, issue78TrendActive ? str.tostring(issue78TargetSigned, "#.0") + "%" : "0%", text_color=issue78TargetColor, bgcolor=issue78PanelBg)
        table.cell(issue78Dash, 0, 7, "規則", text_color=color.white, bgcolor=issue78PanelBg)
        table.cell(issue78Dash, 1, 7, issue78RuleText, text_color=color.white, bgcolor=issue78PanelBg)
        table.cell(issue78Dash, 0, 8, "生命週期", text_color=color.white, bgcolor=issue78PanelBg)
        table.cell(issue78Dash, 1, 8, "試單→加碼→減倉→再加回", text_color=color.white, bgcolor=issue78PanelBg)
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
