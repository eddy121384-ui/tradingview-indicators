from __future__ import annotations

import numpy as np
import pandas as pd

from issue_123_reflation_policy_rematch import (
    ACTIVE,
    BASE,
    REFLATION,
    apply_targets,
    broad_era,
    portfolio_metrics,
    target_for_regime,
)


def test_targets_are_exact():
    np.testing.assert_allclose(BASE, [0.50, 0.50])
    np.testing.assert_allclose(ACTIVE, [0.55, 0.45])
    np.testing.assert_allclose(target_for_regime(REFLATION), ACTIVE)
    np.testing.assert_allclose(target_for_regime("Neutral / Range-bound Macro"), BASE)


def test_broad_eras_are_frozen():
    assert broad_era(1928) == "1928_1945"
    assert broad_era(1945) == "1928_1945"
    assert broad_era(1946) == "1946_1979"
    assert broad_era(1980) == "1980_1999"
    assert broad_era(2000) == "2000_2023"
    assert broad_era(2023) == "2000_2023"


def test_turnover_for_enter_exit_5pp_tilt():
    rows = pd.DataFrame({
        "return_year":[2000,2001,2002],
        "equity":[0.1,0.1,0.1],
        "treasury":[0.05,0.05,0.05],
        "cash":[0.02,0.02,0.02],
        "w_equity":[0.50,0.55,0.50],
        "w_treasury":[0.50,0.45,0.50],
        "active":[False,True,False],
    })
    out = apply_targets(rows)
    np.testing.assert_allclose(out["turnover"].to_numpy(), [0.0,0.05,0.05])
    np.testing.assert_allclose(
        out["tactical_cost"].to_numpy(),
        [0.0, 0.05*0.0005, 0.05*0.0005],
    )


def test_portfolio_metrics_cagr_matches_terminal_wealth():
    r=np.array([0.10,0.0,-0.05,0.08])
    rf=np.array([0.02,0.02,0.02,0.02])
    m=portfolio_metrics(r,rf)
    expected=np.prod(1+r)**(1/4)-1
    assert np.isclose(m["cagr"],expected)
    assert np.isclose(m["terminal_wealth"],np.prod(1+r))
