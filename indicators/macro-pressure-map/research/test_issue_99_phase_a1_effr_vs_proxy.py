from __future__ import annotations

import pandas as pd
from issue_99_phase_a1_effr_vs_proxy import (
    model_features, segment_label, validate_contracts
)

def test_contracts_preoutcome():
    p,pf,_,_=validate_contracts()
    assert p["created_before_A1_model_outcomes"] is True
    assert p["created_before_treasury_outcomes"] is True
    assert pf["model_outcomes_seen"] is False

def test_model_features_same_macro_terms():
    assert model_features("EFFR","M1")[-2:]==["inflation_level_lag2","growth_level_lag2"]
    assert model_features("Proxy","M2")[-4:]==[
      "inflation_level_lag2","growth_level_lag2",
      "inflation_acceleration_lag2","growth_acceleration_lag2"
    ]

def test_stance_controls_target_specific():
    assert model_features("EFFR","M1")[:2]==["effr","effr_6m_change_lag"]
    assert model_features("Proxy","M1")[:2]==["proxy_rate","proxy_6m_change_lag"]

def test_fixed_segments():
    assert segment_label(pd.Timestamp("2008-11-01"))=="Conventional_pre_Dec2008"
    assert segment_label(pd.Timestamp("2008-12-01"))=="Unconventional_post_Dec2008"
    assert segment_label(pd.Timestamp("2020-01-01"))=="Pandemic_and_postpandemic"
