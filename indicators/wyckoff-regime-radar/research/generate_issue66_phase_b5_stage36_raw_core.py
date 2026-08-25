#!/usr/bin/env python3
"""Issue #66 Phase B-5: repair Stage-3/Stage-6 raw symmetry from accepted B-3."""
from __future__ import annotations

import argparse
import sys
import types
from pathlib import Path

from generate_issue66_phase_b3_trend_entry_gate_core import render_phase_b3_source

HERE = Path(__file__).resolve().parent

OLD_REACC_RAW = "    reacc_raw0 = weighted(bull_bg, 0.20, range_score, 0.20, support_holding, 0.25, 100.0 - panic_heat_dn, 0.20, 100.0 - upside_exhaustion, 0.15)"
NEW_REACC_RAW = '''    # Issue #66 B-5: shared reciprocal Stage-3/Stage-6 counter-pressure primitive.
    def issue66_non_opposite_heat(opposite_heat):
        return 100.0 - opposite_heat

    reacc_raw0 = weighted(bull_bg, 0.20, range_score, 0.20, support_holding, 0.25, issue66_non_opposite_heat(panic_heat_dn), 0.20, 100.0 - upside_exhaustion, 0.15)'''

OLD_REDIST_RAW = "    redist_raw0 = weighted(bear_bg, 0.20, range_score, 0.20, resistance_holding, 0.25, rebound_failure, 0.20, 100.0 - downside_exhaustion, 0.15)"
NEW_REDIST_RAW = "    redist_raw0 = weighted(bear_bg, 0.20, range_score, 0.20, resistance_holding, 0.25, issue66_non_opposite_heat(heat_up), 0.20, 100.0 - downside_exhaustion, 0.15)"

DIAGNOSTIC_ANCHOR = '        "reacc_raw": reacc_raw,\n'
DIAGNOSTIC_INSERT = (
    '        "issue66_b5_reacc_non_opposite_heat": issue66_non_opposite_heat(panic_heat_dn),\n'
    '        "issue66_b5_redist_non_opposite_heat": issue66_non_opposite_heat(heat_up),\n'
)


def render_phase_b5_source() -> str:
    source = render_phase_b3_source()
    for old, new, label in (
        (OLD_REACC_RAW, NEW_REACC_RAW, "reacc raw line"),
        (OLD_REDIST_RAW, NEW_REDIST_RAW, "redist raw line"),
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
        "# ISSUE #66 PHASE B-5 — STAGE 3/6 RAW SYMMETRY REPAIR\n"
        "# Parent: accepted Issue #66 Phase B-3 core.\n"
        "# Delta only: Reacc/Redist raw fourth component shares non-opposite-heat primitive.\n"
        "# All other raw components, gates, break evidence, persistence, thresholds, and strategy are unchanged.\n\n"
        + source
    )


def load_phase_b5_namespace() -> dict[str, object]:
    module_name = "wyckoff_issue66_phase_b5_generated"
    module = types.ModuleType(module_name)
    module.__file__ = str(HERE / "generated" / "wyckoff-issue66-phase-b5-stage36-raw-core.py")
    module.__package__ = None
    sys.modules[module_name] = module
    exec(compile(render_phase_b5_source(), module.__file__, "exec"), module.__dict__)
    return module.__dict__


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate Issue #66 Phase B-5 Stage3/6 raw core")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_phase_b5_source(), encoding="utf-8")


if __name__ == "__main__":
    main()
