#!/usr/bin/env python3
"""Build and freeze the Issue #119 Bloomberg 300-stock diagnostic universe."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from issue119_bbg_client import BloombergDesktopClient
from issue119_bbg_common import (
    METADATA_FIELDS,
    SOURCE_INDICES,
    TARGET_BY_SLEEVE,
    UNIVERSE_SEED,
    chunked,
    deterministic_stratified_sample,
    file_sha256,
    normalize_member_security,
)


def _member_value(row: dict[str, Any]) -> str:
    preferred = [
        "Member Ticker and Exchange Code",
        "Member Ticker & Exchange Code",
        "Member Ticker",
    ]
    lowered = {str(k).lower(): v for k, v in row.items()}
    for key in preferred:
        if key.lower() in lowered and str(lowered[key.lower()] or "").strip():
            return str(lowered[key.lower()])
    for key, value in row.items():
        if "member" in str(key).lower() and "ticker" in str(key).lower():
            return str(value or "")
    if row:
        return str(next(iter(row.values())) or "")
    return ""


def fetch_candidates(
    client: BloombergDesktopClient,
    *,
    metadata_batch_size: int = 100,
) -> pd.DataFrame:
    raw_members: list[dict[str, str]] = []
    for sleeve, index_security in SOURCE_INDICES.items():
        rows = client.bulk_index_members(index_security)
        for row in rows:
            member = normalize_member_security(_member_value(row))
            if member:
                raw_members.append(
                    {
                        "sleeve": sleeve,
                        "source_index": index_security,
                        "security": member,
                    }
                )

    members = pd.DataFrame(raw_members).drop_duplicates(
        ["sleeve", "security"]
    )
    if members.empty:
        raise RuntimeError(
            "Bloomberg index-member query produced no candidate securities"
        )

    metadata: dict[str, dict[str, Any]] = {}
    for batch in chunked(
        sorted(members["security"].unique()),
        metadata_batch_size,
    ):
        metadata.update(
            client.reference_data(batch, list(METADATA_FIELDS))
        )

    records: list[dict[str, Any]] = []
    for row in members.itertuples(index=False):
        meta = metadata.get(row.security, {})
        records.append(
            {
                "sleeve": row.sleeve,
                "source_index": row.source_index,
                "security": row.security,
                "figi": meta.get("ID_BB_GLOBAL"),
                "ticker": meta.get("TICKER"),
                "sector": meta.get("GICS_SECTOR_NAME"),
                "market_cap": meta.get("CUR_MKT_CAP"),
                "market_sector": meta.get("MARKET_SECTOR_DES"),
                "security_type": meta.get("SECURITY_TYP"),
                "primary_exchange": meta.get("EQY_PRIM_EXCH_SHRT"),
                "metadata_error": meta.get("_error"),
            }
        )
    return pd.DataFrame(records)


def write_universe_artifacts(
    candidates: pd.DataFrame,
    output_dir: Path,
    *,
    seed: str = UNIVERSE_SEED,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    candidate_path = output_dir / "issue119_bbg_oos2_candidates.csv"
    candidates.to_csv(candidate_path, index=False)

    selected = deterministic_stratified_sample(
        candidates,
        targets=TARGET_BY_SLEEVE,
        seed=seed,
    )
    selected_path = output_dir / "issue119_bbg_oos2_universe_manifest.csv"
    selected.to_csv(selected_path, index=False)

    manifest = {
        "issue": 119,
        "parent_issue": 78,
        "study": "survivorship-limited-large-equity-oos2-diagnostic",
        "provider": "Bloomberg Desktop API",
        "selection_basis": {
            "source_indices": SOURCE_INDICES,
            "targets": TARGET_BY_SLEEVE,
            "sector_allocation": "equal-sector-within-size-sleeve",
            "seed": seed,
        },
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_rows": int(len(candidates)),
        "selected_rows": int(len(selected)),
        "selected_unique_figi": int(selected["figi"].nunique()),
        "counts_by_sleeve": (
            selected["sleeve"].value_counts().sort_index().to_dict()
        ),
        "counts_by_sector": (
            selected["sector"].value_counts().sort_index().to_dict()
        ),
        "counts_by_sleeve_sector": {
            f"{sleeve}|{sector}": int(count)
            for (sleeve, sector), count
            in selected.groupby(["sleeve", "sector"]).size().items()
        },
        "artifacts": {
            candidate_path.name: {
                "sha256": file_sha256(candidate_path),
                "rows": int(len(candidates)),
            },
            selected_path.name: {
                "sha256": file_sha256(selected_path),
                "rows": int(len(selected)),
            },
        },
        "firewall": [
            "No R0 / Warning-First economics were calculated by this builder.",
            "AAPL / JPM / XOM are excluded before sampling.",
            "The universe is a current-constituent survivorship-limited diagnostic cohort.",
        ],
    }
    manifest_path = output_dir / "issue119_bbg_oos2_universe.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--candidate-csv", type=Path)
    ap.add_argument("--seed", default=UNIVERSE_SEED)
    args = ap.parse_args()

    if args.candidate_csv:
        candidates = pd.read_csv(args.candidate_csv)
    else:
        with BloombergDesktopClient() as client:
            candidates = fetch_candidates(client)

    manifest = write_universe_artifacts(
        candidates,
        args.output_dir,
        seed=args.seed,
    )
    print(
        json.dumps(
            {
                "selected_rows": manifest["selected_rows"],
                "counts_by_sleeve": manifest["counts_by_sleeve"],
                "counts_by_sector": manifest["counts_by_sector"],
                "universe_sha256": manifest["artifacts"][
                    "issue119_bbg_oos2_universe_manifest.csv"
                ]["sha256"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
