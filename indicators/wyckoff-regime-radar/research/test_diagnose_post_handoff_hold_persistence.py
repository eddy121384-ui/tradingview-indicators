from __future__ import annotations

import unittest

import numpy as np

from diagnose_post_handoff_hold_persistence import (
    checkpoint_eligible,
    first_retake_lag,
    holds_lead_through,
)


class PostHandoffHoldPersistenceTests(unittest.TestCase):
    def test_hold_requires_continuous_lead_not_endpoint_recovery(self) -> None:
        # context=stage1, carried=stage2
        w = np.array(
            [
                [40.0, 60.0, 0, 0, 0, 0],
                [55.0, 45.0, 0, 0, 0, 0],
                [30.0, 70.0, 0, 0, 0, 0],
            ]
        )
        self.assertFalse(holds_lead_through(w, 0, 2, carried_id=2, context_id=1))

    def test_hold_true_when_carried_leads_every_bar(self) -> None:
        w = np.array(
            [
                [40.0, 60.0, 0, 0, 0, 0],
                [35.0, 65.0, 0, 0, 0, 0],
                [30.0, 70.0, 0, 0, 0, 0],
            ]
        )
        self.assertTrue(holds_lead_through(w, 0, 2, carried_id=2, context_id=1))

    def test_first_retake_is_first_context_ge_carried_before_resolution(self) -> None:
        w = np.array(
            [
                [40.0, 60.0, 0, 0, 0, 0],
                [45.0, 55.0, 0, 0, 0, 0],
                [50.0, 50.0, 0, 0, 0, 0],
                [60.0, 40.0, 0, 0, 0, 0],
            ]
        )
        self.assertEqual(first_retake_lag(w, 0, 4, carried_id=2, context_id=1), 2)

    def test_resolution_bar_is_not_reclassified_as_prior_retake(self) -> None:
        w = np.array(
            [
                [40.0, 60.0, 0, 0, 0, 0],
                [45.0, 55.0, 0, 0, 0, 0],
                [70.0, 30.0, 0, 0, 0, 0],
            ]
        )
        self.assertIsNone(first_retake_lag(w, 0, 2, carried_id=2, context_id=1))

    def test_checkpoint_only_eligible_before_resolution(self) -> None:
        self.assertTrue(checkpoint_eligible(4, 3))
        self.assertFalse(checkpoint_eligible(3, 3))
        self.assertFalse(checkpoint_eligible(2, 3))


if __name__ == "__main__":
    unittest.main()
