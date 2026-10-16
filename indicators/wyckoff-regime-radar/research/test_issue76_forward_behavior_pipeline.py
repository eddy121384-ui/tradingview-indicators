#!/usr/bin/env python3
"""Tiny deterministic fixture tests for the Issue #76 log parser.

These tests validate parsing, de-duplication, horizon expansion, canonical event
labels, and direction alignment. They do not claim to independently validate the
production Pine classifier; that remains anchored to the frozen Issue #68 source
and a later TradingView smoke/spot-check of the research harness.
"""
from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

import parse_issue76_forward_behavior_logs as p


def marker(
    ticker: str,
    representation: str,
    event_time: int,
    event_bar: int,
    stage: int,
    prev: int,
    sign: float,
) -> str:
    parts = [
        "ISSUE76",
        "schema=1",
        f"ticker={ticker}",
        "tf=1D",
        f"repr={representation}",
        f"event_time={event_time}",
        f"event_bar={event_bar}",
        f"stage={stage}",
        f"prev={prev}",
        f"fresh={1 if stage != prev else 0}",
        f"transition={prev}>{stage}",
        "scale=0.01",
    ]
    for h in p.HORIZONS:
        raw = sign * h / 100.0
        norm = sign * h / 10.0
        parts.extend(
            [
                f"move{h}={raw}",
                f"norm{h}={norm}",
                f"mfe{h}={abs(raw) + 0.01}",
                f"mae{h}={-abs(raw) - 0.005}",
                f"mfen{h}={abs(norm) + 0.1}",
                f"maen{h}={-abs(norm) - 0.05}",
                f"rv{h}={0.001 * h}",
                f"rvn{h}={0.01 * h}",
            ]
        )
    return "|".join(parts)


class Issue76PipelineTest(unittest.TestCase):
    def test_parse_dedup_expand_and_summary(self) -> None:
        eur = marker("OANDA:EURUSD", "PRICE_LOG", 1609459200000, 100, 2, 1, +1.0)
        us10 = marker("TVC:US10Y", "YIELD_LEVEL", 1609545600000, 101, 5, 4, -1.0)

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "pine-logs.csv"
            with path.open("w", encoding="utf-8", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(["time", "level", "message"])
                w.writerow(["x", "info", "prefix " + eur])
                w.writerow(["x", "info", "prefix " + eur])  # duplicate by event key
                w.writerow(["y", "info", us10])

            events, metadata = p.load_events([path])
            self.assertEqual(metadata["marker_rows_total_before_dedup"], 3)
            self.assertEqual(metadata["event_rows_after_dedup"], 2)
            self.assertEqual(len(events), 2)

            long_rows = p.expand_horizons(events)
            self.assertEqual(len(long_rows), 8)
            summary = p.build_summary(long_rows)

            s12_h5 = next(
                r
                for r in summary
                if r["ticker"] == "OANDA:EURUSD"
                and r["event_type"] == "canonical_transition"
                and r["event_key"] == "S1->S2"
                and r["horizon"] == 5
            )
            self.assertEqual(s12_h5["n"], 1)
            self.assertAlmostEqual(float(s12_h5["aligned_hit_rate"]), 1.0)
            self.assertAlmostEqual(float(s12_h5["mean_raw_move"]), 0.05)

            s45_h10 = next(
                r
                for r in summary
                if r["ticker"] == "TVC:US10Y"
                and r["event_type"] == "canonical_transition"
                and r["event_key"] == "S4->S5"
                and r["horizon"] == 10
            )
            self.assertAlmostEqual(float(s45_h10["aligned_hit_rate"]), 1.0)
            self.assertAlmostEqual(float(s45_h10["positive_rate"]), 0.0)

    def test_reject_wrong_representation(self) -> None:
        bad = marker("TVC:FR10Y", "PRICE_LOG", 1609459200000, 100, 2, 1, +1.0)
        fields = p.parse_marker_text(bad)
        assert fields is not None
        with self.assertRaisesRegex(ValueError, "representation mismatch"):
            p.validate_event(fields)


if __name__ == "__main__":
    unittest.main()
