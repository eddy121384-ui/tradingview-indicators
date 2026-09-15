#!/usr/bin/env python3
"""Reproduce the Issue #64 raw-axis cross-check from the operator-local Pine log.

The source log is intentionally not committed. Given the exact hash-frozen log,
this script independently computes V6.6 from the logged source inputs and
compares those raw axes with the axes recovered by inverting the plotted EMA(5).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from build_issue_64_frozen_regimes import derive_daily_regimes, parse_message
from v6_6_core import compute_v66

MAX_ALLOWED_ABS_DIFF = 5e-8


def source_inputs_from_log(log_path: Path) -> pd.DataFrame:
    source = pd.read_csv(log_path)
    if "訊息" not in source.columns:
        raise ValueError("Pine log is missing the 訊息 column")
    parsed = pd.DataFrame([parse_message(message) for message in source["訊息"]])
    parsed["date"] = pd.to_datetime(parsed["date"], errors="raise").dt.normalize()
    parsed = parsed.sort_values("date").drop_duplicates("date", keep="last").set_index("date")
    drop = [column for column in ("tv_plot_gpi", "tv_plot_ipi", "tv_plot_fcpi") if column in parsed]
    frame = parsed.drop(columns=drop)
    for column in frame.columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce").astype(float)
    return frame


def verify(log_path: Path) -> dict:
    recovered = derive_daily_regimes(log_path)[["GPI", "IPI", "FCPI"]]
    mirror = compute_v66(source_inputs_from_log(log_path))[["GPI", "IPI", "FCPI"]]
    joined = recovered.add_suffix("_recovered").join(mirror.add_suffix("_mirror"), how="inner")
    required = []
    for axis in ("GPI", "IPI", "FCPI"):
        required.extend([f"{axis}_recovered", f"{axis}_mirror"])
    joined = joined.dropna(subset=required)
    if joined.empty:
        raise RuntimeError("no finite overlapping raw-axis rows after V6.6 warm-up")

    axes: dict[str, dict] = {}
    for axis in ("GPI", "IPI", "FCPI"):
        diff = (joined[f"{axis}_recovered"] - joined[f"{axis}_mirror"]).abs()
        max_date = diff.idxmax()
        max_diff = float(diff.loc[max_date])
        axes[axis] = {
            "max_abs_difference": max_diff,
            "max_difference_date": max_date.date().isoformat(),
            "recovered_value": float(joined.loc[max_date, f"{axis}_recovered"]),
            "mirror_value": float(joined.loc[max_date, f"{axis}_mirror"]),
            "within_tolerance": bool(max_diff <= MAX_ALLOWED_ABS_DIFF),
        }

    result = {
        "first_finite_overlap": joined.index.min().date().isoformat(),
        "last_finite_overlap": joined.index.max().date().isoformat(),
        "finite_overlap_rows": int(len(joined)),
        "max_allowed_abs_difference": MAX_ALLOWED_ABS_DIFF,
        "axes": axes,
        "all_within_tolerance": all(item["within_tolerance"] for item in axes.values()),
    }
    if not result["all_within_tolerance"]:
        raise AssertionError(json.dumps(result, indent=2))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Issue #64 raw-axis reconstruction")
    parser.add_argument("--pine-log", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.pine_log), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
