from __future__ import annotations

import numpy as np
import pandas as pd

from issue_89_episode_diagnostics import (
    contiguous_template_runs,
    eligible_episode_table,
    load_robustness_contract,
    summarize_episodes,
)


def test_secondary_robustness_contract_is_frozen_without_modifying_primary_policy() -> None:
    contract = load_robustness_contract()
    assert contract["primary_policy_modified"] is False
    assert contract["primary_portfolio_results_already_viewed"] is True
    assert contract["frozen_before_issue_89_episode_results_viewed"] is True
    assert contract["exposure_match_tolerance"] == 1e-9


def test_contiguous_template_runs_partition_every_date_once() -> None:
    index = pd.date_range("2020-01-01", periods=7, freq="B")
    template = pd.Series(["A", "A", "B", "B", "B", "C", "A"], index=index)
    runs = contiguous_template_runs(template)
    assert [(r["regime"], r["days"]) for r in runs] == [("A", 2), ("B", 3), ("C", 1), ("A", 1)]
    assert sum(r["days"] for r in runs) == len(template)


def test_episode_screening_selects_largest_positive_and_negative() -> None:
    index = pd.date_range("2020-01-01", periods=6, freq="B")
    template = pd.Series(["A", "A", "B", "B", "C", "C"], index=index)
    active = pd.Series([0.01, 0.02, -0.03, -0.01, 0.04, 0.01], index=index)
    episodes = eligible_episode_table(
        template,
        active,
        segment="full_reused_history",
        start=None,
        end=None,
    )
    summary = summarize_episodes(episodes)
    assert summary["largest_positive_episode"]["regime"] == "C"
    assert np.isclose(summary["largest_positive_episode"]["active_log_return"], 0.05)
    assert summary["largest_negative_episode"]["regime"] == "B"
    assert np.isclose(summary["largest_negative_episode"]["active_log_return"], -0.04)


def test_segment_screening_requires_whole_episode_inside_boundary() -> None:
    index = pd.date_range("2019-12-27", periods=6, freq="B")
    template = pd.Series(["A", "A", "A", "B", "B", "C"], index=index)
    active = pd.Series(0.01, index=index)
    episodes = eligible_episode_table(
        template,
        active,
        segment="post2019_reused_exploratory",
        start=pd.Timestamp("2020-01-01"),
        end=None,
    )
    assert "A" not in set(episodes["regime"])
