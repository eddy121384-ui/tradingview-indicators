#!/usr/bin/env python3
"""Issue #183 — stdlib unittest for frozen repair primitives."""

import unittest

from issue_183_repair import (
    assert_matrix_row, decide_178, decide_180, decide_182,
)


def good_row(**over):
    w = {"sp500": 25.0, "nasdaq": 12.0, "russell": 8.0, "treasury2y": 8.0,
         "treasury10y": 14.0, "longtreasury": 8.0, "gold": 3.0, "oil": 4.0,
         "cash": 18.0}
    w.update(over)
    return w


class TestAsserts(unittest.TestCase):
    def test_good_row(self):
        self.assertEqual(assert_matrix_row("G_Neutral/I_Neutral", good_row()), [])

    def test_sum(self):
        self.assertTrue(any("sum" in e for e in
                            assert_matrix_row("S", good_row(cash=19.0))))

    def test_leverage(self):
        # three sleeves at their frozen caps + residual Cash must exceed 100%
        w = good_row(sp500=35.0, nasdaq=20.0, russell=15.0, cash=2.0)
        errs = assert_matrix_row("S", w)
        self.assertTrue(any("gross" in e for e in errs))
        self.assertAlmostEqual(sum(w.values()), 109.0)

    def test_negative(self):
        self.assertTrue(any("negative" in e for e in
                            assert_matrix_row("S", good_row(gold=-1.0))))

    def test_zero_cell(self):
        self.assertTrue(any("zero-cell" in e for e in
                            assert_matrix_row("G_Low/I_Low",
                                              good_row(oil=1.0, cash=17.0))))

    def test_sleeve_cap(self):
        self.assertTrue(any("sleeve-cap" in e for e in
                            assert_matrix_row("S", good_row(sp500=36.0, cash=17.0))))

    def test_cash_bounds(self):
        self.assertTrue(any("cash-min" in e for e in
                            assert_matrix_row("S", good_row(cash=1.0, gold=8.0))))
        self.assertTrue(any("cash-max" in e for e in
                            assert_matrix_row("S", good_row(cash=61.0, gold=-37.0))))


class TestVerdicts(unittest.TestCase):
    def test_178_revalidated(self):
        self.assertEqual(decide_178(0.2, -1.0, 1.0),
                         "state_weight_policy_candidate_revalidated")

    def test_178_invalidated(self):
        self.assertEqual(decide_178(0.2, -11.0, 1.0),
                         "state_weight_policy_candidate_invalidated_by_repair")

    def test_178_limitations(self):
        self.assertEqual(decide_178(2.5, -1.0, 1.0),
                         "state_weight_policy_candidate_revalidated_with_limitations")

    def test_180(self):
        self.assertEqual(decide_180(0, False, 1.0),
                         "tradable_implementation_revalidated")
        self.assertEqual(decide_180(1, False, 1.0),
                         "tradable_implementation_revalidated_with_limitations")
        self.assertEqual(decide_180(3, False, 1.0),
                         "tradable_implementation_invalidated_by_repair")

    def test_182_supported(self):
        v, g = decide_182(0.2, 0.0, -1.0, 10.0, 0.5, True, -0.2, -1.0)
        self.assertEqual(v, "v66_tactical_overlay_candidate_supported")
        self.assertTrue(all(g.values()))

    def test_182_not_supported(self):
        v, _ = decide_182(-1.0, -0.2, -5.0, 50.0, 0.9, True, -2.0, -5.0)
        self.assertEqual(v, "v66_tactical_overlay_not_supported")


if __name__ == "__main__":
    unittest.main()
