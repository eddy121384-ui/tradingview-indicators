#!/usr/bin/env python3

from __future__ import annotations

import unittest

from generate_issue57_phase_a_report import build_report, render_markdown


class Issue57PhaseAReportTests(unittest.TestCase):
    def test_report_stays_inside_robustness_boundary(self) -> None:
        report = build_report()
        self.assertEqual(report["issue"], 57)
        self.assertEqual(report["phase"], "A")
        self.assertFalse(report["scope"]["pnl_evaluated"])
        self.assertFalse(report["scope"]["final_oos_evaluated"])
        self.assertTrue(report["scope"]["old_final_oos_is_burned"])
        self.assertFalse(report["preservation"]["v05_pine_modified"])
        self.assertEqual(report["design"]["soft_boundary_width_atr"], 0.25)

    def test_report_contains_both_boundary_families_and_residual_cases(self) -> None:
        report = build_report()
        self.assertEqual(report["boundary_50bar"]["summary"]["case_count"], 8)
        self.assertEqual(report["breakout_20bar"]["summary"]["case_count"], 8)
        self.assertIn("worst_v06_case", report["boundary_50bar"])
        self.assertIn("worst_toggled_case", report["breakout_20bar"])

    def test_markdown_explicitly_disclaims_predictive_or_pnl_validation(self) -> None:
        markdown = render_markdown(build_report())
        self.assertIn("does **not** evaluate PnL", markdown)
        self.assertIn("Frozen v0.5.2.1 Pine source: unchanged", markdown)
        self.assertIn("20-bar breakout / breakdown counterfactual", markdown)
        self.assertIn("Do not infer trading improvement", markdown)


if __name__ == "__main__":
    unittest.main()
