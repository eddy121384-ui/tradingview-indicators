#!/usr/bin/env python3
"""Compare copied full-history Pine Logs against the frozen V6.6 Python mirror."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from compare_tradingview_parity import TV_SOURCES
from v6_6_core import V66Config, compute_v66

MARKER = "MPM_PARITY|"
TARGETS = {
    "tv_plot_gpi": "plot_GPI",
    "tv_plot_ipi": "plot_IPI",
    "tv_plot_fcpi": "plot_FCPI",
}

# The log starts at a user-selected date while the original Pine can see older
# chart history. V6.6 needs 63 lagged bars plus 252 valid momentum observations.
# Add 40 bars for EMA(5) seed differences to decay well below the parity gate.
_CFG = V66Config()
WARMUP_ROWS = _CFG.mid_len + _CFG.z_len_daily + 40


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
            row[key.strip()] = value.strip().strip('"')
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
    if len(frame) <= WARMUP_ROWS:
        raise ValueError(f"need more than {WARMUP_ROWS} unique daily rows for parity evaluation")

    source_columns = list(TV_SOURCES.values())
    py = compute_v66(frame[source_columns])
    frame_eval = frame.iloc[WARMUP_ROWS:]
    py_eval = py.iloc[WARMUP_ROWS:]

    comparisons: dict[str, dict] = {}
    for tv_name, py_name in TARGETS.items():
        tv_values = frame_eval[tv_name].to_numpy(float)
        py_values = py_eval[py_name].to_numpy(float)
        valid = np.isfinite(tv_values) & np.isfinite(py_values)
        if not valid.any():
            comparisons[py_name] = {"comparable_rows": 0}
            continue

        diff = np.abs(tv_values[valid] - py_values[valid])
        valid_indices = np.flatnonzero(valid)
        ranked = valid_indices[np.argsort(np.abs(tv_values[valid_indices] - py_values[valid_indices]))[::-1][:20]]
        comparisons[py_name] = {
            "comparable_rows": int(valid.sum()),
            "max_abs_error": float(diff.max()),
            "mean_abs_error": float(diff.mean()),
            "p99_abs_error": float(np.quantile(diff, 0.99)),
            "worst_20_errors_by_date": {
                frame_eval.index[i].date().isoformat(): float(abs(tv_values[i] - py_values[i]))
                for i in ranked
            },
        }

    counts = [comparisons[name].get("comparable_rows", 0) for name in TARGETS.values()]
    maxima = [comparisons[name].get("max_abs_error", np.inf) for name in TARGETS.values()]
    p99s = [comparisons[name].get("p99_abs_error", np.inf) for name in TARGETS.values()]
    acceptance = {
        "at_least_100_comparable_rows_per_axis": min(counts, default=0) >= 100,
        "all_axes_p99_abs_error_at_most_0_10_points": bool(p99s) and max(p99s) <= 0.10,
        "all_axes_max_abs_error_at_most_0_50_points": bool(maxima) and max(maxima) <= 0.50,
    }
    acceptance["pass"] = all(acceptance.values())
    return {
        "rows": int(len(frame)),
        "first_date": frame.index.min().date().isoformat(),
        "last_date": frame.index.max().date().isoformat(),
        "warmup_rows_excluded": WARMUP_ROWS,
        "evaluation_first_date": frame_eval.index.min().date().isoformat(),
        "evaluation_rows": int(len(frame_eval)),
        "comparisons": comparisons,
        "acceptance": acceptance,
        "notes": [
            "Pine Logs fallback supports raw copied logs and TradingView Pine-Logs CSV exports because the parser searches each line for the MPM_PARITY marker.",
            "The helper's three input.source fields must be set to the frozen V6.6 GPI/IPI/FCPI plotted outputs, not chart close.",
            "The helper logs TradingView source rows and original V6.6 plotted EMA axes; Python then recomputes from those same source rows.",
            "Warmup rows are excluded because the truncated log does not contain the original Pine script's pre-start history; the exclusion is derived mechanically from the 63-bar lag, 252-observation momentum Z-score, and EMA(5) seed decay.",
            "This is an engineering parity gate, not an economic-performance gate.",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare Macro Pressure V6.6 Pine Logs history")
    parser.add_argument("--input", type=Path, required=True, help="Raw Pine Logs text or exported Pine-Logs CSV")
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = compare_log_text(args.input.read_text(encoding="utf-8-sig"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report["acceptance"], indent=2))
    return 0 if report["acceptance"]["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
