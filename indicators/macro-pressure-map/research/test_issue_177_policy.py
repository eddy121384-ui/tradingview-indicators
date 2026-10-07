#!/usr/bin/env python3
"""Issue #177 — stdlib unittest for frozen policy primitives."""

import math
import unittest

from issue_177_policy import (
    baseline_tier, zero_rule_b, apply_zero, confidence, cash_bias,
    opportunity_score,
)


class TestTiers(unittest.TestCase):
    def test_favored(self):
        self.assertEqual(baseline_tier("historically_favored", -0.5), "High")

    def test_unfavorable(self):
        self.assertEqual(baseline_tier("historically_unfavorable", 0.5), "Low")

    def test_mixed_sign(self):
        self.assertEqual(baseline_tier("mixed", 0.0), "Neutral")
        self.assertEqual(baseline_tier("mixed", 0.001), "Neutral")
        self.assertEqual(baseline_tier("mixed", -0.0001), "Low")
        self.assertEqual(baseline_tier("mixed", float("nan")), "Low")

    def test_insufficient(self):
        self.assertEqual(baseline_tier("insufficient_sample", 0.9), "Neutral")
        # insufficient sample can never become Low or High, whatever the sign
        self.assertEqual(baseline_tier("insufficient_sample", -0.9), "Neutral")
        self.assertEqual(baseline_tier("insufficient_sample", float("nan")), "Neutral")

    def test_unknown(self):
        with self.assertRaises(ValueError):
            baseline_tier("favored", 0.1)


class TestZero(unittest.TestCase):
    def test_path_b_true(self):
        self.assertTrue(zero_rule_b("historically_unfavorable", -0.01, 0.30,
                                    -0.05, -0.10, 0.05, -0.005))

    def test_path_b_wrong_evidence(self):
        self.assertFalse(zero_rule_b("mixed", -0.01, 0.30,
                                     -0.05, -0.10, 0.05, -0.005))

    def test_path_b_hit_boundary(self):
        self.assertTrue(zero_rule_b("historically_unfavorable", -0.01, 0.40,
                                    -0.04, 0.0, 0.0, -0.001))
        self.assertFalse(zero_rule_b("historically_unfavorable", -0.01, 0.41,
                                     -0.04, 0.0, 0.0, -0.001))

    def test_path_b_no_tail(self):
        self.assertFalse(zero_rule_b("historically_unfavorable", -0.01, 0.30,
                                     -0.01, -0.01, 0.01, -0.005))

    def test_path_b_tail_alternatives(self):
        # each of the three severe-tail conditions independently satisfies 4a/4b/4c
        self.assertTrue(zero_rule_b("historically_unfavorable", -0.01, 0.30,
                                    -0.04, 0.0, 0.0, -0.001))
        self.assertTrue(zero_rule_b("historically_unfavorable", -0.01, 0.30,
                                    0.0, -0.15, 0.0, -0.001))
        self.assertTrue(zero_rule_b("historically_unfavorable", -0.01, 0.30,
                                    0.0, 0.0, 0.10, -0.001))

    def test_path_b_mean_sign_and_ex_worst_boundaries(self):
        self.assertFalse(zero_rule_b("historically_unfavorable", 0.0, 0.30,
                                     -0.05, -0.20, 0.20, -0.001))
        self.assertFalse(zero_rule_b("historically_unfavorable", -0.01, 0.30,
                                     -0.05, -0.20, 0.20, 0.0))
        self.assertFalse(zero_rule_b("historically_unfavorable", -0.01, 0.30,
                                     -0.05, -0.20, 0.20, float("nan")))

    def test_apply_zero(self):
        self.assertEqual(apply_zero("Low", True, False), ("0", "A"))
        self.assertEqual(apply_zero("Low", False, True), ("0", "B"))
        self.assertEqual(apply_zero("Low", True, True), ("0", "A"))
        self.assertEqual(apply_zero("Low", False, False), ("Low", ""))
        self.assertEqual(apply_zero("Neutral", True, True), ("Neutral", ""))
        self.assertEqual(apply_zero("High", True, True), ("High", ""))
        self.assertEqual(apply_zero("0", True, True), ("0", ""))


class TestConfidenceCash(unittest.TestCase):
    def test_confidence(self):
        self.assertEqual(confidence("eligible_with_limitation", None), "limited")
        self.assertEqual(confidence("eligible_primary",
                                    "hardened_with_limitation"), "limited")
        self.assertEqual(confidence("eligible_primary",
                                    "unresolved_keep_issue174_semantics"),
                         "limited")
        self.assertEqual(confidence("eligible_primary", None), "full")

    def test_cash(self):
        self.assertEqual(cash_bias(3), "high")
        self.assertEqual(cash_bias(4), "neutral")
        self.assertEqual(cash_bias(8), "neutral")
        self.assertEqual(cash_bias(9), "low")
        self.assertEqual(cash_bias(-8), "high")
        self.assertEqual(cash_bias(16), "low")
        self.assertEqual(opportunity_score(["High"] * 8), 16)
        self.assertEqual(opportunity_score(["Low"] * 8), 0)

    def test_cash_bands_partition_full_attainable_range(self):
        # attainable range is 8 x [-1, +2] = [-8, 16]; bands must partition it
        seen = set()
        for s in range(-8, 17):
            b = cash_bias(s)
            self.assertIn(b, {"high", "neutral", "low"})
            seen.add(b)
        self.assertEqual(seen, {"high", "neutral", "low"})

    def test_confidence_oil_and_gold(self):
        # oil is eligible_with_limitation in #174 -> limited even under #176 hardening
        self.assertEqual(confidence("eligible_with_limitation",
                                    "hardened_with_limitation"), "limited")
        # gold has no limitation -> full
        self.assertEqual(confidence("eligible_primary", None), "full")


if __name__ == "__main__":
    unittest.main()
