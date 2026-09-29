from __future__ import annotations

import pandas as pd

from issue_125_reflation_bridge import (
    HMRA_REFLATION,
    regime_on_date,
)


def test_hmra_reflation_label_is_exact():
    assert HMRA_REFLATION == "Reflation / Inflation Rising"


def test_transition_lookup_uses_last_effective_state():
    t = pd.DataFrame({
        "start_date": pd.to_datetime(["2007-01-01","2007-01-15","2007-02-01"]),
        "regime_id": [1,3,6],
    })
    assert regime_on_date(t, pd.Timestamp("2007-01-31")) == 3
    assert regime_on_date(t, pd.Timestamp("2007-02-28")) == 6
