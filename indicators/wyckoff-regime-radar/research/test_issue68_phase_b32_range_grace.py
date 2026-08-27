#!/usr/bin/env python3
from __future__ import annotations

import unittest

import numpy as np

from issue68_lifecycle_v32_range_grace import lifecycle_v32_range_grace


MIRROR = np.array([0, 4, 5, 6, 1, 2, 3], dtype=int)


class Issue68RangeGraceTests(unittest.TestCase):
    def _run(self, stages, confirm=3, warmup=0):
        return lifecycle_v32_range_grace(np.asarray(stages, dtype=int), warmup=warmup, confirm_bars=confirm)

    def test_flat_entries_unchanged(self):
        r = self._run([1, 3, 6, 2, 4, 5])
        self.assertEqual(r.position.tolist(), [0, 0, 0, 1, 1, -1])

    def test_transient_range_does_not_wash_long(self):
        r = self._run([2, 1, 4, 2], confirm=3)
        self.assertEqual(r.position.tolist(), [1, 1, 1, 1])
        self.assertEqual(r.range_grace_bars.tolist(), [0, 1, 2, 0])
        self.assertEqual(int(r.events["range_grace_exit_long"].sum()), 0)

    def test_sustained_range_exits_long_after_grace(self):
        r = self._run([2, 1, 4, 1], confirm=3)
        self.assertEqual(r.position.tolist(), [1, 1, 1, 0])
        self.assertTrue(r.events["range_grace_exit_long"][3])

    def test_sustained_range_exits_short_after_grace(self):
        r = self._run([5, 4, 1, 4], confirm=3)
        self.assertEqual(r.position.tolist(), [-1, -1, -1, 0])
        self.assertTrue(r.events["range_grace_exit_short"][3])

    def test_stage0_preserves_position_and_grace_count(self):
        r = self._run([5, 1, 0, 4, 5], confirm=3)
        self.assertEqual(r.position.tolist(), [-1, -1, -1, -1, -1])
        self.assertEqual(r.range_grace_bars.tolist(), [0, 1, 1, 2, 0])

    def test_same_side_trend_resets_grace(self):
        r = self._run([5, 1, 4, 6, 1, 4], confirm=3)
        self.assertEqual(r.position.tolist(), [-1, -1, -1, -1, -1, -1])
        self.assertEqual(r.range_grace_bars.tolist(), [0, 1, 2, 0, 1, 2])

    def test_opposite_trend_family_flips_immediately(self):
        long_to_short = self._run([2, 1, 5], confirm=3)
        self.assertEqual(long_to_short.position.tolist(), [1, 1, -1])
        self.assertTrue(long_to_short.events["flip_long_to_short"][2])

        short_to_long = self._run([5, 4, 3], confirm=3)
        self.assertEqual(short_to_long.position.tolist(), [-1, -1, 1])
        self.assertTrue(short_to_long.events["flip_short_to_long"][2])

    def test_synthetic_reciprocal_sequence_is_exact(self):
        left = np.array([0, 2, 1, 4, 2, 3, 1, 4, 1, 0, 5, 6, 4, 1, 5, 0, 2, 3], dtype=int)
        right = MIRROR[left]
        a = self._run(left, confirm=3)
        b = self._run(right, confirm=3)
        np.testing.assert_array_equal(a.position, -b.position)
        np.testing.assert_array_equal(a.range_grace_bars, b.range_grace_bars)
        np.testing.assert_array_equal(a.events["enter_long"], b.events["enter_short"])
        np.testing.assert_array_equal(a.events["enter_short"], b.events["enter_long"])
        np.testing.assert_array_equal(a.events["exit_long"], b.events["exit_short"])
        np.testing.assert_array_equal(a.events["exit_short"], b.events["exit_long"])
        np.testing.assert_array_equal(a.events["range_grace_exit_long"], b.events["range_grace_exit_short"])
        np.testing.assert_array_equal(a.events["range_grace_exit_short"], b.events["range_grace_exit_long"])

    def test_warmup_forces_flat(self):
        r = self._run([2, 2, 5, 5], confirm=3, warmup=2)
        self.assertEqual(r.position.tolist(), [0, 0, -1, -1])


if __name__ == "__main__":
    unittest.main()
