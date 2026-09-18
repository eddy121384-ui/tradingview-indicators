#!/usr/bin/env python3
"""Fail-closed completion validator for Issue #91 HMRA-v0.1 Phase 1."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
FREEZE = HERE / "decisions" / "issue-91-phase1-hmra-v0.1-source-freeze.json"
PREREG = HERE / "decisions" / "issue-91-phase1-hmra-v0.1-preregistered.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def validate(evidence_dir: Path) -> dict:
    freeze = load_json(FREEZE)
    prereg = load_json(PREREG)
    manifest = load_json(evidence_dir / "issue-91-hmra-v0.1-manifest.json")
    states_path = evidence_dir / "issue-91-hmra-v0.1-macro-states.csv"
    occupancy_path = evidence_dir / "issue-91-hmra-v0.1-occupancy.csv"
    states = pd.read_csv(states_path)
    occupancy = pd.read_csv(occupancy_path)

    require(freeze["issue"] == 91 and freeze["phase"] == "1-hmra-v0.1", "bad Phase 1 freeze identity")
    require(prereg["issue"] == 91 and prereg["phase"] == "1-hmra-v0.1-preregistration", "bad prereg identity")
    require(prereg["created_before_asset_conditioned_results"] is True, "prereg timing guard failed")
    require(freeze["created_before_asset_conditioned_results"] is True, "freeze timing guard failed")
    require(freeze["production_v66_modified"] is False and prereg["production_v66_modified"] is False, "production V6.6 boundary drift")
    require(freeze["exact_v66_claim"] is False and prereg["exact_v66_claim"] is False, "HMRA improperly relabeled exact V6.6")

    for key in ("asset_returns_loaded", "asset_conditioned_results_computed", "portfolio_results_computed"):
        require(manifest[key] is False, f"Phase 1 boundary violated: {key}")
        require(freeze[key] is False, f"freeze boundary violated: {key}")

    forbidden = ("equity", "treasury", "t_bill", "gold", "spy", "tlt", "gld", "asset_return")
    require(not any(any(token in c.lower() for token in forbidden) for c in states.columns), "asset outcome column leaked into macro state file")

    fed_expected = freeze["canonical_input_freeze"]["fed_ip"]
    fed_observed = manifest["sources"]["fed_ip"]
    require(fed_observed["series_code"] == fed_expected["series_code"], "Fed IP series changed")
    require(fed_observed["canonical_used_through_year"] == fed_expected["used_through_year"], "Fed IP cutoff changed")
    require(fed_observed["canonical_used_observations_sha256"] == fed_expected["canonical_used_observations_sha256"], "Fed IP canonical observations changed")
    require(fed_observed["canonical_used_observations_bytes"] == fed_expected["canonical_used_observations_bytes"], "Fed IP canonical byte count changed")

    cpi_expected = freeze["canonical_input_freeze"]["bls_cpi"]
    cpi_observed = manifest["sources"]["bls_cpi"]
    require(cpi_observed["series_code"] == cpi_expected["series_code"], "BLS CPI series changed")
    require(cpi_observed["canonical_observations_sha256"] == cpi_expected["canonical_observations_sha256"], "BLS CPI canonical observations changed")
    require(cpi_observed["canonical_observations_bytes"] == cpi_expected["canonical_observations_bytes"], "BLS CPI canonical byte count changed")

    evidence = freeze["generated_evidence_freeze"]
    require(sha256_file(states_path) == evidence["macro_states_csv"]["sha256"], "HMRA macro-state CSV changed")
    require(states_path.stat().st_size == evidence["macro_states_csv"]["bytes"], "HMRA macro-state CSV size changed")
    require(sha256_file(occupancy_path) == evidence["occupancy_csv"]["sha256"], "HMRA occupancy CSV changed")
    require(occupancy_path.stat().st_size == evidence["occupancy_csv"]["bytes"], "HMRA occupancy CSV size changed")

    coverage = freeze["coverage_and_diagnostics"]
    require(manifest["annual_overlap"] == coverage["annual_overlap"], "annual overlap changed")
    for key, expected in coverage["primary_valid_states"].items():
        require(manifest["primary_valid_states"][key] == expected, f"primary valid-state {key} changed")

    observed_occ = dict(zip(occupancy["core_regime"], occupancy["years"].astype(int)))
    require(observed_occ == coverage["regime_occupancy"], "regime occupancy changed")
    require(len(observed_occ) == 9 and coverage["all_nine_cells_observed"] is True, "not all nine HMRA cells observed")

    sens = manifest["sensitivity_10y"]
    sens_expected = coverage["sensitivity_10y"]
    require(sens["comparable_years"] == sens_expected["comparable_years"], "10y comparable-year count changed")
    require(abs(float(sens["exact_regime_agreement_rate"]) - float(sens_expected["exact_regime_agreement_rate"])) <= 1e-12, "10y agreement changed")
    require(sens["diagnostic_only"] is True, "10y sensitivity ceased to be diagnostic only")

    rules = freeze["model_rule_freeze"]
    require(prereg["score_rule"]["primary_reference_window_years"] == rules["primary_reference_window_years"], "primary lookback drift")
    require(prereg["score_rule"]["sensitivity_reference_window_years"] == rules["sensitivity_reference_window_years"], "sensitivity lookback drift")
    require(prereg["state_thresholds"]["threshold_values"]["low"] == rules["low_threshold"], "low threshold drift")
    require(prereg["state_thresholds"]["threshold_values"]["high"] == rules["high_threshold"], "high threshold drift")
    require(prereg["phase2_pairing_rules"]["strict_causal_primary"]["mapping"] == "HMRA state_t -> full-calendar-year asset return_t+2", "causal timing contract drift")
    require(manifest["timing"]["strict_causal_return_year_offset"] == rules["strict_causal_return_year_offset"], "causal timing offset changed")

    require(freeze["phase2_gate"]["status"] == "blocked_until_separate_preregistration", "Phase 2 gate unexpectedly opened")

    return {
        "validated": True,
        "primary_state_coverage": f"{manifest['primary_valid_states']['first_year']}-{manifest['primary_valid_states']['last_year']}",
        "primary_state_years": manifest["primary_valid_states"]["years"],
        "all_nine_cells_observed": True,
        "ten_year_exact_regime_agreement": sens["exact_regime_agreement_rate"],
        "phase2_gate": freeze["phase2_gate"]["status"],
        "asset_outcomes_seen": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Issue #91 HMRA-v0.1 durable Phase 1 freeze")
    parser.add_argument("--evidence-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(validate(args.evidence_dir), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
