#!/usr/bin/env python3
"""Generate the Issue #57 v0.6 TradingView research/parity harness.

The generator starts from the frozen v0.5.2.1 Pine source and applies only the
already-decided Phase A/B/C/D research deltas. It never edits the frozen source.
The output is a research harness, not the eventual production indicator.
"""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "src" / "chase-risk-market-regime-radar-v0.5.2.1.pine"
EXPECTED_SOURCE_BLOB_SHA = "ab6861181a27697ad566c19bf405a0571be2eb1a"
VISUAL_MARKER = "// Visuals"
SOFT_WIDTH_ATR = 0.25
STALE_DECAY_MULTIPLIER = 2

CHECKPOINTS = (
    (2019, 8, 1),
    (2020, 3, 20),
    (2021, 6, 1),
    (2022, 9, 28),
    (2024, 4, 16),
    (2026, 7, 30),
)


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def _find_unique(lines: list[str], token: str) -> int:
    hits = [index for index, line in enumerate(lines) if token in line]
    if len(hits) != 1:
        raise RuntimeError(f"Expected one Pine line containing {token!r}; found {len(hits)}")
    return hits[0]


def _assignment_index(lines: list[str], variable: str) -> int:
    pattern = re.compile(rf"\b{re.escape(variable)}\s*=")
    hits = [index for index, line in enumerate(lines) if pattern.search(line)]
    if len(hits) != 1:
        raise RuntimeError(f"Expected one assignment to {variable}; found {len(hits)}")
    return hits[0]


def _replace_assignment(lines: list[str], variable: str, expression: str, pine_type: str) -> None:
    index = _assignment_index(lines, variable)
    indent = lines[index][: len(lines[index]) - len(lines[index].lstrip())]
    lines[index] = f"{indent}{pine_type} {variable} = {expression}"


def _extract_atr_name(lines: list[str]) -> str:
    pattern = re.compile(r"^\s*(?:float\s+)?([A-Za-z_]\w*)\s*=\s*ta\.atr\(")
    hits: list[str] = []
    for line in lines:
        match = pattern.search(line)
        if match:
            hits.append(match.group(1))
    if len(hits) != 1:
        raise RuntimeError(f"Expected one ta.atr assignment; found {hits}")
    return hits[0]


def _replace_statement(lines: list[str], variable: str, replacement: list[str]) -> None:
    """Replace a possibly multiline Pine assignment with a supplied block."""
    start = _assignment_index(lines, variable)
    base_indent = len(lines[start]) - len(lines[start].lstrip())
    balance = lines[start].count("(") - lines[start].count(")")
    end = start
    while balance > 0:
        end += 1
        if end >= len(lines):
            raise RuntimeError(f"Unterminated assignment for {variable}")
        balance += lines[end].count("(") - lines[end].count(")")
    while end + 1 < len(lines):
        next_line = lines[end + 1]
        stripped = next_line.strip()
        indent = len(next_line) - len(next_line.lstrip())
        if not stripped:
            break
        if indent <= base_indent and re.match(
            r"(?:bool|float|int|string|var\s+int|var\s+float|if|for|//)\b", stripped
        ):
            break
        if indent <= base_indent and re.match(r"[A-Za-z_]\w*\s*=", stripped):
            break
        end += 1
    lines[start : end + 1] = replacement


def _helpers(atr_name: str) -> list[str]:
    del atr_name
    return [
        "",
        "// ===== Issue #57 v0.6 research helpers (mechanically generated) =====",
        f"float V06_SOFT_WIDTH_ATR = {SOFT_WIDTH_ATR}",
        "f_v06_clamp100(float x) => math.max(0.0, math.min(100.0, x))",
        "f_v06_gate(float x, float lo, float hi) => hi <= lo ? 0.0 : math.max(0.0, math.min(1.0, (x - lo) / (hi - lo)))",
        "f_v06_soft_no_break_low(float c, float boundary, float atrValue) =>",
        "    float scale = atrValue * V06_SOFT_WIDTH_ATR",
        "    na(scale) or scale <= 0.0 or na(boundary) ? na : f_v06_clamp100(50.0 + 50.0 * ((c - boundary) / scale))",
        "f_v06_soft_no_break_high(float c, float boundary, float atrValue) =>",
        "    float scale = atrValue * V06_SOFT_WIDTH_ATR",
        "    na(scale) or scale <= 0.0 or na(boundary) ? na : f_v06_clamp100(50.0 + 50.0 * ((boundary - c) / scale))",
        "f_v06_soft_above_range(float c, float boundary, float atrValue) => 100.0 - f_v06_soft_no_break_high(c, boundary, atrValue)",
        "f_v06_soft_below_range(float c, float boundary, float atrValue) => 100.0 - f_v06_soft_no_break_low(c, boundary, atrValue)",
        "f_v06_soft_break_above(float c, float boundary, float atrValue) =>",
        "    float scale = atrValue * V06_SOFT_WIDTH_ATR",
        "    na(scale) or scale <= 0.0 or na(boundary) ? na : f_v06_clamp100(100.0 * ((c - boundary) / scale))",
        "f_v06_soft_break_below(float c, float boundary, float atrValue) =>",
        "    float scale = atrValue * V06_SOFT_WIDTH_ATR",
        "    na(scale) or scale <= 0.0 or na(boundary) ? na : f_v06_clamp100(100.0 * ((boundary - c) / scale))",
        "f_v06_map4(int id) => id == 1 or id == 3 ? 1 : id == 2 ? 2 : id == 4 or id == 6 ? 3 : id == 5 ? 4 : 0",
        "// ===== End Issue #57 helpers =====",
        "",
    ]


def _force_research_modes(lines: list[str]) -> None:
    for variable, expression, pine_type in (
        ("volumeMode", '"Off"', "string"),
        ("mtfMode", '"Off"', "string"),
        ("divMode", '"Off"', "string"),
        ("witnessStageBiasMode", '"Conservative"', "string"),
    ):
        _replace_assignment(lines, variable, expression, pine_type)


def _apply_phase_a(lines: list[str], atr_name: str) -> None:
    first = _assignment_index(lines, "noBreakLowScore")
    lines[first:first] = _helpers(atr_name)

    _replace_assignment(lines, "noBreakLowScore", f"f_v06_soft_no_break_low(close, prevAbsLow, {atr_name})", "float")
    _replace_assignment(lines, "noBreakHighScore", f"f_v06_soft_no_break_high(close, prevAbsHigh, {atr_name})", "float")

    recent_dn = _assignment_index(lines, "recentMaCrossDn")
    indent = lines[recent_dn][: len(lines[recent_dn]) - len(lines[recent_dn].lstrip())]
    injected = [
        f"{indent}bool recentMaCrossUp = ta.barssince(maCrossUp) <= breakoutBars",
        f"{indent}float rangeBreakUpStrength = f_v06_soft_break_above(close, rangeHighBreak, {atr_name})",
        f"{indent}float rangeBreakDnStrength = f_v06_soft_break_below(close, rangeLowBreak, {atr_name})",
        f"{indent}float recentRangeBreakUpStrength = ta.highest(rangeBreakUpStrength, breakoutBars)",
        f"{indent}float recentRangeBreakDnStrength = ta.highest(rangeBreakDnStrength, breakoutBars)",
    ]
    lines[recent_dn + 1 : recent_dn + 1] = injected

    _replace_statement(
        lines,
        "breakoutScore",
        [
            "float breakoutRangeEvidence = nz(recentRangeBreakUpStrength, 0.0) * 0.70",
            "float breakoutMaEvidence = recentMaCrossUp ? 70.0 : close > ma ? 35.0 : 0.0",
            "float breakoutScore = breakoutModeUp ? 100.0 : math.max(breakoutRangeEvidence, breakoutMaEvidence)",
        ],
    )
    _replace_statement(
        lines,
        "explicitBreakdownScore",
        [
            "float breakdownRangeEvidence = nz(recentRangeBreakDnStrength, 0.0) * 0.85",
            "float breakdownMaEvidence = recentMaCrossDn and panicHeatDn >= orangeLevel and structureWeak >= 50.0 ? 55.0 : 0.0",
            "float explicitBreakdownScore = breakdownModeDn ? 100.0 : math.max(breakdownRangeEvidence, breakdownMaEvidence)",
        ],
    )

    # The frozen Pine names these public continuation scores explicitly; keep
    # those names so all downstream score/gate formulas remain mechanically
    # connected to the v0.6 softened evidence.
    _replace_statement(
        lines,
        "rangeContinuationUpScore",
        [
            f"float abovePrevRangeScore = f_v06_soft_above_range(close, prevRangeHigh, {atr_name})",
            f"float belowPrevRangeScore = f_v06_soft_below_range(close, prevRangeLow, {atr_name})",
            "float sustainedAboveScore = ta.lowest(abovePrevRangeScore, continuationHoldBars)",
            "float sustainedBelowScore = ta.lowest(belowPrevRangeScore, continuationHoldBars)",
            "float rangeBreakUpEvidence = nz(recentRangeBreakUpStrength, 0.0) * 0.65",
            "float rangeBreakDnEvidence = nz(recentRangeBreakDnStrength, 0.0) * 0.65",
            "float rangeContinuationUpBase = math.max(rangeBreakUpEvidence, recentMaCrossUp ? 65.0 : close > rangeMid ? 35.0 : 0.0)",
            "float rangeContinuationDnBase = math.max(rangeBreakDnEvidence, recentMaCrossDn ? 65.0 : close < rangeMid ? 35.0 : 0.0)",
            "float rangeContinuationUpScore = math.max(rangeContinuationUpBase, math.max(nz(abovePrevRangeScore, 0.0) * 0.80, nz(sustainedAboveScore, 0.0)))",
            "float rangeContinuationDnScore = math.max(rangeContinuationDnBase, math.max(nz(belowPrevRangeScore, 0.0) * 0.80, nz(sustainedBelowScore, 0.0)))",
        ],
    )
    dn_hits = [i for i, line in enumerate(lines) if re.match(r"^\s*(?:float\s+)?rangeContinuationDnScore\s*=(?!=)", line)]
    if len(dn_hits) != 2:
        raise RuntimeError(f"Expected generated + frozen rangeContinuationDnScore assignments; found {len(dn_hits)}")
    del lines[dn_hits[1]]

    _replace_statement(
        lines,
        "breakoutGate",
        [
            "float breakoutRecentRangeGate = nz(recentRangeBreakUpStrength, 0.0) / 100.0 * 0.85",
            "float breakoutMaGate = recentMaCrossUp ? 0.85 : f_v06_gate(breakoutMaEvidence, 30.0, 70.0)",
            "float breakoutRecentGate = math.max(breakoutRecentRangeGate, breakoutMaGate)",
            "float breakoutGate = breakoutModeUp ? 1.0 : breakoutRecentGate",
        ],
    )
    _replace_statement(
        lines,
        "explicitBreakdownGate",
        [
            "float explicitRecentBreakdownGate = nz(recentRangeBreakDnStrength, 0.0) / 100.0 * 0.90",
            "float explicitBreakdownMaGate = f_v06_gate(breakdownMaEvidence, 50.0, 85.0)",
            "float explicitBreakdownGate = breakdownModeDn ? 1.0 : math.max(explicitRecentBreakdownGate, explicitBreakdownMaGate)",
        ],
    )


def _apply_phase_b(lines: list[str]) -> None:
    start = _find_unique(lines, "var int confirmed")
    formal_line = _assignment_index(lines, "formalId")
    if formal_line <= start:
        raise RuntimeError("formalId appears before persistence state")

    old_block = lines[start : formal_line + 1]
    confirm_expr = None
    for line in old_block:
        match = re.search(r"candidateBars\s*>=\s*([^\s]+)", line)
        if match:
            confirm_expr = match.group(1)
            break
    if confirm_expr is None:
        confirm_expr = "activeConfirmBars"

    new_block = [
        "// ===== Issue #57 Phase B persistence redesign =====",
        "var int confirmedId = 0",
        "var int candidateId = 0",
        "var int candidateBars = 0",
        "var int stalePressureBars = 0",
        "int stalePressureReason = 0",
        f"int staleLimit = confirmBars * {STALE_DECAY_MULTIPLIER}",
        "int candidateDisplayIdPre = (strongCandidate or weakCandidateRaw) ? topId : 0",
        "if strongCandidate",
        "    stalePressureBars := 0",
        "    stalePressureReason := 0",
        "    int rawId = topId",
        "    if rawId == candidateId",
        "        candidateBars += 1",
        "    else",
        "        candidateId := rawId",
        "        candidateBars := 1",
        f"    if candidateBars >= {confirm_expr}",
        "        confirmedId := candidateId",
        "else",
        "    candidateId := 0",
        "    candidateBars := 0",
        "    bool weakChallenger = confirmedId != 0 and candidateDisplayIdPre != 0 and candidateDisplayIdPre != confirmedId",
        "    bool coexistPressure = confirmedId != 0 and coexistRaw and candidateDisplayIdPre == 0",
        "    if chaosRaw and confirmedId != 0",
        "        stalePressureReason := 1",
        "    else if weakChallenger",
        "        stalePressureReason := 2",
        "    else if coexistPressure",
        "        stalePressureReason := 3",
        "    else",
        "        stalePressureReason := 0",
        "    if stalePressureReason != 0",
        "        stalePressureBars += 1",
        "        if stalePressureBars >= staleLimit",
        "            confirmedId := 0",
        "    else",
        "        stalePressureBars := 0",
        "int formalId = confirmedId",
        "// ===== End Issue #57 Phase B =====",
    ]
    lines[start : formal_line + 1] = new_block


def _apply_phase_c_d(lines: list[str]) -> None:
    candidate_display = _assignment_index(lines, "candidateDisplayId")
    insert_at = candidate_display + 1
    block = [
        "",
        "// ===== Issue #57 Phase C/D canonical four-state layer =====",
        "float v06AccFamily = p1 + p3",
        "float v06Markup = p2",
        "float v06DistFamily = p4 + p6",
        "float v06Markdown = p5",
        "int v06FormalId = f_v06_map4(formalId)",
        "float v06FormalSupport = v06FormalId == 1 ? v06AccFamily : v06FormalId == 2 ? v06Markup : v06FormalId == 3 ? v06DistFamily : v06FormalId == 4 ? v06Markdown : na",
        "float v06Competitor = v06FormalId == 1 ? math.max(v06Markup, math.max(v06DistFamily, v06Markdown)) : v06FormalId == 2 ? math.max(v06AccFamily, math.max(v06DistFamily, v06Markdown)) : v06FormalId == 3 ? math.max(v06AccFamily, math.max(v06Markup, v06Markdown)) : v06FormalId == 4 ? math.max(v06AccFamily, math.max(v06Markup, v06DistFamily)) : na",
        "float v06RegimeMargin = v06FormalId == 0 ? na : v06FormalSupport - v06Competitor",
        "// Regime Support / Regime Margin are descriptive state-strength measures; NOT confidence/probability.",
        "// ===== End Issue #57 Phase C/D =====",
        "",
    ]
    lines[insert_at:insert_at] = block


def _research_suffix() -> str:
    target_rows = []
    for year, month, day in CHECKPOINTS:
        target_rows.append(f'    [{year}, {month}, {day}, "{year:04d}-{month:02d}-{day:02d}"]')
    checkpoints_literal = ",\n".join(target_rows)
    return f'''
// ===== Issue #57 v0.6 compact research outputs =====
plot(v06AccFamily, "V06 acc_family", display=display.data_window)
plot(v06Markup, "V06 markup", display=display.data_window)
plot(v06DistFamily, "V06 dist_family", display=display.data_window)
plot(v06Markdown, "V06 markdown", display=display.data_window)
plot(float(v06FormalId), "V06 formal_id", display=display.data_window)
plot(v06FormalSupport, "V06 regime_support", display=display.data_window)
plot(v06RegimeMargin, "V06 regime_margin", display=display.data_window)
plot(noBreakLowScore, "V06 no_break_low", display=display.data_window)
plot(noBreakHighScore, "V06 no_break_high", display=display.data_window)
plot(breakoutScore, "V06 breakout_score", display=display.data_window)
plot(explicitBreakdownScore, "V06 breakdown_score", display=display.data_window)
plot(float(stalePressureBars), "V06 stale_pressure_bars", display=display.data_window)

var int[] v06Year = array.from(2019, 2020, 2021, 2022, 2024, 2026)
var int[] v06Month = array.from(8, 3, 6, 9, 4, 7)
var int[] v06Day = array.from(1, 20, 1, 28, 16, 30)
var string[] v06Target = array.from("2019-08-01", "2020-03-20", "2021-06-01", "2022-09-28", "2024-04-16", "2026-07-30")
var bool[] v06Captured = array.new_bool(6, false)
var string[] v06BarDate = array.new_string(6, "—")
var float[] v06Close = array.new_float(6, na)
var float[] v06Acc = array.new_float(6, na)
var float[] v06Mk = array.new_float(6, na)
var float[] v06Dist = array.new_float(6, na)
var float[] v06Md = array.new_float(6, na)
var float[] v06Formal = array.new_float(6, na)
var float[] v06Support = array.new_float(6, na)
var float[] v06Margin = array.new_float(6, na)

for i = 0 to 5
    targetTs = timestamp(syminfo.timezone, array.get(v06Year, i), array.get(v06Month, i), array.get(v06Day, i), 0, 0)
    if not array.get(v06Captured, i) and time_close >= targetTs
        array.set(v06Captured, i, true)
        array.set(v06BarDate, i, str.format_time(time_close, "yyyy-MM-dd", syminfo.timezone))
        array.set(v06Close, i, close)
        array.set(v06Acc, i, v06AccFamily)
        array.set(v06Mk, i, v06Markup)
        array.set(v06Dist, i, v06DistFamily)
        array.set(v06Md, i, v06Markdown)
        array.set(v06Formal, i, float(v06FormalId))
        array.set(v06Support, i, v06FormalSupport)
        array.set(v06Margin, i, v06RegimeMargin)

f_v06_num(x) => na(x) ? "—" : str.tostring(x, "#.0")
f_v06_close(x) => na(x) ? "—" : str.tostring(x, "#.#####")
var table v06Table = table.new(position.top_right, 10, 7, border_width=1)
if barstate.islast
    table.cell(v06Table, 0, 0, "Target", text_size=size.tiny)
    table.cell(v06Table, 1, 0, "Bar", text_size=size.tiny)
    table.cell(v06Table, 2, 0, "Close", text_size=size.tiny)
    table.cell(v06Table, 3, 0, "AccFam", text_size=size.tiny)
    table.cell(v06Table, 4, 0, "Markup", text_size=size.tiny)
    table.cell(v06Table, 5, 0, "DistFam", text_size=size.tiny)
    table.cell(v06Table, 6, 0, "Markdown", text_size=size.tiny)
    table.cell(v06Table, 7, 0, "Formal4", text_size=size.tiny)
    table.cell(v06Table, 8, 0, "Support", text_size=size.tiny)
    table.cell(v06Table, 9, 0, "Margin", text_size=size.tiny)
    for i = 0 to 5
        r = i + 1
        table.cell(v06Table, 0, r, array.get(v06Target, i), text_size=size.tiny)
        table.cell(v06Table, 1, r, array.get(v06BarDate, i), text_size=size.tiny)
        table.cell(v06Table, 2, r, f_v06_close(array.get(v06Close, i)), text_size=size.tiny)
        table.cell(v06Table, 3, r, f_v06_num(array.get(v06Acc, i)), text_size=size.tiny)
        table.cell(v06Table, 4, r, f_v06_num(array.get(v06Mk, i)), text_size=size.tiny)
        table.cell(v06Table, 5, r, f_v06_num(array.get(v06Dist, i)), text_size=size.tiny)
        table.cell(v06Table, 6, r, f_v06_num(array.get(v06Md, i)), text_size=size.tiny)
        table.cell(v06Table, 7, r, f_v06_num(array.get(v06Formal, i)), text_size=size.tiny)
        table.cell(v06Table, 8, r, f_v06_num(array.get(v06Support, i)), text_size=size.tiny)
        table.cell(v06Table, 9, r, f_v06_num(array.get(v06Margin, i)), text_size=size.tiny)

float v06SelfAtr = 100.0
float v06SelfBoundary = 100.0
float v06SelfNoBreakBoundary = f_v06_soft_no_break_low(v06SelfBoundary, v06SelfBoundary, v06SelfAtr)
float v06SelfNoBreakPlus = f_v06_soft_no_break_low(v06SelfBoundary + v06SelfAtr * V06_SOFT_WIDTH_ATR, v06SelfBoundary, v06SelfAtr)
float v06SelfBreakBoundary = f_v06_soft_break_above(v06SelfBoundary, v06SelfBoundary, v06SelfAtr)
var table v06Self = table.new(position.bottom_left, 2, 7, border_width=1)
if barstate.islast
    table.cell(v06Self, 0, 0, "v0.6 self-test", text_size=size.tiny)
    table.cell(v06Self, 1, 0, "value", text_size=size.tiny)
    table.cell(v06Self, 0, 1, "NoBreak@boundary", text_size=size.tiny)
    table.cell(v06Self, 1, 1, f_v06_num(v06SelfNoBreakBoundary), text_size=size.tiny)
    table.cell(v06Self, 0, 2, "NoBreak +0.25ATR", text_size=size.tiny)
    table.cell(v06Self, 1, 2, f_v06_num(v06SelfNoBreakPlus), text_size=size.tiny)
    table.cell(v06Self, 0, 3, "Break@boundary", text_size=size.tiny)
    table.cell(v06Self, 1, 3, f_v06_num(v06SelfBreakBoundary), text_size=size.tiny)
    table.cell(v06Self, 0, 4, "Map 3→4state", text_size=size.tiny)
    table.cell(v06Self, 1, 4, str.tostring(f_v06_map4(3)), text_size=size.tiny)
    table.cell(v06Self, 0, 5, "Map 6→4state", text_size=size.tiny)
    table.cell(v06Self, 1, 5, str.tostring(f_v06_map4(6)), text_size=size.tiny)
    table.cell(v06Self, 0, 6, "Stale limit", text_size=size.tiny)
    table.cell(v06Self, 1, 6, str.tostring(staleLimit), text_size=size.tiny)
'''.strip()


def render_v06_parity_source() -> str:
    raw = SOURCE.read_bytes()
    actual = git_blob_sha(raw)
    if actual != EXPECTED_SOURCE_BLOB_SHA:
        raise RuntimeError(f"Frozen Pine changed: expected {EXPECTED_SOURCE_BLOB_SHA}, got {actual}")
    text = raw.decode("utf-8")
    if text.count(VISUAL_MARKER) != 1:
        raise RuntimeError("Expected exactly one // Visuals marker")
    calculation_core, _ = text.split(VISUAL_MARKER, 1)
    lines = calculation_core.rstrip().splitlines()

    title_index = _find_unique(lines, 'indicator("Chase Risk Market Regime Radar v0.5.2.1')
    lines[title_index] = 'indicator("Chase Risk Radar v0.6｜Issue #57 Research Parity", shorttitle="ChaseRisk v0.6 #57", overlay=false, precision=1)'
    _force_research_modes(lines)
    atr_name = _extract_atr_name(lines)
    _apply_phase_a(lines, atr_name)
    _apply_phase_b(lines)
    _apply_phase_c_d(lines)
    return "\n".join(lines).rstrip() + "\n\n" + _research_suffix() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Issue #57 v0.6 Pine research parity harness")
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = render_v06_parity_source()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8")


if __name__ == "__main__":
    main()
