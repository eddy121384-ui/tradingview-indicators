from __future__ import annotations
import json
from pathlib import Path

P=Path("decisions/issue-105-bci10-intended-v0.1-preregistered.json")

def load():
    return json.loads(P.read_text(encoding="utf-8"))

def test_preoutcome_boundary():
    p=load()
    assert p["created_before_fed_validation_results"] is True
    assert p["created_before_treasury_results"] is True
    assert p["treasury_validation_in_scope"] is False

def test_core_repairs_locked():
    p=load()
    s=p["source_repairs"]
    assert s["manufacturing_pmi"]["intended"]=="TradingView request.economic('US','BCOI')"
    assert s["services_pmi"]["intended"]=="TradingView request.economic('US','NMPMI')"
    assert s["core_pce"]["intended"]=="TradingView request.economic('US','CPCEPI')"
    assert s["jolts_openings"]["intended"]=="FRED:JTSJOR rate"

def test_sign_repair_locked():
    p=load()
    assert p["formulas"]["r_hawk"]=="-1 * r_literal"
    assert p["sign_semantics"]["p_axis_positive"]=="hawkish/restrictive"
    assert p["sign_semantics"]["r_hawk_positive"]=="hawkish/tightening momentum"
    assert p["formulas"]["ps_intended"]=="0.4*p_axis + 0.4*r_hawk + 0.2*(p_axis*r_hawk)"

def test_original_defaults_unchanged():
    p=load()
    assert p["frozen_defaults"]=={
      "zscore_period_months":120,
      "nairu_percent":4.0,
      "w_g_lead_pmi":0.60,
      "w_g_mfg":0.35,
      "w_i_price":0.70,
      "w_l_core":0.60
    }

def test_validation_timing_and_no_treasury():
    p=load()
    assert p["validation_timing"]["signal_month"]=="m-2"
    assert p["validation_timing"]["primary_outcome"]=="FEDFUNDS[m+6] - FEDFUNDS[m]"
    assert "Do not add Treasury or portfolio returns." in p["hard_rules"]

def test_short_sample_warning_is_explicit():
    p=load()
    assert p["normalization_and_sample"]["expected_full_surface_start_no_earlier_than"]=="2017-02"
    assert "No structural multi-era claim is permitted." in p["normalization_and_sample"]["warning"]
