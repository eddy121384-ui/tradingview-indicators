from __future__ import annotations

import numpy as np
import pandas as pd

from issue_95_phase3_inflation_overlay import (
    base_weights,
    overlay_weights,
    simulate,
    portfolio_metrics,
    validate_prereg,
)


def test_prereg_primary_locked() -> None:
    p=validate_prereg()
    assert p["sensitivity_discipline"]["primary"]=={
        "inflation_threshold_pct":4.0,
        "treasury_redirect_fraction":0.5,
        "cost_bps":5.0,
    }


def test_overlay_moves_only_treasury_to_cash() -> None:
    base=np.array([.2,.6,0,.2])
    out=overlay_weights(base,True,.5)
    assert np.allclose(out,[.2,.3,.3,.2])
    off=overlay_weights(base,False,.5)
    assert np.allclose(off,base)


def test_base_matrix_mapping() -> None:
    p=validate_prereg()
    assert np.allclose(base_weights("high","low",p),[.6,.3,0,.1])
    assert np.allclose(base_weights("low","high",p),[.2,.5,0,.3])


def test_annual_simulation_turnover_uses_drifted_weights() -> None:
    frame=pd.DataFrame({
        "return_year":[2000,2001],
        "equity":[.10,.00],"treasury":[0,0],"cash":[0,0],"gold":[0,0],
    })
    targets=pd.DataFrame(
        [[.5,.5,0,0],[.5,.5,0,0]],
        index=pd.Index([2000,2001],name="return_year"),columns=["equity","treasury","cash","gold"]
    )
    sim=simulate(frame,targets,0.0,"x")
    assert sim.loc[2000,"turnover"]==0
    assert sim.loc[2001,"turnover"]>0


def test_metrics_sharpe_uses_cash_excess() -> None:
    frame=pd.DataFrame({
        "return_year":[2000,2001,2002],
        "equity":[.10,.05,.08],"treasury":[.02,.02,.02],"cash":[.01,.01,.01],"gold":[.03,.03,.03],
    })
    targets=pd.DataFrame(
        np.tile([1,0,0,0],(3,1)),
        index=pd.Index([2000,2001,2002],name="return_year"),columns=["equity","treasury","cash","gold"]
    )
    sim=simulate(frame,targets,0.0,"x")
    m=portfolio_metrics(sim)
    assert np.isfinite(m["Sharpe_using_TBill"])
    assert m["observations"]==3
