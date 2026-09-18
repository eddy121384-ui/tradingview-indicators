from __future__ import annotations

import io
from pathlib import Path

import numpy as np
import pandas as pd

from issue_91_phase1_hmra_v01 import (
    annual_december,
    build_hmra,
    inflation_bucket,
    parse_bls_cpi,
    parse_fed_ip,
    prior_window_z,
    tri_state,
    validate_prereg,
)


def test_prereg_forbids_asset_outcomes() -> None:
    p=validate_prereg()
    assert p["created_before_asset_conditioned_results"] is True
    assert p["production_v66_modified"] is False
    assert p["exact_v66_claim"] is False
    assert "api.bls.gov" in p["primary_macro_sources"]["inflation"]["url"]
    assert "v1" in p["primary_macro_sources"]["inflation"]["transport"]


def test_parse_fed_ip_total_index() -> None:
    payload=b'"B50001: Total index"\n"B50001" 1919 1 2 3 4 5 6 7 8 9 10 11 12\n"B50002" 1919 9 9 9 9 9 9 9 9 9 9 9 9\n'
    frame=parse_fed_ip(payload)
    assert len(frame)==12
    assert frame.iloc[0].to_dict()=={"year":1919.0,"month":1.0,"ip":1.0}
    assert frame.iloc[-1]["ip"]==12.0


def test_parse_bls_cpi_filters_target_and_months() -> None:
    payload=(
        "series_id\tyear\tperiod\tvalue\tfootnote_codes\n"
        "CUUR0000SA0\t1913\tM11\t9.8\t\n"
        "CUUR0000SA0\t1913\tM12\t10.0\t\n"
        "CUUR0000SA0\t1913\tM13\t9.9\t\n"
        "OTHER\t1913\tM12\t99\t\n"
    ).encode()
    frame=parse_bls_cpi(payload)
    assert list(frame["month"])==[11,12]
    assert list(frame["cpi"])==[9.8,10.0]


def test_annual_december_fails_to_substitute_other_months() -> None:
    ip=pd.DataFrame({"year":[1919,1919,1920,1920],"month":[11,12,11,12],"ip":[10,11,12,13]})
    cpi=pd.DataFrame({"year":[1919,1920],"month":[12,12],"cpi":[5,6]})
    annual=annual_december(ip,cpi,end_year=1920)
    assert list(annual["year"])==[1919,1920]
    assert list(annual["ip"])==[11,13]


def test_prior_window_excludes_current_observation() -> None:
    s=pd.Series([1.,2.,3.,4.,5.,100.])
    z=prior_window_z(s,5)
    expected=(100.0-3.0)/np.std([1.,2.,3.,4.,5.],ddof=0)
    assert np.isclose(z.iloc[-1],expected)


def test_thresholds_are_strict_outside_neutral_band() -> None:
    assert tri_state(-10.0)=="neutral"
    assert tri_state(10.0)=="neutral"
    assert tri_state(-10.0001)=="low"
    assert tri_state(10.0001)=="high"


def test_absolute_inflation_buckets() -> None:
    assert inflation_bucket(-0.1)=="deflation"
    assert inflation_bucket(0.0)=="low"
    assert inflation_bucket(2.0)=="moderate"
    assert inflation_bucket(4.0)=="high"
    assert inflation_bucket(6.0)=="very_high"


def test_build_hmra_contains_no_asset_return_columns() -> None:
    years=list(range(1919,1941))
    annual=pd.DataFrame({
        "year":years,
        "ip":np.exp(np.linspace(2.0,3.0,len(years))),
        "cpi":np.exp(np.linspace(1.0,1.8,len(years))),
    })
    out=build_hmra(annual)
    bad=("equity","treasury","t_bill","gold","spy","tlt","gld","asset_return")
    assert not any(any(token in c.lower() for token in bad) for c in out.columns)
    valid=out.loc[out["core_regime"].ne("n/a")]
    assert not valid.empty
    assert (valid["strict_causal_return_year"]==valid["year"]+2).all()
