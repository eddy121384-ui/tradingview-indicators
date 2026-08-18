#!/usr/bin/env python3
"""Generate the Issue #57 v0.6 Transition Health visual preview.

Unlike the compact parity harness, this generator preserves the frozen
v0.5.2.1 visual layer, applies the already-decided v0.6 Phase A/B/C/D core
changes, forces unvalidated witness layers Off, and adds only the frozen
Transition Health visualization/state machine.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from generate_v06_parity_pine import (
    EXPECTED_SOURCE_BLOB_SHA,
    SOURCE,
    _apply_phase_a,
    _apply_phase_b,
    _apply_phase_c_d,
    _extract_atr_name,
    _find_unique,
    git_blob_sha,
)

VISUAL_MARKER = "// Visuals"


def _force_price_only_modes(lines: list[str]) -> None:
    """Replace only the four global mode declarations, never `==` comparisons."""
    replacements = {
        "volumeMode": 'string volumeMode = "Off"',
        "mtfMode": 'string mtfMode = "Off"',
        "divMode": 'string divMode = "Off"',
        "witnessStageBiasMode": 'string witnessStageBiasMode = "Conservative"',
    }
    for variable, replacement in replacements.items():
        pattern = re.compile(rf"^\s*(?:string\s+)?{re.escape(variable)}\s*=(?!=)")
        hits = [i for i, line in enumerate(lines) if pattern.search(line)]
        if len(hits) != 1:
            raise RuntimeError(f"Expected one declaration for {variable}; found {len(hits)}")
        index = hits[0]
        indent = lines[index][: len(lines[index]) - len(lines[index].lstrip())]
        lines[index] = indent + replacement


def _transition_health_block() -> list[str]:
    return r'''
// ===== Issue #57 v0.6 Transition Health｜frozen +3 OOS candidate =====
groupTransitionHealth = "顯示｜Transition Health v0.6"
showTransitionHealthLabels = input.bool(true, "顯示 Handoff / Healthy / Damaged 標記", group=groupTransitionHealth)
showTransitionHealthPanel = input.bool(true, "顯示 Transition Health 狀態框", group=groupTransitionHealth)
transitionHealthParityLogs = input.bool(false, "Parity Logs（驗證用）", group=groupTransitionHealth)

int V06_TH_CHECKPOINT = 3
int V06_TH_MAX_WATCH = 20
int V06_TH_NONE = 0
int V06_TH_HANDOFF = 1
int V06_TH_HEALTHY = 2
int V06_TH_DAMAGED = 3

f_v06_stage_weight(int id) =>
    id == 1 ? probAcc :
    id == 2 ? probMarkup :
    id == 3 ? probReacc :
    id == 4 ? probDist :
    id == 5 ? probMarkdown :
    id == 6 ? probRedist : na

bool v06BullBridge = ((topId == 1 and (secondaryId == 2 or secondaryId == 3)) or (secondaryId == 1 and (topId == 2 or topId == 3)))
bool v06BearBridge = ((topId == 4 and (secondaryId == 5 or secondaryId == 6)) or (secondaryId == 4 and (topId == 5 or topId == 6)))
int v06BridgeDir = v06BullBridge ? 1 : v06BearBridge ? -1 : 0

bool v06BullActionable = (topId == 2 and secondaryId == 3) or (topId == 3 and secondaryId == 2)
bool v06BearActionable = (topId == 5 and secondaryId == 6) or (topId == 6 and secondaryId == 5)
int v06ActionDir = v06BullActionable ? 1 : v06BearActionable ? -1 : 0

var bool v06ThWatchActive = false
var int v06ThWatchDir = 0
var int v06ThWatchAge = 0
var int v06ThContextId = 0
var int v06ThCarriedId = 0
var bool v06ThTracked = false
var bool v06ThLeadHeld = false
var int v06ThState = V06_TH_NONE

bool v06ThHandoffPulse = false
bool v06ThHealthyPulse = false
bool v06ThDamagedPulse = false
bool v06ThResolutionPulse = false

if not v06ThWatchActive
    if v06BridgeDir != 0
        v06ThWatchActive := true
        v06ThWatchDir := v06BridgeDir
        v06ThWatchAge := 0
        v06ThContextId := v06BridgeDir > 0 ? 1 : 4
        v06ThCarriedId := topId == v06ThContextId ? secondaryId : topId
        float v06ThContextWeight0 = f_v06_stage_weight(v06ThContextId)
        float v06ThCarriedWeight0 = f_v06_stage_weight(v06ThCarriedId)
        v06ThTracked := not na(v06ThContextWeight0) and not na(v06ThCarriedWeight0) and v06ThCarriedWeight0 > v06ThContextWeight0
        v06ThLeadHeld := v06ThTracked
        v06ThState := v06ThTracked ? V06_TH_HANDOFF : V06_TH_NONE
        v06ThHandoffPulse := v06ThTracked
else
    v06ThWatchAge += 1
    bool v06ThResolvesNow = v06ActionDir == v06ThWatchDir or v06ActionDir == -v06ThWatchDir or v06ThWatchAge >= V06_TH_MAX_WATCH

    if v06ThTracked and v06ThWatchAge <= V06_TH_CHECKPOINT
        float v06ThContextWeightNow = f_v06_stage_weight(v06ThContextId)
        float v06ThCarriedWeightNow = f_v06_stage_weight(v06ThCarriedId)
        if not na(v06ThContextWeightNow) and not na(v06ThCarriedWeightNow) and v06ThContextWeightNow >= v06ThCarriedWeightNow
            v06ThLeadHeld := false

    // Research eligibility is resolution_lag > 3. A watch resolving on/before +3 gets no health label.
    if v06ThTracked and v06ThWatchAge == V06_TH_CHECKPOINT and not v06ThResolvesNow
        if v06ThLeadHeld
            v06ThState := V06_TH_HEALTHY
            v06ThHealthyPulse := true
        else
            v06ThState := V06_TH_DAMAGED
            v06ThDamagedPulse := true

    if v06ThResolvesNow
        v06ThResolutionPulse := true
        v06ThWatchActive := false
        v06ThWatchDir := 0
        v06ThWatchAge := 0
        v06ThContextId := 0
        v06ThCarriedId := 0
        v06ThTracked := false
        v06ThLeadHeld := false
        v06ThState := V06_TH_NONE

int v06ThDisplayDir = v06ThTracked ? v06ThWatchDir : 0
string v06ThStateText = v06ThState == V06_TH_HANDOFF ? "Handoff｜等待 +3" : v06ThState == V06_TH_HEALTHY ? "Healthy" : v06ThState == V06_TH_DAMAGED ? "Damaged" : "—"
string v06ThDirText = v06ThDisplayDir > 0 ? "Bull ↑" : v06ThDisplayDir < 0 ? "Bear ↓" : "—"
color v06ThStateColor = v06ThState == V06_TH_HEALTHY ? colBreakout : v06ThState == V06_TH_DAMAGED ? colRed : v06ThState == V06_TH_HANDOFF ? colYellow : colNeutral

if showTransitionHealthLabels and v06ThHandoffPulse
    label.new(bar_index, v06ThWatchDir > 0 ? 8.0 : 92.0, v06ThWatchDir > 0 ? "Handoff ↑" : "Handoff ↓", style=v06ThWatchDir > 0 ? label.style_label_up : label.style_label_down, color=color.new(colYellow, 0), textcolor=colDarkText, size=size.tiny)
if showTransitionHealthLabels and v06ThHealthyPulse
    label.new(bar_index, v06ThWatchDir > 0 ? 18.0 : 82.0, v06ThWatchDir > 0 ? "Healthy ↑" : "Healthy ↓", style=v06ThWatchDir > 0 ? label.style_label_up : label.style_label_down, color=color.new(colBreakout, 0), textcolor=colDarkText, size=size.tiny)
if showTransitionHealthLabels and v06ThDamagedPulse
    label.new(bar_index, v06ThWatchDir > 0 ? 18.0 : 82.0, v06ThWatchDir > 0 ? "Damaged ↑" : "Damaged ↓", style=v06ThWatchDir > 0 ? label.style_label_up : label.style_label_down, color=color.new(colRed, 0), textcolor=color.white, size=size.tiny)

plot(float(v06ThState), "V06 Transition Health State｜0 none 1 handoff 2 healthy 3 damaged", display=display.data_window)
plot(float(v06ThDisplayDir), "V06 Transition Health Direction｜+1 bull -1 bear", display=display.data_window)
plot(v06ThWatchActive ? float(v06ThWatchAge) : na, "V06 Transition Health Watch Age", display=display.data_window)

var table v06ThDash = table.new(position.bottom_left, 2, 4, border_width=1)
if barstate.islast
    table.clear(v06ThDash, 0, 0, 1, 3)
    if showTransitionHealthPanel
        table.cell(v06ThDash, 0, 0, "Transition Health", text_color=colText, bgcolor=color.new(v06ThStateColor, 35), text_size=size.tiny)
        table.cell(v06ThDash, 1, 0, v06ThStateText, text_color=colDarkText, bgcolor=color.new(v06ThStateColor, 35), text_size=size.tiny)
        table.cell(v06ThDash, 0, 1, "方向", text_color=colText, bgcolor=color.new(colRowBg, dashboardTransp), text_size=size.tiny)
        table.cell(v06ThDash, 1, 1, v06ThDirText, text_color=colText, bgcolor=color.new(colRowBg, dashboardTransp), text_size=size.tiny)
        table.cell(v06ThDash, 0, 2, "Watch age", text_color=colText, bgcolor=color.new(colRowBg, dashboardTransp), text_size=size.tiny)
        table.cell(v06ThDash, 1, 2, v06ThWatchActive ? str.tostring(v06ThWatchAge) : "—", text_color=colText, bgcolor=color.new(colRowBg, dashboardTransp), text_size=size.tiny)
        table.cell(v06ThDash, 0, 3, "規則", text_color=colText, bgcolor=color.new(colRowBg, dashboardTransp), text_size=size.tiny)
        table.cell(v06ThDash, 1, 3, "篡位後連守 3 根", text_color=colText, bgcolor=color.new(colRowBg, dashboardTransp), text_size=size.tiny)

if transitionHealthParityLogs and (v06ThHandoffPulse or v06ThHealthyPulse or v06ThDamagedPulse)
    string v06ThEventText = v06ThHandoffPulse ? "handoff" : v06ThHealthyPulse ? "healthy" : "damaged"
    log.info("TH|" + str.format_time(time, "yyyy-MM-dd", syminfo.timezone) + "|event=" + v06ThEventText + "|state=" + str.tostring(v06ThState) + "|dir=" + str.tostring(v06ThDisplayDir) + "|age=" + str.tostring(v06ThWatchAge))
// ===== End Issue #57 Transition Health =====
'''.strip().splitlines()


def render_preview_source() -> str:
    raw = SOURCE.read_bytes()
    actual = git_blob_sha(raw)
    if actual != EXPECTED_SOURCE_BLOB_SHA:
        raise RuntimeError(f"Frozen Pine changed: expected {EXPECTED_SOURCE_BLOB_SHA}, got {actual}")

    lines = raw.decode("utf-8").rstrip().splitlines()
    title_index = _find_unique(lines, 'indicator("Chase Risk Market Regime Radar v0.5.2.1')
    lines[title_index] = 'indicator("Chase Risk Radar v0.6｜Transition Health Preview", shorttitle="ChaseRisk v0.6 TH", overlay=false, precision=1, max_labels_count=300)'

    # Keep the validated Issue #57 research boundary: price-only witnesses Off.
    _force_price_only_modes(lines)
    atr_name = _extract_atr_name(lines)
    _apply_phase_a(lines, atr_name)
    _apply_phase_b(lines)
    _apply_phase_c_d(lines)

    visual_index = _find_unique(lines, VISUAL_MARKER)
    block = ["", *_transition_health_block(), ""]
    lines[visual_index:visual_index] = block
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Issue #57 v0.6 Transition Health visual preview")
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = render_preview_source()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8")


if __name__ == "__main__":
    main()
