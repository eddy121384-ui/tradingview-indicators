"""Tests for the A5 OOS4 validation analyzer.

Guards: A5 reuses frozen A4 machinery by identity (no redefinition), the
OOS4 cohort constant matches the preregistered freeze, and paired specs
are the A4 specs. No OOS4 outcomes are asserted here.
"""
import analyze_issue78_causal_core2_a4 as a4
import analyze_issue78_oos4_validation_a5 as a5


def test_cell_machinery_is_frozen_a4():
    assert a5.econ_cells is a4.econ_cells
    assert a5.fidelity_rows is a4.fidelity_rows
    assert a5.fidelity_summary is a4.fidelity_summary
    assert a5.aggregate_a1_cells is a4.aggregate_a1_cells
    assert a5.paired_deltas is a4.paired_deltas
    assert a5.PAIRED_SPECS == a4.PAIRED_SPECS


def test_oos4_cohort_constant_matches_freeze():
    assert a5.EXPECTED_OOS4_FIGI_SET_SHA == (
        "b0c9423a6e3e5cbd61dcd17dc1a9c5a0fc50b8bc00286ba3a5b86f560209ca49"
    )
    assert a5.HORIZONS == (1, 5, 10, 20)
    assert a5.MIN_CELL_BARS == 5
    assert a5.MIN_AGG_STOCKS == 30
    assert a4.WARMUP_MIN == 252


def test_no_threshold_drift_vs_prereg():
    import numpy as np
    import pandas as pd

    frame = pd.DataFrame(
        {
            "causal_ready": [True] * 6,
            "rank_c_struct": [0.85, 0.75, 0.65, 0.25, 0.15, 0.5],
            "rank_c_ext": [0.1, 0.1, 0.1, 0.9, 0.9, 0.5],
        }
    )
    hard = a4._causal_masks(frame, True)
    assert hard["bull_low"][0].tolist() == [True] + [False] * 5
    assert hard["bear_high"][0].tolist() == [False] * 4 + [True, False]
    rel = a4._causal_masks(frame, False)
    assert rel["bull_low"][0].tolist() == [True, True, False] + [False] * 3
