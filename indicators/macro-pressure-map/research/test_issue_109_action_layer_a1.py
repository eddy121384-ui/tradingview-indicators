from __future__ import annotations

import pandas as pd

from issue_109_action_layer_a1 import (
    SIGNAL_CUTOFF,
    assign_episode_ids,
    first_rows_each_month,
    select_nonoverlap,
    state_on_date,
)


def test_state_on_date_uses_latest_transition_and_stops_after_cutoff():
    t = pd.DataFrame({
        "start_date": pd.to_datetime(["2020-01-02", "2020-01-10", "2020-02-03"]),
        "regime_id": [1, 3, 7],
    })
    assert state_on_date(t, pd.Timestamp("2020-01-01")) is None
    assert state_on_date(t, pd.Timestamp("2020-01-02"))[0] == 1
    assert state_on_date(t, pd.Timestamp("2020-01-31"))[0] == 3
    assert state_on_date(t, pd.Timestamp("2020-02-10"))[0] == 7
    assert state_on_date(t, SIGNAL_CUTOFF + pd.Timedelta(days=1)) is None


def test_first_rows_each_month_returns_first_common_row():
    idx = pd.to_datetime([
        "2020-01-02", "2020-01-03", "2020-01-31",
        "2020-02-03", "2020-02-04",
        "2020-03-02",
    ])
    assert first_rows_each_month(idx) == [0, 3, 5]


def test_nonoverlap_selector_is_greedy_by_common_row_position():
    g = pd.DataFrame({
        "origin_pos": [10, 30, 72, 74, 140],
        "origin_date": pd.to_datetime(["2020-01-02","2020-02-03","2020-04-01","2020-05-01","2020-08-03"]),
        "pairwise_spread": [1,2,3,4,5],
    })
    selected = select_nonoverlap(g, 63)
    assert selected["origin_pos"].tolist() == [10, 74, 140]


def test_episode_assignment_breaks_on_state_change_and_month_gap():
    g = pd.DataFrame({
        "origin_date": pd.to_datetime([
            "2020-01-02", "2020-02-03", "2020-03-02",
            "2020-04-01", "2020-06-01", "2020-07-01",
        ]),
        "regime_id": [1, 1, 2, 2, 2, 2],
    })
    out = assign_episode_ids(g)
    assert out["episode_id"].tolist() == [1, 1, 2, 2, 3, 3]


def test_episode_logic_is_sign_agnostic_at_assignment_stage():
    positive = pd.DataFrame({
        "origin_date": pd.to_datetime(["2020-01-02", "2020-02-03"]),
        "regime_id": [1, 1],
        "pairwise_spread": [0.1, 0.2],
    })
    negative = positive.copy()
    negative["pairwise_spread"] = [-0.1, -0.2]
    assert assign_episode_ids(positive)["episode_id"].tolist() == assign_episode_ids(negative)["episode_id"].tolist()
