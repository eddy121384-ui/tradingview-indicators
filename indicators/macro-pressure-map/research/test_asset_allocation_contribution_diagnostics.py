from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from asset_allocation_contribution_diagnostics import (
    build_contribution_tables,
    validate_phase_c_durable_contribution_audit,
)

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


def test_phase_c_durable_audit_rejects_value_drift_even_when_reconciliation_is_zero() -> None:
    asset = pd.DataFrame(
        [
            {"strategy": "phase_c_combined", "segment": "full_reused_history", "component": "SPY", "annualized_arithmetic_contribution": 0.10},
            {"strategy": "phase_c_combined", "segment": "full_reused_history", "component": "TLT", "annualized_arithmetic_contribution": 0.20},
            {"strategy": "phase_c_combined", "segment": "full_reused_history", "component": "GLD", "annualized_arithmetic_contribution": 0.30},
            {"strategy": "phase_c_combined", "segment": "full_reused_history", "component": "transaction_cost_residual", "annualized_arithmetic_contribution": -0.01},
        ]
    )
    regime = pd.DataFrame(
        [
            {
                "strategy": "phase_c_combined",
                "segment": "full_reused_history",
                "executed_lagged_regime": "Stagflation Pressure",
                "average_invested_weight_SPY": 0.20,
                "average_invested_weight_TLT": 0.40,
                "average_invested_weight_GLD": 0.40,
                "annualized_net_return_contribution": -0.05,
            },
            {
                "strategy": "phase_c_combined",
                "segment": "full_reused_history",
                "executed_lagged_regime": "Reflation / Inflation Rising",
                "annualized_net_return_contribution": 0.08,
            },
            {
                "strategy": "phase_c_combined",
                "segment": "full_reused_history",
                "executed_lagged_regime": "Slowdown / Disinflation",
                "annualized_net_return_contribution": 0.06,
            },
            {
                "strategy": "phase_b_reflation_only",
                "segment": "full_reused_history",
                "executed_lagged_regime": "Stagflation Pressure",
                "annualized_net_return_contribution": -0.07,
            },
        ]
    )
    reconciliation = pd.DataFrame(
        [
            {
                "strategy": "phase_c_combined",
                "segment": "full_reused_history",
                "annualized_arithmetic_net_return": 0.59,
                "asset_reconciliation_error": 0.0,
                "regime_reconciliation_error": 0.0,
            }
        ]
    )
    decision = {
        "schema_version": 5,
        "regenerated_evidence_binding": {"contribution_value_tolerance": 1e-12},
        "portfolio_contribution_audit": {
            "full_history_phase_c_combined": {
                "annualized_arithmetic_net_return": 0.59,
                "annualized_asset_contribution": {"SPY": 0.10, "TLT": 0.20, "GLD": 0.30},
                "annualized_transaction_cost_residual": -0.01,
                "stagflation_realized_average_allocation": {"SPY": 0.20, "TLT": 0.40, "GLD": 0.40},
                "stagflation_annualized_net_return_contribution": -0.05,
                "reflation_annualized_net_return_contribution": 0.08,
                "slowdown_disinflation_annualized_net_return_contribution": 0.06,
            },
            "full_history_phase_b_stagflation_regime_contribution": -0.07,
            "stagflation_regime_contribution_improvement_vs_phase_b": 0.02,
        },
    }

    validated = validate_phase_c_durable_contribution_audit(asset, regime, reconciliation, decision)
    assert validated["validated"] is True
    assert validated["max_abs_error"] < 1e-15

    drifted = regime.copy()
    drifted.loc[drifted["executed_lagged_regime"].eq("Stagflation Pressure") & drifted["strategy"].eq("phase_c_combined"), "annualized_net_return_contribution"] = -0.04
    drifted.loc[drifted["executed_lagged_regime"].eq("Reflation / Inflation Rising"), "annualized_net_return_contribution"] = 0.07

    with pytest.raises(RuntimeError, match="durable contribution audit drifted"):
        validate_phase_c_durable_contribution_audit(asset, drifted, reconciliation, decision)

    original_expected = decision["portfolio_contribution_audit"]["full_history_phase_c_combined"]["stagflation_annualized_net_return_contribution"]
    decision["portfolio_contribution_audit"]["full_history_phase_c_combined"]["stagflation_annualized_net_return_contribution"] = float("nan")
    with pytest.raises(ValueError, match="non-finite durable contribution value"):
        validate_phase_c_durable_contribution_audit(asset, regime, reconciliation, decision)
    decision["portfolio_contribution_audit"]["full_history_phase_c_combined"]["stagflation_annualized_net_return_contribution"] = original_expected

    nonfinite_observed = regime.copy()
    nonfinite_observed.loc[
        nonfinite_observed["executed_lagged_regime"].eq("Stagflation Pressure")
        & nonfinite_observed["strategy"].eq("phase_c_combined"),
        "annualized_net_return_contribution",
    ] = np.inf
    with pytest.raises(ValueError, match="non-finite durable contribution value"):
        validate_phase_c_durable_contribution_audit(asset, nonfinite_observed, reconciliation, decision)

    decision["regenerated_evidence_binding"]["contribution_value_tolerance"] = float("nan")
    with pytest.raises(ValueError, match="tolerance must be finite and positive"):
        validate_phase_c_durable_contribution_audit(asset, regime, reconciliation, decision)
