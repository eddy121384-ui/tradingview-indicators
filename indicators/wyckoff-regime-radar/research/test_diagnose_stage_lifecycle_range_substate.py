#!/usr/bin/env python3
from __future__ import annotations

import unittest
import numpy as np

from diagnose_stage_lifecycle_range_substate import (
    extract_runs,
    fresh_break_lag_after_run,
    summarize_level,
)


class RangeSubstateTests(unittest.TestCase):
    def test_extract_runs(self) -> None:
        self.assertEqual(extract_runs(np.array([False, True, True, False, True])), [(1, 2), (4, 4)])

    def test_break_lag_stops_if_position_family_ends(self) -> None:
        position = np.array([1, 1, 0, 1])
        fresh = np.array([False, False, False, True])
        self.assertIsNone(fresh_break_lag_after_run(1, position, fresh, 1, horizon=3))

    def test_same_bar_end_break_is_lag_zero(self) -> None:
        position = np.array([1, 1, 1])
        fresh = np.array([False, True, False])
        self.assertEqual(fresh_break_lag_after_run(1, position, fresh, 1, horizon=3), 0)

    def test_existing_threshold_counts_only_held_bars(self) -> None:
        position = np.array([0, 1, 1, 1, 0])
        formal = np.array([2, 2, 2, 2, 2])
        score = np.array([80.0, 20.0, 40.0, 80.0, 90.0])
        fresh = np.zeros(5, dtype=bool)
        result = summarize_level(position, formal, score, fresh, 1, 2, 35.0)
        self.assertEqual(result["held_bars"], 3)
        self.assertEqual(result["range_active_bars"], 2)
        self.assertEqual(result["runs"], 1)


if __name__ == "__main__":
    unittest.main()
