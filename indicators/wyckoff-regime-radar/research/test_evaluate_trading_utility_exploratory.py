from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from evaluate_trading_utility_exploratory import (  # noqa: E402
    PIP_SIZE,
    WYCKOFF_RESPONSE,
    donchian55_targets,
    evaluate_targets,
    momentum60_targets,
    sma200_targets,
)


class ExploratoryTradingUtilityTests(unittest.TestCase):
    def make_frame(self, closes: list[float]) -> pd.DataFrame:
        close = np.asarray(closes, dtype=float)
        return pd.DataFrame(
            {
                "date": pd.bdate_range("2020-01-01", periods=len(close)).date,
                "open": close,
                "high": close + 0.01,
                "low": close - 0.01,
                "close": close,
            }
        )

    def test_frozen_response_map_is_exact(self) -> None:
        self.assertEqual(WYCKOFF_RESPONSE, {0: 0.0, 1: 0.0, 2: 1.0, 3: 1.0, 4: 0.0, 5: -1.0, 6: -1.0})

    def test_signal_at_origin_earns_only_next_bar_return(self) -> None:
        frame = self.make_frame([1.00, 1.10, 0.99])
        target = np.array([1.0, -1.0, 0.0])
        metrics, daily = evaluate_targets(frame, target, 0, 2, pip_size=0.0001, cost_pips=0.0)
        self.assertAlmostEqual(float(daily.iloc[0]["gross_return"]), 0.10)
        self.assertAlmostEqual(float(daily.iloc[1]["gross_return"]), 0.10)
        self.assertEqual(metrics["observations"], 2)

    def test_turnover_cost_counts_flip_as_two_units(self) -> None:
        frame = self.make_frame([1.00, 1.00, 1.00, 1.00])
        target = np.array([0.0, 1.0, -1.0, -1.0])
        _, daily = evaluate_targets(frame, target, 1, 3, pip_size=0.0001, cost_pips=1.0)
        self.assertAlmostEqual(float(daily.iloc[0]["turnover"]), 1.0)
        self.assertAlmostEqual(float(daily.iloc[0]["cost_return"]), 0.0001)
        self.assertAlmostEqual(float(daily.iloc[1]["turnover"]), 2.0)
        self.assertAlmostEqual(float(daily.iloc[1]["cost_return"]), 0.0002)

    def test_evaluator_never_uses_return_after_split_end(self) -> None:
        frame = self.make_frame([1.0, 1.1, 1.2, 100.0])
        target = np.ones(4)
        _, daily = evaluate_targets(frame, target, 0, 2, pip_size=0.0001, cost_pips=0.0)
        self.assertEqual(list(daily["next_date"]), [str(frame.iloc[1]["date"]), str(frame.iloc[2]["date"])])
        self.assertLess(float(daily["gross_return"].max()), 0.2)

    def test_baseline_warmups_are_flat(self) -> None:
        frame = self.make_frame(list(np.linspace(1.0, 2.0, 250)))
        self.assertTrue(np.all(sma200_targets(frame)[:199] == 0.0))
        self.assertTrue(np.all(momentum60_targets(frame)[:60] == 0.0))
        self.assertTrue(np.all(donchian55_targets(frame)[:55] == 0.0))

    def test_pip_sizes_are_predeclared(self) -> None:
        self.assertEqual(PIP_SIZE["EURUSD"], 0.0001)
        self.assertEqual(PIP_SIZE["USDJPY"], 0.01)


if __name__ == "__main__":
    unittest.main()
