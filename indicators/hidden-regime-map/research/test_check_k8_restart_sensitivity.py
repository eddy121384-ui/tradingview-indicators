import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np


MODULE_PATH = Path(__file__).with_name("check_k8_restart_sensitivity.py")
SPEC = importlib.util.spec_from_file_location("check_k8_restart_sensitivity", MODULE_PATH)
restarts = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(restarts)


class RestartScheduleTests(unittest.TestCase):
    def test_diagnostic_requires_frozen_seed_groups(self):
        restarts.validate_frozen_seed_groups([42, 84, 126])
        for seeds in (
            [10, 30, 50],
            [42, 126, 84],
            [42, 84],
            [42, 84, 126, 168],
        ):
            with self.assertRaisesRegex(ValueError, "frozen seed groups"):
                restarts.validate_frozen_seed_groups(seeds)

    def test_diagnostic_requires_frozen_expanded_restart_schedule(self):
        restarts.validate_restart_offsets(
            [42, 84, 126], list(restarts.DEFAULT_RESTART_OFFSETS)
        )
        for offsets in (
            [0, 1, 2],
            [0, 1, 2, 3, 4, 5, 6, 8, 7],
            [0, 1, 2, 3, 4, 5, 6, 7],
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        ):
            with self.assertRaisesRegex(ValueError, "frozen restart offsets"):
                restarts.validate_restart_offsets([42, 84, 126], list(offsets))

    def test_overlapping_attempt_seed_sets_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "overlap"):
            restarts.validate_restart_offsets(
                [42, 45], list(restarts.DEFAULT_RESTART_OFFSETS)
            )


class FitAttemptTests(unittest.TestCase):
    @staticmethod
    def call_fit_attempt():
        matrix = np.zeros((3, 1), dtype=float)
        return restarts.fit_attempt(
            matrix,
            matrix,
            2,
            42,
            0,
            matrix,
            np.array(
                ["2026-07-21", "2026-07-22", "2026-07-23"],
                dtype="datetime64[D]",
            ),
            np.ones(3, dtype=float),
        )

    def test_non_runtime_fit_failure_is_recorded(self):
        with patch.object(
            restarts.compare_state_counts,
            "fit_candidate",
            side_effect=ValueError("numerical failure"),
        ):
            result = self.call_fit_attempt()
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"], "ValueError: numerical failure")

    def test_non_runtime_score_failure_is_recorded(self):
        model = SimpleNamespace(score=Mock(side_effect=ValueError("score failure")))
        with patch.object(
            restarts.compare_state_counts,
            "fit_candidate",
            return_value=model,
        ):
            result = self.call_fit_attempt()
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"], "ValueError: score failure")

    def test_fit_metrics_failure_propagates(self):
        model = SimpleNamespace(
            score=Mock(return_value=10.0),
            monitor_=SimpleNamespace(iter=4),
        )
        with (
            patch.object(
                restarts.compare_state_counts,
                "fit_candidate",
                return_value=model,
            ),
            patch.object(
                restarts.compare_state_counts,
                "fit_metrics",
                side_effect=ValueError("malformed metrics"),
            ),
        ):
            with self.assertRaisesRegex(ValueError, "malformed metrics"):
                self.call_fit_attempt()


class SelectionTests(unittest.TestCase):
    def test_highest_likelihood_wins_with_lower_seed_tie_break(self):
        rows = [
            {"offset": 0, "attempt_seed": 42, "train_log_likelihood": 10.0},
            {"offset": 1, "attempt_seed": 43, "train_log_likelihood": 11.0},
            {"offset": 2, "attempt_seed": 44, "train_log_likelihood": 11.0},
        ]
        selected = restarts.select_best_attempt(rows, [0, 1, 2])
        self.assertEqual(selected["attempt_seed"], 43)

    def test_only_requested_offsets_are_eligible(self):
        rows = [
            {"offset": 0, "attempt_seed": 42, "train_log_likelihood": 10.0},
            {"offset": 5, "attempt_seed": 47, "train_log_likelihood": 20.0},
        ]
        selected = restarts.select_best_attempt(rows, [0, 1, 2])
        self.assertEqual(selected["attempt_seed"], 42)


class DecisionTests(unittest.TestCase):
    @staticmethod
    def summary(passed: bool, rare_passed: bool, failed=None):
        return {
            "guardrails": {
                "passed": passed,
                "checks": {"no_rare_oos_states": rare_passed},
                "failed": list(failed or []),
            }
        }

    def test_new_restart_that_recovers_all_guardrails_is_insufficient_schedule(self):
        decision = restarts.decision_for_summaries(
            self.summary(False, False, ["no_rare_oos_states"]),
            self.summary(True, True),
            [{"offset": 0}, {"offset": 4}, {"offset": 1}],
        )
        self.assertEqual(decision["outcome"], "restart_schedule_insufficient")

    def test_failed_expanded_guardrails_are_structural_instability(self):
        decision = restarts.decision_for_summaries(
            self.summary(False, False, ["no_rare_oos_states"]),
            self.summary(False, False, ["no_rare_oos_states"]),
            [{"offset": 4}, {"offset": 5}, {"offset": 6}],
        )
        self.assertEqual(decision["outcome"], "structurally_unstable_k8")

    def test_passing_expanded_result_without_new_selected_restart_is_not_recovery(self):
        decision = restarts.decision_for_summaries(
            self.summary(False, False, ["no_rare_oos_states"]),
            self.summary(True, True),
            [{"offset": 0}, {"offset": 1}, {"offset": 2}],
        )
        self.assertEqual(decision["outcome"], "structurally_unstable_k8")

    def test_known_baseline_failure_must_be_reproduced(self):
        with self.assertRaisesRegex(RuntimeError, "no longer reproduces"):
            restarts.decision_for_summaries(
                self.summary(True, True),
                self.summary(True, True),
                [{"offset": 4}],
            )


if __name__ == "__main__":
    unittest.main()
