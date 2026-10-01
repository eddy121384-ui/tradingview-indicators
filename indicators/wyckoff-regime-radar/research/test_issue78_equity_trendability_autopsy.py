from __future__ import annotations

import math

import numpy as np

import analyze_issue78_equity_trendability_autopsy as m


def test_previous_percentrank_excludes_current():
    x = np.array([3.0, 2.0, 1.0, 0.0, 4.0])
    r = m.pine_previous_percentrank(x, length=3)
    assert all(math.isnan(v) for v in r[:3])
    assert r[3] == 0.0
    assert r[4] == 100.0


def test_previous_percentrank_ties_count_as_less_equal():
    x = np.array([1.0, 1.0, 1.0, 1.0])
    r = m.pine_previous_percentrank(x, length=3)
    assert r[3] == 100.0


def test_rolling_er_is_one_for_monotonic_path():
    x = np.arange(20.0)
    er = m.rolling_er(x, 5)
    assert math.isnan(er[4])
    assert np.allclose(er[5:], 1.0)


def test_fixed_bucket_contract():
    assert m.bucket_score(0.0) == "Low"
    assert m.bucket_score(33.329) == "Low"
    assert m.bucket_score(33.33) == "Neutral"
    assert m.bucket_score(66.67) == "Neutral"
    assert m.bucket_score(66.671) == "High"

    assert m.width_bucket(10.0) == "Narrow"
    assert m.width_bucket(50.0) == "Medium"
    assert m.width_bucket(90.0) == "Wide"


def test_frozen_horizons_and_rank_length():
    assert m.ER_HORIZONS == (63, 126, 252)
    assert m.RANK_LEN == 756
    assert m.WIDTH_HORIZON == 252
    assert m.EXPECTED_UNIVERSE_SHA == (
        "9d4a14d163ed308238737647b94e722c62fd023b641e1015e6d97679f9ba3b44"
    )
