from __future__ import annotations

import numpy as np
import pandas as pd

from asset_allocation_phase_b import month_start_mask, simulate_portfolio, template_change_mask
from asset_allocation_phase_b_diagnostics import mean_invested_weights
from asset_allocation_phase_c_diagnostics import (
    _control_targets_from_shift,
    contiguous_true_runs,
    solve_phase_b_preserving_exposure_match,
)


def test_contiguous_true_runs() -> None:
    mask = np.asarray([False, True, True, False, True, False, True, True, True])
    assert contiguous_true_runs(mask) == [(1, 2), (4, 4), (6, 8)]


def test_phase_b_preserving_control_matches_realized_exposure() -> None:
    index = pd.date_range("2020-01-02", periods=90, freq="B")
    rng = np.random.default_rng(17)
    returns = pd.DataFrame(
        rng.normal([0.0004, 0.0001, 0.0002], [0.009, 0.006, 0.008], size=(len(index), 3)),
        index=index,
        columns=["SPY", "TLT", "GLD"],
    )
    template = pd.Series("neutral", index=index, dtype="object")
    template.iloc[20:35] = "reflation"
    template.iloc[60:72] = "reflation"
    neutral = {"SPY": 0.40, "TLT": 0.40, "GLD": 0.20}
    reflation = {"SPY": 0.60, "TLT": 0.20, "GLD": 0.20}
    known_shift = np.asarray([-0.025, 0.004])
    targets = _control_targets_from_shift(template, neutral, reflation, known_shift)
    rebalance = (month_start_mask(index) | template_change_mask(template)).astype(bool)
    observed = simulate_portfolio(returns, targets, rebalance, cost_bps=5.0, name="known_shift")
    desired = mean_invested_weights(observed)

    _, meta = solve_phase_b_preserving_exposure_match(
        returns,
        template,
        desired,
        neutral=neutral,
        reflation=reflation,
        cost_bps=5.0,
        name="solved",
    )
    assert meta["max_abs_invested_weight_mismatch"] < 1e-9
    assert abs(meta["constant_template_shift"]["SPY"] + 0.025) < 1e-7
    assert abs(meta["constant_template_shift"]["TLT"] - 0.004) < 1e-7
