from __future__ import annotations
from issue_97_phase_a0_source_audit import parse_h15_effr

def test_parse_h15_effr() -> None:
    payload=b'"Unique Identifier: ","H15/H15/RIFSPFF_N.M"\n"Time Period","RIFSPFF_N.M"\n1954-07,0.80\n1954-08,1.22\n'
    out=parse_h15_effr(payload)
    assert len(out)==2
    assert out.iloc[0]["month"].strftime("%Y-%m")=="1954-07"
    assert float(out.iloc[1]["effr"])==1.22
