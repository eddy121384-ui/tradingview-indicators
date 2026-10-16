#!/usr/bin/env python3
"""Small deterministic source-contract tests; no finance outcomes or PTM tuning."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import tempfile
import unittest
from pathlib import Path

import validate_issue185_absolute_ohlc as v


def old_item(repr_name: str, t: int, bar: int, close: float,
             next_high: float, next_low: float, next_close: float):
    return {
        "repr": repr_name, "time": t, "bar": bar,
        "move1": v.historical_identity(repr_name, close, next_close),
        "mfe1": v.historical_identity(repr_name, close, next_high),
        "mae1": v.historical_identity(repr_name, close, next_low),
    }


def candle(t: int, bar: int, o: float, h: float, l: float, c: float):
    return {"time": t, "bar": bar, "o": o, "h": h, "l": l, "c": c}


class AbsoluteOHLCExportTest(unittest.TestCase):
    def test_frozen_pine_is_research_only_and_absolute(self):
        src = (Path(__file__).parent / "issue185_absolute_ohlc_logger.pine").read_text()
        self.assertIn("//@version=6", src)
        self.assertIn("ISSUE185OHLC|schema=1", src)
        self.assertIn("chart.is_standard", src)
        self.assertIn("barstate.isconfirmed", src)
        self.assertIn("str.tostring(time)", src)
        for label in ('"|o="', '"|h="', '"|l="', '"|c="'):
            self.assertIn(label, src)
        self.assertNotIn("strategy.entry(", src)
        self.assertNotIn("request.security(", src)
        self.assertNotIn("ISSUE76|schema=1", src)

    def test_move_mfe_mae_source_parity_both_representations(self):
        t = 1680000000000
        fx, yld = "OANDA:EURUSD", "TVC:US10Y"
        old = {
            (fx, t): old_item("PRICE_LOG", t, 50, 1.07456, 1.0839, 1.073,
                              1.081),
            (yld, t): old_item("YIELD_LEVEL", t, 600, -0.234, -0.222, -0.290,
                               -0.250),
        }
        new = {
            (fx, t): candle(t, 1000, 1.075, 1.078, 1.074, 1.07456),
            (fx, t+86400000): candle(t+86400000, 1001, 1.077, 1.0839,
                                     1.073, 1.081),
            (yld, t): candle(t, 650, -0.24, -0.23, -0.25, -0.234),
            (yld, t+86400000): candle(t+86400000, 651, -0.252,
                                      -0.222, -0.290, -0.250),
        }
        result = v.audit(old, new, expected={fx, yld})
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["matched_events"], 2)
        self.assertEqual(result["missing_next_price_bar"], 0)
        self.assertEqual(result["bar_index_offset_varieties"][fx], 1)

    def test_missing_successor_cannot_be_called_parity_pass(self):
        t = 1680000000000
        sym = "OANDA:EURUSD"
        old = {(sym, t): old_item("PRICE_LOG", t, 100, 1.10, 1.12, 1.09, 1.11)}
        current = candle(t, 99, 1.1, 1.11, 1.09, 1.10)
        future = candle(t + 172800000, 101, 1.1, 1.12, 1.09, 1.11)
        result = v.audit(old, {(sym, t): current, (sym, future["time"]): future},
                         expected={sym})
        self.assertNotEqual(result["status"], "PASS")
        self.assertEqual(result["missing_next_price_bar"], 1)

    def test_changed_feed_is_not_a_roundoff_error(self):
        t = 1680000000000
        sym = "TVC:US10Y"
        old = {(sym, t): old_item("YIELD_LEVEL", t, 10, 4.01, 4.04, 3.99, 4.02)}
        new = {
            (sym, t): candle(t, 20, 4.01, 4.02, 4.00, 4.01),
            (sym, t + 86400000): candle(t + 86400000, 21, 4.02, 4.05, 3.99, 4.03),
        }
        result = v.audit(old, new, expected={sym})
        self.assertNotEqual(result["status"], "PASS")
        self.assertGreater(result["move1_mismatch"], 0)

    def test_parser_rejects_nonstandard_prices_and_conflicting_dup(self):
        lines = [
            "ISSUE185OHLC|schema=1|ticker=OANDA:GBPUSD|tf=1D|repr=PRICE_LOG"
            "|time=1680000000000|bar=20|o=1.20|h=1.23|l=1.19|c=1.22",
            "ISSUE185OHLC|schema=1|ticker=OANDA:GBPUSD|tf=1D|repr=PRICE_LOG"
            "|time=1680000000000|bar=21|o=1.20|h=1.24|l=1.19|c=1.22",
        ]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "new.csv"
            with path.open("w", encoding="utf-8", newline="") as fh:
                w = csv.writer(fh)
                for line in lines:
                    w.writerow(["date", "info", line])
            with self.assertRaisesRegex(ValueError, "conflicting absolute"):
                v.parse_new([path])
            path.write_text(
                lines[0].replace("|h=1.23|", "|h=1.18|") + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "OHLC envelope invalid"):
                v.parse_new([path])

    def test_manifest_compares_bytes_and_hashes_not_filenames(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            old = directory / "downloads (3).csv"
            old.write_bytes(b"frozen private source bytes")
            h = hashlib.sha256(old.read_bytes()).hexdigest()
            manifest = directory / "manifest.json"
            manifest.write_text(json.dumps({"manifest": [
                {"name": "original.csv", "sha256": h, "bytes": old.stat().st_size},
            ]}), encoding="utf-8")
            v.verify_frozen_old_inputs([old], manifest)
            old.write_bytes(b"modified")
            with self.assertRaisesRegex(ValueError, "do not mix datasets"):
                v.verify_frozen_old_inputs([old], manifest)


if __name__ == "__main__":
    unittest.main()
