"""Contracts for Issue #66 Phase B-3 trend-entry gate experiment."""
import unittest

import diagnose_issue66_phase_b3_trend_entry_gate as b3diag
from generate_issue66_phase_b3_trend_entry_gate_core import (
    OLD_NON_END_GATE,
    OLD_TREND_ENTRY_GATES,
    render_phase_b3_source,
)


class Issue66PhaseB3TrendEntryGateTests(unittest.TestCase):
    def test_generator_replaces_only_registered_trend_entry_family(self):
        source = render_phase_b3_source()
        self.assertNotIn(OLD_TREND_ENTRY_GATES, source)
        self.assertNotIn(OLD_NON_END_GATE + "\n    non_range_gate", source)
        self.assertIn("def issue66_trend_entry_gate(", source)
        self.assertIn("non_end_dn_gate = gate(100.0 - end_risk_dn, 35.0, 80.0)", source)
        self.assertIn(
            "breakout_markup_gate = issue66_trend_entry_gate(breakout_gate, structure_strong_gate, non_end_up_gate)",
            source,
        )
        self.assertIn(
            "breakdown_markdown_gate = issue66_trend_entry_gate(explicit_breakdown_gate, structure_weak_gate, non_end_dn_gate)",
            source,
        )
        # B-2 break evidence must remain the accepted parent.
        self.assertIn("def issue66_break_evidence(", source)
        self.assertIn("breakout_gate = issue66_breakout_gate", source)
        self.assertIn("explicit_breakdown_gate = issue66_breakdown_gate", source)
        # Extension / continuation remain untouched in B-3.
        self.assertIn(
            "markup_extension_gate = uptrend_gate * structure_strong_gate * non_range_gate * gate(heat_up, 45.0, 80.0) * non_panic_gate * markup_extension_support",
            source,
        )
        self.assertIn(
            "markdown_extension_gate = downtrend_gate * structure_weak_gate * non_range_gate * gate(panic_heat_dn, 45.0, 80.0) * non_heat_gate * markdown_extension_support",
            source,
        )

    def test_b3_passes_preregistered_trend_entry_gate(self):
        report = b3diag.build_report()
        self.assertTrue(report["primary_gate_pass"])
        self.assertTrue(report["b2_break_metrics_preserved"])
        parent = report["parent_b2"]["aggregate"]
        variant = report["variant_b3"]["aggregate"]
        for key in b3diag.ENTRY_KEYS:
            self.assertLess(variant[key], parent[key])
        self.assertGreaterEqual(variant["ma_up_to_inverse_down_jaccard"], 0.999999)
        self.assertGreaterEqual(variant["ma_down_to_inverse_up_jaccard"], 0.999999)
        self.assertGreaterEqual(variant["range_up_to_inverse_down_jaccard"], 0.999999)
        self.assertGreaterEqual(variant["range_down_to_inverse_up_jaccard"], 0.999999)
        self.assertNotIn("pnl", report)
        self.assertNotIn("lifecycle", report)


if __name__ == "__main__":
    unittest.main()
