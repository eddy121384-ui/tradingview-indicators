#!/usr/bin/env python3

from __future__ import annotations

import unittest

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


if __name__ == "__main__":
    unittest.main()
