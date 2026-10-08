#!/usr/bin/env python3
"""Issue #180 — stdlib unittest for frozen implementation primitives."""

import math
import unittest

from issue_180_policy import (
    apply_cost, track_stats, classify_impl, decide, compound,
    COST_RATE_PRIMARY,
)


class TestCost(unittest.TestCase):
    def test_rate(self):
        self.assertAlmostEqual(COST_RATE_PRIMARY, 0.0002)

    def test_apply(self):
        self.assertAlmostEqual(apply_cost(0.01, 0.20), 0.01 - 0.20 * 0.0002)
        self.assertAlmostEqual(apply_cost(0.01, 0.0), 0.01)


class TestTrack(unittest.TestCase):
    def test_identical(self):
        s = track_stats([0.01] * 100, [0.01] * 100)
        self.assertEqual(s["n"], 100)
        self.assertAlmostEqual(s["mean_diff_pp"], 0.0)
        self.assertAlmostEqual(s["cum_ratio"], 1.0)

    def test_short(self):
        self.assertEqual(track_stats([0.1], [0.1])["n"], 1)

    def test_compound(self):
        self.assertAlmostEqual(compound([0.10, -0.10]), -0.01)


class TestClassify(unittest.TestCase):
    def test_faithful(self):
        self.assertEqual(classify_impl(200, 0.2, 1.0, 0.995, False),
                         "implementation_faithful")

    def test_faithful_blocked_by_mismatch(self):
        self.assertEqual(classify_impl(200, 0.2, 1.0, 0.995, True),
                         "implementation_acceptable_with_limitation")

    def test_not_ready(self):
        self.assertEqual(classify_impl(59, 0.0, 0.0, 1.0, False),
                         "implementation_not_ready")

    def test_different(self):
        self.assertEqual(classify_impl(200, 0.2, 5.0, 0.99, False),
                         "implementation_materially_different")


class TestDecide(unittest.TestCase):
    def test_preserved(self):
        v, _ = decide(0.5, 2.0, -3.0, 0.2, True, 1.0, False, False)
        self.assertEqual(v, "tradable_implementation_candidate_complete")

    def test_boundary(self):
        v, _ = decide(1.0, 2.5, -5.0, 0.4, True, 2.0, False, False)
        self.assertEqual(v, "tradable_implementation_candidate_complete")

    def test_limited(self):
        v, _ = decide(1.5, 2.0, -3.0, 0.2, True, 1.0, False, False)
        self.assertEqual(v,
                         "tradable_implementation_candidate_complete_with_limitations")

    def test_not_ready_flag(self):
        v, _ = decide(0.0, 0.0, 0.0, 0.0, True, 0.0, False, True)
        self.assertEqual(v, "tradable_implementation_not_ready")


if __name__ == "__main__":
    unittest.main()
