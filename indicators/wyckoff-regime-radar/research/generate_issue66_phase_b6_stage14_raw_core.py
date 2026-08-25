#!/usr/bin/env python3
"""Issue #66 Phase B-6: repair Stage-1/Stage-4 raw symmetry from accepted B-5."""
from __future__ import annotations

import argparse
import sys
import types
from pathlib import Path

from generate_issue66_phase_b5_stage36_raw_core import render_phase_b5_source

HERE = Path(__file__).resolve().parent

OLD_ACC_RAW = "    acc_raw0 = weighted(bear_maturity_trace, 0.20, range_score, 0.20, downside_exhaustion, 0.25, support_holding, 0.25, low_vol_score, 0.10)"
NEW_ACC_RAW = '''    # Issue #66 B-6: shared reciprocal Stage-1/Stage-4 quiet-range context.
    issue66_quiet_range_context = low_vol_score
    acc_raw0 = weighted(bear_maturity_trace, 0.20, range_score, 0.20, downside_exhaustion, 0.25, support_holding, 0.25, issue66_quiet_range_context, 0.10)'''

OLD_DIST_RAW = "    dist_raw0 = weighted(bull_maturity_trace, 0.20, range_score, 0.20, upside_exhaustion, 0.25, resistance_holding, 0.25, bear_pressure_rising, 0.10)"
NEW_DIST_RAW = "    dist_raw0 = weighted(bull_maturity_trace, 0.20, range_score, 0.20, upside_exhaustion, 0.25, resistance_holding, 0.25, issue66_quiet_range_context, 0.10)"

DIAGNOSTIC_ANCHOR = '        "acc_raw": acc_raw,\n'
DIAGNOSTIC_INSERT = '        "issue66_b6_quiet_range_context": issue66_quiet_range_context,\n'


def render_phase_b6_source() -> str:
    source = render_phase_b5_source()
    for old, new, label in (
        (OLD_ACC_RAW, NEW_ACC_RAW, "acc raw line"),
        (OLD_DIST_RAW, NEW_DIST_RAW, "dist raw line"),
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
        "# ISSUE #66 PHASE B-6 — STAGE 1/4 RAW SYMMETRY REPAIR\n"
        "# Parent: accepted Issue #66 Phase B-5 core.\n"
        "# Delta only: Acc/Dist raw final component shares direction-neutral quiet-range context.\n"
        "# All other raw components, gates, break evidence, persistence, thresholds, and strategy are unchanged.\n\n"
        + source
    )


def load_phase_b6_namespace() -> dict[str, object]:
    module_name = "wyckoff_issue66_phase_b6_generated"
    module = types.ModuleType(module_name)
    module.__file__ = str(HERE / "generated" / "wyckoff-issue66-phase-b6-stage14-raw-core.py")
    module.__package__ = None
    sys.modules[module_name] = module
    exec(compile(render_phase_b6_source(), module.__file__, "exec"), module.__dict__)
    return module.__dict__


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate Issue #66 Phase B-6 Stage1/4 raw core")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_phase_b6_source(), encoding="utf-8")


if __name__ == "__main__":
    main()
