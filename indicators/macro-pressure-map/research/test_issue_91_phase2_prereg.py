from __future__ import annotations

import json
from pathlib import Path


def test_phase2_prereg_is_pre_outcome_and_no_portfolio() -> None:
    p=json.loads(Path("decisions/issue-91-phase2-asset-validation-preregistered.json").read_text())
    assert p["issue"] == 91
    assert p["created_before_phase2_asset_outcomes"] is True
    assert p["portfolio_policy_test_in_this_phase"] is False
    assert p["production_v66_modified"] is False
    assert p["pairings"]["strict_causal_primary"]["return_year"] == "t+2"
    assert p["gold_boundary"]["primary_investable_gold_start_year"] == 1975


def test_primary_asset_source_is_non_etf_and_frozen() -> None:
    p=json.loads(Path("decisions/issue-91-phase2-asset-validation-preregistered.json").read_text())
    source=p["primary_asset_source"]
    assert "damodaran" in source["id"]
    assert source["frozen_raw_sha256_from_phase0"] == "127c772f0fea8763391dbf2c1c7d3ecd3a07ca2b23f81ab47af58b529e2b5647"
    cols=source["exact_columns"]
    assert cols["equity"] == "S&P 500 (includes dividends)"
    assert cols["treasury"] == "US T. Bond (10-year)"
    assert cols["cash"] == "3-month T.Bill"
    assert cols["gold"] == "Gold*"
    joined=" ".join(cols.values()).lower()
    assert all(token not in joined for token in ("spy","tlt","gld"))


def test_absolute_inflation_split_and_era_boundaries_are_frozen() -> None:
    p=json.loads(Path("decisions/issue-91-phase2-asset-validation-preregistered.json").read_text())
    groups=p["absolute_inflation_regime_test"]["frozen_background_groups"]
    assert groups[0]["label"] == "below_4pct"
    assert groups[1]["label"] == "at_or_above_4pct"
    eras=p["era_definitions"]
    assert eras[2] == {"label":"Great_Inflation_pre_Volcker","start":1971,"end":1979}
    assert eras[-1] == {"label":"Higher_rate_disinflation","start":2023,"end":2025}


def test_verdict_categories_are_exact_and_no_winner_score() -> None:
    p=json.loads(Path("decisions/issue-91-phase2-asset-validation-preregistered.json").read_text())
    assert p["phase2_structural_verdict_categories"] == [
        "structurally_stable_mapping",
        "inflation_regime_dependent_mapping",
        "monetary_regime_dependent_mapping",
        "asset_mapping_unstable",
        "inconclusive_long_history_evidence",
    ]
    assert "Do not rank" in p["regime_stability_tests"]["no_winner_ranking_rule"]
