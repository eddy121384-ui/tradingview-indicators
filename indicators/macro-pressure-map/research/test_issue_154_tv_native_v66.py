#!/usr/bin/env python3
from __future__ import annotations

import pandas as pd

from issue_154_tv_native_v66 import (
    SOURCE_MAP,
    regime_id,
    verdict_from_metrics,
)


def test_exact_symbol_set_is_frozen():
    assert set(SOURCE_MAP) == {
        "AMEX:SPY", "AMEX:IWM", "AMEX:RSP", "AMEX:XLY", "AMEX:XLP",
        "AMEX:XLI", "AMEX:XLU", "COMEX:HG1!", "COMEX:GC1!",
        "FRED:T10YIE", "AMEX:DBC", "NYMEX:CL1!", "NYMEX:RB1!",
    }


def test_regime_mapping_r7():
    assert regime_id(-11.0, -11.0) == 7
    assert regime_id(-10.0, -11.0) == 4
    assert regime_id(-11.0, -10.0) == 8


def test_parity_verdict_passes_only_all_gates():
    m = {
        "common_months": 200,
        "gpi_correlation": 0.999,
        "ipi_correlation": 0.999,
        "gpi_mae": 0.2,
        "ipi_mae": 0.2,
        "regime_agreement": 0.99,
        "r7": {"precision": 0.95, "recall": 0.95},
        "triggers": {"f1": 0.9, "count_ratio": 1.0},
    }
    verdict, gates = verdict_from_metrics(m)
    assert verdict == "tv_native_reconstruction_passed"
    assert all(gates.values())

    m["ipi_correlation"] = 0.994
    verdict, gates = verdict_from_metrics(m)
    assert verdict == "tv_native_reconstruction_failed"
    assert not gates["ipi_corr_ge_0_995"]


def test_sample_gate_is_inconclusive():
    m = {
        "common_months": 179,
        "gpi_correlation": 1.0,
        "ipi_correlation": 1.0,
        "gpi_mae": 0.0,
        "ipi_mae": 0.0,
        "regime_agreement": 1.0,
        "r7": {"precision": 1.0, "recall": 1.0},
        "triggers": {"f1": 1.0, "count_ratio": 1.0},
    }
    verdict, _ = verdict_from_metrics(m)
    assert verdict == "tv_native_reconstruction_inconclusive_sample"
