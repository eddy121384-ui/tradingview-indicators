from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from issue_113_action_layer_sizing import (
    ASSETS,
    BASE_WEIGHTS,
    PRIMARY_COST_BPS,
    TARGETS,
    first_rows_each_month,
    identify_active_episodes,
    portfolio_metrics,
    recompute_action_returns,
    target_for_regime,
)

HERE = Path(__file__).resolve().parent
PREREG = HERE / "decisions" / "issue-113-action-layer-sizing-preregistered.md"


def test_issue113_prereg_exists_and_freezes_core_design():
    s = PREREG.read_text(encoding="utf-8")
    assert "No Issue #113 portfolio result had been viewed" in s
    assert "SPY 0.40" in s
    assert "TLT 0.40" in s
    assert "GLD 0.10" in s
    assert "SHV 0.10" in s
    assert "+5pp" in s
    assert "5 basis points" in s or "0.0005" in s
    assert "+/-2 tier" in s.lower()
    assert "all seven production gates pass" in s


def test_issue113_target_map_is_exact_and_sparse():
    np.testing.assert_allclose(BASE_WEIGHTS, [0.40, 0.40, 0.10, 0.10])
    np.testing.assert_allclose(TARGETS[7], [0.40, 0.40, 0.15, 0.05])
    np.testing.assert_allclose(TARGETS[8], [0.45, 0.35, 0.15, 0.05])
    np.testing.assert_allclose(TARGETS[9], [0.40, 0.40, 0.15, 0.05])
    for rid in range(1, 7):
        np.testing.assert_allclose(target_for_regime(rid), BASE_WEIGHTS)
    assert set(TARGETS) == {7, 8, 9}
    assert PRIMARY_COST_BPS == 5.0
    assert ASSETS == ("SPY", "TLT", "GLD", "SHV")


def test_first_rows_each_month():
    idx = pd.to_datetime([
        "2020-01-02", "2020-01-03", "2020-01-31",
        "2020-02-03", "2020-02-28", "2020-03-02",
    ])
    assert first_rows_each_month(idx) == [0, 3, 5]


def test_tactical_turnover_uses_target_changes_only():
    rows = pd.DataFrame({
        "origin_date": pd.to_datetime(["2020-01-02", "2020-02-03", "2020-03-02"]),
        "signal_date": pd.to_datetime(["2019-12-31", "2020-01-31", "2020-02-28"]),
        "end_date": pd.to_datetime(["2020-02-03", "2020-03-02", "2020-04-01"]),
        "regime_id": [5, 8, 7],
        "regime": ["n", "r8", "r7"],
        "segment": ["pre_2020", "covid_inflation_2020_2022", "covid_inflation_2020_2022"],
        "SPY_return": [0.01, 0.02, 0.03],
        "TLT_return": [0.01, -0.01, 0.00],
        "GLD_return": [0.00, 0.01, 0.02],
        "SHV_return": [0.001, 0.001, 0.001],
        "w_SPY": [0.40, 0.45, 0.40],
        "w_TLT": [0.40, 0.35, 0.40],
        "w_GLD": [0.10, 0.15, 0.15],
        "w_SHV": [0.10, 0.05, 0.05],
    })
    out = recompute_action_returns(rows, 5.0)
    assert out["turnover"].iloc[0] == 0.0
    assert np.isclose(out["turnover"].iloc[1], 0.10)
    assert np.isclose(out["turnover"].iloc[2], 0.05)
    assert np.isclose(out["tactical_cost"].iloc[1], 0.10 * 0.0005)


def test_episode_definition_is_target_vector_based():
    rows = pd.DataFrame({
        "origin_date": pd.to_datetime(["2020-01-02", "2020-02-03", "2020-03-02", "2020-04-01"]),
        "regime_id": [7, 9, 5, 8],
        "al_net_return": [0.01, 0.02, 0.0, 0.03],
        "c0_return": [0.0, 0.0, 0.0, 0.0],
        "w_SPY": [0.40, 0.40, 0.40, 0.45],
        "w_TLT": [0.40, 0.40, 0.40, 0.35],
        "w_GLD": [0.15, 0.15, 0.10, 0.15],
        "w_SHV": [0.05, 0.05, 0.10, 0.05],
    })
    eps = identify_active_episodes(rows)
    assert len(eps) == 2
    assert eps.iloc[0]["months"] == 2
    assert np.isclose(eps.iloc[0]["contribution_sum"], 0.03)


def test_portfolio_metrics_are_monthly_and_cash_excess():
    r = np.array([0.01] * 12)
    cash = np.array([0.002] * 12)
    m = portfolio_metrics(r, cash)
    assert m["n"] == 12
    assert m["cagr"] > 0.12
    assert m["terminal_wealth"] > 1.12
