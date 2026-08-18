from __future__ import annotations

from dataclasses import asdict, dataclass
from io import StringIO
from pathlib import Path
from typing import Callable
from urllib.parse import quote
from urllib.request import urlopen

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SeriesSpec:
    canonical: str
    provider: str
    public_symbol: str
    pine_symbol: str
    group: str
    default_enabled: bool
    feed_note: str


SERIES_SPECS: tuple[SeriesSpec, ...] = (
    SeriesSpec("spy", "yahoo", "SPY", "AMEX:SPY", "GPI", True, "ETF raw close proxy"),
    SeriesSpec("iwm", "yahoo", "IWM", "AMEX:IWM", "GPI", True, "ETF raw close proxy"),
    SeriesSpec("rsp", "yahoo", "RSP", "AMEX:RSP", "GPI", True, "ETF raw close proxy"),
    SeriesSpec("xly", "yahoo", "XLY", "AMEX:XLY", "GPI", True, "ETF raw close proxy"),
    SeriesSpec("xlp", "yahoo", "XLP", "AMEX:XLP", "GPI", True, "ETF raw close proxy"),
    SeriesSpec("xli", "yahoo", "XLI", "AMEX:XLI", "GPI", True, "ETF raw close proxy"),
    SeriesSpec("xlu", "yahoo", "XLU", "AMEX:XLU", "GPI", True, "ETF raw close proxy"),
    SeriesSpec("copper", "yahoo", "HG=F", "COMEX:HG1!", "GPI", True, "Yahoo continuous futures differ from TradingView COMEX:HG1!"),
    SeriesSpec("gold", "yahoo", "GC=F", "COMEX:GC1!", "GPI", True, "Yahoo continuous futures differ from TradingView COMEX:GC1!"),
    SeriesSpec("breakeven_10y", "fred", "T10YIE", "FRED:T10YIE", "IPI", True, "FRED daily series"),
    SeriesSpec("breakeven_5y", "fred", "T5YIE", "FRED:T5YIE", "IPI", False, "optional V6.6 path"),
    SeriesSpec("oil", "yahoo", "CL=F", "NYMEX:CL1!", "IPI", True, "Yahoo continuous futures differ from TradingView NYMEX:CL1!"),
    SeriesSpec("gasoline", "yahoo", "RB=F", "NYMEX:RB1!", "IPI", True, "Yahoo continuous futures differ from TradingView NYMEX:RB1!"),
    SeriesSpec("commodity_basket", "yahoo", "DBC", "AMEX:DBC", "IPI", True, "ETF raw close proxy"),
    SeriesSpec("industrial_metals", "yahoo", "DBB", "AMEX:DBB", "IPI", False, "optional V6.6 path"),
    SeriesSpec("dxy", "yahoo", "DX-Y.NYB", "TVC:DXY", "FCPI", True, "ICE DXY proxy feed differs from TradingView TVC:DXY"),
    SeriesSpec("vix", "yahoo", "^VIX", "CBOE:VIX", "FCPI", True, "CBOE index proxy"),
    SeriesSpec("move", "yahoo", "^MOVE", "TVC:MOVE", "FCPI", True, "Yahoo MOVE history/feed may differ from TradingView TVC:MOVE"),
    SeriesSpec("hyg", "yahoo", "HYG", "AMEX:HYG", "FCPI", True, "ETF raw close proxy"),
    SeriesSpec("ief", "yahoo", "IEF", "NASDAQ:IEF", "FCPI", True, "ETF raw close proxy"),
    SeriesSpec("hy_oas", "fred", "BAMLH0A0HYM2", "FRED:BAMLH0A0HYM2", "FCPI", True, "FRED daily series"),
    SeriesSpec("real_yield", "fred", "DFII10", "FRED:DFII10", "FCPI", True, "FRED daily series"),
    SeriesSpec("kre", "yahoo", "KRE", "AMEX:KRE", "FCPI", False, "optional V6.6 path"),
    SeriesSpec("nfci", "fred", "NFCI", "FRED:NFCI", "FCPI", False, "optional official-FCI path"),
    SeriesSpec("stlfsi", "fred", "STLFSI4", "FRED:STLFSI4", "FCPI", False, "optional official-FCI path"),
    SeriesSpec("pmi", "fred", "NAPM", "FRED:NAPM", "GPI_MACRO", False, "optional macro-confirmation path"),
    SeriesSpec("cfnai", "fred", "CFNAI", "FRED:CFNAI", "GPI_MACRO", False, "optional macro-confirmation path"),
    SeriesSpec("permits", "fred", "PERMIT", "FRED:PERMIT", "GPI_MACRO", False, "optional macro-confirmation path"),
    SeriesSpec("claims", "fred", "ICSA", "FRED:ICSA", "GPI_MACRO", False, "optional macro-confirmation path; inverted in V6.6"),
    SeriesSpec("unemployment", "fred", "UNRATE", "FRED:UNRATE", "GPI_MACRO", False, "optional macro-confirmation path; inverted in V6.6"),
    SeriesSpec("cpi", "fred", "CPIAUCSL", "FRED:CPIAUCSL", "IPI_MACRO", False, "optional macro-confirmation path"),
    SeriesSpec("core_cpi", "fred", "CPILFESL", "FRED:CPILFESL", "IPI_MACRO", False, "optional macro-confirmation path"),
    SeriesSpec("pce", "fred", "PCEPI", "FRED:PCEPI", "IPI_MACRO", False, "optional macro-confirmation path"),
    SeriesSpec("core_pce", "fred", "PCEPILFE", "FRED:PCEPILFE", "IPI_MACRO", False, "optional macro-confirmation path"),
    SeriesSpec("ppi", "fred", "PPIACO", "FRED:PPIACO", "IPI_MACRO", False, "optional macro-confirmation path"),
    SeriesSpec("wage", "fred", "CES0500000003", "FRED:CES0500000003", "IPI_MACRO", False, "optional macro-confirmation path"),
)


def selected_specs(*, include_t5yie: bool = False, include_industrial_metals: bool = False,
                   include_kre: bool = False, include_official_fci: bool = False,
                   include_macro: bool = False) -> list[SeriesSpec]:
    selected: list[SeriesSpec] = []
    for spec in SERIES_SPECS:
        if spec.default_enabled:
            selected.append(spec)
            continue
        if spec.canonical == "breakeven_5y" and include_t5yie:
            selected.append(spec)
        elif spec.canonical == "industrial_metals" and include_industrial_metals:
            selected.append(spec)
        elif spec.canonical == "kre" and include_kre:
            selected.append(spec)
        elif spec.canonical in {"nfci", "stlfsi"} and include_official_fci:
            selected.append(spec)
        elif spec.group in {"GPI_MACRO", "IPI_MACRO"} and include_macro:
            selected.append(spec)
    return selected


def _normalize_index(index_like) -> pd.DatetimeIndex:
    index = pd.to_datetime(index_like, errors="raise")
    if getattr(index, "tz", None) is not None:
        index = index.tz_convert(None)
    return pd.DatetimeIndex(index).normalize()


def download_yahoo_close(symbol: str, start: str, end: str | None) -> pd.Series:
    # Keep yfinance lazy so pure unit tests can run without network dependencies.
    import yfinance as yf

    frame = yf.download(
        symbol,
        start=start,
        end=end,
        auto_adjust=False,
        actions=False,
        repair=True,
        keepna=True,
        progress=False,
        threads=False,
    )
    if frame.empty:
        return pd.Series(dtype=float, name=symbol)
    close = frame["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    values = pd.Series(pd.to_numeric(close, errors="coerce").to_numpy(float), index=_normalize_index(close.index), name=symbol)
    return values[~values.index.duplicated(keep="last")].sort_index()


def download_fred_series(series_id: str, start: str, end: str | None) -> pd.Series:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={quote(series_id)}"
    with urlopen(url, timeout=60) as response:  # noqa: S310 - fixed trusted FRED endpoint
        text = response.read().decode("utf-8")
    frame = pd.read_csv(StringIO(text))
    date_col = "observation_date" if "observation_date" in frame.columns else "DATE"
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

        # Preserve observations that occur off the anchor calendar (for example,
        # monthly FRED observations dated on weekends or market holidays).  First
        # forward-fill across the union of source and anchor dates, then project
        # back onto the anchor trading calendar.  This remains strictly causal:
        # an observation is only visible on anchor dates at or after its own date.
        union_index = calendar.union(clean.index).sort_values()
        aligned = clean.reindex(union_index).ffill().reindex(calendar)
        frame[canonical] = aligned
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
    series_map: dict[str, pd.Series] = {}
    for spec in specs:
        series = downloader(spec, start, end)
        if series.dropna().empty:
            raise ValueError(f"source {spec.canonical!r} ({spec.provider}:{spec.public_symbol}) has no usable observations")
        series_map[spec.canonical] = series

    frame = align_to_anchor(series_map, anchor=anchor)
    manifest = {
        "anchor_calendar": anchor,
        "rows": int(len(frame)),
        "first_date": frame.index.min().date().isoformat() if len(frame) else None,
        "last_date": frame.index.max().date().isoformat() if len(frame) else None,
        "parity_warning": (
            "Public providers are not TradingView. Continuous futures, DXY/MOVE feeds, ETF close conventions, "
            "FRED revisions, and release-date timing can differ. Use TradingView source exports for formula parity."
        ),
        "series": [
            _coverage_entry(spec, series_map[spec.canonical], frame[spec.canonical])
            for spec in specs
        ],
    }
    return frame, manifest


def write_bundle(frame: pd.DataFrame, manifest: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_dir / "v6.6-public-sources.csv", index=True)
    pd.Series(manifest).to_json(output_dir / "v6.6-public-manifest.json", indent=2)
