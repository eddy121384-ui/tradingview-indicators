from __future__ import annotations

import numpy as np
import pandas as pd

from asset_allocation_phase_b import month_start_mask, simulate_portfolio, weights_series
from asset_allocation_phase_b_diagnostics import (
    lagged_reflation_status,
    mean_invested_weights,
    reconstruct_asset_returns,
    solve_static_target_for_realized_average,
)

ASSETS = ("SPY", "TLT", "GLD")


def test_asset_return_reconstruction_recovers_known_returns() -> None:
    date = pd.Timestamp("2020-01-02")
    true_returns = np.asarray([0.01, -0.005, 0.002])
    specifications = {
        "fixed_60_40": np.asarray([0.60, 0.40, 0.00]),
        "fixed_equal_weight": np.asarray([1 / 3, 1 / 3, 1 / 3]),
        "fixed_neutral_40_40_20": np.asarray([0.40, 0.40, 0.20]),
    }
    rows = []
    for strategy, weights in specifications.items():
        rows.append({
            "date": date,
            "strategy": strategy,
            "gross_asset_mix_return": float(weights @ true_returns),
            "invested_weight_SPY": weights[0],
            "invested_weight_TLT": weights[1],
            "invested_weight_GLD": weights[2],
        })
    recovered, residual = reconstruct_asset_returns(pd.DataFrame(rows))
    assert residual < 1e-12
    assert np.allclose(recovered.iloc[0].to_numpy(float), true_returns)


def test_lagged_reflation_status_accepts_microsecond_precision_index() -> None:
    index = pd.DatetimeIndex(
        np.asarray(["2007-01-04", "2007-01-05", "2007-01-08"], dtype="datetime64[us]")
    )
    assert str(index.dtype) == "datetime64[us]"
    status = lagged_reflation_status(index)
    assert status.index.equals(index)
    assert status.dtype == bool
    assert len(status) == len(index)


def test_realized_exposure_solver_matches_invested_weight_average() -> None:
    index = pd.date_range("2020-01-02", periods=140, freq="B")
    x = np.arange(len(index), dtype=float)
    returns = pd.DataFrame(
        {
            "SPY": 0.0004 + 0.006 * np.sin(x / 11.0),
            "TLT": 0.0002 + 0.004 * np.cos(x / 13.0),
            "GLD": 0.0001 + 0.005 * np.sin(x / 17.0 + 0.4),
        },
        index=index,
    )
    known = {"SPY": 0.45, "TLT": 0.35, "GLD": 0.20}
    known_sim = simulate_portfolio(
        returns,
        weights_series(known, index),
        month_start_mask(index),
        cost_bps=5.0,
        name="known",
    )
    desired = mean_invested_weights(known_sim)
    solved, solved_sim, meta = solve_static_target_for_realized_average(
        returns,
        desired,
        cost_bps=5.0,
        name="solved",
    )
    actual = mean_invested_weights(solved_sim)
    assert np.allclose([solved[a] for a in ASSETS], [known[a] for a in ASSETS], atol=1e-9)
    assert np.allclose([actual[a] for a in ASSETS], [desired[a] for a in ASSETS], atol=1e-10)
    assert meta["max_abs_invested_weight_mismatch"] < 1e-10
