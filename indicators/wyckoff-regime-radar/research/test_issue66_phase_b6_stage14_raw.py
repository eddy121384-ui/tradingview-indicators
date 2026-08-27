"""Contracts for Issue #66 Phase B-6 Stage-1/Stage-4 raw repair."""
import unittest

import diagnose_issue66_phase_b6_stage14_raw as b6diag
from generate_issue66_phase_b6_stage14_raw_core import (
    OLD_ACC_RAW,
    OLD_DIST_RAW,
    render_phase_b6_source,
)


class Issue66PhaseB6Stage14RawTests(unittest.TestCase):
    def test_generator_changes_only_registered_stage14_raw_component(self):
        source = render_phase_b6_source()
        self.assertNotIn(OLD_ACC_RAW, source)
        self.assertNotIn(OLD_DIST_RAW, source)
        self.assertIn("issue66_quiet_range_context = low_vol_score", source)
        self.assertIn("issue66_quiet_range_context, 0.10", source)
        # Bear pressure remains available for its existing downstream semantics.
        self.assertIn("bear_pressure_rising = weighted(", source)
        self.assertIn("gate(100.0 - bear_pressure_rising, 25.0, 75.0)", source)
        # Previously repaired raw families remain present.
        self.assertIn("issue66_non_opposite_heat(panic_heat_dn)", source)
        self.assertIn("issue66_non_opposite_heat(heat_up)", source)

    def test_b6_passes_preregistered_stage14_raw_gate(self):
        report = b6diag.build_report()
        self.assertTrue(report["primary_gate_pass"])
        self.assertTrue(report["inherited_b2_b3_b5_metrics_preserved"])
        parent = report["parent_b5"]["aggregate"]
        variant = report["variant_b6"]["aggregate"]
        for key in b6diag.RAW_KEYS:
            self.assertLess(variant[key], parent[key])
        self.assertGreaterEqual(variant["range_up_to_inverse_down_jaccard"], 0.999999)
        self.assertGreaterEqual(variant["range_down_to_inverse_up_jaccard"], 0.999999)
        self.assertGreaterEqual(variant["ma_up_to_inverse_down_jaccard"], 0.999999)
        self.assertGreaterEqual(variant["ma_down_to_inverse_up_jaccard"], 0.999999)
        self.assertNotIn("pnl", report)
        self.assertNotIn("lifecycle", report)


if __name__ == "__main__":
    unittest.main()
