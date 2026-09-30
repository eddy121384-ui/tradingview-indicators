#!/usr/bin/env python3
"""Parse Issue #78 Pine Logs parity capture into the comparator CSV schema."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from generate_issue78_python_parity_log_pine import FIELDS, MARKER

BASE_COLUMNS = ["ticker", "tf", "time", "open", "high", "low", "close", "volume"]
LOG_COLUMNS = BASE_COLUMNS + [name for name, _ in FIELDS]

PARITY_RENAME = {
    "formalId": "PARITY formalId",
    "symATR": "PARITY symATR",
    "volumeQuality": "PARITY volumeQuality",
    "volumeWeight": "PARITY volumeWeight",
    "volumeAbsorption": "PARITY volumeAbsorption",
    "volumeDistribution": "PARITY volumeDistribution",
    "volumeBreakout": "PARITY volumeBreakout",
    "volumeBreakdown": "PARITY volumeBreakdown",
    "accGate": "PARITY accGate",
    "markupGate": "PARITY markupGate",
    "reaccGate": "PARITY reaccGate",
    "distGate": "PARITY distGate",
    "markdownGate": "PARITY markdownGate",
    "redistGate": "PARITY redistGate",
    "probAcc": "PARITY probAcc",
    "probMarkup": "PARITY probMarkup",
    "probReacc": "PARITY probReacc",
    "probDist": "PARITY probDist",
    "probMarkdown": "PARITY probMarkdown",
    "probRedist": "PARITY probRedist",
    "topId": "PARITY topId",
    "topGap": "PARITY topGap",
    "evidence": "PARITY evidence",
    "candidateDisplayId": "PARITY candidateDisplayId",
    "stalePressureBars": "PARITY stalePressureBars",
    "stalePressureReason": "PARITY stalePressureReason",
    "useYieldLevel": "PARITY useYieldLevel",
}


def parse_text(text: str) -> pd.DataFrame:
    rows: list[list[str]] = []
    expected = 1 + len(LOG_COLUMNS)
    needle = MARKER + "|"

    for raw_line in text.splitlines():
        pos = raw_line.find(needle)
        if pos < 0:
            continue
        payload = raw_line[pos:].strip().strip('"')
        parts = payload.split("|")
        if len(parts) != expected:
            raise ValueError(
                f"{MARKER} record has {len(parts)} fields; expected {expected}: {payload[:220]}"
            )
        rows.append(parts[1:])

    if not rows:
        raise ValueError(f"no {MARKER} records found in Pine Logs")

    frame = pd.DataFrame(rows, columns=LOG_COLUMNS)
    for col in LOG_COLUMNS:
        if col in ("ticker", "tf"):
            continue
        frame[col] = pd.to_numeric(frame[col].replace("na", pd.NA), errors="coerce")

    frame = (
        frame.drop_duplicates(subset=["ticker", "tf", "time"], keep="last")
        .sort_values(["ticker", "tf", "time"])
        .reset_index(drop=True)
    )
    return frame.rename(columns=PARITY_RENAME)


def main() -> None:
    ap = argparse.ArgumentParser(description="Parse Issue #78 Pine Logs parity capture")
    ap.add_argument("input", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    frame = parse_text(args.input.read_text(encoding="utf-8", errors="replace"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output, index=False)
    print(f"parsed {len(frame)} {MARKER} bars -> {args.output}")


if __name__ == "__main__":
    main()
