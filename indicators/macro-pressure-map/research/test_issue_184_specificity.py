#!/usr/bin/env python3
"""Issue #184 — unit tests for frozen specificity primitives (stdlib only).

Synthetic data only. No parent returns, no C/D performance inspected.
"""
import math
import unittest

from issue_184_specificity import (
    BUDGET, CASH_MAX, CASH_MIN, D_PP, constant_w, downside_vol, metrics,
    overlay_w, rank_higher, rank_lower, shift_signals, specificity_verdict,
    turnover_ann,
)

BASE = {"sp500": 25.0, "nasdaq": 12.0, "russell": 8.0, "cash": 15.0,
        "treasury2y": 8.0, "treasury10y": 14.0, "longtreasury": 8.0,
        "gold": 6.0, "oil": 4.0}


class TestOverlayW(unittest.TestCase):
    def test_risk_off_cuts_5_pro_rata(self):
        w = overlay_w(BASE, "risk-off")
        self.assertAlmostEqual(sum(w[s] for s in ("sp500", "nasdaq", "russell")),
                               45.0 - 5.0, places=9)
        self.assertAlmostEqual(w["cash"], 20.0, places=9)
        # pro-rata: ratios preserved
        self.assertAlmostEqual(w["sp500"] / w["nasdaq"], 25.0 / 12.0, places=9)

    def test_risk_on_adds_5_pro_rata(self):
        w = overlay_w(BASE, "risk-on")
        self.assertAlmostEqual(sum(w[s] for s in ("sp500", "nasdaq", "russell")),
                               50.0, places=9)
        self.assertAlmostEqual(w["cash"], 10.0, places=9)

    def test_neutral_noop(self):
        w = overlay_w(BASE, "neutral")
        self.assertEqual(w, BASE)

    def test_zero_sleeve_stays_zero(self):
        b = dict(BASE)
        b["oil"] = 0.0
        w = overlay_w(b, "risk-off")
        self.assertEqual(w["oil"], 0.0)
        w2 = overlay_w(b, "risk-on")
        self.assertEqual(w2["oil"], 0.0)

    def test_gross_preserved(self):
        for sig in ("risk-on", "risk-off", "neutral"):
            w = overlay_w(BASE, sig)
            tot = sum(w[s] for s in ("sp500", "nasdaq", "russell", "treasury2y",
                                     "treasury10y", "longtreasury", "gold", "oil",
                                     "cash"))
            self.assertAlmostEqual(tot, 100.0, places=9)


class TestConstantW(unittest.TestCase):
    def test_constant_cut_matches_d(self):
        w = constant_w(BASE)
        E0 = 45.0
        self.assertAlmostEqual(E0 - sum(w[s] for s in ("sp500", "nasdaq", "russell")),
                               D_PP, places=9)
        self.assertAlmostEqual(w["cash"], 15.0 + D_PP, places=9)

    def test_no_v66_info_same_every_month(self):
        # C builder must be signal-invariant: same output regardless of signal
        self.assertEqual(constant_w(BASE), constant_w(BASE))

    def test_zeros_kept(self):
        b = dict(BASE)
        b["oil"] = 0.0
        self.assertEqual(constant_w(b)["oil"], 0.0)


class TestShifts(unittest.TestCase):
    def test_all_nonzero_shifts_preserve_counts(self):
        sigs = ["risk-on"] * 35 + ["risk-off"] * 163 + ["neutral"] * 34
        n = len(sigs)
        self.assertEqual(n, 232)
        for k in (1, 2, 115, 231):
            sh = shift_signals(sigs, k)
            self.assertEqual(len(sh), n)
            self.assertEqual(sorted(sh), sorted(sigs))
        # k=0 is identity (not a placebo, excluded by construction)
        self.assertEqual(shift_signals(sigs, 0), sigs)
        # distinct non-trivial shifts differ (sequence is not periodic with small period)
        self.assertNotEqual(shift_signals(sigs, 1), shift_signals(sigs, 2))

    def test_shift_count(self):
        self.assertEqual(232 - 1, 231)


class TestMetrics(unittest.TestCase):
    def test_flat_zero(self):
        m = metrics([0.0] * 12, [0.0] * 12)
        self.assertEqual(m["n"], 12)
        self.assertAlmostEqual(m["cagr"], 0.0, places=12)
        self.assertAlmostEqual(m["maxdd"], 0.0, places=12)

    def test_turnover_first_month_zero(self):
        s = [dict(BASE), dict(BASE)]
        self.assertAlmostEqual(turnover_ann(s), 0.0, places=12)

    def test_downside_only_negatives(self):
        self.assertAlmostEqual(downside_vol([0.01, 0.02]), 0.0, places=12)


class TestRanksVerdict(unittest.TestCase):
    def test_ranks(self):
        self.assertAlmostEqual(rank_higher(5, [1, 2, 5, 9]), 75.0)
        self.assertAlmostEqual(rank_lower(1, [1, 2, 5, 9]), 100.0)

    def test_verdict_tree(self):
        self.assertEqual(
            specificity_verdict(True, True, True, True, True, True),
            "v66_overlay_specific_information_supported")
        self.assertEqual(
            specificity_verdict(True, True, False, False, True, True),
            "v66_overlay_risk_control_supported_but_timing_not_specific")
        self.assertEqual(
            specificity_verdict(True, False, False, True, True, True),
            "v66_overlay_specificity_suggestive")
        self.assertEqual(
            specificity_verdict(False, True, True, True, True, True),
            "v66_overlay_not_supported_after_controls")
        self.assertEqual(
            specificity_verdict(True, True, True, True, False, True),
            "v66_overlay_not_supported_after_controls")


if __name__ == "__main__":
    unittest.main()
