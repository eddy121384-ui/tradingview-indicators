from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from issue_121_long_history_rematch import (
    SPREADS,
    classify_cell,
    sign_of,
)

HERE = Path(__file__).resolve().parent
PREREG = HERE / "decisions" / "issue-121-phase1-long-history-rematch-preregistered.md"


def test_prereg_is_bound_before_results():
    s = PREREG.read_text(encoding="utf-8")
    assert "PREREGISTERED BEFORE ISSUE #121 REMATCH CLASSIFICATIONS" in s
    assert "state_t -> annual spread return_{t+2}" in s
    assert "strongest-era share <= 0.50" in s
    assert "No Issue #121 rematch classification had been computed" in s


def test_spreads_are_exact():
    assert set(SPREADS) == {
        "equity_minus_treasury",
        "treasury_minus_cash",
        "gold_minus_cash",
    }
    assert SPREADS["gold_minus_cash"]["min_return_year"] == 1975


def test_sign_of():
    assert sign_of(1.0) == 1
    assert sign_of(-1.0) == -1
    assert sign_of(0.0) == 0


def _sample(mean: float, eras: list[str], n_per: int = 4) -> pd.DataFrame:
    vals = []
    for e in eras:
        vals.extend([(e, mean)] * n_per)
    return pd.DataFrame({"era":[x[0] for x in vals],"spread":[x[1] for x in vals]})


def test_clear_stable_positive_can_revive():
    structural = _sample(0.10, ["a","b","c"], 4)
    causal = _sample(0.12, ["a","b","c"], 4)
    result = classify_cell(
        structural,
        causal,
        spread="equity_minus_treasury",
        regime="synthetic",
    )
    assert result["classification"] == "revived_long_history_candidate"
    assert result["causal_direction"] == "equity > treasury"


def test_small_causal_effect_remains_unconfirmed():
    structural = _sample(0.001, ["a","b","c"], 4)
    causal = pd.DataFrame({
        "era":["a"]*4+["b"]*4+["c"]*4,
        "spread":[0.1,-0.1,0.1,-0.1]*3,
    })
    result = classify_cell(
        structural,
        causal,
        spread="treasury_minus_cash",
        regime="synthetic",
    )
    assert result["classification"] in {
        "remains_unconfirmed",
        "long_history_structural_but_timing_unstable",
    }
