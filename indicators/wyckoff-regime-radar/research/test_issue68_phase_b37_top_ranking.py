#!/usr/bin/env python3
from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np
import pandas as pd

import diagnose_issue68_phase_b37_top_ranking as b37
import generate_issue68_phase_b37_top_ranking_audit_pine as pine


class TestIssue68B37TopRanking(unittest.TestCase):
    def test_raw_vs_gate_partition_is_exhaustive(self):
        # Four synthetic bars. Bull target = Stage2/3.
        # bar0: target loses raw; bar1: target wins raw but loses after gates;
        # bar2: target wins and is TOP; bar3: target loses raw to opposite trend.
        model = pd.DataFrame({
            "acc_raw": [70, 20, 10, 10],
            "markup_raw": [50, 80, 80, 20],
            "reacc_raw": [40, 70, 70, 10],
            "dist_raw": [30, 30, 20, 20],
            "markdown_raw": [20, 20, 20, 90],
            "redist_raw": [10, 10, 10, 80],
            "acc_gate": [1, 1, 1, 1],
            "markup_gate": [1, 0.20, 1, 1],
            "reacc_gate": [1, 0.20, 1, 1],
            "dist_gate": [1, 1, 1, 1],
            "markdown_gate": [1, 1, 1, 1],
            "redist_gate": [1, 1, 1, 1],
            "top_id": [1, 1, 2, 5],
        })
        out = b37.direction_audit(model, 1, warmup=0)
        self.assertEqual(out["target_top_loss_bars"], 3)
        self.assertEqual(out["raw_layer_loss"], 2)
        self.assertEqual(out["gate_layer_flip"], 1)
        self.assertEqual(out["unexplained_loss"], 0)
        self.assertEqual(out["top_reproduction_agreement"], 1.0)

    def test_generated_pine_is_diagnostic_only(self):
        text = pine.generate(Path(pine.HERE / pine.SOURCE_RELATIVE))
        self.assertIn("Issue #68 B3.7 TOP formation / ranking audit only", text)
        self.assertIn("TARGET TOP band", text)
        self.assertIn("RAW ADV band", text)
        self.assertIn("OPP TREND BLOCK band", text)
        self.assertNotIn("strategy.", text)
        self.assertNotIn("issue68B34A", text)


if __name__ == "__main__":
    unittest.main()
