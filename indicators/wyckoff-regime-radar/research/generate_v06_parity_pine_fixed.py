#!/usr/bin/env python3
"""Compatibility-fixed driver for the Issue #57 v0.6 Pine generator.

The original generator made a few source-location assumptions that Python tests
could tolerate but Pine could not: it treated equality checks (`==`) as
assignments, assumed there was only one `ta.atr()` call, and emitted the v0.6
helper functions after an earlier generated call site. This driver patches only
those source-location / declaration-order issues, then delegates all Phase A-D
transformations to the audited base generator.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import generate_v06_parity_pine as base


EXPECTED_SOURCE_BLOB_SHA = base.EXPECTED_SOURCE_BLOB_SHA
SOURCE = base.SOURCE
git_blob_sha = base.git_blob_sha

HELPER_START = "// ===== Issue #57 v0.6 research helpers (mechanically generated) ====="
HELPER_END = "// ===== End Issue #57 helpers ====="
FIRST_PHASE_A_HELPER_CALL = "float rangeBreakUpStrength = f_v06_soft_break_above"


def _assignment_index_fixed(lines: list[str], variable: str) -> int:
    pattern = re.compile(
        rf"^\s*(?:(?:var\s+)?(?:bool|float|int|string)\s+)?{re.escape(variable)}\s*=(?!=)"
    )
    hits = [index for index, line in enumerate(lines) if pattern.search(line)]
    if len(hits) != 1:
        raise RuntimeError(f"Expected one assignment to {variable}; found {len(hits)}")
    return hits[0]


def _extract_primary_atr_name_fixed(lines: list[str]) -> str:
    # Phase A's structural transition width was defined against the ordinary
    # short/medium ATR (`atr = ta.atr(atrLen)`), not maturityAtr. Match that
    # declaration explicitly and fail closed if the frozen source changes.
    pattern = re.compile(r"^\s*(?:float\s+)?atr\s*=\s*ta\.atr\(atrLen\)\s*$")
    hits = [index for index, line in enumerate(lines) if pattern.search(line)]
    if len(hits) != 1:
        raise RuntimeError(f"Expected one primary atr = ta.atr(atrLen) declaration; found {len(hits)}")
    return "atr"


def _move_v06_helpers_before_first_use(source: str) -> str:
    """Move generated Pine helper declarations before their first call site.

    Pine requires a user-defined function to be declared before it is called.
    The audited base generator originally inserts the helper block near the
    noBreak primitives, but Phase A also adds an earlier breakout-strength call.
    Relocate only that generated helper block; do not alter any formulas.
    """

    lines = source.splitlines()
    start_hits = [i for i, line in enumerate(lines) if line.strip() == HELPER_START]
    end_hits = [i for i, line in enumerate(lines) if line.strip() == HELPER_END]
    if len(start_hits) != 1 or len(end_hits) != 1:
        raise RuntimeError(
            f"Expected one v0.6 helper block; found starts={len(start_hits)} ends={len(end_hits)}"
        )

    start = start_hits[0]
    end = end_hits[0]
    if end < start:
        raise RuntimeError("v0.6 helper block end appears before start")

    helper_block = lines[start : end + 1]
    del lines[start : end + 1]

    call_hits = [i for i, line in enumerate(lines) if FIRST_PHASE_A_HELPER_CALL in line]
    if len(call_hits) != 1:
        raise RuntimeError(f"Expected one first Phase-A helper call; found {len(call_hits)}")

    insert_at = call_hits[0]
    lines[insert_at:insert_at] = helper_block + [""]
    rendered = "\n".join(lines)
    if source.endswith("\n"):
        rendered += "\n"
    return rendered


def render_v06_parity_source() -> str:
    original_assignment = base._assignment_index
    original_atr = base._extract_atr_name
    base._assignment_index = _assignment_index_fixed
    base._extract_atr_name = _extract_primary_atr_name_fixed
    try:
        rendered = base.render_v06_parity_source()
        return _move_v06_helpers_before_first_use(rendered)
    finally:
        base._assignment_index = original_assignment
        base._extract_atr_name = original_atr


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate fixed Issue #57 v0.6 Pine parity harness")
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rendered = render_v06_parity_source()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
