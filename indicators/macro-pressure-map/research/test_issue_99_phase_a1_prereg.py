from __future__ import annotations
import json
from pathlib import Path

P=Path("decisions/issue-99-phase-a1-effr-vs-proxy-preregistered.json")
F=Path("decisions/issue-99-phase-a0-proxy-source-freeze.json")

def loadp(): return json.loads(P.read_text())
def loadf(): return json.loads(F.read_text())

def test_source_freeze():
    f=loadf()
    assert f["created_before_A1_model_outcomes"] is True
    c=f["canonical_monthly_through_2025_12"]
    assert c["first_month"]=="1976-06"
    assert c["last_month"]=="2025-12"
    assert c["observations"]==595
    assert c["canonical_sha256"]=="a797e085ff0dc9edb7da2e7b35e29db98ae5c11104189a179f52d6262401a413"

def test_a1_preoutcome_boundary():
    p=loadp()
    assert p["created_before_A1_model_outcomes"] is True
    assert p["created_before_treasury_outcomes"] is True
    assert p["production_v66_modified"] is False

def test_exact_common_sample():
    p=loadp()
    s=p["exact_common_sample"]
    assert s["oos_first_forecast_origin"]=="1990-01"
    assert s["oos_last_forecast_origin"]=="2025-06"
    assert s["primary_horizon_months"]==6

def test_models_unchanged_from_issue97():
    p=loadp()
    assert p["model_ladder"]["M1"]["macro_features"]==["inflation_level","growth_level"]
    assert p["model_ladder"]["M2"]["macro_features"]==[
      "inflation_level","growth_level","inflation_acceleration","growth_acceleration"
    ]
    assert p["macro_features"]["macro_month"]=="k = forecast month m - 2 months"

def test_boundary_and_verdicts():
    p=loadp()
    assert p["fixed_subperiods"][0]["end"]=="2008-11"
    assert p["fixed_subperiods"][1]["start"]=="2008-12"
    assert p["decision_categories"]==[
      "policy_measurement_explains_material_era_dependence",
      "policy_measurement_matters_but_speed_still_not_stable",
      "effr_measurement_not_the_main_problem",
      "inconclusive_proxy_rate_evidence"
    ]

def test_no_treasury():
    p=loadp()
    assert "Treasury-minus-cash outcomes" in p["forbidden"]
