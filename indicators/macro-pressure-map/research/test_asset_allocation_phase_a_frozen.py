from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from asset_allocation_phase_a import REGIMES
from asset_allocation_phase_a_frozen import (
    SIGNAL_LAST_DATE,
    load_frozen_transitions,
    map_regimes_to_outcome_calendar,
)
from build_issue_64_frozen_regimes import derive_axis_audit, sha256_file

HERE = Path(__file__).resolve().parent
AXIS_AUDIT = HERE / "data" / "issue-64-frozen-axis-audit.csv"
EXPECTED_AXIS_AUDIT_SHA256 = "9021844c7ed0b927ce95ca3de117ac3749eb3c5541e5d6c46557aa5624fa08c1"


def test_committed_transition_artifact_is_hash_verified_and_well_formed() -> None:
    transitions = load_frozen_transitions()
    assert len(transitions) == 739
    assert transitions.iloc[0]["start_date"] == pd.Timestamp("2007-01-04")
    assert transitions.iloc[-1]["start_date"] == pd.Timestamp("2026-08-07")
    assert transitions["regime_id"].between(1, 9).all()


def test_committed_axis_audit_is_hash_verified_and_includes_fcpi() -> None:
    assert sha256_file(AXIS_AUDIT) == EXPECTED_AXIS_AUDIT_SHA256
    audit = pd.read_csv(AXIS_AUDIT)
    assert list(audit.columns) == ["date", "GPI", "IPI", "FCPI", "regime_id"]
    assert len(audit) == 51
    assert audit.iloc[0]["date"] == "2007-01-04"
    assert audit.iloc[-1]["date"] == "2026-08-14"
    assert audit["FCPI"].notna().all()


def test_axis_audit_sampling_is_deterministic() -> None:
    idx = pd.date_range("2020-01-01", periods=205, freq="D")
    daily = pd.DataFrame(
        {
            "GPI": np.arange(205, dtype=float),
            "IPI": np.arange(205, dtype=float) + 1.0,
            "FCPI": np.arange(205, dtype=float) + 2.0,
            "regime_id": np.ones(205, dtype=int),
        },
        index=idx,
    )
    daily.index.name = "date"
    audit = derive_axis_audit(daily, stride=100)
    assert audit["date"].tolist() == [idx[0], idx[100], idx[200], idx[204]]


def test_regime_mapping_uses_latest_known_transition() -> None:
    idx = pd.to_datetime(["2007-01-04", "2007-01-05", "2007-01-12", "2007-01-16"])
    prices = pd.DataFrame({"SPY": 1.0, "TLT": 1.0, "GLD": 1.0}, index=idx)
    history = map_regimes_to_outcome_calendar(prices, load_frozen_transitions())
    assert history.loc[pd.Timestamp("2007-01-04"), "core_regime"] == REGIMES[6]
    assert history.loc[pd.Timestamp("2007-01-05"), "core_regime"] == REGIMES[6]
    assert history.loc[pd.Timestamp("2007-01-12"), "core_regime"] == REGIMES[3]
    assert history.loc[pd.Timestamp("2007-01-16"), "core_regime"] == REGIMES[6]


def test_mapping_normalizes_second_precision_outcome_dates() -> None:
    idx = pd.DatetimeIndex(
        np.asarray(["2007-01-04", "2007-01-05", "2007-01-12"], dtype="datetime64[s]")
    )
    assert str(idx.dtype) == "datetime64[s]"
    prices = pd.DataFrame({"SPY": 1.0, "TLT": 1.0, "GLD": 1.0}, index=idx)
    history = map_regimes_to_outcome_calendar(prices, load_frozen_transitions())
    assert str(history.index.dtype) == "datetime64[ns]"
    assert history.loc[pd.Timestamp("2007-01-04"), "core_regime"] == REGIMES[6]
    assert history.loc[pd.Timestamp("2007-01-12"), "core_regime"] == REGIMES[3]


def test_signal_is_not_forward_filled_past_frozen_cutoff() -> None:
    idx = pd.to_datetime(["2026-08-13", "2026-08-14", "2026-08-17", "2026-08-18"])
    prices = pd.DataFrame({"SPY": 1.0, "TLT": 1.0, "GLD": 1.0}, index=idx)
    history = map_regimes_to_outcome_calendar(prices, load_frozen_transitions())
    assert SIGNAL_LAST_DATE == pd.Timestamp("2026-08-14")
    assert history.loc[pd.Timestamp("2026-08-14"), "core_regime"] == REGIMES[1]
    assert pd.isna(history.loc[pd.Timestamp("2026-08-17"), "core_regime"])
    assert pd.isna(history.loc[pd.Timestamp("2026-08-18"), "core_regime"])
