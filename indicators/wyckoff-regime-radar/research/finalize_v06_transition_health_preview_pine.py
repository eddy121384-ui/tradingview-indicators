#!/usr/bin/env python3
"""Finalize the generated v0.6 Transition Health Pine preview.

The full-source generator deliberately reuses a large legacy visual source.
This finalizer applies one parity-critical correction discovered by the
bar-for-bar verifier: the frozen research condition `np.all(carried > context)`
means an undefined weight breaks the hold instead of being ignored.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from generate_v06_transition_health_preview_pine import render_preview_source

OLD = """        if not na(v06ThContextWeightNow) and not na(v06ThCarriedWeightNow) and v06ThContextWeightNow >= v06ThCarriedWeightNow
            v06ThLeadHeld := false"""
NEW = """        if na(v06ThContextWeightNow) or na(v06ThCarriedWeightNow) or not (v06ThCarriedWeightNow > v06ThContextWeightNow)
            v06ThLeadHeld := false"""


def finalize_preview_source(source: str) -> str:
    count = source.count(OLD)
    if count != 1:
        raise RuntimeError(f"Expected exactly one Transition Health lead-hold block; found {count}")
    return source.replace(OLD, NEW, 1)


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
