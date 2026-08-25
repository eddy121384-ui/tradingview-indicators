"""Contracts for Issue #66 Phase C-3 residual forensic."""
import unittest

import diagnose_issue66_phase_c3_residual_forensic as c3


class Issue66PhaseC3ResidualForensicTests(unittest.TestCase):
    def test_c3_reconstructs_known_c2_residual_without_formula_change(self):
        report = c3.build_report()
        self.assertTrue(report["c2_exact_persistence_replay"])
        self.assertEqual(report["mismatch_bars"]["strong_stage"], 44)
        self.assertEqual(report["mismatch_bars"]["formal"], 18)
        self.assertEqual(
            report["strong_stage_mismatch_attribution"]["unexplained"]["strong_stage_mismatch_overlap"],
            0,
        )
        pred = report["stage14_conflict_predicate_forensic"]
        self.assertEqual(pred["residual_stage14_conflict_mismatch_bars"], 28)
        self.assertGreaterEqual(pred["holding_predicate_mismatch_bars"], 0)
        self.assertGreaterEqual(pred["exhaustion_predicate_mismatch_bars"], 0)
        self.assertGreaterEqual(pred["inferred_continuation_override_only_bars"], 0)
        self.assertNotIn("pnl", report)
        self.assertNotIn("strategy", report)


if __name__ == "__main__":
    unittest.main()
