#!/usr/bin/env python3
from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np
import pandas as pd

import diagnose_issue68_phase_b38_raw_feature_attribution as b38
import generate_issue68_phase_b38_raw_feature_attribution_audit_pine as pine


class TestIssue68B38RawFeatureAttribution(unittest.TestCase):
    def test_raw_winner_groups_are_exhaustive(self):
        # Bull target is Stage2/3. Four bars: target wins, S1 wins, S4 wins, S5 wins.
        model = pd.DataFrame({
            "acc_raw": [10, 90, 10, 10],
            "markup_raw": [80, 40, 40, 40],
            "reacc_raw": [70, 30, 30, 30],
            "dist_raw": [20, 20, 90, 20],
            "markdown_raw": [30, 20, 20, 90],
            "redist_raw": [20, 10, 10, 80],
        })
        out = b38.direction_raw_audit(model, 1, warmup=0)
        self.assertEqual(out["raw_adv_bars"], 1)
        self.assertEqual(out["raw_loss_bars"], 3)
        self.assertEqual(out["winner_group"]["precursor_range"], 1)
        self.assertEqual(out["winner_group"]["opposite_range"], 1)
        self.assertEqual(out["winner_group"]["opposite_trend"], 1)
        self.assertEqual(out["winner_group"]["unexplained"], 0)

    def test_stage2_stage5_component_reconstruction(self):
        frame = pd.DataFrame({
            "b38_breakout": [80.0, 20.0],
            "b38_breakdown": [20.0, 80.0],
            "b38_heat_up": [70.0, 30.0],
            "b38_panic_dn": [30.0, 70.0],
            "b38_structure_up": [100.0, 50.0],
            "b38_structure_dn": [0.0, 50.0],
            "b38_extension_up": [75.0, 25.0],
            "b38_extension_dn": [25.0, 75.0],
            "b38_continuation_up": [65.0, 35.0],
            "b38_continuation_dn": [35.0, 65.0],
            "b38_acc_trace": [60.0, 40.0],
            "b38_dist_trace": [40.0, 60.0],
        })
        w = b38.COMPONENT_WEIGHTS
        delta = (
            w["break"] * (frame["b38_breakout"] - frame["b38_breakdown"])
            + w["heat"] * (frame["b38_heat_up"] - frame["b38_panic_dn"])
            + w["structure"] * (frame["b38_structure_up"] - frame["b38_structure_dn"])
            + w["extension"] * (frame["b38_extension_up"] - frame["b38_extension_dn"])
            + w["continuation"] * (frame["b38_continuation_up"] - frame["b38_continuation_dn"])
            + w["trace"] * (frame["b38_acc_trace"] - frame["b38_dist_trace"])
        )
        # Only the difference is required by fresh_pair_components; absolute raw0 levels are arbitrary.
        frame["b38_markdown_raw0"] = 50.0
        frame["b38_markup_raw0"] = 50.0 + delta
        out = b38.fresh_pair_components(frame)
        self.assertLessEqual(out["max_abs_reconstruction_error"], 1e-12)
        self.assertEqual(out["markup_raw0_below_markdown_raw0_bars"], 1)

    def test_generated_pine_is_diagnostic_only(self):
        text = pine.generate(Path(pine.HERE / pine.SOURCE_RELATIVE))
        self.assertIn("Issue #68 B3.8 raw feature attribution audit only", text)
        self.assertIn("RAW ADV band", text)
        self.assertIn("TARGET RANGE band", text)
        self.assertIn("BREAK EDGE band", text)
        self.assertIn("TRACE EDGE band", text)
        self.assertNotIn("strategy.", text)
        self.assertNotIn("issue68B34A", text)


if __name__ == "__main__":
    unittest.main()
