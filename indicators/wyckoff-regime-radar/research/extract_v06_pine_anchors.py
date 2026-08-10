#!/usr/bin/env python3
"""Extract small frozen-v0.5 Pine snippets needed by the v0.6 generator.

This is a temporary/audit helper: it does not transform Pine or evaluate data.
"""

from __future__ import annotations

import argparse
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "src" / "chase-risk-market-regime-radar-v0.5.2.1.pine"
KEYWORDS = (
    "noBreakLowScore",
    "noBreakHighScore",
    "rangeBreakUp",
    "rangeBreakDn",
    "recentBreakUp",
    "recentBreakDn",
    "recentRangeBreakDn",
    "recentMaCrossDn",
    "breakoutModeUp",
    "breakdownModeDn",
    "breakoutScore",
    "explicitBreakdownScore",
    "sustainedAbove",
    "sustainedBelow",
    "rangeContUp",
    "rangeContDn",
    "breakoutGate",
    "explicitBreakdownGate",
    "candidateDisplayId",
    "strongCandidate",
    "candidateBars",
    "noRegimeBars",
    "confirmed",
    "formalId",
)


def extract(radius: int = 2) -> str:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    chosen: set[int] = set()
    for index, line in enumerate(lines):
        if any(keyword in line for keyword in KEYWORDS):
            for item in range(max(0, index - radius), min(len(lines), index + radius + 1)):
                chosen.add(item)
    out = ["# Issue #57 frozen Pine anchor map", ""]
    previous = None
    for index in sorted(chosen):
        if previous is not None and index > previous + 1:
            out.append("...")
        out.append(f"{index + 1:04d}: {lines[index]}")
        previous = index
    return "\n".join(out) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(extract(), encoding="utf-8")


if __name__ == "__main__":
    main()
