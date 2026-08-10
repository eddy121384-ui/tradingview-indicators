from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from freeze_static_fx_canonical_data import (  # noqa: E402
    git_blob_sha,
    serialize,
    sha256_bytes,
    split_metadata,
    validate_ohlc,
    verify,
)


class StaticCanonicalFxFreezeTests(unittest.TestCase):
    def make_frame(self, rows: int = 1000) -> pd.DataFrame:
        dates = pd.bdate_range("2012-01-02", periods=rows).date
        base = pd.Series(range(rows), dtype=float) * 0.00001 + 1.20
        return pd.DataFrame(
            {
                "date": dates,
                "open": base,
                "high": base + 0.002,
                "low": base - 0.002,
                "close": base + 0.001,
            }
        )

    def test_git_blob_sha_matches_git_object_rule(self) -> None:
        content = b"hello\n"
        expected = hashlib.sha1(b"blob 6\0hello\n").hexdigest()
        self.assertEqual(git_blob_sha(content), expected)

    def test_split_is_chronological_60_20_20(self) -> None:
        splits = split_metadata(self.make_frame(1000))
        self.assertEqual(splits["development"]["rows"], 600)
        self.assertEqual(splits["exploratory_oos"]["rows"], 200)
        self.assertEqual(splits["final_oos"]["rows"], 200)
        self.assertEqual(splits["development"]["end_index"], 599)
        self.assertEqual(splits["final_oos"]["start_index"], 800)

    def test_ohlc_violation_fails_closed_without_repair(self) -> None:
        frame = self.make_frame(1000)
        frame.loc[100, "high"] = frame.loc[100, "close"] - 0.01
        with self.assertRaises(ValueError):
            validate_ohlc(frame)

    def test_verify_detects_modified_frozen_file(self) -> None:
        frame = self.make_frame(1000)
        content = serialize(frame)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            frozen = root / "frozen"
            frozen.mkdir()
            path = frozen / "eurusd.csv"
            path.write_bytes(content)
            manifest_path = root / "manifest.json"
            manifest = {
                "canonical_fixture": "test",
                "final_oos_status": "SEALED_DO_NOT_EVALUATE",
                "pairs": {
                    "EURUSD": {
                        "frozen_file": "frozen/eurusd.csv",
                        "frozen_sha256": sha256_bytes(content),
                        "rows": len(frame),
                        "start_date": str(frame.iloc[0]["date"]),
                        "end_date": str(frame.iloc[-1]["date"]),
                        "splits": split_metadata(frame),
                    }
                },
            }
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            verify(manifest_path)
            path.write_bytes(content + b"\n")
            with self.assertRaises(ValueError):
                verify(manifest_path)


if __name__ == "__main__":
    unittest.main()
