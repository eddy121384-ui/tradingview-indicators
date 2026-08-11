#!/usr/bin/env python3
"""Generate a TradingView diagnostic for the user's v0.5.2.1 Top-2 heuristic.

Unlike Issue #55 price-only harnesses, this keeps the frozen indicator's actual
input defaults intact, notably Volume Mode = Auto. MTF and Divergence therefore
remain at their frozen defaults (Observe Only), which do not stage-bias weights.

The frozen source is hash-checked, calculations are retained through the state
logic, the original visual layer is removed, and a compact causal historical
scorecard is appended.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "src" / "chase-risk-market-regime-radar-v0.5.2.1.pine"
EXPECTED_SOURCE_BLOB_SHA = "ab6861181a27697ad566c19bf405a0571be2eb1a"
VISUAL_MARKER = "// Visuals"
PRIMARY_THRESHOLD = 90.0


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def suffix() -> str:
    return r'''
// ===== Issue #57 default-v0.5.2.1 Top-2 live-dashboard diagnostic =====
// Frozen semantics: bullish actionable pair = stages 2+3; bearish = stages 5+6.
// Primary user-originated threshold: Top1 + Top2 >= 90%.
// Volume Auto is intentionally preserved from the original default settings.

float issue57Top2Sum = topVal + secondVal
bool issue57BullPair = (topId == 2 and secondId == 3) or (topId == 3 and secondId == 2)
bool issue57BearPair = (topId == 5 and secondId == 6) or (topId == 6 and secondId == 5)
int issue57Top2Signal = issue57Top2Sum >= 90.0 and issue57BullPair ? 1 : issue57Top2Sum >= 90.0 and issue57BearPair ? -1 : 0
int issue57FormalSignal = formalId == 2 or formalId == 3 ? 1 : formalId == 5 or formalId == 6 ? -1 : 0

var int issue57Top2N5 = 0
var int issue57Top2Hit5 = 0
var float issue57Top2Sum5 = 0.0
var int issue57Top2N10 = 0
var int issue57Top2Hit10 = 0
var float issue57Top2Sum10 = 0.0
var int issue57Top2N20 = 0
var int issue57Top2Hit20 = 0
var float issue57Top2Sum20 = 0.0
var int issue57Top2N60 = 0
var int issue57Top2Hit60 = 0
var float issue57Top2Sum60 = 0.0

var int issue57FormalN5 = 0
var int issue57FormalHit5 = 0
var float issue57FormalSum5 = 0.0
var int issue57FormalN10 = 0
var int issue57FormalHit10 = 0
var float issue57FormalSum10 = 0.0
var int issue57FormalN20 = 0
var int issue57FormalHit20 = 0
var float issue57FormalSum20 = 0.0
var int issue57FormalN60 = 0
var int issue57FormalHit60 = 0
var float issue57FormalSum60 = 0.0

if bar_index >= 5 and issue57Top2Signal[5] != 0 and not na(close[5])
    float aligned = issue57Top2Signal[5] * (close / close[5] - 1.0)
    issue57Top2N5 += 1
    issue57Top2Sum5 += aligned
    if aligned > 0.0
        issue57Top2Hit5 += 1
if bar_index >= 10 and issue57Top2Signal[10] != 0 and not na(close[10])
    float aligned = issue57Top2Signal[10] * (close / close[10] - 1.0)
    issue57Top2N10 += 1
    issue57Top2Sum10 += aligned
    if aligned > 0.0
        issue57Top2Hit10 += 1
if bar_index >= 20 and issue57Top2Signal[20] != 0 and not na(close[20])
    float aligned = issue57Top2Signal[20] * (close / close[20] - 1.0)
    issue57Top2N20 += 1
    issue57Top2Sum20 += aligned
    if aligned > 0.0
        issue57Top2Hit20 += 1
if bar_index >= 60 and issue57Top2Signal[60] != 0 and not na(close[60])
    float aligned = issue57Top2Signal[60] * (close / close[60] - 1.0)
    issue57Top2N60 += 1
    issue57Top2Sum60 += aligned
    if aligned > 0.0
        issue57Top2Hit60 += 1

if bar_index >= 5 and issue57FormalSignal[5] != 0 and not na(close[5])
    float aligned = issue57FormalSignal[5] * (close / close[5] - 1.0)
    issue57FormalN5 += 1
    issue57FormalSum5 += aligned
    if aligned > 0.0
        issue57FormalHit5 += 1
if bar_index >= 10 and issue57FormalSignal[10] != 0 and not na(close[10])
    float aligned = issue57FormalSignal[10] * (close / close[10] - 1.0)
    issue57FormalN10 += 1
    issue57FormalSum10 += aligned
    if aligned > 0.0
        issue57FormalHit10 += 1
if bar_index >= 20 and issue57FormalSignal[20] != 0 and not na(close[20])
    float aligned = issue57FormalSignal[20] * (close / close[20] - 1.0)
    issue57FormalN20 += 1
    issue57FormalSum20 += aligned
    if aligned > 0.0
        issue57FormalHit20 += 1
if bar_index >= 60 and issue57FormalSignal[60] != 0 and not na(close[60])
    float aligned = issue57FormalSignal[60] * (close / close[60] - 1.0)
    issue57FormalN60 += 1
    issue57FormalSum60 += aligned
    if aligned > 0.0
        issue57FormalHit60 += 1

f_issue57_pct(int hits, int n) => n > 0 ? hits * 100.0 / n : na
f_issue57_avg(float sumValue, int n) => n > 0 ? sumValue * 100.0 / n : na
f_issue57_pair_text(int a, int b) => str.tostring(a) + "+" + str.tostring(b)

var table issue57Table = table.new(position.top_right, 7, 8, border_width=1)
if barstate.islast
    table.cell(issue57Table, 0, 0, "v0.5.2.1 default")
    table.cell(issue57Table, 1, 0, "Candidate")
    table.cell(issue57Table, 2, 0, "Secondary")
    table.cell(issue57Table, 3, 0, "Top2 Sum")
    table.cell(issue57Table, 4, 0, "Top2 Sig")
    table.cell(issue57Table, 5, 0, "Vol Q")
    table.cell(issue57Table, 6, 0, "Vol W")
    table.cell(issue57Table, 0, 1, syminfo.ticker + " " + timeframe.period)
    table.cell(issue57Table, 1, 1, f_stageName(candidateDisplayId) + " " + f_num(topVal))
    table.cell(issue57Table, 2, 1, f_stageName(secondaryId) + " " + f_num(secondVal))
    table.cell(issue57Table, 3, 1, f_num(issue57Top2Sum))
    table.cell(issue57Table, 4, 1, issue57Top2Signal == 1 ? "BULL" : issue57Top2Signal == -1 ? "BEAR" : "—")
    table.cell(issue57Table, 5, 1, f_num(volumeQualityScore))
    table.cell(issue57Table, 6, 1, f_num(volumeWeightGoverned * 100.0) + "%")

    table.cell(issue57Table, 0, 2, "Signal")
    table.cell(issue57Table, 1, 2, "H")
    table.cell(issue57Table, 2, 2, "n")
    table.cell(issue57Table, 3, 2, "Hit %")
    table.cell(issue57Table, 4, 2, "Avg aligned %")
    table.cell(issue57Table, 5, 2, "Formal Hit %")
    table.cell(issue57Table, 6, 2, "Formal Avg %")

    table.cell(issue57Table, 0, 3, "Top2 >=90")
    table.cell(issue57Table, 1, 3, "5")
    table.cell(issue57Table, 2, 3, str.tostring(issue57Top2N5))
    table.cell(issue57Table, 3, 3, f_num(f_issue57_pct(issue57Top2Hit5, issue57Top2N5)))
    table.cell(issue57Table, 4, 3, f_num(f_issue57_avg(issue57Top2Sum5, issue57Top2N5)))
    table.cell(issue57Table, 5, 3, f_num(f_issue57_pct(issue57FormalHit5, issue57FormalN5)))
    table.cell(issue57Table, 6, 3, f_num(f_issue57_avg(issue57FormalSum5, issue57FormalN5)))

    table.cell(issue57Table, 0, 4, "Top2 >=90")
    table.cell(issue57Table, 1, 4, "10")
    table.cell(issue57Table, 2, 4, str.tostring(issue57Top2N10))
    table.cell(issue57Table, 3, 4, f_num(f_issue57_pct(issue57Top2Hit10, issue57Top2N10)))
    table.cell(issue57Table, 4, 4, f_num(f_issue57_avg(issue57Top2Sum10, issue57Top2N10)))
    table.cell(issue57Table, 5, 4, f_num(f_issue57_pct(issue57FormalHit10, issue57FormalN10)))
    table.cell(issue57Table, 6, 4, f_num(f_issue57_avg(issue57FormalSum10, issue57FormalN10)))

    table.cell(issue57Table, 0, 5, "Top2 >=90")
    table.cell(issue57Table, 1, 5, "20")
    table.cell(issue57Table, 2, 5, str.tostring(issue57Top2N20))
    table.cell(issue57Table, 3, 5, f_num(f_issue57_pct(issue57Top2Hit20, issue57Top2N20)))
    table.cell(issue57Table, 4, 5, f_num(f_issue57_avg(issue57Top2Sum20, issue57Top2N20)))
    table.cell(issue57Table, 5, 5, f_num(f_issue57_pct(issue57FormalHit20, issue57FormalN20)))
    table.cell(issue57Table, 6, 5, f_num(f_issue57_avg(issue57FormalSum20, issue57FormalN20)))

    table.cell(issue57Table, 0, 6, "Top2 >=90")
    table.cell(issue57Table, 1, 6, "60")
    table.cell(issue57Table, 2, 6, str.tostring(issue57Top2N60))
    table.cell(issue57Table, 3, 6, f_num(f_issue57_pct(issue57Top2Hit60, issue57Top2N60)))
    table.cell(issue57Table, 4, 6, f_num(f_issue57_avg(issue57Top2Sum60, issue57Top2N60)))
    table.cell(issue57Table, 5, 6, f_num(f_issue57_pct(issue57FormalHit60, issue57FormalN60)))
    table.cell(issue57Table, 6, 6, f_num(f_issue57_avg(issue57FormalSum60, issue57FormalN60)))

    table.cell(issue57Table, 0, 7, "Semantics")
    table.cell(issue57Table, 1, 7, "Bull 2+3")
    table.cell(issue57Table, 2, 7, "Bear 5+6")
    table.cell(issue57Table, 3, 7, ">=90%")
    table.cell(issue57Table, 4, 7, "Vol Auto")
    table.cell(issue57Table, 5, 7, "MTF Observe")
    table.cell(issue57Table, 6, 7, "Div Observe")

plot(float(issue57Top2Signal), "Issue57 Top2 signal", display=display.data_window)
plot(issue57Top2Sum, "Issue57 Top2 sum", display=display.data_window)
plot(float(candidateDisplayId), "Issue57 candidate id", display=display.data_window)
plot(float(secondaryId), "Issue57 secondary id", display=display.data_window)
plot(topVal, "Issue57 candidate weight", display=display.data_window)
plot(secondVal, "Issue57 secondary weight", display=display.data_window)
plot(volumeQualityScore, "Issue57 volume quality", display=display.data_window)
plot(volumeWeightGoverned * 100.0, "Issue57 volume weight %", display=display.data_window)
'''


def render() -> str:
    raw = SOURCE.read_bytes()
    actual = git_blob_sha(raw)
    if actual != EXPECTED_SOURCE_BLOB_SHA:
        raise RuntimeError(f"frozen v0.5.2.1 Pine blob changed: {actual}")
    source = raw.decode("utf-8")
    if source.count(VISUAL_MARKER) != 1:
        raise RuntimeError(f"expected one visual marker, found {source.count(VISUAL_MARKER)}")
    core = source.split(VISUAL_MARKER, 1)[0].rstrip()
    old_indicator = 'indicator("Chase Risk Market Regime Radar v0.5.2.1｜Non-functional Cleanup", shorttitle="ChaseRisk Radar v0.5.2.1", overlay=false, precision=1)'
    new_indicator = 'indicator("Issue #57｜v0.5.2.1 Default Top2 Diagnostic", shorttitle="#57 v05 Top2 Default", overlay=false, precision=1)'
    if core.count(old_indicator) != 1:
        raise RuntimeError("indicator declaration drifted")
    core = core.replace(old_indicator, new_indicator, 1)
    return core + "\n\n" + suffix().lstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = render()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8")


if __name__ == "__main__":
    main()
