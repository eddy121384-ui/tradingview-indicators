#!/usr/bin/env python3
"""Acquire the preregistered Issue #50 U.S. rates dataset."""

from __future__ import annotations

import argparse
import json
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

FRED_SERIES = ("DGS3MO", "DGS2", "DGS5", "DGS10", "DGS30")
ETF_TICKERS = ("SHY", "IEF", "TLT")
FRED_DATE_COLUMNS = ("DATE", "observation_date")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download Issue #50 rates inputs")
    parser.add_argument("--start", default="2007-01-01")
    parser.add_argument("--end", default="2026-07-31")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    return parser.parse_args()


def fred_url(series: str, start: str, end: str) -> str:
    return (
        "https://fred.stlouisfed.org/graph/fredgraph.csv"
        f"?id={series}&cosd={start}&coed={end}"
    )


def normalize_fred_frame(frame: pd.DataFrame, series: str) -> pd.DataFrame:
    date_column = next(
        (column for column in FRED_DATE_COLUMNS if column in frame.columns), None
    )
    if date_column is None or series not in frame.columns:
        raise ValueError(f"unexpected FRED columns for {series}: {frame.columns.tolist()}")

    normalized = frame[[date_column, series]].rename(columns={date_column: "DATE"}).copy()
    normalized["DATE"] = pd.to_datetime(normalized["DATE"], errors="raise")
    if normalized["DATE"].duplicated().any():
        duplicates = normalized.loc[normalized["DATE"].duplicated(keep=False), "DATE"]
        sample = sorted({value.strftime("%Y-%m-%d") for value in duplicates})[:5]
        raise ValueError(f"duplicate FRED dates for {series}: {sample}")
    normalized[series] = pd.to_numeric(normalized[series], errors="coerce")
    normalized = normalized.dropna(subset=[series])
    if normalized.empty:
        raise ValueError(f"FRED series {series} returned no usable observations")
    return normalized.set_index("DATE").sort_index()


def download_fred(series: str, start: str, end: str) -> pd.DataFrame:
    url = fred_url(series, start, end)
    return normalize_fred_frame(pd.read_csv(url), series)


def extract_adjusted_close(raw: pd.DataFrame) -> pd.DataFrame:
    if raw.empty:
        raise ValueError("yfinance returned no data")
    if isinstance(raw.columns, pd.MultiIndex):
        if "Close" in raw.columns.get_level_values(0):
            close = raw["Close"].copy()
        elif "Close" in raw.columns.get_level_values(1):
            close = raw.xs("Close", axis=1, level=1).copy()
        else:
            raise ValueError("yfinance result has no Close field")
    else:
        if "Close" not in raw.columns:
            raise ValueError("yfinance result has no Close column")
        close = raw[["Close"]].rename(columns={"Close": ETF_TICKERS[0]})
    close.columns = [str(column).upper() for column in close.columns]
    missing = [ticker for ticker in ETF_TICKERS if ticker not in close.columns]
    if missing:
        raise ValueError(f"missing ETF adjusted closes: {missing}")
    return close[list(ETF_TICKERS)]


def normalize_etf_close(close: pd.DataFrame) -> pd.DataFrame:
    normalized = close.copy()
    index = pd.to_datetime(normalized.index, errors="raise")
    if getattr(index, "tz", None) is not None:
        index = index.tz_localize(None)
    normalized.index = index.normalize()
    if normalized.index.duplicated().any():
        duplicates = normalized.index[normalized.index.duplicated(keep=False)]
        sample = sorted({value.strftime("%Y-%m-%d") for value in duplicates})[:5]
        raise ValueError(f"duplicate ETF dates: {sample}")
    normalized = normalized.apply(pd.to_numeric, errors="coerce")
    normalized = normalized.dropna().sort_index()
    if normalized.empty:
        raise ValueError("ETF adjusted-close download produced no common rows")
    if (normalized <= 0.0).any().any() or not np.isfinite(normalized.to_numpy()).all():
        raise ValueError("ETF adjusted closes must be finite and positive")
    return normalized


def download_etfs(start: str, end: str) -> pd.DataFrame:
    end_exclusive = (pd.Timestamp(end) + timedelta(days=1)).strftime("%Y-%m-%d")
    raw = yf.download(
        list(ETF_TICKERS),
        start=start,
        end=end_exclusive,
        auto_adjust=True,
        actions=False,
        progress=False,
        threads=False,
        group_by="column",
    )
    return normalize_etf_close(extract_adjusted_close(raw))


def build_dataset(start: str, end: str) -> tuple[pd.DataFrame, dict[str, object]]:
    yields = pd.concat(
        [download_fred(series, start, end) for series in FRED_SERIES], axis=1, join="inner"
    )
    etfs = download_etfs(start, end)
    combined = yields.join(etfs, how="inner").dropna().sort_index()
    combined = combined.loc[
        (combined.index >= pd.Timestamp(start)) & (combined.index <= pd.Timestamp(end))
    ]
    if len(combined) < 3000:
        raise ValueError(f"only {len(combined)} common rates rows; expected at least 3000")
    if not combined.index.is_monotonic_increasing or combined.index.has_duplicates:
        raise ValueError("combined rates dates must be unique and chronological")
    if not np.isfinite(combined.to_numpy(dtype=float)).all():
        raise ValueError("combined rates data contains non-finite values")
    if (combined[list(ETF_TICKERS)] <= 0.0).any().any():
        raise ValueError("combined ETF prices must be positive")

    result = combined.reset_index(names="Date")
    result["Date"] = result["Date"].dt.strftime("%Y-%m-%d")
    manifest = {
        "contract": "issue-50-rates-v1",
        "start": start,
        "end": end,
        "fred_series": {
            series: fred_url(series, start, end) for series in FRED_SERIES
        },
        "accepted_fred_date_columns": list(FRED_DATE_COLUMNS),
        "etf_tickers": list(ETF_TICKERS),
        "etf_source": "yfinance auto_adjust=True",
        "join": "inner common observed dates; no yield interpolation",
        "rows": int(len(result)),
        "first_date": str(result["Date"].iloc[0]),
        "last_date": str(result["Date"].iloc[-1]),
        "columns": result.columns.tolist(),
    }
    return result, manifest


def main() -> None:
    args = parse_args()
    result, manifest = build_dataset(args.start, args.end)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False, float_format="%.10f", lineterminator="\n")
    args.manifest.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
