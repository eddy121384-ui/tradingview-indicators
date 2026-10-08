#!/usr/bin/env python3
"""Issue #178 — stdlib unittest for frozen weight-policy primitives."""

import unittest

from issue_178_policy import (
    BASELINE, MULT, state_weights, round_largest_remainder, confirm_state,
    perf_stats, compound,
)


class TestBaselineMult(unittest.TestCase):
    def test_baseline_sums(self):
        self.assertAlmostEqual(sum(BASELINE.values()) + 15.0, 100.0)

    def test_mult_order(self):
        self.assertEqual(MULT["0"], 0.0)
        self.assertTrue(0.0 < MULT["Low"] < MULT["Neutral"] < MULT["High"])
        self.assertEqual(MULT["Neutral"], 1.0)


class TestWeights(unittest.TestCase):
    def test_all_neutral(self):
        tiers = {s: "Neutral" for s in BASELINE}
        w, binds = state_weights(tiers, set(BASELINE), "neutral")
        self.assertAlmostEqual(sum(w.values()), 100.0)
        # family caps bind: equity 45 ok; rates 30 ok; real 10 ok -> cash 15
        self.assertAlmostEqual(w["cash"], 15.0)
        self.assertEqual(binds, [])

    def test_zero_stays_zero(self):
        tiers = {s: "Neutral" for s in BASELINE}
        tiers["oil"] = "0"
        w, _ = state_weights(tiers, set(BASELINE), "neutral")
        self.assertEqual(w["oil"], 0.0)

    def test_unavailable_dropped(self):
        tiers = {s: "Neutral" for s in BASELINE}
        avail = set(BASELINE) - {"oil"}
        w, _ = state_weights(tiers, avail, "neutral")
        self.assertEqual(w["oil"], 0.0)
        self.assertAlmostEqual(sum(w.values()), 100.0)

    def test_cash_min_high_bias(self):
        # all High -> huge raw -> caps bind, cash floored at min? cash_raw tiny
        tiers = {s: "High" for s in BASELINE}
        w, binds = state_weights(tiers, set(BASELINE), "high")
        self.assertGreaterEqual(w["cash"], 20.0 - 1e-9)
        self.assertAlmostEqual(sum(w.values()), 100.0, places=6)
        self.assertTrue(binds)

    def test_rounding(self):
        w = {"sp500": 25.0, "nasdaq": 12.0, "russell": 8.0, "treasury2y": 8.0,
             "treasury10y": 14.0, "longtreasury": 8.0, "gold": 6.0, "oil": 4.0,
             "cash": 15.0}
        r = round_largest_remainder(w, set())
        self.assertAlmostEqual(sum(r.values()), 100.0)
        self.assertEqual(r["oil"], 4.0)


class TestConfirm(unittest.TestCase):
    def test_confirmed(self):
        self.assertEqual(confirm_state(["A", "B", "B"]), "B")

    def test_hold(self):
        self.assertEqual(confirm_state(["B", "C"]), "B")

    def test_single(self):
        self.assertEqual(confirm_state(["A"]), "A")


class TestPerf(unittest.TestCase):
    def test_flat(self):
        s = perf_stats([0.01] * 12, [0.0] * 12)
        self.assertAlmostEqual(s["cagr"], (1.01 ** 12) - 1.0)
        self.assertAlmostEqual(s["maxdd"], 0.0)
        self.assertAlmostEqual(s["pos_frac"], 1.0)

    def test_compound(self):
        self.assertAlmostEqual(compound([0.10, -0.10]), -0.01)


if __name__ == "__main__":
    unittest.main()
