#!/usr/bin/env python3
"""Finalize the generated v0.6 Transition Health Pine preview.

The full-source generator deliberately reuses a large legacy visual source.
This finalizer applies two parity/compile-critical corrections:
1. the frozen research condition `np.all(carried > context)` means an undefined
   weight breaks the hold instead of being ignored;
2. Pine's parser can reject the generated multi-line ternary stage-weight helper,
   so the exact same expression is emitted on one line.
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


def _replace_exactly_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"Expected exactly one {label}; found {count}")
    return source.replace(old, new, 1)


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
