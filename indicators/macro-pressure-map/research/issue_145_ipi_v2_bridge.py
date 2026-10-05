#!/usr/bin/env python3
"""Issue #145 — preregistered IPI Bridge v2 evaluator.

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

import numpy as np
import pandas as pd

import issue_141_source_acquisition as src
from issue_141_signal_bridge import (
    EXPECTED_SOURCE_SHA,
    add_turning,
    component_score,
    evaluate_bridge,
    load_exact,
    pearson,
    regime_id,
    sign_agreement,
    wealth_from_pct_return,
    with_period,
)

EXPECTED_V2_SOURCE_SHA = "848a7ba847b3637b3b8b4715df7b555598c6a7a3bcced76d85aed1e42b29ecaa"
EXPECTED_V2_GZIP_SHA = "cf1fee26e606a26cf9166b8871826945b58b2b2fd0e5b3f590533b07faec5c08"
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


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load_v2_source(data_dir: Path) -> tuple[pd.DataFrame, dict]:
    freeze = json.loads(
        (data_dir / "issue-145-v2-source-freeze.json").read_text(encoding="utf-8")
    )
    if freeze["normalized_csv_sha256"] != EXPECTED_V2_SOURCE_SHA:
        raise RuntimeError("Issue #145 frozen source manifest CSV SHA drift")
    if freeze["deterministic_gzip_sha256"] != EXPECTED_V2_GZIP_SHA:
        raise RuntimeError("Issue #145 frozen source manifest gzip SHA drift")
    if freeze["exact_v66_signal_loaded"] is not False or freeze["outcome_data_loaded"] is not False:
        raise RuntimeError("Issue #145 source freeze firewall violation")

    b64 = "".join(
        (data_dir / name).read_text(encoding="utf-8").strip()
        for name in freeze["parts"]
    )
    gz = base64.b64decode(b64, validate=True)
    if sha256(gz) != EXPECTED_V2_GZIP_SHA:
        raise RuntimeError("Issue #145 frozen gzip bytes drift")
    raw = gzip.decompress(gz)
    if sha256(raw) != EXPECTED_V2_SOURCE_SHA:
        raise RuntimeError("Issue #145 frozen normalized CSV bytes drift")

    x = pd.read_csv(io.BytesIO(raw))
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
    if len(x) != 448 or x["period"].min() != pd.Period("1988-12", "M") or x["period"].max() != pd.Period("2026-03", "M"):
        raise RuntimeError("Issue #145 frozen source coverage drift")
    return x.sort_values("period").reset_index(drop=True), freeze


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


def build_gpi_replay() -> tuple[pd.DataFrame, dict]:
    # Replay the frozen Issue #141 GPI formula. French inputs must retain their
    # exact frozen bytes; World Bank may append new rows, so GPI output is
    # validated against #141's frozen holdout metrics before use.
    raw_factors = src.fetch(src.FRENCH_FACTORS)
    raw_ind = src.fetch(src.FRENCH_12IND)
    if sha256(raw_factors) != EXPECTED_SOURCE_SHA["french_factors"]:
        raise RuntimeError("Issue #145 French factors source drift")
    if sha256(raw_ind) != EXPECTED_SOURCE_SHA["french_12_industry"]:
        raise RuntimeError("Issue #145 French industry source drift")

    wb_url, _ = src.locate_world_bank_monthly_url()
    raw_wb = src.fetch(wb_url)

    factors = src.parse_french_block(
        src.first_member_text(raw_factors), {"Mkt-RF", "SMB", "RF"}
    )
    industries = src.parse_french_block(
        src.first_member_text(raw_ind), {"NoDur", "Durbl", "Manuf", "Utils", "Shops"}
    )
    wb = src.selected_world_bank_panel(src.wb_sheet(raw_wb, "Monthly Prices"))

    f = with_period(factors)
    ind = with_period(industries)
    w = with_period(wb)

    fcols = ["period", "Mkt-RF", "SMB", "RF"]
    industry_cols = [x for x in ind.columns if x not in {"date", "period"}]
    if len(industry_cols) != 12:
        raise RuntimeError("Issue #145 expected 12 French industry portfolios")

    fr = f[fcols].merge(
        ind[["period"] + industry_cols],
        on="period",
        how="inner",
        validate="one_to_one",
    ).sort_values("period").reset_index(drop=True)

    fr["small_relative_level"] = wealth_from_pct_return(fr["SMB"])

    ind_ew_ret = fr[industry_cols].astype(float).mean(axis=1)
    market_ret = fr["Mkt-RF"].astype(float) + fr["RF"].astype(float)
    fr["breadth_level"] = (
        wealth_from_pct_return(ind_ew_ret)
        / wealth_from_pct_return(market_ret)
    )

    cyc_ret = fr[["Durbl", "Shops"]].astype(float).mean(axis=1)
    fr["cyc_def_level"] = (
        wealth_from_pct_return(cyc_ret)
        / wealth_from_pct_return(fr["NoDur"].astype(float))
    )

    fr["manuf_utils_level"] = (
        wealth_from_pct_return(fr["Manuf"].astype(float))
        / wealth_from_pct_return(fr["Utils"].astype(float))
    )

    x = fr[[
        "period",
        "small_relative_level",
        "breadth_level",
        "cyc_def_level",
        "manuf_utils_level",
    ]].merge(
        w[["period", "Copper", "Gold"]],
        on="period",
        how="outer",
        validate="one_to_one",
    ).sort_values("period").reset_index(drop=True)

    x["copper_gold_level"] = x["Copper"] / x["Gold"]
    level_cols = [
        "small_relative_level",
        "breadth_level",
        "cyc_def_level",
        "manuf_utils_level",
        "copper_gold_level",
    ]
    score_cols = []
    for i, col in enumerate(level_cols, start=1):
        sc = f"gpi_{i}"
        x[sc] = component_score(x[col])
        score_cols.append(sc)
    x["gpi_a"] = x[score_cols].mean(axis=1, skipna=False)
    x["date"] = x["period"].dt.to_timestamp("M")
    return x[["date", "period", "gpi_a"]], {
        "french_factors_sha256": sha256(raw_factors),
        "french_12_industry_sha256": sha256(raw_ind),
        "world_bank_live_sha256": sha256(raw_wb),
        "world_bank_url": wb_url,
    }


def validate_gpi_replay(gpi: pd.DataFrame, exact: pd.DataFrame) -> dict:
    x = exact[["period", "gpi"]].merge(
        gpi[["period", "gpi_a"]],
        on="period",
        how="inner",
        validate="one_to_one",
    )
    x = x.loc[
        x["period"].between(pd.Period("2017-01", "M"), pd.Period("2026-08", "M"))
        & x["gpi"].notna()
        & x["gpi_a"].notna()
    ].sort_values("period").reset_index(drop=True)

    corr = pearson(x["gpi"], x["gpi_a"])
    slope = sign_agreement(x, "gpi", "gpi_a")["agreement"]
    if corr is None or slope is None:
        raise RuntimeError("Issue #145 GPI replay integrity metrics unevaluable")
    if abs(corr - ISSUE141_HOLDOUT["gpi_correlation"]) > 1e-12:
        raise RuntimeError(
            f"Issue #145 GPI replay correlation drift: {corr} != {ISSUE141_HOLDOUT['gpi_correlation']}"
        )
    if abs(slope - ISSUE141_HOLDOUT["gpi_slope_agreement"]) > 1e-12:
        raise RuntimeError(
            f"Issue #145 GPI replay slope drift: {slope} != {ISSUE141_HOLDOUT['gpi_slope_agreement']}"
        )
    return {
        "common_months": int(len(x)),
        "correlation": corr,
        "slope_sign_agreement": slope,
        "matches_issue141_frozen_metrics": True,
    }


def build_full_analogue_v2(source: pd.DataFrame, gpi: pd.DataFrame) -> pd.DataFrame:
    ipi = build_v2_ipi(source)[["period", "ipi_a", "ipi_v2_eligible"]].copy()
    x = gpi[["period", "gpi_a"]].merge(
        ipi, on="period", how="outer", validate="one_to_one"
    ).sort_values("period").reset_index(drop=True)
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
    return x


def map_verdict(old: str) -> str:
    return {
        "signal_bridge_passed": "signal_bridge_v2_passed",
        "signal_bridge_failed": "signal_bridge_v2_failed",
        "signal_bridge_inconclusive_sample": "signal_bridge_v2_inconclusive_sample",
    }[old]


def holdout_comparison(hold: dict) -> dict:
    current = {
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
            "v2": current[k],
            "delta": None if current[k] is None else float(current[k] - ISSUE141_HOLDOUT[k]),
        }
        for k in ISSUE141_HOLDOUT
    }


def run(source_data_dir: Path, issue133_root: Path, outdir: Path) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)

    source, freeze = load_v2_source(source_data_dir)
    exact, exact_manifest = load_exact(issue133_root)
    if exact_manifest["normalized_csv_sha256"] != EXPECTED_EXACT_SHA:
        raise RuntimeError("Issue #145 exact signal SHA drift")

    gpi, gpi_meta = build_gpi_replay()
    gpi_integrity = validate_gpi_replay(gpi, exact)
    analogue = build_full_analogue_v2(source, gpi)

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

    result = {
        "schema_version": 1,
        "issue": 145,
        "phase": "ipi-bridge-v2",
        "source_panel_sha256": EXPECTED_V2_SOURCE_SHA,
        "source_freeze": {
            "source_run": freeze["source_run"],
            "source_head": freeze["source_head"],
            "artifact_digest": freeze["artifact_digest"],
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
        "gpi_integrity": gpi_integrity,
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
    ap.add_argument("--source-data-dir", type=Path, required=True)
    ap.add_argument("--issue133-root", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    run(args.source_data_dir, args.issue133_root, args.output_dir)


if __name__ == "__main__":
    main()
