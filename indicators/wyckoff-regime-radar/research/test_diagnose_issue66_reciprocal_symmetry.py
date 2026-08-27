from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from diagnose_issue66_reciprocal_symmetry import (
    STAGE_MIRROR,
    boolean_metrics,
    build_report,
    reciprocal_ohlc,
)
from generate_v06_phase_b_core import render_phase_b_source


class Issue66ReciprocalSymmetryTest(unittest.TestCase):
    def test_reciprocal_ohlc_swaps_high_and_low(self) -> None:
        frame = pd.DataFrame({
            "date": ["2026-01-01"],
            "open": [2.0],
            "high": [4.0],
            "low": [1.0],
            "close": [2.5],
        })
        out = reciprocal_ohlc(frame)
        self.assertAlmostEqual(out.loc[0, "open"], 0.5)
        self.assertAlmostEqual(out.loc[0, "high"], 1.0)
        self.assertAlmostEqual(out.loc[0, "low"], 0.25)
        self.assertAlmostEqual(out.loc[0, "close"], 0.4)

    def test_stage_mirror_is_an_involution(self) -> None:
        stages = np.arange(7, dtype=int)
        self.assertTrue(np.array_equal(STAGE_MIRROR[STAGE_MIRROR[stages]], stages))

    def test_sparse_event_metric_uses_jaccard(self) -> None:
        left = np.array([False, False, True, False, False])
        right = np.array([False, False, False, True, False])
        result = boolean_metrics(left, right, warmup=0)
        self.assertEqual(result["bar_agreement"], 0.6)
        self.assertEqual(result["event_jaccard"], 0.0)

    def test_frozen_v06_source_still_contains_known_non_isomorphisms(self) -> None:
        source = render_phase_b_source()
        self.assertIn(
            "breakout_range_evidence = np.nan_to_num(recent_range_break_up_strength, nan=0.0) * 0.70",
            source,
        )
        self.assertIn(
            "breakdown_range_evidence = np.nan_to_num(recent_range_break_dn_strength, nan=0.0) * 0.85",
            source,
        )
        self.assertIn(
            "breakout_recent_range_gate = np.nan_to_num(recent_range_break_up_strength, nan=0.0) / 100.0 * 0.85",
            source,
        )
        self.assertIn(
            "explicit_recent_breakdown_gate = np.nan_to_num(recent_range_break_dn_strength, nan=0.0) / 100.0 * 0.90",
            source,
        )
        self.assertIn(
            "recent_ma_cross_dn & (panic_heat_dn >= cfg.orange_level) & (structure_weak >= 50.0)",
            source,
        )
        self.assertIn(
            "breakout_markup_gate = breakout_gate * structure_strong_gate * non_end_up_gate",
            source,
        )
        self.assertIn(
            "breakdown_markdown_gate = explicit_breakdown_gate * gate(panic_heat_dn, 40.0, 80.0) * structure_weak_gate",
            source,
        )

    def test_clean_issue66_branch_reproduces_frozen_issue61_baseline(self) -> None:
        report = build_report()
        aggregate = report["aggregate"]
        self.assertAlmostEqual(aggregate["range_up_to_inverse_down_jaccard"], 1.0, places=12)
        self.assertAlmostEqual(aggregate["range_down_to_inverse_up_jaccard"], 1.0, places=12)
        self.assertAlmostEqual(aggregate["ma_up_to_inverse_down_jaccard"], 0.924322701665135, places=12)
        self.assertAlmostEqual(aggregate["ma_down_to_inverse_up_jaccard"], 0.9363896747200815, places=12)
        self.assertAlmostEqual(aggregate["candidate_display_mirror_agreement"], 0.7431610942249239, places=12)
        self.assertAlmostEqual(aggregate["formal_stage_mirror_agreement"], 0.761094224924012, places=12)
        self.assertEqual(report["issue"], 66)
        self.assertEqual(report["phase"], "A")
        self.assertIn("stage_vector_mirrors", next(iter(report["pairs"].values())))
        self.assertNotIn("lifecycle", next(iter(report["pairs"].values())))


if __name__ == "__main__":
    unittest.main()
