#!/usr/bin/env python3
"""Generate Issue #78 Trendability / Oscillation Lab from the frozen #68 RC.

Classifier semantics are copied mechanically and remain unchanged. The generated
research script hides the original risk/dashboard clutter, keeps formal regime
background context, and adds a preregistered 63/126/252-bar path-efficiency
visualizer plus a compact fresh-trend-entry logger.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "indicators/wyckoff-regime-radar/src/chase-risk-market-regime-radar-issue68-rc.pine"
DEFAULT_OUTPUT = ROOT / "indicators/wyckoff-regime-radar/research/generated/wyckoff-issue78-trendability-visualizer.pine"
EXPECTED_BLOB_SHA = "e5c3fd2622841a6d3f97bdda4b9d0a6378ebda55"

OLD_DECL = 'indicator("Chase Risk Market Regime Radar｜Issue #68 RC", shorttitle="ChaseRisk Radar #68 RC", overlay=false, precision=1)'
NEW_DECL = 'indicator("Chase Risk Trendability Lab｜Issue #78", shorttitle="Trendability Lab #78", overlay=false, precision=1)'
OLD_DOWN_DEFAULT = 'showDownRiskLine = input.bool(true, "顯示下跌末段恐慌風險線", group=groupDisplay)'
NEW_DOWN_DEFAULT = 'showDownRiskLine = input.bool(false, "顯示下跌末段恐慌風險線", group=groupDisplay)'
OLD_TABLE_DEFAULT = 'showTable        = input.bool(true, "顯示 Dashboard", group=groupDisplay)'
NEW_TABLE_DEFAULT = 'showTable        = input.bool(false, "顯示原始 Dashboard", group=groupDisplay)'
OLD_PACE_DEFAULT = 'showPaceGuide   = input.bool(true, "顯示 Pace Guide 操作節奏", group=groupPace)'
NEW_PACE_DEFAULT = 'showPaceGuide   = input.bool(false, "顯示 Pace Guide 操作節奏", group=groupPace)'
OLD_UP_PLOT = 'plot(endRiskUp, "上漲末段風險", color=upColor, linewidth=2)'
NEW_UP_PLOT = 'plot(na, "上漲末段風險", color=upColor, linewidth=2)'
ANCHOR = "\n// Visuals\n"

INJECTION = r'''

// ============================================================================
// Issue #78 — research-only Trendability / Oscillation Lab
// ----------------------------------------------------------------------------
// Preregistered diagnostic only. This does NOT alter formalId or exposure rules.
// ER = net displacement / total travelled path. Low = oscillation, high = expansion.
// Frozen horizons: 63 / 126 / 252 bars. Percentile normalization: rankLen=756.
// ============================================================================

groupIssue78Trend = "研究｜Issue #78 Trendability"
issue78TrendShow = input.bool(true, "顯示 Trendability Lab", group=groupIssue78Trend)
issue78TrendShowComponents = input.bool(false, "顯示 63/126/252 分量", group=groupIssue78Trend)
issue78TrendShowPanel = input.bool(true, "顯示 Trendability 面板", group=groupIssue78Trend)
issue78TrendLogEnabled = input.bool(true, "Fresh trend entry 寫入 Pine Logs", group=groupIssue78Trend)
issue78TrendColor = input.color(color.rgb(65, 170, 240), "Composite 線色", group=groupIssue78Trend)

f_issue78Er(float src, int len) =>
    step = math.abs(ta.change(src))
    path = ta.sma(step, len) * len
    displacement = math.abs(src - src[len])
    not na(path) and path > 0.0 ? displacement / path : na

f_issue78TrendState(float score) =>
    na(score) ? "資料不足" : score < 33.33 ? "Oscillation｜大型震盪傾向" : score <= 66.67 ? "Neutral｜中性" : "Expansion｜趨勢延伸傾向"

issue78Er63 = f_issue78Er(modelPrice, 63)
issue78Er126 = f_issue78Er(modelPrice, 126)
issue78Er252 = f_issue78Er(modelPrice, 252)
issue78Er63Rank = ta.percentrank(issue78Er63, rankLen)
issue78Er126Rank = ta.percentrank(issue78Er126, rankLen)
issue78Er252Rank = ta.percentrank(issue78Er252, rankLen)
issue78Trendability = not na(issue78Er63Rank) and not na(issue78Er126Rank) and not na(issue78Er252Rank) ? (issue78Er63Rank + issue78Er126Rank + issue78Er252Rank) / 3.0 : na
issue78TrendActive = formalId == 2 or formalId == 5
issue78FreshTrend = issue78TrendActive and formalId != formalId[1]
issue78Representation = useYieldLevel ? "YIELD_LEVEL" : "PRICE_LOG"
issue78D1 = timeframe.isdaily and timeframe.multiplier == 1

plot(issue78TrendShow ? issue78Trendability : na, "#78 Trendability Composite", color=issue78TrendColor, linewidth=3)
plot(issue78TrendShow and issue78TrendShowComponents ? issue78Er63Rank : na, "#78 ER63 percentile", color=color.new(color.green, 25), linewidth=1)
plot(issue78TrendShow and issue78TrendShowComponents ? issue78Er126Rank : na, "#78 ER126 percentile", color=color.new(color.orange, 20), linewidth=1)
plot(issue78TrendShow and issue78TrendShowComponents ? issue78Er252Rank : na, "#78 ER252 percentile", color=color.new(color.purple, 20), linewidth=1)
hline(33.33, "#78 Oscillation / Neutral", color=color.new(color.gray, 55), linestyle=hline.style_dotted)
hline(66.67, "#78 Neutral / Expansion", color=color.new(color.gray, 55), linestyle=hline.style_dotted)
plotshape(issue78TrendShow and issue78FreshTrend, title="#78 Fresh formal trend", text="趨", style=shape.circle, location=location.bottom, color=formalId == 2 ? color.new(color.green, 0) : color.new(color.red, 0), textcolor=color.white, size=size.tiny)

var table issue78TrendDash = table.new(position.bottom_right, 2, 7, border_width=1)
if barstate.islast
    table.clear(issue78TrendDash, 0, 0, 1, 6)
    if issue78TrendShow and issue78TrendShowPanel
        panelBg = color.new(color.rgb(40, 40, 40), 12)
        scoreColor = na(issue78Trendability) ? color.gray : issue78Trendability < 33.33 ? color.orange : issue78Trendability <= 66.67 ? color.yellow : color.aqua
        table.cell(issue78TrendDash, 0, 0, "Issue #78 Trendability", text_color=color.white, bgcolor=color.new(color.rgb(25,25,25), 0))
        table.cell(issue78TrendDash, 1, 0, "研究用｜不改倉位", text_color=color.yellow, bgcolor=color.new(color.rgb(25,25,25), 0))
        table.cell(issue78TrendDash, 0, 1, "Composite", text_color=color.white, bgcolor=panelBg)
        table.cell(issue78TrendDash, 1, 1, na(issue78Trendability) ? "—" : str.tostring(issue78Trendability, "#.0"), text_color=scoreColor, bgcolor=panelBg)
        table.cell(issue78TrendDash, 0, 2, "環境", text_color=color.white, bgcolor=panelBg)
        table.cell(issue78TrendDash, 1, 2, f_issue78TrendState(issue78Trendability), text_color=scoreColor, bgcolor=panelBg)
        table.cell(issue78TrendDash, 0, 3, "ER63 rank", text_color=color.white, bgcolor=panelBg)
        table.cell(issue78TrendDash, 1, 3, na(issue78Er63Rank) ? "—" : str.tostring(issue78Er63Rank, "#.0"), text_color=color.white, bgcolor=panelBg)
        table.cell(issue78TrendDash, 0, 4, "ER126 rank", text_color=color.white, bgcolor=panelBg)
        table.cell(issue78TrendDash, 1, 4, na(issue78Er126Rank) ? "—" : str.tostring(issue78Er126Rank, "#.0"), text_color=color.white, bgcolor=panelBg)
        table.cell(issue78TrendDash, 0, 5, "ER252 rank", text_color=color.white, bgcolor=panelBg)
        table.cell(issue78TrendDash, 1, 5, na(issue78Er252Rank) ? "—" : str.tostring(issue78Er252Rank, "#.0"), text_color=color.white, bgcolor=panelBg)
        table.cell(issue78TrendDash, 0, 6, "正式環境", text_color=color.white, bgcolor=panelBg)
        table.cell(issue78TrendDash, 1, 6, formalId == 2 ? "拉升" : formalId == 5 ? "崩跌" : f_stageName(formalId), text_color=color.white, bgcolor=panelBg)

// Compact entry-time export. Join later to existing Issue #76 outcome rows by ticker/event_time/stage.
if issue78TrendLogEnabled and issue78D1 and issue78FreshTrend and not na(issue78Trendability) and barstate.isconfirmed
    log.info(
         "ISSUE78TREND|schema=1" +
         "|ticker=" + syminfo.tickerid +
         "|tf=" + timeframe.period +
         "|repr=" + issue78Representation +
         "|event_time=" + str.tostring(time) +
         "|event_bar=" + str.tostring(bar_index) +
         "|stage=" + str.tostring(formalId) +
         "|er63=" + str.tostring(issue78Er63, "#.##########") +
         "|er126=" + str.tostring(issue78Er126, "#.##########") +
         "|er252=" + str.tostring(issue78Er252, "#.##########") +
         "|er63r=" + str.tostring(issue78Er63Rank, "#.##########") +
         "|er126r=" + str.tostring(issue78Er126Rank, "#.##########") +
         "|er252r=" + str.tostring(issue78Er252Rank, "#.##########") +
         "|trendability=" + str.tostring(issue78Trendability, "#.##########"))
'''


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def replace_once(source: str, old: str, new: str, label: str) -> str:
    if source.count(old) != 1:
        raise SystemExit(f"{label} anchor missing or duplicated")
    return source.replace(old, new, 1)


def generate(output: Path) -> None:
    raw = SOURCE.read_bytes()
    actual = git_blob_sha(raw)
    if actual != EXPECTED_BLOB_SHA:
        raise SystemExit(f"frozen source drift: expected {EXPECTED_BLOB_SHA}, got {actual}")
    source = raw.decode("utf-8")
    source = replace_once(source, OLD_DECL, NEW_DECL, "indicator declaration")
    source = replace_once(source, OLD_DOWN_DEFAULT, NEW_DOWN_DEFAULT, "down-risk default")
    source = replace_once(source, OLD_TABLE_DEFAULT, NEW_TABLE_DEFAULT, "dashboard default")
    source = replace_once(source, OLD_PACE_DEFAULT, NEW_PACE_DEFAULT, "pace default")
    source = replace_once(source, OLD_UP_PLOT, NEW_UP_PLOT, "up-risk plot")
    if source.count(ANCHOR) != 1:
        raise SystemExit("visual anchor missing or duplicated")
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
