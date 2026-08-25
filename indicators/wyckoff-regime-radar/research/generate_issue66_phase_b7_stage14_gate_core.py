#!/usr/bin/env python3
"""Issue #66 Phase B-7: repair Stage-1/Stage-4 gate symmetry from accepted B-6."""
from __future__ import annotations

import argparse
import sys
import types
from pathlib import Path

from generate_issue66_phase_b6_stage14_raw_core import render_phase_b6_source

HERE = Path(__file__).resolve().parent

OLD_BACKGROUND_GATES = '''    mature_bull_gate = gate(bull_maturity_trace, 60.0, 85.0)
    bear_background_acc_gate = gate(np.maximum(bear_bg, bear_maturity_trace), 35.0, 75.0)'''

NEW_BACKGROUND_GATES = '''    mature_bull_gate = gate(bull_maturity_trace, 60.0, 85.0)  # retained diagnostic compatibility

    # Issue #66 B-7: one direction-neutral background/maturity gate for Stage 1/4.
    def issue66_background_maturity_gate(background, maturity_trace):
        return gate(np.maximum(background, maturity_trace), 35.0, 75.0)

    bear_background_acc_gate = issue66_background_maturity_gate(bear_bg, bear_maturity_trace)
    bull_background_dist_gate = issue66_background_maturity_gate(bull_bg, bull_maturity_trace)'''

OLD_DIST_GATE = "    dist_gate = range_gate * mature_bull_gate * upside_exhaustion_gate * resistance_holding_gate * non_markup_cont_gate"
NEW_DIST_GATE = "    dist_gate = range_gate * bull_background_dist_gate * upside_exhaustion_gate * resistance_holding_gate * non_markup_cont_gate"

DIAGNOSTIC_ANCHOR = '        "acc_gate": acc_gate,\n'
DIAGNOSTIC_INSERT = (
    '        "issue66_b7_bear_background_acc_gate": bear_background_acc_gate,\n'
    '        "issue66_b7_bull_background_dist_gate": bull_background_dist_gate,\n'
)


def render_phase_b7_source() -> str:
    source = render_phase_b6_source()
    for old, new, label in (
        (OLD_BACKGROUND_GATES, NEW_BACKGROUND_GATES, "background gate block"),
        (OLD_DIST_GATE, NEW_DIST_GATE, "distribution gate line"),
    ):
        count = source.count(old)
        if count != 1:
            raise RuntimeError(f"Expected exactly one {label}; found {count}")
        source = source.replace(old, new, 1)

    if source.count(DIAGNOSTIC_ANCHOR) != 1:
        raise RuntimeError(
            f"Expected exactly one diagnostic anchor; found {source.count(DIAGNOSTIC_ANCHOR)}"
        )
    source = source.replace(DIAGNOSTIC_ANCHOR, DIAGNOSTIC_ANCHOR + DIAGNOSTIC_INSERT, 1)

    return (
        "# ISSUE #66 PHASE B-7 — STAGE 1/4 GATE SYMMETRY REPAIR\n"
        "# Parent: accepted Issue #66 Phase B-6 core.\n"
        "# Delta only: Stage-1/Stage-4 background/maturity gate uses one mirrored primitive.\n"
        "# Raw stages, other gates, break evidence, persistence, thresholds, and strategy are unchanged.\n\n"
        + source
    )


def load_phase_b7_namespace() -> dict[str, object]:
    module_name = "wyckoff_issue66_phase_b7_generated"
    module = types.ModuleType(module_name)
    module.__file__ = str(HERE / "generated" / "wyckoff-issue66-phase-b7-stage14-gate-core.py")
    module.__package__ = None
    sys.modules[module_name] = module
    exec(compile(render_phase_b7_source(), module.__file__, "exec"), module.__dict__)
    return module.__dict__


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate Issue #66 Phase B-7 Stage1/4 gate core")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_phase_b7_source(), encoding="utf-8")


if __name__ == "__main__":
    main()
