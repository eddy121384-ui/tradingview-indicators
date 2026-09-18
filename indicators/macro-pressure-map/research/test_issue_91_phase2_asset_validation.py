from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from issue_91_phase2_asset_validation import (
    _parse_percent_decimal,
    absolute_inflation_comparison,
    add_spreads,
    build_pairings,
    metric_summary,
    parse_damodaran_returns,
    sample_label,
    sign_of,
    validate_prereg,
)


def test_prereg_precedes_outcomes_and_disallows_portfolio() -> None:
    p=validate_prereg()
    assert p["created_before_phase2_asset_outcomes"] is True
    assert p["portfolio_policy_test_in_this_phase"] is False
    assert p["production_v66_modified"] is False


def test_percent_parser_is_decimal() -> None:
    assert np.isclose(_parse_percent_decimal("43.81%"),0.4381)
    assert np.isclose(_parse_percent_decimal("-4.25%"),-0.0425)
    assert np.isclose(_parse_percent_decimal("(3.50%)"),-0.035)
    assert np.isclose(_parse_percent_decimal("0.12"),0.12)


def test_add_spreads() -> None:
    frame=pd.DataFrame({"equity":[.10],"treasury":[.03],"cash":[.01],"gold":[.05]})
    out=add_spreads(frame)
    assert np.isclose(out.loc[0,"equity_minus_treasury"],.07)
    assert np.isclose(out.loc[0,"treasury_minus_cash"],.02)
    assert np.isclose(out.loc[0,"equity_minus_gold"],.05)
    assert np.isclose(out.loc[0,"treasury_minus_gold"],-.02)


def test_causal_pairing_is_exact_t_plus_2() -> None:
    states=pd.DataFrame({
        "year":[2000,2001,2002],
        "growth_state":["high"]*3,
        "inflation_state":["low"]*3,
        "core_regime":["Goldilocks / Disinflationary Expansion"]*3,
        "growth_score":[20.]*3,
        "inflation_score":[-20.]*3,
        "growth_rate":[1.]*3,
        "inflation_rate":[1.]*3,
        "absolute_inflation_bucket":["low"]*3,
        "era":["Pre_GFC_2000s"]*3,
    })
    assets=pd.DataFrame({
        "year":[2000,2001,2002,2003,2004],
        "equity":[.1]*5,"treasury":[.02]*5,"cash":[.01]*5,"gold":[.03]*5,
    })
    structural,causal=build_pairings(states,assets)
    assert (structural["state_year"]==structural["return_year"]).all()
    assert (causal["return_year"]==causal["state_year"]+2).all()
    assert list(causal["state_year"])==[2000,2001,2002]


def test_sample_labels() -> None:
    assert sample_label(2)=="insufficient"
    assert sample_label(3)=="very_sparse"
    assert sample_label(5)=="sparse"
    assert sample_label(10)=="regular"


def test_metric_summary_bootstrap_deterministic() -> None:
    p=validate_prereg()
    s=pd.Series([.1,.2,-.1,.05,.03])
    a=metric_summary(s,"equity_minus_treasury",p,"same-key")
    b=metric_summary(s,"equity_minus_treasury",p,"same-key")
    assert a["bootstrap_mean_ci_low"]==b["bootstrap_mean_ci_low"]
    assert a["bootstrap_mean_ci_high"]==b["bootstrap_mean_ci_high"]
    assert a["geometric_mean"] is None


def test_absolute_inflation_requires_both_groups_n5() -> None:
    p=validate_prereg()
    rows=[]
    for idx,pi in enumerate([1,2,3,1,2,5,6,7,5,4]):
        rows.append({
            "return_year":1980+idx,
            "growth_state":"low",
            "inflation_state":"high",
            "core_regime":"Stagflation Pressure",
            "inflation_rate":float(pi),
            "equity_minus_treasury":-.1 if pi>=4 else .1,
            "treasury_minus_cash":-.02 if pi>=4 else .02,
            "equity_minus_gold":-.05 if pi>=4 else .05,
            "treasury_minus_gold":-.03 if pi>=4 else .03,
        })
    frame=pd.DataFrame(rows)
    out=absolute_inflation_comparison(frame,p)
    target=out.loc[out["metric"].eq("equity_minus_treasury")].iloc[0]
    assert bool(target["eligible_both_n_ge_5"])
    assert bool(target["sign_reversal_between_groups"])
    assert target["mean_difference_high_minus_low"] < 0


def test_no_etf_tokens_in_primary_source() -> None:
    p=validate_prereg()
    text=json.dumps(p["primary_asset_source"]).lower()
    assert all(token not in text for token in ('"spy"','"tlt"','"gld"'))
