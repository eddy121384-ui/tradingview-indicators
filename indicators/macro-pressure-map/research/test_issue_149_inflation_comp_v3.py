#!/usr/bin/env python3
from __future__ import annotations

import pandas as pd

from issue_149_inflation_comp_v3 import (
    build_v3_source,
    map_verdict,
)


def test_v3_replaces_only_inflation_level():
    v2 = pd.DataFrame({
        "period": pd.period_range("2000-01", periods=2, freq="M"),
        "expected_inflation_10y": [2.0, 2.1],
        "dbiq_level": [100.0, 101.0],
        "gasoline": [1.0, 1.1],
        "Crude oil, WTI": [25.0, 26.0],
    })
    comp = pd.DataFrame({
        "period": pd.period_range("2000-01", periods=2, freq="M"),
        "cleveland_comp10": [2.4, 2.5],
    })
    out = build_v3_source(v2, comp)
    assert out["expected_inflation_10y"].tolist() == [2.4, 2.5]
    assert out["dbiq_level"].tolist() == [100.0, 101.0]
    assert out["gasoline"].tolist() == [1.0, 1.1]
    assert out["Crude oil, WTI"].tolist() == [25.0, 26.0]


def test_map_verdict():
    assert map_verdict("signal_bridge_passed") == "signal_bridge_v3_passed"
    assert map_verdict("signal_bridge_failed") == "signal_bridge_v3_failed"
