import importlib.util
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


MODULE_PATH = Path(__file__).with_name("compare_feature_sets.py")
SPEC = importlib.util.spec_from_file_location("compare_feature_sets", MODULE_PATH)
features = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(features)


class FormulaTests(unittest.TestCase):
    @staticmethod
    def frame(closes):
        return pd.DataFrame({
            "date": pd.date_range("2020-01-01", periods=len(closes), tz="UTC"),
            "close": closes,
        })

    def test_signed_efficiency_ratio_formula(self):
        closes = [100.0 + index for index in range(21)]
        result = features.calculate_path_features(self.frame(closes))
        self.assertAlmostEqual(result.loc[20, features.EFFICIENCY_RATIO], 1.0)

        alternating = [100.0 + (index % 2) for index in range(21)]
        result = features.calculate_path_features(self.frame(alternating))
        self.assertAlmostEqual(result.loc[20, features.EFFICIENCY_RATIO], 0.0)

    def test_downside_variance_share_formula(self):
        returns = np.asarray([0.01, -0.02] * 10)
        closes = 100.0 * np.exp(np.r_[0.0, returns].cumsum())
        result = features.calculate_path_features(self.frame(closes))
        expected = 10 * 0.02**2 / (10 * 0.01**2 + 10 * 0.02**2)
        self.assertAlmostEqual(result.loc[20, features.DOWNSIDE_SHARE], expected)

    def test_zero_path_length_and_total_variance_are_zero(self):
        result = features.calculate_path_features(self.frame([100.0] * 21))
        self.assertEqual(result.loc[20, features.EFFICIENCY_RATIO], 0.0)
        self.assertEqual(result.loc[20, features.DOWNSIDE_SHARE], 0.0)

    def test_causal_warm_up_and_no_lookahead(self):
        closes = [100.0 + index for index in range(30)]
        original = features.calculate_path_features(self.frame(closes))
        changed = list(closes)
        changed[25:] = [1000.0] * 5
        revised = features.calculate_path_features(self.frame(changed))
        self.assertTrue(original.loc[:19, [features.EFFICIENCY_RATIO, features.DOWNSIDE_SHARE]].isna().all().all())
        self.assertTrue(original.loc[20:, [features.EFFICIENCY_RATIO, features.DOWNSIDE_SHARE]].notna().all().all())
        pd.testing.assert_frame_equal(original.loc[:24], revised.loc[:24])


class VariantDecisionTests(unittest.TestCase):
    def test_exact_feature_set_membership_and_order(self):
        self.assertEqual(list(features.FEATURE_SETS), ["baseline", "baseline_er", "baseline_er_downside"])
        self.assertEqual(features.FEATURE_SETS["baseline"], tuple(features.train_hmm.FEATURE_NAMES))
        self.assertEqual(features.FEATURE_SETS["baseline_er"][-1], features.EFFICIENCY_RATIO)
        self.assertEqual(features.FEATURE_SETS["baseline_er_downside"][-2:], (features.EFFICIENCY_RATIO, features.DOWNSIDE_SHARE))

    @staticmethod
    def variant(selected_k=None):
        return {"decision": {"selected_k": selected_k}, "candidates": []}

    def test_deterministic_variant_comparison(self):
        variants = {
            "baseline": self.variant(3),
            "baseline_er": self.variant(4),
            "baseline_er_downside": self.variant(5),
        }
        first = features.choose_feature_set(variants)
        second = features.choose_feature_set(variants)
        self.assertEqual(first, second)
        self.assertEqual(first["outcome"], "retain_baseline")
        self.assertEqual(first["selected_feature_set"], "baseline")

    def test_no_stable_feature_set_keeps_productization_paused(self):
        variants = {name: self.variant() for name in features.FEATURE_SETS}
        decision = features.choose_feature_set(variants)
        self.assertEqual(decision["outcome"], "keep_productization_paused")
        self.assertIsNone(decision["selected_feature_set"])
        self.assertIsNone(decision["selected_k"])


if __name__ == "__main__":
    unittest.main()
