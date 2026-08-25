"""Contracts for Issue #66 Phase B-2 break-evidence experiment."""
import unittest

import diagnose_issue66_phase_b2_break_evidence as b2diag
from generate_issue66_phase_b2_break_evidence_core import (
    OLD_BREAK_EVIDENCE,
    OLD_BREAK_GATES,
    render_phase_b2_source,
)


class Issue66PhaseB2BreakEvidenceTests(unittest.TestCase):
    def test_generator_replaces_only_registered_break_family(self):
        source = render_phase_b2_source()
        self.assertNotIn(OLD_BREAK_EVIDENCE, source)
        self.assertNotIn(OLD_BREAK_GATES, source)
        self.assertIn("def issue66_break_evidence(", source)
        self.assertIn("breakout_gate = issue66_breakout_gate", source)
        self.assertIn("explicit_breakdown_gate = issue66_breakdown_gate", source)
        # Known downstream Stage-2 / Stage-5 non-isomorphism must remain for a later phase.
        self.assertIn(
            "breakout_markup_gate = breakout_gate * structure_strong_gate * non_end_up_gate",
            source,
        )
        self.assertIn(
            "breakdown_markdown_gate = explicit_breakdown_gate * gate(panic_heat_dn, 40.0, 80.0) * structure_weak_gate",
            source,
        )

    def test_b2_passes_preregistered_break_evidence_gate(self):
        report = b2diag.build_report()
        self.assertTrue(report["primary_gate_pass"])
        parent = report["parent_b1"]["aggregate"]
        variant = report["variant_b2"]["aggregate"]
        for key in b2diag.KEYS:
            self.assertLess(variant[key], parent[key])
        self.assertGreaterEqual(variant["ma_up_to_inverse_down_jaccard"], 0.999999)
        self.assertGreaterEqual(variant["ma_down_to_inverse_up_jaccard"], 0.999999)
        self.assertGreaterEqual(variant["range_up_to_inverse_down_jaccard"], 0.999999)
        self.assertGreaterEqual(variant["range_down_to_inverse_up_jaccard"], 0.999999)
        self.assertNotIn("pnl", report)
        self.assertNotIn("lifecycle", report)


if __name__ == "__main__":
    unittest.main()
