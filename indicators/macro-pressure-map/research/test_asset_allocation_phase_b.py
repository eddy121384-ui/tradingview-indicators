from __future__ import annotations

import numpy as np
import pandas as pd

from asset_allocation_phase_b import (
    build_reflation_targets,
    causal_inverse_vol_targets,
    month_start_mask,
    portfolio_metrics,
    simulate_portfolio,
    template_change_mask,
)

ASSETS = ["SPY", "TLT", "GLD"]
NEUTRAL = {"SPY": 0.40, "TLT": 0.40, "GLD": 0.20}
REFLATION = {"SPY": 0.60, "TLT": 0.20, "GLD": 0.20}


def test_reflation_target_uses_one_bar_lag() -> None:
    idx = pd.date_range("2020-01-01", periods=4, freq="B")
    regimes = pd.Series(
        ["Neutral", "Reflation / Inflation Rising", "Reflation / Inflation Rising", "Neutral"],
        index=idx,
    )
    targets, template = build_reflation_targets(
        regimes,
        NEUTRAL,
        REFLATION,
        "Reflation / Inflation Rising",
    )
    assert pd.isna(template.iloc[0])
    assert template.iloc[1] == "neutral"
    assert template.iloc[2] == "reflation"
    assert np.allclose(targets.iloc[2].to_numpy(float), [0.60, 0.20, 0.20])
    assert template.iloc[3] == "reflation"


def test_non_reflation_regime_change_does_not_change_template() -> None:
    idx = pd.date_range("2020-01-01", periods=5, freq="B")
    regimes = pd.Series(["A", "B", "C", "D", "E"], index=idx)
    _, template = build_reflation_targets(regimes, NEUTRAL, REFLATION, "Reflation / Inflation Rising")
    changed = template_change_mask(template)
    assert not changed.any()


def test_month_start_mask_uses_first_common_trading_day() -> None:
    idx = pd.to_datetime(["2020-01-30", "2020-01-31", "2020-02-03", "2020-02-04", "2020-03-02"])
    mask = month_start_mask(idx)
    assert mask.tolist() == [True, False, True, False, True]


def test_turnover_is_measured_against_drifted_pretrade_weights() -> None:
    idx = pd.to_datetime(["2020-01-02", "2020-01-03"])
    returns = pd.DataFrame([[0.10, 0.0, 0.0], [0.0, 0.0, 0.0]], index=idx, columns=ASSETS)
    targets = pd.DataFrame([[0.4, 0.4, 0.2], [0.4, 0.4, 0.2]], index=idx, columns=ASSETS)
    rebalance = pd.Series([True, True], index=idx)
    sim = simulate_portfolio(returns, targets, rebalance, cost_bps=0.0, name="test")
    drifted = np.asarray([0.44, 0.40, 0.20]) / 1.04
    expected = 0.5 * np.abs(np.asarray([0.4, 0.4, 0.2]) - drifted).sum()
    assert np.isclose(sim.iloc[1]["turnover"], expected)
    assert sim.iloc[0]["turnover"] == 0.0
    assert not bool(sim.iloc[0]["trade"])


def test_transaction_cost_is_deducted_only_after_initialization() -> None:
    idx = pd.to_datetime(["2020-01-02", "2020-01-03"])
    returns = pd.DataFrame(0.0, index=idx, columns=ASSETS)
    targets = pd.DataFrame([[0.4, 0.4, 0.2], [0.6, 0.2, 0.2]], index=idx, columns=ASSETS)
    rebalance = pd.Series([True, True], index=idx)
    sim = simulate_portfolio(returns, targets, rebalance, cost_bps=100.0, name="test")
    expected_turnover = 0.20
    expected_cost = expected_turnover * 100.0 / 10000.0
    assert np.isclose(sim.iloc[1]["turnover"], expected_turnover)
    assert np.isclose(sim.iloc[1]["cost_fraction"], expected_cost)
    assert np.isclose(sim.iloc[-1]["wealth"], 1.0 - expected_cost)


def test_inverse_volatility_target_uses_only_returns_through_previous_row() -> None:
    idx = pd.date_range("2020-01-01", periods=6, freq="B")
    returns = pd.DataFrame(
        {
            "SPY": [0.01, -0.01, 0.02, 0.50, 0.00, 0.00],
            "TLT": [0.02, -0.02, 0.01, 0.00, 0.00, 0.00],
            "GLD": [0.03, -0.01, 0.00, 0.00, 0.00, 0.00],
        },
        index=idx,
    )
    targets = causal_inverse_vol_targets(returns, lookback=3)
    # At row 4 (index position 3), the estimate uses positions 0..2 only;
    # the 50% SPY return on that same row must not affect today's target.
    prior = returns.iloc[0:3].std(ddof=1)
    expected = (1.0 / prior) / (1.0 / prior).sum()
    assert np.allclose(targets.iloc[3].to_numpy(float), expected.to_numpy(float))


def test_template_change_occurs_only_when_lagged_reflation_status_changes() -> None:
    idx = pd.date_range("2020-01-01", periods=6, freq="B")
    regimes = pd.Series(
        ["A", "Reflation / Inflation Rising", "Reflation / Inflation Rising", "B", "C", "Reflation / Inflation Rising"],
        index=idx,
    )
    _, template = build_reflation_targets(regimes, NEUTRAL, REFLATION, "Reflation / Inflation Rising")
    changed = template_change_mask(template)
    assert changed.tolist() == [False, False, True, False, True, False]


def test_drawdown_includes_loss_from_segment_starting_wealth() -> None:
    idx = pd.to_datetime(["2020-01-02", "2020-01-03"])
    sim = pd.DataFrame(
        {
            "net_return": [-0.10, 0.05],
            "turnover": [0.0, 0.0],
            "cost_fraction": [0.0, 0.0],
            "gross_asset_mix_return": [-0.10, 0.05],
            "trade": [False, False],
            "invested_weight_SPY": [0.4, 0.4],
            "invested_weight_TLT": [0.4, 0.4],
            "invested_weight_GLD": [0.2, 0.2],
        },
        index=idx,
    )
    metrics = portfolio_metrics(sim)
    assert np.isclose(metrics["maximum_drawdown"], -0.10)
