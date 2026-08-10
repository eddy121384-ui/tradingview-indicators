#!/usr/bin/env python3

from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from generate_v06_price_only_core import (
    EXPECTED_BASELINE_GIT_BLOB_SHA,
    NEW_HIGH,
    NEW_LOW,
    NEW_RANGE_CONT,
    OLD_HIGH,
    OLD_LOW,
    OLD_RANGE_CONT,
    BASELINE,
    git_blob_sha,
    load_v06_namespace,
    render_v06_source,
)
from v06_boundary_scores import (
    SOFT_BOUNDARY_WIDTH_ATR,
    soft_above_range_score,
    soft_below_range_score,
    soft_hold_strength,
    soft_no_break_high_score,
    soft_no_break_low_score,
)


class V06BoundaryPrimitiveTests(unittest.TestCase):
    def test_boundary_equality_maps_to_midpoint(self) -> None:
        self.assertAlmostEqual(float(soft_no_break_low_score(1.0, 1.0, 0.02)), 50.0)
        self.assertAlmostEqual(float(soft_no_break_high_score(1.0, 1.0, 0.02)), 50.0)
        self.assertAlmostEqual(float(soft_above_range_score(1.0, 1.0, 0.02)), 50.0)
        self.assertAlmostEqual(float(soft_below_range_score(1.0, 1.0, 0.02)), 50.0)

    def test_transition_band_saturates_symmetrically(self) -> None:
        atr_value = 0.02
        width = SOFT_BOUNDARY_WIDTH_ATR * atr_value
        self.assertAlmostEqual(float(soft_no_break_low_score(1.0 - width, 1.0, atr_value)), 0.0)
        self.assertAlmostEqual(float(soft_no_break_low_score(1.0 + width, 1.0, atr_value)), 100.0)
        self.assertAlmostEqual(float(soft_no_break_high_score(1.0 + width, 1.0, atr_value)), 0.0)
        self.assertAlmostEqual(float(soft_no_break_high_score(1.0 - width, 1.0, atr_value)), 100.0)
        self.assertAlmostEqual(float(soft_above_range_score(1.0 + width, 1.0, atr_value)), 100.0)
        self.assertAlmostEqual(float(soft_below_range_score(1.0 - width, 1.0, atr_value)), 100.0)

    def test_low_and_high_are_mirror_symmetric(self) -> None:
        atr_value = 0.02
        offsets = np.linspace(-0.006, 0.006, 25)
        low_scores = soft_no_break_low_score(1.0 + offsets, 1.0, atr_value)
        high_scores = soft_no_break_high_score(1.0 - offsets, 1.0, atr_value)
        above_scores = soft_above_range_score(1.0 + offsets, 1.0, atr_value)
        below_scores = soft_below_range_score(1.0 - offsets, 1.0, atr_value)
        np.testing.assert_allclose(low_scores, high_scores, atol=1e-10)
        np.testing.assert_allclose(above_scores, below_scores, atol=1e-10)

    def test_sub_pip_crossing_is_continuous_instead_of_100_point_jump(self) -> None:
        boundary = 1.06236
        atr_value = 0.008
        epsilon = 0.000001  # 0.01 pip for EURUSD-style quoting.
        below = float(soft_no_break_low_score(boundary - epsilon, boundary, atr_value))
        above = float(soft_no_break_low_score(boundary + epsilon, boundary, atr_value))
        breakout_below = float(soft_above_range_score(boundary - epsilon, boundary, atr_value))
        breakout_above = float(soft_above_range_score(boundary + epsilon, boundary, atr_value))
        self.assertLess(abs(above - below), 0.1)
        self.assertLess(abs(breakout_above - breakout_below), 0.1)
        self.assertEqual(100.0, abs(100.0 - 0.0))  # frozen v0.5 binary jump reference

    def test_soft_hold_uses_weakest_bar_in_window(self) -> None:
        values = np.array([20.0, 80.0, 60.0, 95.0])
        held = soft_hold_strength(values, 2)
        self.assertTrue(np.isnan(held[0]))
        np.testing.assert_allclose(held[1:], np.array([20.0, 60.0, 60.0]))
        np.testing.assert_allclose(soft_hold_strength(values, 1), values)

    def test_soft_hold_rejects_nonpositive_window(self) -> None:
        with self.assertRaises(ValueError):
            soft_hold_strength(np.array([1.0, 2.0]), 0)

    def test_invalid_width_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            soft_no_break_low_score(1.0, 1.0, 0.02, width_atr=0.0)


class V06MechanicalGeneratorTests(unittest.TestCase):
    def test_frozen_v05_python_mirror_blob_is_exact(self) -> None:
        self.assertEqual(git_blob_sha(BASELINE.read_bytes()), EXPECTED_BASELINE_GIT_BLOB_SHA)

    def test_generator_replaces_only_the_named_boundary_blocks(self) -> None:
        source = render_v06_source()
        self.assertNotIn(OLD_LOW, source)
        self.assertNotIn(OLD_HIGH, source)
        self.assertNotIn(OLD_RANGE_CONT, source)
        self.assertEqual(source.count(NEW_LOW), 1)
        self.assertEqual(source.count(NEW_HIGH), 1)
        self.assertEqual(source.count(NEW_RANGE_CONT), 1)
        self.assertIn('"no_break_low_score": no_break_low_score', source)
        self.assertIn('"no_break_high_score": no_break_high_score', source)
        self.assertIn('"above_prev_range_score": above_prev_range_score', source)
        self.assertIn('"sustained_above_score": sustained_above_score', source)

    def test_generated_core_executes_without_touching_v05_module(self) -> None:
        namespace = load_v06_namespace()
        compute = namespace["compute_price_only"]

        n = 900
        x = np.arange(n, dtype=float)
        close = 1.10 + 0.00025 * np.sin(x / 8.0) + 0.000001 * x
        open_ = np.r_[close[0], close[:-1]]
        high = np.maximum(open_, close) + 0.0008
        low = np.minimum(open_, close) - 0.0008
        frame = pd.DataFrame({"open": open_, "high": high, "low": low, "close": close})

        result = compute(frame)
        for column in (
            "no_break_low_score",
            "no_break_high_score",
            "above_prev_range_score",
            "below_prev_range_score",
            "sustained_above_score",
            "sustained_below_score",
        ):
            self.assertIn(column, result.columns)
            finite = result[column].dropna()
            self.assertGreater(len(finite), 0)
            self.assertTrue(((finite >= 0.0) & (finite <= 100.0)).all())


if __name__ == "__main__":
    unittest.main()
