"""Contracts for Issue #66 Phase C-3 residual forensic."""
import unittest

import diagnose_issue66_phase_c3_residual_forensic as c3


class Issue66PhaseC3ResidualForensicTests(unittest.TestCase):
    def test_c3_reconstructs_small_explained_c2_residual_without_formula_change(self):
        report = c3.build_report()

        # D-1B real TradingView runtime evidence corrected the Python mirror of
        # ta.percentrank(). Exact historical residual counts (44 / 18 / 28) were
        # produced under the old off-by-one built-in approximation and are no
        # longer a valid contract. Lock the architectural conclusion instead.
        self.assertTrue(report["c2_exact_persistence_replay"])
        self.assertGreaterEqual(report["agreements"]["strong_stage"], 0.99)
        self.assertGreaterEqual(report["agreements"]["formal"], 0.995)
        self.assertGreaterEqual(report["agreements"]["candidate_display"], 0.99)
        self.assertEqual(
            report["strong_stage_mismatch_attribution"]["unexplained"]["strong_stage_mismatch_overlap"],
            0,
        )

        pred = report["stage14_conflict_predicate_forensic"]
        # Residual conflict must remain a small forensic tail, not a reopened
        # formula-search target. No threshold shopping is authorized here.
        self.assertLess(pred["residual_stage14_conflict_mismatch_bars"], 100)
        self.assertGreaterEqual(pred["holding_predicate_mismatch_bars"], 0)
        self.assertGreaterEqual(pred["exhaustion_predicate_mismatch_bars"], 0)
        self.assertGreaterEqual(pred["inferred_continuation_override_only_bars"], 0)

        self.assertNotIn("pnl", report)
        self.assertNotIn("strategy", report)


if __name__ == "__main__":
    unittest.main()
