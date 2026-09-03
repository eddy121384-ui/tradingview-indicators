#!/usr/bin/env python3
"""Deterministic frozen outcome-price snapshot support for Issue #74.

The research contract requires the exact SPY/TLT/SHV/GSG price panel to be
committed before portfolio PnL is interpreted. The snapshot is stored as UTF-8
Base64 shards containing one deterministic gzip-compressed CSV so text-only
repository writes remain byte-for-byte reproducible.
"""
from __future__ import annotations

import base64
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
ASSETS = ("SPY", "TLT", "SHV", "GSG")
SNAPSHOT_COLUMNS = ["date", *ASSETS]
DEFAULT_MANIFEST = DATA_DIR / "issue-74-outcome-prices-manifest.json"
SHARD_PREFIX = "issue-74-outcome-prices-"
DEFAULT_SHARD_CHARS = 16000


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(HERE))
    except ValueError:
        return str(resolved)


def _assert_github_pr_checkout_matches_trigger() -> None:
    """Fail closed if a PR run checked out a tip newer than its triggering SHA."""
    if os.environ.get("GITHUB_EVENT_NAME") != "pull_request":
        return
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        raise RuntimeError("GitHub PR run is missing GITHUB_EVENT_PATH")
    payload = json.loads(Path(event_path).read_text(encoding="utf-8"))
    expected = str(payload.get("pull_request", {}).get("head", {}).get("sha", "")).strip()
    if not expected:
        raise RuntimeError("GitHub PR event does not declare pull_request.head.sha")
    actual = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=HERE,
        text=True,
    ).strip()
    if actual != expected:
        raise RuntimeError(
            "Issue #74 exact-head provenance failure: "
            f"triggered SHA {expected}, checked-out SHA {actual}"
        )


def normalize_price_panel(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result.index = pd.DatetimeIndex(pd.to_datetime(result.index, errors="raise")).normalize().astype("datetime64[ns]")
    if list(result.columns) != list(ASSETS):
        result = result.loc[:, list(ASSETS)]
    result = result.apply(pd.to_numeric, errors="raise").astype(float).sort_index()
    if result.empty:
        raise ValueError("Issue #74 outcome snapshot cannot be empty")
    if result.index.duplicated().any() or not result.index.is_monotonic_increasing:
        raise ValueError("Issue #74 outcome dates must be unique and increasing")
    values = result.to_numpy(float)
    if not np.isfinite(values).all() or (values <= 0.0).any():
        raise ValueError("Issue #74 outcome prices must be finite and positive")
    return result


def serialize_csv(frame: pd.DataFrame) -> bytes:
    prices = normalize_price_panel(frame)
    serial = prices.copy()
    serial.index.name = "date"
    return serial.to_csv(date_format="%Y-%m-%d", float_format="%.17g").encode("utf-8")


def freeze_price_panel(
    frame: pd.DataFrame,
    *,
    data_dir: Path = DATA_DIR,
    source: dict,
    shard_chars: int = DEFAULT_SHARD_CHARS,
) -> dict:
    if shard_chars < 1000:
        raise ValueError("shard_chars is implausibly small")
    prices = normalize_price_panel(frame)
    csv_bytes = serialize_csv(prices)
    archive = gzip.compress(csv_bytes, compresslevel=9, mtime=0)
    encoded = base64.b64encode(archive).decode("ascii")
    data_dir.mkdir(parents=True, exist_ok=True)

    # Refuse to overwrite a prior committed freeze silently.
    manifest_path = data_dir / DEFAULT_MANIFEST.name
    if manifest_path.exists():
        raise FileExistsError(f"Issue #74 frozen outcome manifest already exists: {manifest_path}")

    shards: list[dict] = []
    for index, start in enumerate(range(0, len(encoded), shard_chars), start=1):
        text = encoded[start : start + shard_chars]
        path = data_dir / f"{SHARD_PREFIX}{index:02d}.b64"
        if path.exists():
            raise FileExistsError(f"Issue #74 snapshot shard already exists: {path}")
        path.write_text(text + "\n", encoding="ascii")
        shards.append({
            "path": display_path(path),
            "chars": len(text),
            "sha256": sha256_bytes(text.encode("ascii")),
        })

    manifest = {
        "schema_version": 1,
        "issue": 74,
        "role": "durable frozen SPY/TLT/SHV/GSG adjusted-price input snapshot",
        "columns": SNAPSHOT_COLUMNS,
        "rows": int(len(prices)),
        "first_date": prices.index.min().date().isoformat(),
        "last_date": prices.index.max().date().isoformat(),
        "csv_sha256": sha256_bytes(csv_bytes),
        "archive_sha256": sha256_bytes(archive),
        "archive_bytes": len(archive),
        "base64_chars": len(encoded),
        "shard_chars": shard_chars,
        "shards": shards,
        "source": source,
        "price_semantics": "Yahoo Finance yfinance auto_adjust=True adjusted Close; strict common finite SPY/TLT/SHV/GSG calendar",
        "interpretation_boundary": "Frozen research input for reproducibility; not a production market-data source.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def _manifest_shard_paths(manifest: dict, manifest_path: Path) -> tuple[Path, ...]:
    base = manifest_path.parent
    result: list[Path] = []
    for item in manifest.get("shards", []):
        declared = str(item.get("path", ""))
        if not declared:
            raise ValueError("Issue #74 outcome manifest contains a shard without a path")
        name = Path(declared).name
        if not name.startswith(SHARD_PREFIX) or not name.endswith(".b64"):
            raise ValueError(f"unexpected Issue #74 shard name: {name}")
        result.append(base / name)
    if not result:
        raise ValueError("Issue #74 outcome manifest has no shards")
    return tuple(result)


def load_frozen_prices(
    start: str = "2007-01-01",
    end: str | None = None,
    *,
    manifest_path: Path = DEFAULT_MANIFEST,
) -> tuple[pd.DataFrame, dict]:
    _assert_github_pr_checkout_matches_trigger()
    if not manifest_path.exists():
        raise FileNotFoundError("committed Issue #74 outcome snapshot manifest is not available")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("issue") != 74 or manifest.get("columns") != SNAPSHOT_COLUMNS:
        raise ValueError("unexpected Issue #74 outcome snapshot identity")

    shard_paths = _manifest_shard_paths(manifest, manifest_path)
    encoded_parts: list[str] = []
    runtime_shards: list[dict] = []
    declared = manifest["shards"]
    if len(declared) != len(shard_paths):
        raise ValueError("Issue #74 outcome shard list mismatch")
    for path, item in zip(shard_paths, declared, strict=True):
        if not path.exists():
            raise FileNotFoundError(f"Issue #74 outcome shard missing: {path}")
        text = path.read_text(encoding="ascii").strip()
        actual_sha = sha256_bytes(text.encode("ascii"))
        if len(text) != int(item["chars"]) or actual_sha != str(item["sha256"]):
            raise ValueError(f"Issue #74 outcome shard verification failed: {path.name}")
        if Path(str(item["path"])).name != path.name:
            raise ValueError(f"Issue #74 outcome shard path mismatch: {path.name}")
        encoded_parts.append(text)
        runtime_shards.append({"path": display_path(path), "chars": len(text), "sha256": actual_sha})

    encoded = "".join(encoded_parts)
    if len(encoded) != int(manifest["base64_chars"]):
        raise ValueError("Issue #74 combined Base64 length mismatch")
    archive = base64.b64decode(encoded, validate=True)
    if len(archive) != int(manifest["archive_bytes"]) or sha256_bytes(archive) != str(manifest["archive_sha256"]):
        raise ValueError("Issue #74 gzip archive verification failed")
    csv_bytes = gzip.decompress(archive)
    if sha256_bytes(csv_bytes) != str(manifest["csv_sha256"]):
        raise ValueError("Issue #74 CSV payload verification failed")

    raw = pd.read_csv(io.BytesIO(csv_bytes))
    if list(raw.columns) != SNAPSHOT_COLUMNS:
        raise ValueError(f"unexpected Issue #74 snapshot columns: {list(raw.columns)}")
    raw["date"] = pd.to_datetime(raw["date"], errors="raise")
    prices = normalize_price_panel(raw.set_index("date"))
    if len(prices) != int(manifest["rows"]):
        raise ValueError("Issue #74 snapshot row count mismatch")
    if prices.index.min().date().isoformat() != manifest["first_date"] or prices.index.max().date().isoformat() != manifest["last_date"]:
        raise ValueError("Issue #74 snapshot coverage mismatch")

    selected = prices.loc[prices.index >= pd.Timestamp(start)]
    if end is not None:
        selected = selected.loc[selected.index < pd.Timestamp(end)]
    if selected.empty:
        raise ValueError("requested Issue #74 outcome snapshot slice is empty")
    runtime = {
        "provider": "frozen repository snapshot derived from Yahoo Finance",
        "source_mode": "committed_frozen_snapshot",
        "snapshot_manifest_path": display_path(manifest_path),
        "snapshot_csv_sha256": manifest["csv_sha256"],
        "snapshot_archive_sha256": manifest["archive_sha256"],
        "snapshot_shards": runtime_shards,
        "snapshot_rows": int(len(prices)),
        "snapshot_first_date": manifest["first_date"],
        "snapshot_last_date": manifest["last_date"],
        "symbols": list(ASSETS),
        "rows": int(len(selected)),
        "first_date": selected.index.min().date().isoformat(),
        "last_date": selected.index.max().date().isoformat(),
        "price_semantics": manifest["price_semantics"],
        "calendar_semantics": "strict common finite SPY/TLT/SHV/GSG calendar; no outcome forward-fill",
    }
    return selected, runtime


def committed_snapshot_available(manifest_path: Path = DEFAULT_MANIFEST) -> bool:
    if not manifest_path.exists():
        return False
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        return all(path.exists() for path in _manifest_shard_paths(manifest, manifest_path))
    except Exception:
        return False
