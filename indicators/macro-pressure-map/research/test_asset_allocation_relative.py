from __future__ import annotations

import numpy as np
import pandas as pd

from asset_allocation_phase_a import REGIMES
from asset_allocation_relative import summarize_relative_returns


def test_relative_spread_compares_same_start_date_asset_returns() -> None:
    index = pd.date_range("2020-01-01", periods=180, freq="B")
    step = np.arange(len(index), dtype=float)
    prices = pd.DataFrame(
        {
            "SPY": 100.0 * np.power(1.0020, step),
            "TLT": 100.0 * np.power(1.0005, step),
            "GLD": 100.0 * np.power(1.0010, step),
        },
        index=index,
    )
    history = pd.DataFrame({"core_regime": REGIMES[1]}, index=index)
    result = summarize_relative_returns(history, prices)
    row = result.loc[
        result["regime"].eq(REGIMES[1])
        & result["horizon"].eq("1M")
        & result["asset_a"].eq("SPY")
        & result["asset_b"].eq("TLT")
    ].iloc[0]
    expected = (1.0020**21 - 1.0) - (1.0005**21 - 1.0)
    assert np.isclose(row["mean_return_spread"], expected)
    assert np.isclose(row["embargoed_mean_return_spread"], expected)
    assert row["asset_a_outperformance_rate"] == 1.0
    assert row["mean_spread_ci95_low"] > 0.0
    assert row["ci_excludes_zero"]
