#!/usr/bin/env python3
"""Issue #141 Phase A — source acquisition only.

This script intentionally does not load exact V6.6 signal history and does not
load any asset-return outcome. It only downloads candidate public signal
sources, records raw SHA256 hashes, and reports schema/date coverage.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 Issue-141-MPM-research/1.0"

FRENCH_BASE = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
FRENCH_FACTORS = FRENCH_BASE + "F-F_Research_Data_Factors_CSV.zip"
FRENCH_12IND = FRENCH_BASE + "12_Industry_Portfolios_CSV.zip"
WB_LANDING = "https://www.worldbank.org/en/research/commodity-markets"
FRED_SERIES = {
    "EXPINF10YR": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=EXPINF10YR",
    "MCOILWTICO": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MCOILWTICO",
    "MGASNYH": "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MGASNYH",
}


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def fetch(url: str) -> bytes:
    r = requests.get(url, headers={"User-Agent": UA}, timeout=90)
    r.raise_for_status()
    return r.content


def first_member_text(raw_zip: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(raw_zip)) as z:
        names = [n for n in z.namelist() if not n.endswith("/")]
        if len(names) != 1:
            raise RuntimeError(f"expected one French ZIP member, got {names}")
        return z.read(names[0]).decode("latin-1")


def parse_french_block(text: str, required_headers: set[str]) -> pd.DataFrame:
    lines = text.splitlines()
    header_i = None
    header = None
    for i, line in enumerate(lines):
        if "," not in line:
            continue
        row = next(csv.reader([line]))
        names = [x.strip() for x in row[1:]]
        if required_headers.issubset(set(names)):
            header_i = i
            header = ["date"] + names
            break
    if header_i is None or header is None:
        raise RuntimeError(f"French block header not found for {sorted(required_headers)}")

    rows: list[list[str]] = []
    for line in lines[header_i + 1 :]:
        row = next(csv.reader([line]))
        if not row:
            continue
        key = row[0].strip()
        if not re.fullmatch(r"\d{6}", key):
            if rows:
                break
            continue
        vals = [x.strip() for x in row]
        if len(vals) != len(header):
            raise RuntimeError(f"unexpected French row width {len(vals)} != {len(header)}")
        rows.append(vals)
    if not rows:
        raise RuntimeError("French monthly block empty")

    df = pd.DataFrame(rows, columns=header)
    df["date"] = pd.to_datetime(df["date"], format="%Y%m") + pd.offsets.MonthEnd(0)
    for c in df.columns[1:]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
        df.loc[df[c].le(-99), c] = pd.NA
    return df


def normalize_wb_columns(df: pd.DataFrame) -> list[str]:
    out = []
    for c in df.columns:
        if isinstance(c, tuple):
            s = " | ".join(str(x) for x in c if str(x) != "nan")
        else:
            s = str(c)
        out.append(s.strip())
    return out


def wb_sheet(raw: bytes, sheet: str) -> pd.DataFrame:
    # Current Pink Sheet examples use four non-table rows before the header.
    df = pd.read_excel(io.BytesIO(raw), sheet_name=sheet, skiprows=4)
    df.columns = normalize_wb_columns(df)
    return df


def coverage_from_frame(df: pd.DataFrame, date_col: str, value_cols: list[str]) -> dict:
    d = pd.to_datetime(df[date_col], errors="coerce")
    out = {}
    for c in value_cols:
        s = pd.to_numeric(df[c], errors="coerce")
        ok = d.notna() & s.notna()
        out[c] = {
            "n": int(ok.sum()),
            "first": d.loc[ok].min().date().isoformat() if ok.any() else None,
            "last": d.loc[ok].max().date().isoformat() if ok.any() else None,
            "missing": int((~s.notna()).sum()),
        }
    return out


def read_fred(raw: bytes, series: str) -> pd.DataFrame:
    df = pd.read_csv(io.BytesIO(raw))
    if "observation_date" not in df.columns:
        raise RuntimeError(f"{series}: missing observation_date")
    value_cols = [c for c in df.columns if c != "observation_date"]
    if len(value_cols) != 1:
        raise RuntimeError(f"{series}: expected one value column, got {value_cols}")
    df = df.rename(columns={value_cols[0]: series, "observation_date": "date"})
    df["date"] = pd.to_datetime(df["date"], errors="raise")
    df[series] = pd.to_numeric(df[series], errors="coerce")
    return df


def locate_world_bank_monthly_url() -> tuple[str, bytes]:
    landing = fetch(WB_LANDING)
    soup = BeautifulSoup(landing, "html.parser")
    candidates = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "CMO-Historical-Data-Monthly.xlsx" in href:
            candidates.append(urljoin(WB_LANDING, href))
    if not candidates:
        raise RuntimeError("World Bank monthly Pink Sheet link not found")
    # Deterministic: choose lexicographically smallest unique href if page has duplicates.
    return sorted(set(candidates))[0], landing


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    outdir = args.output_dir
    outdir.mkdir(parents=True, exist_ok=True)

    raw_factors = fetch(FRENCH_FACTORS)
    raw_ind12 = fetch(FRENCH_12IND)
    factors = parse_french_block(first_member_text(raw_factors), {"Mkt-RF", "SMB", "RF"})
    ind12 = parse_french_block(first_member_text(raw_ind12), {"NoDur", "Durbl", "Manuf", "Utils", "Shops"})

    wb_url, wb_landing = locate_world_bank_monthly_url()
    raw_wb = fetch(wb_url)
    wb_prices = wb_sheet(raw_wb, "Monthly Prices")
    wb_indices = wb_sheet(raw_wb, "Monthly Indices")

    fred_raw: dict[str, bytes] = {}
    fred_frames: dict[str, pd.DataFrame] = {}
    for series, url in FRED_SERIES.items():
        b = fetch(url)
        fred_raw[series] = b
        fred_frames[series] = read_fred(b, series)

    # World Bank schema only: do not choose the broad commodity index in Phase A.
    price_cols = wb_prices.columns.tolist()
    index_cols = wb_indices.columns.tolist()
    price_matches = {
        "copper_candidates": [c for c in price_cols if "COPPER" in c.upper()],
        "gold_candidates": [c for c in price_cols if "GOLD" in c.upper()],
    }
    index_matches = {
        "commodity_candidates": [
            c for c in index_cols
            if "COMMOD" in c.upper() or "ENERGY" in c.upper() or "METAL" in c.upper()
        ]
    }

    ff_cov = {
        "factors": coverage_from_frame(factors, "date", ["Mkt-RF", "SMB", "RF"]),
        "industry12": coverage_from_frame(
            ind12, "date", ["NoDur", "Durbl", "Manuf", "Utils", "Shops"]
        ),
    }
    fred_cov = {
        k: coverage_from_frame(v, "date", [k])[k]
        for k, v in fred_frames.items()
    }

    # Preserve small source-native extracts sufficient for schema/audit; no exact signal loaded.
    factors[["date", "Mkt-RF", "SMB", "RF"]].to_csv(
        outdir / "french-factors-monthly.csv", index=False
    )
    ind12.to_csv(outdir / "french-12-industry-monthly.csv", index=False)
    for k, df in fred_frames.items():
        df.to_csv(outdir / f"fred-{k}.csv", index=False)

    schema = {
        "issue": 141,
        "phase": "A-source-acquisition",
        "outcome_data_loaded": False,
        "exact_v66_signal_loaded": False,
        "sources": {
            "french_factors": {
                "url": FRENCH_FACTORS,
                "sha256": sha256(raw_factors),
                "coverage": ff_cov["factors"],
            },
            "french_12_industry": {
                "url": FRENCH_12IND,
                "sha256": sha256(raw_ind12),
                "columns": ind12.columns.tolist(),
                "coverage": ff_cov["industry12"],
            },
            "world_bank_landing": {
                "url": WB_LANDING,
                "sha256": sha256(wb_landing),
            },
            "world_bank_monthly": {
                "url": wb_url,
                "sha256": sha256(raw_wb),
                "sheet_names": pd.ExcelFile(io.BytesIO(raw_wb)).sheet_names,
                "monthly_prices_columns": price_cols,
                "monthly_indices_columns": index_cols,
                "price_matches": price_matches,
                "index_matches": index_matches,
            },
            "fred": {
                k: {
                    "url": FRED_SERIES[k],
                    "sha256": sha256(fred_raw[k]),
                    "coverage": fred_cov[k],
                }
                for k in FRED_SERIES
            },
        },
    }
    (outdir / "issue-141-source-schema.json").write_text(
        json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(json.dumps({
        "french": ff_cov,
        "fred": fred_cov,
        "world_bank_url": wb_url,
        "world_bank_price_matches": price_matches,
        "world_bank_index_candidates": index_matches["commodity_candidates"],
        "world_bank_sheets": schema["sources"]["world_bank_monthly"]["sheet_names"],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
