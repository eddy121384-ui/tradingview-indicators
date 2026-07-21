#!/usr/bin/env python3
"""Download one daily market series from Yahoo Finance into the prototype CSV shape."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download one Yahoo Finance ticker as chronological OHLC CSV."
    )
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--start", default="2010-01-01")
    parser.add_argument("--end", default=None)
    parser.add_argument("--interval", default="1d")
    parser.add_argument(
        "--raw-prices",
        action="store_true",
        help="Keep unadjusted OHLC. The default uses split/dividend-adjusted OHLC.",
    )
    return parser.parse_args()


def canonicalize_float_noise(result: pd.DataFrame) -> pd.DataFrame:
    """Repair only machine-epsilon OHLC ordering noise from adjusted prices."""
    high_bound = result[["Open", "High", "Low", "Close"]].max(axis=1)
    low_bound = result[["Open", "High", "Low", "Close"]].min(axis=1)
    scale = result[["Open", "High", "Low", "Close"]].abs().max(axis=1).clip(lower=1.0)
    tolerance = scale * 1e-12

    high_gap = high_bound - result["High"]
    low_gap = result["Low"] - low_bound
    if (high_gap > tolerance).any():
        raise RuntimeError("download contains a material high-price ordering violation")
    if (low_gap > tolerance).any():
        raise RuntimeError("download contains a material low-price ordering violation")

    result = result.copy()
    result["High"] = high_bound
    result["Low"] = low_bound
    return result


def download(args: argparse.Namespace) -> pd.DataFrame:
    ticker = args.ticker.strip().upper()
    if not ticker:
        raise ValueError("ticker must not be empty")

    frame = yf.download(
        ticker,
        start=args.start,
        end=args.end,
        interval=args.interval,
        auto_adjust=not args.raw_prices,
        actions=False,
        repair=True,
        keepna=False,
        progress=False,
        threads=False,
        timeout=30,
        multi_level_index=False,
    )
    if frame is None or frame.empty:
        raise RuntimeError(f"no data returned for {ticker}")

    frame = frame.reset_index()
    date_column = "Date" if "Date" in frame.columns else "Datetime"
    required = [date_column, "Open", "High", "Low", "Close"]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise RuntimeError(f"download missing columns: {', '.join(missing)}")

    result = frame[required].rename(columns={date_column: "Date"}).copy()
    result["Date"] = pd.to_datetime(result["Date"], errors="raise", utc=True)
    for column in ("Open", "High", "Low", "Close"):
        result[column] = pd.to_numeric(result[column], errors="raise")

    result = result.sort_values("Date").drop_duplicates("Date", keep="last")
    result = result.dropna(subset=["Date", "Open", "High", "Low", "Close"])
    if len(result) < 400:
        raise RuntimeError(f"only {len(result)} usable rows returned for {ticker}")
    if not np.isfinite(result[["Open", "High", "Low", "Close"]].to_numpy()).all():
        raise RuntimeError("download contains non-finite OHLC values")
    if (result[["Open", "High", "Low", "Close"]] <= 0).any().any():
        raise RuntimeError("download contains non-positive OHLC values")

    result = canonicalize_float_noise(result)
    return result.reset_index(drop=True)


def main() -> int:
    args = parse_args()
    frame = download(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output, index=False, date_format="%Y-%m-%d")
    print(f"ticker: {args.ticker.strip().upper()}")
    print(f"rows: {len(frame)}")
    print(f"first date: {frame['Date'].iloc[0].date()}")
    print(f"last date: {frame['Date'].iloc[-1].date()}")
    print(f"adjusted OHLC: {not args.raw_prices}")
    print(f"wrote: {args.output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
