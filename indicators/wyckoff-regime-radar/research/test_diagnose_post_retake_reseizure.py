import unittest

import numpy as np

from diagnose_post_retake_reseizure import (
    checkpoint_eligible_after_retake,
    first_reseizure_after_retake,
    reseized_by_checkpoint,
)


class PostRetakeReseizureTests(unittest.TestCase):
    def test_finds_first_reseizure_after_retake(self):
        weights = np.zeros((6, 6), dtype=float)
        weights[:, 0] = [40, 60, 55, 45, 30, 20]  # context
        weights[:, 1] = [60, 40, 45, 55, 70, 80]  # carried
        self.assertEqual(first_reseizure_after_retake(weights, 0, 1, 6, 2, 1), 2)

    def test_resolution_bar_cannot_create_reseizure(self):
        weights = np.zeros((5, 6), dtype=float)
        weights[:, 0] = [40, 60, 60, 60, 20]
        weights[:, 1] = [60, 40, 40, 40, 80]
        self.assertIsNone(first_reseizure_after_retake(weights, 0, 1, 4, 2, 1))

    def test_checkpoint_is_relative_to_retake_and_pre_resolution(self):
        self.assertTrue(checkpoint_eligible_after_retake(8, 2, 5))
        self.assertFalse(checkpoint_eligible_after_retake(7, 2, 5))

    def test_reseized_by_checkpoint(self):
        self.assertTrue(reseized_by_checkpoint(1, 1))
        self.assertTrue(reseized_by_checkpoint(3, 5))
        self.assertFalse(reseized_by_checkpoint(5, 3))
        self.assertFalse(reseized_by_checkpoint(None, 5))


if __name__ == "__main__":
    unittest.main()
