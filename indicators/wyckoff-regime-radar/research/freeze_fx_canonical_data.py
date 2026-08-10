#!/usr/bin/env python3
"""Freeze the canonical FX daily OHLC inputs for Issue #55.

The frozen research subject is evaluated on one reproducible market-data snapshot.
Yahoo Finance is the canonical feed for the primary experiment because it is
available non-interactively in CI. Cross-feed robustness (for example OANDA vs
Yahoo) is a separate audit and must not silently redefine the primary input.

This script has two modes:

* ``freeze``: download the fixed historical window once, normalize to OHLC,
  write deterministic CSV files, and write a manifest with SHA-256 checksums and
  preregistered 60/20/20 chronological split boundaries.
* ``verify``: never contact the provider; verify that the committed files still
  match their recorded checksums and split metadata.

The final-OOS boundary may be recorded, but this script deliberately computes no
regime outcome or utility statistics.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import pandas as pd
import yfinance as yf


SOURCE_NAME = "Yahoo Finance via yfinance"
SOURCE_START = "2000-01-01"
SNAPSHOT_LAST_COMPLETE_BAR = "2026-08-07"
DOWNLOAD_END_EXCLUSIVE = "2026-08-08"
FREEZE_DECISION_DATE = "2026-08-10"

PAIR_TICKERS: Mapping[str, str] = {
    "EURUSD": "EURUSD=X",
    "USDJPY": "JPY=X",
    "GBPUSD": "GBPUSD=X",
    "AUDUSD": "AUDUSD=X",
}


@dataclass(frozen=True)
class SplitBoundary:
    name: str
    start_index: int
    end_index: int
    start_date: str
    end_date: str
    rows: int


def normalize_download(frame: pd.DataFrame) -> pd.DataFrame:
    """Return deterministic date/open/high/low/close rows from yfinance output."""
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

    out = out.dropna(subset=["date", *required])
    out = out[out["date"] <= pd.Timestamp(SNAPSHOT_LAST_COMPLETE_BAR).date()]
    out = out.sort_values("date").drop_duplicates(subset=["date"], keep="last").reset_index(drop=True)
    validate_ohlc(out)
    return out


def _row_text(row: pd.Series) -> str:
    return (
        f"date={row['date']} open={float(row['open']):.10f} high={float(row['high']):.10f} "
        f"low={float(row['low']):.10f} close={float(row['close']):.10f}"
    )


def validate_ohlc(frame: pd.DataFrame) -> None:
    if frame.empty:
        raise ValueError("normalized OHLC is empty")
    if frame["date"].duplicated().any():
        raise ValueError("duplicate dates in normalized OHLC")
    if not frame["date"].is_monotonic_increasing:
        raise ValueError("dates are not strictly sorted")
    if (frame[["open", "high", "low", "close"]] <= 0).any().any():
        bad = (frame[["open", "high", "low", "close"]] <= 0).any(axis=1)
        raise ValueError(f"non-positive FX price: {_row_text(frame.loc[bad].iloc[0])}")

    high_bad = frame["high"] < frame[["open", "close", "low"]].max(axis=1)
    if high_bad.any():
        raise ValueError(
            f"OHLC integrity failure: high below another price: {_row_text(frame.loc[high_bad].iloc[0])}"
        )

    low_bad = frame["low"] > frame[["open", "close", "high"]].min(axis=1)
    if low_bad.any():
        raise ValueError(
            f"OHLC integrity failure: low above another price: {_row_text(frame.loc[low_bad].iloc[0])}"
        )


def serialize_ohlc(frame: pd.DataFrame) -> bytes:
    """Stable CSV representation used as the exact evaluation input."""
    text = frame.to_csv(index=False, float_format="%.10f", lineterminator="\n")
    return text.encode("utf-8")


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def chronological_splits(frame: pd.DataFrame) -> list[SplitBoundary]:
    """Preregistered row-wise 60/20/20 split; final OOS outcomes remain unopened."""
    n = len(frame)
    if n < 10:
        raise ValueError("too few rows for chronological split")
    dev_stop = int(n * 0.60)
    exploratory_stop = int(n * 0.80)
    bounds = [
        ("development", 0, dev_stop - 1),
        ("exploratory_oos", dev_stop, exploratory_stop - 1),
        ("final_oos", exploratory_stop, n - 1),
    ]
    result: list[SplitBoundary] = []
    for name, start, end in bounds:
        if start > end:
            raise ValueError(f"empty split {name}")
        result.append(
            SplitBoundary(
                name=name,
                start_index=start,
                end_index=end,
                start_date=str(frame.iloc[start]["date"]),
                end_date=str(frame.iloc[end]["date"]),
                rows=end - start + 1,
            )
        )
    return result


def download_pair(ticker: str) -> pd.DataFrame:
    frame = yf.download(
        ticker,
        start=SOURCE_START,
        end=DOWNLOAD_END_EXCLUSIVE,
        interval="1d",
        auto_adjust=False,
        actions=False,
        progress=False,
        threads=False,
    )
    return normalize_download(frame)


def freeze(output_dir: Path, manifest_path: Path) -> dict:
    if manifest_path.exists():
        raise FileExistsError(
            f"manifest already exists: {manifest_path}; refusing to silently redefine frozen inputs"
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    pairs: dict[str, dict] = {}
    for pair, ticker in PAIR_TICKERS.items():
        try:
            frame = download_pair(ticker)
        except ValueError as exc:
            raise ValueError(f"{pair} ({ticker}) failed canonical-data validation: {exc}") from exc
        filename = f"issue-55-{pair.lower()}-yahoo-1d-through-2026-08-07.csv"
        path = output_dir / filename
        content = serialize_ohlc(frame)
        path.write_bytes(content)
        splits = chronological_splits(frame)
        pairs[pair] = {
            "ticker": ticker,
            "file": str(path.relative_to(manifest_path.parent)),
            "sha256": sha256_bytes(content),
            "rows": len(frame),
            "start_date": str(frame.iloc[0]["date"]),
            "end_date": str(frame.iloc[-1]["date"]),
            "splits": {split.name: split.__dict__ for split in splits},
        }

    manifest = {
        "schema_version": 1,
        "issue": 55,
        "freeze_decision_date": FREEZE_DECISION_DATE,
        "canonical_feed": SOURCE_NAME,
        "download_start": SOURCE_START,
        "download_end_exclusive": DOWNLOAD_END_EXCLUSIVE,
        "snapshot_last_complete_bar": SNAPSHOT_LAST_COMPLETE_BAR,
        "normalization": {
            "columns": ["date", "open", "high", "low", "close"],
            "auto_adjust": False,
            "drop_na": True,
            "sort_ascending": True,
            "deduplicate_date_keep": "last",
            "csv_float_format": "%.10f",
        },
        "split_rule": "per-pair chronological row split: 60% development / 20% exploratory OOS / 20% final OOS using floor(0.60*n) and floor(0.80*n) boundaries",
        "final_oos_status": "SEALED_DO_NOT_EVALUATE",
        "pairs": pairs,
        "research_boundary": (
            "These CSVs are the exact canonical inputs for the primary Issue #55 experiment. "
            "Do not replace them with a refreshed provider download. Cross-feed and micro-perturbation "
            "tests are separate robustness audits. This freeze records final-OOS dates only; it does not "
            "evaluate final-OOS outcomes."
        ),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def _resolve_data_path(manifest_path: Path, relative: str) -> Path:
    return (manifest_path.parent / relative).resolve()


def verify(manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("final_oos_status") != "SEALED_DO_NOT_EVALUATE":
        raise ValueError("final OOS seal is missing")

    for pair, meta in manifest["pairs"].items():
        path = _resolve_data_path(manifest_path, meta["file"])
        content = path.read_bytes()
        actual_sha = sha256_bytes(content)
        if actual_sha != meta["sha256"]:
            raise ValueError(f"checksum mismatch for {pair}: {actual_sha} != {meta['sha256']}")
        frame = pd.read_csv(path)
        frame["date"] = pd.to_datetime(frame["date"], errors="raise").dt.date
        validate_ohlc(frame)
        if len(frame) != int(meta["rows"]):
            raise ValueError(f"row-count mismatch for {pair}")
        if str(frame.iloc[0]["date"]) != meta["start_date"] or str(frame.iloc[-1]["date"]) != meta["end_date"]:
            raise ValueError(f"date-range mismatch for {pair}")
        expected_splits = {split.name: split.__dict__ for split in chronological_splits(frame)}
        if expected_splits != meta["splits"]:
            raise ValueError(f"split metadata mismatch for {pair}")
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    here = Path(__file__).resolve().parent
    parser.add_argument("mode", choices=["freeze", "verify"])
    parser.add_argument("--output-dir", type=Path, default=here / "data" / "frozen")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=here / "data" / "issue-55-fx-canonical-manifest.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.mode == "freeze":
        manifest = freeze(args.output_dir, args.manifest)
    else:
        manifest = verify(args.manifest)
    summary = {
        "mode": args.mode,
        "canonical_feed": manifest["canonical_feed"],
        "snapshot_last_complete_bar": manifest["snapshot_last_complete_bar"],
        "final_oos_status": manifest["final_oos_status"],
        "pairs": {
            pair: {
                "rows": meta["rows"],
                "start_date": meta["start_date"],
                "end_date": meta["end_date"],
                "sha256": meta["sha256"],
                "final_oos_start": meta["splits"]["final_oos"]["start_date"],
            }
            for pair, meta in manifest["pairs"].items()
        },
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
