#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("generate_rates_k6_pine.py")
spec = importlib.util.spec_from_file_location("generate_rates_k6_pine", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class GenerateRatesK6PineTests(unittest.TestCase):
    def profile(self):
        return {
            "profile_id": "test-rates-k6",
            "feature_names": ["a", "b", "c", "d", "e"],
            "requested_symbols": {
                "DGS2": "FRED:DGS2",
                "DGS5": "FRED:DGS5",
                "DGS10": "FRED:DGS10",
                "DGS30": "FRED:DGS30",
            },
            "provenance": {"feature_last_date": "2026-07-30"},
            "scaler": {"mean": [0, 0, 0, 0, 0], "scale": [1, 1, 1, 1, 1]},
            "instability_diagnostics": {
                "state_concentration_window_bars": 126,
                "feature_drift_threshold": 3.0,
                "state_concentration_threshold": 0.9,
            },
            "hmm": {
                "state_count": 6,
                "start_probability": [1 / 6] * 6,
                "transition_matrix": [[1 / 6] * 6 for _ in range(6)],
                "emission_means": [[0.0] * 5 for _ in range(6)],
                "emission_variances": [[1.0] * 5 for _ in range(6)],
            },
        }

    def test_generated_script_contains_rates_contract(self):
        script = module.generate(self.profile())
        self.assertIn('indicator("Hidden Regime Map — U.S. Rates K=6 Visual"', script)
        self.assertIn('input.symbol("FRED:DGS2"', script)
        self.assertIn('request.security(symbol30Y, "D"', script)
        self.assertIn('"HRM Rates Posterior R6"', script)
        self.assertIn("Historical colors are retrospective", script)
        self.assertIn("CONCENTRATION_WINDOW = 126", script)

    def test_wrong_state_count_is_rejected(self):
        profile = self.profile()
        profile["hmm"]["state_count"] = 5
        with self.assertRaisesRegex(ValueError, "exactly six states"):
            module.generate(profile)


if __name__ == "__main__":
    unittest.main()
