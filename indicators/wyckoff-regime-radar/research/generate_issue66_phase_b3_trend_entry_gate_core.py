#!/usr/bin/env python3
"""Issue #66 Phase B-3: derive a direction-neutral Stage-2/Stage-5 fresh-entry gate.

Parent is the accepted B-2 core. This generator changes only the fresh trend-entry
gate feeding Markup/Markdown. Raw stages, break evidence, extension/continuation,
other stage gates, persistence, and strategy concepts remain untouched.
"""
from __future__ import annotations

import argparse
import sys
import types
from pathlib import Path

from generate_issue66_phase_b2_break_evidence_core import render_phase_b2_source

HERE = Path(__file__).resolve().parent

OLD_NON_END_GATE = "    non_end_up_gate = gate(non_end_risk_up, 35.0, 80.0)"
NEW_NON_END_GATE = '''    non_end_up_gate = gate(non_end_risk_up, 35.0, 80.0)
    non_end_dn_gate = gate(100.0 - end_risk_dn, 35.0, 80.0)'''

OLD_TREND_ENTRY_GATES = '''    breakout_markup_gate = breakout_gate * structure_strong_gate * non_end_up_gate
    markup_extension_gate = uptrend_gate * structure_strong_gate * non_range_gate * gate(heat_up, 45.0, 80.0) * non_panic_gate * markup_extension_support
    markup_cont_gate = range_cont_up_gate * ma_bull_spread_gate * markup_cont_support * structure_strong_gate * gate(100.0 - np.maximum(upside_exhaustion, resistance_holding), 20.0, 70.0)
    breakdown_markdown_gate = explicit_breakdown_gate * gate(panic_heat_dn, 40.0, 80.0) * structure_weak_gate
    markdown_extension_gate = downtrend_gate * structure_weak_gate * non_range_gate * gate(panic_heat_dn, 45.0, 80.0) * non_heat_gate * markdown_extension_support
    markdown_cont_gate = range_cont_dn_gate * ma_bear_spread_gate * markdown_cont_support * structure_weak_gate * gate(100.0 - np.maximum(downside_exhaustion, support_holding), 20.0, 70.0)'''

NEW_TREND_ENTRY_GATES = '''    # Issue #66 B-3: one direction-neutral fresh trend-entry gate.
    def issue66_trend_entry_gate(break_gate, structure_gate, non_end_gate):
        return break_gate * structure_gate * non_end_gate

    breakout_markup_gate = issue66_trend_entry_gate(breakout_gate, structure_strong_gate, non_end_up_gate)
    markup_extension_gate = uptrend_gate * structure_strong_gate * non_range_gate * gate(heat_up, 45.0, 80.0) * non_panic_gate * markup_extension_support
    markup_cont_gate = range_cont_up_gate * ma_bull_spread_gate * markup_cont_support * structure_strong_gate * gate(100.0 - np.maximum(upside_exhaustion, resistance_holding), 20.0, 70.0)
    breakdown_markdown_gate = issue66_trend_entry_gate(explicit_breakdown_gate, structure_weak_gate, non_end_dn_gate)
    markdown_extension_gate = downtrend_gate * structure_weak_gate * non_range_gate * gate(panic_heat_dn, 45.0, 80.0) * non_heat_gate * markdown_extension_support
    markdown_cont_gate = range_cont_dn_gate * ma_bear_spread_gate * markdown_cont_support * structure_weak_gate * gate(100.0 - np.maximum(downside_exhaustion, support_holding), 20.0, 70.0)'''

DIAGNOSTIC_ANCHOR = '        "breakout_markup_gate": breakout_markup_gate,\n'
DIAGNOSTIC_INSERT = (
    '        "issue66_b3_non_end_up_gate": non_end_up_gate,\n'
    '        "issue66_b3_non_end_dn_gate": non_end_dn_gate,\n'
    '        "issue66_b3_markup_entry_gate": breakout_markup_gate,\n'
    '        "issue66_b3_markdown_entry_gate": breakdown_markdown_gate,\n'
)


def render_phase_b3_source() -> str:
    source = render_phase_b2_source()
    for old, new, label in (
        (OLD_NON_END_GATE, NEW_NON_END_GATE, "non-end gate anchor"),
        (OLD_TREND_ENTRY_GATES, NEW_TREND_ENTRY_GATES, "trend-entry gate block"),
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
        "# ISSUE #66 PHASE B-3 — DIRECTION-NEUTRAL TREND-ENTRY GATE\n"
        "# Parent: Issue #66 Phase B-2 break-evidence core.\n"
        "# Delta only: Stage-2/Stage-5 fresh-entry gates share break * structure * non-end.\n"
        "# Raw stages, break evidence, extension/continuation, other gates, persistence, and strategy are unchanged.\n\n"
        + source
    )


def load_phase_b3_namespace() -> dict[str, object]:
    module_name = "wyckoff_issue66_phase_b3_generated"
    module = types.ModuleType(module_name)
    module.__file__ = str(HERE / "generated" / "wyckoff-issue66-phase-b3-trend-entry-gate-core.py")
    module.__package__ = None
    sys.modules[module_name] = module
    exec(compile(render_phase_b3_source(), module.__file__, "exec"), module.__dict__)
    return module.__dict__


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate Issue #66 Phase B-3 trend-entry gate core")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_phase_b3_source(), encoding="utf-8")


if __name__ == "__main__":
    main()
