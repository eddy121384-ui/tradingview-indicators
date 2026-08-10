#!/usr/bin/env python3
"""Probe FXCM public yearly D1 candle files for Issue #55.

The endpoint shape follows FXCM's public MarketData repository documentation.
This source-qualification probe checks recent-year availability, parseability,
chronology, bar calendar, and OHLC envelope integrity for the four target pairs.
No Wyckoff calculation or OOS utility statistic is run.
"""

from __future__ import annotations

import csv
import gzip
import io
import json
import socket
import urllib.error
import urllib.request
from datetime import datetime


PAIRS = ("EURUSD", "USDJPY", "GBPUSD", "AUDUSD")
YEARS = (2024, 2025)


def url_for(pair: str, year: int) -> str:
    return f"https://candledata.fxcorporate.com/D1/{pair}/{year}.csv.gz"


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "Issue55Research/1.0"})
    with urllib.request.urlopen(request, timeout=15) as response:
        return response.read()


def _find_column(fieldnames: list[str], candidates: tuple[str, ...]) -> str | None:
    normalized = {name.strip().lower().replace(" ", "").replace("_", ""): name for name in fieldnames}
    for candidate in candidates:
        key = candidate.lower().replace(" ", "").replace("_", "")
        if key in normalized:
            return normalized[key]
    return None


def parse_rows(content: bytes) -> list[dict]:
    text = gzip.decompress(content).decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError("FXCM CSV has no header")
    fields = list(reader.fieldnames)
    date_col = _find_column(fields, ("DateTime", "Date", "Time"))
    open_col = _find_column(fields, ("BidOpen", "Open", "AskOpen"))
    high_col = _find_column(fields, ("BidHigh", "High", "AskHigh"))
    low_col = _find_column(fields, ("BidLow", "Low", "AskLow"))
    close_col = _find_column(fields, ("BidClose", "Close", "AskClose"))
    missing = [
        name
        for name, column in {
            "date": date_col,
            "open": open_col,
            "high": high_col,
            "low": low_col,
            "close": close_col,
        }.items()
        if column is None
    ]
    if missing:
        preview = text[:300].replace("\n", "\\n")
        raise ValueError(f"FXCM CSV missing {missing}; header={fields}; preview={preview!r}")

    rows = []
    for raw in reader:
        stamp = str(raw[date_col]).strip()
        parsed = None
        for fmt in (
            "%m/%d/%Y %H:%M:%S",
            "%m/%d/%Y %H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ):
            try:
                parsed = datetime.strptime(stamp, fmt)
                break
            except ValueError:
                pass
        if parsed is None:
            raise ValueError(f"unrecognized FXCM timestamp {stamp!r}")
        rows.append(
            {
                "date": parsed.date().isoformat(),
                "weekday": parsed.weekday(),
                "open": float(raw[open_col]),
                "high": float(raw[high_col]),
                "low": float(raw[low_col]),
                "close": float(raw[close_col]),
            }
        )
    return rows


def audit(rows: list[dict], year: int) -> dict:
    if len(rows) < 200:
        raise ValueError(f"expected full daily year, got {len(rows)} rows")
    dates = [row["date"] for row in rows]
    if dates != sorted(dates) or len(dates) != len(set(dates)):
        raise ValueError("FXCM dates not unique and ascending")
    violations = []
    weekend = []
    for row in rows:
        if row["high"] < max(row["open"], row["low"], row["close"]) or row["low"] > min(
            row["open"], row["high"], row["close"]
        ):
            violations.append(row)
        if row["weekday"] >= 5:
            weekend.append(row)
    if violations:
        raise ValueError(f"FXCM OHLC envelope violations={len(violations)} first={violations[0]}")
    return {
        "rows": len(rows),
        "first_date": dates[0],
        "last_date": dates[-1],
        "weekend_rows": len(weekend),
        "ohlc_envelope_violations": 0,
        "first_row": rows[0],
        "last_row": rows[-1],
    }


def main() -> None:
    report = {
        "status": "fxcm_public_d1_probe",
        "pairs": {},
        "years": list(YEARS),
        "boundary": "Source qualification only; no Wyckoff or OOS outcome is computed.",
    }
    failures = []
    for pair in PAIRS:
        pair_report = {}
        for year in YEARS:
            url = url_for(pair, year)
            try:
                content = fetch(url)
                rows = parse_rows(content)
                result = audit(rows, year)
                result["url"] = url
                result["compressed_bytes"] = len(content)
                pair_report[str(year)] = result
            except (urllib.error.URLError, gzip.BadGzipFile, OSError, TimeoutError, socket.timeout, ValueError) as exc:
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
