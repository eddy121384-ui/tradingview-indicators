from __future__ import annotations

import unittest

from diagnose_issue66_phase_b1_representation import build_report
from generate_issue66_phase_b1_representation_core import render_phase_b1_source


class Issue66PhaseB1RepresentationTests(unittest.TestCase):
    def test_generator_changes_representation_but_preserves_known_directional_asymmetries(self) -> None:
        source = render_phase_b1_source()
        self.assertIn("ISSUE #66 PHASE B-1 — RECIPROCAL-SAFE REPRESENTATION", source)
        self.assertIn("ma_log = rolling_sma(log_price, cfg.ma_len)", source)
        self.assertIn("ma_cross_up = crossover(log_price, ma_log)", source)
        self.assertIn("atr_pct = sym_atr * 100.0", source)
        self.assertIn("range_width_log = np.log(range_high) - np.log(range_low)", source)
        self.assertIn("ma_spread_atr = safe_div(ma_log - maturity_ma_log, sym_atr)", source)

        # Frozen for this slice: these known directional asymmetries must still exist.
        self.assertIn("recent_range_break_up_strength, nan=0.0) * 0.70", source)
        self.assertIn("recent_range_break_dn_strength, nan=0.0) * 0.85", source)
        self.assertIn("recent_range_break_up_strength, nan=0.0) / 100.0 * 0.85", source)
        self.assertIn("recent_range_break_dn_strength, nan=0.0) / 100.0 * 0.90", source)
        self.assertIn("panic_heat_dn >= cfg.orange_level", source)
        self.assertIn("structure_weak >= 50.0", source)

    def test_frozen_phase_a_baseline_is_still_exactly_reproduced(self) -> None:
        report = build_report()
        a = report["baseline"]["aggregate"]
        self.assertAlmostEqual(a["ma_up_to_inverse_down_jaccard"], 0.924322701665135, places=12)
        self.assertAlmostEqual(a["ma_down_to_inverse_up_jaccard"], 0.9363896747200815, places=12)
        self.assertAlmostEqual(a["candidate_display_mirror_agreement"], 0.7431610942249239, places=12)
        self.assertAlmostEqual(a["formal_stage_mirror_agreement"], 0.761094224924012, places=12)

    def test_b1_passes_preregistered_representation_gate(self) -> None:
        report = build_report()
        b = report["baseline"]["aggregate"]
        v = report["variant"]["aggregate"]
        self.assertTrue(report["primary_gate_pass"])
        self.assertGreaterEqual(v["ma_up_to_inverse_down_jaccard"], 0.999999)
        self.assertGreaterEqual(v["ma_down_to_inverse_up_jaccard"], 0.999999)
        self.assertLess(v["representation_numeric_mae"], b["representation_numeric_mae"])


if __name__ == "__main__":
    unittest.main()
