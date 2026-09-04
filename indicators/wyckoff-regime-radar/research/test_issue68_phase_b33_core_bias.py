#!/usr/bin/env python3
from __future__ import annotations

import unittest

import numpy as np

from issue68_core_bias_v33 import core_bias_v33

MIRROR = np.array([0, 4, 5, 6, 1, 2, 3], dtype=int)


class Issue68CoreBiasTests(unittest.TestCase):
    def _run(self, stages, warmup=0):
        return core_bias_v33(np.asarray(stages, dtype=int), warmup=warmup)

    def test_stage14_do_not_erase_bear_bias(self):
        r = self._run([5, 4, 1, 4, 0, 6])
        self.assertEqual(r.bias.tolist(), [-1, -1, -1, -1, -1, -1])

    def test_stage14_do_not_erase_bull_bias(self):
        r = self._run([2, 1, 4, 1, 0, 3])
        self.assertEqual(r.bias.tolist(), [1, 1, 1, 1, 1, 1])

    def test_only_opposite_trend_family_flips(self):
        r = self._run([5, 1, 4, 3, 6, 2])
        self.assertEqual(r.bias.tolist(), [-1, -1, -1, 1, -1, 1])
        self.assertTrue(r.events["flip_bear_to_bull"][3])
        self.assertTrue(r.events["flip_bull_to_bear"][4])
        self.assertTrue(r.events["flip_bear_to_bull"][5])

    def test_flat_bias_only_established_by_stage2_or5(self):
        r = self._run([1, 3, 6, 0, 2])
        self.assertEqual(r.bias.tolist(), [0, 0, 0, 0, 1])

    def test_synthetic_reciprocal_sequence_is_exact(self):
        left = np.array([0, 5, 4, 1, 6, 0, 4, 3, 1, 2, 0, 4, 5, 6, 1, 3], dtype=int)
        right = MIRROR[left]
        a = self._run(left)
        b = self._run(right)
        np.testing.assert_array_equal(a.bias, -b.bias)
        np.testing.assert_array_equal(a.events["establish_bull_bias"], b.events["establish_bear_bias"])
        np.testing.assert_array_equal(a.events["establish_bear_bias"], b.events["establish_bull_bias"])
        np.testing.assert_array_equal(a.events["flip_bull_to_bear"], b.events["flip_bear_to_bull"])
        np.testing.assert_array_equal(a.events["flip_bear_to_bull"], b.events["flip_bull_to_bear"])

    def test_warmup_forces_zero_bias(self):
        r = self._run([2, 5, 5, 6], warmup=2)
        self.assertEqual(r.bias.tolist(), [0, 0, -1, -1])


if __name__ == "__main__":
    unittest.main()
