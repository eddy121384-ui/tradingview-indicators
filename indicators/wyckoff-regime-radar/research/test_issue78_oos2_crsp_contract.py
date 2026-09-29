from __future__ import annotations

import pandas as pd
import numpy as np

from issue78_oos2_crsp_contract import (
    EVENT_START,
    add_entry_eligibility,
    normalize_crsp,
    require_columns,
)


def fixture(rows: int = 320):
    dates = pd.bdate_range("1999-01-04", periods=rows)
    daily = pd.DataFrame(
        {
            "PERMNO": 10001,
            "DlyCalDt": dates,
            "DlyOpen": 50.0,
            "DlyHigh": 51.0,
            "DlyLow": 49.0,
            "DlyClose": 50.0,
            "DlyPrc": 50.0,
            "DlyVol": 200000.0,
            "DlyRetx": 0.0,
            "DlyDelFlg": "N",
        }
    )
    factors = pd.DataFrame(
        {
            "PERMNO": 10001,
            "DlyCalDt": dates,
            "DlyCumFacPr": 2.0,
            "DlyCumFacShr": 2.0,
        }
    )
    info = pd.DataFrame(
        {
            "PERMNO": [10001],
            "SecInfoStartDt": ["1990-01-01"],
            "SecInfoEndDt": [None],
            "PrimaryExch": ["Q"],
            "SecurityType": ["EQTY"],
            "SecuritySubType": ["COM"],
            "ShareType": ["NS"],
            "IssuerType": ["CORP"],
            "USIncFlg": ["Y"],
            "Ticker": ["TEST"],
            "TradingSymbol": ["TEST"],
            "SICCD": [3571],
        }
    )
    return daily, factors, info


def test_adjustment_contract_and_point_in_time_security_filter():
    daily, factors, info = fixture()
    out = normalize_crsp(daily, factors, info)
    assert np.isclose(out.iloc[-1]["close"], 25.0)
    assert np.isclose(out.iloc[-1]["volume"], 400000.0)
    assert bool(out.iloc[-1]["eligible_security_type"])
    assert bool(out.iloc[-1]["valid_classifier_bar"])


def test_adr_is_excluded():
    daily, factors, info = fixture()
    info.loc[0, "ShareType"] = "ADR"
    out = normalize_crsp(daily, factors, info)
    assert not bool(out.iloc[-1]["eligible_security_type"])


def test_exchange_outside_naq_is_excluded():
    daily, factors, info = fixture()
    info.loc[0, "PrimaryExch"] = "R"
    out = normalize_crsp(daily, factors, info)
    assert not bool(out.iloc[-1]["eligible_security_type"])


def test_entry_rule_is_causal_and_requires_history_liquidity_and_price():
    daily, factors, info = fixture(420)
    out = add_entry_eligibility(normalize_crsp(daily, factors, info))
    eligible = out[out["entry_eligible"]]
    assert not eligible.empty
    assert eligible.iloc[0]["date"] >= EVENT_START
    assert eligible.iloc[0]["prior_valid_bars"] >= 252
    assert eligible.iloc[0]["median_dollar_volume_60"] >= 5_000_000.0
    assert eligible.iloc[0]["close"] >= 5.0


def test_missing_adjustment_factor_invalidates_bar():
    daily, factors, info = fixture()
    factors.loc[factors.index[-1], "DlyCumFacPr"] = np.nan
    out = normalize_crsp(daily, factors, info)
    assert not bool(out.iloc[-1]["valid_classifier_bar"])
    assert np.isnan(out.iloc[-1]["close"])


def test_missing_contract_column_raises():
    daily, _, _ = fixture()
    try:
        require_columns(daily.rename(columns=str.lower), {"definitely_missing"}, "daily")
    except ValueError as exc:
        assert "definitely_missing" in str(exc)
    else:
        raise AssertionError("expected missing-column failure")
