#!/usr/bin/env python3

from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from v06_state_mapping import (
    FOUR_STATE_NAMES,
    aggregate_six_weights_to_four,
    attach_canonical_four_state,
    map_six_id_to_four,
)


class V06StateMappingTests(unittest.TestCase):
    def test_ids_follow_phase_c_decision(self) -> None:
        values = np.array([0, 1, 2, 3, 4, 5, 6], dtype=int)
        mapped = map_six_id_to_four(values)
        np.testing.assert_array_equal(mapped, np.array([0, 1, 2, 1, 3, 4, 3], dtype=int))
        self.assertEqual(set(FOUR_STATE_NAMES), set(range(5)))

    def test_unknown_six_state_id_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            map_six_id_to_four(np.array([1, 7], dtype=int))

    def test_aggregated_four_weights_preserve_total(self) -> None:
        frame = pd.DataFrame(
            {
                "prob_acc": [10.0],
                "prob_markup": [20.0],
                "prob_reacc": [5.0],
                "prob_dist": [25.0],
                "prob_markdown": [30.0],
                "prob_redist": [10.0],
            }
        )
        result = aggregate_six_weights_to_four(frame)
        self.assertAlmostEqual(float(result.iloc[0].sum()), 100.0)
        self.assertAlmostEqual(float(result.iloc[0]["regime_accumulation_family"]), 15.0)
        self.assertAlmostEqual(float(result.iloc[0]["regime_distribution_family"]), 35.0)

    def test_attach_retains_six_fields_and_adds_canonical_view(self) -> None:
        frame = pd.DataFrame(
            {
                "formal_id": [3],
                "candidate_display_id": [6],
                "prob_acc": [10.0],
                "prob_markup": [20.0],
                "prob_reacc": [5.0],
                "prob_dist": [25.0],
                "prob_markdown": [30.0],
                "prob_redist": [10.0],
            }
        )
        result = attach_canonical_four_state(frame)
        self.assertEqual(int(result.iloc[0]["formal_id"]), 3)
        self.assertEqual(int(result.iloc[0]["canonical_formal_id"]), 1)
        self.assertEqual(int(result.iloc[0]["canonical_candidate_display_id"]), 3)
        self.assertIn("regime_markup", result.columns)


if __name__ == "__main__":
    unittest.main()
