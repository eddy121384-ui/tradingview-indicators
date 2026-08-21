#!/usr/bin/env python3
from __future__ import annotations

import unittest

import numpy as np

from evaluate_stage_lifecycle_breakout_invalidation import breakout_invalidation_signal


class BreakoutInvalidationLifecycleTests(unittest.TestCase):
    def run_overlay(
        self,
        base,
        close,
        formal,
        fresh_up=None,
        fresh_down=None,
        high_break=None,
        low_break=None,
        confirm_bars=3,
    ):
        n = len(base)
        fresh_up = np.zeros(n, dtype=bool) if fresh_up is None else np.asarray(fresh_up, dtype=bool)
        fresh_down = np.zeros(n, dtype=bool) if fresh_down is None else np.asarray(fresh_down, dtype=bool)
        high_break = np.full(n, np.nan) if high_break is None else np.asarray(high_break, dtype=float)
        low_break = np.full(n, np.nan) if low_break is None else np.asarray(low_break, dtype=float)
        return breakout_invalidation_signal(
            np.asarray(base, dtype=int),
            np.asarray(close, dtype=float),
            np.asarray(formal, dtype=int),
            fresh_up,
            fresh_down,
            high_break,
            low_break,
            warmup=0,
            confirm_bars=confirm_bars,
        )

    def test_direct_long_uses_break_level_and_requires_new_break_to_reenter(self):
        signal, stats = self.run_overlay(
            base=[1, 1, 1, 1, 0],
            close=[101, 102, 99, 103, 103],
            formal=[2, 2, 2, 2, 0],
            fresh_up=[1, 0, 0, 1, 0],
            high_break=[100, 100, 100, 102, 102],
        )
        self.assertEqual(signal.tolist(), [1, 1, 0, 1, 0])
        self.assertEqual(stats["long_invalidation_exits"], 1)
        self.assertEqual(stats["long_reentries_after_invalidation"], 1)
        self.assertEqual(stats["entry_anchor_missing"], 0)

    def test_confirmed_long_recovers_precursor_break_anchor(self):
        signal, stats = self.run_overlay(
            base=[0, 0, 1, 1, 0],
            close=[101, 102, 103, 99, 99],
            formal=[1, 1, 2, 2, 0],
            fresh_up=[1, 0, 0, 0, 0],
            high_break=[100, 100, 100, 100, 100],
        )
        self.assertEqual(signal.tolist(), [0, 0, 1, 0, 0])
        self.assertEqual(stats["long_invalidation_exits"], 1)
        self.assertEqual(stats["entry_anchor_missing"], 0)

    def test_short_side_is_mirror(self):
        signal, stats = self.run_overlay(
            base=[-1, -1, -1, 0],
            close=[99, 98, 101, 101],
            formal=[5, 5, 5, 0],
            fresh_down=[1, 0, 0, 0],
            low_break=[100, 100, 100, 100],
        )
        self.assertEqual(signal.tolist(), [-1, -1, 0, 0])
        self.assertEqual(stats["short_invalidation_exits"], 1)
        self.assertEqual(stats["entry_anchor_missing"], 0)

    def test_entry_bar_is_not_stopped_even_in_contradictory_synthetic_case(self):
        signal, stats = self.run_overlay(
            base=[1, 1],
            close=[99, 99],
            formal=[2, 2],
            fresh_up=[1, 0],
            high_break=[100, 100],
        )
        self.assertEqual(signal.tolist(), [1, 0])
        self.assertEqual(stats["long_invalidation_exits"], 1)

    def test_overlay_matches_base_when_anchor_never_invalidates(self):
        base = [0, 1, 1, 1, 0, -1, -1, 0]
        signal, stats = self.run_overlay(
            base=base,
            close=[100, 101, 102, 103, 103, 99, 98, 98],
            formal=[0, 2, 2, 2, 0, 5, 5, 0],
            fresh_up=[0, 1, 0, 0, 0, 0, 0, 0],
            fresh_down=[0, 0, 0, 0, 0, 1, 0, 0],
            high_break=[np.nan, 100, 100, 100, 100, 100, 100, 100],
            low_break=[np.nan, 100, 100, 100, 100, 100, 100, 100],
        )
        self.assertEqual(signal.tolist(), base)
        self.assertEqual(stats["long_invalidation_exits"], 0)
        self.assertEqual(stats["short_invalidation_exits"], 0)


if __name__ == "__main__":
    unittest.main()
