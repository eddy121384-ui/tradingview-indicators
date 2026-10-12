#!/usr/bin/env python3
"""Issue #188 unit tests (stdlib only, synthetic data; no parent returns)."""
import math
import unittest

from issue_188_primitives import (
    apply_verdict, bootstrap_cagr_diff_ci, cdar95, drawdowns,
    favorable_percentile, mulberry32, shapley_2factor, ulcer_index,
    underwater_duration, upi, worst_rolling_12m,
)


class TestDrawdownMetrics(unittest.TestCase):
    def test_flat_zero(self):
        self.assertEqual(drawdowns([0.0] * 12), [0.0] * 12)
        self.assertEqual(ulcer_index([0.0] * 12), 0.0)
        self.assertIsNone(upi(0.05, 0.02, 0.0))
        self.assertEqual(underwater_duration([0.01] * 12)["months"], 0)

    def test_single_crash(self):
        r = [0.0, 0.0, -0.5, 0.0, 0.0]  # -50% then flat
        dd = drawdowns(r)
        self.assertAlmostEqual(min(dd), -0.5, places=12)
        self.assertAlmostEqual(ulcer_index(r),
                               100 * math.sqrt((0.25 + 0.25 + 0.25) / 5), places=9)
        u = underwater_duration(r)
        self.assertEqual(u["months"], 3)
        self.assertTrue(u["censored"])

    def test_cdar95_null_small(self):
        self.assertIsNone(cdar95([0.01] * 10))

    def test_cdar95_shape(self):
        r = [-0.01] * 100
        v = cdar95(r)
        self.assertTrue(v is not None and v > 0)

    def test_worst_rolling(self):
        r = [0.0] * 6 + [-0.5] + [0.0] * 11
        w = worst_rolling_12m(r)
        self.assertAlmostEqual(w, -0.5, places=12)
        self.assertIsNone(worst_rolling_12m([0.01] * 11))

    def test_upi(self):
        self.assertAlmostEqual(upi(0.08, 0.02, 10.0), 0.6, places=12)


class TestPercentile(unittest.TestCase):
    def test_basic(self):
        self.assertAlmostEqual(favorable_percentile(5, [1, 2, 5, 9]), 62.5)
        self.assertAlmostEqual(favorable_percentile(0, [1, 2, 3]), 0.0)
        self.assertAlmostEqual(favorable_percentile(9, [1, 2, 3]), 100.0)

    def test_nan(self):
        self.assertTrue(math.isnan(favorable_percentile(float("nan"), [1])))


class TestRngBootstrap(unittest.TestCase):
    def test_mulberry_deterministic(self):
        a = mulberry32(188)
        b = mulberry32(188)
        self.assertEqual([a() for _ in range(5)], [b() for _ in range(5)])
        self.assertTrue(0 <= a() < 1)

    def test_bootstrap_zero_diff(self):
        dh = [0.01] * 48
        lo, hi = bootstrap_cagr_diff_ci(dh, list(dh), block=24, reps=200, seed=188)
        self.assertAlmostEqual(lo, 0.0, places=12)
        self.assertAlmostEqual(hi, 0.0, places=12)

    def test_bootstrap_positive(self):
        dh = [0.02] * 48
        ct = [0.01] * 48
        lo, hi = bootstrap_cagr_diff_ci(dh, ct, block=24, reps=200, seed=188)
        self.assertGreater(lo, 0)


class TestShapleyVerdict(unittest.TestCase):
    def test_shapley(self):
        pe, ae, it = shapley_2factor(10, 4, 6, 8)
        self.assertAlmostEqual(pe, 0.5 * ((10 - 6) + (8 - 4)))
        self.assertAlmostEqual(ae, 0.5 * ((10 - 8) + (6 - 4)))
        self.assertAlmostEqual(it, (10 - 8) - (6 - 4))

    def _flags(self, **kw):
        f = {f"G{i}": True for i in range(1, 9)}
        f["assessable"] = True
        f.update(kw)
        return f

    def test_tree(self):
        self.assertEqual(apply_verdict(self._flags()),
                         "deep_history_macro_information_supported")
        self.assertEqual(apply_verdict(self._flags(assessable=False)),
                         "deep_history_evidence_mixed_or_inconclusive")
        self.assertEqual(apply_verdict(self._flags(G4=False)),
                         "deep_history_reducible_to_simpler_defense")
        self.assertEqual(apply_verdict(self._flags(G6=False)),
                         "deep_history_exposure_or_availability_explained")
        self.assertEqual(apply_verdict(self._flags(G8=False)),
                         "deep_history_evidence_mixed_or_inconclusive")


if __name__ == "__main__":
    unittest.main()
