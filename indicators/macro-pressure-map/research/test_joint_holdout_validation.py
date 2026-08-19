#!/usr/bin/env python3
from __future__ import annotations

import pandas as pd

from joint_holdout_validation import HORIZON, embargo_pair, evaluation_indices


def test_embargo_pair_blocks_overlapping_forward_windows_across_signs() -> None:
    index = pd.bdate_range("2020-01-01", periods=50)
    positive = pd.Series(False, index=index)
    negative = pd.Series(False, index=index)
    positive.iloc[[0, 10, 20, 40]] = True
    negative.iloc[[5, 21, 41]] = True

    kept_positive, kept_negative = embargo_pair(positive, negative, index, HORIZON)

    accepted = [
        position
        for position in range(len(index))
        if kept_positive.iloc[position] or kept_negative.iloc[position]
    ]
    assert accepted == [0, 20, 40]
    assert all(b - a >= HORIZON for a, b in zip(accepted, accepted[1:]))


def test_training_evaluation_purges_horizon_before_holdout() -> None:
    index = pd.bdate_range("2019-10-01", "2020-02-28")
    frame = pd.DataFrame({"dummy": range(len(index))}, index=index)

    train_eval_index, holdout_index, train_for_cuts = evaluation_indices(frame)

    assert train_for_cuts.index.max() == pd.Timestamp("2019-12-31")
    assert len(train_for_cuts) - len(train_eval_index) == HORIZON
    assert train_eval_index.max() == train_for_cuts.index[-HORIZON - 1]
    assert holdout_index.min() == pd.Timestamp("2020-01-01")
