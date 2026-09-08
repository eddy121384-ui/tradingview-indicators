#!/usr/bin/env python3
from __future__ import annotations

import unittest

import numpy as np

from issue68_lifecycle_v3_regime_first import lifecycle_v3_regime_first


MIRROR_STAGE = {0: 0, 1: 4, 2: 5, 3: 6, 4: 1, 5: 2, 6: 3}


class Issue68RegimeFirstV3Tests(unittest.TestCase):
    def test_stage2_enters_long_and_stage5_enters_short(self):
        x = lifecycle_v3_regime_first(np.array([1, 2, 2, 4, 5, 5]), warmup=0)
        self.assertEqual(x.position.tolist(), [0, 1, 1, 0, -1, -1])
        self.assertTrue(x.events["enter_long"][1])
        self.assertTrue(x.events["enter_short"][4])

    def test_stage3_holds_long_but_cannot_open_from_flat(self):
        x = lifecycle_v3_regime_first(np.array([3, 2, 3, 3, 1, 3]), warmup=0)
        self.assertEqual(x.position.tolist(), [0, 1, 1, 1, 0, 0])
        self.assertTrue(x.events["hold_long_reaccumulation"][2])
        self.assertFalse(x.events["enter_long"][0])
        self.assertFalse(x.events["enter_long"][5])

    def test_stage6_holds_short_but_cannot_open_from_flat(self):
        x = lifecycle_v3_regime_first(np.array([6, 5, 6, 6, 4, 6]), warmup=0)
        self.assertEqual(x.position.tolist(), [0, -1, -1, -1, 0, 0])
        self.assertTrue(x.events["hold_short_redistribution"][2])
        self.assertFalse(x.events["enter_short"][0])
        self.assertFalse(x.events["enter_short"][5])

    def test_stage1_and_stage4_flatten(self):
        x = lifecycle_v3_regime_first(np.array([2, 3, 1, 5, 6, 4]), warmup=0)
        self.assertEqual(x.position.tolist(), [1, 1, 0, -1, -1, 0])
        self.assertTrue(x.events["exit_long"][2])
        self.assertTrue(x.events["exit_short"][5])

    def test_stage0_preserves_prior_state(self):
        x = lifecycle_v3_regime_first(np.array([2, 0, 0, 1, 5, 0, 0, 4]), warmup=0)
        self.assertEqual(x.position.tolist(), [1, 1, 1, 0, -1, -1, -1, 0])

    def test_direct_opposite_trend_stage_flips(self):
        x = lifecycle_v3_regime_first(np.array([2, 5, 2]), warmup=0)
        self.assertEqual(x.position.tolist(), [1, -1, 1])
        self.assertTrue(x.events["flip_long_to_short"][1])
        self.assertTrue(x.events["flip_short_to_long"][2])

    def test_synthetic_reciprocal_sequence_is_exact(self):
        formal = np.array([1, 2, 2, 3, 0, 3, 1, 4, 5, 6, 0, 5, 4, 2, 3, 1])
        inverse = np.array([MIRROR_STAGE[int(v)] for v in formal])
        a = lifecycle_v3_regime_first(formal, warmup=0)
        b = lifecycle_v3_regime_first(inverse, warmup=0)
        np.testing.assert_array_equal(a.position, -b.position)
        pairs = {
            "enter_long": "enter_short",
            "enter_short": "enter_long",
            "exit_long": "exit_short",
            "exit_short": "exit_long",
            "flip_long_to_short": "flip_short_to_long",
            "flip_short_to_long": "flip_long_to_short",
            "hold_long_reaccumulation": "hold_short_redistribution",
            "hold_short_redistribution": "hold_long_reaccumulation",
        }
        for left, right in pairs.items():
            np.testing.assert_array_equal(a.events[left], b.events[right])

    def test_warmup_forces_flat_then_begins_cleanly(self):
        x = lifecycle_v3_regime_first(np.array([2, 2, 2, 3]), warmup=2)
        self.assertEqual(x.position.tolist(), [0, 0, 1, 1])


if __name__ == "__main__":
    unittest.main()
