from __future__ import annotations

import numpy as np
import pandas as pd

from issue_107_continuous_policy_reaction import (
    MODELS,
    _download_fred_mirror,
    complete_case_mask,
    standardize_fit_predict,
    trajectory_features,
)


def test_model_ladder_matches_prereg():
    assert MODELS["M0"] == ["GPI", "IPI"]
    assert MODELS["M1"] == ["GPI", "IPI", "real_policy_rate"]
    assert len(MODELS["M2"]) == 9


def test_trajectory_reuses_20_63_and_acceleration():
    idx = pd.date_range("2020-01-01", periods=100, freq="D")
    x = np.arange(100.0)
    frame = pd.DataFrame({"GPI": x, "IPI": 2.0 * x}, index=idx)
    out = trajectory_features(frame, 20, 63)
    row = out.iloc[-1]
    assert np.isclose(row["fast_slope_GPI"], 1.0)
    assert np.isclose(row["mid_slope_GPI"], 1.0)
    assert np.isclose(row["acceleration_GPI"], 0.0)
    assert np.isclose(row["fast_slope_IPI"], 2.0)
    assert np.isclose(row["mid_slope_IPI"], 2.0)
    assert np.isclose(row["acceleration_IPI"], 0.0)


def test_standardized_ols_predicts_linear_relation():
    n = 60
    a = np.arange(n, dtype=float)
    b = (a % 7.0) - 3.0
    train = pd.DataFrame({"a": a, "b": b})
    train["y"] = 1.5 + 0.2 * train["a"] - 0.7 * train["b"]
    row_b = (61.0 % 7.0) - 3.0
    row = pd.Series({"a": 61.0, "b": row_b})
    pred, _ = standardize_fit_predict(train, row, ["a", "b"], "y")
    assert np.isclose(pred, 1.5 + 0.2 * 61.0 - 0.7 * row_b)


def test_complete_case_is_common_m2_universe():
    cols = MODELS["M2"] + ["outcome_6m"]
    frame = pd.DataFrame([{c: 1.0 for c in cols}, {c: 1.0 for c in cols}])
    frame.loc[1, "acceleration_IPI"] = np.nan
    mask = complete_case_mask(frame)
    assert mask.tolist() == [True, False]


def test_pcepilfe_frozen_snapshot_preserves_official_index_values():
    series = _download_fred_mirror("PCEPILFE", "2020-01-01", "2020-04-01")
    assert series.index.tolist() == [
        pd.Timestamp("2020-01-01"),
        pd.Timestamp("2020-02-01"),
        pd.Timestamp("2020-03-01"),
    ]
    assert np.allclose(series.to_numpy(), [104.507, 104.711, 104.632])
