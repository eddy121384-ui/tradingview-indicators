"""Contracts for Issue #66 Phase C-1 candidate-conflict pre-audit."""
import unittest

import diagnose_issue66_phase_c1_candidate_conflict_preaudit as c1


class Issue66PhaseC1ConflictPreAuditTests(unittest.TestCase):
    def test_conflict_family_attribution_reconstructs_attributable_total(self):
        report = c1.build_report()
        reconstructed = sum(node["conflict_mismatch_bars"] for node in report["families"].values())
        self.assertEqual(reconstructed, report["attributable_conflict_mismatch_bars"])
        self.assertEqual(
            report["total_conflict_mismatch_bars"],
            report["attributable_conflict_mismatch_bars"] + report["conflict_mismatch_with_top_not_mirrored"],
        )
        self.assertNotIn("pnl", report)
        self.assertNotIn("strategy", report)


if __name__ == "__main__":
    unittest.main()
