from __future__ import annotations

import math

import analyze_issue78_heterogeneous_oos1 as m


def test_oos_universe_is_balanced_three_by_two():
    assert len(m.EXPECTED_MARKETS) == 6
    counts = {}
    for ticker in m.EXPECTED_MARKETS:
        cls = m.ASSET_CLASS[ticker]
        counts[cls] = counts.get(cls, 0) + 1
    assert counts == {
        "EquityIndex": 2,
        "PreciousMetals": 2,
        "Crypto": 2,
    }


def test_oos_universe_excludes_discovery_markets():
    discovery = {
        "OANDA:EURUSD", "OANDA:GBPUSD", "OANDA:USDJPY",
        "TVC:US10Y", "TVC:DE10Y", "TVC:FR10Y",
        "TVC:GB10Y", "TVC:AU10Y", "TVC:JP10Y",
    }
    assert not (set(m.EXPECTED_MARKETS) & discovery)


def test_candidate_set_is_frozen():
    assert m.CANDIDATES == ("R0_NoDerisk", "R0_WarningFirst")


def test_calendarized_metrics_do_not_assume_252_bars():
    year_ms = int(m.MS_YEAR)
    times = [0, year_ms]
    out = m.path_metrics(
        returns=[1.0, 1.0],
        exposures=[0.25, 1.0],
        times=times,
        episode_count=1,
    )
    assert math.isclose(out["calendar_years"], 1.0, rel_tol=1e-6)
    assert math.isclose(out["calendarized_return"], 2.0, rel_tol=1e-6)


def test_profit_factor_basic():
    assert math.isclose(m.profit_factor([2.0, -1.0, 1.0]), 3.0)


def test_ndx_runtime_feed_namespace_is_frozen():
    assert "NASDAQ_DLY:NDX" in m.EXPECTED_MARKETS
    assert "NASDAQ:NDX" not in m.EXPECTED_MARKETS
    assert m.ASSET_CLASS["NASDAQ_DLY:NDX"] == "EquityIndex"
