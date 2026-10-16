#!/usr/bin/env python3
from __future__ import annotations

import pandas as pd

from issue_136_r7_async_turn import (
    assign_episode_ids,
    assign_roles,
    build_modern_labels,
    cluster_bootstrap_diff,
)


def test_assign_episode_ids_breaks_on_calendar_gap_and_non_r7():
    dates = pd.to_datetime([
        "2020-01-31", "2020-02-28", "2020-03-31",
        "2020-05-29", "2020-06-30", "2020-07-31",
    ])
    flags = pd.Series([True, True, False, True, True, True])
    got = assign_episode_ids(flags, pd.Series(dates)).tolist()
    assert got == [1, 1, 0, 2, 2, 2]


def test_async_turn_allows_different_turn_months_and_first_trigger_only():
    dates = pd.to_datetime([
        "2007-01-31", "2007-02-28", "2007-03-30", "2007-04-30",
        "2007-05-31", "2007-06-29", "2007-07-31", "2007-08-31",
        "2007-09-28",
    ])
    # GPI slope: negative through Apr, turns positive in May.
    gpi = [3, 2, 1, 0, 1, 2, 3, 4, 5]
    # IPI slope: negative through May, turns positive in Jun.
    ipi = [4, 3, 2, 1, 0, 1, 2, 3, 4]
    # Enter R7 in May; asynchronous completion occurs in Jun.
    regime = [5, 5, 5, 5, 7, 7, 7, 7, 7]
    sig = pd.DataFrame({"date": dates, "gpi": gpi, "ipi": ipi, "regime": regime})
    x = build_modern_labels(sig)
    hits = x.loc[x["is_signal"]]
    assert len(hits) == 1
    assert hits.iloc[0]["date"] == pd.Timestamp("2007-06-29")
    assert hits.iloc[0]["turn_order"] == "GPI_first"
    assert int(hits.iloc[0]["turn_lag"]) == 1
    assert not x.loc[x["date"].gt("2007-06-29"), "is_signal"].any()


def test_assign_roles_excludes_post_trigger_months():
    f = pd.DataFrame({
        "episode_id": [1, 1, 1, 1, 2, 2],
        "is_signal": [False, False, True, False, False, False],
        "eligible": [True, True, True, True, True, True],
    })
    role = assign_roles(f, "eligible").tolist()
    assert role == ["control", "control", "signal", "excluded_post_trigger", "control", "control"]


def test_cluster_bootstrap_is_deterministic_and_uses_episode_clusters():
    f = pd.DataFrame({
        "episode_id": [1, 1, 2, 2, 3, 4],
        "is_signal": [False, True, False, True, False, False],
        "value": [0.00, 0.10, 0.01, 0.09, 0.02, 0.03],
    })
    a = cluster_bootstrap_diff(f, "value", key="unit")
    b = cluster_bootstrap_diff(f, "value", key="unit")
    assert a == b
    assert a["episodes"] == 4
    assert a["signal_n"] == 2
    assert a["control_n"] == 4
    assert a["mean_diff"] > 0
    assert a["valid_bootstrap_reps"] > 0
