from __future__ import annotations

import json
from pathlib import Path

P=Path("decisions/issue-95-phase3-inflation-overlay-preregistered.json")


def load():
    return json.loads(P.read_text(encoding="utf-8"))


def test_prereg_is_pre_outcome_and_frozen() -> None:
    p=load()
    assert p["issue"]==95
    assert p["created_before_phase3_portfolio_outcomes"] is True
    assert p["production_v66_modified"] is False
    assert p["hmra_modified"] is False
    assert p["base_policy_modified"] is False


def test_primary_overlay_is_exactly_4pct_and_50pct_treasury_to_cash() -> None:
    p=load()
    assert p["overlay_rule"]["primary_treasury_redirect_fraction_to_cash"]==0.50
    assert ">= 4.0%" in p["overlay_rule"]["activation_condition"]
    assert p["sensitivity_discipline"]["primary"]=={
        "inflation_threshold_pct":4.0,
        "treasury_redirect_fraction":0.50,
        "cost_bps":5.0,
    }
    assert p["overlay_rule"]["diagnostic_redirect_sensitivities"]==[0.25,0.75]
    assert p["overlay_rule"]["sensitivity_selection_forbidden"] is True


def test_base_matrix_is_issue89_matrix_and_cash_zero() -> None:
    p=load()
    m=p["base_policy"]["matrix"]
    assert m["growth_high|inflation_low"]==[0.60,0.30,0.10]
    assert m["growth_high|inflation_high"]==[0.60,0.10,0.30]
    assert m["growth_neutral|inflation_neutral"]==[0.40,0.40,0.20]
    assert m["growth_low|inflation_low"]==[0.20,0.70,0.10]
    assert m["growth_low|inflation_high"]==[0.20,0.50,0.30]
    assert p["base_policy"]["cash_weight"]==0.0


def test_timing_and_gold_window_are_locked() -> None:
    p=load()
    s=p["sample_and_timing"]
    assert s["return_year_start"]==1975 and s["return_year_end"]==2025
    assert s["state_year_start"]==1973 and s["state_year_end"]==2023
    assert s["mapping"]=="HMRA state_t -> full-calendar-year return_t+2"
    assert s["return_year_inflation_forbidden"] is True


def test_matched_static_and_recent_rescue_guard_are_required() -> None:
    p=load()
    c=p["required_strategies_and_controls"]["realized_exposure_matched_static_control"]
    assert c["required"] is True
    assert c["fail_closed_tolerance"]==1e-9
    assert p["temporal_validation"]["compare_1975_1984_vs_2020_2025"] is True
    assert "recent_era_rescue_only" in p["temporal_validation"]["recent_era_rescue_guard"]


def test_verdict_categories_exact() -> None:
    p=load()
    assert p["verdict_categories"]==[
        "robust_inflation_conditioned_switching_value",
        "historical_risk_management_value_only",
        "recent_era_rescue_only",
        "allocation_mix_only_no_switching_value",
        "no_material_overlay_value",
        "inconclusive_insufficient_evidence",
    ]


def test_no_etf_and_no_threshold_shopping() -> None:
    p=load()
    assert p["primary_underlying_asset_source"]["etfs_used"] is False
    forbidden=" ".join(p["sensitivity_discipline"]["forbidden"]).lower()
    assert "threshold shopping" in forbidden
    assert "3%/5% inflation threshold rescue" in forbidden
