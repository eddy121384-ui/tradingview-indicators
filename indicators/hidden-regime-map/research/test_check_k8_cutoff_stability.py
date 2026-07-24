import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

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


class DecisionTests(unittest.TestCase):
    @staticmethod
    def row(passed=True, status="ok"):
        return {
            "status": status,
            "guardrails": {"passed": passed, "failed": [] if passed else ["x"]},
        }

    def test_all_cutoffs_must_pass(self):
        decision = cutoffs.decision_for_rows([self.row(), self.row()])
        self.assertEqual(decision["outcome"], "candidate_stable_across_cutoffs")
        self.assertEqual(decision["passing_cutoffs"], 2)

    def test_any_guardrail_failure_is_cutoff_sensitive(self):
        decision = cutoffs.decision_for_rows([self.row(), self.row(False)])
        self.assertEqual(decision["outcome"], "cutoff_sensitive")
        self.assertEqual(decision["passing_cutoffs"], 1)

    def test_any_fit_failure_is_cutoff_sensitive(self):
        decision = cutoffs.decision_for_rows([self.row(), {"status": "failed"}])
        self.assertEqual(decision["outcome"], "cutoff_sensitive")
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
            cutoffs.compare_state_counts,
            "fit_seed_group",
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
            cutoffs.compare_state_counts,
            "fit_seed_group",
            side_effect=ValueError("unexpected seed error"),
        ):
            with self.assertRaisesRegex(ValueError, "unexpected seed error"):
                cutoffs.fit_seed_metrics(**self.inputs())

    def test_unexpected_metrics_error_propagates(self):
        model = object()
        with patch.object(
            cutoffs.compare_state_counts,
            "fit_seed_group",
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
