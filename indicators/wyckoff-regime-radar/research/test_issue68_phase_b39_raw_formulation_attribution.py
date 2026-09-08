#!/usr/bin/env python3
from __future__ import annotations

import unittest
from pathlib import Path

import pandas as pd

import diagnose_issue68_phase_b39_raw_formulation_attribution as b39
import generate_issue68_phase_b39_raw_formulation_attribution_audit_pine as pine


class TestIssue68B39RawFormulationAttribution(unittest.TestCase):
    def test_bull_exact_competitor_attribution_is_exhaustive(self):
        # Five bars: Bull target wins, then S1, S4, S5, S6 each wins exactly once.
        model = pd.DataFrame({
            "acc_raw":      [10.0, 95.0, 10.0, 10.0, 10.0],
            "markup_raw":   [90.0, 60.0, 60.0, 60.0, 60.0],
            "reacc_raw":    [80.0, 55.0, 55.0, 55.0, 55.0],
            "dist_raw":     [20.0, 20.0, 95.0, 20.0, 20.0],
            "markdown_raw": [30.0, 30.0, 30.0, 95.0, 30.0],
            "redist_raw":   [20.0, 20.0, 20.0, 20.0, 95.0],
        })
        out = b39.direction_audit(model, 1, warmup=0)
        self.assertEqual(out["raw_adv_bars"], 1)
        self.assertEqual(out["raw_loss_bars"], 4)
        counts = out["exact_raw_winner_on_loss"]["competitor_stage_counts"]
        self.assertEqual(counts["1"], 1)
        self.assertEqual(counts["4"], 1)
        self.assertEqual(counts["5"], 1)
        self.assertEqual(counts["6"], 1)
        self.assertEqual(out["exact_raw_winner_on_loss"]["target_tie_priority"], 0)
        self.assertEqual(out["exact_raw_winner_on_loss"]["unexplained"], 0)
        self.assertEqual(out["target_substage_on_loss"]["fresh"], 4)
        self.assertEqual(out["target_substage_on_loss"]["continuation"], 0)

    def test_bear_competitors_are_exact_reciprocal_stage_set(self):
        spec = b39._direction_spec(-1)
        self.assertEqual(spec["target"], [5, 6])
        self.assertEqual(spec["fresh"], 5)
        self.assertEqual(spec["continuation"], 6)
        self.assertEqual(spec["competitors"], [4, 1, 2, 3])
        for stage, mirror in b39.STAGE_MIRROR.items():
            self.assertEqual(b39.STAGE_MIRROR[mirror], stage)

    def test_target_tie_priority_is_accounted_not_unexplained(self):
        # S1 ties S2 at 80. Strict Stage1-first winner means raw_adv is false and S1 is attributed.
        model = pd.DataFrame({
            "acc_raw": [80.0],
            "markup_raw": [80.0],
            "reacc_raw": [70.0],
            "dist_raw": [10.0],
            "markdown_raw": [20.0],
            "redist_raw": [10.0],
        })
        out = b39.direction_audit(model, 1, warmup=0)
        self.assertEqual(out["raw_loss_bars"], 1)
        self.assertEqual(out["exact_raw_winner_on_loss"]["competitor_stage_counts"]["1"], 1)
        self.assertEqual(out["exact_raw_winner_on_loss"]["unexplained"], 0)

    def test_generated_pine_is_diagnostic_only(self):
        text = pine.generate(Path(pine.HERE / pine.SOURCE_RELATIVE))
        self.assertIn("Issue #68 B3.9 raw formulation attribution audit only", text)
        self.assertIn("B39 RAW ADV band", text)
        self.assertIn("B39 FRESH TARGET band", text)
        self.assertIn("B39 COMP A band", text)
        self.assertIn("B39 COMP D band", text)
        self.assertIn("B39 BREAK band", text)
        self.assertIn("B39 STRUCTURE band", text)
        self.assertNotIn("strategy.", text)
        self.assertNotIn("issue68B34A", text)


if __name__ == "__main__":
    unittest.main()
