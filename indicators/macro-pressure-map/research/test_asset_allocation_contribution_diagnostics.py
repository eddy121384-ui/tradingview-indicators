from __future__ import annotations

import numpy as np
import pandas as pd

from asset_allocation_contribution_diagnostics import build_contribution_tables

ASSETS = ["SPY", "TLT", "GLD"]


def test_contributions_reconcile_assets_costs_and_regimes() -> None:
    price_index = pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-06"])
    prices = pd.DataFrame(
        {
            "SPY": [100.0, 102.0, 101.0, 103.0],
            "TLT": [100.0, 100.0, 101.0, 100.0],
            "GLD": [100.0, 101.0, 102.0, 102.0],
        },
        index=price_index,
    )
    dates = price_index[1:]
    weights = np.asarray([0.50, 0.30, 0.20])
    returns = prices.pct_change(fill_method=None).loc[dates, ASSETS]
    gross = returns.to_numpy(float) @ weights
    cost_fraction = np.asarray([0.0, 0.0010, 0.0])
    net = (1.0 - cost_fraction) * (1.0 + gross) - 1.0

    daily = pd.DataFrame(
        {
            "date": dates,
            "strategy": "toy",
            "net_return": net,
            "gross_asset_mix_return": gross,
            "invested_weight_SPY": weights[0],
            "invested_weight_TLT": weights[1],
            "invested_weight_GLD": weights[2],
        }
    )
    executed = pd.Series(
        ["Regime A", "Regime A", "Regime B"],
        index=dates,
        name="executed_regime",
    )

    asset, regime, reconciliation = build_contribution_tables(
        daily,
        prices,
        executed,
        annualization=3,
    )
    full_asset = asset.loc[asset["segment"].eq("full_reused_history")]
    full_regime = regime.loc[regime["segment"].eq("full_reused_history")]
    full_recon = reconciliation.loc[reconciliation["segment"].eq("full_reused_history")].iloc[0]

    expected_ann = float(np.mean(net) * 3.0)
    assert np.isclose(full_asset["annualized_arithmetic_contribution"].sum(), expected_ann)
    assert np.isclose(full_regime["annualized_net_return_contribution"].sum(), expected_ann)
    assert np.isclose(full_recon["annualized_arithmetic_net_return"], expected_ann)
    assert abs(full_recon["asset_reconciliation_error"]) < 1e-12
    assert abs(full_recon["regime_reconciliation_error"]) < 1e-12

    regime_a = full_regime.loc[full_regime["executed_lagged_regime"].eq("Regime A")].iloc[0]
    assert regime_a["observations"] == 2
    assert np.isclose(regime_a["occupancy"], 2.0 / 3.0)
    assert np.isclose(regime_a["average_invested_weight_SPY"], 0.50)
    assert np.isclose(regime_a["average_invested_weight_TLT"], 0.30)
    assert np.isclose(regime_a["average_invested_weight_GLD"], 0.20)

    cost = full_asset.loc[full_asset["component"].eq("transaction_cost_residual")].iloc[0]
    expected_cost_residual = float((net - gross).mean() * 3.0)
    assert np.isclose(cost["annualized_arithmetic_contribution"], expected_cost_residual)


def test_asset_contribution_rejects_gross_return_mismatch() -> None:
    prices = pd.DataFrame(
        {"SPY": [100.0, 101.0], "TLT": [100.0, 100.0], "GLD": [100.0, 100.0]},
        index=pd.to_datetime(["2020-01-01", "2020-01-02"]),
    )
    daily = pd.DataFrame(
        {
            "date": [pd.Timestamp("2020-01-02")],
            "strategy": ["toy"],
            "net_return": [0.005],
            "gross_asset_mix_return": [0.999],
            "invested_weight_SPY": [0.5],
            "invested_weight_TLT": [0.3],
            "invested_weight_GLD": [0.2],
        }
    )
    executed = pd.Series(["Regime A"], index=pd.to_datetime(["2020-01-02"]))

    try:
        build_contribution_tables(daily, prices, executed)
    except ValueError as exc:
        assert "do not reproduce gross return" in str(exc)
    else:
        raise AssertionError("gross-return mismatch should fail closed")
