#!/usr/bin/env python3
"""Issue #149 — preregistered Inflation Compensation Bridge v3.

Signal-only. No asset-return outcome is loaded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from issue_141_signal_bridge import add_turning, evaluate_bridge, load_exact
from issue_145_ipi_v2_bridge import (
    HIST_END,
    HIST_START,
    build_full_analogue_v2,
    build_gpi_replay,
    load_v2_source,
    validate_gpi_replay,
)

EXPECTED_COMP_SHA = "a07dbdb377a2ae1dedc7a176d43b20b14d951caddde776aef18dfcf810256a10"
EXPECTED_EXACT_SHA = "1d03923503e7fe82a69b033897484c48aa646279ecf70164d090ed62a5a70719"

ISSUE145_HOLDOUT = {
    "ipi_correlation": 0.8998539582818686,
    "ipi_slope_agreement": 0.8181818181818182,
    "regime_agreement": 0.5675675675675675,
    "r7_precision": 0.8,
    "r7_recall": 0.6153846153846154,
    "trigger_f1": 0.5,
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_comp_source(source_dir: Path) -> tuple[pd.DataFrame, dict]:
    csv_path = source_dir / "issue-149-cleveland-comp10.csv"
    manifest_path = source_dir / "issue-149-source-manifest.json"
    if sha256_file(csv_path) != EXPECTED_COMP_SHA:
        raise RuntimeError("Issue #149 normalized compensation CSV SHA drift")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["normalized_csv_sha256"] != EXPECTED_COMP_SHA:
        raise RuntimeError("Issue #149 source manifest SHA mismatch")
    if manifest["exact_v66_signal_loaded"] is not False:
        raise RuntimeError("Issue #149 Phase-A firewall violation: exact signal loaded")
    if manifest["outcome_data_loaded"] is not False:
        raise RuntimeError("Issue #149 Phase-A firewall violation: outcome loaded")

    x = pd.read_csv(csv_path)
    required = {
        "date",
        "expected_inflation_10y",
        "inflation_risk_premium_10y",
        "cleveland_comp10",
    }
    if set(x.columns) != required:
        raise RuntimeError(f"Issue #149 compensation columns changed: {x.columns.tolist()}")
    x["date"] = pd.to_datetime(x["date"], errors="raise")
    x["period"] = x["date"].dt.to_period("M")
    if x["period"].duplicated().any():
        raise RuntimeError("Issue #149 duplicate compensation month")
    for c in required - {"date"}:
        x[c] = pd.to_numeric(x[c], errors="raise")
    check = x["expected_inflation_10y"] + x["inflation_risk_premium_10y"]
    if not np.allclose(
        check.to_numpy(float),
        x["cleveland_comp10"].to_numpy(float),
        rtol=0,
        atol=1e-11,
    ):
        raise RuntimeError("Issue #149 compensation +1/+1 formula drift")
    if not x["cleveland_comp10"].gt(0).all():
        raise RuntimeError("Issue #149 compensation level must remain positive")
    return x.sort_values("period").reset_index(drop=True), manifest


def build_v3_source(v2_source: pd.DataFrame, comp: pd.DataFrame) -> pd.DataFrame:
    x = v2_source.copy()
    x = x.drop(columns=["expected_inflation_10y"], errors="raise")
    x = x.merge(
        comp[["period", "cleveland_comp10"]],
        on="period",
        how="left",
        validate="one_to_one",
    )
    x = x.rename(columns={"cleveland_comp10": "expected_inflation_10y"})
    return x.sort_values("period").reset_index(drop=True)


def map_verdict(old: str) -> str:
    return {
        "signal_bridge_passed": "signal_bridge_v3_passed",
        "signal_bridge_failed": "signal_bridge_v3_failed",
        "signal_bridge_inconclusive_sample": "signal_bridge_v3_inconclusive_sample",
    }[old]


def compare_to_issue145(hold: dict) -> dict:
    current = {
        "ipi_correlation": hold["ipi_correlation"],
        "ipi_slope_agreement": hold["ipi_slope_sign"]["agreement"],
        "regime_agreement": hold["regime_agreement"],
        "r7_precision": hold["r7"]["precision"],
        "r7_recall": hold["r7"]["recall"],
        "trigger_f1": hold["triggers"]["f1"],
    }
    return {
        k: {
            "issue145": ISSUE145_HOLDOUT[k],
            "v3": current[k],
            "delta": None if current[k] is None else float(current[k] - ISSUE145_HOLDOUT[k]),
        }
        for k in ISSUE145_HOLDOUT
    }


def run(
    v2_data_dir: Path,
    comp_source_dir: Path,
    issue133_root: Path,
    outdir: Path,
) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)

    v2_source, v2_freeze = load_v2_source(v2_data_dir)
    comp, comp_manifest = load_comp_source(comp_source_dir)
    exact, exact_manifest = load_exact(issue133_root)
    if exact_manifest["normalized_csv_sha256"] != EXPECTED_EXACT_SHA:
        raise RuntimeError("Issue #149 exact signal SHA drift")

    gpi, gpi_meta = build_gpi_replay()
    gpi_integrity = validate_gpi_replay(gpi, exact)

    v3_source = build_v3_source(v2_source, comp)
    analogue = build_full_analogue_v2(v3_source, gpi)

    # Verify the inherited historical eligibility boundary did not change.
    eligible = analogue.loc[
        analogue["ipi_v2_eligible"].fillna(False), "period"
    ]
    first_ipi = eligible.min()
    if first_ipi != HIST_START:
        raise RuntimeError(
            f"Issue #149 first complete IPI v3 score drift: {first_ipi} != {HIST_START}"
        )

    bridge_old, merged, _ = evaluate_bridge(exact, analogue)
    verdict = map_verdict(bridge_old["verdict"])
    validated = verdict == "signal_bridge_v3_passed"

    full_turn = add_turning(
        analogue, "gpi_a", "ipi_a", "regime_a", "analogue"
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

    historical_complete = bool(
        len(historical) > 0
        and historical["analogue_eligible"].fillna(False).all()
    )
    if validated and not historical_complete:
        raise RuntimeError(
            "Issue #149 bridge passed but historical window is not fully eligible"
        )

    result = {
        "schema_version": 1,
        "issue": 149,
        "phase": "inflation-compensation-bridge-v3",
        "compensation_source_sha256": EXPECTED_COMP_SHA,
        "compensation_source": {
            "source_run": 37258981774,
            "source_head": "2cdf1bb5eeebe43a5ae60b212348c55a833cb690",
            "artifact_digest": "sha256:b679efc77f8eee89f6fb2c28bdffe97f3680eee6ea281341e6e4765cadace2fd",
            "workbook_sha256": comp_manifest["source"]["workbook_sha256"],
            "formula": comp_manifest["formula"],
        },
        "v2_source_freeze": {
            "source_run": v2_freeze["source_run"],
            "source_head": v2_freeze["source_head"],
            "artifact_digest": v2_freeze["artifact_digest"],
        },
        "exact_signal_sha256": exact_manifest["normalized_csv_sha256"],
        "gpi_replay_meta": gpi_meta,
        "gpi_replay_integrity": gpi_integrity,
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
        "comparison_to_issue145": compare_to_issue145(bridge_old["holdout"]),
        "outcome_data_loaded": False,
        "production_authorized": False,
    }

    merged.to_csv(
        outdir / "issue-149-modern-bridge-evidence.csv",
        index=False,
        float_format="%.12g",
    )
    historical.to_csv(
        outdir / "issue-149-historical-signals-1990-2006.csv",
        index=False,
        float_format="%.12g",
    )
    (outdir / "issue-149-result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    print(json.dumps({
        "verdict": verdict,
        "validated_for_outcome_testing": validated,
        "gpi_integrity": gpi_integrity,
        "development": bridge_old["development"],
        "holdout": bridge_old["holdout"],
        "subsegments": bridge_old["holdout_subsegments"],
        "gates": bridge_old["gates"],
        "historical_window": result["historical_window"],
        "comparison_to_issue145": result["comparison_to_issue145"],
        "outcome_data_loaded": False,
    }, indent=2, ensure_ascii=False))
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--v2-data-dir", type=Path, required=True)
    ap.add_argument("--comp-source-dir", type=Path, required=True)
    ap.add_argument("--issue133-root", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    run(args.v2_data_dir, args.comp_source_dir, args.issue133_root, args.output_dir)


if __name__ == "__main__":
    main()
