#!/usr/bin/env python3
"""Issue #145 — preregistered IPI Bridge v2 evaluator.

Signal-only. No asset-return outcome is loaded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from issue_141_signal_bridge import (
    add_turning,
    build_analogue,
    component_score,
    evaluate_bridge,
    load_exact,
    load_frozen_sources,
    regime_id,
)

EXPECTED_V2_SOURCE_SHA = "848a7ba847b3637b3b8b4715df7b555598c6a7a3bcced76d85aed1e42b29ecaa"
EXPECTED_EXACT_SHA = "1d03923503e7fe82a69b033897484c48aa646279ecf70164d090ed62a5a70719"
HIST_START = pd.Period("1990-02", "M")
HIST_END = pd.Period("2006-12", "M")

ISSUE141_HOLDOUT = {
    "gpi_correlation": 0.8980438446122531,
    "ipi_correlation": 0.6829508192246171,
    "gpi_slope_agreement": 0.8608695652173913,
    "ipi_slope_agreement": 0.6956521739130435,
    "regime_agreement": 0.45689655172413796,
    "r7_precision": 0.7222222222222222,
    "r7_recall": 0.5,
    "trigger_f1": 0.1818181818181818,
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_v2_source(source_dir: Path) -> tuple[pd.DataFrame, dict]:
    panel_path = source_dir / "issue-145-v2-source-panel.csv"
    manifest_path = source_dir / "issue-145-source-manifest.json"
    if sha256_file(panel_path) != EXPECTED_V2_SOURCE_SHA:
        raise RuntimeError("Issue #145 frozen normalized source-panel SHA drift")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["exact_v66_signal_loaded"] is not False:
        raise RuntimeError("Issue #145 Phase-A firewall violation: exact signal loaded")
    if manifest["outcome_data_loaded"] is not False:
        raise RuntimeError("Issue #145 Phase-A firewall violation: outcome loaded")
    if manifest["v2_panel"]["csv_sha256"] != EXPECTED_V2_SOURCE_SHA:
        raise RuntimeError("Issue #145 manifest source-panel SHA mismatch")

    x = pd.read_csv(panel_path)
    required = {
        "dbiq_level",
        "gasoline",
        "Crude oil, WTI",
        "expected_inflation_10y",
        "date",
    }
    if not required.issubset(x.columns):
        raise RuntimeError(f"Issue #145 source columns changed: {x.columns.tolist()}")
    x["date"] = pd.to_datetime(x["date"], errors="raise")
    x["period"] = x["date"].dt.to_period("M")
    if x["period"].duplicated().any():
        raise RuntimeError("Issue #145 duplicate source month")
    for c in required - {"date"}:
        x[c] = pd.to_numeric(x[c], errors="coerce")
    return x.sort_values("period").reset_index(drop=True), manifest


def build_v2_ipi(source: pd.DataFrame) -> pd.DataFrame:
    x = source.copy()
    x["ipi_expected"] = component_score(x["expected_inflation_10y"])
    x["ipi_dbiq"] = component_score(x["dbiq_level"])
    x["ipi_wti"] = component_score(x["Crude oil, WTI"])
    x["ipi_gasoline"] = component_score(x["gasoline"])
    x["ipi_energy"] = x[["ipi_wti", "ipi_gasoline"]].mean(axis=1, skipna=False)

    score_cols = ["ipi_expected", "ipi_dbiq", "ipi_wti", "ipi_gasoline"]
    x["ipi_v2_eligible"] = x[score_cols].notna().all(axis=1)
    x["ipi_a"] = (
        0.35 * x["ipi_expected"]
        + 0.40 * x["ipi_dbiq"]
        + 0.25 * x["ipi_energy"]
    )
    x.loc[~x["ipi_v2_eligible"], "ipi_a"] = np.nan
    return x


def build_full_analogue_v2(source: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    factors, industries, wb, cleveland, gpi_meta = load_frozen_sources()
    old = build_analogue(factors, industries, wb, cleveland)
    gpi = old[["period", "gpi_a"]].copy()

    ipi = build_v2_ipi(source)[["period", "ipi_a", "ipi_v2_eligible"]].copy()
    x = gpi.merge(ipi, on="period", how="outer", validate="one_to_one")
    x = x.sort_values("period").reset_index(drop=True)
    x["analogue_eligible"] = (
        x["gpi_a"].notna()
        & x["ipi_a"].notna()
        & x["ipi_v2_eligible"].fillna(False)
    )
    x["regime_a"] = [
        regime_id(g, i) if np.isfinite(g) and np.isfinite(i) else np.nan
        for g, i in zip(
            pd.to_numeric(x["gpi_a"], errors="coerce").to_numpy(float),
            pd.to_numeric(x["ipi_a"], errors="coerce").to_numpy(float),
        )
    ]
    x["date"] = x["period"].dt.to_timestamp("M")
    return x, gpi_meta


def map_verdict(old: str) -> str:
    return {
        "signal_bridge_passed": "signal_bridge_v2_passed",
        "signal_bridge_failed": "signal_bridge_v2_failed",
        "signal_bridge_inconclusive_sample": "signal_bridge_v2_inconclusive_sample",
    }[old]


def holdout_comparison(hold: dict) -> dict:
    mapping = {
        "gpi_correlation": hold["gpi_correlation"],
        "ipi_correlation": hold["ipi_correlation"],
        "gpi_slope_agreement": hold["gpi_slope_sign"]["agreement"],
        "ipi_slope_agreement": hold["ipi_slope_sign"]["agreement"],
        "regime_agreement": hold["regime_agreement"],
        "r7_precision": hold["r7"]["precision"],
        "r7_recall": hold["r7"]["recall"],
        "trigger_f1": hold["triggers"]["f1"],
    }
    return {
        k: {
            "issue141": ISSUE141_HOLDOUT[k],
            "v2": mapping[k],
            "delta": (
                None if mapping[k] is None
                else float(mapping[k] - ISSUE141_HOLDOUT[k])
            ),
        }
        for k in ISSUE141_HOLDOUT
    }


def run(source_dir: Path, issue133_root: Path, outdir: Path) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)

    source, source_manifest = load_v2_source(source_dir)
    exact, exact_manifest = load_exact(issue133_root)
    if exact_manifest["normalized_csv_sha256"] != EXPECTED_EXACT_SHA:
        raise RuntimeError("Issue #145 exact signal SHA drift")

    analogue, gpi_meta = build_full_analogue_v2(source)

    first_ipi = analogue.loc[
        analogue["ipi_v2_eligible"].fillna(False), "period"
    ].min()
    if first_ipi != HIST_START:
        raise RuntimeError(
            f"Issue #145 first complete IPI v2 score drift: {first_ipi} != {HIST_START}"
        )

    bridge_old, merged, _ = evaluate_bridge(exact, analogue)
    verdict = map_verdict(bridge_old["verdict"])
    validated = verdict == "signal_bridge_v2_passed"

    full_turn = add_turning(
        analogue,
        "gpi_a",
        "ipi_a",
        "regime_a",
        "analogue",
    )
    historical = full_turn.loc[
        full_turn["period"].between(HIST_START, HIST_END),
        [
            "date",
            "period",
            "gpi_a",
            "ipi_a",
            "regime_a",
            "analogue_episode_id",
            "analogue_trigger",
            "analogue_eligible",
        ],
    ].copy()
    historical["validated_for_outcome_testing"] = validated

    # The entire frozen historical window must be fully eligible for use if bridge passes.
    historical_complete = bool(
        len(historical) > 0
        and historical["analogue_eligible"].fillna(False).all()
    )

    result = {
        "schema_version": 1,
        "issue": 145,
        "phase": "ipi-bridge-v2",
        "source_panel_sha256": EXPECTED_V2_SOURCE_SHA,
        "exact_signal_sha256": exact_manifest["normalized_csv_sha256"],
        "source_manifest": {
            "dbiq": source_manifest["dbiq"],
            "mgasnyh": source_manifest["mgasnyh"],
            "v2_panel": source_manifest["v2_panel"],
        },
        "gpi_source_meta": gpi_meta,
        "development": bridge_old["development"],
        "holdout": bridge_old["holdout"],
        "holdout_subsegments": bridge_old["holdout_subsegments"],
        "gates": bridge_old["gates"],
        "verdict": verdict,
        "validated_for_outcome_testing": validated,
        "historical_window": {
            "start": str(HIST_START),
            "end": str(HIST_END),
            "rows": int(len(historical)),
            "all_rows_eligible": historical_complete,
            "r7_months": int(historical["regime_a"].eq(7).sum()),
            "async_turn_triggers": int(historical["analogue_trigger"].sum()),
            "trigger_months": [
                str(p)
                for p in historical.loc[
                    historical["analogue_trigger"], "period"
                ].tolist()
            ],
        },
        "comparison_to_issue141": holdout_comparison(bridge_old["holdout"]),
        "outcome_data_loaded": False,
        "production_authorized": False,
    }

    if validated and not historical_complete:
        raise RuntimeError(
            "Issue #145 bridge passed but historical window is not fully eligible"
        )

    merged.to_csv(
        outdir / "issue-145-modern-bridge-evidence.csv",
        index=False,
        float_format="%.12g",
    )
    historical.to_csv(
        outdir / "issue-145-historical-signals-1990-2006.csv",
        index=False,
        float_format="%.12g",
    )
    (outdir / "issue-145-result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    print(json.dumps({
        "verdict": verdict,
        "validated_for_outcome_testing": validated,
        "development": bridge_old["development"],
        "holdout": bridge_old["holdout"],
        "subsegments": bridge_old["holdout_subsegments"],
        "gates": bridge_old["gates"],
        "historical_window": result["historical_window"],
        "comparison_to_issue141": result["comparison_to_issue141"],
        "outcome_data_loaded": False,
    }, indent=2, ensure_ascii=False))
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-dir", type=Path, required=True)
    ap.add_argument("--issue133-root", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    run(args.source_dir, args.issue133_root, args.output_dir)


if __name__ == "__main__":
    main()
