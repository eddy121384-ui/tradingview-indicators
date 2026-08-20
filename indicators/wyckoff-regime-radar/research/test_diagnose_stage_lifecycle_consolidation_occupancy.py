#!/usr/bin/env python3
from __future__ import annotations

import unittest
import numpy as np

from diagnose_stage_lifecycle_consolidation_occupancy import run_lengths, summarize_side


class ConsolidationOccupancyTests(unittest.TestCase):
    def test_run_lengths(self) -> None:
        mask = np.array([False, True, True, False, True, False])
        self.assertEqual(run_lengths(mask), [2, 1])

    def test_stage3_counts_only_while_long_is_held(self) -> None:
        position = np.array([0, 1, 1, 1, 0, 0])
        formal = np.array([3, 2, 3, 3, 3, 2])
        result = summarize_side(position, formal, direction=1, trend_stage=2, consolidation_stage=3)
        self.assertEqual(result["held_bars"], 3)
        self.assertEqual(result["trend_stage_bars"], 1)
        self.assertEqual(result["consolidation_stage_bars"], 2)
        self.assertEqual(result["consolidation_runs"], 1)
        self.assertEqual(result["transitions_from_trend_stage"], 1)

    def test_stage6_short_is_mirror(self) -> None:
        position = np.array([0, -1, -1, -1, 0])
        formal = np.array([6, 5, 6, 6, 6])
        result = summarize_side(position, formal, direction=-1, trend_stage=5, consolidation_stage=6)
        self.assertEqual(result["held_bars"], 3)
        self.assertEqual(result["consolidation_stage_bars"], 2)
        self.assertEqual(result["transitions_from_trend_stage"], 1)


if __name__ == "__main__":
    unittest.main()
