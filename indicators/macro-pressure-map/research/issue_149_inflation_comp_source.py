#!/usr/bin/env python3
"""Issue #149 Phase A — Cleveland inflation-compensation source freeze only.

No exact V6.6 signal and no asset-return outcome is loaded.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
from pathlib import Path

import pandas as pd

import issue_141_source_acquisition as i141

EXPECTED_CLEVELAND_SHA = "20701ccf394d280fe1db38fa9def5628f2385dd0aef148ff989e33ff15caba95"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def normalize_col(x: object) -> str:
    return re.sub(r"\s+", " ", str(x)).strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    url, landing = i141.locate_cleveland_xlsx()
    raw = i141.fetch(url)
    observed = sha256_bytes(raw)
    if observed != EXPECTED_CLEVELAND_SHA:
        raise RuntimeError(
            f"Cleveland workbook SHA drift: {observed} != {EXPECTED_CLEVELAND_SHA}"
        )

    xls = pd.ExcelFile(io.BytesIO(raw))
    inventory: dict[str, list[str]] = {}
    candidates: list[dict] = []

    for sheet in xls.sheet_names:
        df = pd.read_excel(io.BytesIO(raw), sheet_name=sheet)
        cols = [normalize_col(c) for c in df.columns]
        inventory[sheet] = cols
        for original, norm in zip(df.columns, cols):
            low = norm.lower()
            if "10 year" in low or "10-year" in low:
                if "expected inflation" in low or "inflation risk premium" in low:
                    candidates.append({
                        "sheet": sheet,
                        "original_column": str(original),
                        "normalized_column": norm,
                    })

    expected_candidates = [
        x for x in candidates
        if "expected inflation" in x["normalized_column"].lower()
    ]
    risk_candidates = [
        x for x in candidates
        if "inflation risk premium" in x["normalized_column"].lower()
    ]

    print(json.dumps({
        "sheets": xls.sheet_names,
        "candidates": candidates,
    }, indent=2, ensure_ascii=False), flush=True)

    if len(expected_candidates) != 1 or len(risk_candidates) != 1:
        raise RuntimeError(
            "Expected exactly one 10Y expected-inflation column and one "
            f"10Y inflation-risk-premium column; got {expected_candidates=} "
            f"{risk_candidates=}"
        )

    e = expected_candidates[0]
    r = risk_candidates[0]
    if e["sheet"] != r["sheet"]:
        raise RuntimeError(
            f"Expected and risk-premium columns are on different sheets: {e} vs {r}"
        )

    df = pd.read_excel(io.BytesIO(raw), sheet_name=e["sheet"])
    date_candidates = [
        c for c in df.columns
        if normalize_col(c).lower() in {"model output date", "date"}
    ]
    if len(date_candidates) != 1:
        raise RuntimeError(f"Expected one date column, got {date_candidates}")
    date_col = date_candidates[0]

    panel = df[[date_col, e["original_column"], r["original_column"]]].copy()
    panel.columns = [
        "date",
        "expected_inflation_10y",
        "inflation_risk_premium_10y",
    ]
    panel["date"] = pd.to_datetime(panel["date"], errors="coerce")
    panel["expected_inflation_10y"] = pd.to_numeric(
        panel["expected_inflation_10y"], errors="coerce"
    )
    panel["inflation_risk_premium_10y"] = pd.to_numeric(
        panel["inflation_risk_premium_10y"], errors="coerce"
    )
    panel = panel.loc[panel["date"].notna()].copy()
    panel["period"] = panel["date"].dt.to_period("M")
    if panel["period"].duplicated().any():
        raise RuntimeError("duplicate Cleveland monthly period")

    panel["cleveland_comp10"] = (
        panel["expected_inflation_10y"]
        + panel["inflation_risk_premium_10y"]
    )
    panel = panel.sort_values("period").reset_index(drop=True)

    finite = panel[
        ["expected_inflation_10y", "inflation_risk_premium_10y", "cleveland_comp10"]
    ].notna().all(axis=1)
    if not finite.any():
        raise RuntimeError("Cleveland compensation series has no finite observations")

    csv_path = out / "issue-149-cleveland-comp10.csv"
    panel.drop(columns=["period"]).to_csv(
        csv_path, index=False, date_format="%Y-%m-%d", float_format="%.12g"
    )

    manifest = {
        "schema_version": 1,
        "issue": 149,
        "phase": "A-source-only",
        "exact_v66_signal_loaded": False,
        "outcome_data_loaded": False,
        "source": {
            "url": url,
            "landing_sha256": sha256_bytes(landing),
            "workbook_sha256": observed,
            "sheet": e["sheet"],
            "date_column": str(date_col),
            "expected_inflation_column": e["original_column"],
            "inflation_risk_premium_column": r["original_column"],
        },
        "coverage": {
            "rows": int(len(panel)),
            "finite_rows": int(finite.sum()),
            "first_finite_period": str(panel.loc[finite, "period"].min()),
            "last_finite_period": str(panel.loc[finite, "period"].max()),
        },
        "formula": "cleveland_comp10 = expected_inflation_10y + inflation_risk_premium_10y",
        "normalized_csv_sha256": sha256_bytes(csv_path.read_bytes()),
        "column_inventory": inventory,
        "guardrail": "Source freeze only; no exact V6.6 target and no asset-return outcome loaded.",
    }
    (out / "issue-149-source-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
