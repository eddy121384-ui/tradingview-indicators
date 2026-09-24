#!/usr/bin/env python3
"""Parse copied TradingView Pine Logs for Issue #109 A2 into a canonical CSV.

The parser accepts arbitrary surrounding UI text and extracts only lines containing
the MPM_A2 payload prefix.
"""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

FIELDS = (
    "date",
    "raw_gpi",
    "raw_ipi",
    "gpi_fast20",
    "gpi_mid63",
    "gpi_acc",
    "ipi_fast20",
    "ipi_mid63",
    "ipi_acc",
    "regime_id",
)

PATTERN = re.compile(
    r"MPM_A2"
    r"\|date=(?P<date>\d{4}-\d{1,2}-\d{1,2})"
    r"\|raw_gpi=(?P<raw_gpi>[^|\s]+)"
    r"\|raw_ipi=(?P<raw_ipi>[^|\s]+)"
    r"\|gpi_fast20=(?P<gpi_fast20>[^|\s]+)"
    r"\|gpi_mid63=(?P<gpi_mid63>[^|\s]+)"
    r"\|gpi_acc=(?P<gpi_acc>[^|\s]+)"
    r"\|ipi_fast20=(?P<ipi_fast20>[^|\s]+)"
    r"\|ipi_mid63=(?P<ipi_mid63>[^|\s]+)"
    r"\|ipi_acc=(?P<ipi_acc>[^|\s]+)"
    r"\|regime_id=(?P<regime_id>[^|\s]+)"
)


def normalize_value(value: str) -> str:
    v = value.strip()
    if v.lower() in {"na", "nan", "n/a"}:
        return ""
    return v


def parse(text: str) -> list[dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for match in PATTERN.finditer(text):
        row = {k: normalize_value(v) for k, v in match.groupdict().items()}
        rows[row["date"]] = row
    return [rows[k] for k in sorted(rows)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path, help="Copied Pine Logs text file")
    ap.add_argument("output", type=Path, help="Canonical CSV output")
    args = ap.parse_args()

    text = args.input.read_text(encoding="utf-8", errors="replace")
    rows = parse(text)
    if not rows:
        raise SystemExit("No MPM_A2 payloads found in copied Pine Logs")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    print({
        "rows": len(rows),
        "first_date": rows[0]["date"],
        "last_date": rows[-1]["date"],
        "output": str(args.output),
    })


if __name__ == "__main__":
    main()
