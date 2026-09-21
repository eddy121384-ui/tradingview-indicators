from __future__ import annotations
import json
from pathlib import Path

P=Path("decisions/issue-103-bci10-v15-audit.json")

def load():
    return json.loads(P.read_text(encoding="utf-8"))

def test_preoutcome_boundary():
    p=load()
    assert p["created_before_fed_validation"] is True
    assert p["created_before_treasury_validation"] is True
    assert p["production_v66_modified"] is False

def test_literal_formulas_frozen():
    p=load()
    assert p["literal_formulas"]["p_axis"]=="0.5*z_rir + 0.3*i_axis + 0.2*(-z_uergap)"
    assert p["literal_formulas"]["r_axis"].startswith("0.25*(-g_lead)")
    assert p["literal_formulas"]["ps_axis"]=="0.4*p_axis + 0.4*r_axis + 0.2*(p_axis*r_axis)"

def test_sign_conflict_is_explicit():
    p=load()
    assert p["sign_semantics"]["p_axis"]["positive_interpretation"]=="more restrictive / more hawkish"
    assert p["sign_semantics"]["r_axis"]["inferred_positive_interpretation"]=="greater easing / dovish pressure"
    assert p["phase_a0_decisions"]["ps_sign_semantics"]=="internally_conflicted"
    assert p["phase_a0_decisions"]["literal_model_validation_allowed"] is False

def test_known_source_mismatches_are_frozen():
    p=load()
    by_symbol={x["original_symbol"]:x for x in p["source_audit"]}
    assert by_symbol["ECONOMICS:USNMPR"]["status"]=="semantic_mismatch"
    assert by_symbol["ECONOMICS:USPCEPIAC"]["status"]=="semantic_mismatch_and_double_yoy_transform_risk"
    assert by_symbol["FRED:JTSJOL"]["status"]=="unit_comment_mismatch"
    assert by_symbol["FRED:JTSQUR"]["status"]=="concept_match"

def test_no_silent_literal_repair():
    p=load()
    mismatches=[x for x in p["source_audit"] if "mismatch" in x["status"]]
    assert mismatches
    for x in mismatches:
        if "literal_repair_allowed" in x:
            assert x["literal_repair_allowed"] is False
