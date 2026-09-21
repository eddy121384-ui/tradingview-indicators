from __future__ import annotations
import json
from pathlib import Path

P=Path("decisions/issue-97-phase-a-policy-reaction-preregistered.json")

def load(): return json.loads(P.read_text())

def test_preoutcome_boundary():
    p=load()
    assert p["created_before_policy_model_outcomes"] is True
    assert p["created_before_treasury_outcomes"] is True
    assert p["production_v66_modified"] is False

def test_features_are_frozen():
    p=load()
    f=p["features"]
    assert f["growth_acceleration"]=="growth_level_k - growth_level_k-6"
    assert f["inflation_acceleration"]=="inflation_level_k - inflation_level_k-6"
    assert p["timestamps"]["macro_month"]=="k = m-2"

def test_model_ladder():
    p=load()
    assert p["model_ladder"]["M1"]["macro_features"]==["inflation_level","growth_level"]
    assert p["model_ladder"]["M2"]["macro_features"]==[
        "inflation_level","growth_level","inflation_acceleration","growth_acceleration"
    ]

def test_primary_outcome_and_labels():
    p=load()
    assert p["primary_outcome"]["formula"]=="EFFR_m+6 - EFFR_m"
    assert p["policy_direction_labels"]["tightening"]=="> +0.25 percentage point"
    assert p["policy_direction_labels"]["easing"]=="< -0.25 percentage point"

def test_phase_b_locked():
    p=load()
    assert p["phase_b_gate"]["treasury_outcome_may_be_loaded_only_after_phase_a_finding_is_durable"] is True
    assert "Treasury-minus-cash outcome before Phase A finding" in p["forbidden"]
