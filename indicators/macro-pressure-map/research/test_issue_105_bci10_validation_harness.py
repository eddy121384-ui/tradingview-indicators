from __future__ import annotations
from pathlib import Path

P=Path("bci10_intended_v01_fed_validation.pine")

def text():
    return P.read_text(encoding="utf-8")

def test_intended_sources_are_present():
    s=text()
    for token in [
        'request.economic("US", "BCOI")',
        'request.economic("US", "NMPMI")',
        'request.economic("US", "IRYY")',
        'request.economic("US", "CIR")',
        'request.security("FRED:PCEPILFE"',
        'request.security("FRED:JTSJOR"',
        'request.security("FRED:JTSQUR"',
    ]:
        assert token in s

def test_sign_repair_and_weights_are_frozen():
    s=text()
    assert "float r_hawk = -r_literal" in s
    assert "0.40 * p_axis + 0.40 * r_hawk + 0.20 * (p_axis * r_hawk)" in s
    assert "int ZLEN = 120" in s
    assert "float W_G_LEAD_PMI = 0.60" in s
    assert "float W_G_MFG = 0.35" in s
    assert "float W_I_PRICE = 0.70" in s
    assert "float W_L_CORE = 0.60" in s

def test_zscore_does_not_zero_fill_missing_history():
    s=text()
    assert 'na(m) or na(s) ? na : s == 0.0 ? 0.0' in s

def test_validation_alignment_is_preregistered():
    s=text()
    assert "float actual_6m = fed_funds - fed_funds[6]" in s
    assert "float sig_ps = ps_intended[8]" in s
    assert "bool frozen_end = year <= 2025" in s

def test_no_treasury_or_portfolio_outcomes():
    s=text().lower()
    forbidden=["treasury return","t-bill return","portfolio return","spy","tlt","gld"]
    assert all(x not in s for x in forbidden)


def test_core_pce_transport_amendment_is_documented_preoutcome():
    amendment = Path("decisions/issue-105-preoutcome-runtime-source-amendment.md").read_text(encoding="utf-8")
    assert "BEFORE ANY #105 OUTCOME WAS VIEWED" in amendment
    assert 'request.security("FRED:PCEPILFE", "M", close)' in amendment
    assert 'request.economic("US", "CPCEPI")' in amendment
