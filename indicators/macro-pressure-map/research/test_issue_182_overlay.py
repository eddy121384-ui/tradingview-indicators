#!/usr/bin/env python3
"""Issue #182 — stdlib unittest for frozen overlay primitives."""

import unittest

from issue_182_overlay import classify, apply_overlay, decide


def base_weights(**over):
    w = {"sp500": 25.0, "nasdaq": 12.0, "russell": 8.0,
         "treasury2y": 8.0, "treasury10y": 14.0, "longtreasury": 8.0,
         "gold": 6.0, "oil": 4.0, "cash": 15.0}
    w.update(over)
    return w


class TestClassify(unittest.TestCase):
    def test_risk_on(self):
        self.assertEqual(classify("High", "Low"), "risk-on")
        self.assertEqual(classify("High", "Neutral"), "risk-on")

    def test_high_high_is_risk_off(self):
        # Inflation==High excludes risk-on AND triggers risk-off.
        self.assertEqual(classify("High", "High"), "risk-off")

    def test_risk_off(self):
        self.assertEqual(classify("Low", "Low"), "risk-off")
        self.assertEqual(classify("Low", "Neutral"), "risk-off")
        self.assertEqual(classify("Neutral", "High"), "risk-off")

    def test_neutral(self):
        self.assertEqual(classify("Neutral", "Neutral"), "neutral")
        self.assertEqual(classify("Neutral", "Low"), "neutral")
        self.assertEqual(classify("High", "Low"), "risk-on")


class TestOverlay(unittest.TestCase):
    def test_neutral_unchanged(self):
        w, b = apply_overlay(base_weights(), "neutral")
        self.assertEqual(w, base_weights())
        self.assertEqual(b, 0.0)

    def test_risk_on_adds_five(self):
        w, b = apply_overlay(base_weights(), "risk-on")
        self.assertAlmostEqual(sum(w[s] for s in ("sp500", "nasdaq", "russell")), 50.0)
        self.assertAlmostEqual(w["cash"], 10.0)
        self.assertAlmostEqual(sum(w.values()), 100.0)
        # pro-rata: sp500 share of equity preserved
        self.assertAlmostEqual(w["sp500"] / 50.0, 25.0 / 45.0)

    def test_risk_off_cuts_five(self):
        w, b = apply_overlay(base_weights(), "risk-off")
        self.assertAlmostEqual(sum(w[s] for s in ("sp500", "nasdaq", "russell")), 40.0)
        self.assertAlmostEqual(w["cash"], 20.0)

    def test_cash_floor_blocks(self):
        w, b = apply_overlay(base_weights(cash=3.0), "risk-on")
        self.assertGreaterEqual(w["cash"], 2.0 - 1e-9)
        self.assertAlmostEqual(sum(w.values()), 100.0)

    def test_family_cap_blocks(self):
        w = base_weights(sp500=35.0, nasdaq=17.0, russell=8.0, cash=5.0,
                         treasury2y=8.0, treasury10y=14.0, longtreasury=8.0,
                         gold=1.0, oil=4.0)
        self.assertAlmostEqual(sum(w[s] for s in ("sp500", "nasdaq", "russell")), 60.0)
        w2, b2 = apply_overlay(w, "risk-on")
        self.assertEqual(w2, w)  # fully blocked: nothing moves
        self.assertAlmostEqual(sum(w2.values()), 100.0)

    def test_zero_sleeve_stays_zero(self):
        w, b = apply_overlay(base_weights(oil=0.0, cash=19.0), "risk-on")
        self.assertEqual(w["oil"], 0.0)

    def test_sleeve_cap_single_pass(self):
        w = base_weights(sp500=34.0, cash=10.0, nasdaq=12.0, russell=8.0,
                         treasury2y=8.0, treasury10y=14.0, longtreasury=8.0,
                         gold=2.0, oil=4.0)
        w2, b2 = apply_overlay(w, "risk-on")
        self.assertLessEqual(w2["sp500"], 35.0 + 1e-9)
        self.assertAlmostEqual(sum(w2.values()), 100.0)


class TestDecide(unittest.TestCase):
    def test_supported(self):
        v, g = decide(0.2, 0.0, -1.0, 10.0, 0.5, True, -0.2, -1.0)
        self.assertEqual(v, "v66_tactical_overlay_candidate_supported")
        self.assertTrue(all(g.values()))

    def test_suggestive(self):
        v, _ = decide(0.3, -0.06, -1.0, 10.0, 0.5, True, -0.2, -1.0)
        self.assertEqual(v, "v66_tactical_overlay_candidate_suggestive")

    def test_not_supported(self):
        v, _ = decide(-1.0, -0.2, -5.0, 50.0, 0.9, True, -2.0, -5.0)
        self.assertEqual(v, "v66_tactical_overlay_not_supported")

    def test_moot_concentration(self):
        v, g = decide(-0.1, 0.0, 0.0, 5.0, 0.99, False, 0.0, 0.0)
        self.assertTrue(g["g5_concentration"])


if __name__ == "__main__":
    unittest.main()
