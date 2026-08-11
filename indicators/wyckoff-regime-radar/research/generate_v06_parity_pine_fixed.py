#!/usr/bin/env python3
"""Compatibility-fixed driver for the Issue #57 v0.6 Pine generator.

The original generator made two overly-broad source assumptions: it treated
Pine equality checks (`==`) as assignments, and it assumed there was only one
`ta.atr()` call in the frozen script. This driver patches only those source-
location helpers, then delegates all Phase A-D transformations to the audited
base generator.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import generate_v06_parity_pine as base


EXPECTED_SOURCE_BLOB_SHA = base.EXPECTED_SOURCE_BLOB_SHA
SOURCE = base.SOURCE
git_blob_sha = base.git_blob_sha


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


def render_v06_parity_source() -> str:
    original_assignment = base._assignment_index
    original_atr = base._extract_atr_name
    base._assignment_index = _assignment_index_fixed
    base._extract_atr_name = _extract_primary_atr_name_fixed
    try:
        return base.render_v06_parity_source()
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
