from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from audit_fx_source_quality import scan_envelope_violations, summarize_pair  # noqa: E402


class FxSourceQualityAuditTests(unittest.TestCase):
    def make_frame(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "date": pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06"]).date,
                "open": [1.1000, 1.1000, 1.1000],
                "high": [1.1020, 1.1009, 1.0900],
                "low": [1.0980, 1.0980, 1.0980],
                "close": [1.1010, 1.1010, 1.1010],
            }
        )

    def test_scanner_distinguishes_small_and_large_envelope_defects(self) -> None:
        violations = scan_envelope_violations(self.make_frame())
        self.assertEqual(len(violations), 2)
        self.assertEqual(violations[0]["date"], "2020-01-03")
        self.assertEqual(violations[0]["severity"], "small_repairable")
        self.assertEqual(violations[1]["date"], "2020-01-06")
        self.assertEqual(violations[1]["severity"], "large")

    def test_summary_reports_latest_large_without_model_outputs(self) -> None:
        frame = self.make_frame()
        violations = scan_envelope_violations(frame)
        summary = summarize_pair(frame, violations)
        self.assertEqual(summary["large_count"], 1)
        self.assertEqual(summary["small_repairable_count"], 1)
        self.assertEqual(summary["latest_large_date"], "2020-01-06")
        self.assertNotIn("formal_id", summary)
        self.assertNotIn("prob_markdown", summary)


if __name__ == "__main__":
    unittest.main()
