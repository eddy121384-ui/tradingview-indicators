"""Contracts for Issue #66 Phase C-2 Stage-1/Stage-4 conflict repair."""
import unittest

import diagnose_issue66_phase_c2_stage14_conflict as c2diag
from generate_issue66_phase_c2_stage14_conflict_core import (
    OLD_STAGE1_CONFLICT,
    NEW_STAGE1_CONFLICT,
    STAGE4_CANONICAL,
    STAGE2_CLAUSE,
    STAGE5_CLAUSE,
    STAGE3_CLAUSE,
    STAGE6_CLAUSE,
    render_phase_c2_source,
)


class Issue66PhaseC2Stage14ConflictTests(unittest.TestCase):
    def test_generator_changes_only_registered_stage1_conflict_clause(self):
        source = render_phase_c2_source()
        self.assertNotIn(OLD_STAGE1_CONFLICT, source)
        self.assertIn(NEW_STAGE1_CONFLICT, source)
        for snippet in (STAGE4_CANONICAL, STAGE2_CLAUSE, STAGE5_CLAUSE, STAGE3_CLAUSE, STAGE6_CLAUSE):
            self.assertEqual(source.count(snippet), 1)
        self.assertIn("upside_exhaustion >= cfg.absorb_threshold", NEW_STAGE1_CONFLICT)
        self.assertIn("~markdown_cont_override", NEW_STAGE1_CONFLICT)

    def test_c2_passes_preregistered_conflict_gate(self):
        report = c2diag.build_report()
        self.assertTrue(report["primary_gate_pass"])
        self.assertTrue(report["inherited_b7_numeric_metrics_preserved"])
        self.assertTrue(report["other_conflict_families_remain_zero"])

        parent = report["parent_b7_conflict"]
        variant = report["variant_c2_conflict"]
        self.assertGreater(
            variant["candidate_conflict_mirror_agreement"],
            parent["candidate_conflict_mirror_agreement"],
        )
        self.assertLess(
            variant["families"]["stage1_4"]["conflict_mismatch_bars"],
            parent["families"]["stage1_4"]["conflict_mismatch_bars"],
        )
        self.assertEqual(variant["families"]["stage2_5"]["conflict_mismatch_bars"], 0)
        self.assertEqual(variant["families"]["stage3_6"]["conflict_mismatch_bars"], 0)
        self.assertTrue(report["variant_c2_persistence"]["all_original_replays_exact"])
        self.assertNotIn("pnl", report)
        self.assertNotIn("strategy", report)


if __name__ == "__main__":
    unittest.main()
