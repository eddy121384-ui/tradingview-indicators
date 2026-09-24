from __future__ import annotations

from pathlib import Path

import generate_issue76_forward_behavior_logger_pine as base
import generate_issue78_python_parity_log_pine as m
from parse_issue78_python_parity_logs import LOG_COLUMNS, parse_text


def frozen_source() -> Path:
    return Path(__file__).resolve().parents[1] / "src" / base.SOURCE_NAME


def test_log_harness_is_parent_plus_transport():
    text = m.generate(frozen_source())
    assert '#78 PY PARITY LOG' in text
    assert '"I78P1" + "|" + syminfo.tickerid' in text
    assert 'input.int(2500, "Parity log capture bars"' in text
    assert "log.info(" in text
    assert "f_i78pNum(volume)" in text
    assert "f_i78pNum(float(formalId))" in text
    assert "f_i78pNum(symATR)" in text
    assert "f_i78pNum(volumeQualityScore)" in text
    assert "strategy.entry" not in text
    assert '"PARITY formalId"' not in text
    assert "request.security_lower_tf" not in text


def test_parser_accepts_plain_pine_log_line():
    values = [
        "NASDAQ:AAPL", "1D", "1700000000000", "100", "103", "99", "102", "1234567"
    ] + [str(i) for i in range(len(m.FIELDS))]
    frame = parse_text("noise\nINFO I78P1|" + "|".join(values) + "\n")
    assert len(frame) == 1
    assert frame.iloc[0]["ticker"] == "NASDAQ:AAPL"
    assert frame.iloc[0]["tf"] == "1D"
    assert frame.iloc[0]["close"] == 102.0
    field_index = {name: i for i, (name, _) in enumerate(m.FIELDS)}
    assert frame.iloc[0]["PARITY formalId"] == float(field_index["formalId"])


def test_parser_accepts_tradingview_csv_wrapper_and_deduplicates():
    values = [
        "NASDAQ:AAPL", "1D", "1700000000000", "100", "103", "99", "102", "1234567"
    ] + [str(i) for i in range(len(m.FIELDS))]
    msg = "I78P1|" + "|".join(values)
    text = '日期,訊息\n2026-09-24T00:00:00+08:00,"' + msg + '"\n2026-09-24T00:00:01+08:00,"' + msg + '"\n'
    frame = parse_text(text)
    assert len(frame) == 1
    assert "PARITY useYieldLevel" in frame.columns
    assert set(["ticker","tf","time","open","high","low","close","volume"]).issubset(frame.columns)


def test_parser_schema_matches_fields():
    assert len(LOG_COLUMNS) == 8 + len(m.FIELDS)


def test_log_only_build_does_not_add_plot_budget():
    text = m.generate(frozen_source())
    frozen = frozen_source().read_text(encoding="utf-8")
    # The logger should inherit only the frozen RC's own visuals; it must not
    # add the 29 plot-based parity channels from the chart-export harness.
    assert text.count("plot(") == frozen.count("plot(")
    assert text.count("plotshape(") == frozen.count("plotshape(")
    assert text.count("plotchar(") == frozen.count("plotchar(")
