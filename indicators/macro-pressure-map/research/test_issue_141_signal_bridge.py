#!/usr/bin/env python3
from __future__ import annotations

import numpy as np
import pandas as pd

from issue_141_signal_bridge import (
    add_turning,
    component_score,
    regime_id,
    trigger_match,
)


def test_regime_id_matches_v66_3x3_order():
    assert regime_id(20, -20) == 1
    assert regime_id(20, 0) == 2
    assert regime_id(20, 20) == 3
    assert regime_id(0, -20) == 4
    assert regime_id(0, 0) == 5
    assert regime_id(0, 20) == 6
    assert regime_id(-20, -20) == 7
    assert regime_id(-20, 0) == 8
    assert regime_id(-20, 20) == 9


def test_monthly_component_score_has_warmup_and_finite_tail():
    s = pd.Series(np.linspace(100.0, 160.0, 48))
    out = component_score(s)
    assert out.iloc[:13].isna().all()
    assert out.iloc[-12:].notna().all()
    assert np.isfinite(out.iloc[-1])


def test_first_trigger_only_inside_contiguous_r7_episode():
    periods = pd.period_range("2000-01", periods=10, freq="M")
    # GPI turns in May; IPI turns in Jun; both remain R7.
    g = [3, 2, 1, 0, 1, 2, 3, 4, 5, 6]
    i = [4, 3, 2, 1, 0, 1, 2, 3, 4, 5]
    f = pd.DataFrame({
        "period": periods,
        "g": g,
        "i": i,
        "r": [5, 5, 5, 5, 7, 7, 7, 7, 7, 7],
    })
    out = add_turning(f, "g", "i", "r", "x")
    hits = out.loc[out["x_trigger"], "period"].tolist()
    assert hits == [pd.Period("2000-06", freq="M")]


def test_trigger_matching_is_one_to_one_and_nearest_first():
    exact = [pd.Period("2020-01", "M"), pd.Period("2020-04", "M")]
    analogue = [
        pd.Period("2019-12", "M"),
        pd.Period("2020-01", "M"),
        pd.Period("2020-05", "M"),
    ]
    r = trigger_match(exact, analogue)
    assert r["matched"] == 2
    assert r["exact_n"] == 2
    assert r["analogue_n"] == 3
    assert r["pairs"][0] == {
        "exact": "2020-01",
        "analogue": "2020-01",
        "month_distance": 0,
    }


def test_trigger_metrics_when_analogue_has_zero():
    r = trigger_match([pd.Period("2020-01", "M")], [])
    assert r["precision"] == 0.0
    assert r["recall"] == 0.0
    assert r["f1"] == 0.0
    assert r["count_ratio"] == 0.0
