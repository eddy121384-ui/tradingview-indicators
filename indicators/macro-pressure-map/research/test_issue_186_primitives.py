#!/usr/bin/env python3
"""Issue #186 — unit tests for frozen turning-lag primitives (stdlib only).

Synthetic data only. No parent prices, no allocation timeline, no outcomes.
"""
import unittest

from issue_186_primitives import (
    ALREADY_DEFENSIVE, ALREADY_EXPOSED, MOVE_PP, THRESH_20, WINDOW,
    drawdown_before_action, extract_bears, match_peak, match_trough, median,
    month_diff, pct, rebound_fraction, turning_verdict,
)


def mk_months(y0, n):
    out = []
    y, m = y0
    for _ in range(n):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m > 12:
            m, y = 1, y + 1
    return out


class TestExtractor(unittest.TestCase):
    def test_single_bear(self):
        ms = mk_months((2000, 1), 24)
        # peak idx2=100, trough idx8=70 (-30%), recovery idx15=100
        cl = [90, 95, 100, 98, 92, 85, 78, 72, 70, 75, 82, 88, 93, 97, 99, 100,
              101, 102, 103, 104, 105, 106, 107, 108]
        ev = extract_bears(ms, cl)
        self.assertEqual(len(ev), 1)
        self.assertEqual(ms[ev[0]["peak_i"]], "2000-03")
        self.assertEqual(ms[ev[0]["trough_i"]], "2000-09")
        self.assertEqual(ms[ev[0]["rec_i"]], "2001-04")
        self.assertAlmostEqual(ev[0]["severity"], -0.30, places=9)
        self.assertFalse(ev[0]["censored"])

    def test_no_bear(self):
        ms = mk_months((2000, 1), 12)
        cl = [100 + i for i in range(12)]  # steady climb, max DD 0
        self.assertEqual(extract_bears(ms, cl), [])

    def test_correction_below_threshold_ignored(self):
        ms = mk_months((2000, 1), 12)
        cl = [100, 102, 105, 100, 95, 90, 88, 92, 98, 104, 108, 112]  # max DD 88/105=16.2%
        self.assertEqual(extract_bears(ms, cl, thresh=0.20), [])
        self.assertEqual(len(extract_bears(ms, cl, thresh=0.10)), 1)

    def test_censored_no_recovery(self):
        ms = mk_months((2000, 1), 12)
        cl = [100, 105, 110, 100, 90, 80, 75, 78, 82, 85, 88, 90]  # never retakes 110
        ev = extract_bears(ms, cl)
        self.assertEqual(len(ev), 1)
        self.assertTrue(ev[0]["censored"])
        self.assertIsNone(ev[0]["rec_i"])
        self.assertEqual(ms[ev[0]["trough_i"]], "2000-07")

    def test_non_overlapping_two_bears(self):
        ms = mk_months((2000, 1), 36)
        cl = ([100, 110, 120, 100, 90, 80, 85, 95, 105, 115, 125, 130]
              + [140, 150, 130, 110, 100, 95, 100, 110, 125, 140, 155, 160]
              + [165, 170, 175, 180, 185, 190, 195, 200, 205, 210, 215, 220])
        ev = extract_bears(ms, cl)
        self.assertEqual(len(ev), 2)
        self.assertLess(ev[0]["rec_i"], ev[1]["peak_i"])

    def test_tie_peak_earliest(self):
        ms = mk_months((2000, 1), 10)
        cl = [100, 100, 95, 85, 79, 82, 90, 100, 105, 110]  # DD 21% from 100
        ev = extract_bears(ms, cl)
        self.assertEqual(len(ev), 1)
        self.assertEqual(ms[ev[0]["peak_i"]], "2000-01")


class TestMatching(unittest.TestCase):
    def test_peak_early(self):
        em = [f"2000-{m:02d}-01" for m in range(1, 13)]
        E = [50] * 5 + [40] * 7  # -10pp in June (idx5)
        lab, lag, act = match_peak("2000-08", em, E)
        self.assertEqual(lab, "early_protection")
        self.assertEqual(lag, -2)
        self.assertEqual(act, "2000-06-01")

    def test_peak_late(self):
        em = [f"2000-{m:02d}-01" for m in range(1, 13)]
        E = [50] * 9 + [40] * 3  # -10pp in Oct (idx9)
        lab, lag, act = match_peak("2000-08", em, E)
        self.assertEqual(lab, "late_protection")
        self.assertEqual(lag, 2)

    def test_peak_reversal_disqualifies(self):
        em = [f"2000-{m:02d}-01" for m in range(1, 13)]
        E = [50] * 5 + [40] + [50] * 6  # cut then fully reversed by Aug
        lab, lag, act = match_peak("2000-08", em, E)
        self.assertNotEqual(lab, "early_protection")

    def test_peak_already_defensive(self):
        em = [f"2000-{m:02d}-01" for m in range(1, 13)]
        E = [25] * 12
        self.assertEqual(match_peak("2000-08", em, E)[0], "already_defensive")

    def test_trough_late(self):
        em = [f"2000-{m:02d}-01" for m in range(1, 13)]
        E = [30] * 9 + [40] * 3
        lab, lag, act = match_trough("2000-08", em, E)
        self.assertEqual(lab, "late_re-risk")
        self.assertEqual(lag, 2)

    def test_trough_already_exposed(self):
        em = [f"2000-{m:02d}-01" for m in range(1, 13)]
        E = [55] * 12
        self.assertEqual(match_trough("2000-08", em, E)[0], "already_exposed")

    def test_pivot_held_over_12mo_not_timely(self):
        em = [f"1999-{m:02d}-01" for m in range(1, 13)] + [f"2000-{m:02d}-01" for m in range(1, 13)]
        E = [50] * 3 + [40] * 21  # cut 21 months before T
        lab, lag, act = match_peak("2000-08", em, E)
        self.assertNotEqual(lab, "early_protection")


class TestMetrics(unittest.TestCase):
    def test_drawdown_fraction(self):
        self.assertAlmostEqual(drawdown_before_action(100, 90, 70), 10 / 30)
        self.assertAlmostEqual(drawdown_before_action(100, 105, 70), -5 / 30)

    def test_rebound_fraction(self):
        self.assertAlmostEqual(rebound_fraction(85, 70, 100), 15 / 30)

    def test_month_diff(self):
        self.assertEqual(month_diff("2000-08", "2000-06"), -2)
        self.assertEqual(month_diff("2000-08", "2000-10"), 2)
        self.assertEqual(month_diff("2007-10", "2009-03"), 17)

    def test_median_pct(self):
        self.assertEqual(median([3, 1, 2]), 2)
        self.assertEqual(median([4, 1, 2, 3]), 2.5)
        self.assertTrue(median([]) != median([]))  # NaN

    def test_verdict_tree(self):
        self.assertEqual(turning_verdict(5, 8, 0.7, 8), "deep_history_timing_materially_late")
        self.assertEqual(turning_verdict(1, 3, 0.4, 8), "deep_history_timing_acceptable_with_limitations")
        self.assertEqual(turning_verdict(1, 8, 0.4, 8), "deep_history_timing_mixed_by_cycle")
        self.assertEqual(turning_verdict(1, 3, 0.4, 2), "deep_history_timing_not_assessable")


if __name__ == "__main__":
    unittest.main()
