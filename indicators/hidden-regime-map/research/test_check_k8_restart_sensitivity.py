import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("check_k8_restart_sensitivity.py")
SPEC = importlib.util.spec_from_file_location("check_k8_restart_sensitivity", MODULE_PATH)
restarts = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(restarts)


class RestartScheduleTests(unittest.TestCase):
    def test_expanded_schedule_must_include_existing_offsets(self):
        with self.assertRaisesRegex(ValueError, "include the existing schedule"):
            restarts.validate_restart_offsets([42, 84, 126], [0, 1, 3])

    def test_overlapping_attempt_seed_sets_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "overlap"):
            restarts.validate_restart_offsets([42, 45], [0, 1, 2, 3])

    def test_default_schedule_is_valid(self):
        restarts.validate_restart_offsets(
            [42, 84, 126], list(restarts.DEFAULT_RESTART_OFFSETS)
        )


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
