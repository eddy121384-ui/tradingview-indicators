#!/usr/bin/env python3
"""Generate the Issue #78 native-weekly context logger from frozen Issue #68 RC.

The classifier is copied mechanically and its parameters are unchanged. The
research-only injection logs completed native 1W formal regime plus a separately
specified 13/26/52-week Trendability context for causal as-of joining to the
accepted Issue #76 daily evidence.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "indicators/wyckoff-regime-radar/src/chase-risk-market-regime-radar-issue68-rc.pine"
DEFAULT_OUTPUT = ROOT / "indicators/wyckoff-regime-radar/research/generated/wyckoff-issue78-weekly-context-logger.pine"
EXPECTED_BLOB_SHA = "e5c3fd2622841a6d3f97bdda4b9d0a6378ebda55"

OLD_DECL = 'indicator("Chase Risk Market Regime Radar｜Issue #68 RC", shorttitle="ChaseRisk Radar #68 RC", overlay=false, precision=1)'
NEW_DECL = 'indicator("Chase Risk Weekly Context Logger｜Issue #78", shorttitle="Weekly Context #78", overlay=false, precision=1)'
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
// Issue #78 — native 1W sizing-context export
// ----------------------------------------------------------------------------
// Frozen classifier: Issue #68 RC, unchanged, evaluated directly on 1W bars.
// Weekly Trendability is a separate calendar-ish context:
// ER13 / ER26 / ER52, each percentile-ranked over the prior 156 weekly bars.
// Every decision must use only a COMPLETED weekly bar. The downstream join uses
// week_close_time <= daily_event_time.
// ============================================================================

groupIssue78Weekly = "研究｜Issue #78 Weekly Context Export"
issue78WeeklyLogEnabled = input.bool(true, "Enable Weekly Context Pine Logs", group=groupIssue78Weekly)
issue78WeeklyShow = input.bool(true, "顯示 Weekly Trendability", group=groupIssue78Weekly)
issue78WeeklyStart = input.time(0, "Weekly start time (1970 = all)", group=groupIssue78Weekly)
issue78WeeklyEnd = input.time(4102444800000, "Weekly end time (2100 = all)", group=groupIssue78Weekly)

f_issue78WeeklyEr(float src, int len) =>
    step = math.abs(ta.change(src))
    path = ta.sma(step, len) * len
    displacement = math.abs(src - src[len])
    not na(path) and path > 0.0 ? displacement / path : na

issue78WeeklyAllowedFeed = syminfo.tickerid == "OANDA:EURUSD" or syminfo.tickerid == "OANDA:GBPUSD" or syminfo.tickerid == "OANDA:USDJPY" or syminfo.tickerid == "TVC:US10Y" or syminfo.tickerid == "TVC:DE10Y" or syminfo.tickerid == "TVC:FR10Y" or syminfo.tickerid == "TVC:GB10Y" or syminfo.tickerid == "TVC:AU10Y" or syminfo.tickerid == "TVC:JP10Y"
issue78Native1W = timeframe.isweekly and timeframe.multiplier == 1
issue78WeeklyRepresentation = useYieldLevel ? "YIELD_LEVEL" : "PRICE_LOG"
issue78WeeklyInWindow = time >= issue78WeeklyStart and time <= issue78WeeklyEnd

issue78Er13w = f_issue78WeeklyEr(modelPrice, 13)
issue78Er26w = f_issue78WeeklyEr(modelPrice, 26)
issue78Er52w = f_issue78WeeklyEr(modelPrice, 52)
issue78Er13wRank = ta.percentrank(issue78Er13w, 156)
issue78Er26wRank = ta.percentrank(issue78Er26w, 156)
issue78Er52wRank = ta.percentrank(issue78Er52w, 156)
issue78WeeklyTrendability = not na(issue78Er13wRank) and not na(issue78Er26wRank) and not na(issue78Er52wRank) ? (issue78Er13wRank + issue78Er26wRank + issue78Er52wRank) / 3.0 : na

plot(issue78WeeklyShow and issue78Native1W ? issue78WeeklyTrendability : na, "#78 Weekly Trendability", color=color.rgb(65, 170, 240), linewidth=3)
hline(66.67, "#78 Weekly high-trendability boundary", color=color.new(color.orange, 45), linestyle=hline.style_dotted)
plot(issue78Native1W ? formalId : na, "#78 Weekly Formal Stage ID", display=display.none)
plot(issue78Native1W ? issue78WeeklyTrendability : na, "#78 Weekly Trendability hidden", display=display.none)

issue78WeeklyReady = issue78WeeklyAllowedFeed and issue78Native1W and issue78WeeklyInWindow and barstate.isconfirmed

if issue78WeeklyLogEnabled and issue78WeeklyReady
    log.info(
         "ISSUE78WEEKLY|schema=1" +
         "|ticker=" + syminfo.tickerid +
         "|tf=" + timeframe.period +
         "|repr=" + issue78WeeklyRepresentation +
         "|week_open_time=" + str.tostring(time) +
         "|week_close_time=" + str.tostring(time_close) +
         "|week_bar=" + str.tostring(bar_index) +
         "|formal=" + str.tostring(formalId) +
         "|er13=" + str.tostring(issue78Er13w, "#.##########") +
         "|er26=" + str.tostring(issue78Er26w, "#.##########") +
         "|er52=" + str.tostring(issue78Er52w, "#.##########") +
         "|er13r=" + str.tostring(issue78Er13wRank, "#.##########") +
         "|er26r=" + str.tostring(issue78Er26wRank, "#.##########") +
         "|er52r=" + str.tostring(issue78Er52wRank, "#.##########") +
         "|wtrend=" + str.tostring(issue78WeeklyTrendability, "#.##########"))
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
