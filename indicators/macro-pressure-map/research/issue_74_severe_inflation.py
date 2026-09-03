#!/usr/bin/env python3
"""Issue #74 severe-inflation evidence support.

Phase C needs the historical V6.6 severe-inflation condition (raw IPI >= +60).
The preregistration permits either the exact prior hash-matching Pine parity log
or an equivalently exact verified reconstruction.  The compact committed format
stores every positive severe-inflation source date plus raw IPI and treats every
other source date within the verified coverage window as false.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"

# Legacy full-daily artifact path retained for backwards compatibility.
DEFAULT_DATA = DATA_DIR / "issue-74-frozen-severe-inflation.csv"
DEFAULT_MANIFEST = DATA_DIR / "issue-74-frozen-severe-inflation-manifest.json"
EXPECTED_SOURCE_LOG_SHA256 = "c0220d4974b2fd0154c4cf8f33b4b3effb27a58e21ee96a1b0109011ce638e3d"

# Verified-reconstruction compact evidence committed for Phase C.
POSITIVE_DATA = DATA_DIR / "issue-74-severe-inflation-positive-dates.csv"
POSITIVE_MANIFEST = DATA_DIR / "issue-74-severe-inflation-positive-dates-manifest.json"
EXPECTED_RECONSTRUCTION_SOURCE_SHA256 = "6c5aa03419d2e5325d28fb33bf9c83a9744d7170da84f72a614676a7fc1aad4d"
RECONSTRUCTION_PARITY_MAX_ERROR = 5e-8
RECONSTRUCTION_MIN_CHECKPOINTS = 51
INFLATION_EXTREME_THRESHOLD = 60.0


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compact_available(
    data_path: Path = POSITIVE_DATA,
    manifest_path: Path = POSITIVE_MANIFEST,
) -> bool:
    return data_path.exists() and manifest_path.exists()


def legacy_available(
    data_path: Path = DEFAULT_DATA,
    manifest_path: Path = DEFAULT_MANIFEST,
) -> bool:
    return data_path.exists() and manifest_path.exists()


def available() -> bool:
    """Return true only when at least one frozen evidence path fully validates."""
    if compact_available():
        try:
            load_severe_positive_dates()
            return True
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            pass
    if legacy_available():
        try:
            load_daily_ipi()
            return True
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            pass
    return False


def load_severe_positive_dates(
    data_path: Path = POSITIVE_DATA,
    manifest_path: Path = POSITIVE_MANIFEST,
) -> tuple[pd.Series, dict]:
    """Load verified positive severe-inflation dates as raw IPI observations."""
    if not compact_available(data_path, manifest_path):
        raise FileNotFoundError("Issue #74 verified severe-inflation reconstruction is not frozen")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("issue") != 74:
        raise ValueError("unexpected Issue #74 severe-inflation manifest identity")
    if manifest.get("evidence_mode") != "equivalently exact verified reconstruction":
        raise ValueError("Issue #74 compact evidence is not a verified reconstruction")
    if manifest.get("source_log_sha256") != EXPECTED_RECONSTRUCTION_SOURCE_SHA256:
        raise ValueError("Issue #74 reconstruction source SHA mismatch")
    if manifest.get("parity_pass") is not True:
        raise ValueError("Issue #74 reconstruction did not pass parity")
    if int(manifest.get("parity_checkpoints", 0)) < RECONSTRUCTION_MIN_CHECKPOINTS:
        raise ValueError("Issue #74 reconstruction parity checkpoint count is insufficient")
    if float(manifest.get("parity_max_abs_ipi_error")) > RECONSTRUCTION_PARITY_MAX_ERROR:
        raise ValueError("Issue #74 reconstruction parity error exceeds frozen gate")
    if float(manifest.get("inflation_extreme_threshold")) != INFLATION_EXTREME_THRESHOLD:
        raise ValueError("Issue #74 severe-inflation threshold differs from frozen V6.6 +60")
    if sha256_file(data_path) != str(manifest.get("positive_dates_csv_sha256")):
        raise ValueError("Issue #74 severe-inflation positive-date CSV SHA mismatch")

    frame = pd.read_csv(data_path)
    if list(frame.columns) != ["date", "IPI"]:
        raise ValueError(f"unexpected Issue #74 compact evidence columns: {list(frame.columns)}")
    frame["date"] = pd.to_datetime(frame["date"], errors="raise").dt.normalize()
    frame["IPI"] = pd.to_numeric(frame["IPI"], errors="raise").astype(float)
    if frame["date"].duplicated().any() or not frame["date"].is_monotonic_increasing:
        raise ValueError("Issue #74 severe-inflation positive dates must be unique and increasing")
    if not frame["IPI"].ge(INFLATION_EXTREME_THRESHOLD).all():
        raise ValueError("Issue #74 compact evidence contains non-severe IPI values")
    if len(frame) != int(manifest.get("severe_rows")):
        raise ValueError("Issue #74 compact severe-row count mismatch")
    return frame.set_index("date")["IPI"], manifest


def severe_flag_on_calendar(calendar: pd.DatetimeIndex) -> tuple[pd.Series, dict]:
    """Map the verified binary severe state onto an outcome trading calendar."""
    positive, manifest = load_severe_positive_dates()
    first = pd.Timestamp(manifest["raw_ipi_coverage_first_date"])
    last = pd.Timestamp(manifest["raw_ipi_coverage_last_date"])
    if calendar.min() < first or calendar.max() > last:
        raise ValueError("outcome calendar extends beyond verified raw-IPI coverage")
    flag = pd.Series(False, index=calendar, dtype=bool)
    flag.loc[flag.index.intersection(positive.index)] = True
    return flag, manifest


def load_daily_ipi(
    data_path: Path = DEFAULT_DATA,
    manifest_path: Path = DEFAULT_MANIFEST,
) -> tuple[pd.Series, dict]:
    """Legacy full-daily loader for the exact prior source-log path."""
    if not legacy_available(data_path, manifest_path):
        raise FileNotFoundError(
            "Full daily raw IPI is not committed; use verified compact severe-date evidence for Phase C."
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
    return frame.set_index("date")["IPI"], manifest
