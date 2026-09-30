#!/usr/bin/env python3
"""Audit the completed Issue #119 Bloomberg raw snapshot.

Engineering/data-quality audit only. No classifier or policy economics.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import pandas as pd

from issue119_bbg_common import EVENT_END, file_sha256


def audit_snapshot(universe_path: Path, manifest_path: Path, raw_dir: Path) -> dict:
    universe = pd.read_csv(universe_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    completed = manifest.get("completed", {})
    failures = manifest.get("failures", {})
    normalization = manifest.get("normalization", {})

    universe_figi = set(universe["figi"].astype(str))
    completed_figi = set(map(str, completed))
    missing_figi = sorted(universe_figi - completed_figi)
    extra_figi = sorted(completed_figi - universe_figi)

    checksum_failures = []
    row_counts = []
    start_dates = []
    end_dates = []
    repaired = []
    missing_volume_total = 0

    for figi, diag in completed.items():
        path = raw_dir / str(diag["path"])
        if not path.exists():
            checksum_failures.append({"figi": figi, "reason": "missing_file"})
            continue
        actual = file_sha256(path)
        if actual != diag.get("sha256"):
            checksum_failures.append(
                {
                    "figi": figi,
                    "reason": "sha256_mismatch",
                    "expected": diag.get("sha256"),
                    "actual": actual,
                }
            )

        row_counts.append(int(diag.get("rows", 0)))
        if diag.get("min_date"):
            start_dates.append(str(diag["min_date"]))
        if diag.get("max_date"):
            end_dates.append(str(diag["max_date"]))
        missing_volume_total += int(diag.get("missing", {}).get("volume", 0))

        repair_count = int(diag.get("ohlc_range_repairs", 0))
        if repair_count:
            repaired.append(
                {
                    "figi": figi,
                    "ticker": diag.get("ticker"),
                    "security": diag.get("security"),
                    "repairs": repair_count,
                    "records": diag.get("ohlc_range_repair_records", []),
                }
            )

    sector_counts = Counter(universe["sector"].astype(str))
    sleeve_counts = Counter(universe["sleeve"].astype(str))

    summary = {
        "issue": 119,
        "universe_rows": int(len(universe)),
        "completed": int(len(completed)),
        "failures": int(len(failures)),
        "missing_from_completed": missing_figi,
        "extra_completed": extra_figi,
        "checksum_failures": checksum_failures,
        "universe_sha256_actual": file_sha256(universe_path),
        "universe_sha256_manifest": manifest.get("universe_sha256"),
        "universe_sha256_match": (
            file_sha256(universe_path) == manifest.get("universe_sha256")
        ),
        "sector_counts": dict(sorted(sector_counts.items())),
        "sleeve_counts": dict(sorted(sleeve_counts.items())),
        "row_count_min": min(row_counts) if row_counts else None,
        "row_count_median": (
            float(pd.Series(row_counts).median()) if row_counts else None
        ),
        "row_count_max": max(row_counts) if row_counts else None,
        "earliest_security_start": min(start_dates) if start_dates else None,
        "latest_security_end": max(end_dates) if end_dates else None,
        "requested_end": manifest.get("requested_end"),
        "requested_end_matches_frozen_event_end": (
            manifest.get("requested_end") == EVENT_END
        ),
        "missing_volume_total": missing_volume_total,
        "normalization_contract_version": normalization.get("contract_version"),
        "ohlc_range_repairs_total_manifest": normalization.get(
            "ohlc_range_repairs_total", 0
        ),
        "securities_with_repairs_manifest": normalization.get(
            "securities_with_ohlc_range_repairs", 0
        ),
        "ohlc_range_repairs_total_recomputed": int(
            sum(x["repairs"] for x in repaired)
        ),
        "securities_with_repairs_recomputed": int(len(repaired)),
        "repaired_securities": repaired,
    }

    summary["pass"] = all(
        [
            summary["universe_rows"] == 300,
            summary["completed"] == 300,
            summary["failures"] == 0,
            not summary["missing_from_completed"],
            not summary["extra_completed"],
            not summary["checksum_failures"],
            summary["universe_sha256_match"],
            summary["requested_end_matches_frozen_event_end"],
            summary["normalization_contract_version"] == 2,
            summary["ohlc_range_repairs_total_manifest"]
            == summary["ohlc_range_repairs_total_recomputed"],
            summary["securities_with_repairs_manifest"]
            == summary["securities_with_repairs_recomputed"],
        ]
    )
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--raw-dir", type=Path, required=True)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()

    report = audit_snapshot(args.universe, args.manifest, args.raw_dir)

    if args.output:
        args.output.write_text(
            json.dumps(report, indent=2, default=str) + "\n",
            encoding="utf-8",
        )

    compact = {
        "pass": report["pass"],
        "universe_rows": report["universe_rows"],
        "completed": report["completed"],
        "failures": report["failures"],
        "universe_sha256_match": report["universe_sha256_match"],
        "row_count_min": report["row_count_min"],
        "row_count_median": report["row_count_median"],
        "row_count_max": report["row_count_max"],
        "earliest_security_start": report["earliest_security_start"],
        "latest_security_end": report["latest_security_end"],
        "missing_volume_total": report["missing_volume_total"],
        "ohlc_range_repairs_total": report[
            "ohlc_range_repairs_total_recomputed"
        ],
        "securities_with_repairs": report[
            "securities_with_repairs_recomputed"
        ],
    }
    print(json.dumps(compact, indent=2))
    if not report["pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
