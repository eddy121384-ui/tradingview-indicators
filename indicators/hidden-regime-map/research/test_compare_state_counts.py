import copy
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np


MODULE_PATH = Path(__file__).with_name("compare_state_counts.py")
SPEC = importlib.util.spec_from_file_location("compare_state_counts", MODULE_PATH)
comparison = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(comparison)


class DummyModel:
    def __init__(self, means, variances, transition=None):
        self.means_ = np.asarray(means, dtype=float)
        self._variances = np.asarray(variances, dtype=float)
        self.n_components = len(self.means_)
        self.transmat_ = np.asarray(
            transition if transition is not None else np.eye(self.n_components),
            dtype=float,
        )
        self.startprob_ = np.full(self.n_components, 1.0 / self.n_components)

    @property
    def covars_(self):
        return self._variances


class CandidateTests(unittest.TestCase):
    def test_candidate_generation_is_inclusive_and_ordered(self):
        self.assertEqual(comparison.candidate_state_counts(), [3, 4, 5, 6, 7, 8])
        with self.assertRaisesRegex(ValueError, "state-count range"):
            comparison.candidate_state_counts(8, 3)

    def test_deterministic_seed_repeats_identical_fit(self):
        rng = np.random.default_rng(10)
        matrix = np.vstack(
            [rng.normal(-2, 0.3, (120, 3)), rng.normal(2, 0.3, (120, 3))]
        )
        first = comparison.fit_candidate(matrix, 3, 42)
        second = comparison.fit_candidate(matrix, 3, 42)
        np.testing.assert_allclose(first.means_, second.means_)
        np.testing.assert_allclose(first.transmat_, second.transmat_)
        self.assertEqual(first.score(matrix), second.score(matrix))

    def test_non_converged_fit_is_rejected(self):
        class NonConvergedModel:
            def __init__(self, **kwargs):
                self.monitor_ = type("Monitor", (), {"converged": False})()

            def fit(self, matrix):
                return self

        with patch.object(comparison, "GaussianHMM", NonConvergedModel):
            with self.assertRaisesRegex(RuntimeError, "did not converge"):
                comparison.fit_candidate(np.ones((20, 3)), 3, 42)

    def test_negative_likelihood_delta_is_not_accepted_as_convergence(self):
        class FalseConvergedModel:
            def __init__(self, **kwargs):
                self.monitor_ = type(
                    "Monitor", (), {"converged": True, "history": [10.0, 9.0]}
                )()

            def fit(self, matrix):
                return self

        with patch.object(comparison, "GaussianHMM", FalseConvergedModel):
            with self.assertRaisesRegex(RuntimeError, "negative likelihood delta"):
                comparison.fit_candidate(np.ones((20, 3)), 3, 42)


class AlignmentTests(unittest.TestCase):
    def test_permuted_states_align_before_parameter_comparison(self):
        reference = DummyModel(
            [[-2, 0, 0], [0, 2, 0], [2, 0, 0]],
            [[1, 1, 1], [1, 1, 1], [1, 1, 1]],
        )
        permutation = [2, 0, 1]
        candidate = DummyModel(
            reference.means_[permutation], reference.covars_[permutation]
        )
        alignment = comparison.state_alignment(reference, candidate)
        aligned = comparison.aligned_parameters(candidate, alignment)
        np.testing.assert_allclose(aligned["means"], reference.means_)
        self.assertNotEqual(alignment, [0, 1, 2])

    def test_alignment_rejects_different_state_counts(self):
        with self.assertRaisesRegex(ValueError, "equal state counts"):
            comparison.state_alignment(
                DummyModel([[0], [1]], [[1], [1]]),
                DummyModel([[0], [1], [2]], [[1], [1], [1]]),
            )


class MetricTests(unittest.TestCase):
    def test_information_criteria_and_pairwise_separation(self):
        aic, bic = comparison.information_criteria(-100.0, 200, 3, 3)
        parameter_count = (3 - 1) + 3 * (3 - 1) + 2 * 3 * 3
        self.assertEqual(aic, 2 * parameter_count + 200)
        self.assertAlmostEqual(bic, np.log(200) * parameter_count + 200)
        model = DummyModel([[-2, 0], [0, 0], [4, 0]], [[1, 1]] * 3)
        self.assertAlmostEqual(comparison.minimum_pairwise_separation(model), 2.0)

    def test_run_lengths_include_absent_states(self):
        self.assertEqual(
            comparison.run_lengths(np.asarray([0, 0, 1, 1, 1, 0]), 3),
            [[2, 1], [3], []],
        )

    def test_train_and_oos_durations_do_not_cross_split(self):
        states = np.asarray([0, 0, 0, 0])
        self.assertEqual(comparison.run_lengths(states[:2], 2), [[2], []])
        self.assertEqual(comparison.run_lengths(states[2:], 2), [[2], []])

    def test_interpretability_helpers_include_noise_and_feature_means(self):
        matrix = np.asarray([[1.0, 2.0], [3.0, 4.0]])
        posterior = np.asarray([[1.0, 0.0], [0.0, 1.0]])
        self.assertEqual(
            comparison.state_feature_means(matrix, posterior),
            [[1.0, 2.0], [3.0, 4.0]],
        )
        self.assertEqual(comparison.single_bar_shares([[1, 2, 1], []]), [2 / 3, 1.0])


class FailureAndDecisionTests(unittest.TestCase):
    @staticmethod
    def guardrail_input():
        scalar = lambda value: {"mean": value, "std": 0.0}
        return {
            "fits": [
                {
                    "converged": True,
                    "final_likelihood_delta": 0.01,
                }
            ],
            "aggregate": {
                "train_oos_likelihood_drift": scalar(0.1),
                "occupancy_drift_l1": scalar(0.1),
                "rare_state_count_train": scalar(0.0),
                "rare_state_count_oos": scalar(0.0),
                "minimum_pairwise_separation": scalar(2.0),
                "reproducibility": {
                    "emission_mean_rmse": {"max": 0.1},
                    "transition_rmse": {"max": 0.1},
                    "oos_occupancy_rmse": {"max": 0.05},
                },
                "state_ranges": {
                    "feature_mean_drift_l2": {"maximum": [0.2, 0.2, 0.2]},
                    "mean_state_duration_oos": {"minimum": [2.0, 2.0, 2.0]},
                    "single_bar_share_oos": {"maximum": [0.2, 0.2, 0.2]},
                },
            },
        }

    @staticmethod
    def candidate(k, aic, bic, oos, passed=True):
        return {
            "k": k,
            "status": "ok",
            "guardrails": {"passed": passed, "checks": {}, "failed": []},
            "aggregate": {
                "aic": {"mean": aic},
                "bic": {"mean": bic},
                "oos_log_likelihood_per_observation": {"mean": oos},
            },
        }

    def test_failed_candidates_produce_explicit_inconclusive_outcome(self):
        candidates = [
            {"k": k, "status": "failed", "failures": [{"seed": 42, "error": "fit failed"}]}
            for k in comparison.candidate_state_counts()
        ]
        decision = comparison.choose_outcome(candidates)
        self.assertEqual(decision["outcome"], "inconclusive")
        self.assertIsNone(decision["selected_k"])

    def test_decision_does_not_hard_code_six_states(self):
        decision = comparison.choose_outcome(
            [
                self.candidate(3, 100, 100, -3.0),
                self.candidate(6, 90, 90, -2.0),
                self.candidate(5, 80, 80, -1.0),
            ]
        )
        self.assertEqual(decision, {
            "outcome": "select_other_k",
            "selected_k": 5,
            "reason": "AIC, BIC, and OOS likelihood agree after the candidate cleared every model-selection guardrail.",
        })

    def test_any_incomplete_k_forces_inconclusive(self):
        candidates = [self.candidate(k, k, k, -float(k)) for k in range(3, 8)]
        candidates.append({"k": 8, "status": "failed", "failures": []})
        self.assertEqual(
            comparison.choose_outcome(candidates)["outcome"], "inconclusive"
        )

    def test_failed_guardrail_forces_inconclusive(self):
        candidates = [self.candidate(k, k, k, -float(k), passed=False) for k in range(3, 9)]
        decision = comparison.choose_outcome(candidates)
        self.assertEqual(decision["outcome"], "inconclusive")
        self.assertIn("guardrail", decision["reason"])

    def test_conflicting_selection_evidence_forces_inconclusive(self):
        candidates = [
            self.candidate(3, 10, 30, -3.0),
            self.candidate(4, 20, 10, -2.0),
            self.candidate(5, 30, 20, -1.0),
        ]
        decision = comparison.choose_outcome(candidates)
        self.assertEqual(decision["outcome"], "inconclusive")
        self.assertIn("conflicts", decision["reason"])

    def test_all_model_selection_guardrails_are_enforced(self):
        baseline = self.guardrail_input()
        self.assertTrue(comparison.evaluate_guardrails(baseline)["passed"])
        failures = {
            "all_fits_converged": lambda row: row["fits"][0].update(converged=False),
            "non_negative_convergence_delta": lambda row: row["fits"][0].update(final_likelihood_delta=-1.0),
            "oos_likelihood_drift": lambda row: row["aggregate"]["train_oos_likelihood_drift"].update(mean=2.0),
            "occupancy_drift": lambda row: row["aggregate"]["occupancy_drift_l1"].update(mean=1.0),
            "feature_drift": lambda row: row["aggregate"]["state_ranges"]["feature_mean_drift_l2"].update(maximum=[2.0]),
            "no_rare_train_states": lambda row: row["aggregate"]["rare_state_count_train"].update(mean=1.0),
            "no_rare_oos_states": lambda row: row["aggregate"]["rare_state_count_oos"].update(mean=1.0),
            "state_separation": lambda row: row["aggregate"]["minimum_pairwise_separation"].update(mean=0.5),
            "oos_duration": lambda row: row["aggregate"]["state_ranges"]["mean_state_duration_oos"].update(minimum=[1.0]),
            "oos_noise": lambda row: row["aggregate"]["state_ranges"]["single_bar_share_oos"].update(maximum=[1.0]),
            "emission_reproducibility": lambda row: row["aggregate"]["reproducibility"]["emission_mean_rmse"].update(max=1.0),
            "transition_reproducibility": lambda row: row["aggregate"]["reproducibility"]["transition_rmse"].update(max=1.0),
            "oos_occupancy_reproducibility": lambda row: row["aggregate"]["reproducibility"]["oos_occupancy_rmse"].update(max=1.0),
        }
        for expected_failure, mutate in failures.items():
            with self.subTest(guardrail=expected_failure):
                candidate = copy.deepcopy(baseline)
                mutate(candidate)
                result = comparison.evaluate_guardrails(candidate)
                self.assertFalse(result["passed"])
                self.assertIn(expected_failure, result["failed"])


if __name__ == "__main__":
    unittest.main()
