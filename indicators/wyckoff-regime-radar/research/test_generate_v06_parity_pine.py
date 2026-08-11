#!/usr/bin/env python3

from __future__ import annotations

import unittest

from generate_v06_parity_pine_fixed import (
    EXPECTED_SOURCE_BLOB_SHA,
    SOURCE,
    git_blob_sha,
    render_v06_parity_source,
)


class V06PineParityGeneratorTests(unittest.TestCase):
    def test_frozen_v05_pine_blob_is_unchanged(self) -> None:
        self.assertEqual(git_blob_sha(SOURCE.read_bytes()), EXPECTED_SOURCE_BLOB_SHA)

    def test_generated_harness_contains_frozen_v06_decisions(self) -> None:
        source = render_v06_parity_source()
        self.assertIn("f_v06_soft_no_break_low", source)
        self.assertIn("recentRangeBreakUpStrength", source)
        self.assertIn("staleLimit = confirmBars * 2", source)
        self.assertIn("weakChallenger", source)
        self.assertIn("v06AccFamily = probAcc + probReacc", source)
        self.assertIn("v06DistFamily = probDist + probRedist", source)
        self.assertIn("v06RegimeMargin", source)
        self.assertIn("NOT confidence/probability", source)

    def test_old_visual_layer_is_removed_and_research_tables_exist(self) -> None:
        source = render_v06_parity_source()
        self.assertNotIn("// Visuals", source)
        self.assertIn("var table v06Table", source)
        self.assertIn("var table v06Self", source)
        self.assertIn("NoBreak@boundary", source)
        self.assertIn("Stale limit", source)

    def test_research_modes_are_forced_off(self) -> None:
        source = render_v06_parity_source()
        self.assertIn('string volumeMode = "Off"', source)
        self.assertIn('string mtfMode = "Off"', source)
        self.assertIn('string divMode = "Off"', source)
        self.assertIn('string witnessStageBiasMode = "Conservative"', source)

    def test_plot_budget_is_small(self) -> None:
        source = render_v06_parity_source()
        self.assertEqual(source.count("plot("), 12)
        self.assertLess(source.count("plot("), 64)


if __name__ == "__main__":
    unittest.main()
