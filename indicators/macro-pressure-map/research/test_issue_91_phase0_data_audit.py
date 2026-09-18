from __future__ import annotations

import io
import json
from pathlib import Path

import pandas as pd
import pytest

from issue_91_phase0_data_audit import (
    audit_fred_csv,
    audit_fred_table_page,
    audit_jst_xlsx,
    first_last_numeric_year,
    validate_plan,
)


def test_plan_forbids_etfs_and_outcome_analysis() -> None:
    path = Path("decisions/issue-91-phase0-source-plan.json")
    plan = json.loads(path.read_text(encoding="utf-8"))
    validate_plan(plan)
    assert plan["etf_use_in_primary_long_history_analysis"] is False
    assert plan["created_before_regime_conditioned_asset_results"] is True
    assert all(source["etf"] is False for source in plan["sources"])
    assert "regime-conditioned asset returns" in " ".join(plan["phase0_output_policy"]["forbidden_outputs"])


def test_validate_plan_rejects_etf_source() -> None:
    plan = {
        "issue":91,
        "phase":"0-source-audit",
        "created_before_regime_conditioned_asset_results":True,
        "etf_use_in_primary_long_history_analysis":False,
        "sources":[{"id":"SPY","etf":True}],
    }
    with pytest.raises(ValueError, match="ETF source leaked"):
        validate_plan(plan)


def test_fred_audit_uses_only_finite_observations() -> None:
    payload = b"observation_date,CPIAUCSL\n1947-01-01,21.5\n1947-02-01,.\n1947-03-01,22.0\n"
    result = audit_fred_csv(payload, "CPIAUCSL")
    assert result["first_observation"] == "1947-01-01"
    assert result["last_observation"] == "1947-03-01"
    assert result["usable_observations"] == 2


def test_first_last_numeric_year_ignores_summary_rows() -> None:
    first,last,rows = first_last_numeric_year(pd.Series(["Year",1928,1929,"Average",2025]))
    assert (first,last,rows) == (1928,2025,3)


def test_jst_audit_finds_usa_total_return_columns() -> None:
    frame = pd.DataFrame({
        "year":[1870,1871,1870,1871],
        "iso":["USA","USA","GBR","GBR"],
        "cpi":[10.0,10.1,9.0,9.2],
        "eq_tr":[0.05,0.06,0.04,0.03],
        "bond_tr":[0.03,0.02,0.02,0.01],
        "bill_rate":[0.02,0.02,0.01,0.01],
        "stir":[2.0,2.1,1.0,1.1],
        "rgdppc":[100.0,102.0,90.0,91.0],
        "ltrate":[3.0,3.1,2.0,2.1],
    })
    buf=io.BytesIO()
    with pd.ExcelWriter(buf,engine="openpyxl") as writer:
        frame.to_excel(writer,index=False,sheet_name="Data")
    result=audit_jst_xlsx(buf.getvalue())
    assert result["first_year"] == 1870
    assert result["last_year"] == 1871
    assert result["usa_rows"] == 2
    assert result["candidate_coverage"]["equity_total_return"]["usable_observations"] == 2
    assert result["candidate_coverage"]["government_bond_total_return"]["usable_observations"] == 2


def test_fred_table_page_audit_reads_date_value_table() -> None:
    payload = b"""<html><body><table><thead><tr><th>DATE</th><th>VALUE</th></tr></thead>
    <tbody><tr><td>1919-01-01</td><td>4.8</td></tr><tr><td>1919-02-01</td><td>4.9</td></tr></tbody></table></body></html>"""
    result = audit_fred_table_page(payload, "INDPRO")
    assert result["first_observation"] == "1919-01-01"
    assert result["last_observation"] == "1919-02-01"
    assert result["usable_observations"] == 2
