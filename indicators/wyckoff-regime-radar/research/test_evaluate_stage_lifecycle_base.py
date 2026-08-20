#!/usr/bin/env python3
from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from evaluate_stage_lifecycle_base import (
    binary_color_signal,
    stage_lifecycle_signal,
    strategy_metrics,
)


class StageLifecycleBaseTests(unittest.TestCase):
    def test_binary_color_mapping_is_only_historical_comparator(self) -> None:
        formal = np.array([0, 1, 2, 3, 4, 5, 6, 0])
        got = binary_color_signal(formal, warmup=1)
        np.testing.assert_array_equal(got, np.array([0, 1, 1, 1, -1, -1, -1, 0]))

    def test_stage1_break_arms_and_stage2_within_three_bars_enters(self) -> None:
        formal = np.array([0, 1, 1, 1, 2, 2, 3, 4])
        up = np.array([False, True, False, False, False, False, False, False])
        down = np.zeros(len(formal), dtype=bool)
        signal, stats = stage_lifecycle_signal(formal, up, down, warmup=0, confirm_bars=3)
        self.assertEqual(signal[1], 0)
        self.assertEqual(signal[4], 1)
        self.assertEqual(signal[6], 1)  # Stage 3 holds core.
        self.assertEqual(signal[7], 0)  # Leaving {2,3} exits.
        self.assertEqual(stats["bull_setups_armed"], 1)
        self.assertEqual(stats["bull_setup_confirmed_entries"], 1)

    def test_setup_expires_instead_of_waiting_indefinitely(self) -> None:
        formal = np.array([1, 1, 1, 1, 1, 2, 2])
        up = np.array([True, False, False, False, False, False, False])
        down = np.zeros(len(formal), dtype=bool)
        signal, stats = stage_lifecycle_signal(formal, up, down, warmup=0, confirm_bars=3)
        self.assertTrue(np.all(signal == 0))
        self.assertEqual(stats["bull_setup_expired_or_cancelled"], 1)

    def test_stage2_without_fresh_break_does_not_auto_enter(self) -> None:
        formal = np.array([0, 2, 2, 2])
        no_events = np.zeros(len(formal), dtype=bool)
        signal, _ = stage_lifecycle_signal(formal, no_events, no_events, warmup=0, confirm_bars=3)
        self.assertTrue(np.all(signal == 0))

    def test_fresh_break_inside_stage2_directly_enters_when_flat(self) -> None:
        formal = np.array([0, 2, 2, 2])
        up = np.array([False, True, False, False])
        down = np.zeros(len(formal), dtype=bool)
        signal, stats = stage_lifecycle_signal(formal, up, down, warmup=0, confirm_bars=3)
        self.assertEqual(signal[1], 1)
        self.assertEqual(stats["bull_direct_stage2_break_entries"], 1)

    def test_short_side_is_mirror(self) -> None:
        formal = np.array([0, 4, 4, 5, 6, 1])
        down = np.array([False, True, False, False, False, False])
        up = np.zeros(len(formal), dtype=bool)
        signal, stats = stage_lifecycle_signal(formal, up, down, warmup=0, confirm_bars=3)
        self.assertEqual(signal[1], 0)
        self.assertEqual(signal[3], -1)
        self.assertEqual(signal[4], -1)
        self.assertEqual(signal[5], 0)
        self.assertEqual(stats["bear_setup_confirmed_entries"], 1)

    def test_strategy_metrics_use_one_bar_execution_lag(self) -> None:
        frame = pd.DataFrame({"close": [100.0, 100.0, 110.0, 110.0, 110.0]})
        signal = np.array([0, 1, 0, 0, 0])
        metrics = strategy_metrics(frame, signal, warmup=0)
        # Signal becomes long after close index 1, so the +10% move from index 1
        # to 2 is captured. If same-bar execution were used it would not be.
        self.assertGreater(float(metrics["gross_ann_return"]), 0.0)


if __name__ == "__main__":
    unittest.main()
