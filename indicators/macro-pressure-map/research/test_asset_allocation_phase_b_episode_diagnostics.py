from __future__ import annotations

import numpy as np
import pandas as pd

from asset_allocation_phase_b_diagnostics import mean_invested_weights
from asset_allocation_phase_b_episode_diagnostics import (
    build_leaveout_realized_exposure_matched_control,
    concentration_summary,
    reflation_episode_table,
    simulate_reflation_path,
)


def test_reflation_episode_table_groups_contiguous_true_runs_and_includes_exit_day() -> None:
    index = pd.date_range("2020-01-01", periods=7, freq="B")
    status = pd.Series([False, True, True, False, True, True, True], index=index)
    active = pd.Series([0.0, 0.01, -0.002, -0.003, 0.003, 0.004, -0.001], index=index)
    episodes = reflation_episode_table(status, active)
    assert len(episodes) == 2
    assert episodes.iloc[0]["days"] == 2
    assert np.isclose(episodes.iloc[0]["active_log_return_status_days"], 0.008)
    assert np.isclose(episodes.iloc[0]["active_log_return"], 0.005)
    assert bool(episodes.iloc[0]["exit_day_included"])
    assert episodes.iloc[1]["days"] == 3
    assert np.isclose(episodes.iloc[1]["active_log_return_status_days"], 0.006)
    assert np.isclose(episodes.iloc[1]["active_log_return"], 0.006)
    assert not bool(episodes.iloc[1]["exit_day_included"])


def test_concentration_summary_ranks_episode_using_exit_inclusive_contribution() -> None:
    index = pd.date_range("2020-01-01", periods=8, freq="B")
    status = pd.Series([True, True, False, True, True, False, True, True], index=index)
    active = pd.Series([0.03, 0.02, -0.02, 0.01, 0.01, 0.0, -0.01, 0.0], index=index)
    summary, episodes = concentration_summary("synthetic", status, active)
    assert len(episodes) == 3
    assert summary["positive_reflation_episodes"] == 2
    assert np.isclose(summary["total_active_log_return"], 0.04)
    # First episode is +0.05 on status-True days but only +0.03 after its exit row.
    assert np.isclose(summary["largest_positive_episode_active_log_including_exit_day"], 0.03)
    assert summary["largest_positive_episode_start"] == index[0].date().isoformat()
    assert np.isclose(summary["top1_share_of_positive_episode_contribution"], 0.03 / 0.05)


def test_counterfactual_replay_removes_entry_and_exit_rebalance_costs() -> None:
    index = pd.date_range("2020-01-02", periods=5, freq="B")
    returns = pd.DataFrame(0.0, index=index, columns=["SPY", "TLT", "GLD"])
    status = pd.Series([False, True, True, False, False], index=index)
    neutral = {"SPY": 0.4, "TLT": 0.4, "GLD": 0.2}
    reflation = {"SPY": 0.6, "TLT": 0.2, "GLD": 0.2}

    original = simulate_reflation_path(
        returns,
        status,
        neutral_weights=neutral,
        reflation_weights=reflation,
        cost_bps=5.0,
        name="original",
    )
    disabled = status.copy()
    disabled.iloc[1:3] = False
    leaveout = simulate_reflation_path(
        returns,
        disabled,
        neutral_weights=neutral,
        reflation_weights=reflation,
        cost_bps=5.0,
        name="leaveout",
    )

    # The original path pays both the entry and exit event-rebalance costs.
    assert original["trade"].sum() == 2
    assert original.loc[index[1], "cost_fraction"] > 0.0
    assert original.loc[index[3], "cost_fraction"] > 0.0
    # Disabling the whole episode removes both event trades; only the scheduled
    # month-start row remains, and initial allocation is cost-free.
    assert leaveout["trade"].sum() == 0
    assert np.isclose(leaveout["net_return"].sum(), 0.0)
    assert original["net_return"].sum() < 0.0


def test_leaveout_control_rematches_realized_exposure_of_counterfactual_path() -> None:
    index = pd.date_range("2020-01-02", periods=80, freq="B")
    x = np.arange(len(index), dtype=float)
    returns = pd.DataFrame(
        {
            "SPY": 0.0005 + 0.0008 * np.sin(x / 7.0),
            "TLT": 0.0002 - 0.0005 * np.sin(x / 9.0),
            "GLD": 0.0001 + 0.0004 * np.cos(x / 11.0),
        },
        index=index,
    )
    neutral = {"SPY": 0.4, "TLT": 0.4, "GLD": 0.2}
    reflation = {"SPY": 0.6, "TLT": 0.2, "GLD": 0.2}
    status = pd.Series(False, index=index)
    status.iloc[10:28] = True
    status.iloc[45:60] = True
    leaveout_status = status.copy()
    leaveout_status.iloc[10:28] = False

    leaveout = simulate_reflation_path(
        returns,
        leaveout_status,
        neutral_weights=neutral,
        reflation_weights=reflation,
        cost_bps=5.0,
        name="leaveout",
    )
    leaveout_seg, matched, meta = build_leaveout_realized_exposure_matched_control(
        leaveout,
        returns,
        segment_start=None,
        segment_end=None,
        cost_bps=5.0,
        name="leaveout_match",
    )

    desired = mean_invested_weights(leaveout_seg)
    actual = mean_invested_weights(matched)
    assert meta["matching_basis"] == "leaveout realized average invested_weight_* exposure"
    assert meta["max_abs_invested_weight_mismatch"] <= 1e-9
    for asset in ("SPY", "TLT", "GLD"):
        assert np.isclose(actual[asset], desired[asset], atol=1e-9)
