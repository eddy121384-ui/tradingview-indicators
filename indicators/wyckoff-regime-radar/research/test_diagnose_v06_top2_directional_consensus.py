#!/usr/bin/env python3

from __future__ import annotations

import unittest

import pandas as pd

from diagnose_v06_top2_directional_consensus import (
    formal_family_signal,
    formal_trend_only_signal,
    top1_signal,
    top2_consensus_signal,
)


class Top2DirectionalConsensusTests(unittest.TestCase):
    def _model(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                # bullish aligned, total 91 -> +1
                "prob_acc": [55.0, 1.0, 55.0, 50.0],
                "prob_markup": [36.0, 1.0, 1.0, 39.0],
                "prob_reacc": [2.0, 1.0, 1.0, 2.0],
                # row 2 is mixed top-2; row 4 bull same-dir but only 89
                "prob_dist": [3.0, 48.0, 40.0, 3.0],
                "prob_markdown": [2.0, 43.0, 2.0, 3.0],
                "prob_redist": [2.0, 6.0, 1.0, 3.0],
                "formal_id": [1, 5, 4, 3],
            }
        )

    def test_primary_top2_rule_requires_same_direction_and_90(self) -> None:
        signal = top2_consensus_signal(self._model(), 90.0)
        self.assertEqual(signal.tolist(), [1.0, -1.0, 0.0, 0.0])

    def test_top1_uses_directional_family(self) -> None:
        signal = top1_signal(self._model())
        self.assertEqual(signal.tolist(), [1.0, -1.0, 1.0, 1.0])

    def test_formal_family_and_trend_only_are_distinct_comparators(self) -> None:
        model = self._model()
        self.assertEqual(formal_family_signal(model).tolist(), [1.0, -1.0, -1.0, 1.0])
        self.assertEqual(formal_trend_only_signal(model).tolist(), [0.0, -1.0, 0.0, 1.0])


if __name__ == "__main__":
    unittest.main()
