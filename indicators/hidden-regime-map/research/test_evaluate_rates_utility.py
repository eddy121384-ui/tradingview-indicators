#!/usr/bin/env python3

from __future__ import annotations

import math
import unittest

import numpy as np
import pandas as pd

import evaluate_rates_utility as utility


class RatesUtilityTests(unittest.TestCase):
    def test_state_duration_mapping_orders_risk(self) -> None:
        means = np.zeros((3, len(utility.FEATURE_NAMES)), dtype=float)
        change = utility.FEATURE_NAMES.index("level_change_bp")
        vol = utility.FEATURE_NAMES.index("level_vol_20_bp")
        means[0, change] = 1.0
        means[1, change] = -1.0
        means[2, vol] = 0.5

        mapping, scores = utility.state_duration_mapping(means, 3)

        self.assertEqual(mapping[1], "TLT")
        self.assertEqual(mapping[2], "IEF")
        self.assertEqual(mapping[0], "SHY")
        self.assertEqual(len(scores), 3)

    def test_k4_mapping_uses_cash_for_highest_risk(self) -> None:
        means = np.zeros((4, len(utility.FEATURE_NAMES)), dtype=float)
        change = utility.FEATURE_NAMES.index("level_change_bp")
        means[:, change] = [-2.0, -1.0, 0.0, 2.0]
        mapping, _ = utility.state_duration_mapping(means, 4)
        self.assertEqual(mapping, {0: "TLT", 1: "IEF", 2: "SHY", 3: "CASH"})

    def test_posterior_weights_are_fully_invested(self) -> None:
        posterior = np.asarray([[0.2, 0.3, 0.5], [0.8, 0.1, 0.1]])
        weights = utility.posterior_duration_weights(
            posterior, {0: "TLT", 1: "IEF", 2: "SHY"}, pd.RangeIndex(2)
        )
        np.testing.assert_allclose(weights.sum(axis=1), 1.0)
        self.assertAlmostEqual(weights.loc[0, "SHY"], 0.5)
        self.assertAlmostEqual(weights.loc[1, "TLT"], 0.8)

    def test_execution_is_lagged_and_full_switch_is_one_turnover(self) -> None:
        panel = pd.DataFrame(
            {
                "SHY_return": [0.0, 0.01, 0.0],
                "IEF_return": [0.0, 0.0, 0.0],
                "TLT_return": [0.0, 0.02, 0.03],
                "CASH_return": [0.0001, 0.0001, 0.0001],
            }
        )
        target = utility.empty_weights(panel.index)
        target.loc[0, "TLT"] = 1.0
        target.loc[1, "SHY"] = 1.0
        target.loc[2, "SHY"] = 1.0

        executed = utility.execute_weights(panel, target, cost_bps=2.0)

        self.assertEqual(executed.loc[0, "weight_CASH"], 1.0)
        self.assertEqual(executed.loc[1, "weight_TLT"], 1.0)
        self.assertEqual(executed.loc[2, "weight_SHY"], 1.0)
        self.assertAlmostEqual(executed.loc[1, "turnover"], 1.0)
        self.assertAlmostEqual(executed.loc[1, "cost"], 0.0002)
        self.assertAlmostEqual(executed.loc[1, "net_return"], 0.0198)

    def test_drawdown_includes_first_return(self) -> None:
        result = utility.max_drawdown(pd.Series([-0.10, 0.05]))
        self.assertAlmostEqual(result, -0.10)

    def test_split_is_sixty_twenty_twenty(self) -> None:
        self.assertEqual(utility.split_boundaries(4000), (2400, 3200))

    def test_prepare_panel_uses_prior_cash_rate(self) -> None:
        rows = 2525
        dates = pd.date_range("2007-01-02", periods=rows, freq="B", tz="UTC")
        base = np.linspace(2.0, 4.0, rows)
        raw = pd.DataFrame(
            {
                "Date": dates,
                "DGS3MO": np.linspace(1.0, 3.0, rows),
                "DGS2": base,
                "DGS5": base + 0.2,
                "DGS10": base + 0.5,
                "DGS30": base + 0.8,
                "SHY": 80.0 * np.exp(np.linspace(0.0, 0.08, rows)),
                "IEF": 90.0 * np.exp(np.linspace(0.0, 0.12, rows)),
                "TLT": 100.0 * np.exp(np.linspace(0.0, 0.16, rows)),
            }
        )
        panel = utility.prepare_panel(raw)
        source_index = 20
        self.assertAlmostEqual(panel.loc[0, "curve_level"], raw.loc[source_index, ["DGS2", "DGS5", "DGS10", "DGS30"]].mean())
        self.assertAlmostEqual(panel.loc[0, "slope_2s10s"], 0.5)
        expected_cash = raw.loc[source_index - 1, "DGS3MO"] / 100.0 / utility.TRADING_DAYS
        self.assertAlmostEqual(panel.loc[0, "CASH_return"], expected_cash)

    def test_trading_gate_requires_return_and_sharpe(self) -> None:
        baseline = {
            "annualized_return": 0.04,
            "sharpe_excess_cash": 0.40,
            "maximum_drawdown": -0.10,
            "calmar": 0.40,
            "top_5_positive_days_share": 0.20,
            "active_duration_days": 500,
        }
        hmm = {
            "annualized_return": 0.035,
            "sharpe_excess_cash": 0.55,
            "maximum_drawdown": -0.08,
            "calmar": 0.4375,
            "top_5_positive_days_share": 0.20,
            "active_duration_days": 500,
        }
        gate = utility.gate_comparison(hmm, baseline)
        self.assertTrue(gate["trading_value_pass"])
        self.assertFalse(gate["risk_value_pass"])
        self.assertTrue(math.isclose(gate["sharpe_improvement"], 0.15))


if __name__ == "__main__":
    unittest.main()
