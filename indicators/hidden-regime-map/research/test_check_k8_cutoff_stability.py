import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np


MODULE_PATH = Path(__file__).with_name("check_k8_cutoff_stability.py")
SPEC = importlib.util.spec_from_file_location("check_k8_cutoff_stability", MODULE_PATH)
cutoffs = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(cutoffs)


class CutoffSelectionTests(unittest.TestCase):
    def test_latest_adjacent_cutoffs_are_returned_in_order(self):
        self.assertEqual(cutoffs.cutoff_positions(10, 5), [5, 6, 7, 8, 9])

    def test_invalid_cutoff_counts_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "at least 2"):
            cutoffs.cutoff_positions(10, 1)
        with self.assertRaisesRegex(ValueError, "cannot exceed"):
            cutoffs.cutoff_positions(4, 5)


class ExpandedRestartTests(unittest.TestCase):
    def test_frozen_schedule_contains_nine_ordered_offsets(self):
        self.assertEqual(cutoffs.EXPANDED_RESTART_OFFSETS, tuple(range(9)))

    def test_diagnostic_requires_exact_frozen_seed_groups(self):
        cutoffs.validate_frozen_seed_groups([42, 84, 126])
        for seeds in (
            [42, 84],
            [42, 84, 126, 168],
            [42, 126, 84],
            [10, 30, 50],
            [42, 48],
        ):
            with self.assertRaisesRegex(ValueError, "frozen seed groups"):
                cutoffs.validate_frozen_seed_groups(seeds)

    def test_expanded_group_selects_best_fit_and_preserves_all_attempts(self):
        class ScoredModel:
            def __init__(self, score):
                self._score = score
                self.monitor_ = SimpleNamespace(iter=5)

            def score(self, matrix):
                return self._score

        def attempt(matrix, n_states, seed):
            if seed == 42:
                raise ValueError("synthetic fit failure")
            return ScoredModel(float(seed))

        with patch.object(
            cutoffs.compare_state_counts, "fit_candidate", side_effect=attempt
        ):
            model, attempts, selected_seed = cutoffs.fit_seed_group_expanded(
                np.ones((20, 3)), 8, 42
            )

        self.assertEqual(selected_seed, 50)
        self.assertEqual(model.score(None), 50.0)
        self.assertEqual(
            [row["attempt_seed"] for row in attempts], list(range(42, 51))
        )
        self.assertEqual(attempts[0]["status"], "failed")
        self.assertTrue(all(row["status"] == "ok" for row in attempts[1:]))

    def test_expanded_group_failure_preserves_all_nine_attempts(self):
        with patch.object(
            cutoffs.compare_state_counts,
            "fit_candidate",
            side_effect=RuntimeError("no convergence"),
        ):
            with self.assertRaises(
                cutoffs.compare_state_counts.RestartGroupError
            ) as caught:
                cutoffs.fit_seed_group_expanded(np.ones((20, 3)), 8, 42)

        self.assertEqual(
            [row["attempt_seed"] for row in caught.exception.attempts],
            list(range(42, 51)),
        )
        self.assertTrue(
            all(row["status"] == "failed" for row in caught.exception.attempts)
        )


class AuditProjectionTests(unittest.TestCase):
    def test_seed_diagnostics_preserve_every_restart_attempt(self):
        attempts = [
            {"attempt_seed": seed, "status": "ok" if seed != 44 else "failed"}
            for seed in range(42, 51)
        ]
        summary = {
            "fits": [
                {
                    "group_seed": 42,
                    "selected_attempt_seed": 47,
                    "restart_attempts": attempts,
                    "occupancy_oos": [0.1, 0.2],
                    "rare_state_count_oos": 0,
                    "occupancy_drift_l1": 0.3,
                    "train_oos_likelihood_drift": 0.1,
                }
            ]
        }
        diagnostics = cutoffs.seed_diagnostics_for_summary(summary)
        self.assertEqual(diagnostics[0]["restart_attempts"], attempts)
        self.assertEqual(diagnostics[0]["selected_attempt_seed"], 47)

    def test_markdown_lists_all_restart_attempts(self):
        attempts = [
            {"attempt_seed": seed, "status": "ok" if seed != 44 else "failed"}
            for seed in range(42, 51)
        ]
        result = {
            "decision": {
                "outcome": "cutoff_sensitive_after_expansion",
                "passing_cutoffs": 0,
                "tested_cutoffs": 1,
                "reason": "synthetic",
            },
            "cutoffs": [
                {
                    "cutoff": "2026-07-21",
                    "status": "ok",
                    "guardrails": {"failed": ["no_rare_oos_states"]},
                    "worst_seed": {
                        "minimum_oos_occupancy": 0.01968,
                        "maximum_rare_state_count_oos": 1,
                    },
                    "seed_diagnostics": [
                        {
                            "group_seed": 42,
                            "selected_attempt_seed": 47,
                            "restart_attempts": attempts,
                        }
                    ],
                }
            ],
        }
        report = cutoffs.markdown_report(result)
        self.assertIn("42:ok", report)
        self.assertIn("44:failed", report)
        self.assertIn("50:ok", report)


class DecisionTests(unittest.TestCase):
    @staticmethod
    def row(passed=True, status="ok"):
        return {
            "status": status,
            "guardrails": {"passed": passed, "failed": [] if passed else ["x"]},
        }

    def test_all_cutoffs_must_pass(self):
        decision = cutoffs.decision_for_rows([self.row(), self.row()])
        self.assertEqual(decision["outcome"], "stable_with_expanded_restarts")
        self.assertEqual(decision["passing_cutoffs"], 2)

    def test_any_guardrail_failure_is_cutoff_sensitive(self):
        decision = cutoffs.decision_for_rows([self.row(), self.row(False)])
        self.assertEqual(
            decision["outcome"], "cutoff_sensitive_after_expansion"
        )
        self.assertEqual(decision["passing_cutoffs"], 1)

    def test_any_fit_failure_is_cutoff_sensitive(self):
        decision = cutoffs.decision_for_rows([self.row(), {"status": "failed"}])
        self.assertEqual(
            decision["outcome"], "cutoff_sensitive_after_expansion"
        )
        self.assertEqual(decision["passing_cutoffs"], 1)


class FitErrorHandlingTests(unittest.TestCase):
    @staticmethod
    def inputs():
        return {
            "train_matrix": np.zeros((2, 1)),
            "full_matrix": np.zeros((3, 1)),
            "train_rows": 2,
            "seed": 42,
            "observation_matrix": np.zeros((3, 1)),
            "dates": np.asarray(
                ["2020-01-01", "2020-01-02", "2020-01-03"],
                dtype="datetime64[D]",
            ),
            "closes": np.ones(3),
        }

    def test_expected_restart_exhaustion_becomes_cutoff_failure(self):
        attempts = [{"attempt_seed": 42, "status": "failed"}]
        error = cutoffs.compare_state_counts.RestartGroupError(42, attempts)
        with patch.object(
            cutoffs,
            "fit_seed_group_expanded",
            side_effect=error,
        ), patch.object(cutoffs.compare_state_counts, "fit_metrics") as fit_metrics:
            model, metrics, failure = cutoffs.fit_seed_metrics(**self.inputs())

        self.assertIsNone(model)
        self.assertIsNone(metrics)
        self.assertEqual(failure["group_seed"], 42)
        self.assertEqual(failure["restart_attempts"], attempts)
        fit_metrics.assert_not_called()

    def test_unexpected_seed_group_error_propagates(self):
        with patch.object(
            cutoffs,
            "fit_seed_group_expanded",
            side_effect=ValueError("unexpected seed error"),
        ):
            with self.assertRaisesRegex(ValueError, "unexpected seed error"):
                cutoffs.fit_seed_metrics(**self.inputs())

    def test_unexpected_metrics_error_propagates(self):
        model = object()
        with patch.object(
            cutoffs,
            "fit_seed_group_expanded",
            return_value=(model, [], 43),
        ), patch.object(
            cutoffs.compare_state_counts,
            "fit_metrics",
            side_effect=ValueError("malformed metrics"),
        ):
            with self.assertRaisesRegex(ValueError, "malformed metrics"):
                cutoffs.fit_seed_metrics(**self.inputs())


if __name__ == "__main__":
    unittest.main()
