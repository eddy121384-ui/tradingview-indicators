#!/usr/bin/env python3
"""Issue #66 Phase C-2: make Stage-1 candidate conflict the reciprocal mirror of Stage-4.

Parent is accepted B-7. This generator changes one Stage-1 candidate-conflict
clause only. Numeric classifier layers and persistence are untouched.
"""
from __future__ import annotations

import argparse
import sys
import types
from pathlib import Path

from generate_issue66_phase_b7_stage14_gate_core import render_phase_b7_source


HERE = Path(__file__).resolve().parent

OLD_STAGE1_CONFLICT = '''    candidate_conflict |= (top_id == 1) & (resistance_holding >= cfg.absorb_threshold) & (rebound_failure_gate > 0.50) & ~markup_cont_override'''
NEW_STAGE1_CONFLICT = '''    # Issue #66 C-2: Stage 1 is the reciprocal mirror of canonical Stage 4 conflict.
    candidate_conflict |= (top_id == 1) & (resistance_holding >= cfg.absorb_threshold) & (upside_exhaustion >= cfg.absorb_threshold) & ~markdown_cont_override'''

STAGE4_CANONICAL = '''    candidate_conflict |= (top_id == 4) & (support_holding >= cfg.absorb_threshold) & (downside_exhaustion >= cfg.absorb_threshold) & ~markup_cont_override'''
STAGE2_CLAUSE = '''    candidate_conflict |= (top_id == 2) & (upside_exhaustion >= cfg.absorb_threshold) & (resistance_holding >= cfg.absorb_threshold) & ~markup_cont_override'''
STAGE5_CLAUSE = '''    candidate_conflict |= (top_id == 5) & (downside_exhaustion >= cfg.absorb_threshold) & (support_holding >= cfg.absorb_threshold) & ~markdown_cont_override'''
STAGE3_CLAUSE = '''    candidate_conflict |= (top_id == 3) & (upside_exhaustion >= cfg.absorb_threshold) & (resistance_holding >= cfg.absorb_threshold) & ~markup_cont_override'''
STAGE6_CLAUSE = '''    candidate_conflict |= (top_id == 6) & (downside_exhaustion >= cfg.absorb_threshold) & (support_holding >= cfg.absorb_threshold) & ~markdown_cont_override'''


def render_phase_c2_source() -> str:
    source = render_phase_b7_source()
    count = source.count(OLD_STAGE1_CONFLICT)
    if count != 1:
        raise RuntimeError(f"Expected exactly one Stage-1 conflict clause; found {count}")
    source = source.replace(OLD_STAGE1_CONFLICT, NEW_STAGE1_CONFLICT, 1)

    for label, snippet in (
        ("Stage-4 canonical clause", STAGE4_CANONICAL),
        ("Stage-2 clause", STAGE2_CLAUSE),
        ("Stage-5 clause", STAGE5_CLAUSE),
        ("Stage-3 clause", STAGE3_CLAUSE),
        ("Stage-6 clause", STAGE6_CLAUSE),
    ):
        if source.count(snippet) != 1:
            raise RuntimeError(f"C-2 must preserve exactly one {label}")

    return (
        "# ISSUE #66 PHASE C-2 — STAGE 1/4 CANDIDATE-CONFLICT SYMMETRY\n"
        "# Parent: accepted Issue #66 Phase B-7 core.\n"
        "# Delta only: Stage-1 conflict mirrors canonical Stage-4 exhaustion/holding/continuation pattern.\n"
        "# Numeric classifier layers, other conflict clauses, Candidate thresholds, and persistence are unchanged.\n\n"
        + source
    )


def load_phase_c2_namespace() -> dict[str, object]:
    module_name = "wyckoff_issue66_phase_c2_generated"
    module = types.ModuleType(module_name)
    module.__file__ = str(HERE / "generated" / "wyckoff-issue66-phase-c2-stage14-conflict-core.py")
    module.__package__ = None
    sys.modules[module_name] = module
    exec(compile(render_phase_c2_source(), module.__file__, "exec"), module.__dict__)
    return module.__dict__


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate Issue #66 Phase C-2 Stage1/4 conflict core")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_phase_c2_source(), encoding="utf-8")


if __name__ == "__main__":
    main()
