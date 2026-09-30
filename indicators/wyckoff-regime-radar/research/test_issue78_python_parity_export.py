from __future__ import annotations

from pathlib import Path

import generate_issue78_python_parity_export_pine as m


def frozen_source() -> Path:
    return Path(__file__).resolve().parents[1] / "src" / m.base.SOURCE_NAME


def test_parity_generator_keeps_frozen_source_contract():
    text = m.generate(frozen_source())
    assert "#78 PY PARITY" in text
    assert "calc_bars_count=10000" in text
    assert "formalId = confirmedId" in text
    assert "symATR  = ta.rma(modelTR, atrLen)" in text


def test_parity_channels_exist():
    text = m.generate(frozen_source())
    assert '"PARITY formalId"' in text
    assert '"PARITY confirmedId"' in text
    assert '"PARITY symATR"' in text
    assert '"PARITY useYieldLevel"' in text
    assert '"PARITY volume"' in text
    assert '"PARITY volumeQuality"' in text
    assert '"PARITY volumeWeight"' in text
    assert '"PARITY accGate"' in text
    assert '"PARITY probMarkup"' in text
    assert '"PARITY candidateDisplayId"' in text
    assert '"PARITY stalePressureBars"' in text


def test_observe_only_mtf_requests_are_removed():
    text = m.generate(frozen_source())
    assert 'mtfMode = input.string("Observe Only"' in text
    assert "request.security_lower_tf" not in text
    assert text.count("array.new_float(0)") >= 8


def test_parity_export_contains_no_strategy_calls():
    text = m.generate(frozen_source())
    assert "strategy.entry" not in text
    assert "strategy.close" not in text
