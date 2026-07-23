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
    def variant(selected_k=None, dimensions=3, fits=None, k=4):
        candidates = []
        if fits is not None:
            candidates.append({"k": k, "status": "ok", "fits": fits})
        return {
            "decision": {"selected_k": selected_k},
            "method": {"features": [f"feature_{index}" for index in range(dimensions)]},
            "candidates": candidates,
        }

    @staticmethod
    def fit(separation, likelihood_drift, occupancy_drift):
        return {
            "minimum_pairwise_separation": separation,
            "train_oos_likelihood_drift": likelihood_drift,
            "occupancy_drift_l1": occupancy_drift,
        }

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

    def test_dimension_normalization_rejects_raw_separation_inflation(self):
        baseline = self.variant(
            dimensions=3,
            fits=[self.fit(1.8, 0.9, 0.4), self.fit(1.9, 0.8, 0.3)],
        )
        enriched = self.variant(
            selected_k=4,
            dimensions=4,
            fits=[self.fit(2.0, 0.7, 0.3), self.fit(2.1, 0.6, 0.2)],
        )
        raw = features.cross_feature_diagnostics(enriched["candidates"][0], 4)
        self.assertEqual(raw["raw_worst_seed"]["minimum_separation"], 2.0)
        self.assertEqual(raw["normalized_worst_seed"]["minimum_separation_per_sqrt_dimension"], 1.0)
        self.assertFalse(features.materially_clearer(baseline, enriched))

    def test_hidden_bad_seed_prevents_material_improvement(self):
        baseline = self.variant(
            dimensions=3,
            fits=[self.fit(1.5, 0.9, 0.4)] * 3,
        )
        enriched = self.variant(
            selected_k=4,
            dimensions=4,
            fits=[
                self.fit(2.4, 0.5, 0.2),
                self.fit(2.4, 0.5, 0.2),
                self.fit(1.6, 1.4, 0.6),
            ],
        )
        self.assertFalse(features.materially_clearer(baseline, enriched))

    def test_genuine_enriched_feature_improvement_is_selected(self):
        baseline = self.variant(
            dimensions=3,
            fits=[self.fit(1.5, 0.9, 0.4), self.fit(1.6, 0.8, 0.35)],
        )
        enriched = self.variant(
            selected_k=4,
            dimensions=4,
            fits=[self.fit(2.2, 0.8, 0.3), self.fit(2.3, 0.7, 0.25)],
        )
        variants = {
            "baseline": baseline,
            "baseline_er": enriched,
            "baseline_er_downside": self.variant(dimensions=5),
        }
        decision = features.choose_feature_set(variants)
        self.assertEqual(decision["outcome"], "select_feature_set")
        self.assertEqual(decision["selected_feature_set"], "baseline_er")
        self.assertEqual(decision["selected_k"], 4)

    def test_non_material_normalized_improvement_is_rejected(self):
        baseline = self.variant(
            dimensions=3,
            fits=[self.fit(np.sqrt(3), 0.9, 0.4)],
        )
        enriched = self.variant(
            selected_k=4,
            dimensions=4,
            fits=[self.fit(2.1, 1.14, 0.38)],
        )
        self.assertFalse(features.materially_clearer(baseline, enriched))


if __name__ == "__main__":
    unittest.main()
