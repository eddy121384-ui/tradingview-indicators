"""Contracts for Issue #66 Phase B-7 Stage-1/Stage-4 gate repair."""
import unittest

import diagnose_issue66_phase_b7_stage14_gate as b7diag
from generate_issue66_phase_b7_stage14_gate_core import (
    OLD_BACKGROUND_GATES,
    OLD_DIST_GATE,
    render_phase_b7_source,
)


class Issue66PhaseB7Stage14GateTests(unittest.TestCase):
    def test_generator_changes_only_registered_stage14_gate_factor(self):
        source = render_phase_b7_source()
        self.assertNotIn(OLD_BACKGROUND_GATES, source)
        self.assertNotIn(OLD_DIST_GATE, source)
        self.assertIn("def issue66_background_maturity_gate(", source)
        self.assertIn("bear_background_acc_gate = issue66_background_maturity_gate", source)
        self.assertIn("bull_background_dist_gate = issue66_background_maturity_gate", source)
        self.assertIn("dist_gate = range_gate * bull_background_dist_gate", source)
        # Mature bull gate is deliberately retained for diagnostic compatibility.
        self.assertIn("mature_bull_gate = gate(bull_maturity_trace, 60.0, 85.0)", source)
        # Previously repaired raw primitives remain present.
        self.assertIn("issue66_quiet_range_context = low_vol_score", source)
        self.assertIn("issue66_non_opposite_heat(heat_up)", source)

    def test_b7_passes_preregistered_stage14_gate(self):
        report = b7diag.build_report()
        self.assertTrue(report["primary_gate_pass"])
        self.assertTrue(report["inherited_b2_b3_b5_b6_metrics_preserved"])
        parent = report["parent_b6"]["aggregate"]
        variant = report["variant_b7"]["aggregate"]
        for key in b7diag.GATE_KEYS:
            self.assertLess(variant[key], parent[key])
        self.assertGreaterEqual(variant["range_up_to_inverse_down_jaccard"], 0.999999)
        self.assertGreaterEqual(variant["range_down_to_inverse_up_jaccard"], 0.999999)
        self.assertGreaterEqual(variant["ma_up_to_inverse_down_jaccard"], 0.999999)
        self.assertGreaterEqual(variant["ma_down_to_inverse_up_jaccard"], 0.999999)
        self.assertNotIn("pnl", report)
        self.assertNotIn("lifecycle", report)


if __name__ == "__main__":
    unittest.main()
