from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from diagnose_color_first_th_overlay import (
    early_damage_pulses,
    formal_color_direction,
    managed_color_signal,
    strategy_metrics,
)


class ColorFirstTransitionHealthOverlayTests(unittest.TestCase):
    def test_formal_color_direction_uses_frozen_stage_families(self) -> None:
        model = pd.DataFrame({"formal_id": [0, 1, 2, 3, 4, 5, 6, np.nan]})
        got = formal_color_direction(model)
        np.testing.assert_array_equal(got, np.array([0, 1, 1, 1, -1, -1, -1, 0]))

    def test_early_damage_is_first_lead_loss_inside_plus3(self) -> None:
        th = pd.DataFrame(
            {
                "transition_health_tracked": [True, True, True, True, False],
                "transition_health_lead_held": [True, True, False, False, False],
                "transition_health_watch_age": [0, 1, 2, 3, 0],
                "transition_health_direction": [1, 1, 1, 1, 0],
                "transition_health_healthy_pulse": [False] * 5,
            }
        )
        got = early_damage_pulses(th)
        np.testing.assert_array_equal(got, np.array([False, False, True, False, False]))

    def test_managed_signal_blocks_then_later_healthy_rerisks(self) -> None:
        color = np.array([1, 1, 1, 1, 1, 1, -1, -1])
        th = pd.DataFrame(
            {
                "transition_health_tracked": [True, True, True, False, True, True, False, False],
                "transition_health_lead_held": [True, True, False, False, True, True, False, False],
                "transition_health_watch_age": [0, 1, 2, 0, 0, 3, 0, 0],
                "transition_health_direction": [1, 1, 1, 0, 1, 1, 0, 0],
                "transition_health_healthy_pulse": [False, False, False, False, False, True, False, False],
            }
        )
        got, counts = managed_color_signal(color, th)
        np.testing.assert_array_equal(got, np.array([1, 1, 0, 0, 0, 1, -1, -1]))
        self.assertEqual(counts["early_damage_blocks"], 1)
        self.assertEqual(counts["healthy_rerisks"], 1)

    def test_healthy_without_prior_block_does_not_delay_color_entry(self) -> None:
        color = np.array([1, 1, 1, 1])
        th = pd.DataFrame(
            {
                "transition_health_tracked": [True, True, True, True],
                "transition_health_lead_held": [True, True, True, True],
                "transition_health_watch_age": [0, 1, 2, 3],
                "transition_health_direction": [1, 1, 1, 1],
                "transition_health_healthy_pulse": [False, False, False, True],
            }
        )
        got, counts = managed_color_signal(color, th)
        np.testing.assert_array_equal(got, color)
        self.assertEqual(counts["early_damage_blocks"], 0)
        self.assertEqual(counts["healthy_rerisks"], 0)

    def test_color_family_flip_resets_old_block(self) -> None:
        color = np.array([1, 1, 1, -1, -1])
        th = pd.DataFrame(
            {
                "transition_health_tracked": [True, True, True, False, False],
                "transition_health_lead_held": [True, True, False, False, False],
                "transition_health_watch_age": [0, 1, 2, 0, 0],
                "transition_health_direction": [1, 1, 1, 0, 0],
                "transition_health_healthy_pulse": [False] * 5,
            }
        )
        got, _ = managed_color_signal(color, th)
        np.testing.assert_array_equal(got, np.array([1, 1, 0, -1, -1]))

    def test_strategy_metrics_apply_signal_with_one_bar_lag(self) -> None:
        frame = pd.DataFrame(
            {
                "date": pd.date_range("2026-01-01", periods=3, freq="D"),
                "close": [100.0, 110.0, 121.0],
            }
        )
        # Signal becomes long only at the second close, so only the third
        # close-to-close return may earn the position.
        metrics = strategy_metrics(frame, np.array([0, 1, 1]))
        self.assertEqual(metrics["observations"], 2)
        self.assertAlmostEqual(float(metrics["exposure_share"]), 0.5)
        self.assertGreater(float(metrics["gross_ann_return"]), 0.0)
        self.assertGreater(float(metrics["annualized_turnover"]), 0.0)


if __name__ == "__main__":
    unittest.main()
