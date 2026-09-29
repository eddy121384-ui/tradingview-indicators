from __future__ import annotations

import numpy as np
import pandas as pd

from issue_127_exact_reflation_translation import (
    ACTIVE,
    BASE,
    ACTIVE_REGIME,
    apply_returns,
    target_for_regime,
)


def test_only_regime_3_is_active():
    np.testing.assert_allclose(BASE, [0.40, 0.40, 0.10, 0.10])
    np.testing.assert_allclose(ACTIVE, [0.45, 0.35, 0.10, 0.10])
    assert ACTIVE_REGIME == 3
    for rid in range(1, 10):
        expected = ACTIVE if rid == 3 else BASE
        np.testing.assert_allclose(target_for_regime(rid), expected)


def test_5pp_enter_exit_turnover_and_cost():
    rows = pd.DataFrame({
        "origin_date": pd.to_datetime(["2020-01-02","2020-02-03","2020-03-02"]),
        "signal_date": pd.to_datetime(["2019-12-31","2020-01-31","2020-02-28"]),
        "end_date": pd.to_datetime(["2020-02-03","2020-03-02","2020-04-01"]),
        "regime_id": [5,3,5],
        "active": [False,True,False],
        "segment": ["pre_2020","covid_inflation_2020_2022","covid_inflation_2020_2022"],
        "SPY_return": [0.01,0.02,0.03],
        "TLT_return": [0.01,-0.01,0.00],
        "GLD_return": [0.00,0.01,0.02],
        "SHV_return": [0.001,0.001,0.001],
        "w_SPY": [0.40,0.45,0.40],
        "w_TLT": [0.40,0.35,0.40],
        "w_GLD": [0.10,0.10,0.10],
        "w_SHV": [0.10,0.10,0.10],
    })
    out = apply_returns(rows)
    np.testing.assert_allclose(out["turnover"].to_numpy(), [0.0,0.05,0.05])
    np.testing.assert_allclose(
        out["tactical_cost"].to_numpy(),
        [0.0, 0.05*0.0005, 0.05*0.0005],
    )
    assert np.isclose(
        out["gross_sleeve_contribution"].iloc[1],
        0.05 * (0.02 - (-0.01)),
    )


def test_non_active_month_has_zero_sleeve_contribution():
    rows = pd.DataFrame({
        "origin_date": pd.to_datetime(["2020-01-02"]),
        "signal_date": pd.to_datetime(["2019-12-31"]),
        "end_date": pd.to_datetime(["2020-02-03"]),
        "regime_id": [5],
        "active": [False],
        "segment": ["pre_2020"],
        "SPY_return": [0.02],
        "TLT_return": [-0.01],
        "GLD_return": [0.00],
        "SHV_return": [0.001],
        "w_SPY": [0.40],
        "w_TLT": [0.40],
        "w_GLD": [0.10],
        "w_SHV": [0.10],
    })
    out = apply_returns(rows)
    assert out["gross_sleeve_contribution"].iloc[0] == 0.0
