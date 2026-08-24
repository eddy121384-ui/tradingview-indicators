from __future__ import annotations

import numpy as np
import pandas as pd

from asset_allocation_phase_b_diagnostics import matched_weights, reconstruct_asset_returns


def test_matched_weights_preserve_gold_and_shift_only_spy_tlt() -> None:
    weights = matched_weights(0.25)
    assert np.isclose(weights["SPY"], 0.45)
    assert np.isclose(weights["TLT"], 0.35)
    assert np.isclose(weights["GLD"], 0.20)
    assert np.isclose(sum(weights.values()), 1.0)


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
