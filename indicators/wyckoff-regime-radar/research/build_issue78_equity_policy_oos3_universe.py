#!/usr/bin/env python3
"""Build the untouched Issue #78 proof-policy OOS3 300-stock universe.

Uses the frozen Issue #119 candidate snapshot and excludes every security from
the first Issue #119 / OOS2 300-stock cohort before deterministic sampling.
No price history, classifier, or strategy economics are read by this script.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from issue119_bbg_common import (
    CALIBRATION_TICKERS,
    TARGET_BY_SLEEVE,
    canonical_ticker,
    deterministic_stratified_sample,
    file_sha256,
)

OOS3_SEED = "issue78-equity-proof-policy-oos3-v1"


def build_oos3(
    candidates: pd.DataFrame,
    prior_universe: pd.DataFrame,
    *,
    seed: str = OOS3_SEED,
) -> tuple[pd.DataFrame, dict]:
    required_prior = {"figi", "ticker"}
    missing = required_prior.difference(prior_universe.columns)
    if missing:
        raise ValueError(
            f"prior universe missing columns: {sorted(missing)}"
        )

    prior_figi = {
        str(x).strip()
        for x in prior_universe["figi"].tolist()
        if str(x).strip()
    }
    if len(prior_figi) != len(prior_universe):
        raise ValueError("prior universe contains missing or duplicate FIGI")

    work = candidates.copy()
    work["ticker"] = work["ticker"].map(canonical_ticker)
    candidate_rows = len(work)

    excluded_prior = work["figi"].astype(str).isin(prior_figi)
    excluded_cal = work["ticker"].isin(CALIBRATION_TICKERS)
    pool = work[~excluded_prior & ~excluded_cal].copy()

    selected = deterministic_stratified_sample(
        pool,
        targets=TARGET_BY_SLEEVE,
        seed=seed,
    )

    overlap = set(selected["figi"].astype(str)) & prior_figi
    if overlap:
        raise AssertionError(
            f"OOS3 overlaps prior universe: {sorted(overlap)[:5]}"
        )
    if set(selected["ticker"]) & CALIBRATION_TICKERS:
        raise AssertionError("OOS3 contains calibration ticker")
    if len(selected) != 300:
        raise AssertionError(f"OOS3 selected {len(selected)} rows, expected 300")

    diagnostics = {
        "candidate_rows": int(candidate_rows),
        "prior_universe_rows": int(len(prior_universe)),
        "excluded_prior_candidate_rows": int(excluded_prior.sum()),
        "excluded_calibration_candidate_rows": int(excluded_cal.sum()),
        "remaining_candidate_rows_before_eligibility": int(len(pool)),
        "selected_rows": int(len(selected)),
        "selected_unique_figi": int(selected["figi"].nunique()),
        "counts_by_sleeve": (
            selected["sleeve"].value_counts().sort_index().to_dict()
        ),
        "counts_by_sector": (
            selected["sector"].value_counts().sort_index().to_dict()
        ),
        "overlap_with_prior_figi": 0,
    }
    return selected, diagnostics


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", type=Path, required=True)
    ap.add_argument("--prior-universe", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--seed", default=OOS3_SEED)
    args = ap.parse_args()

    candidates = pd.read_csv(args.candidates)
    prior = pd.read_csv(args.prior_universe)
    selected, diagnostics = build_oos3(
        candidates,
        prior,
        seed=args.seed,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    universe_path = (
        args.output_dir
        / "issue78_equity_proof_policy_oos3_universe_manifest.csv"
    )
    selected.to_csv(universe_path, index=False)

    manifest = {
        "issue": 78,
        "study": "equity-proof-policy-oos3",
        "cohort_role": "untouched-security survivorship-limited diagnostic",
        "selection_basis": {
            "candidate_snapshot": str(args.candidates),
            "prior_universe": str(args.prior_universe),
            "targets": TARGET_BY_SLEEVE,
            "sector_allocation": "equal-sector-within-size-sleeve",
            "seed": args.seed,
            "exclusions": [
                "all FIGIs in first Issue #119 / OOS2 300-stock cohort",
                "AAPL / JPM / XOM calibration fixtures",
                "same Issue #119 metadata eligibility rules",
            ],
        },
        "created_utc": datetime.now(timezone.utc).isoformat(),
        **diagnostics,
        "universe_sha256": file_sha256(universe_path),
        "universe_file": universe_path.name,
        "firewall": [
            "No OOS3 price history was read.",
            "No classifier or policy economics were computed.",
            "The universe must be frozen before OOS3 history is downloaded.",
            "No security may be replaced after strategy outcomes are visible.",
        ],
    }
    manifest_path = (
        args.output_dir
        / "issue78_equity_proof_policy_oos3_universe.json"
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, default=str) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(manifest, indent=2, default=str))


if __name__ == "__main__":
    main()
