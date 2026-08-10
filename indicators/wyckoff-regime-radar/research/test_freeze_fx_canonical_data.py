from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from freeze_fx_canonical_data import (  # noqa: E402
    chronological_splits,
    repair_ohlc_envelope,
    serialize_ohlc,
    sha256_bytes,
    validate_ohlc,
    verify,
)


class CanonicalFxFreezeTests(unittest.TestCase):
    def make_frame(self, rows: int = 10) -> pd.DataFrame:
        dates = pd.bdate_range("2020-01-01", periods=rows).date
        base = pd.Series(range(rows), dtype=float) * 0.001 + 1.10
        return pd.DataFrame(
            {
                "date": dates,
                "open": base,
                "high": base + 0.002,
                "low": base - 0.002,
                "close": base + 0.001,
            }
        )

    def test_split_is_exact_chronological_60_20_20(self) -> None:
        frame = self.make_frame(10)
        splits = chronological_splits(frame)
        self.assertEqual([split.rows for split in splits], [6, 2, 2])
        self.assertEqual(splits[0].start_index, 0)
        self.assertEqual(splits[0].end_index, 5)
        self.assertEqual(splits[1].start_index, 6)
        self.assertEqual(splits[1].end_index, 7)
        self.assertEqual(splits[2].start_index, 8)
        self.assertEqual(splits[2].end_index, 9)

    def test_serialization_and_checksum_are_deterministic(self) -> None:
        frame = self.make_frame(10)
        first = serialize_ohlc(frame)
        second = serialize_ohlc(frame.copy())
        self.assertEqual(first, second)
        self.assertEqual(sha256_bytes(first), sha256_bytes(second))
        self.assertTrue(first.startswith(b"date,open,high,low,close\n"))

    def test_invalid_ohlc_is_rejected(self) -> None:
        frame = self.make_frame(10)
        frame.loc[3, "high"] = frame.loc[3, "low"] - 0.01
        with self.assertRaises(ValueError):
            validate_ohlc(frame)

    def test_small_envelope_violation_is_minimally_repaired_and_recorded(self) -> None:
        frame = self.make_frame(10)
        original_close = float(frame.loc[3, "close"])
        frame.loc[3, "high"] = original_close - 0.0001
        repairs = repair_ohlc_envelope(frame)
        self.assertEqual(len(repairs), 1)
        self.assertEqual(repairs[0]["field"], "high")
        self.assertAlmostEqual(float(frame.loc[3, "high"]), original_close)
        self.assertAlmostEqual(float(frame.loc[3, "close"]), original_close)
        validate_ohlc(frame)

    def test_large_envelope_violation_fails_closed(self) -> None:
        frame = self.make_frame(10)
        frame.loc[3, "high"] = float(frame.loc[3, "close"]) - 0.01
        with self.assertRaises(ValueError):
            repair_ohlc_envelope(frame)

    def test_verify_fails_closed_if_frozen_csv_is_modified(self) -> None:
        frame = self.make_frame(10)
        content = serialize_ohlc(frame)
        splits = {split.name: split.__dict__ for split in chronological_splits(frame)}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "frozen"
            data_dir.mkdir()
            csv_path = data_dir / "eurusd.csv"
            csv_path.write_bytes(content)
            manifest_path = root / "manifest.json"
            manifest = {
                "canonical_feed": "test",
                "snapshot_last_complete_bar": "2020-01-14",
                "final_oos_status": "SEALED_DO_NOT_EVALUATE",
                "pairs": {
                    "EURUSD": {
                        "file": "frozen/eurusd.csv",
                        "sha256": sha256_bytes(content),
                        "rows": len(frame),
                        "start_date": str(frame.iloc[0]["date"]),
                        "end_date": str(frame.iloc[-1]["date"]),
                        "splits": splits,
                    }
                },
            }
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            verify(manifest_path)
            csv_path.write_bytes(content + b"\n")
            with self.assertRaises(ValueError):
                verify(manifest_path)


if __name__ == "__main__":
    unittest.main()
