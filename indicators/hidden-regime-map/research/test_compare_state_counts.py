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

    def test_iteration_capped_positive_delta_must_satisfy_tolerance(self):
        class IterationCappedModel:
            def __init__(self, **kwargs):
                self.n_iter = kwargs["n_iter"]
                self.tol = kwargs["tol"]
                self.monitor_ = type(
                    "Monitor",
                    (),
                    {
                        "converged": True,
                        "iter": self.n_iter,
                        "history": [10.0, 10.01],
                    },
                )()

            def fit(self, matrix):
                return self

        with patch.object(comparison, "GaussianHMM", IterationCappedModel):
            with self.assertRaisesRegex(RuntimeError, "iteration cap"):
                comparison.fit_candidate(np.ones((20, 3)), 3, 42)

    def test_restart_group_selects_best_valid_fit_and_preserves_failures(self):
        class ScoredModel:
            def __init__(self, score):
                self._score = score
                self.monitor_ = type("Monitor", (), {"iter": 5})()

            def score(self, matrix):
                return self._score

        def attempt(matrix, n_states, seed):
            if seed == 42:
                raise RuntimeError("synthetic failure")
            return ScoredModel({43: -20.0, 44: -10.0}[seed])

        with patch.object(comparison, "fit_candidate", side_effect=attempt):
            model, attempts, selected_seed = comparison.fit_seed_group(
                np.ones((20, 3)), 7, 42
            )
        self.assertEqual(selected_seed, 44)
        self.assertEqual(model.score(None), -10.0)
        self.assertEqual([row["status"] for row in attempts], ["failed", "ok", "ok"])
        self.assertIn("synthetic failure", attempts[0]["error"])

    def test_restart_group_failure_preserves_every_attempt(self):
        with patch.object(
            comparison, "fit_candidate", side_effect=RuntimeError("no convergence")
        ):
            with self.assertRaises(comparison.RestartGroupError) as caught:
                comparison.fit_seed_group(np.ones((20, 3)), 7, 42)
        self.assertEqual(
            [row["attempt_seed"] for row in caught.exception.attempts], [42, 43, 44]
        )
        self.assertTrue(
            all(row["status"] == "failed" for row in caught.exception.attempts)
        )


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

    def test_alignment_reorders_variances_transitions_and_event_exposure(self):
        metrics = {
            key: [[20], [30], [10]] if "feature" in key or "emission" in key else [20, 30, 10]
            for key in (
                "occupancy_train", "occupancy_oos", "mean_state_duration_train",
                "mean_state_duration_oos", "median_state_duration_train",
                "median_state_duration_oos", "single_bar_share_train",
                "single_bar_share_oos", "posterior_feature_mean_train",
                "posterior_feature_mean_oos", "posterior_feature_variance_train",
                "posterior_feature_variance_oos", "variance_aware_feature_drift",
                "emission_mean", "emission_variance", "self_transition",
            )
        }
        metrics["transition_matrix"] = [[2, 20, 21], [30, 3, 31], [10, 11, 1]]
        metrics["event_window_exposure"] = [{
            "average_posterior": [20, 30, 10],
            "dominant_state_share": [0.2, 0.3, 0.1],
        }]
        aligned = comparison.align_metric_lists(metrics, [2, 0, 1])
        self.assertEqual(aligned["emission_variance"], [[10], [20], [30]])
        self.assertEqual(aligned["transition_matrix"], [[1, 10, 11], [21, 2, 20], [31, 30, 3]])
        self.assertEqual(aligned["event_window_exposure"][0]["average_posterior"], [10, 20, 30])


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
        variances = comparison.state_feature_variances(
            matrix, posterior, [[1.0, 2.0], [3.0, 4.0]]
        )
        self.assertEqual(variances, [[0.0, 0.0], [0.0, 0.0]])
        self.assertGreater(
            comparison.feature_distribution_drift(
                [0.0], [1.0], [0.0], [4.0]
            ),
            0.0,
        )

    def test_event_window_exposure_uses_existing_windows_shape(self):
        rows = comparison.event_window_exposure(
            np.asarray(["2020-02-18", "2020-02-20"], dtype="datetime64[D]"),
            np.asarray([[0.8, 0.2], [0.1, 0.9]]),
            [{"name": "shock", "start": "2020-02-19", "end": "2020-02-21", "context": "synthetic"}],
            closes=np.asarray([100.0, 90.0]),
        )
        self.assertEqual(rows[0]["bars"], 1)
        self.assertEqual(rows[0]["coverage_status"], "partial_coverage")
        self.assertEqual(rows[0]["coverage_ratio"], 0.5)
        self.assertEqual(rows[0]["window_return"], 0.0)
        self.assertEqual(rows[0]["average_posterior"], [0.1, 0.9])


class FailureAndDecisionTests(unittest.TestCase):
    @staticmethod
    def guardrail_input():
        scalar = lambda value: {
            "mean": value,
            "std": 0.0,
            "min": value,
            "max": value,
        }
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
                    "variance_aware_feature_drift": {"maximum": [0.2, 0.2, 0.2]},
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

    def test_rejected_metric_leader_is_not_hidden_by_prefiltering(self):
        rejected = self.candidate(7, 1, 1, -1.0, passed=False)
        rejected["guardrails"]["failed"] = ["oos_noise"]
        candidates = [
            self.candidate(3, 10, 10, -2.0),
            rejected,
            self.candidate(8, 20, 20, -3.0),
        ]
        decision = comparison.choose_outcome(candidates)
        self.assertEqual(decision["outcome"], "inconclusive")
        self.assertIn("K=7", decision["reason"])
        self.assertIn("oos_noise", decision["reason"])

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
            "oos_likelihood_drift": lambda row: row["aggregate"]["train_oos_likelihood_drift"].update(max=2.0),
            "occupancy_drift": lambda row: row["aggregate"]["occupancy_drift_l1"].update(max=1.0),
            "feature_drift": lambda row: row["aggregate"]["state_ranges"]["variance_aware_feature_drift"].update(maximum=[4.0]),
            "no_rare_train_states": lambda row: row["aggregate"]["rare_state_count_train"].update(max=1.0),
            "no_rare_oos_states": lambda row: row["aggregate"]["rare_state_count_oos"].update(max=1.0),
            "state_separation": lambda row: row["aggregate"]["minimum_pairwise_separation"].update(min=0.5),
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

    def test_one_unstable_seed_cannot_hide_behind_mean_drift(self):
        candidate = self.guardrail_input()
        candidate["aggregate"]["train_oos_likelihood_drift"].update(
            mean=0.4, max=1.2
        )
        candidate["aggregate"]["occupancy_drift_l1"].update(mean=0.2, max=0.7)
        result = comparison.evaluate_guardrails(candidate)
        self.assertFalse(result["passed"])
        self.assertIn("oos_likelihood_drift", result["failed"])
        self.assertIn("occupancy_drift", result["failed"])

    def test_worst_seed_also_controls_rare_states_and_separation(self):
        candidate = self.guardrail_input()
        candidate["aggregate"]["rare_state_count_oos"].update(mean=0.34, max=1.0)
        candidate["aggregate"]["minimum_pairwise_separation"].update(
            mean=1.5, min=0.8
        )
        result = comparison.evaluate_guardrails(candidate)
        self.assertFalse(result["passed"])
        self.assertIn("no_rare_oos_states", result["failed"])
        self.assertIn("state_separation", result["failed"])

    def test_machine_status_maps_to_explicit_issue_outcome(self):
        mapped = comparison.map_issue_26_status(
            {"outcome": "inconclusive", "selected_k": None, "reason": "conflict"}
        )
        self.assertEqual(mapped["machine_status"], "inconclusive")
        self.assertEqual(mapped["issue_26_research_outcome"], "collect_more_evidence")


if __name__ == "__main__":
    unittest.main()
