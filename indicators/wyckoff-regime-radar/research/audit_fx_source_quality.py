#!/usr/bin/env python3
"""Audit Yahoo FX daily OHLC envelope quality for Issue #55.

This is a market-data diagnostic only. It does not run the Wyckoff model and
cannot inspect development/OOS utility. The purpose is to choose one common
canonical start date based on provider data quality rather than repeatedly
moving the start date after one fail-fast anomaly at a time.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

import pandas as pd
import yfinance as yf


AUDIT_START = "2000-01-01"
AUDIT_END_EXCLUSIVE = "2026-08-08"
MAX_SMALL_REPAIR_RELATIVE = 0.0002  # same 2 bps boundary as the freezer

PAIR_TICKERS: Mapping[str, str] = {
    "EURUSD": "EURUSD=X",
    "USDJPY": "JPY=X",
    "GBPUSD": "GBPUSD=X",
    "AUDUSD": "AUDUSD=X",
}


def normalize_raw(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        raise ValueError("provider returned no rows")
    work = frame.copy()
    if isinstance(work.columns, pd.MultiIndex):
        work.columns = [str(column[0]) for column in work.columns]
    work = work.reset_index()
    lower = {str(column).lower(): column for column in work.columns}
    date_column = next((lower[name] for name in ("date", "datetime") if name in lower), None)
    if date_column is None:
        raise ValueError(f"provider output missing date column: {list(work.columns)}")
    required = ["open", "high", "low", "close"]
    missing = [name for name in required if name not in lower]
    if missing:
        raise ValueError(f"provider output missing OHLC columns {missing}: {list(work.columns)}")
    rename = {date_column: "date", **{lower[name]: name for name in required}}
    out = work.rename(columns=rename)[["date", *required]].copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.date
    for column in required:
        out[column] = pd.to_numeric(out[column], errors="coerce")
    return (
        out.dropna(subset=["date", *required])
        .sort_values("date")
        .drop_duplicates(subset=["date"], keep="last")
        .reset_index(drop=True)
    )


def scan_envelope_violations(frame: pd.DataFrame) -> list[dict]:
    """Return every row where provider H/L does not contain O/C/L/H."""
    violations: list[dict] = []
    for _, row in frame.iterrows():
        close = float(row["close"])
        if close <= 0:
            violations.append(
                {
                    "date": str(row["date"]),
                    "field": "non_positive_price",
                    "relative_to_close": None,
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": close,
                    "severity": "large",
                }
            )
            continue

        high = float(row["high"])
        required_high = max(float(row["open"]), high, float(row["low"]), close)
        if high < required_high:
            relative = (required_high - high) / close
            violations.append(
                {
                    "date": str(row["date"]),
                    "field": "high",
                    "original": high,
                    "required_envelope": required_high,
                    "relative_to_close": relative,
                    "bps": relative * 10_000.0,
                    "open": float(row["open"]),
                    "high": high,
                    "low": float(row["low"]),
                    "close": close,
                    "severity": "small_repairable" if relative <= MAX_SMALL_REPAIR_RELATIVE else "large",
                }
            )

        low = float(row["low"])
        required_low = min(float(row["open"]), high, low, close)
        if low > required_low:
            relative = (low - required_low) / close
            violations.append(
                {
                    "date": str(row["date"]),
                    "field": "low",
                    "original": low,
                    "required_envelope": required_low,
                    "relative_to_close": relative,
                    "bps": relative * 10_000.0,
                    "open": float(row["open"]),
                    "high": high,
                    "low": low,
                    "close": close,
                    "severity": "small_repairable" if relative <= MAX_SMALL_REPAIR_RELATIVE else "large",
                }
            )
    return violations


def summarize_pair(frame: pd.DataFrame, violations: list[dict]) -> dict:
    small = [item for item in violations if item["severity"] == "small_repairable"]
    large = [item for item in violations if item["severity"] == "large"]
    large_years = Counter(item["date"][:4] for item in large)
    small_years = Counter(item["date"][:4] for item in small)
    latest_large = max((item["date"] for item in large), default=None)
    latest_any = max((item["date"] for item in violations), default=None)
    maximum = max(
        (item for item in violations if item.get("relative_to_close") is not None),
        key=lambda item: item["relative_to_close"],
        default=None,
    )
    return {
        "rows": len(frame),
        "start_date": str(frame.iloc[0]["date"]),
        "end_date": str(frame.iloc[-1]["date"]),
        "violation_count": len(violations),
        "small_repairable_count": len(small),
        "large_count": len(large),
        "latest_large_date": latest_large,
        "latest_any_violation_date": latest_any,
        "large_by_year": dict(sorted(large_years.items())),
        "small_repairable_by_year": dict(sorted(small_years.items())),
        "maximum_violation": maximum,
        "violations": violations,
    }


def download_pair(ticker: str) -> pd.DataFrame:
    frame = yf.download(
        ticker,
        start=AUDIT_START,
        end=AUDIT_END_EXCLUSIVE,
        interval="1d",
        auto_adjust=False,
        actions=False,
        progress=False,
        threads=False,
    )
    return normalize_raw(frame)


def build_report() -> dict:
    pairs: dict[str, dict] = {}
    for pair, ticker in PAIR_TICKERS.items():
        frame = download_pair(ticker)
        violations = scan_envelope_violations(frame)
        summary = summarize_pair(frame, violations)
        summary["ticker"] = ticker
        pairs[pair] = summary

    latest_large_dates = [
        meta["latest_large_date"] for meta in pairs.values() if meta["latest_large_date"] is not None
    ]
    overall_latest_large = max(latest_large_dates, default=None)
    return {
        "schema_version": 1,
        "issue": 55,
        "status": "provider_data_quality_audit_only",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "provider": "Yahoo Finance via yfinance",
        "audit_start": AUDIT_START,
        "audit_end_exclusive": AUDIT_END_EXCLUSIVE,
        "small_repair_limit_relative": MAX_SMALL_REPAIR_RELATIVE,
        "small_repair_limit_bps": MAX_SMALL_REPAIR_RELATIVE * 10_000.0,
        "overall_latest_large_violation_date": overall_latest_large,
        "pairs": pairs,
        "boundary": (
            "No Wyckoff calculation or utility statistic is run here. This audit may be used only to define "
            "a common canonical data-quality start date before the primary experiment is frozen."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_report()
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    compact = {
        "status": report["status"],
        "overall_latest_large_violation_date": report["overall_latest_large_violation_date"],
        "pairs": {
            pair: {
                "rows": meta["rows"],
                "large_count": meta["large_count"],
                "latest_large_date": meta["latest_large_date"],
                "small_repairable_count": meta["small_repairable_count"],
                "latest_any_violation_date": meta["latest_any_violation_date"],
                "maximum_violation": meta["maximum_violation"],
            }
            for pair, meta in report["pairs"].items()
        },
    }
    print(json.dumps(compact, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
