from __future__ import annotations
import json
from pathlib import Path

P=Path("decisions/issue-101-state-dependent-policy-reaction-preregistered.json")

def load(): return json.loads(P.read_text())

def test_preoutcome_boundary():
    p=load()
    assert p["created_before_model_outcomes"] is True
    assert p["created_before_treasury_outcomes"] is True
    assert p["production_v66_modified"] is False

def test_oos_and_timing_frozen():
    p=load()
    assert p["exact_oos_sample"]["first_forecast_origin"]=="1990-01"
    assert p["exact_oos_sample"]["last_forecast_origin"]=="2025-06"
    assert p["timing"]["horizon_months"]==6
    assert p["timing"]["macro_lag_months"]==2
    assert p["timing"]["acceleration_lookback_months"]==6

def test_m3_exact_interactions():
    p=load()
    f=p["models"]["M3"]["features"]
    assert f[-2:]==[
      "z_inflation_level_x_z_inflation_acceleration",
      "z_growth_level_x_z_growth_acceleration"
    ]
    assert "cross-axis interactions" in p["forbidden_model_changes"]

def test_causal_standardization():
    p=load()
    c=p["causal_standardization"]
    assert c["moments_source"]=="training rows only at each forecast origin"
    assert c["stance_controls_standardized"] is False

def test_stop_rule():
    p=load()
    assert "Treasury transmission remains closed" in p["stop_rule"]
