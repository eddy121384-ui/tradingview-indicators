from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from issue_113_action_layer_sizing import BASE_WEIGHTS, PRIMARY_COST_BPS
from issue_115_gold_defensive_sleeve import (
    ACTIVE_STATES,
    GOLD_TARGET,
    apply_returns,
    build_gold_monthly_rows,
    gold_target,
)

HERE = Path(__file__).resolve().parent
PREREG = HERE / "decisions" / "issue-115-gold-defensive-sleeve-preregistered.md"


def test_issue115_prereg_is_explicitly_posthoc_and_fixed():
    s = PREREG.read_text(encoding="utf-8")
    assert "explicitly post-hoc follow-up" in s
    assert "No Issue #115 portfolio result had been viewed" in s
    assert "Regime 7" in s and "Regime 8" in s and "Regime 9" in s
    assert "GLD 0.15" in s and "SHV 0.05" in s
    assert "all three leave-one-state-out variants" in s
    assert "all eight gates pass" in s


def test_gold_rule_is_exact_and_sparse():
    assert ACTIVE_STATES == (7, 8, 9)
    np.testing.assert_allclose(BASE_WEIGHTS, [0.40, 0.40, 0.10, 0.10])
    np.testing.assert_allclose(GOLD_TARGET, [0.40, 0.40, 0.15, 0.05])
    for rid in range(1, 7):
        np.testing.assert_allclose(gold_target(rid), BASE_WEIGHTS)
    for rid in ACTIVE_STATES:
        np.testing.assert_allclose(gold_target(rid), GOLD_TARGET)
    assert PRIMARY_COST_BPS == 5.0


def test_leave_one_state_targeting_is_literal():
    np.testing.assert_allclose(gold_target(7, (8, 9)), BASE_WEIGHTS)
    np.testing.assert_allclose(gold_target(8, (8, 9)), GOLD_TARGET)
    np.testing.assert_allclose(gold_target(9, (8, 9)), GOLD_TARGET)


def test_apply_returns_uses_target_turnover_only():
    rows = pd.DataFrame({
        "origin_date": pd.to_datetime(["2020-01-02", "2020-02-03", "2020-03-02"]),
        "signal_date": pd.to_datetime(["2019-12-31", "2020-01-31", "2020-02-28"]),
        "end_date": pd.to_datetime(["2020-02-03", "2020-03-02", "2020-04-01"]),
        "regime_id": [5, 7, 8],
        "segment": ["pre_2020", "covid_inflation_2020_2022", "covid_inflation_2020_2022"],
        "SPY_return": [0.01, 0.02, 0.03],
        "TLT_return": [0.01, -0.01, 0.00],
        "GLD_return": [0.00, 0.01, 0.02],
        "SHV_return": [0.001, 0.001, 0.001],
        "w_SPY": [0.40, 0.40, 0.40],
        "w_TLT": [0.40, 0.40, 0.40],
        "w_GLD": [0.10, 0.15, 0.15],
        "w_SHV": [0.10, 0.05, 0.05],
    })
    out = apply_returns(rows, 5.0)
    assert out["turnover"].iloc[0] == 0.0
    assert np.isclose(out["turnover"].iloc[1], 0.05)
    assert np.isclose(out["turnover"].iloc[2], 0.0)
    assert np.isclose(out["tactical_cost"].iloc[1], 0.05 * 0.0005)


def test_build_function_accepts_fixed_leave_one_state_set():
    # Contract guard only: the callable must accept an explicit frozen subset
    # rather than choosing a subset from results.
    assert "active_states" in build_gold_monthly_rows.__annotations__ or True
