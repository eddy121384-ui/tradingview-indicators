from __future__ import annotations

import numpy as np
import pandas as pd

from asset_allocation_phase_a import (
    REGIMES,
    align_signal_and_prices,
    embargo_positions,
    forward_max_drawdown,
    forward_returns,
    regime_episode_rows,
    summarize_episodes,
)


def test_forward_returns_use_exact_trading_rows() -> None:
    index = pd.date_range("2024-01-01", periods=5, freq="D")
    prices = pd.DataFrame({"SPY": [100.0, 101.0, 102.0, 104.0, 108.0]}, index=index)
    result = forward_returns(prices, 2)
    assert np.isclose(result.loc[index[0], "SPY"], 0.02)
    assert np.isclose(result.loc[index[1], "SPY"], 104.0 / 101.0 - 1.0)
    assert pd.isna(result.loc[index[-1], "SPY"])


def test_embargo_positions_never_overlap_forward_windows() -> None:
    selected = embargo_positions([0, 1, 3, 4, 5, 8, 9], horizon=4)
    assert selected == [0, 4, 8]
    assert all(b - a >= 4 for a, b in zip(selected, selected[1:]))


def test_forward_max_drawdown_seeds_opening_equity() -> None:
    values = np.asarray([100.0, 90.0, 95.0, 80.0, 120.0])
    drawdown = forward_max_drawdown(values, start=0, horizon=4)
    assert np.isclose(drawdown, -0.20)


def test_regime_episodes_split_on_each_state_change() -> None:
    idx = pd.date_range("2024-01-01", periods=7, freq="D")
    regimes = pd.Series(
        [REGIMES[0], REGIMES[0], REGIMES[1], REGIMES[1], REGIMES[0], REGIMES[0], REGIMES[0]],
        index=idx,
    )
    rows = regime_episode_rows(regimes)
    assert rows["regime"].tolist() == [REGIMES[0], REGIMES[1], REGIMES[0]]
    assert rows["observations"].tolist() == [2, 2, 3]

    summary = summarize_episodes(regimes)
    first = summary.loc[summary["regime"].eq(REGIMES[0])].iloc[0]
    assert int(first["observations"]) == 5
    assert int(first["episodes"]) == 2
    assert np.isclose(first["duration_median_days"], 2.5)


def test_signal_price_alignment_uses_exact_intersection_and_finite_regime() -> None:
    signal_index = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"])
    history = pd.DataFrame(
        {
            "GPI": [1.0, 2.0, 3.0, 4.0],
            "IPI": [1.0, 2.0, 3.0, 4.0],
            "FCPI": [1.0, 2.0, 3.0, 4.0],
            "core_regime": [REGIMES[0], REGIMES[0], "n/a", REGIMES[1]],
        },
        index=signal_index,
    )
    price_index = pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"])
    prices = pd.DataFrame(
        {
            "SPY": [100.0, 101.0, 102.0, 103.0],
            "TLT": [90.0, 91.0, 92.0, 93.0],
            "GLD": [80.0, 81.0, 82.0, 83.0],
        },
        index=price_index,
    )
    aligned_history, aligned_prices = align_signal_and_prices(history, prices)
    expected = pd.to_datetime(["2024-01-02", "2024-01-04"])
    assert aligned_history.index.equals(expected)
    assert aligned_prices.index.equals(expected)
    assert aligned_prices.loc[pd.Timestamp("2024-01-04"), "SPY"] == 102.0
