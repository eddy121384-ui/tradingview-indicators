from __future__ import annotations

import numpy as np
import pandas as pd

from asset_allocation_phase_a import REGIMES
from asset_allocation_phase_a_frozen import (
    SIGNAL_LAST_DATE,
    load_frozen_transitions,
    map_regimes_to_outcome_calendar,
)


def test_committed_transition_artifact_is_hash_verified_and_well_formed() -> None:
    transitions = load_frozen_transitions()
    assert len(transitions) == 739
    assert transitions.iloc[0]["start_date"] == pd.Timestamp("2007-01-04")
    assert transitions.iloc[-1]["start_date"] == pd.Timestamp("2026-08-07")
    assert transitions["regime_id"].between(1, 9).all()


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
