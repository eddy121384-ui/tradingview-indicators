from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from evaluate_regime_paths_pre_final import analyze_pair, future_metrics  # noqa: E402


class PreFinalRegimePathTests(unittest.TestCase):
    def make_frame(self, rows: int = 1200) -> pd.DataFrame:
        x = np.arange(rows, dtype=float)
        close = 1.10 + 0.00005 * x + 0.01 * np.sin(x / 17.0)
        return pd.DataFrame(
            {
                "date": pd.bdate_range("2010-01-04", periods=rows).date,
                "open": close - 0.0002,
                "high": close + 0.0015,
                "low": close - 0.0015,
                "close": close,
            }
        )

    def metadata(self) -> dict:
        return {
            "splits": {
                "development": {
                    "start_index": 0,
                    "end_index": 719,
                    "start_date": "2010-01-04",
                    "end_date": "2012-10-05",
                    "rows": 720,
                },
                "exploratory_oos": {
                    "start_index": 720,
                    "end_index": 959,
                    "start_date": "2012-10-08",
                    "end_date": "2013-09-06",
                    "rows": 240,
                },
                "final_oos": {
                    "start_index": 960,
                    "end_index": 1199,
                    "start_date": "2013-09-09",
                    "end_date": "2014-08-08",
                    "rows": 240,
                },
            }
        }

    def test_future_metric_does_not_exist_past_input_end(self) -> None:
        metrics = future_metrics(self.make_frame(100), 20)
        self.assertTrue(np.isnan(metrics["forward_return"][80:]).all())
        self.assertTrue(np.isfinite(metrics["forward_return"][79]))

    def test_analyzer_never_computes_final_oos_rows(self) -> None:
        result = analyze_pair(self.make_frame(), self.metadata())
        self.assertEqual(result["model_rows_computed"], 960)
        self.assertEqual(result["final_oos_rows_computed"], 0)
        self.assertEqual(
            result["splits"]["exploratory_oos"]["horizons"]["60"]["eligible_origin_rows"],
            180,
        )


if __name__ == "__main__":
    unittest.main()
