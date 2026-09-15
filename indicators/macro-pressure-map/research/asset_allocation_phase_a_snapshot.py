#!/usr/bin/env python3
"""Issue #64 Phase A entrypoint with durable outcome snapshot capture/use."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import asset_allocation_phase_a as phase_a_live
import asset_allocation_phase_a_frozen as phase_a_frozen
from issue_64_outcome_snapshot import (
    committed_snapshot_available,
    load_frozen_prices,
    write_price_snapshot,
)


def resolve_exact_prices(start: str, end: str | None, output_dir: Path):
    if committed_snapshot_available():
        prices, manifest = load_frozen_prices(start, end)
        acquisition_mode = "committed_frozen_snapshot"
    else:
        prices, manifest = phase_a_live.build_outcome_prices(start, end)
        acquisition_mode = "bootstrap_live_yahoo_for_freeze"

    artifact_manifest = write_price_snapshot(
        prices,
        output_dir / "phase-a-outcome-prices.csv",
        output_dir / "phase-a-outcome-prices-manifest.json",
        source={
            "acquisition_mode": acquisition_mode,
            "runtime_manifest": manifest,
        },
    )
    runtime_manifest = dict(manifest)
    runtime_manifest.update({
        "durable_snapshot_acquisition_mode": acquisition_mode,
        "generated_snapshot_sha256": artifact_manifest["csv_sha256"],
        "generated_snapshot_rows": artifact_manifest["rows"],
        "generated_snapshot_first_date": artifact_manifest["first_date"],
        "generated_snapshot_last_date": artifact_manifest["last_date"],
    })
    return prices, runtime_manifest


def run(start: str, end: str | None, output_dir: Path) -> dict:
    prices, manifest = resolve_exact_prices(start, end, output_dir)

    def exact_panel(_start: str, _end: str | None):
        if _start != start or _end != end:
            raise ValueError("snapshot wrapper called with an unexpected date range")
        return prices.copy(), dict(manifest)

    phase_a_frozen.build_outcome_prices = exact_panel
    return phase_a_frozen.run_phase_a_frozen(start, end, output_dir)


def main() -> int:
    parser = argparse.ArgumentParser(description="Issue #64 Phase A with durable outcome snapshot")
    parser.add_argument("--start", default="2007-01-01")
    parser.add_argument("--end", default=None)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.start, args.end, args.output_dir)
    print(json.dumps({
        "phase": result["phase"],
        "rows": result["common_finite_regime_rows"],
        "outcome_mode": result["outcome_data"].get("durable_snapshot_acquisition_mode"),
        "snapshot_sha256": result["outcome_data"].get("generated_snapshot_sha256"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
