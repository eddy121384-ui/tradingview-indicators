from __future__ import annotations

import numpy as np
import pandas as pd

from asset_allocation_phase_a import REGIMES
from asset_allocation_phase_b import template_change_mask
from issue_89_ex_ante_regime_policy import (
    build_policy_targets,
    load_contract,
)


def test_contract_is_frozen_non_return_fitted_and_complete() -> None:
    contract = load_contract()
    assert contract["frozen_before_issue_89_portfolio_results_viewed"] is True
    assert contract["return_fitted_weight_selection_allowed"] is False
    assert contract["weight_tuning_after_results_allowed"] is False
    assert contract["production_v66_parameters_modified"] is False
    assert set(contract["policy"]["matrix"]) == set(REGIMES)


def test_preregistered_matrix_matches_issue_89_policy() -> None:
    matrix = load_contract()["policy"]["matrix"]
    expected = {
        "Goldilocks / Disinflationary Expansion": [0.60, 0.30, 0.10],
        "Benign Expansion / Stable Inflation": [0.60, 0.20, 0.20],
        "Reflation / Inflation Rising": [0.60, 0.10, 0.30],
        "Disinflationary Drift": [0.40, 0.50, 0.10],
        "Neutral / Range-bound Macro": [0.40, 0.40, 0.20],
        "Inflation Pressure without Growth Confirmation": [0.40, 0.30, 0.30],
        "Slowdown / Disinflation": [0.20, 0.70, 0.10],
        "Growth Slowdown / Stable Inflation": [0.20, 0.60, 0.20],
        "Stagflation Pressure": [0.20, 0.50, 0.30],
    }
    for regime, weights in expected.items():
        actual = [matrix[regime][asset] for asset in ("SPY", "TLT", "GLD")]
        assert np.allclose(actual, weights, atol=0.0, rtol=0.0)
        assert np.isclose(sum(actual), 1.0, atol=1e-12)


def test_policy_uses_one_bar_lag() -> None:
    contract = load_contract()
    index = pd.date_range("2020-01-01", periods=4, freq="B")
    regimes = pd.Series(
        [
            "Neutral / Range-bound Macro",
            "Reflation / Inflation Rising",
            "Stagflation Pressure",
            "Goldilocks / Disinflationary Expansion",
        ],
        index=index,
    )
    targets, template = build_policy_targets(regimes, contract)
    assert pd.isna(template.iloc[0])
    assert template.iloc[1] == "Neutral / Range-bound Macro"
    assert template.iloc[2] == "Reflation / Inflation Rising"
    assert template.iloc[3] == "Stagflation Pressure"
    assert np.allclose(targets.iloc[1].to_numpy(float), [0.40, 0.40, 0.20])
    assert np.allclose(targets.iloc[2].to_numpy(float), [0.60, 0.10, 0.30])
    assert np.allclose(targets.iloc[3].to_numpy(float), [0.20, 0.50, 0.30])


def test_event_rebalance_occurs_when_lagged_policy_regime_changes() -> None:
    contract = load_contract()
    index = pd.date_range("2020-01-01", periods=5, freq="B")
    regimes = pd.Series(
        [
            "Neutral / Range-bound Macro",
            "Neutral / Range-bound Macro",
            "Reflation / Inflation Rising",
            "Reflation / Inflation Rising",
            "Stagflation Pressure",
        ],
        index=index,
    )
    _, template = build_policy_targets(regimes, contract)
    changed = template_change_mask(template)
    assert changed.tolist() == [False, False, False, True, False]
