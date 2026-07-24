import importlib.util
import unittest
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()
