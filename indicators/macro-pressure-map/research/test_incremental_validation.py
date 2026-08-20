#!/usr/bin/env python3
from __future__ import annotations

import pandas as pd

from incremental_validation import embargo_entry_events


def test_embargo_entry_events_uses_one_shared_horizon_across_high_and_low() -> None:
    index = pd.bdate_range("2020-01-01", periods=30)
    high = pd.Series(False, index=index)
    low = pd.Series(False, index=index)
    high.iloc[[0, 8, 20]] = True
    low.iloc[[4, 12, 24]] = True

    kept_high, kept_low = embargo_entry_events(high, low, horizon=10)

    accepted = [
        position
        for position in range(len(index))
        if kept_high.iloc[position] or kept_low.iloc[position]
    ]
    assert accepted == [0, 12, 24]
    assert kept_high.iloc[0]
    assert kept_low.iloc[12]
    assert kept_low.iloc[24]
