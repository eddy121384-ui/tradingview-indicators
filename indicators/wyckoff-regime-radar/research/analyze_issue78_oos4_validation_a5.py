#!/usr/bin/env python3
"""Issue #78 A5: untouched OOS4 validation of frozen causal Core-2.

First OOS4 contact for outcomes. All Core-2 definitions reused from the
frozen A4 module by import (causal ranks, masks, cells, aggregation,
paired specs) — nothing redefined, no thresholds/weights changed.

Only this module's own cohort gate differs: it requires the frozen OOS4
300-FIGI set and asserts zero overlap with the OOS2/OOS3 cohorts.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

import analyze_issue78_factorized_classifier_discovery as a0
import analyze_issue78_direction_decomposition_a1 as a1
import analyze_issue78_supply_demand_a2 as a2
import analyze_issue78_causal_core2_a4 as a4
from audit_issue119_bbg_oos2_snapshot import audit_snapshot
from smoke_issue119_frozen_classifier import FROZEN_CLASSIFIER_BLOB, load_classifier

EXPECTED_OOS4_FIGI_SET_SHA = (
    "b0c9423a6e3e5cbd61dcd17dc1a9c5a0fc50b8bc00286ba3a5b86f560209ca49"
)
HORIZONS = a0.HORIZONS
MIN_CELL_BARS = a0.MIN_CELL_BARS
MIN_AGG_STOCKS = a0.MIN_AGG_STOCKS

# Frozen A4 cell machinery reused verbatim.
econ_cells = a4.econ_cells
fidelity_rows = a4.fidelity_rows
fidelity_summary = a4.fidelity_summary
aggregate_a1_cells = a1.aggregate_a1_cells
paired_deltas = a1.paired_deltas
PAIRED_SPECS = a4.PAIRED_SPECS


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--universe", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--raw-dir", type=Path, required=True)
    ap.add_argument(
        "--classifier",
        type=Path,
        default=Path("generated/wyckoff-issue78-rc-python.py"),
    )
    ap.add_argument("--oos2-universe", type=Path, required=True)
    ap.add_argument("--oos3-universe", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    for contact in (args.universe, args.manifest, args.raw_dir):
        assert "oos4" in str(contact).lower() or "snapshot" in str(
            contact
        ).lower(), "unexpected OOS4 path"

    audit = audit_snapshot(args.universe, args.manifest, args.raw_dir)
    if not audit["pass"]:
        raise SystemExit("snapshot audit failed")

    universe = pd.read_csv(args.universe)
    if len(universe) != 300 or universe["figi"].nunique() != 300:
        raise AssertionError("universe membership drift")
    cohort_sha = a0.figi_set_sha(universe)
    if cohort_sha != EXPECTED_OOS4_FIGI_SET_SHA:
        raise AssertionError(f"OOS4 FIGI-set drift: {cohort_sha}")

    oos2 = set(
        pd.read_csv(args.oos2_universe)["figi"].astype(str).tolist()
    )
    oos3 = set(
        pd.read_csv(args.oos3_universe)["figi"].astype(str).tolist()
    )
    mine = set(universe["figi"].astype(str).tolist())
    if mine & oos2:
        raise AssertionError("OOS4 overlaps OOS2")
    if mine & oos3:
        raise AssertionError("OOS4 overlaps OOS3")

    classifier, blob = load_classifier(args.classifier)
    if blob != FROZEN_CLASSIFIER_BLOB:
        raise AssertionError("frozen classifier blob drift")

    coverage = []
    econ_rows = []
    fid_rows = []

    for i, meta_row in enumerate(universe.itertuples(index=False), start=1):
        figi = str(meta_row.figi)
        raw_path = args.raw_dir / f"{figi}.csv.gz"
        if not raw_path.exists():
            raise FileNotFoundError(raw_path)
        raw = pd.read_csv(raw_path)
        frame = a4.add_causal_ranks(
            a2.add_within_stock_ranks(a2.build_sd_frame(raw, classifier))
        )
        meta = {
            "sector": str(meta_row.sector),
            "sleeve": str(meta_row.sleeve),
        }
        coverage.append(
            {
                "figi": figi,
                "ticker": str(meta_row.ticker),
                **meta,
                "raw_rows": int(len(frame)),
                "eligible_rows": int(frame["eligible"].sum()),
                "causal_ready_rows": int(frame["causal_ready"].sum()),
            }
        )
        econ_rows.extend(econ_cells(figi, frame, meta))
        fid_rows.extend(fidelity_rows(figi, frame, meta))
        print(
            f"[oos4-validation-a5] "
            f"{i}/{len(universe)} {meta_row.ticker} "
            f"eligible={int(frame['eligible'].sum())} "
            f"causal_ready={int(frame['causal_ready'].sum())}",
            flush=True,
        )

    econ_stock = pd.DataFrame(econ_rows)
    econ_summary = aggregate_a1_cells(
        econ_stock, ["test", "state", "block", "horizon"]
    )
    bear_stock = econ_stock[
        econ_stock["state"].str.startswith("bear")
    ].assign(test=lambda d: d["test"] + "_bear")
    pair_stock, pair_summary = paired_deltas(
        pd.concat([econ_stock, bear_stock], ignore_index=True),
        PAIRED_SPECS,
    )
    fid_stock = pd.DataFrame(fid_rows)
    fid_summary = fidelity_summary(fid_stock)

    summary = {
        "integrity": {
            "issue": 78,
            "study": "Causal Core-2 OOS4 Validation A5",
            "role": (
                "untouched-cohort architecture validation; "
                "not a strategy claim"
            ),
            "classifier_blob": blob,
            "figi_set_sha256": cohort_sha,
            "stocks": int(len(universe)),
            "raw_files": int(audit["completed"]),
            "raw_failures": int(audit["failures"]),
            "horizons": list(HORIZONS),
            "blocks": list(a1.BLOCK_LABELS),
            "min_cell_bars": MIN_CELL_BARS,
            "min_aggregate_stocks": MIN_AGG_STOCKS,
            "oos4_touched": True,
            "oos2_overlap": 0,
            "oos3_overlap": 0,
        },
        "frozen_design": {
            "translation": "A4 verbatim (reused by import)",
            "primary": "h10 hard 80/20",
            "robustness": "70/30",
        },
        "notes": [
            "First OOS4 outcome contact under A5 preregistration.",
            "No thresholds, weights, or formulas changed for OOS4.",
        ],
    }

    args.out.mkdir(parents=True, exist_ok=True)
    for name, df in (
        ("coverage.csv", pd.DataFrame(coverage)),
        ("econ_per_stock.csv", econ_stock),
        ("econ_summary.csv", econ_summary),
        ("paired_delta_per_stock.csv", pair_stock),
        ("paired_delta_summary.csv", pair_summary),
        ("fidelity_per_stock.csv", fid_stock),
        ("fidelity_summary.csv", fid_summary),
    ):
        df.to_csv(args.out / name, index=False)
    (args.out / "summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
