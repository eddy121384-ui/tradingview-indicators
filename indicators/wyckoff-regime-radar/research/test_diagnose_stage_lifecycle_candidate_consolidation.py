#!/usr/bin/env python3
from __future__ import annotations

import unittest
import numpy as np

from diagnose_stage_lifecycle_candidate_consolidation import summarize_candidate


class CandidateConsolidationTests(unittest.TestCase):
    def test_candidate_stage3_counts_only_during_held_long(self) -> None:
        position = np.array([0, 1, 1, 1, 0])
        formal = np.array([2, 2, 2, 3, 2])
        candidate = np.array([3, 0, 3, 3, 3])
        result = summarize_candidate(position, formal, candidate, 1, 2, 3)
        self.assertEqual(result["held_bars"], 3)
        self.assertEqual(result["candidate_consolidation_bars"], 2)
        self.assertEqual(result["candidate_inside_matching_formal_trend_bars"], 1)
        self.assertEqual(result["candidate_runs"], 1)

    def test_candidate_stage6_short_is_mirror(self) -> None:
        position = np.array([0, -1, -1, -1, 0])
        formal = np.array([5, 5, 5, 5, 5])
        candidate = np.array([0, 6, 6, 0, 6])
        result = summarize_candidate(position, formal, candidate, -1, 5, 6)
        self.assertEqual(result["candidate_consolidation_bars"], 2)
        self.assertEqual(result["candidate_inside_matching_formal_trend_bars"], 2)
        self.assertEqual(result["candidate_runs"], 1)
        self.assertEqual(result["candidate_onsets_while_formal_trend"], 1)


if __name__ == "__main__":
    unittest.main()
