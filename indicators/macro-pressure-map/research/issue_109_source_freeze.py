#!/usr/bin/env python3
"""Issue #109 Phase A0 source freeze.

This script freezes only the new raw inputs needed by the Action Layer:
- SHV adjusted Close (cash-like Treasury ETF proxy)
- GSG adjusted Close (broad commodity futures proxy)
- CPI-U All Items NSA monthly level (BLS CUUR0000SA0)

It deliberately does NOT load V6.6 states, compute forward returns, pairwise
spreads, model fits, rankings, portfolio metrics, or Issue #109 verdicts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

START_DATE = "2007-01-01"
END_EXCLUSIVE = "2026-09-24"
ASSETS = ("SHV", "GSG")
BLS_SERIES = "CUUR0000SA0"
BLS_ENDPOINT = "https://api.bls.gov/publicAPI/v2/timeseries/data/"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _normalize_index(index: pd.Index) -> pd.DatetimeIndex:
    result = pd.to_datetime(index, errors="raise", utc=True)
    return result.tz_convert(None).normalize()


def download_adjusted_close(symbol: str) -> pd.Series:
    try:
        import yfinance as yf
    except ImportError as exc:
        raise RuntimeError("yfinance is required for Issue #109 source freeze") from exc

    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            frame = yf.download(
                symbol,
                start=START_DATE,
                end=END_EXCLUSIVE,
                interval="1d",
                auto_adjust=True,
                actions=False,
                repair=True,
                keepna=True,
                progress=False,
                threads=False,
                timeout=30,
                multi_level_index=False,
            )
            if frame is None or frame.empty or "Close" not in frame.columns:
                raise RuntimeError(f"Yahoo returned no adjusted Close series for {symbol}")
            values = pd.to_numeric(frame["Close"], errors="coerce")
            values.index = _normalize_index(values.index)
            values = values.sort_index().dropna().astype(float)
            if values.empty:
                raise RuntimeError(f"Yahoo returned no finite adjusted Close values for {symbol}")
            if values.index.duplicated().any():
                raise RuntimeError(f"duplicate Yahoo dates for {symbol}")
            if not np.isfinite(values.to_numpy(float)).all() or (values.to_numpy(float) <= 0).any():
                raise RuntimeError(f"invalid adjusted Close values for {symbol}")
            values.name = symbol
            return values
        except Exception as exc:  # pragma: no cover - network retry
            last_error = exc
            if attempt < 3:
                time.sleep(5 * attempt)
    raise RuntimeError(f"failed to download {symbol} after retries") from last_error


def build_asset_panel() -> tuple[pd.DataFrame, dict]:
    series = {symbol: download_adjusted_close(symbol) for symbol in ASSETS}
    panel = pd.concat(series.values(), axis=1, join="inner").dropna(how="any")
    panel.columns = list(ASSETS)
    panel = panel.sort_index()
    if panel.empty:
        raise RuntimeError("SHV/GSG have no common adjusted-price history")
    manifest = {
        "provider": "Yahoo Finance via yfinance",
        "price_semantics": "auto_adjust=True adjusted Close; dividend/split-adjusted investable price proxy",
        "calendar_semantics": "strict SHV/GSG common finite observation dates; no outcome forward-fill",
        "start_request": START_DATE,
        "end_exclusive_request": END_EXCLUSIVE,
        "symbols": list(ASSETS),
        "rows": int(len(panel)),
        "first_date": panel.index.min().date().isoformat(),
        "last_date": panel.index.max().date().isoformat(),
        "individual_coverage": {
            symbol: {
                "rows": int(len(values)),
                "first_date": values.index.min().date().isoformat(),
                "last_date": values.index.max().date().isoformat(),
            }
            for symbol, values in series.items()
        },
    }
    return panel, manifest


def _bls_request(start_year: int, end_year: int) -> tuple[dict, bytes]:
    payload = {
        "seriesid": [BLS_SERIES],
        "startyear": str(start_year),
        "endyear": str(end_year),
    }
    response = requests.post(BLS_ENDPOINT, json=payload, timeout=45)
    response.raise_for_status()
    raw = response.content
    data = response.json()
    if data.get("status") != "REQUEST_SUCCEEDED":
        raise RuntimeError(f"BLS request failed: {data.get('message')}")
    return data, raw


def build_cpi_snapshot() -> tuple[pd.DataFrame, dict]:
    chunks = [(2005, 2014), (2015, 2024), (2025, 2026)]
    observations: list[dict] = []
    raw_hashes: list[dict] = []
    skipped_non_numeric: list[dict] = []

    for start_year, end_year in chunks:
        data, raw = _bls_request(start_year, end_year)
        raw_hashes.append({
            "start_year": start_year,
            "end_year": end_year,
            "sha256": sha256_bytes(raw),
            "bytes": len(raw),
        })
        series = data["Results"]["series"]
        if len(series) != 1 or series[0].get("seriesID") != BLS_SERIES:
            raise RuntimeError("unexpected BLS series payload")
        for item in series[0]["data"]:
            period = str(item["period"])
            if not period.startswith("M") or period == "M13":
                continue
            month = int(period[1:])
            if not 1 <= month <= 12:
                continue
            raw_value = str(item["value"]).strip().replace(",", "")
            try:
                value = float(raw_value)
            except ValueError:
                skipped_non_numeric.append({
                    "year": int(item["year"]),
                    "period": period,
                    "raw_value": raw_value,
                })
                continue
            observations.append({
                "date": f"{int(item['year']):04d}-{month:02d}-01",
                "CPI_U_NSA": value,
            })

    frame = pd.DataFrame(observations)
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    frame = frame.drop_duplicates(subset=["date"], keep="last").sort_values("date")
    if frame.empty or frame["date"].duplicated().any():
        raise RuntimeError("invalid CPI snapshot")
    if not np.isfinite(frame["CPI_U_NSA"].to_numpy(float)).all():
        raise RuntimeError("non-finite CPI observations")

    manifest = {
        "provider": "U.S. Bureau of Labor Statistics Public Data API v2",
        "endpoint": BLS_ENDPOINT,
        "series_id": BLS_SERIES,
        "concept": "CPI-U U.S. city average, All items, not seasonally adjusted",
        "chunks": raw_hashes,
        "skipped_non_numeric_observations": skipped_non_numeric,
        "rows": int(len(frame)),
        "first_month": frame["date"].min().strftime("%Y-%m"),
        "last_month": frame["date"].max().strftime("%Y-%m"),
        "transformation_reserved_for_later_diagnostic": "100 * (CPI_t / CPI_t-12 - 1)",
        "availability_lag_months_reserved_for_later_diagnostic": 2,
        "no_issue109_payoff_computed": True,
    }
    return frame, manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    prices, price_meta = build_asset_panel()
    price_csv = out / "issue-109-shv-gsg-adjusted-prices.csv"
    serial_prices = prices.copy()
    serial_prices.index.name = "date"
    serial_prices.to_csv(price_csv, date_format="%Y-%m-%d", float_format="%.17g")

    cpi, cpi_meta = build_cpi_snapshot()
    cpi_csv = out / "issue-109-cpi-u-nsa-monthly.csv"
    cpi.to_csv(cpi_csv, index=False, date_format="%Y-%m-%d", float_format="%.10g")

    manifest = {
        "schema_version": 1,
        "issue": 109,
        "phase": "A0-source-freeze",
        "created_before_issue109_payoff_results": True,
        "payoff_results_computed": False,
        "pairwise_spreads_computed": False,
        "portfolio_metrics_computed": False,
        "v66_states_loaded": False,
        "prices": {
            **price_meta,
            "file": price_csv.name,
            "csv_sha256": sha256_file(price_csv),
        },
        "cpi": {
            **cpi_meta,
            "file": cpi_csv.name,
            "csv_sha256": sha256_file(cpi_csv),
        },
    }
    manifest_path = out / "issue-109-source-freeze-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({
        "prices": {
            "rows": manifest["prices"]["rows"],
            "coverage": [manifest["prices"]["first_date"], manifest["prices"]["last_date"]],
            "sha256": manifest["prices"]["csv_sha256"],
        },
        "cpi": {
            "rows": manifest["cpi"]["rows"],
            "coverage": [manifest["cpi"]["first_month"], manifest["cpi"]["last_month"]],
            "sha256": manifest["cpi"]["csv_sha256"],
        },
        "payoff_results_computed": False,
    }, indent=2))


if __name__ == "__main__":
    main()
