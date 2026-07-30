from __future__ import annotations

import gzip
import hashlib
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

import evaluate_trading_utility as utility


class TradingUtilityTests(unittest.TestCase):
    def test_decompressed_hash_matches_original_csv(self) -> None:
        payload = b"Date,Open,High,Low,Close\n2020-01-01,1,1,1,1\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.csv.gz"
            with gzip.open(path, "wb") as handle:
                handle.write(payload)
            self.assertEqual(
                utility.sha256_decompressed(path),
                hashlib.sha256(payload).hexdigest(),
            )

    def test_split_boundaries_are_non_overlapping(self) -> None:
        fit_end, exploratory_end = utility.split_boundaries(2000)
        self.assertEqual(fit_end, 1200)
        self.assertEqual(exploratory_end, 1600)
        slices = utility.period_slices(2000, fit_end, exploratory_end)
        self.assertEqual(slices["exploratory"], slice(1200, 1600))
        self.assertEqual(slices["final"], slice(1600, 2000))

    def test_execution_uses_prior_confirmed_target_and_cost(self) -> None:
        close = pd.Series([100.0, 110.0, 121.0])
        target = pd.Series([0.0, 1.0, 1.0])
        executed = utility.execute_target(close, target, cost_bps=5.0)
        self.assertEqual(executed["position"].tolist(), [0.0, 0.0, 1.0])
        self.assertEqual(executed["turnover"].tolist(), [0.0, 0.0, 1.0])
        self.assertAlmostEqual(executed["net_return"].iloc[1], 0.0)
        self.assertAlmostEqual(executed["net_return"].iloc[2], 0.10 - 0.0005)

    def test_state_buckets_use_predeclared_risk_score(self) -> None:
        means = np.asarray(
            [
                [1.0, -1.0, 1.0],
                [0.0, 0.0, 0.0],
                [-1.0, 1.0, -1.0],
            ]
        )
        favorable, defensive, scores = utility.state_buckets(
            means, ("standardized_return", "atr_pct", "trend_strength")
        )
        self.assertEqual(favorable, [0])
        self.assertEqual(defensive, [2])
        self.assertEqual(scores, [-3.0, 0.0, 3.0])

    def test_hmm_targets_are_bounded_and_distinct(self) -> None:
        base = pd.Series([1.0, 1.0, 1.0])
        posterior = np.asarray(
            [
                [0.8, 0.1, 0.1],
                [0.2, 0.2, 0.6],
                [0.4, 0.4, 0.2],
            ]
        )
        targets = utility.hmm_targets(base, posterior, [0], [2])
        self.assertEqual(targets["favorable_filter"].tolist(), [1.0, 0.0, 0.0])
        self.assertEqual(targets["defensive_switch"].tolist(), [1.0, 0.0, 1.0])
        self.assertTrue(
            ((targets["size_modifier"] >= 0.25) & (targets["size_modifier"] <= 1.0)).all()
        )

    def test_drawdown_includes_negative_first_period_return(self) -> None:
        frame = pd.DataFrame(
            {
                "position": [1.0, 1.0],
                "turnover": [0.0, 0.0],
                "net_return": [-0.10, 0.0],
            }
        )
        metrics = utility.performance_metrics(frame)
        self.assertAlmostEqual(metrics["maximum_drawdown"], -0.10)

    def test_trade_episode_metrics_report_payoff_distribution_and_censoring(self) -> None:
        frame = pd.DataFrame(
            {
                "position": [1.0, 1.0, 0.0, 1.0, 1.0, 0.0],
                "turnover": [0.0, 0.0, 1.0, 1.0, 0.0, 1.0],
                "net_return": [0.10, -0.05, -0.0005, 0.02, 0.03, -0.0005],
            }
        )
        metrics = utility.trade_episode_metrics(frame)
        self.assertEqual(metrics["trade_episode_count"], 2)
        self.assertEqual(metrics["new_entries_within_period"], 1)
        self.assertEqual(metrics["exits_within_period"], 2)
        self.assertEqual(metrics["completed_round_trips"], 1)
        self.assertTrue(metrics["left_censored_trade"])
        self.assertFalse(metrics["right_censored_trade"])
        expected_median = ((1.10 * 0.95 - 1.0) + (1.02 * 1.03 - 1.0)) / 2.0
        self.assertAlmostEqual(metrics["trade_payoff_median"], expected_median)
        self.assertAlmostEqual(metrics["top_3_positive_trades_share"], 1.0)

    def test_carried_position_is_not_counted_as_completed_round_trip(self) -> None:
        frame = pd.DataFrame(
            {
                "position": [1.0, 1.0, 1.0],
                "turnover": [0.0, 0.0, 0.0],
                "net_return": [0.01, -0.01, 0.02],
            }
        )
        metrics = utility.trade_episode_metrics(frame)
        self.assertEqual(metrics["trade_episode_count"], 1)
        self.assertEqual(metrics["new_entries_within_period"], 0)
        self.assertEqual(metrics["exits_within_period"], 0)
        self.assertEqual(metrics["completed_round_trips"], 0)
        self.assertTrue(metrics["left_censored_trade"])
        self.assertTrue(metrics["right_censored_trade"])

    def test_claim_checks_require_simple_filter_edge(self) -> None:
        baseline_exploratory = self.metrics(sharpe=0.5, drawdown=-0.20)
        baseline_final = self.metrics(sharpe=0.5, drawdown=-0.20)
        simple_final = self.metrics(sharpe=0.65, drawdown=-0.15)
        variant_exploratory = self.metrics(sharpe=0.6, drawdown=-0.18)
        variant_final = self.metrics(sharpe=0.67, drawdown=-0.14)
        checks = utility.claim_checks(
            variant_exploratory,
            variant_final,
            baseline_exploratory,
            baseline_final,
            simple_final,
        )
        self.assertFalse(checks["trading_value"]["passed"])
        self.assertFalse(
            checks["trading_value"]["checks"]["beats_simple_filter_sharpe"]
        )

    def test_decision_requires_two_baselines_for_same_candidate_role(self) -> None:
        claims = [
            self.claim("k3", "defensive_switch", "buy_and_hold", trading=True),
            self.claim("k3", "defensive_switch", "trend_100", trading=True),
            self.claim("k8", "size_modifier", "momentum_63", trading=True),
        ]
        decision = utility.decide_outcome(claims)
        self.assertEqual(decision["outcome"], "adds_oos_trading_value")
        self.assertEqual(
            decision["trading_winners"][0]["baselines"],
            ["buy_and_hold", "trend_100"],
        )

    def test_negative_complete_result_is_retained(self) -> None:
        claims = [
            self.claim("k3", "defensive_switch", baseline)
            for baseline in utility.BASELINES
        ]
        decision = utility.decide_outcome(claims)
        self.assertEqual(decision["outcome"], "no_incremental_value")

    def test_strict_json_replaces_non_finite_values(self) -> None:
        result = utility.strict_json({"nan": float("nan"), "inf": float("inf")})
        self.assertIsNone(result["nan"])
        self.assertIsNone(result["inf"])

    @staticmethod
    def metrics(
        *,
        sharpe: float,
        drawdown: float,
        annualized_return: float = 0.10,
        calmar: float = 0.50,
        active_days: int = 200,
        concentration: float = 0.20,
    ) -> dict[str, float | int]:
        return {
            "sharpe": sharpe,
            "maximum_drawdown": drawdown,
            "annualized_return": annualized_return,
            "calmar": calmar,
            "active_days": active_days,
            "top_5_positive_days_share": concentration,
        }

    @staticmethod
    def claim(
        candidate: str,
        role: str,
        baseline: str,
        *,
        trading: bool = False,
        risk: bool = False,
    ) -> dict[str, object]:
        return {
            "candidate": candidate,
            "role": role,
            "baseline": baseline,
            "checks": {
                "trading_value": {"passed": trading, "checks": {}},
                "risk_value": {"passed": risk, "checks": {}},
                "deltas": {},
            },
        }


if __name__ == "__main__":
    unittest.main()
