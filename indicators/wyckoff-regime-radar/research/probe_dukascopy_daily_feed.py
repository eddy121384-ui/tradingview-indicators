#!/usr/bin/env python3
"""Probe Dukascopy yearly BID daily-candle files for Issue #55.

This is a source-qualification probe only. It downloads a small fixed set of
yearly files from Dukascopy's public datafeed, decodes the documented 24-byte
OHLC records, and checks chronology plus OHLC envelope integrity. No Wyckoff
calculation or utility statistic is run.
"""

from __future__ import annotations

import json
import lzma
import struct
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone


PAIRS = {
    "EURUSD": 0.00001,
    "USDJPY": 0.001,
    "GBPUSD": 0.00001,
    "AUDUSD": 0.00001,
}
YEARS = (2006, 2010, 2020, 2024, 2026)
RECORD = struct.Struct(">5If")  # seconds, open, close, low, high, volume


def url_for(pair: str, year: int) -> str:
    return f"https://datafeed.dukascopy.com/datafeed/{pair}/{year}/BID_candles_day_1.bi5"


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "Issue55Research/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def decode_year(content: bytes, year: int, price_scale: float) -> list[dict]:
    raw = lzma.decompress(content)
    if len(raw) % RECORD.size != 0:
        raise ValueError(f"decoded length {len(raw)} is not divisible by {RECORD.size}")
    anchor = datetime(year, 1, 1, tzinfo=timezone.utc)
    rows: list[dict] = []
    for offset in range(0, len(raw), RECORD.size):
        seconds, open_i, close_i, low_i, high_i, volume = RECORD.unpack_from(raw, offset)
        when = anchor + timedelta(seconds=int(seconds))
        rows.append(
            {
                "date": when.date().isoformat(),
                "timestamp": when.isoformat(),
                "open": open_i * price_scale,
                "high": high_i * price_scale,
                "low": low_i * price_scale,
                "close": close_i * price_scale,
                "volume": float(volume),
            }
        )
    return rows


def audit_rows(rows: list[dict], expected_year: int) -> dict:
    if not rows:
        raise ValueError("decoded file contains zero rows")
    dates = [row["date"] for row in rows]
    if dates != sorted(dates) or len(dates) != len(set(dates)):
        raise ValueError("decoded daily dates are not strictly increasing and unique")
    if any(int(date[:4]) != expected_year for date in dates):
        raise ValueError(f"decoded record falls outside expected year {expected_year}")
    violations = []
    for row in rows:
        required_high = max(row["open"], row["low"], row["close"])
        required_low = min(row["open"], row["high"], row["close"])
        if row["high"] < required_high or row["low"] > required_low:
            violations.append(row)
    return {
        "rows": len(rows),
        "first_date": dates[0],
        "last_date": dates[-1],
        "ohlc_envelope_violations": len(violations),
        "first_row": rows[0],
        "last_row": rows[-1],
    }


def main() -> None:
    report = {
        "status": "dukascopy_daily_feed_probe",
        "price_basis": "BID",
        "record_format": ">5If: seconds/open/close/low/high/volume",
        "pairs": {},
        "boundary": "Source qualification only; no Wyckoff or OOS outcome is computed.",
    }
    failures = []
    for pair, scale in PAIRS.items():
        pair_report = {}
        for year in YEARS:
            url = url_for(pair, year)
            try:
                content = fetch(url)
                rows = decode_year(content, year, scale)
                result = audit_rows(rows, year)
                result["url"] = url
                result["compressed_bytes"] = len(content)
                pair_report[str(year)] = result
            except (urllib.error.URLError, lzma.LZMAError, ValueError) as exc:
                pair_report[str(year)] = {"url": url, "error": f"{type(exc).__name__}: {exc}"}
                failures.append(f"{pair}/{year}: {exc}")
        report["pairs"][pair] = pair_report

    report["probe_failure_count"] = len(failures)
    report["failures"] = failures
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
