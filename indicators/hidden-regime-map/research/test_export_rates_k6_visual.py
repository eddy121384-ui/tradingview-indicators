#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np

MODULE_PATH = Path(__file__).with_name("export_rates_k6_visual.py")
spec = importlib.util.spec_from_file_location("export_rates_k6_visual", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class ExportRatesK6VisualTests(unittest.TestCase):
    def make_parameters(self, offset: float = 0.0):
        means = np.arange(30, dtype=float).reshape(6, 5) / 10.0 + offset
        variances = np.full((6, 5), 0.75 + offset * 0.01)
        transition = np.full((6, 6), 0.02)
        np.fill_diagonal(transition, 0.90)
        transition /= transition.sum(axis=1, keepdims=True)
        start = np.array([0.50, 0.20, 0.10, 0.10, 0.05, 0.05])
        return {
            "means": means,
            "variances": variances,
            "transition": transition,
            "start_probability": start,
        }

    def test_medoid_prefers_middle_parameter_set(self):
        sets = [
            self.make_parameters(-0.5),
            self.make_parameters(0.0),
            self.make_parameters(0.6),
        ]
        index, totals = module.medoid_index(sets)
        self.assertEqual(index, 1)
        self.assertEqual(len(totals), 3)
        self.assertLess(totals[1], totals[0])
        self.assertLess(totals[1], totals[2])

    def test_economic_state_order_is_complete_and_deterministic(self):
        means = np.zeros((6, 5), dtype=float)
        change = module.evaluate_rates_utility.FEATURE_NAMES.index("level_change_bp")
        vol = module.evaluate_rates_utility.FEATURE_NAMES.index("level_vol_20_bp")
        means[:, change] = [2.0, -3.0, 1.0, -1.0, 0.0, 3.0]
        means[:, vol] = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        order = module.economic_state_order(means)
        self.assertEqual(order, [1, 3, 4, 2, 0, 5])
        self.assertEqual(sorted(order), list(range(6)))

    def test_reordered_forward_filter_is_normalized(self):
        parameters = self.make_parameters()
        order = [5, 4, 3, 2, 1, 0]
        reordered = module.reorder_parameters(parameters, order)
        module.validate_parameters(reordered)
        matrix = np.linspace(-1.0, 1.0, 100).reshape(20, 5)
        posterior = module.forward_filter_params(matrix, reordered)
        self.assertEqual(posterior.shape, (20, 6))
        self.assertTrue(np.allclose(posterior.sum(axis=1), 1.0, atol=1e-10))
        self.assertTrue(np.isfinite(posterior).all())

    def test_invalid_transition_rows_are_rejected(self):
        parameters = self.make_parameters()
        parameters["transition"][0, 0] += 0.1
        with self.assertRaisesRegex(ValueError, "transition rows"):
            module.validate_parameters(parameters)


if __name__ == "__main__":
    unittest.main()
