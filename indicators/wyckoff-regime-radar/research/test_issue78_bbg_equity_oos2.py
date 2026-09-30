from __future__ import annotations

import math

import numpy as np
import pandas as pd

import analyze_issue78_bbg_equity_oos2 as m


class FakeClassifier:
    @staticmethod
    def compute_price_only(frame):
        n = len(frame)
        formal = np.zeros(n, dtype=int)
        if n >= 4:
            formal[1:3] = 2
            formal[3:] = 0
        return pd.DataFrame(
            {
                "formal_id": formal,
                "sym_atr": np.full(n, 0.02),
            }
        )


def test_prepare_frame_creates_fresh_transition_and_log_moves():
    raw = pd.DataFrame(
        {
            "date": pd.date_range("2020-01-01", periods=5, freq="D"),
            "open": [10, 11, 12, 13, 14],
            "high": [11, 12, 13, 14, 15],
            "low": [9, 10, 11, 12, 13],
            "close": [10.5, 11.5, 12.5, 13.5, 14.5],
            "volume": [1_000_000] * 5,
        }
    )
    out = m.prepare_frame(raw, FakeClassifier(), "BBGTEST")
    assert out["stage"].tolist() == [0, 2, 2, 0, 0]
    assert out["fresh"].tolist() == [0, 1, 0, 0, 0]
    expected = math.log(11.5) - math.log(10.5)
    assert abs(out.loc[0, "move1"] - expected) < 1e-12
    assert out.loc[0, "repr"] == "PRICE_LOG"


def test_entry_eligibility_is_causal_and_frozen():
    n = 320
    raw = pd.DataFrame(
        {
            "date": pd.bdate_range("2000-01-03", periods=n),
            "open": np.full(n, 20.0),
            "high": np.full(n, 21.0),
            "low": np.full(n, 19.0),
            "close": np.full(n, 20.0),
            "volume": np.full(n, 1_000_000.0),
        }
    )

    class Flat:
        @staticmethod
        def compute_price_only(frame):
            return pd.DataFrame(
                {
                    "formal_id": np.zeros(len(frame)),
                    "sym_atr": np.full(len(frame), 0.02),
                }
            )

    frame = m.prepare_frame(raw, Flat(), "BBGTEST")
    ok, reason = m.entry_eligibility(frame, 252)
    assert ok, reason

    frame_low_price = frame.copy()
    frame_low_price.loc[252, "raw_close"] = 4.99
    ok, reason = m.entry_eligibility(frame_low_price, 252)
    assert not ok
    assert reason == "close_lt5"


def test_primary_aggregation_is_one_stock_one_vote():
    rows = []
    for policy in m.POLICIES:
        for figi, expectancy in (("A", 1.0), ("B", -0.5)):
            for ep in range(5):
                rows.append(
                    {
                        "figi": figi,
                        "ticker": figi,
                        "sector": "Industrials",
                        "sleeve": "large",
                        "policy": policy,
                        "episode_id": ep,
                        "harvest": expectancy,
                        "avg_exposure": 0.5,
                        "turnover": 1.0,
                    }
                )
    records = pd.DataFrame(rows)
    stocks = m.stock_summary(records)
    primary = stocks[stocks["episodes"] >= 5]
    agg = m.aggregate_primary(primary)
    r0 = agg[agg["policy"] == "R0_NoDerisk"].iloc[0]
    assert r0["stocks"] == 2
    assert abs(r0["equal_stock_mean_expectancy"] - 0.25) < 1e-12
    assert abs(r0["positive_stock_fraction"] - 0.5) < 1e-12


def test_concentration_removes_top_positive_stock_deterministically():
    primary = pd.DataFrame(
        [
            {
                "figi": f"F{i}",
                "policy": "R0_NoDerisk",
                "mean_expectancy": value,
            }
            for i, value in enumerate([4.0, 3.0, 2.0, 1.0, -1.0])
        ]
        + [
            {
                "figi": f"F{i}",
                "policy": "R0_WarningFirst",
                "mean_expectancy": value,
            }
            for i, value in enumerate([3.0, 2.0, 1.0, 0.5, -0.5])
        ]
    )
    out = m.concentration(primary)
    assert out["positive_stocks"] == 4
    assert out["top1pct_positive_stock_count"] == 1
    assert abs(out["top1pct_positive_contribution_share"] - 0.4) < 1e-12
    assert abs(
        out["equal_stock_mean_after_removing_top1pct_positive"]
        - ((3.0 + 2.0 + 1.0 - 1.0) / 4.0)
    ) < 1e-12


def test_frozen_threshold_constants():
    assert m.MIN_PRIMARY_EPISODES == 5
    assert m.MIN_TEMPORAL_STOCKS == 20
    assert m.MIN_SECTOR_STOCKS == 5
    assert m.MIN_PRIOR_VALID == 252
    assert m.LIQUIDITY_WINDOW == 60
    assert m.MIN_PRICE == 5.0
    assert m.MIN_MEDIAN_DOLLAR_VOLUME == 5_000_000.0
    assert m.POLICIES == ("R0_NoDerisk", "R0_WarningFirst")
