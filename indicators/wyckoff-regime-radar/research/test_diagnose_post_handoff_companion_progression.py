import unittest

import numpy as np

from diagnose_post_handoff_companion_progression import (
    companion_top3,
    future_resolution,
    tie_rank,
)


class PostHandoffCompanionProgressionTests(unittest.TestCase):
    def test_tie_rank_is_one_plus_strictly_greater_count(self):
        w = np.array([40.0, 30.0, 30.0, 0.0, 0.0, 0.0])
        self.assertEqual(tie_rank(w, 2), 2)
        self.assertEqual(tie_rank(w, 3), 2)
        self.assertEqual(tie_rank(w, 4), 4)

    def test_companion_top3_requires_positive_weight(self):
        self.assertTrue(companion_top3(np.array([50.0, 30.0, 20.0, 0.0, 0.0, 0.0]), 3))
        self.assertFalse(companion_top3(np.array([60.0, 40.0, 0.0, 0.0, 0.0, 0.0]), 3))

    def test_future_resolution_uses_first_actionable_direction(self):
        actionable = np.array([0.0, 0.0, -1.0, 1.0, 0.0])
        self.assertEqual(future_resolution(actionable, 0, 1.0, 4), "failure")

    def test_future_resolution_respects_horizon(self):
        actionable = np.array([0.0, 0.0, 0.0, 1.0, 0.0])
        self.assertEqual(future_resolution(actionable, 0, 1.0, 2), "unresolved")
        self.assertEqual(future_resolution(actionable, 0, 1.0, 3), "success")


if __name__ == "__main__":
    unittest.main()
