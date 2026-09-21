from __future__ import annotations
from issue_99_phase_a0_proxy_source_schema import resolve_workbook_url

def test_resolve_workbook_url():
    html=b'<html><a href="/wp-content/uploads/proxy-funds-rate-data.xlsx?x=1">data</a></html>'
    got=resolve_workbook_url(html,"https://www.frbsf.org/research-and-insights/data-and-indicators/proxy-funds-rate/")
    assert got.startswith("https://www.frbsf.org/wp-content/uploads/proxy-funds-rate-data.xlsx")


import io
import pandas as pd
from issue_99_phase_a0_proxy_source_schema import parse_monthly_proxy

def test_parse_monthly_proxy():
    buf=io.BytesIO()
    frame=pd.DataFrame([
      ["Date","Effective funds rate","Proxy funds rate"],
      [pd.Timestamp("1976-06-30"),5.48,6.02],
      [pd.Timestamp("1976-07-31"),5.31,5.79],
    ])
    with pd.ExcelWriter(buf,engine="openpyxl") as w:
        pd.DataFrame([["x"]]).to_excel(w,sheet_name="Description",header=False,index=False)
        frame.to_excel(w,sheet_name="Monthly",header=False,index=False)
    out=parse_monthly_proxy(buf.getvalue(),"1976-07")
    assert len(out)==2
    assert out.iloc[-1]["date"].strftime("%Y-%m")=="1976-07"
