"""Contracts for Issue #66 Phase B-4 raw-stage residual pre-audit."""
import unittest

import diagnose_issue66_phase_b4_raw_stage_pre_audit as b4


class Issue66PhaseB4RawStagePreAuditTests(unittest.TestCase):
    def test_b4_reconstructs_parent_raw_stage_mae_without_formula_change(self):
        report = b4.build_report()
        self.assertTrue(report["reconstruction_pass"])
        self.assertLessEqual(report["reconstruction_error"], 1e-12)
        self.assertAlmostEqual(
            report["raw_stage_vector_mae"],
            report["reconstructed_raw_stage_mae"],
            places=12,
        )
        self.assertEqual(set(report["ranking"]), set(b4.FAMILIES))
        self.assertEqual(report["dominant_raw_stage_family"], report["ranking"][0])
        shares = [report["families"][f]["stage_raw"]["absolute_error_share"] for f in b4.FAMILIES]
        self.assertAlmostEqual(sum(shares), 1.0, places=12)
        dominant_share = report["families"][report["dominant_raw_stage_family"]]["stage_raw"]["absolute_error_share"]
        self.assertEqual(dominant_share, max(shares))
        self.assertNotIn("pnl", report)
        self.assertNotIn("lifecycle", report)


if __name__ == "__main__":
    unittest.main()
