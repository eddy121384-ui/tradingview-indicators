#!/usr/bin/env python3

from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from diagnose_v06_canonical_strength import _bin, _cutpoints, add_strength_fields


class V06CanonicalStrengthTests(unittest.TestCase):
    def test_formal_support_margin_and_concentration(self) -> None:
        frame = pd.DataFrame(
            {
                "formal_id": [2, 5],
                "candidate_display_id": [2, 5],
                "prob_acc": [10.0, 5.0],
                "prob_markup": [60.0, 10.0],
                "prob_reacc": [5.0, 5.0],
                "prob_dist": [10.0, 10.0],
                "prob_markdown": [10.0, 60.0],
                "prob_redist": [5.0, 10.0],
            }
        )
        result = add_strength_fields(frame)
        self.assertEqual(int(result.iloc[0]["canonical_formal_id"]), 2)
        self.assertAlmostEqual(float(result.iloc[0]["canonical_formal_support"]), 60.0)
        self.assertAlmostEqual(float(result.iloc[0]["canonical_formal_margin"]), 45.0)
        self.assertEqual(int(result.iloc[1]["canonical_formal_id"]), 4)
        self.assertAlmostEqual(float(result.iloc[1]["canonical_formal_support"]), 60.0)
        self.assertAlmostEqual(float(result.iloc[1]["canonical_formal_margin"]), 40.0)
        self.assertTrue((result["canonical_concentration"] >= 0.0).all())
        self.assertTrue((result["canonical_concentration"] <= 100.0).all())

    def test_stale_formal_can_have_negative_margin(self) -> None:
        frame = pd.DataFrame(
            {
                "formal_id": [2],
                "candidate_display_id": [5],
                "prob_acc": [5.0],
                "prob_markup": [10.0],
                "prob_reacc": [5.0],
                "prob_dist": [10.0],
                "prob_markdown": [60.0],
                "prob_redist": [10.0],
            }
        )
        result = add_strength_fields(frame)
        self.assertLess(float(result.iloc[0]["canonical_formal_margin"]), 0.0)

    def test_development_cutpoints_and_bins_are_ordered(self) -> None:
        values = np.arange(60, dtype=float)
        cuts = _cutpoints(values)
        self.assertIsNotNone(cuts)
        assert cuts is not None
        self.assertLess(cuts[0], cuts[1])
        bins = _bin(np.array([cuts[0] - 1.0, np.mean(cuts), cuts[1] + 1.0]), cuts)
        np.testing.assert_array_equal(bins, np.array([0, 1, 2], dtype=int))

    def test_cutpoints_require_minimum_development_sample(self) -> None:
        self.assertIsNone(_cutpoints(np.arange(10, dtype=float)))


if __name__ == "__main__":
    unittest.main()
