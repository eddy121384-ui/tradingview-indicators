import unittest

import numpy as np

from diagnose_bridge_formation_outcomes import bridge_direction, extract_bridge_watches


class BridgeFormationOutcomeTests(unittest.TestCase):
    def test_bridge_direction_classifies_unordered_semantic_pairs(self):
        top1 = np.array([1, 2, 1, 3, 4, 5, 4, 6, 2])
        top2 = np.array([2, 1, 3, 1, 5, 4, 6, 4, 3])
        got = bridge_direction(top1, top2)
        np.testing.assert_array_equal(got, np.array([1, 1, 1, 1, -1, -1, -1, -1, 0], dtype=float))

    def test_watch_is_non_overlapping_and_resolves_on_same_actionable(self):
        bridge = np.zeros(30, dtype=float)
        actionable = np.zeros(30, dtype=float)
        bridge[1:4] = 1.0
        actionable[5] = 1.0
        bridge[3] = 1.0  # would be a repeated bridge bar, not a second event
        rows = extract_bridge_watches(bridge, actionable)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["onset"], 1)
        self.assertEqual(rows[0]["success_lag"], 4)
        self.assertTrue(rows[0]["success_within_5"])

    def test_opposite_actionable_resolves_as_failure_before_later_success(self):
        bridge = np.zeros(35, dtype=float)
        actionable = np.zeros(35, dtype=float)
        bridge[2] = -1.0
        actionable[6] = 1.0   # opposite to bearish watch
        actionable[9] = -1.0  # later same-direction action must not rescue event
        rows = extract_bridge_watches(bridge, actionable)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["resolution"], "opposite_actionable")
        self.assertIsNone(rows[0]["success_lag"])
        self.assertEqual(rows[0]["opposite_lag"], 4)

    def test_tail_bridge_without_full_twenty_bar_window_is_excluded(self):
        bridge = np.zeros(25, dtype=float)
        actionable = np.zeros(25, dtype=float)
        bridge[10] = 1.0
        rows = extract_bridge_watches(bridge, actionable)
        self.assertEqual(rows, [])

    def test_timeout_skips_overlapping_bridge_attempts_inside_watch(self):
        bridge = np.zeros(50, dtype=float)
        actionable = np.zeros(50, dtype=float)
        bridge[1] = 1.0
        bridge[8] = -1.0
        rows = extract_bridge_watches(bridge, actionable)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["onset"], 1)
        self.assertEqual(rows[0]["resolution"], "timeout")


if __name__ == "__main__":
    unittest.main()
