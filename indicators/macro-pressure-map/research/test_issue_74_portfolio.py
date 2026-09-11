from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import asset_allocation_phase_b as issue64
import issue_74_portfolio as p74


def test_generic_simulator_matches_issue64_accounting_on_three_assets() -> None:
    index = pd.bdate_range("2021-01-04", periods=12)
    assets = ("SPY", "TLT", "GLD")
    returns = pd.DataFrame(
        {
            "SPY": np.linspace(-0.01, 0.012, len(index)),
            "TLT": np.linspace(0.006, -0.004, len(index)),
            "GLD": np.linspace(0.002, 0.005, len(index)),
        },
        index=index,
    )
    target = pd.DataFrame(np.tile([0.4, 0.4, 0.2], (len(index), 1)), index=index, columns=assets)
    target.loc[index[6]:, :] = [0.6, 0.2, 0.2]
    rebalance = pd.Series(False, index=index)
    rebalance.iloc[[0, 6, 10]] = True
    old = issue64.simulate_portfolio(returns, target, rebalance, cost_bps=5.0, name="old")
    new = p74.simulate_portfolio(returns, target, rebalance, cost_bps=5.0, name="new")
    columns = [
        "net_return",
        "gross_asset_mix_return",
        "wealth",
        "turnover",
        "cost_fraction",
        *[f"invested_weight_{a}" for a in assets],
        *[f"end_weight_{a}" for a in assets],
    ]
    np.testing.assert_allclose(old[columns].to_numpy(float), new[columns].to_numpy(float), atol=1e-15, rtol=0.0)


def test_four_asset_simulation_reconciles_daily_asset_mix() -> None:
    index = pd.bdate_range("2022-01-03", periods=8)
    assets = ("SPY", "TLT", "SHV", "GSG")
    returns = pd.DataFrame(
        {
            "SPY": [0.01, -0.02, 0.005, 0.0, 0.02, -0.01, 0.003, 0.004],
            "TLT": [-0.004, -0.005, 0.003, 0.002, -0.006, 0.004, 0.0, 0.001],
            "SHV": [0.0001] * 8,
            "GSG": [0.02, 0.01, -0.01, 0.03, -0.02, 0.015, 0.0, -0.005],
        },
        index=index,
    )
    target = pd.DataFrame(np.tile([0.2, 0.2, 0.4, 0.2], (8, 1)), index=index, columns=assets)
    rebalance = pd.Series(False, index=index)
    rebalance.iloc[[0, 4]] = True
    sim = p74.simulate_portfolio(returns, target, rebalance, cost_bps=5.0, name="four")
    for date in index:
        weights = sim.loc[date, [f"invested_weight_{a}" for a in assets]].to_numpy(float)
        expected = float(np.dot(weights, returns.loc[date, list(assets)].to_numpy(float)))
        assert sim.loc[date, "gross_asset_mix_return"] == pytest.approx(expected, abs=1e-15)


def test_core_targets_use_one_bar_lag() -> None:
    index = pd.bdate_range("2020-01-02", periods=5)
    regimes = pd.Series(
        ["Neutral", "Reflation", "Stagflation", "Neutral", "Neutral"],
        index=index,
    )
    targets, template = p74.build_core_regime_targets(
        regimes,
        assets=("SPY", "TLT", "SHV"),
        neutral={"SPY": 0.4, "TLT": 0.4, "SHV": 0.2},
        reflation={"SPY": 0.6, "TLT": 0.2, "SHV": 0.2},
        stagflation={"SPY": 0.2, "TLT": 0.2, "SHV": 0.6},
        reflation_regime="Reflation",
        stagflation_regime="Stagflation",
    )
    assert pd.isna(template.iloc[0])
    assert template.iloc[1] == "neutral"  # today's Reflation is not tradable today
    assert template.iloc[2] == "reflation"
    assert template.iloc[3] == "stagflation"
    np.testing.assert_allclose(targets.iloc[3].to_numpy(float), [0.2, 0.2, 0.6])


def test_severe_inflation_requires_lagged_stagflation_and_lagged_ipi_60() -> None:
    index = pd.bdate_range("2020-01-02", periods=6)
    regimes = pd.Series(["Neutral", "Stag", "Stag", "Stag", "Neutral", "Neutral"], index=index)
    ipi = pd.Series([0.0, 59.9, 60.0, 70.0, 80.0, 0.0], index=index)
    targets, template = p74.build_severe_inflation_targets(
        regimes,
        ipi,
        assets=("SPY", "TLT", "SHV", "GSG"),
        neutral={"SPY": 0.4, "TLT": 0.4, "SHV": 0.2, "GSG": 0.0},
        reflation={"SPY": 0.6, "TLT": 0.2, "SHV": 0.2, "GSG": 0.0},
        stagflation={"SPY": 0.2, "TLT": 0.2, "SHV": 0.6, "GSG": 0.0},
        severe_stagflation={"SPY": 0.2, "TLT": 0.2, "SHV": 0.4, "GSG": 0.2},
        reflation_regime="Refl",
        stagflation_regime="Stag",
        inflation_extreme_threshold=60.0,
    )
    assert template.iloc[2] == "stagflation"  # prior IPI was only 59.9
    assert template.iloc[3] == "severe_inflation_stagflation"  # prior IPI == 60 qualifies
    assert template.iloc[4] == "severe_inflation_stagflation"
    assert targets.iloc[3]["GSG"] == pytest.approx(0.2)
    assert targets.iloc[2]["GSG"] == pytest.approx(0.0)


def test_invalid_weight_sum_is_rejected() -> None:
    with pytest.raises(ValueError):
        p74.validate_weights({"SPY": 0.5, "TLT": 0.5, "SHV": 0.5}, ("SPY", "TLT", "SHV"), "bad")
