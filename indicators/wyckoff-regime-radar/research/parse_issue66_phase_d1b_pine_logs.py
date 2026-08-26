#!/usr/bin/env python3
"""Parse Issue #66 D-1B Pine Logs into the D-1 comparator CSV schema."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from generate_issue66_phase_d1b_log_capture_pine import FIELDS


COLUMNS = ["time", "open", "high", "low", "close"] + [f"PARITY {name}" for name, _ in FIELDS]


def parse_text(text: str) -> pd.DataFrame:
    rows: list[list[str]] = []
    expected = 1 + len(COLUMNS)  # D1B marker + values
    for raw_line in text.splitlines():
        pos = raw_line.find("D1B|")
        if pos < 0:
            continue
        payload = raw_line[pos:].strip()
        parts = payload.split("|")
        if len(parts) != expected:
            raise ValueError(f"D1B record has {len(parts)} fields; expected {expected}: {payload[:160]}")
        rows.append(parts[1:])
    if not rows:
        raise ValueError("no D1B records found in Pine Logs text")

    frame = pd.DataFrame(rows, columns=COLUMNS)
    for column in COLUMNS:
        frame[column] = pd.to_numeric(frame[column].replace("na", pd.NA), errors="coerce")
    frame = frame.drop_duplicates(subset=["time"], keep="last").sort_values("time").reset_index(drop=True)
    return frame


def main() -> None:
    ap = argparse.ArgumentParser(description="Parse Issue #66 D-1B Pine Logs")
    ap.add_argument("input", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    frame = parse_text(args.input.read_text(encoding="utf-8", errors="replace"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output, index=False)
    print(f"parsed {len(frame)} D1B bars -> {args.output}")


if __name__ == "__main__":
    main()
