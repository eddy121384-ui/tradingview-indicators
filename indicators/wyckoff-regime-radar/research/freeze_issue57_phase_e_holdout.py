#!/usr/bin/env python3
"""Freeze the preregistered Issue #57 Phase-E untouched FX holdout.

This module downloads only the three predeclared cross-market holdout pairs from
an already-pinned static GitHub commit, validates OHLC without repair, stores the
normalized files, and records checksums. It does not compute any Wyckoff output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

from freeze_static_fx_canonical_data import (
    RAW_BASE,
    SOURCE_COMMIT,
    SOURCE_REPO,
    download_text,
    git_blob_sha,
    normalize_source_text,
    validate_ohlc,
)


HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data"
FROZEN_DIR = DATA_DIR / "frozen"
MANIFEST_PATH = DATA_DIR / "issue-57-phase-e-holdout-manifest.json"
HOLDOUT_PAIRS = ("USDCAD", "USDCHF", "NZDUSD")
EXPECTED_ROWS = 2400
EXPECTED_START = "2012-12-04"
EXPECTED_END = "2022-03-04"


def _source_path(pair: str) -> str:
    return f"{pair}/{pair}_D1.csv"


def _frozen_path(pair: str) -> Path:
    return FROZEN_DIR / f"issue-57-holdout-{pair.lower()}-static-d1.csv"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_source(pair: str) -> tuple[pd.DataFrame, bytes, str, str]:
    path = _source_path(pair)
    url = f"{RAW_BASE}/{path}"
    raw_text = download_text(url)
    raw_bytes = raw_text.encode("utf-8")
    frame = normalize_source_text(raw_text, pair)
    validate_ohlc(frame, pair)
    return frame, raw_bytes, url, path


def _validate_coverage(frame: pd.DataFrame, pair: str) -> None:
    rows = len(frame)
    start = str(frame["date"].iloc[0])
    end = str(frame["date"].iloc[-1])
    if rows != EXPECTED_ROWS or start != EXPECTED_START or end != EXPECTED_END:
        raise RuntimeError(
            f"{pair}: holdout coverage drifted; expected {EXPECTED_ROWS} rows "
            f"{EXPECTED_START}..{EXPECTED_END}, got {rows} rows {start}..{end}"
        )


def freeze() -> dict[str, Any]:
    FROZEN_DIR.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {
        "issue": 57,
        "phase": "E-independent-cross-market-holdout",
        "status": "SEALED_DO_NOT_EVALUATE_UNTIL_V06_PINE_PARITY_GATE_PASSES",
        "source_repository": SOURCE_REPO,
        "source_commit": SOURCE_COMMIT,
        "selection": {
            "pairs": list(HOLDOUT_PAIRS),
            "reason": "untouched cross-market holdout; same pinned source/bar construction as Issue #55",
            "used_in_issue_55_or_v06_phases_a_to_d": False,
        },
        "pairs": {},
    }

    for pair in HOLDOUT_PAIRS:
        frame, raw_bytes, url, source_path = _load_source(pair)
        _validate_coverage(frame, pair)
        payload = frame.to_csv(index=False, lineterminator="\n", float_format="%.10g").encode("utf-8")
        target = _frozen_path(pair)
        target.write_bytes(payload)
        manifest["pairs"][pair] = {
            "source_url": url,
            "source_path": source_path,
            "source_git_blob_sha": git_blob_sha(raw_bytes),
            "raw_sha256": _sha256(raw_bytes),
            "frozen_file": str(target.relative_to(DATA_DIR)),
            "frozen_sha256": _sha256(payload),
            "rows": len(frame),
            "start_date": str(frame["date"].iloc[0]),
            "end_date": str(frame["date"].iloc[-1]),
            "ohlc_validation": "PASS_NO_REPAIR",
            "evaluation_status": "SEALED_NOT_COMPUTED",
        }

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def verify() -> dict[str, Any]:
    if not MANIFEST_PATH.exists():
        raise RuntimeError("Phase-E holdout manifest missing; run freeze first")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("status") != "SEALED_DO_NOT_EVALUATE_UNTIL_V06_PINE_PARITY_GATE_PASSES":
        raise RuntimeError("Phase-E holdout seal/status changed unexpectedly")
    if tuple(manifest.get("selection", {}).get("pairs", [])) != HOLDOUT_PAIRS:
        raise RuntimeError("Phase-E holdout pair set changed")
    if manifest.get("source_commit") != SOURCE_COMMIT:
        raise RuntimeError("Phase-E holdout source commit changed")

    for pair in HOLDOUT_PAIRS:
        entry = manifest["pairs"][pair]
        target = DATA_DIR / entry["frozen_file"]
        data = target.read_bytes()
        if _sha256(data) != entry["frozen_sha256"]:
            raise RuntimeError(f"{pair}: frozen holdout checksum mismatch")
        frame = pd.read_csv(target)
        validate_ohlc(frame, pair)
        _validate_coverage(frame, pair)
        if entry.get("evaluation_status") != "SEALED_NOT_COMPUTED":
            raise RuntimeError(f"{pair}: holdout evaluation status is no longer sealed")
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Freeze/verify Issue #57 Phase-E cross-market holdout")
    parser.add_argument("mode", choices=("freeze", "verify"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = freeze() if args.mode == "freeze" else verify()
    print(
        json.dumps(
            {
                "mode": args.mode,
                "status": manifest["status"],
                "source_commit": manifest["source_commit"],
                "pairs": {
                    pair: {
                        "rows": manifest["pairs"][pair]["rows"],
                        "start_date": manifest["pairs"][pair]["start_date"],
                        "end_date": manifest["pairs"][pair]["end_date"],
                        "frozen_sha256": manifest["pairs"][pair]["frozen_sha256"],
                        "evaluation_status": manifest["pairs"][pair]["evaluation_status"],
                    }
                    for pair in HOLDOUT_PAIRS
                },
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
