#!/usr/bin/env python3
"""Issue #143 Phase A — source-only acquisition for IPI attribution.

No exact V6.6 signal and no asset-return outcome is loaded here.

Outputs:
- normalized daily public exact-input panel on SPY trading calendar
- normalized monthly structural-source panel reused from Issue #141 sources
- manifest with coverage and SHA256 hashes
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import yfinance as yf

import issue_141_source_acquisition as i141

UA = "Mozilla/5.0 Issue-143-MPM-research/1.0"
START = "2006-01-01"
END = "2026-09-01"

EXPECTED_I141_SHA = {
    "world_bank_monthly": "9fdcfa8a2aed9a1bb545a10c1a5ce036c6a0acd4766f450424ca800b4b5a0225",
    "cleveland_inflation_expectations": "20701ccf394d280fe1db38fa9def5628f2385dd0aef148ff989e33ff15caba95",
}


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def fetch(url: str) -> bytes:
    print(f"FETCH {url}", flush=True)
    r = requests.get(url, headers={"User-Agent": UA}, timeout=(15, 60))
    r.raise_for_status()
    print(f"OK {len(r.content)} bytes", flush=True)
    return r.content


def yahoo_close(symbol: str) -> pd.Series:
    print(f"YAHOO {symbol}", flush=True)
    frame = yf.download(
        symbol,
        start=START,
        end=END,
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
    s = pd.to_numeric(frame["Close"], errors="coerce")
    idx = pd.to_datetime(s.index, utc=True).tz_convert(None).normalize()
    s.index = idx
    s = s[~s.index.duplicated(keep="last")].sort_index()
    s.name = symbol
    if s.dropna().empty:
        raise RuntimeError(f"Yahoo {symbol} is empty after normalization")
    return s.astype(float)


def read_fred_static_text(series: str) -> tuple[pd.Series, bytes]:
    url = f"https://fred.stlouisfed.org/data/{series}.txt"
    raw = fetch(url)
    text = raw.decode("utf-8", errors="replace")
    rows = []
    started = False
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) >= 2 and len(parts[0]) == 10 and parts[0][4] == "-" and parts[0][7] == "-":
            started = True
            rows.append((parts[0], parts[1]))
        elif started:
            # Ignore footer if one appears.
            continue
    if not rows:
        raise RuntimeError(f"FRED static text for {series} had no date/value rows")
    df = pd.DataFrame(rows, columns=["date", "value"])
    idx = pd.to_datetime(df["date"], errors="raise")
    vals = pd.to_numeric(df["value"].replace(".", np.nan), errors="coerce")
    s = pd.Series(vals.to_numpy(float), index=idx, name=series)
    s = s.loc[(s.index >= pd.Timestamp(START)) & (s.index < pd.Timestamp(END))]
    if s.dropna().empty:
        raise RuntimeError(f"FRED {series} empty in requested window")
    return s, raw


def align_to_spy(spy: pd.Series, series: dict[str, pd.Series]) -> pd.DataFrame:
    calendar = pd.DatetimeIndex(spy.dropna().index).sort_values().unique()
    frame = pd.DataFrame(index=calendar)
    frame["spy"] = spy.reindex(calendar)
    for name, s in series.items():
        clean = s.copy()
        clean.index = pd.to_datetime(clean.index).normalize()
        clean = clean[~clean.index.duplicated(keep="last")].sort_index()
        union = calendar.union(clean.index).sort_values()
        frame[name] = clean.reindex(union).ffill().reindex(calendar)
    frame.index.name = "date"
    return frame


def coverage(s: pd.Series) -> dict:
    x = pd.to_numeric(s, errors="coerce")
    ok = x.notna()
    return {
        "n": int(ok.sum()),
        "first": x.index[ok].min().date().isoformat() if ok.any() else None,
        "last": x.index[ok].max().date().isoformat() if ok.any() else None,
        "missing": int((~ok).sum()),
    }


def load_issue141_structural_sources() -> tuple[pd.DataFrame, dict]:
    wb_url, wb_landing = i141.locate_world_bank_monthly_url()
    raw_wb = i141.fetch(wb_url)
    cl_url, cl_landing = i141.locate_cleveland_xlsx()
    raw_cl = i141.fetch(cl_url)

    observed = {
        "world_bank_monthly": sha256_bytes(raw_wb),
        "cleveland_inflation_expectations": sha256_bytes(raw_cl),
    }
    drift = {
        k: {"expected": EXPECTED_I141_SHA[k], "observed": observed[k]}
        for k in EXPECTED_I141_SHA if observed[k] != EXPECTED_I141_SHA[k]
    }
    if drift:
        raise RuntimeError(f"Issue #141 frozen source drift: {drift}")

    wb = i141.selected_world_bank_panel(i141.wb_sheet(raw_wb, "Monthly Prices"))
    cl = i141.selected_cleveland_panel(raw_cl)
    wb["period"] = pd.to_datetime(wb["date"]).dt.to_period("M")
    cl["period"] = pd.to_datetime(cl["date"]).dt.to_period("M")
    monthly = wb.drop(columns=["date"]).merge(
        cl.drop(columns=["date"]),
        on="period",
        how="inner",
        validate="one_to_one",
    ).sort_values("period").reset_index(drop=True)
    monthly["date"] = monthly["period"].dt.to_timestamp("M")
    monthly = monthly.loc[
        monthly["period"].between(pd.Period("2006-01", "M"), pd.Period("2026-08", "M"))
    ].copy()

    meta = {
        "world_bank_url": wb_url,
        "world_bank_landing_sha256": sha256_bytes(wb_landing),
        "world_bank_monthly_sha256": observed["world_bank_monthly"],
        "cleveland_url": cl_url,
        "cleveland_landing_sha256": sha256_bytes(cl_landing),
        "cleveland_xlsx_sha256": observed["cleveland_inflation_expectations"],
    }
    return monthly, meta


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    outdir = args.output_dir
    outdir.mkdir(parents=True, exist_ok=True)

    spy = yahoo_close("SPY")
    dbc = yahoo_close("DBC")
    oil = yahoo_close("CL=F")
    gasoline = yahoo_close("RB=F")
    t10yie, t10_raw = read_fred_static_text("T10YIE")

    daily = align_to_spy(
        spy,
        {
            "breakeven_10y": t10yie,
            "commodity_basket": dbc,
            "oil": oil,
            "gasoline": gasoline,
        },
    )
    daily = daily.loc[
        (daily.index >= pd.Timestamp(START)) & (daily.index < pd.Timestamp(END))
    ].copy()

    monthly_structural, structural_meta = load_issue141_structural_sources()

    daily_path = outdir / "issue-143-public-exact-ipi-daily.csv"
    structural_path = outdir / "issue-143-structural-monthly.csv"
    daily.reset_index().to_csv(daily_path, index=False, date_format="%Y-%m-%d", float_format="%.12g")
    monthly_structural.drop(columns=["period"]).to_csv(
        structural_path, index=False, date_format="%Y-%m-%d", float_format="%.12g"
    )

    manifest = {
        "schema_version": 1,
        "issue": 143,
        "phase": "A-source-only",
        "exact_v66_signal_loaded": False,
        "outcome_data_loaded": False,
        "requested_start": START,
        "requested_end_exclusive": END,
        "daily_panel": {
            "sha256": sha256_file(daily_path),
            "rows": int(len(daily)),
            "first": daily.index.min().date().isoformat(),
            "last": daily.index.max().date().isoformat(),
            "coverage": {c: coverage(daily[c]) for c in daily.columns},
        },
        "structural_monthly": {
            "sha256": sha256_file(structural_path),
            "rows": int(len(monthly_structural)),
            "first": monthly_structural["date"].min().date().isoformat(),
            "last": monthly_structural["date"].max().date().isoformat(),
        },
        "fred_t10yie_static_text": {
            "url": "https://fred.stlouisfed.org/data/T10YIE.txt",
            "raw_sha256": sha256_bytes(t10_raw),
        },
        "issue141_sources": structural_meta,
        "yahoo_symbols": {
            "anchor": "SPY",
            "commodity_basket": "DBC",
            "oil": "CL=F",
            "gasoline": "RB=F",
        },
        "guardrail": "Signal-input acquisition only. No exact IPI target or asset-return outcome was loaded.",
    }
    (outdir / "issue-143-source-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
