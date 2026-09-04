"""Static contracts for Issue #68 Phase-B Pine lifecycle previews."""
from __future__ import annotations

import unittest
from pathlib import Path

import generate_issue68_phase_b_lifecycle_pine as gen


class Issue68PhaseBPineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = gen.HERE / gen.SOURCE_RELATIVE
        cls.visual = gen.generate(cls.source, "visual")
        cls.performance = gen.generate(cls.source, "performance")

    def test_visual_and_performance_differ_only_in_strategy_declaration(self):
        self.assertNotEqual(gen.VISUAL_DECL, gen.PERFORMANCE_DECL)
        self.assertEqual(gen.strip_declaration(self.visual), gen.strip_declaration(self.performance))

    def test_visual_uses_fixed_one_unit_and_next_bar_processing(self):
        self.assertIn("default_qty_type=strategy.fixed", self.visual)
        self.assertIn("default_qty_value=1", self.visual)
        self.assertIn("process_orders_on_close=false", self.visual)
        self.assertIn("pyramiding=0", self.visual)

    def test_performance_declaration_is_normalized_but_body_is_same(self):
        self.assertIn("initial_capital=100000", self.performance)
        self.assertIn("default_qty_type=strategy.percent_of_equity", self.performance)
        self.assertIn("default_qty_value=100", self.performance)
        self.assertIn("commission_value=0.02", self.performance)
        self.assertIn("process_orders_on_close=false", self.performance)

    def test_reuses_issue66_c2_price_only_lineage_without_parity_transport(self):
        for token in (
            "Issue #66 C-2",
            'volumeMode = "Off"',
            'mtfMode = "Off"',
            'divMode = "Off"',
            "breakoutRangeEvidence",
            "nonEndDnGate",
        ):
            self.assertIn(token, self.visual)
        for forbidden in ("PARITY formal_id", "D1B|", "screenshot parity checkpoints"):
            self.assertNotIn(forbidden, self.visual)

    def test_pine_body_locks_no_chase_and_opposite_family_semantics(self):
        self.assertIn(
            "issue68DirectTransitionLong = rangeBreakUp and issue68Stage == 2 and formalId[1] == 1",
            self.visual,
        )
        self.assertIn(
            "issue68DirectTransitionShort = rangeBreakDn and issue68Stage == 5 and formalId[1] == 4",
            self.visual,
        )
        self.assertIn("else if rangeBreakUp and issue68Stage == 1", self.visual)
        self.assertIn("else if rangeBreakDn and issue68Stage == 4", self.visual)
        self.assertIn(
            "issue68Pos == 1 and (issue68Stage == 4 or issue68Stage == 5 or issue68Stage == 6)",
            self.visual,
        )
        self.assertIn(
            "issue68Pos == -1 and (issue68Stage == 1 or issue68Stage == 2 or issue68Stage == 3)",
            self.visual,
        )

    def test_early_fail_and_same_bar_reopen_block_are_present(self):
        self.assertIn("issue68EntryAge <= confirmBars", self.visual)
        self.assertIn("issue68ClosedThisBar := true", self.visual)
        self.assertIn("issue68Pos == 0 and not issue68ClosedThisBar", self.visual)

    def test_visual_review_markers_default_on_as_preregistered(self):
        self.assertIn('showIssue68Arms = input.bool(true, "顯示 ARM 等待確認"', self.visual)
        self.assertIn('showIssue68TradeMarks = input.bool(true, "顯示 LONG / SHORT / FAIL / EXIT"', self.visual)
        self.assertIn('showIssue68Protection = input.bool(true, "顯示前三根 Early Fail 保護線"', self.visual)
        self.assertIn('showIssue68FreshBreaks = input.bool(false', self.visual)
        self.assertIn('showIssue68AddCandidates = input.bool(false', self.visual)


if __name__ == "__main__":
    unittest.main()
