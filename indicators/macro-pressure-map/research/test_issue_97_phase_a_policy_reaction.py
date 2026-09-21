from __future__ import annotations
import numpy as np, pandas as pd
from issue_97_phase_a_policy_reaction import classify, balanced_accuracy, ols_fit_predict, validate_contracts

def test_contracts():
    p,f=validate_contracts()
    assert p["created_before_treasury_outcomes"] is True
    assert f["treasury_outcomes_seen"] is False

def test_policy_classes():
    assert classify(.251)=="tightening"
    assert classify(.25)=="neutral"
    assert classify(-.25)=="neutral"
    assert classify(-.251)=="easing"

def test_balanced_accuracy():
    a=pd.Series(["tightening","neutral","easing"])
    p=pd.Series(["tightening","neutral","easing"])
    assert balanced_accuracy(a,p)==1.0

def test_ols():
    x=np.arange(30,dtype=float)
    train=pd.DataFrame({"x":x,"y":1.0+2.0*x})
    row=pd.Series({"x":30.})
    pred,coef=ols_fit_predict(train,row,["x"],"y")
    assert np.isclose(pred,61.)
    assert np.isclose(coef["x"],2.)
