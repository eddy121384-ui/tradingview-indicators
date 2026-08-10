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
    """Replace a possibly multiline Pine assignment with a supplied block.

    Continuation lines are identified by bracket balance and indentation. This
    is intentionally limited to top-level float/bool assignments in the frozen
    source and fails closed if the expected statement cannot be isolated.
    """

    start = _assignment_index(lines, variable)
    base_indent = len(lines[start]) - len(lines[start].lstrip())
    balance = lines[start].count("(") - lines[start].count(")")
    end = start
    while balance > 0:
        end += 1
        if end >= len(lines):
            raise RuntimeError(f"Unterminated assignment for {variable}")
        balance += lines[end].count("(") - lines[end].count(")")
    # Ternary expressions may be line-wrapped without parentheses. Continue
    # through deeper-indented lines until the next peer-level declaration.
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
    del atr_name  # helper signatures receive ATR explicitly; retained for audit clarity.
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
    # The v0.6 experiment remains price/structure only. Replacing the input
    # declarations with constants also makes the generated research boundary
    # impossible to accidentally toggle in TradingView.
    for variable, expression, pine_type in (
        ("volumeMode", '"Off"', "string"),
        ("mtfMode", '"Off"', "string"),
        ("divMode", '"Off"', "string"),
        ("witnessStageBiasMode", '"Conservative"', "string"),
    ):
        _replace_assignment(lines, variable, expression, pine_type)


def _apply_phase_a(lines: list[str], atr_name: str) -> None:
    # Insert helpers before the first modified primitive.
    first = _assignment_index(lines, "noBreakLowScore")
    lines[first:first] = _helpers(atr_name)

    _replace_assignment(
        lines,
        "noBreakLowScore",
        f"f_v06_soft_no_break_low(close, prevAbsLow, {atr_name})",
        "float",
    )
    _replace_assignment(
        lines,
        "noBreakHighScore",
        f"f_v06_soft_no_break_high(close, prevAbsHigh, {atr_name})",
        "float",
    )

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

    _replace_statement(
        lines,
        "rangeContUp",
        [
            f"float abovePrevRangeScore = f_v06_soft_above_range(close, prevRangeHigh, {atr_name})",
            f"float belowPrevRangeScore = f_v06_soft_below_range(close, prevRangeLow, {atr_name})",
            "float sustainedAboveScore = ta.lowest(abovePrevRangeScore, continuationHoldBars)",
            "float sustainedBelowScore = ta.lowest(belowPrevRangeScore, continuationHoldBars)",
            "float rangeBreakUpEvidence = nz(recentRangeBreakUpStrength, 0.0) * 0.65",
            "float rangeBreakDnEvidence = nz(recentRangeBreakDnStrength, 0.0) * 0.65",
            "float rangeContUpBase = math.max(rangeBreakUpEvidence, recentMaCrossUp ? 65.0 : close > rangeMid ? 35.0 : 0.0)",
            "float rangeContDnBase = math.max(rangeBreakDnEvidence, recentMaCrossDn ? 65.0 : close < rangeMid ? 35.0 : 0.0)",
            "float rangeContUp = math.max(rangeContUpBase, math.max(nz(abovePrevRangeScore, 0.0) * 0.80, nz(sustainedAboveScore, 0.0)))",
            "float rangeContDn = math.max(rangeContDnBase, math.max(nz(belowPrevRangeScore, 0.0) * 0.80, nz(sustainedBelowScore, 0.0)))",
        ],
    )
    # Remove the old mirror assignment if it still remains after replacing the
    # rangeContUp statement block.
    old_dn_hits = [i for i, line in enumerate(lines) if re.search(r"\brangeContDn\s*=", line)]
    if len(old_dn_hits) > 1:
        # Keep the v0.6 declaration; delete any later frozen declaration.
        for index in reversed(old_dn_hits[1:]):
            del lines[index]

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
        # The frozen script may spell the active horizon inline; use the already
        # frozen fast-switch inputs rather than inventing a new parameter.
        confirm_expr = "(fastSwitch ? fastSwitchConfirmBars : confirmBars)"

    new_block = [
        "// ===== Issue #57 Phase B persistence redesign =====",
        "var int confirmed = 0",
        "var int candidate = 0",
        "var int candidateBars = 0",
        "var int stalePressureBars = 0",
        "int stalePressureReason = 0",
        "int staleLimit = confirmBars * 2",
        "if strongCandidate",
        "    stalePressureBars := 0",
        "    stalePressureReason := 0",
        "    int rawId = topId",
        "    if rawId == candidate",
        "        candidateBars += 1",
        "    else",
        "        candidate := rawId",
        "        candidateBars := 1",
        f"    if candidateBars >= {confirm_expr}",
        "        confirmed := candidate",
        "else",
        "    candidate := 0",
        "    candidateBars := 0",
        "    bool weakChallenger = confirmed != 0 and candidateDisplayId != 0 and candidateDisplayId != confirmed",
        "    bool coexistPressure = confirmed != 0 and coexist and candidateDisplayId == 0",
        "    if chaos and confirmed != 0",
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
        "            confirmed := 0",
        "    else",
        "        stalePressureBars := 0",
        "int formalId = confirmed",
        "// ===== End Issue #57 Phase B =====",
    ]
    lines[start : formal_line + 1] = new_block


def _apply_phase_c_d(lines: list[str]) -> None:
    formal_index = _assignment_index(lines, "formalId")
    insert = [
        "",
        "// ===== Issue #57 Phase C/D canonical regime layer =====",
        "float v06AccFamily = probAcc + probReacc",
        "float v06Markup = probMarkup",
        "float v06DistFamily = probDist + probRedist",
        "float v06Markdown = probMarkdown",
        "int v06CanonicalCandidate = f_v06_map4(candidateDisplayId)",
        "int v06CanonicalFormal = f_v06_map4(formalId)",
        "float v06RegimeSupport = v06CanonicalFormal == 1 ? v06AccFamily : v06CanonicalFormal == 2 ? v06Markup : v06CanonicalFormal == 3 ? v06DistFamily : v06CanonicalFormal == 4 ? v06Markdown : na",
        "float v06StrongestOther = v06CanonicalFormal == 1 ? math.max(v06Markup, math.max(v06DistFamily, v06Markdown)) : v06CanonicalFormal == 2 ? math.max(v06AccFamily, math.max(v06DistFamily, v06Markdown)) : v06CanonicalFormal == 3 ? math.max(v06AccFamily, math.max(v06Markup, v06Markdown)) : v06CanonicalFormal == 4 ? math.max(v06AccFamily, math.max(v06Markup, v06DistFamily)) : na",
        "float v06RegimeMargin = v06CanonicalFormal == 0 ? na : v06RegimeSupport - v06StrongestOther",
        "// Regime Support/Margin are descriptive classification-strength fields, not probability/confidence.",
        "// ===== End Issue #57 Phase C/D =====",
        "",
    ]
    lines[formal_index + 1 : formal_index + 1] = insert


def _checkpoint_append() -> str:
    timestamp_rows = ",\n    ".join(
        f"timestamp(syminfo.timezone, {year}, {month}, {day}, 0, 0)" for year, month, day in CHECKPOINTS
    )
    target_labels = ", ".join(f'"{year:04d}-{month:02d}-{day:02d}"' for year, month, day in CHECKPOINTS)
    return f'''

// ===== Issue #57 v0.6 parity outputs =====
plot(v06AccFamily, "v06 Accumulation family", display=display.data_window)
plot(v06Markup, "v06 Markup", display=display.data_window)
plot(v06DistFamily, "v06 Distribution family", display=display.data_window)
plot(v06Markdown, "v06 Markdown", display=display.data_window)
plot(v06CanonicalCandidate, "v06 canonical candidate", display=display.data_window)
plot(v06CanonicalFormal, "v06 canonical formal", display=display.data_window)
plot(v06RegimeMargin, "v06 Regime Margin", display=display.data_window)
plot(v06RegimeSupport, "v06 Regime Support", display=display.data_window)
plot(formalId, "v06 six-state formal", display=display.data_window)
plot(stalePressureBars, "v06 stale pressure bars", display=display.data_window)
plot(noBreakLowScore, "v06 no-break low score", display=display.data_window)
plot(noBreakHighScore, "v06 no-break high score", display=display.data_window)

var int[] v06Targets = array.from(
    {timestamp_rows}
)
var string[] v06TargetLabels = array.from({target_labels})
var bool[] v06Captured = array.new_bool({len(CHECKPOINTS)}, false)
var int[] v06BarTs = array.new_int({len(CHECKPOINTS)}, na)
var float[] v06CpAcc = array.new_float({len(CHECKPOINTS)}, na)
var float[] v06CpMk = array.new_float({len(CHECKPOINTS)}, na)
var float[] v06CpDist = array.new_float({len(CHECKPOINTS)}, na)
var float[] v06CpMd = array.new_float({len(CHECKPOINTS)}, na)
var int[] v06CpCand = array.new_int({len(CHECKPOINTS)}, 0)
var int[] v06CpFormal = array.new_int({len(CHECKPOINTS)}, 0)
var float[] v06CpMargin = array.new_float({len(CHECKPOINTS)}, na)
var float[] v06CpSupport = array.new_float({len(CHECKPOINTS)}, na)
var int[] v06CpSixFormal = array.new_int({len(CHECKPOINTS)}, 0)
var int[] v06CpStaleBars = array.new_int({len(CHECKPOINTS)}, 0)
var int[] v06CpStaleReason = array.new_int({len(CHECKPOINTS)}, 0)

for i = 0 to {len(CHECKPOINTS) - 1}
    if not array.get(v06Captured, i) and not na(time_close) and time_close >= array.get(v06Targets, i)
        array.set(v06Captured, i, true)
        array.set(v06BarTs, i, time_close)
        array.set(v06CpAcc, i, v06AccFamily)
        array.set(v06CpMk, i, v06Markup)
        array.set(v06CpDist, i, v06DistFamily)
        array.set(v06CpMd, i, v06Markdown)
        array.set(v06CpCand, i, v06CanonicalCandidate)
        array.set(v06CpFormal, i, v06CanonicalFormal)
        array.set(v06CpMargin, i, v06RegimeMargin)
        array.set(v06CpSupport, i, v06RegimeSupport)
        array.set(v06CpSixFormal, i, formalId)
        array.set(v06CpStaleBars, i, stalePressureBars)
        array.set(v06CpStaleReason, i, stalePressureReason)

var table v06Table = table.new(position.top_right, 12, {len(CHECKPOINTS) + 1}, border_width=1)
var table v06Self = table.new(position.bottom_left, 2, 7, border_width=1)

if barstate.islast
    string[] headers = array.from("Target", "Bar", "AccFam", "Markup", "DistFam", "Markdown", "Cand4", "Formal4", "Margin", "Support", "Formal6", "Stale")
    for c = 0 to 11
        table.cell(v06Table, c, 0, array.get(headers, c), text_size=size.tiny)
    for i = 0 to {len(CHECKPOINTS) - 1}
        int row = i + 1
        int barTs = array.get(v06BarTs, i)
        table.cell(v06Table, 0, row, array.get(v06TargetLabels, i), text_size=size.tiny)
        table.cell(v06Table, 1, row, na(barTs) ? "—" : str.format_time(barTs, "yyyy-MM-dd", syminfo.timezone), text_size=size.tiny)
        table.cell(v06Table, 2, row, str.tostring(array.get(v06CpAcc, i), "#.0"), text_size=size.tiny)
        table.cell(v06Table, 3, row, str.tostring(array.get(v06CpMk, i), "#.0"), text_size=size.tiny)
        table.cell(v06Table, 4, row, str.tostring(array.get(v06CpDist, i), "#.0"), text_size=size.tiny)
        table.cell(v06Table, 5, row, str.tostring(array.get(v06CpMd, i), "#.0"), text_size=size.tiny)
        table.cell(v06Table, 6, row, str.tostring(array.get(v06CpCand, i)), text_size=size.tiny)
        table.cell(v06Table, 7, row, str.tostring(array.get(v06CpFormal, i)), text_size=size.tiny)
        table.cell(v06Table, 8, row, str.tostring(array.get(v06CpMargin, i), "#.0"), text_size=size.tiny)
        table.cell(v06Table, 9, row, str.tostring(array.get(v06CpSupport, i), "#.0"), text_size=size.tiny)
        table.cell(v06Table, 10, row, str.tostring(array.get(v06CpSixFormal, i)), text_size=size.tiny)
        table.cell(v06Table, 11, row, str.tostring(array.get(v06CpStaleBars, i)) + "/" + str.tostring(array.get(v06CpStaleReason, i)), text_size=size.tiny)

    // Feed-independent primitive/mapping self-checks. These values must match
    // Python unit tests regardless of the chart data source.
    float selfAtr = 0.008
    float selfBoundary = 1.06236
    table.cell(v06Self, 0, 0, "v0.6 self-test", text_size=size.tiny)
    table.cell(v06Self, 1, 0, "TV", text_size=size.tiny)
    table.cell(v06Self, 0, 1, "NoBreak@boundary", text_size=size.tiny)
    table.cell(v06Self, 1, 1, str.tostring(f_v06_soft_no_break_low(selfBoundary, selfBoundary, selfAtr), "#.000"), text_size=size.tiny)
    table.cell(v06Self, 0, 2, "NoBreak +0.25ATR", text_size=size.tiny)
    table.cell(v06Self, 1, 2, str.tostring(f_v06_soft_no_break_low(selfBoundary + selfAtr * 0.25, selfBoundary, selfAtr), "#.000"), text_size=size.tiny)
    table.cell(v06Self, 0, 3, "Break@boundary", text_size=size.tiny)
    table.cell(v06Self, 1, 3, str.tostring(f_v06_soft_break_above(selfBoundary, selfBoundary, selfAtr), "#.000"), text_size=size.tiny)
    table.cell(v06Self, 0, 4, "Map 3→4state", text_size=size.tiny)
    table.cell(v06Self, 1, 4, str.tostring(f_v06_map4(3)), text_size=size.tiny)
    table.cell(v06Self, 0, 5, "Map 6→4state", text_size=size.tiny)
    table.cell(v06Self, 1, 5, str.tostring(f_v06_map4(6)), text_size=size.tiny)
    table.cell(v06Self, 0, 6, "Stale limit", text_size=size.tiny)
    table.cell(v06Self, 1, 6, str.tostring(confirmBars * {STALE_DECAY_MULTIPLIER}), text_size=size.tiny)
// ===== End Issue #57 v0.6 parity outputs =====
'''


def render_v06_parity_source() -> str:
    raw = SOURCE.read_bytes()
    actual = git_blob_sha(raw)
    if actual != EXPECTED_SOURCE_BLOB_SHA:
        raise RuntimeError(
            "Frozen v0.5.2.1 Pine moved; refusing v0.6 parity generation: "
            f"expected {EXPECTED_SOURCE_BLOB_SHA}, got {actual}"
        )
    lines = raw.decode("utf-8").splitlines()
    _force_research_modes(lines)
    atr_name = _extract_atr_name(lines)
    _apply_phase_a(lines, atr_name)
    _apply_phase_b(lines)
    _apply_phase_c_d(lines)

    visual_hits = [index for index, line in enumerate(lines) if line.strip() == VISUAL_MARKER]
    if len(visual_hits) != 1:
        raise RuntimeError(f"Expected exactly one {VISUAL_MARKER!r}; found {len(visual_hits)}")
    core = "\n".join(lines[: visual_hits[0]]) + "\n"
    banner = (
        "// GENERATED RESEARCH HARNESS — Issue #57 / Wyckoff v0.6\n"
        "// Source: frozen chase-risk-market-regime-radar-v0.5.2.1.pine\n"
        "// v0.5.2.1 is NOT modified. Price-only witnesses are forced off.\n"
        "// Regime Support/Margin are descriptive classification strength, NOT confidence/probability.\n\n"
    )
    return banner + core + _checkpoint_append()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Issue #57 v0.6 Pine parity harness")
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_v06_parity_source(), encoding="utf-8")


if __name__ == "__main__":
    main()
