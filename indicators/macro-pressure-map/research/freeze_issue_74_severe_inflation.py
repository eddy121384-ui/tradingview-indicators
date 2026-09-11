#!/usr/bin/env python3
"""Freeze full daily raw IPI from the exact prior V6.6 Pine parity log.

This utility does no portfolio evaluation. It accepts only the already-frozen
Issue #64 source-log SHA and writes the exact daily raw IPI plus the existing
V6.6 severe-inflation classification (IPI >= +60).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_issue_64_frozen_regimes import derive_daily_regimes, sha256_file
from issue_74_severe_inflation import (
    DEFAULT_DATA,
    DEFAULT_MANIFEST,
    EXPECTED_SOURCE_LOG_SHA256,
    INFLATION_EXTREME_THRESHOLD,
)


def freeze(log_path: Path, data_path: Path, manifest_path: Path) -> dict:
    actual_source_sha = sha256_file(log_path)
    if actual_source_sha != EXPECTED_SOURCE_LOG_SHA256:
        raise ValueError(
            f"Pine log SHA mismatch: expected {EXPECTED_SOURCE_LOG_SHA256}, got {actual_source_sha}"
        )
    daily = derive_daily_regimes(log_path)
    out = daily[["IPI"]].copy()
    out["severe_inflation"] = out["IPI"].ge(INFLATION_EXTREME_THRESHOLD)
    out.index.name = "date"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    if data_path.exists() or manifest_path.exists():
        raise FileExistsError("Issue #74 severe-inflation evidence is already frozen; refusing overwrite")
    out.to_csv(data_path, date_format="%Y-%m-%d", float_format="%.17g")
    manifest = {
        "schema_version": 1,
        "issue": 74,
        "role": "frozen daily raw IPI for severe-inflation classification",
        "source_log_sha256": actual_source_sha,
        "source_role": "same operator-local TradingView V6.6 Pine parity log already hash-frozen for Issue #64",
        "inflation_extreme_threshold": INFLATION_EXTREME_THRESHOLD,
        "classification": "severe_inflation = raw IPI >= +60.0",
        "rows": int(len(out)),
        "first_date": out.index.min().date().isoformat(),
        "last_date": out.index.max().date().isoformat(),
        "severe_rows": int(out["severe_inflation"].sum()),
        "csv_sha256": sha256_file(data_path),
        "production_v66_modified": False,
        "portfolio_results_calculated": False,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Freeze Issue #74 severe-inflation daily state")
    parser.add_argument("--pine-log", type=Path, required=True)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    print(json.dumps(freeze(args.pine_log, args.data, args.manifest), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
