#!/usr/bin/env python3

from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from diagnose_transition_formation_and_regime_decay import extract_action_episodes, normalized_entropy, opposite_structural_pressure

COLUMNS = ["prob_acc", "prob_markup", "prob_reacc", "prob_dist", "prob_markdown", "prob_redist"]


class TransitionFormationDecayTests(unittest.TestCase):
    def test_extract_action_episodes_counts_each_consecutive_family_once(self) -> None:
        direction = np.array([0, 1, 1, 1, 0, -1, -1, 1, 1, 0], dtype=float)
        got = extract_action_episodes(direction)
        self.assertEqual(
            got,
            [
                {"start": 1, "end": 3, "direction": 1.0, "duration": 3},
                {"start": 5, "end": 6, "direction": -1.0, "duration": 2},
                {"start": 7, "end": 8, "direction": 1.0, "duration": 2},
            ],
        )

    def test_normalized_entropy_falls_when_weights_concentrate(self) -> None:
        model = pd.DataFrame([[1, 1, 1, 1, 1, 1], [0, 60, 40, 0, 0, 0], [0, 100, 0, 0, 0, 0]], columns=COLUMNS)
        entropy = normalized_entropy(model)
        self.assertAlmostEqual(float(entropy[0]), 1.0, places=12)
        self.assertGreater(float(entropy[0]), float(entropy[1]))
        self.assertGreater(float(entropy[1]), float(entropy[2]))
        self.assertAlmostEqual(float(entropy[2]), 0.0, places=12)

    def test_opposite_structural_pressure_uses_full_opposite_half(self) -> None:
        model = pd.DataFrame([[10, 50, 30, 5, 3, 2], [10, 5, 5, 20, 30, 30], [10, 10, 10, 10, 10, 10]], columns=COLUMNS)
        direction = np.array([1, -1, 0], dtype=float)
        got = opposite_structural_pressure(model, direction)
        self.assertAlmostEqual(float(got[0]), 10.0)
        self.assertAlmostEqual(float(got[1]), 20.0)
        self.assertTrue(np.isnan(got[2]))


if __name__ == "__main__":
    unittest.main()
