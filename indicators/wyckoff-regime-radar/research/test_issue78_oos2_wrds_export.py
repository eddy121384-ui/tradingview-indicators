from __future__ import annotations

import pytest

from issue78_oos2_wrds_export import TABLE_CANDIDATES, _queries, choose_table, qident


def test_choose_table_prefers_documented_wrds_view():
    available = ["dsf_v2", "stkSecurityInfoHist", "stkDlyCumulativeAdjFactor", "stkDelists"]
    assert choose_table(available, TABLE_CANDIDATES["daily"]) == "dsf_v2"
    assert choose_table(available, TABLE_CANDIDATES["info_hist"]) == "stkSecurityInfoHist"


def test_choose_table_fails_closed():
    with pytest.raises(RuntimeError):
        choose_table(["other_table"], ("wanted",))


def test_queries_pin_dates_and_do_not_contain_economics():
    tables = {
        "daily": "dsf_v2",
        "factors": "stkdlycumulativeadjfactor",
        "info_hist": "stksecurityinfohist",
        "delists": "stkdelists",
    }
    q = _queries("crsp_m_stock", tables)
    joined = "\n".join(q.values()).lower()
    assert "1998-01-01" in joined
    assert "2026-08-31" in joined
    assert "warning-first" not in joined
    assert "r0" not in joined


def test_sql_identifier_rejects_punctuation():
    with pytest.raises(ValueError):
        qident("crsp;drop")
