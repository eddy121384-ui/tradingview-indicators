#!/usr/bin/env python3
"""Public-data loader and symbol mapping for Macro Pressure Map V6.6 research.

This module separates provider/feed questions from the frozen V6.6 calculation
logic. The mapping below is a reproducible public-data approximation of the
TradingView symbols used by the Pine script; it is not a claim of vendor
identity.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import io
import json
from pathlib import Path
from typing import Callable, Literal
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

Provider = Literal["yahoo", "fred"]


@dataclass(frozen=True)
class SeriesSpec:
    canonical: str
    pine_symbol: str
    provider: Provider
    public_symbol: str
    group: str
    default_enabled: bool
    note: str = ""


SERIES_SPECS: tuple[SeriesSpec, ...] = (
    SeriesSpec("spy", "AMEX:SPY", "yahoo", "SPY", "GPI", True),
    SeriesSpec("iwm", "AMEX:IWM", "yahoo", "IWM", "GPI", True),
    SeriesSpec("rsp", "AMEX:RSP", "yahoo", "RSP", "GPI", True),
    SeriesSpec("xly", "AMEX:XLY", "yahoo", "XLY", "GPI", True),
    SeriesSpec("xlp", "AMEX:XLP", "yahoo", "XLP", "GPI", True),
    SeriesSpec("xli", "AMEX:XLI", "yahoo", "XLI", "GPI", True),
    SeriesSpec("xlu", "AMEX:XLU", "yahoo", "XLU", "GPI", True),
    SeriesSpec("copper", "COMEX:HG1!", "yahoo", "HG=F", "GPI", True,
               "Yahoo continuous-futures construction can differ from TradingView HG1!."),
    SeriesSpec("gold", "COMEX:GC1!", "yahoo", "GC=F", "GPI", True,
               "Yahoo continuous-futures construction can differ from TradingView GC1!."),
    SeriesSpec("breakeven_10y", "FRED:T10YIE", "fred", "T10YIE", "IPI", True),
    SeriesSpec("breakeven_5y", "FRED:T5YIE", "fred", "T5YIE", "IPI_OPTIONAL", False),
    SeriesSpec("oil", "NYMEX:CL1!", "yahoo", "CL=F", "IPI", True,
               "Yahoo continuous-futures construction can differ from TradingView CL1!."),
    SeriesSpec("gasoline", "NYMEX:RB1!", "yahoo", "RB=F", "IPI", True,
               "Yahoo continuous-futures construction can differ from TradingView RB1!."),
    SeriesSpec("commodity_basket", "AMEX:DBC", "yahoo", "DBC", "IPI", True),
    SeriesSpec("industrial_metals", "AMEX:DBB", "yahoo", "DBB", "IPI_OPTIONAL", False),
    SeriesSpec("dxy", "TVC:DXY", "yahoo", "DX-Y.NYB", "FCPI", True,
               "Yahoo dollar-index feed may differ from TradingView TVC:DXY."),
    SeriesSpec("vix", "CBOE:VIX", "yahoo", "^VIX", "FCPI", True),
    SeriesSpec("move", "TVC:MOVE", "yahoo", "^MOVE", "FCPI", True,
               "Yahoo MOVE history/feed may differ from TradingView TVC:MOVE."),
    SeriesSpec("hyg", "AMEX:HYG", "yahoo", "HYG", "FCPI", True),
    SeriesSpec("ief", "NASDAQ:IEF", "yahoo", "IEF", "FCPI", True),
    SeriesSpec("kre", "AMEX:KRE", "yahoo", "KRE", "FCPI_OPTIONAL", False),
    SeriesSpec("hy_oas", "FRED:BAMLH0A0HYM2", "fred", "BAMLH0A0HYM2", "FCPI", True),
    SeriesSpec("real_yield", "FRED:DFII10", "fred", "DFII10", "FCPI", True),
    SeriesSpec("nfci", "FRED:NFCI", "fred", "NFCI", "FCPI_OFFICIAL", False),
    SeriesSpec("stlfsi", "FRED:STLFSI4", "fred", "STLFSI4", "FCPI_OFFICIAL", False),
    SeriesSpec("pmi", "FRED:NAPM", "fred", "NAPM", "MACRO_GPI", False),
    SeriesSpec("cfnai", "FRED:CFNAI", "fred", "CFNAI", "MACRO_GPI", False),
    SeriesSpec("building_permits", "FRED:PERMIT", "fred", "PERMIT", "MACRO_GPI", False),
    SeriesSpec("initial_claims", "FRED:ICSA", "fred", "ICSA", "MACRO_GPI", False),
    SeriesSpec("unemployment", "FRED:UNRATE", "fred", "UNRATE", "MACRO_GPI", False),
    SeriesSpec("cpi", "FRED:CPIAUCSL", "fred", "CPIAUCSL", "MACRO_IPI", False),
    SeriesSpec("core_cpi", "FRED:CPILFESL", "fred", "CPILFESL", "MACRO_IPI", False),
    SeriesSpec("pce", "FRED:PCEPI", "fred", "PCEPI", "MACRO_IPI", False),
    SeriesSpec("core_pce", "FRED:PCEPILFE", "fred", "PCEPILFE", "MACRO_IPI", False),
    SeriesSpec("ppi", "FRED:PPIACO", "fred", "PPIACO", "MACRO_IPI", False),
    SeriesSpec("wage", "FRED:CES0500000003", "fred", "CES0500000003", "MACRO_IPI", False),
)


def selected_specs(*, include_t5yie: bool = False, include_industrial_metals: bool = False,
                   include_kre: bool = False, include_official_fci: bool = False,
                   include_macro: bool = False) -> list[SeriesSpec]:
    chosen: list[SeriesSpec] = []
    for spec in SERIES_SPECS:
        enabled = spec.default_enabled
        if spec.canonical == "breakeven_5y":
            enabled = include_t5yie
        elif spec.canonical == "industrial_metals":
            enabled = include_industrial_metals
        elif spec.canonical == "kre":
            enabled = include_kre
        elif spec.group == "FCPI_OFFICIAL":
            enabled = include_official_fci
        elif spec.group.startswith("MACRO_"):
            enabled = include_macro
        if enabled:
            chosen.append(spec)
    return chosen


def _normalize_index(index: pd.Index) -> pd.DatetimeIndex:
    result = pd.to_datetime(index, errors="raise", utc=True)
    return result.tz_convert(None).normalize()


def download_yahoo_close(symbol: str, start: str, end: str | None) -> pd.Series:
    try:
        import yfinance as yf
    except ImportError as exc:
        raise RuntimeError("yfinance is required for Yahoo public-data downloads") from exc
    frame = yf.download(
        symbol,
        start=start,
        end=end,
        interval="1d",
        auto_adjust=False,
        actions=False,
        repair=True,
        keepna=True,
        progress=False,
        threads=False,
        timeout=30,
        multi_level_index=False,
    )
    if frame is None or frame.empty or "Close" not in frame.columns:
        raise RuntimeError(f"Yahoo returned no usable Close series for {symbol}")
    values = pd.to_numeric(frame["Close"], errors="coerce")
    values.index = _normalize_index(values.index)
    values = values[~values.index.duplicated(keep="last")].sort_index()
    values.name = symbol
    return values.astype(float)


def _read_fred_csv(series_id: str) -> pd.DataFrame:
    query = urlencode({"id": series_id})
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?{query}"
    request = Request(url, headers={"User-Agent": "tradingview-indicators-research/1.0"})
    with urlopen(request, timeout=30) as response:  # nosec B310 - fixed trusted HTTPS host
        payload = response.read()
    return pd.read_csv(io.BytesIO(payload))


def download_fred_series(series_id: str, start: str, end: str | None) -> pd.Series:
    frame = _read_fred_csv(series_id)
    date_col = "observation_date" if "observation_date" in frame.columns else "DATE"
    if date_col not in frame.columns or series_id not in frame.columns:
        raise RuntimeError(f"FRED CSV for {series_id} has unexpected columns: {list(frame.columns)}")
    index = _normalize_index(frame[date_col])
    raw = frame[series_id].replace(".", np.nan)
    values = pd.Series(pd.to_numeric(raw, errors="coerce").to_numpy(float), index=index, name=series_id)
    values = values[~values.index.duplicated(keep="last")].sort_index()
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end) if end else None
    mask = values.index >= start_ts
    if end_ts is not None:
        mask &= values.index < end_ts
    return values.loc[mask]


def download_spec(spec: SeriesSpec, start: str, end: str | None) -> pd.Series:
    if spec.provider == "yahoo":
        return download_yahoo_close(spec.public_symbol, start, end)
    if spec.provider == "fred":
        return download_fred_series(spec.public_symbol, start, end)
    raise ValueError(f"unsupported provider {spec.provider!r}")


def align_to_anchor(series_map: dict[str, pd.Series], anchor: str = "spy") -> pd.DataFrame:
    if anchor not in series_map:
        raise ValueError(f"anchor series {anchor!r} was not downloaded")
    anchor_series = series_map[anchor].dropna()
    if anchor_series.empty:
        raise ValueError(f"anchor series {anchor!r} has no usable observations")
    calendar = pd.DatetimeIndex(anchor_series.index).sort_values().unique()
    frame = pd.DataFrame(index=calendar)
    for canonical, series in series_map.items():
        clean = series.copy()
        clean.index = _normalize_index(clean.index)
        clean = clean[~clean.index.duplicated(keep="last")].sort_index()
        frame[canonical] = clean.reindex(calendar).ffill()
    frame.index.name = "date"
    return frame


def _coverage_entry(spec: SeriesSpec, series: pd.Series, aligned: pd.Series) -> dict:
    finite_raw = series.dropna()
    finite_aligned = aligned.dropna()
    return {
        **asdict(spec),
        "raw_observations": int(finite_raw.size),
        "raw_first_date": finite_raw.index.min().date().isoformat() if not finite_raw.empty else None,
        "raw_last_date": finite_raw.index.max().date().isoformat() if not finite_raw.empty else None,
        "aligned_observations": int(finite_aligned.size),
        "aligned_coverage_pct": float(100.0 * finite_aligned.size / len(aligned)) if len(aligned) else 0.0,
    }


def build_public_sources(start: str = "2007-01-01", end: str | None = None, *,
                         anchor: str = "spy", include_t5yie: bool = False,
                         include_industrial_metals: bool = False, include_kre: bool = False,
                         include_official_fci: bool = False, include_macro: bool = False,
                         downloader: Callable[[SeriesSpec, str, str | None], pd.Series] = download_spec,
                         ) -> tuple[pd.DataFrame, dict]:
    specs = selected_specs(
        include_t5yie=include_t5yie,
        include_industrial_metals=include_industrial_metals,
        include_kre=include_kre,
        include_official_fci=include_official_fci,
        include_macro=include_macro,
    )
    if anchor not in {spec.canonical for spec in specs}:
        raise ValueError(f"anchor {anchor!r} is not enabled by the selected source set")

    downloaded: dict[str, pd.Series] = {}
    for spec in specs:
        series = downloader(spec, start, end)
        if series is None or series.dropna().empty:
            raise RuntimeError(f"no usable data for {spec.canonical} ({spec.provider}:{spec.public_symbol})")
        downloaded[spec.canonical] = series

    aligned = align_to_anchor(downloaded, anchor=anchor)
    manifest = {
        "schema_version": 1,
        "purpose": "Macro Pressure Map V6.6 public-data research approximation",
        "generated_at_utc": pd.Timestamp.utcnow().isoformat(),
        "requested_start": start,
        "requested_end_exclusive": end,
        "anchor_calendar": anchor,
        "rows": int(len(aligned)),
        "first_date": aligned.index.min().date().isoformat() if len(aligned) else None,
        "last_date": aligned.index.max().date().isoformat() if len(aligned) else None,
        "alignment_semantics": "Reindex to anchor trading dates; forward-fill only; never backfill before first observation.",
        "parity_warning": (
            "Public providers are not TradingView. Continuous futures construction, index feeds, ETF price adjustment, "
            "holiday calendars, and publication timing can differ. Stage-2 Pine parity must bound these differences."
        ),
        "series": [
            _coverage_entry(spec, downloaded[spec.canonical], aligned[spec.canonical]) for spec in specs
        ],
    }
    return aligned, manifest


def write_bundle(frame: pd.DataFrame, manifest: dict, csv_path: Path, manifest_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    frame.reset_index().to_csv(csv_path, index=False, date_format="%Y-%m-%d")
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
