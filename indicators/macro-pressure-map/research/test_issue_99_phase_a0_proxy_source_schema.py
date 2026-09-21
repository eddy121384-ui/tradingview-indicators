from __future__ import annotations
from issue_99_phase_a0_proxy_source_schema import resolve_workbook_url

def test_resolve_workbook_url():
    html=b'<html><a href="/wp-content/uploads/proxy-funds-rate-data.xlsx?x=1">data</a></html>'
    got=resolve_workbook_url(html,"https://www.frbsf.org/research-and-insights/data-and-indicators/proxy-funds-rate/")
    assert got.startswith("https://www.frbsf.org/wp-content/uploads/proxy-funds-rate-data.xlsx")
