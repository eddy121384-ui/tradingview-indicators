from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from issue_117_source_freeze import (
    DEFENSIVE,
    GOLD_MIRROR_COMMIT,
    build_monthly_hmra,
    prior_z,
    tri_state,
)

HERE = Path(__file__).resolve().parent
PREREG = HERE / "decisions" / "issue-117-long-history-gold-cash-preregistered.md"


def test_prereg_core_contract_is_frozen():
    s = PREREG.read_text(encoding="utf-8")
    assert "PREREGISTERED BEFORE CONDITIONED GOLD-vs-CASH PAYOFF RESULTS" in s
    assert "trailing 60 monthly observations" in s
    assert "macro source month t-2" in s
    assert "Primary 3M outcome" in s
    assert "No conditioned Gold-vs-Cash payoff result had been computed" in s


def test_gold_transport_commit_is_pinned():
    assert GOLD_MIRROR_COMMIT == "95bfea9197222dcda13d8c4d9928fb631fe745aa"


def test_thresholds_are_exact():
    assert tri_state(-10.0001) == "low"
    assert tri_state(-10.0) == "neutral"
    assert tri_state(10.0) == "neutral"
    assert tri_state(10.0001) == "high"


def test_prior_z_excludes_current_observation():
    s = pd.Series(np.arange(61, dtype=float))
    z = prior_z(s, 60)
    expected = (60.0 - np.mean(np.arange(60.0))) / np.std(np.arange(60.0), ddof=0)
    assert np.isclose(z.iloc[60], expected)


def test_monthly_hmra_has_only_expected_defensive_semantics():
    dates = pd.date_range("1960-01-01", periods=200, freq="MS")
    ip = pd.DataFrame({"date":dates,"ip":100*np.exp(np.linspace(0,1,len(dates)))})
    cpi = pd.DataFrame({"date":dates,"cpi":50*np.exp(np.linspace(0,0.6,len(dates)))})
    out = build_monthly_hmra(ip,cpi)
    assert set(out.loc[out["defensive_gold_state"],"regime"]).issubset(DEFENSIVE)
