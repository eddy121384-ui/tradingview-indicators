#!/usr/bin/env python3
"""Frozen outcome-price snapshot support for Issue #64.

Yahoo may revise adjusted history, so durable verdicts retain the exact
SPY/TLT/GLD panel they consumed. Repository storage uses a gzip-compressed CSV;
generated workflow artifacts may still use plain CSV. Both paths are hash
verified before use.
"""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from asset_allocation_phase_a import ASSETS

HERE = Path(__file__).resolve().parent
DEFAULT_SNAPSHOT = HERE / "data" / "issue-64-outcome-prices.csv.gz"
DEFAULT_MANIFEST = HERE / "data" / "issue-64-outcome-prices-manifest.json"
SNAPSHOT_COLUMNS = ["date", *ASSETS]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_gzip_payload(path: Path) -> str:
    """Hash the exact uncompressed CSV bytes stored inside a gzip snapshot."""
    digest = hashlib.sha256()
    with gzip.open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def display_path(path: Path) -> str:
    """Prefer a repo-relative provenance path, but allow temp/test files."""
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(HERE))
    except ValueError:
        return str(resolved)


def normalize_price_panel(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result.index = pd.DatetimeIndex(pd.to_datetime(result.index, errors="raise")).normalize().astype("datetime64[ns]")
    result = result.loc[:, list(ASSETS)].apply(pd.to_numeric, errors="raise").astype(float)
    result = result.sort_index()
    if result.empty:
        raise ValueError("outcome snapshot cannot be empty")
    if result.index.duplicated().any() or not result.index.is_monotonic_increasing:
        raise ValueError("outcome snapshot dates must be unique and increasing")
    if not np.isfinite(result.to_numpy(float)).all() or (result.to_numpy(float) <= 0.0).any():
        raise ValueError("outcome snapshot prices must be finite and positive")
    return result


def write_price_snapshot(frame: pd.DataFrame, csv_path: Path, manifest_path: Path, *, source: dict) -> dict:
    """Write deterministic plain-CSV workflow evidence and its manifest."""
    prices = normalize_price_panel(frame)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    serial = prices.copy()
    serial.index.name = "date"
    serial.to_csv(csv_path, date_format="%Y-%m-%d", float_format="%.17g")
    digest = sha256_file(csv_path)
    manifest = {
        "schema_version": 1,
        "issue": 64,
        "role": "durable frozen SPY/TLT/GLD adjusted-price input snapshot",
        "columns": SNAPSHOT_COLUMNS,
        "rows": int(len(prices)),
        "first_date": prices.index.min().date().isoformat(),
        "last_date": prices.index.max().date().isoformat(),
        "csv_sha256": digest,
        "source": source,
        "price_semantics": "Yahoo Finance yfinance auto_adjust=True adjusted Close; strict common finite SPY/TLT/GLD calendar",
        "interpretation_boundary": "This file freezes research inputs for reproducibility; it is not a production market-data source.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def load_frozen_prices(
    start: str,
    end: str | None,
    *,
    snapshot_path: Path = DEFAULT_SNAPSHOT,
    manifest_path: Path = DEFAULT_MANIFEST,
) -> tuple[pd.DataFrame, dict]:
    if not snapshot_path.exists() or not manifest_path.exists():
        raise FileNotFoundError("committed Issue #64 outcome snapshot is not available")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_csv = str(manifest.get("csv_sha256", ""))
    if not expected_csv:
        raise ValueError("outcome snapshot manifest is missing csv_sha256")

    is_gzip = snapshot_path.suffix == ".gz"
    if is_gzip:
        expected_archive = str(manifest.get("archive_sha256", ""))
        actual_archive = sha256_file(snapshot_path)
        if not expected_archive or actual_archive != expected_archive:
            raise ValueError(
                f"outcome snapshot archive SHA mismatch: expected {expected_archive}, got {actual_archive}"
            )
        actual_csv = sha256_gzip_payload(snapshot_path)
        if actual_csv != expected_csv:
            raise ValueError(
                f"outcome snapshot payload SHA mismatch: expected {expected_csv}, got {actual_csv}"
            )
        raw = pd.read_csv(snapshot_path, compression="gzip")
    else:
        actual_csv = sha256_file(snapshot_path)
        if actual_csv != expected_csv:
            raise ValueError(
                f"outcome snapshot SHA mismatch: expected {expected_csv}, got {actual_csv}"
            )
        actual_archive = None
        raw = pd.read_csv(snapshot_path)

    if list(raw.columns) != SNAPSHOT_COLUMNS:
        raise ValueError(f"unexpected outcome snapshot columns: {list(raw.columns)}")
    raw["date"] = pd.to_datetime(raw["date"], errors="raise")
    prices = normalize_price_panel(raw.set_index("date"))
    if int(manifest.get("rows", -1)) != len(prices):
        raise ValueError("outcome snapshot row count disagrees with manifest")
    if (
        manifest.get("first_date") != prices.index.min().date().isoformat()
        or manifest.get("last_date") != prices.index.max().date().isoformat()
    ):
        raise ValueError("outcome snapshot coverage disagrees with manifest")

    start_ts = pd.Timestamp(start)
    selected = prices.loc[prices.index >= start_ts]
    if end is not None:
        selected = selected.loc[selected.index < pd.Timestamp(end)]
    if selected.empty:
        raise ValueError("requested outcome snapshot slice is empty")

    runtime_manifest = {
        "provider": "frozen repository snapshot derived from Yahoo Finance",
        "source_mode": "committed_frozen_snapshot",
        "snapshot_path": display_path(snapshot_path),
        "snapshot_manifest_path": display_path(manifest_path),
        # Backward-compatible alias used by the original snapshot wrappers/tests.
        "snapshot_sha256": actual_csv,
        "snapshot_csv_sha256": actual_csv,
        "snapshot_archive_sha256": actual_archive,
        "snapshot_rows": int(len(prices)),
        "snapshot_first_date": prices.index.min().date().isoformat(),
        "snapshot_last_date": prices.index.max().date().isoformat(),
        "price_semantics": manifest["price_semantics"],
        "calendar_semantics": "strict intersection of finite SPY, TLT and GLD observation dates; no outcome forward-fill",
        "symbols": list(ASSETS),
        "rows": int(len(selected)),
        "first_date": selected.index.min().date().isoformat(),
        "last_date": selected.index.max().date().isoformat(),
    }
    return selected, runtime_manifest


def committed_snapshot_available() -> bool:
    return DEFAULT_SNAPSHOT.exists() and DEFAULT_MANIFEST.exists()
