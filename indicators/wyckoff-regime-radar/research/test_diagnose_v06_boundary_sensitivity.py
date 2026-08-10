#!/usr/bin/env python3

from __future__ import annotations

import json
import unittest

from diagnose_v06_boundary_sensitivity import run_sweep


class V06BoundarySensitivityDiagnosticTests(unittest.TestCase):
    def test_development_only_sweep_runs_and_softens_named_primitive(self) -> None:
        report = run_sweep()
        self.assertEqual(report["summary"]["case_count"], 8)
        self.assertEqual(report["summary"]["v05_hard_primitive_jump"], 100.0)
        self.assertLess(report["summary"]["median_v06_soft_primitive_jump"], 0.1)
        for row in report["cases"]:
            self.assertLess(row["v06_soft_primitive_jump"], 0.1)
            self.assertAlmostEqual(row["epsilon_atr"], 1e-4, places=12)

        # Deliberately report, rather than assert, downstream behavior. Other
        # frozen hard gates may still own residual discontinuity; the worst case
        # determines whether Phase A must expand beyond the two noBreak scores.
        compact_cases = [
            {
                "pair": row["pair"],
                "side": row["side"],
                "date": row["date"],
                "v05_l1": row["v05_probability_l1_jump"],
                "v06_l1": row["v06_probability_l1_jump"],
                "v05_dm": row["v05_dist_markdown_jump"],
                "v06_dm": row["v06_dist_markdown_jump"],
                "v05_top": [row["v05_top_id_below"], row["v05_top_id_above"]],
                "v06_top": [row["v06_top_id_below"], row["v06_top_id_above"]],
                "v05_candidate": [row["v05_candidate_below"], row["v05_candidate_above"]],
                "v06_candidate": [row["v06_candidate_below"], row["v06_candidate_above"]],
            }
            for row in report["cases"]
        ]
        print("V06_BOUNDARY_CASES=" + json.dumps(compact_cases, sort_keys=True))
        print("V06_BOUNDARY_SWEEP=" + json.dumps(report["summary"], sort_keys=True))


if __name__ == "__main__":
    unittest.main()
