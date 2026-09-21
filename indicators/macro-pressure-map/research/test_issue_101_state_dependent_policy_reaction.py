from __future__ import annotations
import numpy as np
import pandas as pd

from issue_101_state_dependent_policy_reaction import (
    causal_standardize, features, validate_prereg
)

def test_prereg():
    p=validate_prereg()
    assert p["created_before_model_outcomes"] is True
    assert p["created_before_treasury_outcomes"] is True

def test_m3_features_exact():
    f=features("Proxy","M3")
    assert f[-2:]==[
      "z_inflation_level_x_z_inflation_acceleration",
      "z_growth_level_x_z_growth_acceleration"
    ]

def test_causal_standardization_uses_training_only():
    n=30
    train=pd.DataFrame({
      "inflation_level_lag2":np.arange(n,dtype=float),
      "growth_level_lag2":np.arange(n,dtype=float)+10,
      "inflation_acceleration_lag2":np.arange(n,dtype=float)*.1,
      "growth_acceleration_lag2":np.arange(n,dtype=float)*-.2,
    })
    row=pd.Series({
      "inflation_level_lag2":999.,
      "growth_level_lag2":999.,
      "inflation_acceleration_lag2":99.,
      "growth_acceleration_lag2":-99.,
    })
    out,r,m=causal_standardize(train,row)
    assert np.isclose(m["inflation_level_lag2"]["mean"],14.5)
    assert r["z_inflation_level"]>10
    assert np.isclose(
      r["z_inflation_level_x_z_inflation_acceleration"],
      r["z_inflation_level"]*r["z_inflation_acceleration"]
    )
