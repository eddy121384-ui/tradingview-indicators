#!/usr/bin/env python3
from __future__ import annotations

import unittest
import numpy as np
import pandas as pd

from evaluate_stage_lifecycle_range_management import (
    range_managed_exposure,
    strategy_metrics_fractional,
)


class RangeManagedLifecycleTests(unittest.TestCase):
    def test_new_entry_starts_full_then_strong_range_reduces(self) -> None:
        base = np.array([0, 1, 1, 1, 1])
        formal = np.array([0, 2, 2, 2, 2])
        score = np.array([0.0, 80.0, 80.0, 20.0, 20.0])
        up = np.zeros(5, dtype=bool)
        down = np.zeros(5, dtype=bool)
        exposure, stats = range_managed_exposure(base, formal, score, up, down, warmup=0)
        self.assertEqual(exposure[1], 1.0)  # entry gets full size despite high score.
        self.assertEqual(exposure[2], 0.5)
        self.assertEqual(exposure[3], 0.5)  # score cooling does not auto restore.
        self.assertEqual(stats["long_reductions"], 1)

    def test_fresh_stage2_break_restores_full(self) -> None:
        base = np.array([0, 1, 1, 1, 1])
        formal = np.array([0, 2, 2, 2, 2])
        score = np.array([0.0, 20.0, 80.0, 20.0, 90.0])
        up = np.array([False, False, False, True, True])
        down = np.zeros(5, dtype=bool)
        exposure, stats = range_managed_exposure(base, formal, score, up, down, warmup=0)
        self.assertEqual(exposure[2], 0.5)
        self.assertEqual(exposure[3], 1.0)
        self.assertEqual(exposure[4], 1.0)  # same-bar fresh break beats range reduction.
        self.assertEqual(stats["long_readds"], 1)

    def test_family_exit_resets_reduced_latch_and_new_episode_full(self) -> None:
        base = np.array([0, 1, 1, 0, 1, 1])
        formal = np.array([0, 2, 2, 1, 2, 2])
        score = np.array([0.0, 20.0, 80.0, 0.0, 90.0, 90.0])
        no_break = np.zeros(6, dtype=bool)
        exposure, _ = range_managed_exposure(base, formal, score, no_break, no_break, warmup=0)
        self.assertEqual(exposure[2], 0.5)
        self.assertEqual(exposure[3], 0.0)
        self.assertEqual(exposure[4], 1.0)
        self.assertEqual(exposure[5], 0.5)

    def test_short_side_is_mirror(self) -> None:
        base = np.array([0, -1, -1, -1])
        formal = np.array([0, 5, 5, 5])
        score = np.array([0.0, 20.0, 80.0, 20.0])
        up = np.zeros(4, dtype=bool)
        down = np.array([False, False, False, True])
        exposure, stats = range_managed_exposure(base, formal, score, up, down, warmup=0)
        self.assertEqual(exposure[2], -0.5)
        self.assertEqual(exposure[3], -1.0)
        self.assertEqual(stats["short_reductions"], 1)
        self.assertEqual(stats["short_readds"], 1)

    def test_fractional_metrics_use_one_bar_lag_and_partial_exposure(self) -> None:
        frame = pd.DataFrame({"close": [100.0, 100.0, 110.0, 121.0, 121.0]})
        full = np.array([0.0, 1.0, 1.0, 0.0, 0.0])
        half = np.array([0.0, 0.5, 0.5, 0.0, 0.0])
        full_metrics = strategy_metrics_fractional(frame, full, warmup=0)
        half_metrics = strategy_metrics_fractional(frame, half, warmup=0)
        self.assertGreater(float(full_metrics["gross_ann_return"]), float(half_metrics["gross_ann_return"]))
        self.assertLess(float(half_metrics["average_absolute_exposure"]), float(full_metrics["average_absolute_exposure"]))


if __name__ == "__main__":
    unittest.main()
