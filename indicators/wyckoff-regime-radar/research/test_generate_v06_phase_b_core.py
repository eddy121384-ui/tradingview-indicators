#!/usr/bin/env python3

from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from generate_v06_phase_b_core import (
    NEW_DIAGNOSTIC_TAIL,
    NEW_INERTIA_BLOCK,
    OLD_DIAGNOSTIC_TAIL,
    OLD_INERTIA_BLOCK,
    load_phase_b_namespace,
    render_phase_b_source,
)


class V06PhaseBCoreGeneratorTests(unittest.TestCase):
    def test_generator_changes_only_persistence_layer_on_top_of_phase_a(self) -> None:
        source = render_phase_b_source()
        self.assertNotIn(OLD_INERTIA_BLOCK, source)
        self.assertNotIn(OLD_DIAGNOSTIC_TAIL, source)
        self.assertEqual(source.count(NEW_INERTIA_BLOCK), 1)
        self.assertEqual(source.count(NEW_DIAGNOSTIC_TAIL), 1)
        self.assertIn("soft_no_break_low_score", source)
        self.assertIn("range_break_up_strength", source)
        self.assertIn("confirmed = candidate", source)
        self.assertNotIn("confirmed = display_id", source)

    def test_generated_phase_b_core_executes_and_emits_stale_pressure(self) -> None:
        compute = load_phase_b_namespace()["compute_price_only"]
        n = 900
        x = np.arange(n, dtype=float)
        close = 1.10 + 0.0015 * np.sin(x / 11.0) + 0.000003 * x
        open_ = np.r_[close[0], close[:-1]]
        high = np.maximum(open_, close) + 0.0010
        low = np.minimum(open_, close) - 0.0010
        frame = pd.DataFrame({"open": open_, "high": high, "low": low, "close": close})

        result = compute(frame)
        self.assertIn("stale_pressure_bars", result.columns)
        self.assertIn("stale_pressure_reason", result.columns)
        self.assertTrue((result["stale_pressure_bars"] >= 0).all())
        self.assertTrue(result["stale_pressure_reason"].isin([0, 1, 2, 3]).all())
        self.assertTrue(result["formal_id"].isin(range(7)).all())


if __name__ == "__main__":
    unittest.main()
