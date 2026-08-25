"""Contracts for Issue #66 Phase B-5 Stage-3/Stage-6 raw repair."""
import unittest

import diagnose_issue66_phase_b5_stage36_raw as b5diag
from generate_issue66_phase_b5_stage36_raw_core import (
    OLD_REACC_RAW,
    OLD_REDIST_RAW,
    render_phase_b5_source,
)


class Issue66PhaseB5Stage36RawTests(unittest.TestCase):
    def test_generator_changes_only_registered_stage36_raw_component(self):
        source = render_phase_b5_source()
        self.assertNotIn(OLD_REACC_RAW, source)
        self.assertNotIn(OLD_REDIST_RAW, source)
        self.assertIn("def issue66_non_opposite_heat(", source)
        self.assertIn("issue66_non_opposite_heat(panic_heat_dn)", source)
        self.assertIn("issue66_non_opposite_heat(heat_up)", source)
        # Rebound failure is retained for its existing downstream semantics.
        self.assertIn("rebound_failure = weighted(", source)
        self.assertIn("rebound_failure_gate = gate(rebound_failure, 40.0, 80.0)", source)
        # Other raw-stage formulas remain untouched.
        self.assertIn("acc_raw0 = weighted(bear_maturity_trace, 0.20, range_score, 0.20", source)
        self.assertIn("markup_base_raw = weighted(breakout_score, 0.20", source)
        self.assertIn("dist_raw0 = weighted(bull_maturity_trace, 0.20, range_score, 0.20", source)
        self.assertIn("markdown_base_raw = weighted(explicit_breakdown_score, 0.20", source)

    def test_b5_passes_preregistered_stage36_raw_gate(self):
        report = b5diag.build_report()
        self.assertTrue(report["primary_gate_pass"])
        self.assertTrue(report["inherited_b2_b3_metrics_preserved"])
        parent = report["parent_b3"]["aggregate"]
        variant = report["variant_b5"]["aggregate"]
        for key in b5diag.RAW_KEYS:
            self.assertLess(variant[key], parent[key])
        self.assertGreaterEqual(variant["range_up_to_inverse_down_jaccard"], 0.999999)
        self.assertGreaterEqual(variant["range_down_to_inverse_up_jaccard"], 0.999999)
        self.assertGreaterEqual(variant["ma_up_to_inverse_down_jaccard"], 0.999999)
        self.assertGreaterEqual(variant["ma_down_to_inverse_up_jaccard"], 0.999999)
        self.assertNotIn("pnl", report)
        self.assertNotIn("lifecycle", report)


if __name__ == "__main__":
    unittest.main()
