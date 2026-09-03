#!/usr/bin/env python3
"""Issue #74 severe-inflation evidence support.

Phase C needs the historical raw V6.6 IPI >= +60 condition. Issue #64 committed
only the 3x3 regime transitions plus sparse axis audit checkpoints, so Phase C
must not infer the missing daily extreme state. This module fails closed until
an exact daily evidence artifact is produced from the previously hash-frozen
Pine parity log.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
DEFAULT_DATA = DATA_DIR / "issue-74-frozen-severe-inflation.csv"
DEFAULT_MANIFEST = DATA_DIR / "issue-74-frozen-severe-inflation-manifest.json"
EXPECTED_SOURCE_LOG_SHA256 = "c0220d4974b2fd0154c4cf8f33b4b3effb27a58e21ee96a1b0109011ce638e3d"
INFLATION_EXTREME_THRESHOLD = 60.0


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def available(data_path: Path = DEFAULT_DATA, manifest_path: Path = DEFAULT_MANIFEST) -> bool:
    return data_path.exists() and manifest_path.exists()


def load_daily_ipi(
    data_path: Path = DEFAULT_DATA,
    manifest_path: Path = DEFAULT_MANIFEST,
) -> tuple[pd.Series, dict]:
    if not available(data_path, manifest_path):
        raise FileNotFoundError(
            "Issue #74 Phase C is blocked: full daily raw IPI severe-inflation evidence is not frozen. "
            "The Issue #64 3x3 transition artifact is insufficient to infer historical IPI >= +60 days."
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("issue") != 74 or manifest.get("role") != "frozen daily raw IPI for severe-inflation classification":
        raise ValueError("unexpected Issue #74 severe-inflation manifest identity")
    if manifest.get("source_log_sha256") != EXPECTED_SOURCE_LOG_SHA256:
        raise ValueError("Issue #74 severe-inflation source log is not the exact prior Pine evidence")
    if float(manifest.get("inflation_extreme_threshold")) != INFLATION_EXTREME_THRESHOLD:
        raise ValueError("Issue #74 severe-inflation threshold differs from frozen V6.6 +60")
    actual_sha = sha256_file(data_path)
    if actual_sha != str(manifest.get("csv_sha256")):
        raise ValueError("Issue #74 severe-inflation CSV SHA mismatch")
    frame = pd.read_csv(data_path)
    if list(frame.columns) != ["date", "IPI", "severe_inflation"]:
        raise ValueError(f"unexpected Issue #74 severe-inflation columns: {list(frame.columns)}")
    frame["date"] = pd.to_datetime(frame["date"], errors="raise").dt.normalize()
    frame["IPI"] = pd.to_numeric(frame["IPI"], errors="raise").astype(float)
    expected = frame["IPI"].ge(INFLATION_EXTREME_THRESHOLD)
    actual = frame["severe_inflation"].astype(str).str.lower().map({"true": True, "false": False})
    if actual.isna().any() or not actual.equals(expected):
        raise ValueError("Issue #74 severe-inflation flags do not equal raw IPI >= +60")
    if frame["date"].duplicated().any() or not frame["date"].is_monotonic_increasing:
        raise ValueError("Issue #74 severe-inflation dates must be unique and increasing")
    series = frame.set_index("date")["IPI"]
    return series, manifest
