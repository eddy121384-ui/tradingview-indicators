#!/usr/bin/env python3

from __future__ import annotations

import json
import unittest
from pathlib import Path

import pandas as pd

import download_rates_data as rates_data


class RatesDataTests(unittest.TestCase):
    def test_normalizes_legacy_date_column(self) -> None:
        frame = pd.DataFrame(
            {
                "DATE": ["2026-01-02", "2026-01-05"],
                "DGS2": [4.10, 4.08],
            }
        )
        normalized = rates_data.normalize_fred_frame(frame, "DGS2")
        self.assertEqual(normalized.index.name, "DATE")
        self.assertEqual(normalized.index[0], pd.Timestamp("2026-01-02"))
        self.assertAlmostEqual(normalized.iloc[1, 0], 4.08)

    def test_normalizes_current_observation_date_column(self) -> None:
        frame = pd.DataFrame(
            {
                "observation_date": ["2026-01-02", "2026-01-05"],
                "DGS10": [4.20, 4.18],
            }
        )
        normalized = rates_data.normalize_fred_frame(frame, "DGS10")
        self.assertEqual(normalized.index.name, "DATE")
        self.assertEqual(normalized.index[-1], pd.Timestamp("2026-01-05"))
        self.assertAlmostEqual(normalized.iloc[0, 0], 4.20)

    def test_rejects_unknown_date_column(self) -> None:
        frame = pd.DataFrame({"date": ["2026-01-02"], "DGS5": [4.0]})
        with self.assertRaisesRegex(ValueError, "unexpected FRED columns"):
            rates_data.normalize_fred_frame(frame, "DGS5")

    def test_committed_manifest_exactly_matches_frozen_csv(self) -> None:
        research_dir = Path(__file__).resolve().parent
        data_dir = research_dir / "data"
        frozen = data_dir / "issue-50-rates-2007-2026.csv.gz"
        manifest_path = data_dir / "issue-50-rates-2007-2026-manifest.json"
        if not frozen.exists() or not manifest_path.exists():
            self.skipTest("formal Issue #50 frozen input is not committed yet")

        frame = pd.read_csv(frozen)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected_keys = {
            "accepted_fred_date_columns",
            "columns",
            "contract",
            "end",
            "etf_source",
            "etf_tickers",
            "first_date",
            "fred_series",
            "join",
            "last_date",
            "rows",
            "start",
        }
        self.assertEqual(set(manifest), expected_keys)

        expected_columns = [
            "Date",
            "DGS3MO",
            "DGS2",
            "DGS5",
            "DGS10",
            "DGS30",
            "SHY",
            "IEF",
            "TLT",
        ]
        expected_start = "2007-01-01"
        expected_end = "2026-07-31"
        self.assertEqual(list(frame.columns), expected_columns)
        self.assertEqual(manifest["columns"], expected_columns)
        self.assertEqual(manifest["contract"], "issue-50-rates-v1")
        self.assertEqual(manifest["start"], expected_start)
        self.assertEqual(manifest["end"], expected_end)
        self.assertEqual(
            manifest["accepted_fred_date_columns"], ["DATE", "observation_date"]
        )
        self.assertEqual(manifest["etf_tickers"], ["SHY", "IEF", "TLT"])
        self.assertEqual(manifest["etf_source"], "yfinance auto_adjust=True")
        self.assertEqual(
            manifest["join"], "inner common observed dates; no yield interpolation"
        )
        self.assertEqual(
            manifest["fred_series"],
            {
                series: rates_data.fred_url(series, expected_start, expected_end)
                for series in rates_data.FRED_SERIES
            },
        )
        self.assertEqual(manifest["rows"], len(frame))
        self.assertEqual(manifest["first_date"], str(frame["Date"].iloc[0]))
        self.assertEqual(manifest["last_date"], str(frame["Date"].iloc[-1]))

        dates = pd.to_datetime(frame["Date"], errors="raise")
        self.assertTrue(dates.is_monotonic_increasing)
        self.assertFalse(dates.duplicated().any())


if __name__ == "__main__":
    unittest.main()
