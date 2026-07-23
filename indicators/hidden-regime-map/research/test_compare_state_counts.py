import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np


MODULE_PATH = Path(__file__).with_name("compare_state_counts.py")
sys.path.insert(0, str(MODULE_PATH.parent))
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


class FailureAndDecisionTests(unittest.TestCase):
    def test_failed_candidates_produce_explicit_inconclusive_outcome(self):
        candidates = [
            {"k": k, "status": "failed", "failures": [{"seed": 42, "error": "fit failed"}]}
            for k in comparison.candidate_state_counts()
        ]
        decision = comparison.choose_outcome(candidates)
        self.assertEqual(decision["outcome"], "inconclusive")
        self.assertIsNone(decision["selected_k"])

    def test_decision_does_not_hard_code_six_states(self):
        def candidate(k, bic):
            return {
                "k": k,
                "status": "ok",
                "aggregate": {
                    "bic": {"mean": bic},
                    "rare_state_count_oos": {"mean": 0.0},
                    "minimum_pairwise_separation": {"mean": 2.0},
                },
            }

        decision = comparison.choose_outcome([candidate(3, 100), candidate(6, 90), candidate(5, 80)])
        self.assertEqual(decision, {
            "outcome": "select_other_k",
            "selected_k": 5,
            "reason": "Selected the lowest mean train BIC among candidates without rare OOS states or weak pairwise separation.",
        })


if __name__ == "__main__":
    unittest.main()
