#!/usr/bin/env python3

from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from diagnose_consensus_formation_and_formal_lag import (
    action_pair_direction,
    formal_action_direction,
    persistence_event_signal,
    strength_bin_masks,
    threshold_signal,
)


def fake_model(rows: list[tuple[float, float, float, float, float, float, int]]) -> pd.DataFrame:
    return pd.DataFrame(
        rows,
        columns=[
            "prob_acc",
            "prob_markup",
            "prob_reacc",
            "prob_dist",
            "prob_markdown",
            "prob_redist",
            "formal_id",
        ],
    )


class ConsensusFormationTests(unittest.TestCase):
    def test_action_pair_semantics_only_accept_23_and_56(self) -> None:
        top1 = np.array([2, 3, 5, 6, 1, 4, 2])
        top2 = np.array([3, 2, 6, 5, 2, 5, 5])
        got = action_pair_direction(top1, top2)
        np.testing.assert_array_equal(got, np.array([1, 1, -1, -1, 0, 0, 0], dtype=float))

    def test_threshold_signal_requires_action_pair_and_90(self) -> None:
        model = fake_model([
            (1, 50, 42, 1, 3, 3, 0),   # 2+3 = 92 bull
            (1, 46, 43, 1, 5, 4, 0),   # 2+3 = 89 no signal
            (1, 2, 2, 1, 49, 45, 0),   # 5+6 = 94 bear
            (5, 50, 1, 1, 42, 1, 0),   # top 2 + 5, incompatible
        ])
        np.testing.assert_array_equal(threshold_signal(model), np.array([1, 0, -1, 0], dtype=float))

    def test_strength_bins_are_predeclared_and_nonoverlapping(self) -> None:
        model = fake_model([
            (1, 35, 34, 1, 20, 9, 0),  # 69
            (1, 40, 35, 1, 15, 8, 0),  # 75
            (1, 45, 40, 1, 8, 5, 0),   # 85
            (1, 50, 42, 1, 3, 3, 0),   # 92
            (1, 52, 44, 1, 2, 0, 0),   # 96
        ])
        masks = strength_bin_masks(model)
        labels = [next(label for label, mask in masks.items() if mask[i]) for i in range(len(model))]
        self.assertEqual(labels, ["<70", "70-<80", "80-<90", "90-<95", ">=95"])

    def test_formal_action_direction_keeps_1_and_4_neutral(self) -> None:
        model = fake_model([
            (0, 60, 30, 0, 5, 5, 1),
            (0, 60, 30, 0, 5, 5, 2),
            (0, 60, 30, 0, 5, 5, 3),
            (0, 5, 5, 0, 60, 30, 4),
            (0, 5, 5, 0, 60, 30, 5),
            (0, 5, 5, 0, 60, 30, 6),
        ])
        np.testing.assert_array_equal(
            formal_action_direction(model), np.array([0, 1, 1, 0, -1, -1], dtype=float)
        )

    def test_persistence_scores_only_first_bar_reaching_streak(self) -> None:
        model = fake_model([
            (1, 50, 42, 1, 3, 3, 0),
            (1, 51, 41, 1, 3, 3, 0),
            (1, 52, 40, 1, 3, 3, 0),
            (1, 53, 39, 1, 3, 3, 0),
            (5, 40, 30, 5, 10, 10, 0),  # break episode
            (1, 2, 2, 1, 50, 44, 0),
            (1, 2, 2, 1, 51, 43, 0),
            (1, 2, 2, 1, 52, 42, 0),
        ])
        np.testing.assert_array_equal(
            persistence_event_signal(model, 2),
            np.array([0, 1, 0, 0, 0, 0, -1, 0], dtype=float),
        )
        np.testing.assert_array_equal(
            persistence_event_signal(model, 3),
            np.array([0, 0, 1, 0, 0, 0, 0, -1], dtype=float),
        )


if __name__ == "__main__":
    unittest.main()
