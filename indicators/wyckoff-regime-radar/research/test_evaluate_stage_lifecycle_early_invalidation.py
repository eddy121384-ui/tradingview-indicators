#!/usr/bin/env python3
from __future__ import annotations

import unittest

import numpy as np

from evaluate_stage_lifecycle_early_invalidation import early_breakout_invalidation_signal


class EarlyBreakoutInvalidationTests(unittest.TestCase):
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
        return early_breakout_invalidation_signal(
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

    def test_long_invalidates_inside_first_three_bars(self):
        signal, stats = self.run_overlay(
            base=[1, 1, 1, 1, 0],
            close=[101, 102, 99, 103, 103],
            formal=[2, 2, 2, 2, 0],
            fresh_up=[1, 0, 0, 0, 0],
            high_break=[100, 100, 100, 100, 100],
        )
        self.assertEqual(signal.tolist(), [1, 1, 0, 0, 0])
        self.assertEqual(stats["long_early_invalidation_exits"], 1)

    def test_anchor_retires_after_age_three(self):
        signal, stats = self.run_overlay(
            base=[1, 1, 1, 1, 1, 1, 0],
            close=[101, 102, 103, 104, 99, 98, 98],
            formal=[2, 2, 2, 2, 2, 2, 0],
            fresh_up=[1, 0, 0, 0, 0, 0, 0],
            high_break=[100, 100, 100, 100, 100, 100, 100],
        )
        self.assertEqual(signal.tolist(), [1, 1, 1, 1, 1, 1, 0])
        self.assertEqual(stats["long_early_invalidation_exits"], 0)
        self.assertEqual(stats["windows_survived"], 1)

    def test_new_fresh_break_reentry_starts_new_window(self):
        signal, stats = self.run_overlay(
            base=[1, 1, 1, 1, 1, 0],
            close=[101, 99, 101, 103, 101, 101],
            formal=[2, 2, 2, 2, 2, 0],
            fresh_up=[1, 0, 1, 0, 0, 0],
            high_break=[100, 100, 102, 102, 102, 102],
        )
        self.assertEqual(signal.tolist(), [1, 0, 1, 1, 0, 0])
        self.assertEqual(stats["long_early_invalidation_exits"], 2)
        self.assertEqual(stats["long_reentries_after_early_invalidation"], 1)

    def test_confirmed_entry_uses_precursor_anchor(self):
        signal, stats = self.run_overlay(
            base=[0, 0, 1, 1, 0],
            close=[101, 102, 103, 99, 99],
            formal=[1, 1, 2, 2, 0],
            fresh_up=[1, 0, 0, 0, 0],
            high_break=[100, 100, 100, 100, 100],
        )
        self.assertEqual(signal.tolist(), [0, 0, 1, 0, 0])
        self.assertEqual(stats["long_early_invalidation_exits"], 1)
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
        self.assertEqual(stats["short_early_invalidation_exits"], 1)


if __name__ == "__main__":
    unittest.main()
