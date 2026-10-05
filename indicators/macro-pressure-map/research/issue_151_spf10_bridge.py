#!/usr/bin/env python3
"""Issue #151 — preregistered causal SPF 10Y CPI bridge.

Signal-only. No asset-return outcome is loaded.
"""
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import io
import json
from pathlib import Path

import pandas as pd

from issue_141_signal_bridge import add_turning, evaluate_bridge, load_exact
from issue_145_ipi_v2_bridge import (
    build_full_analogue_v2,
    build_gpi_replay,
    load_v2_source,
    validate_gpi_replay,
)

EXPECTED_SPF_SHA = "bfd9a8e76d882007a80584a439289f456bf06999223d2f1f30f85bb02f4e65e5"
EXPECTED_SPF_GZIP_SHA = "8d21fb8a3b346d160a63d8b67ac1fe454b27a20605388033f886cf3406681c3c"
EXPECTED_EXACT_SHA = "1d03923503e7fe82a69b033897484c48aa646279ecf70164d090ed62a5a70719"

HIST_START = pd.Period("1993-01", "M")
HIST_END = pd.Period("2006-12", "M")

ISSUE145_HOLDOUT = {
    "ipi_correlation": 0.8998539582818686,
    "ipi_slope_agreement": 0.8181818181818182,
    "regime_agreement": 0.5675675675675675,
    "r7_precision": 0.8,
    "r7_recall": 0.6153846153846154,
    "trigger_f1": 0.5,
}


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load_spf_source(data_dir: Path) -> tuple[pd.DataFrame, dict]:
    manifest = json.loads(
        (data_dir / "issue-151-spf10-source-freeze.json").read_text(encoding="utf-8")
    )
    if manifest["normalized_csv_sha256"] != EXPECTED_SPF_SHA:
        raise RuntimeError("Issue #151 SPF source manifest CSV SHA drift")
    if manifest["deterministic_gzip_sha256"] != EXPECTED_SPF_GZIP_SHA:
        raise RuntimeError("Issue #151 SPF source manifest gzip SHA drift")
    if manifest["exact_v66_signal_loaded"] is not False:
        raise RuntimeError("Issue #151 SPF source firewall violation: exact signal loaded")
    if manifest["outcome_data_loaded"] is not False:
        raise RuntimeError("Issue #151 SPF source firewall violation: outcome loaded")

    b64 = (
        data_dir / "issue-151-spf10-causal-monthly.csv.gz.b64"
    ).read_text(encoding="utf-8").strip()
    gz = base64.b64decode(b64, validate=True)
    if sha256(gz) != EXPECTED_SPF_GZIP_SHA:
        raise RuntimeError("Issue #151 SPF frozen gzip bytes drift")
    raw = gzip.decompress(gz)
    if sha256(raw) != EXPECTED_SPF_SHA:
        raise RuntimeError("Issue #151 SPF frozen CSV bytes drift")

    x = pd.read_csv(io.BytesIO(raw))
    expected_cols = ["date", "spf10", "survey", "release_date"]
    if list(x.columns) != expected_cols:
        raise RuntimeError(f"Issue #151 SPF columns changed: {x.columns.tolist()}")
    x["date"] = pd.to_datetime(x["date"], errors="raise")
    x["release_date"] = pd.to_datetime(x["release_date"], errors="raise")
    x["period"] = x["date"].dt.to_period("M")
    x["spf10"] = pd.to_numeric(x["spf10"], errors="raise")
    if x["period"].duplicated().any():
        raise RuntimeError("Issue #151 duplicate SPF month")
    if len(x) != 418:
        raise RuntimeError(f"Issue #151 SPF row-count drift: {len(x)}")
    if x["period"].min() != pd.Period("1991-11", "M"):
        raise RuntimeError("Issue #151 SPF first-month drift")
    if x["period"].max() != pd.Period("2026-08", "M"):
        raise RuntimeError("Issue #151 SPF last-month drift")
    if (x["release_date"] > x["date"]).any():
        raise RuntimeError("Issue #151 SPF causal availability violation")
    return x.sort_values("period").reset_index(drop=True), manifest


def build_spf_v2_source(v2_source: pd.DataFrame, spf: pd.DataFrame) -> pd.DataFrame:
    x = v2_source.copy()
    x = x.drop(columns=["expected_inflation_10y"], errors="raise")
    x = x.merge(
        spf[["period", "spf10"]],
        on="period",
        how="left",
        validate="one_to_one",
    )
    x = x.rename(columns={"spf10": "expected_inflation_10y"})
    return x.sort_values("period").reset_index(drop=True)


def map_verdict(old: str) -> str:
    return {
        "signal_bridge_passed": "signal_bridge_spf_passed",
        "signal_bridge_failed": "signal_bridge_spf_failed",
        "signal_bridge_inconclusive_sample": "signal_bridge_spf_inconclusive_sample",
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
            "spf": current[k],
            "delta": None if current[k] is None else float(current[k] - ISSUE145_HOLDOUT[k]),
        }
        for k in ISSUE145_HOLDOUT
    }


def spf_descriptives(spf: pd.DataFrame) -> dict:
    x = spf.copy().sort_values("period").reset_index(drop=True)
    unchanged = x["spf10"].diff().eq(0)
    new_survey = x["survey"].ne(x["survey"].shift(1))
    return {
        "months": int(len(x)),
        "unchanged_level_fraction_after_first": (
            float(unchanged.iloc[1:].mean()) if len(x) > 1 else None
        ),
        "effective_survey_months": int(new_survey.sum()),
        "distinct_surveys": int(x["survey"].nunique()),
        "first_month": str(x["period"].min()),
        "last_month": str(x["period"].max()),
    }


def run(
    data_dir: Path,
    issue133_root: Path,
    outdir: Path,
) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)

    v2_source, v2_freeze = load_v2_source(data_dir)
    spf, spf_freeze = load_spf_source(data_dir)
    exact, exact_manifest = load_exact(issue133_root)
    if exact_manifest["normalized_csv_sha256"] != EXPECTED_EXACT_SHA:
        raise RuntimeError("Issue #151 exact signal SHA drift")

    gpi, gpi_meta = build_gpi_replay()
    gpi_integrity = validate_gpi_replay(gpi, exact)

    bridge_source = build_spf_v2_source(v2_source, spf)
    analogue = build_full_analogue_v2(bridge_source, gpi)

    first_ipi = analogue.loc[
        analogue["ipi_v2_eligible"].fillna(False), "period"
    ].min()
    if first_ipi != HIST_START:
        raise RuntimeError(
            f"Issue #151 first complete SPF IPI score drift: {first_ipi} != {HIST_START}"
        )

    bridge_old, merged, _ = evaluate_bridge(exact, analogue)
    verdict = map_verdict(bridge_old["verdict"])
    validated = verdict == "signal_bridge_spf_passed"

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
            "Issue #151 bridge passed but historical window is not fully eligible"
        )

    result = {
        "schema_version": 1,
        "issue": 151,
        "phase": "spf10-causal-bridge",
        "spf_source_sha256": EXPECTED_SPF_SHA,
        "spf_source_freeze": {
            "source_run": spf_freeze["source_run"],
            "source_head": spf_freeze["source_head"],
            "artifact_digest": spf_freeze["artifact_digest"],
            "inflation_workbook_sha256": spf_freeze["inflation_workbook_sha256"],
            "release_dates_sha256": spf_freeze["release_dates_sha256"],
            "monthly_rule": spf_freeze["monthly_rule"],
        },
        "v2_source_freeze": {
            "source_run": v2_freeze["source_run"],
            "source_head": v2_freeze["source_head"],
            "artifact_digest": v2_freeze["artifact_digest"],
        },
        "exact_signal_sha256": exact_manifest["normalized_csv_sha256"],
        "gpi_replay_meta": gpi_meta,
        "gpi_replay_integrity": gpi_integrity,
        "spf_descriptives": spf_descriptives(spf),
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
        outdir / "issue-151-modern-bridge-evidence.csv",
        index=False,
        float_format="%.12g",
    )
    historical.to_csv(
        outdir / "issue-151-historical-signals-1993-2006.csv",
        index=False,
        float_format="%.12g",
    )
    (outdir / "issue-151-result.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    print(json.dumps({
        "verdict": verdict,
        "validated_for_outcome_testing": validated,
        "spf_descriptives": result["spf_descriptives"],
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
    ap.add_argument("--data-dir", type=Path, required=True)
    ap.add_argument("--issue133-root", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    run(args.data_dir, args.issue133_root, args.output_dir)


if __name__ == "__main__":
    main()
