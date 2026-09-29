from __future__ import annotations

import numpy as np
import pandas as pd

from issue_117_long_history_gold_cash import (
    DEFENSIVE,
    era,
    month_ord,
    nonoverlap,
    summarize,
)


def test_defensive_states_are_exact():
    assert DEFENSIVE == (
        "Slowdown / Disinflation",
        "Growth Slowdown / Stable Inflation",
        "Stagflation Pressure",
    )


def test_eras_are_frozen():
    assert era(pd.Timestamp("1975-01-01")) == "1975_1989"
    assert era(pd.Timestamp("1989-12-01")) == "1975_1989"
    assert era(pd.Timestamp("1990-01-01")) == "1990_2006"
    assert era(pd.Timestamp("2007-01-01")) == "2007_2019"
    assert era(pd.Timestamp("2020-01-01")) == "2020_latest"


def test_nonoverlap_uses_three_calendar_months():
    df=pd.DataFrame({"decision_date":pd.to_datetime([
        "2000-01-01","2000-02-01","2000-03-01","2000-04-01","2000-06-01"
    ]),"spread_3M":[1,2,3,4,5]})
    out=nonoverlap(df,3)
    assert list(out["decision_date"].dt.strftime("%Y-%m")) == ["2000-01","2000-04"]


def test_month_ord_is_monotonic():
    assert month_ord(pd.Timestamp("2000-02-01")) - month_ord(pd.Timestamp("2000-01-01")) == 1


def test_bootstrap_summary_is_deterministic():
    a=summarize(np.array([0.01,0.02,-0.01,0.03]),seed=117)
    b=summarize(np.array([0.01,0.02,-0.01,0.03]),seed=117)
    assert a == b
