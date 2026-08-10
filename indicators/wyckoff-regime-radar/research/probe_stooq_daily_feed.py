#!/usr/bin/env python3
"""Probe Stooq daily FX CSV downloads for Issue #55.

Source qualification only: fetch one representative full year for each target
pair, parse OHLC, and verify chronology plus OHLC envelope integrity. No Wyckoff
calculation or OOS utility statistic is run.
"""

from __future__ import annotations

import csv
import io
import json
import socket
import urllib.error
import urllib.parse
import urllib.request


PAIRS = {
    "EURUSD": "eurusd",
    "USDJPY": "usdjpy",
    "GBPUSD": "gbpusd",
    "AUDUSD": "audusd",
}
START = "20240101"
END = "20241231"


def url_for(symbol: str) -> str:
    query = urllib.parse.urlencode({"s": symbol, "d1": START, "d2": END, "i": "d"})
    return f"https://stooq.com/q/d/l/?{query}"


def fetch_text(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 Issue55Research/1.0",
            "Accept": "text/csv,text/plain,*/*",
        },
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_csv(text: str) -> list[dict]:
    stripped = text.lstrip()
    if stripped.startswith("<"):
        raise ValueError("response is HTML, not CSV")
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise ValueError("CSV has no header")
    normalized = {name.lower(): name for name in reader.fieldnames}
    required = ["date", "open", "high", "low", "close"]
    missing = [name for name in required if name not in normalized]
    if missing:
        preview = text[:200].replace("\n", "\\n")
        raise ValueError(f"missing columns {missing}; header={reader.fieldnames}; preview={preview!r}")
    rows: list[dict] = []
    for raw in reader:
        try:
            row = {
                "date": raw[normalized["date"]],
                "open": float(raw[normalized["open"]]),
                "high": float(raw[normalized["high"]]),
                "low": float(raw[normalized["low"]]),
                "close": float(raw[normalized["close"]]),
            }
        except (TypeError, ValueError, KeyError) as exc:
            raise ValueError(f"malformed Stooq row: {raw}") from exc
        rows.append(row)
    return rows


def audit_rows(rows: list[dict]) -> dict:
    if len(rows) < 200:
        raise ValueError(f"expected a full daily year, got only {len(rows)} rows")
    dates = [row["date"] for row in rows]
    if dates != sorted(dates) or len(dates) != len(set(dates)):
        raise ValueError("dates are not strictly increasing and unique")
    violations = []
    nonpositive = []
    for row in rows:
        if min(row["open"], row["high"], row["low"], row["close"]) <= 0:
            nonpositive.append(row)
            continue
        if row["high"] < max(row["open"], row["low"], row["close"]):
            violations.append(row)
        elif row["low"] > min(row["open"], row["high"], row["close"]):
            violations.append(row)
    if nonpositive:
        raise ValueError(f"non-positive OHLC rows: {len(nonpositive)}; first={nonpositive[0]}")
    if violations:
        raise ValueError(f"OHLC envelope violations: {len(violations)}; first={violations[0]}")
    return {
        "rows": len(rows),
        "first_date": dates[0],
        "last_date": dates[-1],
        "ohlc_envelope_violations": 0,
        "first_row": rows[0],
        "last_row": rows[-1],
    }


def main() -> None:
    report = {
        "status": "stooq_daily_feed_probe",
        "period": {"start": START, "end": END},
        "pairs": {},
        "boundary": "Source qualification only; no Wyckoff or OOS outcome is computed.",
    }
    failures = []
    for pair, symbol in PAIRS.items():
        url = url_for(symbol)
        try:
            text = fetch_text(url)
            rows = parse_csv(text)
            result = audit_rows(rows)
            result["url"] = url
            result["response_bytes"] = len(text.encode("utf-8"))
            report["pairs"][pair] = result
        except (urllib.error.URLError, TimeoutError, socket.timeout, ValueError) as exc:
            report["pairs"][pair] = {"url": url, "error": f"{type(exc).__name__}: {exc}"}
            failures.append(f"{pair}: {exc}")

    report["probe_failure_count"] = len(failures)
    report["failures"] = failures
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
