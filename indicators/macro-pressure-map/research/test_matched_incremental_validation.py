#!/usr/bin/env python3
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from matched_incremental_validation import (
    CURATED_DECISION_JSON,
    CURATED_DECISION_MD,
    DEFAULT_OUTPUT_JSON,
    DEFAULT_OUTPUT_MD,
    GENERATED_DIR,
    _assert_not_curated_output,
    matched_lift_stats,
)


def test_matched_lift_uses_same_anchor_event_universe() -> None:
    events = pd.DataFrame(
        {
            "sign": [1, 1, 1, 1, 1, 1, -1, -1, -1, -1, -1, -1],
            "aligned": [False, False, False, True, True, True] * 2,
            "us10y_tvc": [1.0, 1.0, 1.0, 10.0, 10.0, 10.0, -1.0, -1.0, -1.0, -10.0, -10.0, -10.0],
        },
        index=pd.bdate_range("2020-01-01", periods=12),
    )

    stats = matched_lift_stats(events, "us10y_tvc", draws=1000, seed=123)

    assert stats["n_positive"] == 6
    assert stats["n_negative"] == 6
    assert stats["n_aligned_positive"] == 3
    assert stats["n_aligned_negative"] == 3
    assert np.isclose(stats["anchor_all_spread"], 11.0)
    assert np.isclose(stats["aligned_spread"], 20.0)
    assert np.isclose(stats["aligned_minus_all"], 9.0)
    assert stats["bootstrap_valid_draws"] > 0


def test_generated_outputs_default_outside_curated_decisions() -> None:
    assert DEFAULT_OUTPUT_JSON.parent == GENERATED_DIR
    assert DEFAULT_OUTPUT_MD.parent == GENERATED_DIR
    assert DEFAULT_OUTPUT_JSON.name.endswith(".generated.json")
    assert DEFAULT_OUTPUT_MD.name.endswith(".generated.md")


def test_curated_decision_paths_cannot_be_overwritten_by_generator(tmp_path) -> None:
    with pytest.raises(ValueError, match="generated evidence only"):
        _assert_not_curated_output(CURATED_DECISION_JSON)
    with pytest.raises(ValueError, match="generated evidence only"):
        _assert_not_curated_output(CURATED_DECISION_MD)

    _assert_not_curated_output(tmp_path / "matched.generated.json")
