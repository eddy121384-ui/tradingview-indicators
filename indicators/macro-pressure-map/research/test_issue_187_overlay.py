#!/usr/bin/env python3
"""Issue #187 unit tests (stdlib only, synthetic data)."""
import math
import unittest

from issue_187_overlay import (
    BUDGET, apply_gates, downside_vol, entry_signal, exit_check, low_episodes,
    metrics, size_overlay, turnover_ann,
)

BASE = {"sp500": 25.0, "nasdaq": 12.0, "russell": 8.0, "cash": 15.0,
        "treasury2y": 8.0, "treasury10y": 14.0, "longtreasury": 8.0,
        "gold": 6.0, "oil": 4.0}
LOWLOW = {"sp500": 25.19, "nasdaq": 12.09, "russell": 8.05, "cash": 5.0,
          "treasury2y": 12.54, "treasury10y": 21.95, "longtreasury": 12.54,
          "gold": 5.64, "oil": 0.0}


class TestSignal(unittest.TestCase):
    def test_fires(self):
        self.assertTrue(entry_signal(-14, -12, -11, 0, 5))

    def test_level_not_low(self):
        self.assertFalse(entry_signal(-14, -12, -9, 0, 5))

    def test_not_strict(self):
        self.assertFalse(entry_signal(-14, -12, -12, 0, 5))
        self.assertFalse(entry_signal(-11, -12, -11, 0, 5))

    def test_inflation_high(self):
        self.assertFalse(entry_signal(-14, -12, -11, 0, 11))

    def test_inflation_accel(self):
        self.assertFalse(entry_signal(-14, -12, -11, 0, 6))  # +6 > 5
        self.assertTrue(entry_signal(-14, -12, -11, 0, 5))   # +5 ok


class TestEpisodes(unittest.TestCase):
    def test_one_per_run(self):
        g = [-5, -11, -12, -13, -8, -11, -9]
        self.assertEqual(low_episodes(g), [(1, 3), (5, 5)])

    def test_nan_breaks(self):
        g = [-11, float("nan"), -12, -13]
        self.assertEqual(low_episodes(g), [(0, 0), (2, 3)])


class TestSizing(unittest.TestCase):
    def test_full_5pp(self):
        w, add, blocked, reason = size_overlay(BASE)
        self.assertAlmostEqual(add, 5.0, places=9)
        self.assertAlmostEqual(blocked, 0.0, places=9)
        self.assertEqual(reason, "full")
        tot = sum(w[s] for s in ("sp500", "nasdaq", "russell", "treasury2y",
                                 "treasury10y", "longtreasury", "gold", "oil",
                                 "cash"))
        self.assertAlmostEqual(tot, 100.0, places=9)
        self.assertAlmostEqual(w["cash"], 10.0, places=9)

    def test_low_cash_partial(self):
        w, add, blocked, reason = size_overlay(LOWLOW)
        self.assertAlmostEqual(add, 3.0, places=9)  # 5 - 2 floor
        self.assertAlmostEqual(blocked, 2.0, places=9)
        self.assertEqual(reason, "cash_floor")
        self.assertGreaterEqual(w["cash"], 2.0 - 1e-9)

    def test_zeros_caps_kept(self):
        w, *_ = size_overlay(LOWLOW)
        self.assertEqual(w["oil"], 0.0)
        for s in ("sp500", "nasdaq", "russell"):
            self.assertLessEqual(w[s], {"sp500": 35, "nasdaq": 20, "russell": 15}[s] + 1e-9)
        for s in ("treasury2y", "treasury10y", "longtreasury", "gold"):
            self.assertAlmostEqual(w[s], LOWLOW[s], places=9)


class TestExits(unittest.TestCase):
    def test_A(self):
        self.assertEqual(exit_check(-5, -4, -6, 0, 0, 40, 45, 45, 2), ["A"])

    def test_B_high(self):
        self.assertIn("B", exit_check(-5, -4, -6, 11, 9, 40, 40, 40, 2))

    def test_B_accel(self):
        self.assertIn("B", exit_check(-5, -4, -6, 9, 3, 40, 40, 40, 2))

    def test_C(self):
        self.assertEqual(exit_check(-4, -4, -3, 0, 0, 40, 40, 40, 2), ["C"])

    def test_C_needs_two(self):
        self.assertNotIn("C", exit_check(-5, -3, -4, 0, 0, 40, 40, 40, 2))

    def test_D(self):
        self.assertIn("D", exit_check(-5, -4, -6, 0, 0, 45, 40, 45, 2))

    def test_E(self):
        self.assertEqual(exit_check(-5, -4, -6, 0, 0, 40, 40, 40, 6), ["E"])
        self.assertNotIn("E", exit_check(-5, -4, -6, 0, 0, 40, 40, 40, 5))

    def test_nan_safe(self):
        nan = float("nan")
        self.assertEqual(exit_check(nan, nan, nan, nan, nan, 40, 40, 40, 1), [])


class TestGates(unittest.TestCase):
    def base(self, **kw):
        g = {f"G{i}": True for i in range(1, 9)}
        g.update(n_act=10, overlap_y=60)
        g.update(kw)
        return g

    def test_supported(self):
        self.assertEqual(apply_gates(self.base()),
                         "early_recovery_equity_overlay_supported")

    def test_not_assessable(self):
        self.assertEqual(apply_gates(self.base(n_act=2)),
                         "early_recovery_equity_overlay_not_assessable")

    def test_suggestive(self):
        self.assertEqual(apply_gates(self.base(G5=False, G7=False)),
                         "early_recovery_equity_overlay_suggestive_with_limitations")

    def test_not_supported_g2(self):
        self.assertEqual(apply_gates(self.base(G2=False)),
                         "early_recovery_equity_overlay_not_supported")

    def test_metrics_smoke(self):
        m = metrics([0.01] * 12, [0.001] * 12)
        self.assertEqual(m["n"], 12)
        self.assertGreater(m["cagr"], 0.1)
        self.assertAlmostEqual(turnover_ann([dict(BASE), dict(BASE)]), 0.0, places=12)
        self.assertEqual(downside_vol([0.01, 0.02]), 0.0)


if __name__ == "__main__":
    unittest.main()
