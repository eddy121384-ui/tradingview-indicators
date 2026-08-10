from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from evaluate_state_separation_pre_final import (  # noqa: E402
    eta_squared,
    sign_stability,
    spearman_from_stage_means,
)


class StateSeparationDiagnosticTests(unittest.TestCase):
    def test_eta_squared_is_zero_when_group_means_are_equal(self) -> None:
        values = np.array([-1.0, 1.0, -1.0, 1.0])
        groups = np.array([1.0, 1.0, 2.0, 2.0])
        self.assertAlmostEqual(eta_squared(values, groups), 0.0)

    def test_eta_squared_is_one_for_perfect_group_separation(self) -> None:
        values = np.array([0.0, 0.0, 10.0, 10.0])
        groups = np.array([1.0, 1.0, 2.0, 2.0])
        self.assertAlmostEqual(eta_squared(values, groups), 1.0)

    def test_rank_stability_detects_reversal(self) -> None:
        result = spearman_from_stage_means(
            {1: -1.0, 2: 0.0, 5: 1.0},
            {1: 1.0, 2: 0.0, 5: -1.0},
        )
        self.assertEqual(result["common_stage_count"], 3)
        self.assertAlmostEqual(result["rho"], -1.0)

    def test_rank_stability_requires_three_common_states(self) -> None:
        result = spearman_from_stage_means({1: 0.0, 2: 1.0}, {1: 0.0, 2: 1.0})
        self.assertIsNone(result["rho"])

    def test_sign_stability_counts_same_direction(self) -> None:
        result = sign_stability(
            {1: 0.1, 2: -0.2, 5: 0.3},
            {1: 0.4, 2: -0.1, 5: -0.3},
        )
        self.assertEqual(result["common_stage_count"], 3)
        self.assertEqual(result["same_sign_count"], 2)


if __name__ == "__main__":
    unittest.main()
