#!/usr/bin/env python3
"""Compare frozen V6.6 TradingView output with the Python mirror on TV inputs.

Expected CSV: TradingView chart-data export from an SPY 1D chart with both the
frozen Macro Pressure Map V6.6 and the Issue #59 parity-source helper attached.
The helper exposes TradingView's own source rows; Python therefore consumes the
same vendor inputs for implementation-parity testing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

import numpy as np
import pandas as pd

from v6_6_core import compute_v66


TV_SOURCES = {
    "PARITY SRC spy": "spy",
    "PARITY SRC iwm": "iwm",
    "PARITY SRC rsp": "rsp",
    "PARITY SRC xly": "xly",
    "PARITY SRC xlp": "xlp",
    "PARITY SRC xli": "xli",
    "PARITY SRC xlu": "xlu",
    "PARITY SRC copper": "copper",
    "PARITY SRC gold": "gold",
    "PARITY SRC breakeven_10y": "breakeven_10y",
    "PARITY SRC oil": "oil",
    "PARITY SRC gasoline": "gasoline",
    "PARITY SRC commodity_basket": "commodity_basket",
    "PARITY SRC dxy": "dxy",
    "PARITY SRC vix": "vix",
    "PARITY SRC move": "move",
    "PARITY SRC hyg": "hyg",
    "PARITY SRC ief": "ief",
    "PARITY SRC hy_oas": "hy_oas",
    "PARITY SRC real_yield": "real_yield",
}

TV_OUTPUTS = {
    "GPI - Growth Pressure": "plot_GPI",
    "IPI - Inflation Pressure": "plot_IPI",
    "FCPI - Financial Conditions Pressure": "plot_FCPI",
}


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(name).lower()).strip()


def find_column(columns, wanted: str) -> str:
    wanted_norm = _norm(wanted)
    exact = [column for column in columns if _norm(column) == wanted_norm]
    if len(exact) == 1:
        return exact[0]
    suffix = [column for column in columns if _norm(column).endswith(wanted_norm)]
    if len(suffix) == 1:
        return suffix[0]
    contains = [column for column in columns if wanted_norm in _norm(column)]
    if len(contains) == 1:
        return contains[0]
    raise ValueError(f"could not uniquely locate column {wanted!r}; matches={contains or suffix or exact}")


def load_tv_csv(path: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, str]]:
    raw = pd.read_csv(path)
    columns = list(raw.columns)
    mapping: dict[str, str] = {}

    date_column = None
    for candidate in ("time", "date", "datetime"):
        try:
            date_column = find_column(columns, candidate)
            break
        except ValueError:
            pass

    if date_column is not None:
        index = pd.to_datetime(raw[date_column], errors="raise", utc=True).dt.tz_convert(None).dt.normalize()
        mapping["date"] = date_column
    else:
        index = pd.RangeIndex(len(raw))

    sources = pd.DataFrame(index=index)
    targets = pd.DataFrame(index=index)
    for tv_name, canonical in TV_SOURCES.items():
        column = find_column(columns, tv_name)
        mapping[tv_name] = column
        sources[canonical] = pd.to_numeric(raw[column], errors="coerce").to_numpy(float)
    for tv_name, py_name in TV_OUTPUTS.items():
        column = find_column(columns, tv_name)
        mapping[tv_name] = column
        targets[py_name] = pd.to_numeric(raw[column], errors="coerce").to_numpy(float)
    return sources, targets, mapping


def compare(path: Path) -> dict:
    sources, tv_targets, mapping = load_tv_csv(path)
    py = compute_v66(sources)

    comparisons: dict[str, dict] = {}
    common_mask = np.ones(len(py), dtype=bool)
    for py_name in TV_OUTPUTS.values():
        tv_values = tv_targets[py_name].to_numpy(float)
        py_values = pd.to_numeric(py[py_name], errors="coerce").to_numpy(float)
        valid = np.isfinite(tv_values) & np.isfinite(py_values)
        common_mask &= valid
        count = int(valid.sum())
        if count == 0:
            comparisons[py_name] = {"comparable_rows": 0}
            continue
        diff = np.abs(tv_values[valid] - py_values[valid])
        comparisons[py_name] = {
            "comparable_rows": count,
            "max_abs_error": float(diff.max()),
            "mean_abs_error": float(diff.mean()),
            "p99_abs_error": float(np.quantile(diff, 0.99)),
        }

    common_indices = np.flatnonzero(common_mask)
    p99 = [comparisons[name].get("p99_abs_error", np.inf) for name in TV_OUTPUTS.values()]
    maxima = [comparisons[name].get("max_abs_error", np.inf) for name in TV_OUTPUTS.values()]
    counts = [comparisons[name].get("comparable_rows", 0) for name in TV_OUTPUTS.values()]

    acceptance = {
        "at_least_100_comparable_rows_per_axis": min(counts, default=0) >= 100,
        "all_axes_p99_abs_error_at_most_0_10_points": bool(p99) and max(p99) <= 0.10,
        "all_axes_max_abs_error_at_most_0_50_points": bool(maxima) and max(maxima) <= 0.50,
    }
    acceptance["pass"] = all(acceptance.values())

    return {
        "source_csv": str(path),
        "rows": int(len(py)),
        "first_all_axes_comparable_row_index": int(common_indices[0]) if len(common_indices) else None,
        "last_all_axes_comparable_row_index": int(common_indices[-1]) if len(common_indices) else None,
        "column_mapping": mapping,
        "comparisons": comparisons,
        "acceptance": acceptance,
        "notes": [
            "This is an engineering parity gate, not an economic-performance gate.",
            "Python consumes TradingView-exported source rows, so public Yahoo/FRED feed mismatch is excluded from this test.",
            "The compared TradingView outputs are V6.6 plotted EMA axes; V6.6 dashboard states use unsmoothed axes.",
            "If this gate fails, fix implementation semantics before public-feed history diagnostics or event studies.",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare TradingView Macro Pressure V6.6 export to Python mirror")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = compare(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report["acceptance"], indent=2))
    return 0 if report["acceptance"]["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
