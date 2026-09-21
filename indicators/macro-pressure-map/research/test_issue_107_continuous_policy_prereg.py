from __future__ import annotations
import json
from pathlib import Path

P=Path("decisions/issue-107-continuous-policy-reaction-preregistered.json")

def load():
    return json.loads(P.read_text(encoding="utf-8"))

def test_preoutcome_boundary():
    p=load()
    assert p["created_before_policy_outcomes"] is True
    assert p["created_before_display_formula"] is True
    assert p["production_v66_modified"] is False

def test_trajectory_is_existing_20_63_only():
    p=load()
    f=p["features"]
    assert f["fast_len"]==20
    assert f["mid_len"]==63
    assert f["formulas"]["acceleration_GPI"]=="fast_slope_GPI - mid_slope_GPI"
    assert f["formulas"]["acceleration_IPI"]=="fast_slope_IPI - mid_slope_IPI"

def test_policy_input_is_single_and_frozen():
    p=load()
    s=p["features"]["policy_starting_point"]
    assert s["formula"]=="FEDFUNDS_(m-2) - CorePCE_YoY_(m-2)"
    assert s["core_pce_source"]=="FRED PCEPILFE"
    assert s["lag_months"]==2

def test_model_ladder():
    p=load()
    assert p["model_ladder"]["M0"]["features"]==["GPI","IPI"]
    assert p["model_ladder"]["M1"]["features"]==["GPI","IPI","real_policy_rate"]
    assert len(p["model_ladder"]["M2"]["features"])==9

def test_primary_timing():
    p=load()
    m=p["monthly_sampling"]
    assert m["outcome"]=="FEDFUNDS_(m+6) - FEDFUNDS_m"
    assert m["primary_horizon_months"]==6
    assert p["estimation"]["initial_training_information_date"]=="2014-12"\n    assert p["estimation"]["first_oos_latest_eligible_training_origin"]=="2014-06"
    assert p["estimation"]["first_oos_origin"]=="2015-01"

def test_a1_cannot_authorize_production():
    p=load()
    assert p["data_gates"]["A1_public_feed_screening"]["can_authorize_production"] is False
    assert p["data_gates"]["A2_tradingview_feed_confirmation"]["can_authorize_phase_B"] is True

def test_display_remains_unwritten_and_uncategorized():
    p=load()
    b=p["phase_B_boundary"]
    assert b["formula_must_be_preregistered_after_phase_A"] is True
    assert b["categorical_labels_default"] is False
    assert b["thresholds_for_hawk_dove_forbidden"] is True

def test_no_asset_return_rescue():
    p=load()
    joined=" ".join(p["forbidden"]).lower()
    assert "treasury/equity/gold/etf returns" in joined
    assert "portfolio metrics" in joined
