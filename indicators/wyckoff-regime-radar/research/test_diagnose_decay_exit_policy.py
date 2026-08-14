import unittest

import numpy as np
import pandas as pd

from diagnose_decay_exit_policy import (
    directional_return,
    first_warning_index,
    summarize_events,
    trade_excursions,
)


class DecayExitPolicyTests(unittest.TestCase):
    def test_directional_return_handles_long_and_short_exactly(self):
        self.assertAlmostEqual(directional_return(100.0, 110.0, 1.0), 0.10)
        self.assertAlmostEqual(directional_return(100.0, 90.0, -1.0), 100.0 / 90.0 - 1.0)
        self.assertIsNone(directional_return(0.0, 90.0, 1.0))

    def test_first_warning_requires_two_of_three_deterioration_signs(self):
        strength = np.array([50.0, 55.0, 60.0, 70.0, 65.0])
        entropy = np.array([0.4, 0.4, 0.4, 0.5, 0.6])
        opposite = np.array([20.0, 20.0, 20.0, 25.0, 30.0])
        # At bar 3 strength is still stronger than bar 0, but entropy and
        # opposite pressure both rose: exactly two warnings.
        self.assertEqual(first_warning_index(0, 4, strength, entropy, opposite), 3)

    def test_trade_excursions_stop_before_exit_open(self):
        frame = pd.DataFrame(
            {
                "open": [100.0, 100.0, 101.0, 102.0],
                "high": [101.0, 105.0, 110.0, 200.0],
                "low": [99.0, 95.0, 98.0, 1.0],
            }
        )
        mae, mfe = trade_excursions(frame, 1, 3, 1.0)
        self.assertAlmostEqual(mae, 0.05)
        self.assertAlmostEqual(mfe, 0.10)
        # Bar 3 extremes must not enter because exit occurs at bar 3 open.
        self.assertLess(mfe, 0.50)

    def test_summary_compares_same_events_without_threshold_fitting(self):
        rows = [
            {
                "warning_exit_better": True,
                "regime_change_exit_better": False,
                "bars_exited_earlier": 2,
                "warning_exit_return": 0.02,
                "regime_change_exit_return": 0.01,
                "warning_exit_advantage": 0.01,
                "post_warning_hold_return": -0.01,
                "warning_exit_mae": 0.01,
                "regime_change_exit_mae": 0.03,
                "mae_reduction_from_warning_exit": 0.02,
                "warning_exit_mfe": 0.04,
                "regime_change_exit_mfe": 0.05,
                "mfe_sacrificed_by_warning_exit": 0.01,
            },
            {
                "warning_exit_better": False,
                "regime_change_exit_better": True,
                "bars_exited_earlier": 4,
                "warning_exit_return": 0.01,
                "regime_change_exit_return": 0.03,
                "warning_exit_advantage": -0.02,
                "post_warning_hold_return": 0.02,
                "warning_exit_mae": 0.02,
                "regime_change_exit_mae": 0.02,
                "mae_reduction_from_warning_exit": 0.0,
                "warning_exit_mfe": 0.03,
                "regime_change_exit_mfe": 0.06,
                "mfe_sacrificed_by_warning_exit": 0.03,
            },
        ]
        summary = summarize_events(rows)
        self.assertEqual(summary["events"], 2)
        self.assertAlmostEqual(summary["warning_exit_better_rate"], 0.5)
        self.assertAlmostEqual(summary["median_bars_exited_earlier"], 3.0)
        self.assertAlmostEqual(summary["mean_warning_exit_advantage"], -0.005)


if __name__ == "__main__":
    unittest.main()
