import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


RESEARCH_DIR = Path(__file__).resolve().parent
ROOT = RESEARCH_DIR.parent
PROFILE_PATH = ROOT / "models" / "spy-1d-v0.1.json"
FIXTURE_PATH = RESEARCH_DIR / "fixtures" / "spy-1d-parity-checkpoints.json"
COMPARATOR_PATH = RESEARCH_DIR / "compare_pine_export.py"
SPEC = importlib.util.spec_from_file_location("compare_pine_export", COMPARATOR_PATH)
compare_pine_export = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(compare_pine_export)


class FrozenProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))

    def test_profile_dimensions_and_probabilities(self) -> None:
        self.assertEqual(self.profile["profile_id"], "spy-1d-v0.1")
        self.assertEqual(
            self.profile["feature_names"],
            ["standardized_return", "atr_pct", "trend_strength"],
        )
        scaler = self.profile["scaler"]
        self.assertEqual(len(scaler["mean"]), 3)
        self.assertEqual(len(scaler["scale"]), 3)
        self.assertTrue(all(value > 0.0 for value in scaler["scale"]))

        hmm = self.profile["hmm"]
        self.assertEqual(len(hmm["start_probability"]), 3)
        self.assertAlmostEqual(sum(hmm["start_probability"]), 1.0, places=12)
        self.assertEqual(np.asarray(hmm["transition_matrix"]).shape, (3, 3))
        self.assertEqual(np.asarray(hmm["emission_means"]).shape, (3, 3))
        variances = np.asarray(hmm["emission_variances"], dtype=float)
        self.assertEqual(variances.shape, (3, 3))
        self.assertTrue((variances > 0.0).all())
        for row in hmm["transition_matrix"]:
            self.assertAlmostEqual(sum(row), 1.0, places=12)


class CheckpointFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_checkpoints_are_sorted_unique_and_normalized(self) -> None:
        checkpoints = self.fixture["checkpoints"]
        dates = [row["date"] for row in checkpoints]
        self.assertEqual(dates, sorted(dates))
        self.assertEqual(len(dates), len(set(dates)))
        self.assertGreaterEqual(len(checkpoints), 10)
        for row in checkpoints:
            posteriors = {
                state: float(row[f"posterior_{state}"]) for state in "ABC"
            }
            self.assertAlmostEqual(sum(posteriors.values()), 1.0, places=12)
            self.assertEqual(max(posteriors, key=posteriors.get), row["dominant_state"])


class ComparatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def exact_export(self) -> pd.DataFrame:
        rows = []
        for checkpoint in self.fixture["checkpoints"]:
            rows.append(
                {
                    "time": checkpoint["date"],
                    "HRM SPY Parity: HRM Adjusted Close": checkpoint["close"],
                    "HRM SPY Parity: HRM Standardized Return": checkpoint[
                        "standardized_return"
                    ],
                    "HRM SPY Parity: HRM ATR Percent": checkpoint["atr_pct"],
                    "HRM SPY Parity: HRM Trend Strength": checkpoint[
                        "trend_strength"
                    ],
                    "HRM SPY Parity: HRM Posterior A": checkpoint["posterior_A"],
                    "HRM SPY Parity: HRM Posterior B": checkpoint["posterior_B"],
                    "HRM SPY Parity: HRM Posterior C": checkpoint["posterior_C"],
                    "HRM SPY Parity: HRM Probability Sum": (
                        checkpoint["posterior_A"]
                        + checkpoint["posterior_B"]
                        + checkpoint["posterior_C"]
                    ),
                }
            )
        return pd.DataFrame(rows)

    def test_exact_export_has_negligible_roundtrip_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            export_path = Path(directory) / "export.csv"
            self.exact_export().to_csv(export_path, index=False)
            result = compare_pine_export.compare(export_path, FIXTURE_PATH)
        self.assertEqual(
            result["checkpoint_count"], len(self.fixture["checkpoints"])
        )
        self.assertEqual(
            result["dominant_state_matches"], result["checkpoint_count"]
        )
        self.assertTrue(
            all(error == 0.0 for error in result["max_feature_errors"].values())
        )
        self.assertTrue(
            all(
                error <= 1e-15
                for error in result["max_posterior_errors"].values()
            )
        )
        self.assertLessEqual(result["max_probability_sum_error"], 1e-15)

    def test_missing_checkpoint_date_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            export_path = Path(directory) / "export.csv"
            self.exact_export().iloc[1:].to_csv(export_path, index=False)
            with self.assertRaisesRegex(ValueError, "missing checkpoint dates"):
                compare_pine_export.compare(export_path, FIXTURE_PATH)


if __name__ == "__main__":
    unittest.main()
