import importlib.util
import json
import math
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


MODULE_PATH = Path(__file__).with_name("characterize_states.py")
SPEC = importlib.util.spec_from_file_location("characterize_states", MODULE_PATH)
characterize_states = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(characterize_states)


def diagnostics() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "state": ["A", "B", "C"],
            "occupancy_all": [0.6, 0.2, 0.2],
            "occupancy_train": [0.6, 0.2, 0.2],
            "occupancy_oos": [0.6, 0.2, 0.2],
            "mean_duration_all": [5.0, 3.0, 2.0],
            "mean_duration_oos": [5.0, 3.0, 2.0],
            "self_transition_probability": [0.9, 0.8, 0.7],
        }
    )


def directional_frame(train_value: float, oos_value: float) -> pd.DataFrame:
    sample = ["train"] * 10 + ["out_of_sample"] * 10
    values = [train_value] * 10 + [oos_value] * 10
    return pd.DataFrame(
        {
            "sample": sample,
            "trend_strength": values,
            "atr_pct": [0.01] * 20,
            "standardized_return": [0.0] * 20,
            "forward_5d_return": values,
            "forward_20d_return": values,
            "posterior_A": [0.8] * 20,
            "posterior_B": [0.15] * 20,
            "posterior_C": [0.05] * 20,
        }
    )


class DirectionTests(unittest.TestCase):
    def assert_train_oos_reversal(self, train: float, oos: float) -> None:
        result, descriptions = characterize_states.characterize_states(
            directional_frame(train, oos), diagnostics()
        )
        state = result.set_index("state").loc["A"]
        self.assertNotEqual(state["train_direction"], state["oos_direction"])
        self.assertIn("train direction", state["contradictions"])
        self.assertNotEqual(state["confidence"], "high")
        self.assertTrue(descriptions["A"]["contradictions"])

    def test_positive_train_negative_oos_is_contradiction(self) -> None:
        self.assert_train_oos_reversal(0.5, -0.5)

    def test_negative_train_positive_oos_is_contradiction(self) -> None:
        self.assert_train_oos_reversal(-0.5, 0.5)

    def test_directional_train_flat_oos_limits_confidence(self) -> None:
        result, _ = characterize_states.characterize_states(
            directional_frame(0.5, 0.0), diagnostics()
        )
        state = result.set_index("state").loc["A"]
        self.assertEqual(state["oos_direction"], "flat")
        self.assertIn("flat out of sample", state["contradictions"])
        self.assertNotEqual(state["confidence"], "high")

    def test_low_occupancy_is_not_a_flat_oos_contradiction(self) -> None:
        low_occupancy = diagnostics()
        low_occupancy.loc[0, "occupancy_oos"] = 0.01
        result, _ = characterize_states.characterize_states(
            directional_frame(0.5, 0.0), low_occupancy
        )
        contradictions = result.set_index("state").loc["A", "contradictions"]
        self.assertNotIn("flat out of sample", contradictions)
        self.assertIn("low out-of-sample occupancy", contradictions)


class StrictJsonTests(unittest.TestCase):
    def test_non_finite_values_are_null_and_strict_parser_accepts_output(self) -> None:
        cleaned = characterize_states.strict_json_value(
            {
                "values": [float("nan"), float("inf"), -float("inf"), 1.25],
                "numpy": (np.float64("nan"), np.float64(2.5), np.int64(3)),
            }
        )
        encoded = json.dumps(cleaned, allow_nan=False)
        parsed = json.loads(
            encoded,
            parse_constant=lambda token: self.fail(f"non-standard token: {token}"),
        )
        self.assertEqual(parsed["values"], [None, None, None, 1.25])
        self.assertEqual(parsed["numpy"], [None, 2.5, 3])
        self.assertNotIn("NaN", encoded)
        self.assertNotIn("Infinity", encoded)


class EventCoverageTests(unittest.TestCase):
    def setUp(self) -> None:
        dates = pd.date_range("2020-01-01", "2020-01-10", tz="UTC")
        self.frame = pd.DataFrame(
            {
                "date": dates,
                "close": np.arange(100.0, 110.0),
                "dominant_state": ["A"] * 10,
                "posterior_A": [0.8] * 10,
                "posterior_B": [0.1] * 10,
                "posterior_C": [0.1] * 10,
            }
        )

    @staticmethod
    def event(start: str, end: str) -> list[dict[str, str]]:
        return [{"name": "test", "start": start, "end": end, "context": "synthetic"}]

    def test_complete_event_coverage(self) -> None:
        rows = characterize_states.analyze_events(
            self.frame, self.event("2020-01-02", "2020-01-09")
        )
        self.assertEqual(set(rows["coverage_status"]), {"complete"})
        self.assertEqual(set(rows["coverage_ratio"]), {1.0})

    def test_partial_event_coverage_is_auditable(self) -> None:
        rows = characterize_states.analyze_events(
            self.frame, self.event("2019-12-28", "2020-01-05")
        )
        self.assertEqual(set(rows["coverage_status"]), {"partial_coverage"})
        self.assertEqual(set(rows["actual_start"]), {"2020-01-01"})
        self.assertEqual(set(rows["actual_end"]), {"2020-01-05"})
        self.assertTrue(rows["coverage_ratio"].between(0.0, 1.0, inclusive="neither").all())

    def test_event_without_overlap_is_unavailable(self) -> None:
        rows = characterize_states.analyze_events(
            self.frame, self.event("2021-01-01", "2021-01-05")
        )
        self.assertEqual(rows.iloc[0]["coverage_status"], "unavailable")
        self.assertEqual(rows.iloc[0]["bars"], 0)
        self.assertTrue(math.isnan(rows.iloc[0]["average_posterior"]))


if __name__ == "__main__":
    unittest.main()
