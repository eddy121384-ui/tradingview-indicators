#!/usr/bin/env python3
"""Finalize the generated v0.6 Transition Health Pine preview.

The full-source generator deliberately reuses a large legacy visual source.
This finalizer applies four parity/compile/UI-critical corrections:
1. the frozen research condition `np.all(carried > context)` means an undefined
   weight breaks the hold instead of being ignored;
2. Pine's parser can reject the generated multi-line ternary stage-weight helper,
   so the exact same expression is emitted on one line;
3. the shared Phase-A generator inserts its helper block near `noBreakLowScore`,
   but the full visual source first calls those helpers earlier. Pine requires the
   function definitions to appear before that first use, so the helper block is
   relocated without changing any formula;
4. dense text labels are reduced to event-only geometric markers so historical
   Transition Health episodes remain visually readable without changing state
   semantics or event timing.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from generate_v06_transition_health_preview_pine import render_preview_source

OLD_LEAD = """        if not na(v06ThContextWeightNow) and not na(v06ThCarriedWeightNow) and v06ThContextWeightNow >= v06ThCarriedWeightNow
            v06ThLeadHeld := false"""
NEW_LEAD = """        if na(v06ThContextWeightNow) or na(v06ThCarriedWeightNow) or not (v06ThCarriedWeightNow > v06ThContextWeightNow)
            v06ThLeadHeld := false"""

OLD_STAGE_WEIGHT = """f_v06_stage_weight(int id) =>
    id == 1 ? probAcc :
    id == 2 ? probMarkup :
    id == 3 ? probReacc :
    id == 4 ? probDist :
    id == 5 ? probMarkdown :
    id == 6 ? probRedist : na"""
NEW_STAGE_WEIGHT = """f_v06_stage_weight(int id) =>
    id == 1 ? probAcc : id == 2 ? probMarkup : id == 3 ? probReacc : id == 4 ? probDist : id == 5 ? probMarkdown : id == 6 ? probRedist : na"""

OLD_EVENT_MARKERS = """if showTransitionHealthLabels and v06ThHandoffPulse
    label.new(bar_index, v06ThWatchDir > 0 ? 8.0 : 92.0, v06ThWatchDir > 0 ? \"Handoff ↑\" : \"Handoff ↓\", style=v06ThWatchDir > 0 ? label.style_label_up : label.style_label_down, color=color.new(colYellow, 0), textcolor=colDarkText, size=size.tiny)
if showTransitionHealthLabels and v06ThHealthyPulse
    label.new(bar_index, v06ThWatchDir > 0 ? 18.0 : 82.0, v06ThWatchDir > 0 ? \"Healthy ↑\" : \"Healthy ↓\", style=v06ThWatchDir > 0 ? label.style_label_up : label.style_label_down, color=color.new(colBreakout, 0), textcolor=colDarkText, size=size.tiny)
if showTransitionHealthLabels and v06ThDamagedPulse
    label.new(bar_index, v06ThWatchDir > 0 ? 18.0 : 82.0, v06ThWatchDir > 0 ? \"Damaged ↑\" : \"Damaged ↓\", style=v06ThWatchDir > 0 ? label.style_label_up : label.style_label_down, color=color.new(colRed, 0), textcolor=color.white, size=size.tiny)"""

NEW_EVENT_MARKERS = """// Minimal event-only markers: no repeated text strip on historical charts.
if showTransitionHealthLabels and v06ThHandoffPulse
    label.new(bar_index, v06ThWatchDir > 0 ? 7.0 : 93.0, \"\", style=label.style_circle, color=color.new(colYellow, 30), textcolor=colYellow, size=size.tiny)
if showTransitionHealthLabels and v06ThHealthyPulse
    label.new(bar_index, v06ThWatchDir > 0 ? 17.0 : 83.0, \"\", style=v06ThWatchDir > 0 ? label.style_triangleup : label.style_triangledown, color=color.new(colBreakout, 0), textcolor=colBreakout, size=size.small)
if showTransitionHealthLabels and v06ThDamagedPulse
    label.new(bar_index, v06ThWatchDir > 0 ? 17.0 : 83.0, \"\", style=label.style_xcross, color=color.new(colRed, 0), textcolor=colRed, size=size.small)"""

HELPER_START = "// ===== Issue #57 v0.6 research helpers (mechanically generated) ====="
HELPER_END = "// ===== End Issue #57 helpers ====="
FIRST_HELPER_USE = "float rangeBreakUpStrength = f_v06_soft_break_above(close, rangeHighBreak, atr)"


def _replace_exactly_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"Expected exactly one {label}; found {count}")
    return source.replace(old, new, 1)


def _relocate_phase_a_helpers(source: str) -> str:
    """Move the generated Phase-A helper block before its first full-source use."""
    lines = source.splitlines()
    starts = [i for i, line in enumerate(lines) if line.strip() == HELPER_START]
    ends = [i for i, line in enumerate(lines) if line.strip() == HELPER_END]
    uses = [i for i, line in enumerate(lines) if FIRST_HELPER_USE in line]
    if len(starts) != 1 or len(ends) != 1 or len(uses) != 1:
        raise RuntimeError(
            "Expected one Phase-A helper block and one first-use anchor; "
            f"starts={starts}, ends={ends}, uses={uses}"
        )

    start, end, use = starts[0], ends[0], uses[0]
    if end < start:
        raise RuntimeError("Phase-A helper end appears before helper start")
    if start < use:
        return source

    block = lines[start : end + 1]
    del lines[start : end + 1]

    # Removing a block that originally lived after the first-use anchor does not
    # change the first-use index. Insert one blank line plus the helper block.
    lines[use:use] = [*block, ""]

    rebuilt = "\n".join(lines).rstrip() + "\n"
    helper_pos = rebuilt.find(HELPER_START)
    use_pos = rebuilt.find(FIRST_HELPER_USE)
    if helper_pos < 0 or use_pos < 0 or helper_pos >= use_pos:
        raise RuntimeError("Phase-A helper relocation failed compile-order check")
    return rebuilt


def finalize_preview_source(source: str) -> str:
    source = _replace_exactly_once(
        source,
        OLD_LEAD,
        NEW_LEAD,
        "Transition Health lead-hold block",
    )
    source = _replace_exactly_once(
        source,
        OLD_STAGE_WEIGHT,
        NEW_STAGE_WEIGHT,
        "Transition Health stage-weight helper",
    )
    source = _replace_exactly_once(
        source,
        OLD_EVENT_MARKERS,
        NEW_EVENT_MARKERS,
        "Transition Health event-marker block",
    )
    source = _relocate_phase_a_helpers(source)
    return source


def render_final_preview_source() -> str:
    return finalize_preview_source(render_preview_source())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = render_final_preview_source()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8")


if __name__ == "__main__":
    main()
