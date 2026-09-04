from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

import diagnose_issue68_phase_b36_strong_blockage as b36
import generate_issue68_phase_b36_strong_blockage_audit_pine as pine


class TestIssue68B36StrongBlockage(unittest.TestCase):
    def test_blocker_taxonomy_is_exhaustive(self):
        cfg = SimpleNamespace(dominant_min=45.0, top_gap_min=10.0, evidence_min=35.0)
        model = pd.DataFrame({
            "top_id": [2, 2, 5, 3, 6, 1],
            "top_value": [40.0, 60.0, 60.0, 60.0, 60.0, 60.0],
            "top_gap": [20.0, 5.0, 20.0, 20.0, 20.0, 20.0],
            "evidence_strength": [60.0, 60.0, 20.0, 60.0, 60.0, 60.0],
            "candidate_conflict": [False, False, False, True, False, False],
            "strong_candidate": [False, False, False, False, False, False],
        })
        m = b36.blocker_masks(model, cfg)
        self.assertTrue(m["dominance"][0])
        self.assertTrue(m["gap"][1])
        self.assertTrue(m["evidence"][2])
        self.assertTrue(m["conflict"][3])
        self.assertTrue(m["no_sharp"][4])
        self.assertFalse(m["blocked"][5])
        self.assertFalse(np.any(m["unexplained"]))

    def test_generated_pine_is_diagnostic_only(self):
        text = pine.generate(Path(pine.HERE / pine.SOURCE_RELATIVE))
        for token in ("DOM GAP gate band", "EVIDENCE gate band", "CONFLICT FREE gate band", "CORE direction memory band"):
            self.assertIn(token, text)
        self.assertNotIn("strategy.", text)
        self.assertIn('volumeMode = "Off"', text)
        self.assertIn('mtfMode = "Off"', text)
        self.assertIn('divMode = "Off"', text)


if __name__ == "__main__":
    unittest.main()
