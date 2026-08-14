#!/usr/bin/env python3
"""Compare copied Pine Logs checkpoints against the frozen V6.6 Python mirror."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from compare_tradingview_parity import TV_SOURCES
from v6_6_core import compute_v66

MARKER = "MPM_PARITY|"
TARGETS = {
    "tv_plot_gpi": "plot_GPI",
    "tv_plot_ipi": "plot_IPI",
    "tv_plot_fcpi": "plot_FCPI",
}


def parse_log_text(text: str) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    for raw_line in text.splitlines():
        pos = raw_line.find(MARKER)
        if pos < 0:
            continue
        payload = raw_line[pos + len(MARKER):]
        row: dict[str, str] = {}
        for token in payload.split("|"):
            if "=" not in token:
                continue
            key, value = token.split("=", 1)
            row[key.strip()] = value.strip()
        if row:
            rows.append(row)
    if not rows:
        raise ValueError("no MPM_PARITY log lines found")

    required = {"date", *TV_SOURCES.values(), *TARGETS.keys()}
    present = set().union(*(row.keys() for row in rows))
    missing = sorted(required - present)
    if missing:
        raise ValueError(f"parity logs are missing required fields: {missing}")

    frame = pd.DataFrame(rows)
    frame["date"] = pd.to_datetime(frame["date"], errors="raise")
    for column in required - {"date"}:
        frame[column] = pd.to_numeric(frame[column].replace({"NaN": np.nan, "na": np.nan}), errors="coerce")
    return frame.sort_values("date").drop_duplicates("date", keep="last").set_index("date")


def compare_log_text(text: str) -> dict:
    frame = parse_log_text(text)
    source_columns = list(TV_SOURCES.values())
    py = compute_v66(frame[source_columns])

    comparisons: dict[str, dict] = {}
    for tv_name, py_name in TARGETS.items():
        tv_values = frame[tv_name].to_numpy(float)
        py_values = py[py_name].to_numpy(float)
        valid = np.isfinite(tv_values) & np.isfinite(py_values)
        if not valid.any():
            comparisons[py_name] = {"comparable_checkpoints": 0}
            continue
        diff = np.abs(tv_values[valid] - py_values[valid])
        comparisons[py_name] = {
            "comparable_checkpoints": int(valid.sum()),
            "max_abs_error": float(diff.max()),
            "mean_abs_error": float(diff.mean()),
            "errors_by_date": {
                frame.index[i].date().isoformat(): float(abs(tv_values[i] - py_values[i]))
                for i in np.flatnonzero(valid)
            },
        }

    counts = [comparisons[name].get("comparable_checkpoints", 0) for name in TARGETS.values()]
    maxima = [comparisons[name].get("max_abs_error", np.inf) for name in TARGETS.values()]
    acceptance = {
        "at_least_8_comparable_checkpoints_per_axis": min(counts, default=0) >= 8,
        "all_axes_max_abs_error_at_most_0_50_points": bool(maxima) and max(maxima) <= 0.50,
    }
    acceptance["pass"] = all(acceptance.values())
    return {
        "checkpoints": int(len(frame)),
        "dates": [value.date().isoformat() for value in frame.index],
        "comparisons": comparisons,
        "acceptance": acceptance,
        "notes": [
            "Pine Logs fallback is intended for accounts/environments where chart-data CSV export is unavailable.",
            "The helper's three input.source fields must be set to the frozen V6.6 GPI/IPI/FCPI plotted outputs, not chart close.",
            "The helper logs TradingView source rows and original V6.6 plotted EMA axes; Python then recomputes from those same source rows.",
            "This is an engineering parity gate, not an economic-performance gate.",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare Macro Pressure V6.6 Pine Logs checkpoints")
    parser.add_argument("--input", type=Path, required=True, help="Text copied from TradingView Pine Logs")
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = compare_log_text(args.input.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report["acceptance"], indent=2))
    return 0 if report["acceptance"]["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
