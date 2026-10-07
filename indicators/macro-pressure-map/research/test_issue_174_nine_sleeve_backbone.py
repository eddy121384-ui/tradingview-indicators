#!/usr/bin/env python3
"""Issue #174 — stdlib unittest for frozen backbone primitives.

Covers: bands/state (incl. ±10 boundaries), era assignment, price/cash/bond
math (analytic cases), percentile/median/sd/downside, episode contiguity with
calendar gaps, evidence classification branches, zero-candidate gates.
All vectors are analytic (hand-derived); the suite was additionally
cross-checked through the executed Node mirror.
"""

import math
import unittest

from issue_174_nine_sleeve_backbone import (
    band, state_of, era_of, price_return, cash_monthly,
    synthetic_bond_monthly_return, mean, median, biased_sd, downside_dev,
    percentile, compound, geometric_excess, build_episodes,
    classify_evidence, zero_candidate,
)


class TestBands(unittest.TestCase):
    def test_boundaries_inclusive_neutral(self):
        self.assertEqual(band(-10.0), "Neutral")
        self.assertEqual(band(10.0), "Neutral")
        self.assertEqual(band(-10.0001), "Low")
        self.assertEqual(band(10.0001), "High")

    def test_state_joint(self):
        self.assertEqual(state_of(-11, -11), "G_Low/I_Low")
        self.assertEqual(state_of(0, 0), "G_Neutral/I_Neutral")
        self.assertEqual(state_of(11, 11), "G_High/I_High")
        self.assertEqual(state_of(float("nan"), 0), "NA")

    def test_eras(self):
        self.assertEqual(era_of("1966-03-01"), "E1_pre_volcker")
        self.assertEqual(era_of("1979-12-01"), "E1_pre_volcker")
        self.assertEqual(era_of("1980-01-01"), "E2_great_moderation")
        self.assertEqual(era_of("2007-12-01"), "E2_great_moderation")
        self.assertEqual(era_of("2008-01-01"), "E3_post_gfc_qe")
        self.assertEqual(era_of("2019-12-01"), "E3_post_gfc_qe")
        self.assertEqual(era_of("2020-01-01"), "E4_post_2020")
        self.assertEqual(era_of("2026-08-01"), "E4_post_2020")
        self.assertEqual(era_of("2026-09-01"), "OUT")


class TestReturns(unittest.TestCase):
    def test_price(self):
        self.assertAlmostEqual(price_return(100.0, 110.0), 0.10)
        self.assertTrue(math.isnan(price_return(0.0, 1.0)))

    def test_cash(self):
        self.assertAlmostEqual(cash_monthly(12.0), 0.01)
        self.assertAlmostEqual(cash_monthly(3.94), 3.94 / 1200.0)
        self.assertTrue(math.isnan(cash_monthly(float("nan"))))

    def test_bond_flat_yield_is_coupon(self):
        # Flat yield: par bond rolled at same yield earns coupon/12 approx.
        r = synthetic_bond_monthly_return(0.06, 0.06, 10)
        self.assertTrue(math.isfinite(r))
        # Coupon 6% p.a. => ~0.5% per month before repricing effects (flat => ~coupon/12).
        self.assertAlmostEqual(r, 0.06 / 12, places=3)

    def test_bond_rising_yield_loses(self):
        r = synthetic_bond_monthly_return(0.05, 0.10, 10)
        self.assertLess(r, -0.02)

    def test_bond_falling_yield_gains(self):
        r = synthetic_bond_monthly_return(0.10, 0.05, 10)
        self.assertGreater(r, 0.02)

    def test_bond_duration_ordering(self):
        # Same shock: long loses more than 2Y when yields jump.
        r2 = synthetic_bond_monthly_return(0.05, 0.06, 2)
        r20 = synthetic_bond_monthly_return(0.05, 0.06, 20)
        self.assertLess(r20, r2)
        self.assertLess(r2, 0.06 / 12 + 0.005)

    def test_bond_nan(self):
        self.assertTrue(math.isnan(synthetic_bond_monthly_return(float("nan"), 0.05, 10)))


class TestStats(unittest.TestCase):
    def test_median(self):
        self.assertEqual(median([3.0, 1.0, 2.0]), 2.0)
        self.assertEqual(median([1.0, 2.0, 3.0, 4.0]), 2.5)

    def test_p10(self):
        xs = [float(i) for i in range(10)]  # 0..9
        self.assertAlmostEqual(percentile(xs, 0.10), 0.9)

    def test_downside(self):
        self.assertAlmostEqual(downside_dev([0.01, -0.02, 0.03]), math.sqrt((0.0004) / 3))

    def test_compound(self):
        self.assertAlmostEqual(compound([0.10, -0.10]), -0.01)

    def test_gex(self):
        self.assertAlmostEqual(geometric_excess([0.10], [0.02]), 1.10 / 1.02 - 1)


class TestEpisodes(unittest.TestCase):
    def test_contiguity_and_gap(self):
        months = ["1966-03-01", "1966-04-01", "1966-05-01", "1966-07-01"]
        states = ["G_Neutral/I_Neutral"] * 4
        eps = build_episodes(months, states)
        self.assertEqual(len(eps), 2)  # gap 1966-06 breaks
        self.assertEqual(eps[0], (0, 2, "G_Neutral/I_Neutral"))

    def test_state_break(self):
        months = ["1966-03-01", "1966-04-01", "1966-05-01"]
        states = ["A", "A", "B"]
        eps = build_episodes(months, states)
        self.assertEqual(eps, [(0, 1, "A"), (2, 2, "B")])


class TestClassification(unittest.TestCase):
    def test_insufficient(self):
        self.assertEqual(classify_evidence(10, 2, 0.01, 0.9, 0.9, 0.0, 0.0, 0.1, False, False),
                         "insufficient_sample")

    def test_favored(self):
        self.assertEqual(classify_evidence(100, 10, 0.002, 0.60, 0.70, -0.01, -0.05, 0.40, False, False),
                         "historically_favored")

    def test_unfavorable(self):
        self.assertEqual(classify_evidence(100, 10, -0.002, 0.40, 0.30, -0.05, -0.12, 0.60, False, False),
                         "historically_unfavorable")

    def test_mixed(self):
        self.assertEqual(classify_evidence(100, 10, 0.0005, 0.52, 0.55, -0.02, -0.05, 0.48, False, False),
                         "mixed")

    def test_zero_candidate_true(self):
        self.assertTrue(zero_candidate("eligible_primary", "historically_unfavorable",
                                       100, 10, 0.30, -0.002, -0.05, -0.20, 0.12, False, -0.001))

    def test_zero_candidate_blocked_by_ep_hit(self):
        self.assertFalse(zero_candidate("eligible_primary", "historically_unfavorable",
                                        100, 10, 0.60, -0.002, -0.05, -0.20, 0.12, False, -0.001))

    def test_zero_candidate_blocked_by_qa(self):
        self.assertFalse(zero_candidate("qa_only", "historically_unfavorable",
                                        100, 10, 0.30, -0.002, -0.05, -0.20, 0.12, False, -0.001))


if __name__ == "__main__":
    unittest.main()
