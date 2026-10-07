#!/usr/bin/env python3
"""Issue #176 — stdlib unittest for frozen hardening primitives."""

import math
import unittest

from issue_176_backbone import (
    sp500_tr_recon, oil_investable, dividend_wedge,
    mean, biased_sd, pearson, mae, compound, largest_disagreements,
)


class TestBuilders(unittest.TestCase):
    def test_sp500_recon(self):
        # price 100 -> 110 (+10%) + div accrual (3.0/12)/100 = +0.25% => 10.25%
        self.assertAlmostEqual(sp500_tr_recon(100.0, 110.0, 3.0), 0.1025)
        self.assertTrue(math.isnan(sp500_tr_recon(0.0, 1.0, 3.0)))
        self.assertTrue(math.isnan(sp500_tr_recon(100.0, 110.0, float("nan"))))

    def test_oil_investable(self):
        # flat front + 12% bill => ~1% collateral
        self.assertAlmostEqual(oil_investable(50.0, 50.0, 12.0), 0.01)
        # +10% excess, no collateral
        self.assertAlmostEqual(oil_investable(50.0, 55.0, 0.0), 0.10)
        self.assertTrue(math.isnan(oil_investable(50.0, 55.0, float("nan"))))

    def test_wedge(self):
        self.assertAlmostEqual(dividend_wedge(100.0, 101.0, 100.0, 100.5), 0.01 - 0.005)
        self.assertTrue(math.isnan(dividend_wedge(0.0, 1.0, 1.0, 1.0)))


class TestMetrics(unittest.TestCase):
    def test_pearson(self):
        self.assertAlmostEqual(pearson([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]), 1.0)
        self.assertTrue(math.isnan(pearson([1.0, 1.0], [1.0, 2.0])))

    def test_mae(self):
        self.assertAlmostEqual(mae([0.01, 0.02], [0.02, 0.02]), 0.005)

    def test_compound(self):
        self.assertAlmostEqual(compound([0.10, -0.10]), -0.01)

    def test_disagreements(self):
        rows = largest_disagreements(["a", "b", "c"], [0.0, 0.0, 0.0], [0.01, -0.05, 0.02], k=2)
        self.assertEqual([r[0] for r in rows], ["b", "c"])


if __name__ == "__main__":
    unittest.main()
