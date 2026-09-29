#!/usr/bin/env python3
"""Download Bloomberg OHLCV for the frozen Issue #119 diagnostic universe.

This module performs data acquisition and validation only. It does not import
or execute the Issue #78 classifier or policy economics.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Protocol

import pandas as pd

from issue119_bbg_client import BloombergDesktopClient
from issue119_bbg_common import (
    EVENT_END,
    HISTORICAL_FIELDS,
    RAW_START,
    chunked,
    file_sha256,
    normalize_ohlcv,
)


class HistoryClient(Protocol):
    def historical_data(
        self,
        securities: list[str],
        *,
        start_date: str,
        end_date: str,
        fields: tuple[str, ...] = HISTORICAL_FIELDS,
    ) -> dict[str, pd.DataFrame]: ...


def _git_head() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def _safe_name(figi: str) -> str:
    return "".join(
        ch if ch.isalnum() or ch in "-_." else "_"
        for ch in figi
    )


def _load_checkpoint(path: Path) -> dict:
    if not path.exists():
        return {"completed": {}, "failures": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json_atomic(path: Path, payload: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    os.replace(tmp, path)


def _write_security_file(
    raw_dir: Path,
    *,
    figi: str,
    ticker: str,
    security: str,
    frame: pd.DataFrame,
) -> tuple[Path, dict]:
    normalized, diagnostics = normalize_ohlcv(frame)
    normalized.insert(0, "security", security)
    normalized.insert(0, "ticker", ticker)
    normalized.insert(0, "stable_security_id", figi)

    path = raw_dir / f"{_safe_name(figi)}.csv.gz"
    normalized.to_csv(path, index=False, compression="gzip")
    diagnostics = {
        **diagnostics,
        "sha256": file_sha256(path),
        "path": path.name,
        "ticker": ticker,
        "security": security,
        "figi": figi,
    }
    return path, diagnostics


def download_universe(
    client: HistoryClient,
    universe: pd.DataFrame,
    output_dir: Path,
    *,
    start_date: str = RAW_START,
    end_date: str = EVENT_END,
    batch_size: int = 25,
    max_attempts: int = 3,
    sleep: Callable[[float], None] = time.sleep,
) -> dict:
    required = {"security", "figi", "ticker"}
    missing = required.difference(universe.columns)
    if missing:
        raise ValueError(
            f"universe missing columns: {sorted(missing)}"
        )
    if universe["figi"].duplicated().any():
        raise ValueError("universe contains duplicate FIGI")
    if len(universe) == 0:
        raise ValueError("universe is empty")

    output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(exist_ok=True)
    checkpoint_path = (
        output_dir / "issue119_bbg_oos2_checkpoint.json"
    )
    checkpoint = _load_checkpoint(checkpoint_path)
    completed: dict[str, dict] = dict(
        checkpoint.get("completed", {})
    )
    failures: dict[str, str] = dict(
        checkpoint.get("failures", {})
    )

    rows = {
        str(row.security): {
            "figi": str(row.figi),
            "ticker": str(row.ticker),
            "security": str(row.security),
        }
        for row in universe.itertuples(index=False)
    }

    pending: list[str] = []
    for security, meta in rows.items():
        prev = completed.get(meta["figi"])
        if prev:
            path = raw_dir / str(prev.get("path", ""))
            if (
                path.exists()
                and prev.get("sha256") == file_sha256(path)
            ):
                continue
            completed.pop(meta["figi"], None)
        pending.append(security)

    batches = chunked(pending, batch_size)
    print(
        f"[issue119] universe={len(universe)} completed={len(completed)} "
        f"pending={len(pending)} batches={len(batches)}",
        flush=True,
    )

    for batch_no, batch in enumerate(batches, start=1):
        remaining = list(batch)
        last_errors: dict[str, str] = {}
        print(
            f"[issue119] batch {batch_no}/{len(batches)} "
            f"requesting {len(remaining)} securities",
            flush=True,
        )

        for attempt in range(1, max_attempts + 1):
            if not remaining:
                break

            print(
                f"[issue119] batch {batch_no}/{len(batches)} "
                f"attempt {attempt}/{max_attempts}; remaining={len(remaining)}",
                flush=True,
            )

            try:
                response = client.historical_data(
                    remaining,
                    start_date=start_date,
                    end_date=end_date,
                    fields=HISTORICAL_FIELDS,
                )
                transport_error = None
            except Exception as exc:
                response = {}
                transport_error = (
                    f"{type(exc).__name__}: {exc}"
                )

            next_remaining: list[str] = []
            for security in remaining:
                meta = rows[security]
                frame = response.get(security)

                if frame is None or frame.empty:
                    last_errors[security] = (
                        transport_error
                        or "missing_or_empty_history"
                    )
                    next_remaining.append(security)
                    continue

                try:
                    _, diag = _write_security_file(
                        raw_dir,
                        frame=frame,
                        **meta,
                    )
                except Exception as exc:
                    last_errors[security] = (
                        f"{type(exc).__name__}: {exc}"
                    )
                    next_remaining.append(security)
                    continue

                completed[meta["figi"]] = diag
                failures.pop(meta["figi"], None)

            remaining = next_remaining

            _write_json_atomic(
                checkpoint_path,
                {
                    "issue": 119,
                    "updated_utc": (
                        datetime.now(timezone.utc).isoformat()
                    ),
                    "start_date": start_date,
                    "end_date": end_date,
                    "fields": HISTORICAL_FIELDS,
                    "completed": completed,
                    "failures": failures,
                },
            )

            done_in_batch = len(batch) - len(remaining)
            print(
                f"[issue119] batch {batch_no}/{len(batches)} "
                f"completed_this_batch={done_in_batch}/{len(batch)} "
                f"total_completed={len(completed)}",
                flush=True,
            )

            if remaining and attempt < max_attempts:
                wait = float(2 ** (attempt - 1))
                print(
                    f"[issue119] retrying {len(remaining)} securities "
                    f"after {wait:.0f}s",
                    flush=True,
                )
                sleep(wait)

        for security in remaining:
            meta = rows[security]
            failures[meta["figi"]] = last_errors.get(
                security,
                "unknown_download_failure",
            )

        _write_json_atomic(
            checkpoint_path,
            {
                "issue": 119,
                "updated_utc": (
                    datetime.now(timezone.utc).isoformat()
                ),
                "start_date": start_date,
                "end_date": end_date,
                "fields": HISTORICAL_FIELDS,
                "completed": completed,
                "failures": failures,
            },
        )

    universe_path = (
        output_dir / "issue119_bbg_oos2_universe_manifest.csv"
    )
    if not universe_path.exists():
        universe.to_csv(universe_path, index=False)

    manifest = {
        "issue": 119,
        "parent_issue": 78,
        "provider": "Bloomberg Desktop API",
        "retrieved_utc": (
            datetime.now(timezone.utc).isoformat()
        ),
        "requested_start": start_date,
        "requested_end": end_date,
        "fields": list(HISTORICAL_FIELDS),
        "adjustment_policy": {
            "adjustmentSplit": True,
            "adjustmentNormal": False,
            "adjustmentAbnormal": False,
            "adjustmentFollowDPDF": False,
            "description": (
                "split-adjusted; ordinary/abnormal cash-dividend "
                "back-adjustment disabled"
            ),
        },
        "universe_rows": int(len(universe)),
        "universe_sha256": file_sha256(universe_path),
        "normalization": {
            "contract_version": 2,
            "ohlc_range_rule": (
                "If Bloomberg high does not bound open/close, replace high "
                "with max(open, high, close); if low does not bound "
                "open/close, replace low with min(open, low, close). "
                "Every repair is retained in per-security diagnostics."
            ),
            "ohlc_range_repairs_total": int(
                sum(
                    int(diag.get("ohlc_range_repairs", 0))
                    for diag in completed.values()
                )
            ),
            "securities_with_ohlc_range_repairs": int(
                sum(
                    int(diag.get("ohlc_range_repairs", 0)) > 0
                    for diag in completed.values()
                )
            ),
        },
        "completed": completed,
        "failures": failures,
        "downloader_git_head": _git_head(),
        "firewall": [
            (
                "No classifier or R0 / Warning-First policy "
                "economics are executed by this downloader."
            ),
            (
                "No failed security is replaced after "
                "outcome inspection."
            ),
        ],
    }

    manifest_path = (
        output_dir / "issue119_bbg_oos2_raw_manifest.json"
    )
    _write_json_atomic(manifest_path, manifest)

    print(
        f"[issue119] snapshot finished completed={len(completed)} "
        f"failures={len(failures)} manifest={manifest_path}",
        flush=True,
    )

    if failures:
        raise RuntimeError(
            f"Bloomberg snapshot incomplete: "
            f"{len(failures)} securities failed; "
            f"see {manifest_path}"
        )

    return manifest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--universe",
        type=Path,
        required=True,
    )
    ap.add_argument(
        "--output-dir",
        type=Path,
        required=True,
    )
    ap.add_argument(
        "--start-date",
        default=RAW_START,
    )
    ap.add_argument(
        "--end-date",
        default=EVENT_END,
    )
    ap.add_argument(
        "--batch-size",
        type=int,
        default=25,
    )
    ap.add_argument(
        "--max-attempts",
        type=int,
        default=3,
    )
    args = ap.parse_args()

    universe = pd.read_csv(args.universe)
    with BloombergDesktopClient() as client:
        manifest = download_universe(
            client,
            universe,
            args.output_dir,
            start_date=args.start_date,
            end_date=args.end_date,
            batch_size=args.batch_size,
            max_attempts=args.max_attempts,
        )

    print(
        json.dumps(
            {
                "universe_rows": manifest["universe_rows"],
                "completed": len(manifest["completed"]),
                "failures": len(manifest["failures"]),
                "raw_manifest": str(
                    args.output_dir
                    / "issue119_bbg_oos2_raw_manifest.json"
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
