#!/usr/bin/env python3
"""Generate Issue #68 B3.4R A-vs-C resume audit Pine.

Display-only wrapper around the frozen B3.4 A/B/C semantics. Candidate B remains
implemented and available, but is hidden by default so the resumed unresolved
human gate focuses on CORE + A + C.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import generate_issue68_phase_b34_exposure_bakeoff_audit_pine as b34
from generate_price_only_parity_pine import SOURCE_RELATIVE, replace_once

HERE = Path(__file__).resolve().parent

OLD_DECL = b34.AUDIT_DECL
NEW_DECL = 'indicator("Chase Risk Radar｜Issue #68 B3.4R A-vs-C Resume", shorttitle="ChaseRisk #68 B34R", overlay=false, precision=2)'
OLD_B_DEFAULT = 'showIssue68B34B = input.bool(true, "顯示 B｜Flat Action authorization", group=groupIssue68B34)'
NEW_B_DEFAULT = 'showIssue68B34B = input.bool(false, "顯示 B｜Flat Action authorization（已凍結，預設隱藏）", group=groupIssue68B34)'


def generate(source: Path) -> str:
    out = b34.generate(source)
    out = replace_once(out, OLD_DECL, NEW_DECL)
    out = replace_once(out, OLD_B_DEFAULT, NEW_B_DEFAULT)

    banner = """
// ============================================================================
// Issue #68 B3.4R resumed human semantic gate.
// DISPLAY ONLY: Candidate B is hidden by default; A/B/C formulas are unchanged.
// Active unresolved comparison: CORE + A vs C. No PnL. No classifier repair.
// ============================================================================
""".strip()
    marker = "groupIssue68B34 = \"Issue #68｜Exposure B3.4 Bakeoff\""
    out = replace_once(out, marker, banner + "\n\n" + marker)

    required = (
        "B3.4R resumed human semantic gate",
        "A Formal-family exposure",
        "B Flat-Action exposure",
        "C Stateful exposure",
        'showIssue68B34B = input.bool(false',
        "CORE Bias band",
    )
    for token in required:
        if token not in out:
            raise RuntimeError(f"missing B3.4R token: {token}")

    if "strategy." in out:
        raise RuntimeError("strategy token leaked into B3.4R diagnostic")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=HERE / SOURCE_RELATIVE)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    text = generate(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
