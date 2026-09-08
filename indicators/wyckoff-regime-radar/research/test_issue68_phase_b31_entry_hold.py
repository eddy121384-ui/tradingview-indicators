#!/usr/bin/env python3
import unittest
import numpy as np

from issue68_lifecycle_v31_entry_hold import lifecycle_v31


class Issue68V31Tests(unittest.TestCase):
    def run_life(self, formal, strong):
        return lifecycle_v31(np.array(formal, dtype=int), np.array(strong, dtype=int), warmup=0)

    def test_flat_requires_aligned_strong_stage_for_entry(self):
        r = self.run_life([2, 2, 5, 5], [0, 2, 0, 5])
        self.assertEqual(r.position.tolist(), [0, 1, 0, -1])
        self.assertTrue(r.events['blocked_long_entry'][0])
        self.assertTrue(r.events['blocked_short_entry'][2])

    def test_existing_long_holds_without_strong_candidate(self):
        r = self.run_life([2, 2, 3, 0, 2], [2, 0, 0, 0, 0])
        self.assertEqual(r.position.tolist(), [1, 1, 1, 1, 1])

    def test_existing_short_holds_without_strong_candidate(self):
        r = self.run_life([5, 5, 6, 0, 5], [5, 0, 0, 0, 0])
        self.assertEqual(r.position.tolist(), [-1, -1, -1, -1, -1])

    def test_stage1_and_stage4_flatten(self):
        r = self.run_life([2, 1, 5, 4], [2, 0, 5, 0])
        self.assertEqual(r.position.tolist(), [1, 0, -1, 0])

    def test_stage3_and_stage6_cannot_open_from_flat(self):
        r = self.run_life([3, 6], [3, 6])
        self.assertEqual(r.position.tolist(), [0, 0])

    def test_opposite_formal_without_aligned_strong_only_exits(self):
        r = self.run_life([2, 5, 5], [2, 0, 5])
        self.assertEqual(r.position.tolist(), [1, 0, -1])
        self.assertFalse(r.events['flip_long_to_short'][1])
        self.assertTrue(r.events['exit_long'][1])

    def test_opposite_formal_with_aligned_strong_can_flip(self):
        r = self.run_life([2, 5], [2, 5])
        self.assertEqual(r.position.tolist(), [1, -1])
        self.assertTrue(r.events['flip_long_to_short'][1])

    def test_synthetic_reciprocal_sequence_is_exact(self):
        formal = np.array([1,2,2,3,0,4,5,5,6,0,1,2,4,5], dtype=int)
        strong = np.array([0,2,0,0,0,0,5,0,0,0,0,2,0,5], dtype=int)
        mirror_map = {0:0,1:4,2:5,3:6,4:1,5:2,6:3}
        inv_formal = np.array([mirror_map[x] for x in formal], dtype=int)
        inv_strong = np.array([mirror_map[x] for x in strong], dtype=int)
        a = lifecycle_v31(formal, strong, warmup=0)
        b = lifecycle_v31(inv_formal, inv_strong, warmup=0)
        np.testing.assert_array_equal(a.position, -b.position)


if __name__ == '__main__':
    unittest.main()
