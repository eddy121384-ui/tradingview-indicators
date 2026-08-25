#!/usr/bin/env python3
"""Issue #64 Phase B entrypoint pinned to the exact Phase A/frozen outcome panel."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import asset_allocation_phase_b as phase_b
from issue_64_outcome_snapshot import (
    HERE,
    committed_snapshot_available,
    load_frozen_prices,
    write_price_snapshot,
)

PHASE_A_BOOTSTRAP_CSV = HERE / "generated" / "issue-64-phase-a" / "phase-a-outcome-prices.csv"
PHASE_A_BOOTSTRAP_MANIFEST = HERE / "generated" / "issue-64-phase-a" / "phase-a-outcome-prices-manifest.json"


def resolve_exact_prices(start: str):
    end = phase_b.DEFAULT_PRICE_END_EXCLUSIVE
    if committed_snapshot_available():
        prices, manifest = load_frozen_prices(start, end)
        acquisition_mode = "committed_frozen_snapshot"
    else:
        if not PHASE_A_BOOTSTRAP_CSV.exists() or not PHASE_A_BOOTSTRAP_MANIFEST.exists():
            raise FileNotFoundError(
                "Phase B bootstrap requires the Phase A snapshot artifact from the same workflow run"
            )
        prices, manifest = load_frozen_prices(
            start,
            end,
            snapshot_path=PHASE_A_BOOTSTRAP_CSV,
            manifest_path=PHASE_A_BOOTSTRAP_MANIFEST,
        )
        acquisition_mode = "same_run_phase_a_snapshot"
    runtime_manifest = dict(manifest)
    runtime_manifest["durable_snapshot_acquisition_mode"] = acquisition_mode
    return prices, runtime_manifest


def run(start: str, output_dir: Path) -> dict:
    prices, manifest = resolve_exact_prices(start)
    snapshot_meta = write_price_snapshot(
        prices,
        output_dir / "phase-b-outcome-prices.csv",
        output_dir / "phase-b-outcome-prices-manifest.json",
        source={
            "acquisition_mode": manifest["durable_snapshot_acquisition_mode"],
            "runtime_manifest": manifest,
        },
    )
    manifest.update({
        "generated_snapshot_sha256": snapshot_meta["csv_sha256"],
        "generated_snapshot_rows": snapshot_meta["rows"],
        "generated_snapshot_first_date": snapshot_meta["first_date"],
        "generated_snapshot_last_date": snapshot_meta["last_date"],
    })

    def exact_panel(_start: str, _end: str | None):
        if _start != start or _end != phase_b.DEFAULT_PRICE_END_EXCLUSIVE:
            raise ValueError("Phase B snapshot wrapper called with an unexpected date range")
        return prices.copy(), dict(manifest)

    phase_b.build_outcome_prices = exact_panel
    return phase_b.run_phase_b(start, output_dir)


def main() -> int:
    parser = argparse.ArgumentParser(description="Issue #64 Phase B with durable outcome snapshot")
    parser.add_argument("--start", default="2007-01-01")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.start, args.output_dir)
    print(json.dumps({
        "phase": result["phase"],
        "rows": result["evaluation_rows"],
        "outcome_mode": result["price_data"].get("durable_snapshot_acquisition_mode"),
        "snapshot_sha256": result["price_data"].get("generated_snapshot_sha256"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
