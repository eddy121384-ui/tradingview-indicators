#!/usr/bin/env python3
from __future__ import annotations

import pandas as pd

from issue_151_spf10_bridge import build_spf_v2_source, map_verdict


def test_spf_replaces_only_inflation_leg():
    v2 = pd.DataFrame({
        "period": pd.period_range("2000-01", periods=3, freq="M"),
        "expected_inflation_10y": [2.0, 2.0, 2.0],
        "dbiq_level": [100.0, 101.0, 102.0],
        "gasoline": [1.0, 1.1, 1.2],
        "Crude oil, WTI": [25.0, 26.0, 27.0],
    })
    spf = pd.DataFrame({
        "period": pd.period_range("2000-01", periods=3, freq="M"),
        "spf10": [2.5, 2.5, 2.4],
    })
    out = build_spf_v2_source(v2, spf)
    assert out["expected_inflation_10y"].tolist() == [2.5, 2.5, 2.4]
    assert out["dbiq_level"].tolist() == [100.0, 101.0, 102.0]
    assert out["gasoline"].tolist() == [1.0, 1.1, 1.2]


def test_map_verdict():
    assert map_verdict("signal_bridge_passed") == "signal_bridge_spf_passed"
    assert map_verdict("signal_bridge_failed") == "signal_bridge_spf_failed"
    assert (
        map_verdict("signal_bridge_inconclusive_sample")
        == "signal_bridge_spf_inconclusive_sample"
    )
