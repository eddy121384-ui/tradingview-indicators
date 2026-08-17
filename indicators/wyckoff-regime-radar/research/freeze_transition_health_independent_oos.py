#!/usr/bin/env python3
"""Freeze the independent Issue #57 Transition Health FX sample before evaluation."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd
import yfinance as yf

TICKERS = {
    "NZDUSD": "NZDUSD=X",
    "EURGBP": "EURGBP=X",
    "GBPJPY": "GBPJPY=X",
    "AUDJPY": "AUDJPY=X",
    "CADJPY": "CADJPY=X",
}
DOWNLOAD_START = "2018-01-01"
DOWNLOAD_END_EXCLUSIVE = "2026-08-15"
SCORE_START = "2022-01-01"
SCORE_END = "2026-08-14"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_download(raw: pd.DataFrame) -> pd.DataFrame:
    if raw.empty:
        raise RuntimeError("download returned no rows")
    frame = raw.copy()
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = frame.columns.get_level_values(0)
    required = ["Open", "High", "Low", "Close"]
    missing = [c for c in required if c not in frame.columns]
    if missing:
        raise RuntimeError(f"missing OHLC columns: {missing}")
    out = frame.loc[:, required].copy()
    out.index = pd.to_datetime(out.index, errors="raise")
    if out.index.tz is not None:
        out.index = out.index.tz_localize(None)
    out = out.reset_index()
    date_col = out.columns[0]
    out = out.rename(columns={date_col: "date", "Open": "open", "High": "high", "Low": "low", "Close": "close"})
    out["date"] = pd.to_datetime(out["date"], errors="raise").dt.date
    for col in ("open", "high", "low", "close"):
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out.dropna(subset=["open", "high", "low", "close"]).drop_duplicates("date").sort_values("date")
    if out.empty:
        raise RuntimeError("no valid OHLC rows after normalization")
    return out.reset_index(drop=True)


def freeze_pair(pair: str, ticker: str, out_dir: Path) -> dict[str, object]:
    raw = yf.download(
        ticker,
        start=DOWNLOAD_START,
        end=DOWNLOAD_END_EXCLUSIVE,
        interval="1d",
        auto_adjust=False,
        repair=False,
        progress=False,
        threads=False,
    )
    frame = normalize_download(raw)
    first = str(frame["date"].iloc[0])
    last = str(frame["date"].iloc[-1])
    if first > DOWNLOAD_START:
        raise RuntimeError(f"{pair}: insufficient warmup start {first}")
    if last < SCORE_END:
        raise RuntimeError(f"{pair}: incomplete freeze end {last}, expected at least {SCORE_END}")
    frame = frame.loc[pd.to_datetime(frame["date"]) <= pd.Timestamp(SCORE_END)].copy()
    path = out_dir / f"issue-57-transition-health-oos-{pair.lower()}.csv"
    csv_bytes = frame.to_csv(index=False, lineterminator="\n", float_format="%.10f").encode("utf-8")
    path.write_bytes(csv_bytes)
    return {
        "ticker": ticker,
        "frozen_file": path.name,
        "sha256": sha256_bytes(csv_bytes),
        "rows": int(len(frame)),
        "start_date": str(frame["date"].iloc[0]),
        "end_date": str(frame["date"].iloc[-1]),
    }


def build_manifest(out_dir: Path) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    pairs = {pair: freeze_pair(pair, ticker, out_dir) for pair, ticker in TICKERS.items()}
    return {
        "schema_version": 1,
        "issue": 57,
        "status": "FROZEN_BEFORE_OUTCOME_EVALUATION",
        "source": "Yahoo Finance via yfinance",
        "download_start": DOWNLOAD_START,
        "download_end_exclusive": DOWNLOAD_END_EXCLUSIVE,
        "score_start": SCORE_START,
        "score_end": SCORE_END,
        "pairs": pairs,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    manifest = build_manifest(args.output_dir)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
