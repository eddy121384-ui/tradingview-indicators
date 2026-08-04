#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PROFILE_PATH = ROOT / "models" / "spy-1d-k6-visual-v0.1.json"
PINE_PATH = ROOT / "pine" / "hidden-regime-map-spy-k6-visual.pine"
SPEC_PATH = ROOT / "spec" / "hidden-regime-map-v0.3-k6-visual-prototype.md"


class K6VisualAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        cls.pine = PINE_PATH.read_text(encoding="utf-8")
        cls.spec = SPEC_PATH.read_text(encoding="utf-8")

    def test_profile_dimensions_and_probability_contract(self) -> None:
        profile = self.profile
        self.assertEqual(profile["profile_id"], "spy-1d-k6-visual-v0.1")
        self.assertEqual(profile["state_count"], 6)
        self.assertEqual(len(profile["feature_names"]), 5)
        self.assertEqual(len(profile["scaler"]["mean"]), 5)
        self.assertEqual(len(profile["scaler"]["scale"]), 5)
        self.assertEqual(len(profile["hmm"]["start_probability"]), 6)
        self.assertAlmostEqual(sum(profile["hmm"]["start_probability"]), 1.0)
        transition = profile["hmm"]["transition_matrix"]
        self.assertEqual(len(transition), 6)
        self.assertTrue(all(len(row) == 6 for row in transition))
        for row in transition:
            self.assertAlmostEqual(sum(row), 1.0, places=10)
        means = profile["hmm"]["emission_means"]
        variances = profile["hmm"]["emission_variances"]
        self.assertEqual((len(means), len(means[0])), (6, 5))
        self.assertEqual((len(variances), len(variances[0])), (6, 5))
        self.assertTrue(all(value > 0.0 for row in variances for value in row))

    def test_profile_preserves_research_and_product_boundaries(self) -> None:
        profile = self.profile
        self.assertTrue(profile["provenance"]["guardrails_passed"])
        self.assertEqual(profile["provenance"]["guardrail_failures"], [])
        self.assertLess(profile["initialization_verification"]["absolute_error"], 1e-8)
        self.assertFalse(profile["decision_boundary"]["k6_uniquely_optimal_claim"])
        self.assertFalse(profile["decision_boundary"]["strategy_or_pnl_claim"])
        self.assertFalse(profile["constraints"]["repainting_allowed"])

    def test_pine_references_the_frozen_profile_and_required_ui(self) -> None:
        expected_fragments = (
            'const string PROFILE_ID = "spy-1d-k6-visual-v0.1"',
            "const int STATE_COUNT = 6",
            "barstate.isconfirmed",
            "barmerge.lookahead_off",
            "maximumPosterior - secondPosterior",
            "stateDuration",
            "Unsupported: use SPY 1D",
            "No PnL claim",
        )
        for fragment in expected_fragments:
            self.assertIn(fragment, self.pine)
        self.assertEqual(len(re.findall(r'plotshape\(showTransitions', self.pine)), 6)
        self.assertEqual(len(re.findall(r'"Posterior R[1-6]"', self.pine)), 6)

    def test_spec_freezes_confidence_thresholds_before_code(self) -> None:
        for fragment in ("below 55%", "55% to below 75%", "75% or above"):
            self.assertIn(fragment, self.spec)
        self.assertIn("No smoothing or hysteresis", self.spec)
        self.assertIn("feed mismatch", self.spec)


if __name__ == "__main__":
    unittest.main()
