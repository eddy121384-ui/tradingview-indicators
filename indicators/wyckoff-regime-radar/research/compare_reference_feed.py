#!/usr/bin/env python3
"""Provisional cross-feed parity check for Issue #55.

This is not the final parity gate. It downloads Yahoo EURUSD daily OHLC via
``yfinance``, runs the frozen Python mirror, and compares the resulting
checkpoint outputs to the manually captured TradingView/OANDA reference
fixture. Differences combine feed differences and implementation differences,
so this report is diagnostic only. Exact/same-feed parity remains the preferred
final gate when available.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

try:
    from .price_only_core import compute_price_only
except ImportError:  # direct script execution
    from price_only_core import compute_price_only  # type: ignore


DEFAULT_TICKER = "EURUSD=X"
PARITY_FIELDS = [
    "prob_acc",
    "prob_markup",
    "prob_reacc",
    "prob_dist",
    "prob_markdown",
    "prob_redist",
    "top_gap",
    "evidence_strength",
]


def download_yahoo(ticker: str) -> tuple[bytes, pd.DataFrame]:
    frame = yf.download(
        ticker,
        start="2000-01-01",
        interval="1d",
        auto_adjust=False,
        actions=False,
        progress=False,
        threads=False,
    )
    if frame.empty:
        raise ValueError(f"Yahoo returned no rows for {ticker}")

    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = [str(column[0]) for column in frame.columns]
    frame = frame.reset_index()
    raw = frame.to_csv(index=False).encode("utf-8")
    return raw, frame


def normalize_ohlc(frame: pd.DataFrame) -> pd.DataFrame:
    lower = {str(column).lower(): column for column in frame.columns}
    date_column = next((lower[name] for name in ("date", "datetime") if name in lower), None)
    if date_column is None:
        raise ValueError(f"downloaded feed missing date column; got {list(frame.columns)}")
    required_price = ["open", "high", "low", "close"]
    missing = [column for column in required_price if column not in lower]
    if missing:
        raise ValueError(f"downloaded feed missing columns: {missing}; got {list(frame.columns)}")

    rename = {date_column: "date", **{lower[name]: name for name in required_price}}
    out = frame.rename(columns=rename)[["date", *required_price]].copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.date
    out = out.dropna(subset=["date", *required_price]).sort_values("date").reset_index(drop=True)
    return out


def compare(reference_path: Path, ticker: str) -> dict:
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    raw, downloaded = download_yahoo(ticker)
    ohlc = normalize_ohlc(downloaded)
    result = compute_price_only(ohlc)

    rows = []
    for ref in reference["rows"]:
        if ref.get("status"):
            continue
        target = pd.Timestamp(ref["target_date"]).date()
        candidates = result.index[result["date"] >= target].tolist()
        if not candidates:
            rows.append({"target_date": ref["target_date"], "status": "no_public_feed_bar"})
            continue
        idx = candidates[0]
        actual = result.loc[idx]
        row = {
            "target_date": ref["target_date"],
            "public_feed_date": str(actual["date"]),
            "reference_close": ref["close"],
            "public_feed_close": float(actual["close"]),
            "close_abs_diff": abs(float(actual["close"]) - float(ref["close"])),
            "reference_candidate": int(ref["candidate_display_id"]),
            "public_feed_candidate": int(actual["candidate_display_id"]),
            "reference_formal": int(ref["formal_id"]),
            "public_feed_formal": int(actual["formal_id"]),
        }
        field_diffs = {}
        for field in PARITY_FIELDS:
            py_value = float(actual[field]) if np.isfinite(actual[field]) else None
            ref_value = float(ref[field])
            field_diffs[field] = {
                "reference": ref_value,
                "python_public_feed": py_value,
                "abs_diff": None if py_value is None else abs(py_value - ref_value),
            }
        row["fields"] = field_diffs
        rows.append(row)

    comparable = [row for row in rows if "fields" in row]
    candidate_matches = sum(row["reference_candidate"] == row["public_feed_candidate"] for row in comparable)
    formal_matches = sum(row["reference_formal"] == row["public_feed_formal"] for row in comparable)
    numeric_diffs = [
        values["abs_diff"]
        for row in comparable
        for values in row["fields"].values()
        if values["abs_diff"] is not None
    ]
    return {
        "schema_version": 1,
        "status": "diagnostic_cross_feed_only",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "public_feed": "Yahoo Finance via yfinance",
        "public_feed_ticker": ticker,
        "public_feed_sha256": hashlib.sha256(raw).hexdigest(),
        "public_feed_rows": int(len(ohlc)),
        "public_feed_start": str(ohlc.iloc[0]["date"]),
        "public_feed_end": str(ohlc.iloc[-1]["date"]),
        "reference_fixture": str(reference_path),
        "comparable_checkpoints": len(comparable),
        "candidate_match_count": candidate_matches,
        "formal_match_count": formal_matches,
        "mean_numeric_abs_diff_points": float(np.mean(numeric_diffs)) if numeric_diffs else None,
        "max_numeric_abs_diff_points": float(np.max(numeric_diffs)) if numeric_diffs else None,
        "rows": rows,
        "boundary": "Cross-feed differences combine market-data and implementation differences. Do not treat this as final Pine/Python parity or economic validation.",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    here = Path(__file__).resolve().parent
    parser.add_argument(
        "--reference",
        type=Path,
        default=here / "fixtures" / "issue-55-oanda-eurusd-tv-checkpoints-v1.json",
    )
    parser.add_argument("--ticker", default=DEFAULT_TICKER)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = compare(args.reference, args.ticker)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "comparable_checkpoints": report["comparable_checkpoints"],
        "candidate_match_count": report["candidate_match_count"],
        "formal_match_count": report["formal_match_count"],
        "mean_numeric_abs_diff_points": report["mean_numeric_abs_diff_points"],
        "max_numeric_abs_diff_points": report["max_numeric_abs_diff_points"],
    }, indent=2))


if __name__ == "__main__":
    main()
