#!/usr/bin/env python3
"""Build the untouched Issue #78 factorized-classifier OOS4 300-stock universe.

Uses the frozen Issue #119 Bloomberg candidate snapshot and excludes every
security used by both prior 300-stock equity cohorts before deterministic
sampling. No price history, classifier output, or economic outcome is read.
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

OOS4_SEED = "issue78-factorized-classifier-oos4-v1"


def _prior_figis(frames: list[pd.DataFrame]) -> set[str]:
    out: set[str] = set()
    for i, frame in enumerate(frames, start=1):
        missing = {"figi", "ticker"}.difference(frame.columns)
        if missing:
            raise ValueError(
                f"exclude universe {i} missing columns: {sorted(missing)}"
            )
        values = [
            str(x).strip()
            for x in frame["figi"].tolist()
            if str(x).strip()
        ]
        if len(values) != len(frame):
            raise ValueError(
                f"exclude universe {i} contains missing FIGI"
            )
        if len(set(values)) != len(values):
            raise ValueError(
                f"exclude universe {i} contains duplicate FIGI"
            )
        out.update(values)
    return out


def build_oos4(
    candidates: pd.DataFrame,
    exclude_universes: list[pd.DataFrame],
    *,
    seed: str = OOS4_SEED,
) -> tuple[pd.DataFrame, dict]:
    if len(exclude_universes) < 2:
        raise ValueError(
            "OOS4 requires at least the OOS2 and OOS3 exclusion universes"
        )

    prior_figi = _prior_figis(exclude_universes)

    work = candidates.copy()
    required = {"figi", "ticker", "sleeve", "sector"}
    missing = required.difference(work.columns)
    if missing:
        raise ValueError(
            f"candidate snapshot missing columns: {sorted(missing)}"
        )

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
            f"OOS4 overlaps prior universes: {sorted(overlap)[:5]}"
        )
    if set(selected["ticker"]) & CALIBRATION_TICKERS:
        raise AssertionError("OOS4 contains calibration ticker")
    if len(selected) != 300:
        raise AssertionError(
            f"OOS4 selected {len(selected)} rows, expected 300"
        )
    if selected["figi"].nunique() != 300:
        raise AssertionError("OOS4 FIGIs are not unique")

    diagnostics = {
        "candidate_rows": int(candidate_rows),
        "exclude_universe_count": int(len(exclude_universes)),
        "excluded_unique_prior_figi": int(len(prior_figi)),
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
    ap.add_argument(
        "--exclude-universe",
        type=Path,
        action="append",
        required=True,
        help=(
            "Prior equity-universe manifest to exclude. "
            "Pass once for OOS2 and once for OOS3."
        ),
    )
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--seed", default=OOS4_SEED)
    args = ap.parse_args()

    candidates = pd.read_csv(args.candidates)
    exclude_frames = [
        pd.read_csv(path) for path in args.exclude_universe
    ]
    selected, diagnostics = build_oos4(
        candidates,
        exclude_frames,
        seed=args.seed,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    universe_path = (
        args.output_dir
        / "issue78_factorized_classifier_oos4_universe_manifest.csv"
    )
    selected.to_csv(universe_path, index=False)

    manifest = {
        "issue": 78,
        "study": "factorized-classifier-architecture-oos4",
        "cohort_role": (
            "untouched-security cross-sectional architecture validation"
        ),
        "selection_basis": {
            "candidate_snapshot": str(args.candidates),
            "exclude_universes": [
                str(path) for path in args.exclude_universe
            ],
            "targets": TARGET_BY_SLEEVE,
            "sector_allocation": "equal-sector-within-size-sleeve",
            "seed": args.seed,
            "exclusions": [
                "all FIGIs in Issue #119 / OOS2 300-stock cohort",
                "all FIGIs in Issue #78 / OOS3 300-stock cohort",
                "AAPL / JPM / XOM calibration fixtures",
                "same Issue #119 metadata eligibility rules",
            ],
        },
        "created_utc": datetime.now(timezone.utc).isoformat(),
        **diagnostics,
        "universe_sha256": file_sha256(universe_path),
        "universe_file": universe_path.name,
        "firewall": [
            "No OOS4 price history was read.",
            "No factor forward outcome was computed.",
            "The universe must be frozen before OOS4 history is downloaded.",
            "No security may be replaced after OOS4 outcomes are visible.",
        ],
    }
    manifest_path = (
        args.output_dir
        / "issue78_factorized_classifier_oos4_universe.json"
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, default=str) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(manifest, indent=2, default=str))


if __name__ == "__main__":
    main()
