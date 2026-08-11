#!/usr/bin/env python3

from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from evaluate_issue57_phase_e_holdout import live_window, v06_targets


class Issue57PhaseEHoldoutTests(unittest.TestCase):
    def test_frozen_response_map_uses_canonical_four_state(self) -> None:
        model = pd.DataFrame({"canonical_formal_id": [0, 1, 2, 3, 4]})
        np.testing.assert_array_equal(v06_targets(model), np.array([0.0, 0.0, 1.0, 0.0, -1.0]))

    def test_live_window_excludes_only_pre_weight_warmup(self) -> None:
        model = pd.DataFrame(
            {
                "regime_accumulation_family": [np.nan, np.nan, 25.0, 30.0],
                "regime_markup": [np.nan, np.nan, 25.0, 20.0],
                "regime_distribution_family": [np.nan, np.nan, 25.0, 30.0],
                "regime_markdown": [np.nan, np.nan, 25.0, 20.0],
            }
        )
        self.assertEqual(live_window(model), (2, 3))

    def test_live_window_fails_closed_without_canonical_weights(self) -> None:
        model = pd.DataFrame(
            {
                "regime_accumulation_family": [np.nan, 0.0],
                "regime_markup": [np.nan, 0.0],
                "regime_distribution_family": [np.nan, 0.0],
                "regime_markdown": [np.nan, 0.0],
            }
        )
        with self.assertRaises(ValueError):
            live_window(model)


if __name__ == "__main__":
    unittest.main()
