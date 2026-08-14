import unittest

from diagnose_formation_transition_paths import classify_precursor


class FormationTransitionPathTests(unittest.TestCase):
    def test_bull_semantic_context_bridge(self):
        self.assertEqual(classify_precursor(1, 2, 1.0), "semantic_context_bridge")
        self.assertEqual(classify_precursor(3, 1, 1.0), "semantic_context_bridge")

    def test_bear_semantic_context_bridge(self):
        self.assertEqual(classify_precursor(4, 5, -1.0), "semantic_context_bridge")
        self.assertEqual(classify_precursor(6, 4, -1.0), "semantic_context_bridge")

    def test_direct_opposite_actionable_flip_has_precedence(self):
        self.assertEqual(classify_precursor(5, 6, 1.0), "opposite_actionable_flip")
        self.assertEqual(classify_precursor(2, 3, -1.0), "opposite_actionable_flip")

    def test_other_one_stage_carry(self):
        self.assertEqual(classify_precursor(2, 4, 1.0), "one_stage_carry_other")
        self.assertEqual(classify_precursor(1, 5, -1.0), "one_stage_carry_other")

    def test_both_stages_new(self):
        self.assertEqual(classify_precursor(1, 4, 1.0), "both_stages_new")
        self.assertEqual(classify_precursor(1, 2, -1.0), "both_stages_new")


if __name__ == "__main__":
    unittest.main()
