from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from evaluate_final_oos import (  # noqa: E402
    CONTINUATION_LOOKBACK,
    episode_summary,
    path_summary,
)


class FinalOosEvaluatorTests(unittest.TestCase):
    def make_frame(self, rows: int = 200) -> pd.DataFrame:
        x = np.arange(rows, dtype=float)
        close = 1.10 + 0.0002 * x + 0.01 * np.sin(x / 9.0)
        return pd.DataFrame(
            {
                "date": pd.bdate_range("2020-01-01", periods=rows).date,
                "open": close - 0.0003,
                "high": close + 0.0015,
                "low": close - 0.0015,
                "close": close,
            }
        )

    def test_path_summary_never_uses_origin_past_final_minus_horizon(self) -> None:
        frame = self.make_frame(200)
        formal = np.full(200, 2, dtype=int)
        result = path_summary(frame, formal, start=100, end=159, horizon=20)
        self.assertEqual(result["eligible_origin_rows"], 40)
        self.assertEqual(result["by_formal_stage"]["2"]["sample_count"], 40)

    def test_all_six_stages_exist_in_final_path_schema_even_when_empty(self) -> None:
        frame = self.make_frame(200)
        formal = np.full(200, 5, dtype=int)
        result = path_summary(frame, formal, start=100, end=159, horizon=5)
        self.assertEqual(set(result["by_formal_stage"]), {"1", "2", "3", "4", "5", "6"})
        self.assertEqual(result["by_formal_stage"]["1"]["sample_count"], 0)
        self.assertGreater(result["by_formal_stage"]["5"]["sample_count"], 0)

    def test_episode_summary_reports_transition_counts(self) -> None:
        formal = np.array([2, 2, 5, 5, 4, 4, 2, 2], dtype=int)
        result = episode_summary(formal, 0, 7)
        self.assertEqual(result["stages"]["2"]["next_state_counts"]["5"], 1)
        self.assertEqual(result["stages"]["5"]["next_state_counts"]["4"], 1)
        self.assertEqual(result["stages"]["4"]["next_state_counts"]["2"], 1)

    def test_continuation_lookback_is_fixed_at_twenty(self) -> None:
        self.assertEqual(CONTINUATION_LOOKBACK, 20)


if __name__ == "__main__":
    unittest.main()
