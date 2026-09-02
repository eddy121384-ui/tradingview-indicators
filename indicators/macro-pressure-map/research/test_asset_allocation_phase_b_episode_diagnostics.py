from __future__ import annotations

import numpy as np
import pandas as pd

from asset_allocation_phase_b_episode_diagnostics import (
    concentration_summary,
    reflation_episode_table,
)


def test_reflation_episode_table_groups_contiguous_true_runs() -> None:
    index = pd.date_range("2020-01-01", periods=7, freq="B")
    status = pd.Series([False, True, True, False, True, True, True], index=index)
    active = pd.Series([0.0, 0.01, -0.002, 0.0, 0.003, 0.004, -0.001], index=index)
    episodes = reflation_episode_table(status, active)
    assert len(episodes) == 2
    assert episodes.iloc[0]["days"] == 2
    assert np.isclose(episodes.iloc[0]["active_log_return"], 0.008)
    assert episodes.iloc[1]["days"] == 3
    assert np.isclose(episodes.iloc[1]["active_log_return"], 0.006)


def test_concentration_summary_leave_largest_episode_out_is_additive() -> None:
    index = pd.date_range("2020-01-01", periods=8, freq="B")
    status = pd.Series([True, True, False, True, True, False, True, True], index=index)
    active = pd.Series([0.03, 0.02, -0.01, 0.01, 0.01, -0.005, -0.01, 0.0], index=index)
    summary, episodes = concentration_summary("synthetic", status, active)
    assert len(episodes) == 3
    assert summary["positive_reflation_episodes"] == 2
    assert np.isclose(summary["total_active_log_return"], 0.045)
    assert np.isclose(summary["largest_positive_episode_active_log"], 0.05)
    assert np.isclose(
        summary["active_log_after_removing_largest_positive_reflation_episode"],
        -0.005,
    )
    assert np.isclose(summary["top1_share_of_positive_episode_contribution"], 0.05 / 0.07)
