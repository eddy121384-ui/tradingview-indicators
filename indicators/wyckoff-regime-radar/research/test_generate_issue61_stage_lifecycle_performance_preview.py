from __future__ import annotations

import unittest

from generate_issue61_stage_lifecycle_performance_preview import (
    PERFORMANCE_DECL,
    VISUAL_DECL,
    build,
)
from generate_issue61_stage_lifecycle_strategy_preview import build as build_visual


class Issue61PerformancePreviewTest(unittest.TestCase):
    def test_normalized_performance_declaration(self) -> None:
        text = build()
        self.assertIn(PERFORMANCE_DECL, text)
        self.assertNotIn(VISUAL_DECL, text)
        self.assertIn("initial_capital=100000", text)
        self.assertIn("currency=currency.USD", text)
        self.assertIn("default_qty_type=strategy.percent_of_equity", text)
        self.assertIn("default_qty_value=50", text)
        self.assertIn("commission_value=0.02", text)
        self.assertIn("process_orders_on_close=false", text)
        self.assertIn("margin_long=100", text)
        self.assertIn("margin_short=100", text)

    def test_trade_logic_is_byte_identical_after_declaration(self) -> None:
        visual = build_visual()
        perf = build()
        visual_body = visual.split("\n", 2)[2]
        perf_body = perf.split("\n", 2)[2]
        self.assertEqual(visual_body, perf_body)

    def test_performance_preview_keeps_human_review_semantics(self) -> None:
        text = build()
        for token in (
            "issue61DirectTransitionLong",
            "issue61DirectTransitionShort",
            "issue61EarlyFailLong",
            "issue61OppositeExitLong",
            "issue61AddLongCandidate",
            'strategy.entry("Long"',
            'strategy.entry("Short"',
            'strategy.close("Long"',
            'strategy.close("Short"',
        ):
            self.assertIn(token, text)
        self.assertNotIn("RE-LONG", text)
        self.assertNotIn("RE-SHORT", text)


if __name__ == "__main__":
    unittest.main()
