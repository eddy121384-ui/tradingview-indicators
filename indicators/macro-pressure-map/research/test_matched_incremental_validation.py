#!/usr/bin/env python3
from __future__ import annotations

import numpy as np
import pandas as pd

from matched_incremental_validation import matched_lift_stats


def test_matched_lift_uses_same_anchor_event_universe() -> None:
    events = pd.DataFrame(
        {
            "sign": [1, 1, 1, 1, 1, 1, -1, -1, -1, -1, -1, -1],
            "aligned": [False, False, False, True, True, True] * 2,
            "us10y_tvc": [1.0, 1.0, 1.0, 10.0, 10.0, 10.0, -1.0, -1.0, -1.0, -10.0, -10.0, -10.0],
        },
        index=pd.bdate_range("2020-01-01", periods=12),
    )

    stats = matched_lift_stats(events, "us10y_tvc", draws=1000, seed=123)

    assert stats["n_positive"] == 6
    assert stats["n_negative"] == 6
    assert stats["n_aligned_positive"] == 3
    assert stats["n_aligned_negative"] == 3
    assert np.isclose(stats["anchor_all_spread"], 11.0)
    assert np.isclose(stats["aligned_spread"], 20.0)
    assert np.isclose(stats["aligned_minus_all"], 9.0)
    assert stats["bootstrap_valid_draws"] > 0
