#!/usr/bin/env python3
from __future__ import annotations

import numpy as np
import pandas as pd

from issue_145_ipi_v2_bridge import (
    HIST_START,
    build_v2_ipi,
    map_verdict,
)


def test_map_verdict_is_deterministic():
    assert map_verdict("signal_bridge_passed") == "signal_bridge_v2_passed"
    assert map_verdict("signal_bridge_failed") == "signal_bridge_v2_failed"
    assert (
        map_verdict("signal_bridge_inconclusive_sample")
        == "signal_bridge_v2_inconclusive_sample"
    )


def test_v2_ipi_uses_frozen_weights_and_warmup():
    dates = pd.period_range("1988-12", periods=36, freq="M")
    x = pd.DataFrame({
        "period": dates,
        "dbiq_level": np.linspace(100.0, 180.0, len(dates)),
        "gasoline": np.linspace(0.5, 1.2, len(dates)),
        "Crude oil, WTI": np.linspace(15.0, 40.0, len(dates)),
        "expected_inflation_10y": np.linspace(0.04, 0.025, len(dates)),
    })
    out = build_v2_ipi(x)
    first = out.loc[out["ipi_v2_eligible"], "period"].min()
    assert first == HIST_START
    row = out.loc[out["ipi_v2_eligible"]].iloc[-1]
    expected = (
        0.35 * row["ipi_expected"]
        + 0.40 * row["ipi_dbiq"]
        + 0.25 * ((row["ipi_wti"] + row["ipi_gasoline"]) / 2.0)
    )
    assert abs(row["ipi_a"] - expected) < 1e-12
