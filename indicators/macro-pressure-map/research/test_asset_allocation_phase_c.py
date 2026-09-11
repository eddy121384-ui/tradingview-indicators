from __future__ import annotations

import numpy as np
import pandas as pd

from asset_allocation_phase_c import (
    REFLATION_REGIME,
    STAGFLATION_REGIME,
    build_three_state_targets,
    load_contract,
)


def test_phase_c_contract_is_frozen_and_symmetric() -> None:
    contract = load_contract()
    assert contract["frozen_before_phase_c_portfolio_results_viewed"] is True
    assert contract["templates"]["neutral"] == {"SPY": 0.40, "TLT": 0.40, "GLD": 0.20}
    assert contract["templates"]["reflation"] == {"SPY": 0.60, "TLT": 0.20, "GLD": 0.20}
    assert contract["templates"]["stagflation"] == {"SPY": 0.20, "TLT": 0.40, "GLD": 0.40}
    assert contract["primary_cost_bps"] == 5.0


def test_phase_c_uses_one_row_lag_for_template_choice() -> None:
    index = pd.date_range("2020-01-02", periods=5, freq="B")
    regimes = pd.Series(
        [
            REFLATION_REGIME,
            STAGFLATION_REGIME,
            "Neutral / Range-bound Macro",
            STAGFLATION_REGIME,
            REFLATION_REGIME,
        ],
        index=index,
    )
    neutral = {"SPY": 0.40, "TLT": 0.40, "GLD": 0.20}
    reflation = {"SPY": 0.60, "TLT": 0.20, "GLD": 0.20}
    stag = {"SPY": 0.20, "TLT": 0.40, "GLD": 0.40}

    targets, template = build_three_state_targets(
        regimes,
        neutral=neutral,
        reflation=reflation,
        stagflation=stag,
        include_reflation=True,
        include_stagflation=True,
    )

    assert pd.isna(template.iloc[0])
    assert template.iloc[1] == "reflation"
    assert template.iloc[2] == "stagflation"
    assert template.iloc[3] == "neutral"
    assert template.iloc[4] == "stagflation"
    np.testing.assert_allclose(targets.iloc[1].to_numpy(float), [0.60, 0.20, 0.20])
    np.testing.assert_allclose(targets.iloc[2].to_numpy(float), [0.20, 0.40, 0.40])


def test_stagflation_only_does_not_modify_reflation_days() -> None:
    index = pd.date_range("2020-01-02", periods=4, freq="B")
    regimes = pd.Series(
        [REFLATION_REGIME, STAGFLATION_REGIME, REFLATION_REGIME, STAGFLATION_REGIME],
        index=index,
    )
    neutral = {"SPY": 0.40, "TLT": 0.40, "GLD": 0.20}
    reflation = {"SPY": 0.60, "TLT": 0.20, "GLD": 0.20}
    stag = {"SPY": 0.20, "TLT": 0.40, "GLD": 0.40}
    targets, template = build_three_state_targets(
        regimes,
        neutral=neutral,
        reflation=reflation,
        stagflation=stag,
        include_reflation=False,
        include_stagflation=True,
    )
    assert template.iloc[1] == "neutral"
    assert template.iloc[2] == "stagflation"
    np.testing.assert_allclose(targets.iloc[1].to_numpy(float), [0.40, 0.40, 0.20])
    np.testing.assert_allclose(targets.iloc[2].to_numpy(float), [0.20, 0.40, 0.40])
