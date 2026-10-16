#!/usr/bin/env python3
"""Fail-closed validator for Issue #91 Phase 0 durable source freeze."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FREEZE = HERE / "decisions" / "issue-91-phase0-source-freeze.json"
PLAN = HERE / "decisions" / "issue-91-phase0-source-plan.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def validate(evidence_dir: Path) -> dict:
    freeze = load_json(FREEZE)
    plan = load_json(PLAN)
    audit = load_json(evidence_dir / "issue-91-phase0-source-audit.json")

    require(freeze["issue"] == 91 and freeze["phase"] == "0-source-audit", "bad source-freeze identity")
    require(plan["issue"] == 91 and plan["phase"] == "0-source-audit", "bad Phase 0 plan identity")
    require(plan["etf_use_in_primary_long_history_analysis"] is False, "ETF use became allowed in Phase 0 plan")
    require(audit["regime_conditioned_asset_results_computed"] is False, "Phase 0 computed conditioned outcomes")
    require(audit["portfolio_results_computed"] is False, "Phase 0 computed portfolio outcomes")
    require(audit["etfs_used"] is False, "ETF leaked into Phase 0")
    require(audit["raw_third_party_files_committed"] is False, "Phase 0 claims raw third-party files were committed")
    require(audit["required_source_failures"] == [], "required live source failure detected")

    rows = {row["id"]: row for row in audit["sources"]}
    expected = freeze["required_live_sources"]
    require(set(expected).issubset(rows), "required frozen source missing from regenerated audit")

    dam = rows["damodaran_us_returns"]
    dam_expected = expected["damodaran_us_returns"]
    require(dam["audit_status"] == "ok" and dam["required"] is True, "Damodaran required source not clean")
    require(dam["raw_sha256"] == dam_expected["raw_sha256"], "Damodaran raw source SHA changed")
    require(dam["raw_bytes"] == dam_expected["raw_bytes"], "Damodaran raw byte size changed")
    require(dam["parsed"]["first_year"] == dam_expected["first_year"], "Damodaran first year changed")
    require(dam["parsed"]["last_year"] == dam_expected["last_year"], "Damodaran last year changed")
    require(dam["parsed"]["numeric_year_rows"] == dam_expected["numeric_year_rows"], "Damodaran year-row count changed")
    require(not dam["etf"], "Damodaran unexpectedly marked ETF")

    jst = rows["jst_macrohistory_r6"]
    jst_expected = expected["jst_macrohistory_r6"]
    require(jst["audit_status"] == "ok" and jst["required"] is True, "JST required source not clean")
    require(jst["raw_sha256"] == jst_expected["raw_sha256"], "JST raw source SHA changed")
    require(jst["raw_bytes"] == jst_expected["raw_bytes"], "JST raw byte size changed")
    require(jst["parsed"]["first_year"] == jst_expected["first_year"], "JST first year changed")
    require(jst["parsed"]["last_year"] == jst_expected["last_year"], "JST last year changed")
    require(jst["parsed"]["usa_rows"] == jst_expected["usa_rows"], "JST USA row count changed")
    require(not jst["etf"], "JST unexpectedly marked ETF")

    observed_cov = jst["parsed"]["candidate_coverage"]
    for name, spec in jst_expected["usa_candidate_coverage"].items():
        require(name in observed_cov, f"JST frozen candidate missing: {name}")
        observed = observed_cov[name]
        for key in ("column", "usable_observations", "first_year", "last_year"):
            require(observed[key] == spec[key], f"JST {name}.{key} changed: {observed[key]} != {spec[key]}")

    require(all(row["etf"] is False for row in audit["sources"]), "one or more Phase 0 sources are marked ETF")
    require(freeze["phase1_gate"]["status"] == "not_started", "Phase 0 freeze must not imply Phase 1 results")

    return {
        "validated": True,
        "required_live_sources": list(expected),
        "damodaran_coverage": f"{dam['parsed']['first_year']}-{dam['parsed']['last_year']}",
        "jst_usa_coverage": f"{jst['parsed']['first_year']}-{jst['parsed']['last_year']}",
        "jst_equity_total_return": observed_cov["equity_total_return"],
        "jst_government_bond_total_return": observed_cov["government_bond_total_return"],
        "jst_real_gdp_per_capita_ppp_maddison": observed_cov["real_gdp_per_capita_ppp_maddison"],
        "jst_real_gdp_per_capita_index": observed_cov["real_gdp_per_capita_index"],
        "phase1_gate": freeze["phase1_gate"]["status"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Issue #91 Phase 0 durable source-freeze validation")
    parser.add_argument("--evidence-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(validate(args.evidence_dir), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
