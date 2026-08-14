#!/usr/bin/env python3
"""Build a reproducible public-data V6.6 history bundle for Issue #59.

This is the Stage-1 research data path. Its output is not parity evidence:
public Yahoo/FRED feeds can differ from TradingView and must be checked in
Stage 2 before any economic conclusions are drawn.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

import pandas as pd

from public_data import build_public_sources, write_bundle
from v6_6_core import V66Config, compute_v66


HISTORY_COLUMNS = [
    "GPI", "IPI", "FCPI",
    "plot_GPI", "plot_IPI", "plot_FCPI",
    "gpi_state", "ipi_state", "fcpi_state",
    "core_regime", "risk_note", "risk_posture",
    "gpi_market", "ipi_market", "fcpi_market",
    "CreditStress", "RatesDollarConstraint", "VolatilityShock",
]


def build_history(sources: pd.DataFrame, cfg: V66Config) -> pd.DataFrame:
    result = compute_v66(sources, cfg)
    missing = [column for column in HISTORY_COLUMNS if column not in result]
    if missing:
        raise RuntimeError(f"V6.6 mirror missing expected history columns: {missing}")
    return sources.join(result[HISTORY_COLUMNS])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Macro Pressure Map V6.6 public research history")
    parser.add_argument("--start", default="2007-01-01")
    parser.add_argument("--end", default=None, help="Exclusive end date, YYYY-MM-DD")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--include-t5yie", action="store_true")
    parser.add_argument("--include-industrial-metals", action="store_true")
    parser.add_argument("--include-kre", action="store_true")
    parser.add_argument("--include-official-fci", action="store_true")
    parser.add_argument("--include-macro", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sources, manifest = build_public_sources(
        start=args.start,
        end=args.end,
        include_t5yie=args.include_t5yie,
        include_industrial_metals=args.include_industrial_metals,
        include_kre=args.include_kre,
        include_official_fci=args.include_official_fci,
        include_macro=args.include_macro,
    )
    cfg = V66Config(
        use_t5yie=args.include_t5yie,
        use_industrial_metals_in_ipi=args.include_industrial_metals,
        use_kre_stress_addon=args.include_kre,
        use_official_fci=args.include_official_fci,
        use_macro_data=args.include_macro,
    )
    history = build_history(sources, cfg)

    axes = history[["GPI", "IPI", "FCPI"]]
    complete = axes.notna().all(axis=1)
    first_complete = history.index[int(complete.to_numpy().argmax())] if complete.any() else None
    manifest["v66_config"] = asdict(cfg)
    manifest["history_columns"] = HISTORY_COLUMNS
    manifest["first_all_axes_finite_date"] = first_complete.date().isoformat() if first_complete is not None else None
    manifest["all_axes_finite_rows"] = int(complete.sum())
    manifest["interpretation_guardrail"] = (
        "This bundle is a public-feed research approximation only. Do not run event-study or regime utility claims "
        "until Stage-2 Pine parity is sufficiently established or its limitations are explicitly bounded."
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_bundle(
        sources,
        manifest,
        args.output_dir / "v6.6-public-sources.csv",
        args.output_dir / "v6.6-public-manifest.json",
    )
    history.reset_index().to_csv(
        args.output_dir / "v6.6-public-history.csv", index=False, date_format="%Y-%m-%d"
    )
    print(json.dumps({
        "rows": len(history),
        "first_date": history.index.min().date().isoformat() if len(history) else None,
        "last_date": history.index.max().date().isoformat() if len(history) else None,
        "first_all_axes_finite_date": manifest["first_all_axes_finite_date"],
        "all_axes_finite_rows": manifest["all_axes_finite_rows"],
        "output_dir": str(args.output_dir),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
