#!/usr/bin/env python3
"""Build and freeze the preregistered Issue #74 outcome-price panel.

This command is intentionally data-only: it downloads SPY/TLT/SHV/GSG, writes
the deterministic committed snapshot, and does not calculate portfolio PnL.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from asset_allocation_phase_a import download_adjusted_close
from issue_74_outcome_snapshot import ASSETS, DATA_DIR, freeze_price_panel

DEFAULT_START = "2007-01-01"
DEFAULT_END_EXCLUSIVE = "2026-08-25"


def build_common_prices(start: str, end: str | None) -> tuple[pd.DataFrame, dict]:
    series = {asset: download_adjusted_close(asset, start, end) for asset in ASSETS}
    prices = pd.concat(series.values(), axis=1, join="inner").dropna(how="any")
    prices.columns = list(ASSETS)
    prices = prices.sort_index()
    if prices.empty or prices.index.duplicated().any():
        raise RuntimeError("Issue #74 outcome panel is empty or has duplicate dates")
    if not np.isfinite(prices.to_numpy(float)).all() or (prices.to_numpy(float) <= 0.0).any():
        raise RuntimeError("Issue #74 outcome panel has invalid prices")
    source = {
        "provider": "Yahoo Finance via yfinance",
        "download_start": start,
        "download_end_exclusive": end,
        "auto_adjust": True,
        "repair": True,
        "common_calendar": list(ASSETS),
        "individual_coverage": {
            asset: {
                "observations": int(len(values)),
                "first_date": values.index.min().date().isoformat(),
                "last_date": values.index.max().date().isoformat(),
            }
            for asset, values in series.items()
        },
    }
    return prices, source


def main() -> int:
    parser = argparse.ArgumentParser(description="Freeze Issue #74 SPY/TLT/SHV/GSG outcome panel")
    parser.add_argument("--start", default=DEFAULT_START)
    parser.add_argument("--end", default=DEFAULT_END_EXCLUSIVE)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    args = parser.parse_args()
    prices, source = build_common_prices(args.start, args.end)
    manifest = freeze_price_panel(prices, data_dir=args.data_dir, source=source)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
