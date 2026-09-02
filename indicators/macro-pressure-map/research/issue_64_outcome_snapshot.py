#!/usr/bin/env python3
"""Frozen outcome-price snapshot support for Issue #64.

Yahoo may revise adjusted history, so durable verdicts retain the exact
SPY/TLT/GLD panel they consumed. The committed snapshot is stored as UTF-8
Base64 shards containing one deterministic gzip-compressed CSV. This avoids
binary corruption through text-only repository write paths while preserving
byte-for-byte reproducibility of the research input.
"""
from __future__ import annotations

import base64
import gzip
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import pandas as pd

from asset_allocation_phase_a import ASSETS

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
DEFAULT_MANIFEST = DATA_DIR / "issue-64-outcome-prices-manifest.json"
DEFAULT_SHARDS = tuple(DATA_DIR / f"issue-64-outcome-prices-{index:02d}.b64" for index in range(1, 11))
SNAPSHOT_COLUMNS = ["date", *ASSETS]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
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


def _load_sharded_archive(manifest: dict, shard_paths: tuple[Path, ...]) -> tuple[bytes, bytes, dict]:
    declared = manifest.get("shards")
    if not isinstance(declared, list) or len(declared) != len(shard_paths):
        raise ValueError("outcome snapshot manifest shard list is missing or has the wrong length")

    encoded_parts: list[str] = []
    shard_runtime: list[dict] = []
    for path, item in zip(shard_paths, declared, strict=True):
        if not path.exists():
            raise FileNotFoundError(f"committed Issue #64 outcome snapshot shard is missing: {path}")
        text = path.read_text(encoding="ascii").strip()
        expected_path = str(item.get("path", ""))
        expected_sha = str(item.get("sha256", ""))
        expected_chars = int(item.get("chars", -1))
        actual_sha = sha256_bytes(text.encode("ascii"))
        if expected_path and expected_path != display_path(path):
            raise ValueError(f"outcome snapshot shard path mismatch: expected {expected_path}, got {display_path(path)}")
        if expected_chars != len(text):
            raise ValueError(f"outcome snapshot shard length mismatch for {path.name}")
        if not expected_sha or actual_sha != expected_sha:
            raise ValueError(f"outcome snapshot shard SHA mismatch for {path.name}: expected {expected_sha}, got {actual_sha}")
        encoded_parts.append(text)
        shard_runtime.append({"path": display_path(path), "chars": len(text), "sha256": actual_sha})

    encoded = "".join(encoded_parts)
    expected_chars = int(manifest.get("base64_chars", -1))
    if expected_chars != len(encoded):
        raise ValueError("outcome snapshot combined Base64 length disagrees with manifest")
    try:
        archive = base64.b64decode(encoded, validate=True)
    except Exception as exc:
        raise ValueError("outcome snapshot Base64 shards do not decode cleanly") from exc

    actual_archive = sha256_bytes(archive)
    expected_archive = str(manifest.get("archive_sha256", ""))
    if not expected_archive or actual_archive != expected_archive:
        raise ValueError(f"outcome snapshot archive SHA mismatch: expected {expected_archive}, got {actual_archive}")
    if int(manifest.get("archive_bytes", -1)) != len(archive):
        raise ValueError("outcome snapshot archive byte length disagrees with manifest")

    try:
        csv_bytes = gzip.decompress(archive)
    except Exception as exc:
        raise ValueError("outcome snapshot gzip archive does not decompress cleanly") from exc
    actual_csv = sha256_bytes(csv_bytes)
    expected_csv = str(manifest.get("csv_sha256", ""))
    if not expected_csv or actual_csv != expected_csv:
        raise ValueError(f"outcome snapshot payload SHA mismatch: expected {expected_csv}, got {actual_csv}")

    return csv_bytes, archive, {"shards": shard_runtime, "archive_sha256": actual_archive, "csv_sha256": actual_csv}


def load_frozen_prices(
    start: str,
    end: str | None,
    *,
    snapshot_path: Path | None = None,
    manifest_path: Path = DEFAULT_MANIFEST,
    shard_paths: tuple[Path, ...] = DEFAULT_SHARDS,
) -> tuple[pd.DataFrame, dict]:
    """Load a hash-verified frozen price panel.

    `snapshot_path` is retained for unit tests and ad-hoc plain-CSV evidence.
    Normal repository execution leaves it unset and reconstructs the committed
    Base64-sharded gzip snapshot.
    """
    if not manifest_path.exists():
        raise FileNotFoundError("committed Issue #64 outcome snapshot manifest is not available")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if snapshot_path is not None:
        if not snapshot_path.exists():
            raise FileNotFoundError("requested outcome snapshot is not available")
        expected_csv = str(manifest.get("csv_sha256", ""))
        actual_csv = sha256_file(snapshot_path)
        if not expected_csv or actual_csv != expected_csv:
            raise ValueError(f"outcome snapshot SHA mismatch: expected {expected_csv}, got {actual_csv}")
        raw = pd.read_csv(snapshot_path)
        archive_sha = None
        storage_paths = [display_path(snapshot_path)]
        shard_runtime = None
    else:
        csv_bytes, _archive, provenance = _load_sharded_archive(manifest, shard_paths)
        raw = pd.read_csv(io.BytesIO(csv_bytes))
        actual_csv = provenance["csv_sha256"]
        archive_sha = provenance["archive_sha256"]
        storage_paths = [item["path"] for item in provenance["shards"]]
        shard_runtime = provenance["shards"]

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
        "source_mode": "committed_frozen_snapshot" if snapshot_path is None else "explicit_plain_csv_snapshot",
        "snapshot_path": storage_paths[0] if len(storage_paths) == 1 else "base64-sharded repository snapshot",
        "snapshot_paths": storage_paths,
        "snapshot_manifest_path": display_path(manifest_path),
        "snapshot_sha256": actual_csv,
        "snapshot_csv_sha256": actual_csv,
        "snapshot_archive_sha256": archive_sha,
        "snapshot_shards": shard_runtime,
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
    return DEFAULT_MANIFEST.exists() and all(path.exists() for path in DEFAULT_SHARDS)
