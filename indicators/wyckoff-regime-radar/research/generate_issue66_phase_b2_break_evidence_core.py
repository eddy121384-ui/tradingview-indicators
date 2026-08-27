#!/usr/bin/env python3
"""Issue #66 Phase B-2: derive direction-neutral break evidence from B-1.

The parent is the Phase B-1 reciprocal-safe representation core. This generator
changes only breakout / breakdown evidence and its directly-derived gate. Stage
formulas, continuation/extension logic, persistence, and strategy concepts are
untouched.
"""

from __future__ import annotations

import argparse
import sys
import types
from pathlib import Path

from generate_issue66_phase_b1_representation_core import render_phase_b1_source


HERE = Path(__file__).resolve().parent

OLD_BREAK_EVIDENCE = '''    breakout_range_evidence = np.nan_to_num(recent_range_break_up_strength, nan=0.0) * 0.70
    breakout_ma_evidence = np.where(recent_ma_cross_up, 70.0, np.where(close > ma, 35.0, 0.0))
    breakout_score = np.where(
        breakout_mode_up,
        100.0,
        np.maximum(breakout_range_evidence, breakout_ma_evidence),
    )
    breakdown_range_evidence = np.nan_to_num(recent_range_break_dn_strength, nan=0.0) * 0.85
    breakdown_ma_evidence = np.where(
        recent_ma_cross_dn & (panic_heat_dn >= cfg.orange_level) & (structure_weak >= 50.0),
        55.0,
        0.0,
    )
    explicit_breakdown_score = np.where(
        breakdown_mode_dn,
        100.0,
        np.maximum(breakdown_range_evidence, breakdown_ma_evidence),
    )'''

NEW_BREAK_EVIDENCE = '''    # Issue #66 B-2: one direction-neutral break-evidence primitive.
    # The existing 0-100 range-break strength is used directly. MA evidence uses
    # the inherited generic tiers (recent cross=70, directional MA side=35).
    def issue66_break_evidence(recent_range_strength, recent_ma_cross, directional_side, mode):
        range_component = clamp(np.nan_to_num(recent_range_strength, nan=0.0), 0.0, 100.0)
        ma_component = np.where(recent_ma_cross, 70.0, np.where(directional_side, 35.0, 0.0))
        score = np.where(mode, 100.0, np.maximum(range_component, ma_component))
        gate_value = clamp(score / 100.0, 0.0, 1.0)
        return range_component, ma_component, score, gate_value

    breakout_range_evidence, breakout_ma_evidence, breakout_score, issue66_breakout_gate = issue66_break_evidence(
        recent_range_break_up_strength,
        recent_ma_cross_up,
        log_price > ma_log,
        breakout_mode_up,
    )
    breakdown_range_evidence, breakdown_ma_evidence, explicit_breakdown_score, issue66_breakdown_gate = issue66_break_evidence(
        recent_range_break_dn_strength,
        recent_ma_cross_dn,
        log_price < ma_log,
        breakdown_mode_dn,
    )'''

OLD_BREAK_GATES = '''    breakout_recent_range_gate = np.nan_to_num(recent_range_break_up_strength, nan=0.0) / 100.0 * 0.85
    breakout_ma_gate = np.where(recent_ma_cross_up, 0.85, gate(breakout_ma_evidence, 30.0, 70.0))
    breakout_recent_gate = np.maximum(breakout_recent_range_gate, breakout_ma_gate)
    breakout_gate = np.where(breakout_mode_up, 1.0, breakout_recent_gate)
    explicit_recent_breakdown_gate = np.nan_to_num(recent_range_break_dn_strength, nan=0.0) / 100.0 * 0.90
    explicit_breakdown_ma_gate = gate(breakdown_ma_evidence, 50.0, 85.0)
    explicit_breakdown_gate = np.where(
        breakdown_mode_dn,
        1.0,
        np.maximum(explicit_recent_breakdown_gate, explicit_breakdown_ma_gate),
    )'''

NEW_BREAK_GATES = '''    # Diagnostic component gates are retained as mirrored decompositions of the
    # shared primitive. The classifier-facing gates are exactly score / 100.
    breakout_recent_range_gate = clamp(breakout_range_evidence / 100.0, 0.0, 1.0)
    breakout_ma_gate = clamp(breakout_ma_evidence / 100.0, 0.0, 1.0)
    breakout_recent_gate = np.maximum(breakout_recent_range_gate, breakout_ma_gate)
    breakout_gate = issue66_breakout_gate
    explicit_recent_breakdown_gate = clamp(breakdown_range_evidence / 100.0, 0.0, 1.0)
    explicit_breakdown_ma_gate = clamp(breakdown_ma_evidence / 100.0, 0.0, 1.0)
    explicit_breakdown_gate = issue66_breakdown_gate'''

DIAGNOSTIC_ANCHOR = '        "breakout_score": breakout_score,\n'
DIAGNOSTIC_INSERT = (
    '        "issue66_b2_breakout_range_component": breakout_range_evidence,\n'
    '        "issue66_b2_breakdown_range_component": breakdown_range_evidence,\n'
    '        "issue66_b2_breakout_ma_component": breakout_ma_evidence,\n'
    '        "issue66_b2_breakdown_ma_component": breakdown_ma_evidence,\n'
    '        "issue66_b2_breakout_gate": breakout_gate,\n'
    '        "issue66_b2_breakdown_gate": explicit_breakdown_gate,\n'
)


def render_phase_b2_source() -> str:
    source = render_phase_b1_source()
    for old, new, label in (
        (OLD_BREAK_EVIDENCE, NEW_BREAK_EVIDENCE, "break-evidence block"),
        (OLD_BREAK_GATES, NEW_BREAK_GATES, "break-gate block"),
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
        "# ISSUE #66 PHASE B-2 — DIRECTION-NEUTRAL BREAK EVIDENCE\n"
        "# Parent: Issue #66 Phase B-1 reciprocal-safe representation core.\n"
        "# Delta only: breakout/breakdown evidence and directly-derived gate share one primitive.\n"
        "# Stage formulas/gates, continuation/extension, persistence, and strategy logic are unchanged.\n\n"
        + source
    )


def load_phase_b2_namespace() -> dict[str, object]:
    module_name = "wyckoff_issue66_phase_b2_generated"
    module = types.ModuleType(module_name)
    module.__file__ = str(HERE / "generated" / "wyckoff-issue66-phase-b2-break-evidence-core.py")
    module.__package__ = None
    sys.modules[module_name] = module
    exec(compile(render_phase_b2_source(), module.__file__, "exec"), module.__dict__)
    return module.__dict__


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Issue #66 Phase B-2 break-evidence core")
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_phase_b2_source(), encoding="utf-8")


if __name__ == "__main__":
    main()
