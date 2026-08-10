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

        # Deliberately print the downstream comparison instead of asserting that
        # Phase A is already sufficient.  Other frozen hard gates may still own
        # the remaining discontinuity; that finding determines the next slice.
        print("V06_BOUNDARY_SWEEP=" + json.dumps(report["summary"], sort_keys=True))


if __name__ == "__main__":
    unittest.main()
