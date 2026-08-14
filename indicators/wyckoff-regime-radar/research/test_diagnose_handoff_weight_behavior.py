import unittest

from diagnose_handoff_weight_behavior import decompose_bridge, summarize_rows


class HandoffWeightBehaviorTests(unittest.TestCase):
    def test_decompose_bull_bridge_unordered(self):
        self.assertEqual(decompose_bridge(2, 1, 1.0), (1, 2, 3))
        self.assertEqual(decompose_bridge(1, 3, 1.0), (1, 3, 2))

    def test_decompose_bear_bridge_unordered(self):
        self.assertEqual(decompose_bridge(6, 4, -1.0), (4, 6, 5))
        self.assertEqual(decompose_bridge(4, 5, -1.0), (4, 5, 6))

    def test_decompose_rejects_non_bridge(self):
        with self.assertRaises(ValueError):
            decompose_bridge(2, 3, 1.0)

    def test_flag_summary_does_not_fit_threshold(self):
        base = {
            "success_within_5": False,
            "success_within_20": False,
            "context_weight": 40.0,
            "carried_weight": 50.0,
            "companion_weight": 10.0,
            "carried_minus_context": 10.0,
            "companion_minus_context": -30.0,
            "family_minus_context": 20.0,
            "context_change_3": -5.0,
            "carried_change_3": 4.0,
            "companion_change_3": 1.0,
            "carried_minus_context_change_3": 9.0,
            "companion_minus_context_change_3": 6.0,
            "context_falling_carried_rising_3": True,
            "context_falling_companion_rising_3": True,
            "both_new_targets_rising_context_falling_3": True,
        }
        a = dict(base, success_within_10=True, carried_already_leads_context=True)
        b = dict(base, success_within_10=False, carried_already_leads_context=False)
        summary = summarize_rows([a, b])
        flag = summary["flags"]["carried_already_leads_context"]
        self.assertEqual(flag["yes_events"], 1)
        self.assertEqual(flag["yes_success_rate_10"], 1.0)
        self.assertEqual(flag["no_success_rate_10"], 0.0)


if __name__ == "__main__":
    unittest.main()
