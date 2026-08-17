import unittest

import pandas as pd

from diagnose_transition_health_price_outcomes import price_path_metrics, summarize_group


class TransitionHealthPriceOutcomeTests(unittest.TestCase):
    def test_long_price_path_metrics(self):
        frame = pd.DataFrame(
            {
                "close": [100.0, 101.0, 102.0, 103.0],
                "high": [100.5, 102.0, 103.0, 104.0],
                "low": [99.5, 99.0, 100.0, 101.0],
            }
        )
        got = price_path_metrics(frame, 0, 1.0, 3)
        self.assertIsNotNone(got)
        self.assertAlmostEqual(got["aligned_return"], 0.03)
        self.assertAlmostEqual(got["mfe"], 0.04)
        self.assertAlmostEqual(got["mae"], 0.01)

    def test_short_price_path_metrics_are_direction_aligned(self):
        frame = pd.DataFrame(
            {
                "close": [100.0, 99.0, 98.0, 97.0],
                "high": [100.5, 101.0, 100.0, 99.0],
                "low": [99.5, 98.0, 96.0, 95.0],
            }
        )
        got = price_path_metrics(frame, 0, -1.0, 3)
        self.assertIsNotNone(got)
        self.assertAlmostEqual(got["aligned_return"], 0.03)
        self.assertAlmostEqual(got["mfe"], 0.05)
        self.assertAlmostEqual(got["mae"], 0.01)

    def test_price_metrics_fail_closed_near_tail(self):
        frame = pd.DataFrame(
            {
                "close": [100.0, 101.0],
                "high": [101.0, 102.0],
                "low": [99.0, 100.0],
            }
        )
        self.assertIsNone(price_path_metrics(frame, 0, 1.0, 2))

    def test_summary_uses_only_valid_horizon_rows(self):
        rows = [
            {
                "aligned_return_5": 0.02,
                "mfe_5": 0.03,
                "mae_5": 0.01,
                "hit_5": True,
                "aligned_return_10": None,
                "mfe_10": None,
                "mae_10": None,
                "hit_10": None,
                "aligned_return_20": None,
                "mfe_20": None,
                "mae_20": None,
                "hit_20": None,
            },
            {
                "aligned_return_5": -0.01,
                "mfe_5": 0.01,
                "mae_5": 0.02,
                "hit_5": False,
                "aligned_return_10": None,
                "mfe_10": None,
                "mae_10": None,
                "hit_10": None,
                "aligned_return_20": None,
                "mfe_20": None,
                "mae_20": None,
                "hit_20": None,
            },
        ]
        got = summarize_group(rows)
        h5 = got["horizons"]["5"]
        self.assertEqual(h5["valid_events"], 2)
        self.assertAlmostEqual(h5["mean_aligned_return"], 0.005)
        self.assertAlmostEqual(h5["hit_rate"], 0.5)
        self.assertAlmostEqual(h5["mean_mfe_minus_mae"], 0.005)


if __name__ == "__main__":
    unittest.main()
