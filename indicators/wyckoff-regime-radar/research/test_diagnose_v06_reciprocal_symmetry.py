from __future__ import annotations

from types import SimpleNamespace
import unittest

import numpy as np
import pandas as pd

from diagnose_v06_reciprocal_symmetry_v2 import (
    STAGE_MIRROR,
    boolean_metrics,
    lifecycle_v2,
    reciprocal_ohlc,
)
from generate_v06_phase_b_core import render_phase_b_source


class ReciprocalSymmetryAuditTest(unittest.TestCase):
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

    def test_sparse_event_metric_uses_jaccard_not_only_bar_agreement(self) -> None:
        left = np.array([False, False, True, False, False])
        right = np.array([False, False, False, True, False])
        result = boolean_metrics(left, right, warmup=0)
        self.assertEqual(result["bar_agreement"], 0.6)
        self.assertEqual(result["event_jaccard"], 0.0)

    def test_frozen_source_contains_explicit_bull_bear_asymmetries(self) -> None:
        source = render_phase_b_source()
        self.assertIn("breakout_range_evidence = np.nan_to_num(recent_range_break_up_strength, nan=0.0) * 0.70", source)
        self.assertIn("breakdown_range_evidence = np.nan_to_num(recent_range_break_dn_strength, nan=0.0) * 0.85", source)
        self.assertIn("breakout_recent_range_gate = np.nan_to_num(recent_range_break_up_strength, nan=0.0) / 100.0 * 0.85", source)
        self.assertIn("explicit_recent_breakdown_gate = np.nan_to_num(recent_range_break_dn_strength, nan=0.0) / 100.0 * 0.90", source)
        self.assertIn("recent_ma_cross_dn & (panic_heat_dn >= cfg.orange_level) & (structure_weak >= 50.0)", source)

    def test_lifecycle_shell_is_symmetric_on_mirrored_synthetic_states(self) -> None:
        original = pd.DataFrame({
            "formal_id": [1, 2, 2, 2, 4],
            "range_break_up": [1, 0, 0, 0, 0],
            "range_break_dn": [0, 0, 0, 0, 0],
            "range_high_break": [1.00, 1.00, 1.00, 1.00, 1.00],
            "range_low_break": [0.90, 0.90, 0.90, 0.90, 0.90],
        })
        inverse = pd.DataFrame({
            "formal_id": [4, 5, 5, 5, 1],
            "range_break_up": [0, 0, 0, 0, 0],
            "range_break_dn": [1, 0, 0, 0, 0],
            "range_high_break": [1.20, 1.20, 1.20, 1.20, 1.20],
            "range_low_break": [1.00, 1.00, 1.00, 1.00, 1.00],
        })
        config = SimpleNamespace(confirm_bars=3)
        a = lifecycle_v2(original, np.array([1.10, 1.20, 1.25, 1.30, 1.25]), config, 0)
        b = lifecycle_v2(inverse, np.array([0.90, 0.80, 0.78, 0.75, 0.80]), config, 0)
        self.assertTrue(np.array_equal(b["position"], -a["position"]))
        self.assertTrue(np.array_equal(a["entry_long"], b["entry_short"]))
        self.assertTrue(np.array_equal(a["opposite_exit_long"], b["opposite_exit_short"]))


if __name__ == "__main__":
    unittest.main()
