#!/usr/bin/env python3
from __future__ import annotations

import pandas as pd

from joint_holdout_validation import HORIZON, OUTCOMES, embargo_pair, evaluation_indices, render_markdown


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


def test_development_evaluation_purges_horizon_before_post_2019() -> None:
    index = pd.bdate_range("2019-10-01", "2020-02-28")
    frame = pd.DataFrame({"dummy": range(len(index))}, index=index)

    development_index, post_2019_index, train_for_cuts = evaluation_indices(frame)

    assert train_for_cuts.index.max() == pd.Timestamp("2019-12-31")
    assert len(train_for_cuts) - len(development_index) == HORIZON
    assert development_index.max() == train_for_cuts.index[-HORIZON - 1]
    assert post_2019_index.min() == pd.Timestamp("2020-01-01")


def test_generated_joint_report_preserves_exploratory_boundary() -> None:
    stats = {
        "n_positive": 5,
        "n_negative": 5,
        "mean_positive": 1.0,
        "mean_negative": 0.0,
        "spread": 1.0,
        "ci95_low": -1.0,
        "ci95_high": 2.0,
    }
    outcomes = {
        outcome: {
            "joint_reflation_minus_slowdown": dict(stats),
            "gpi_high_minus_low": dict(stats),
            "ipi_high_minus_low": dict(stats),
        }
        for outcome in OUTCOMES
    }
    report = {
        "design": {
            "threshold_definition_start": "2008-06-02",
            "threshold_definition_end": "2019-12-31",
            "development_eval_end": "2019-12-02",
            "post_2019_start": "2020-01-02",
            "post_2019_end": "2026-08-14",
            "post_2019_status": "exploratory_reused_era_not_untouched_holdout",
            "cuts": {
                "axis_gpi_change20": (-21.0, 19.5),
                "axis_ipi_change20": (-21.2, 22.5),
            },
            "horizon": HORIZON,
            "event_embargo_trading_rows": HORIZON,
            "development_tail_purged_trading_rows": HORIZON,
        },
        "periods": {
            "development": {
                "event_counts": {
                    "reflation_impulse": 5,
                    "slowdown_disinflation_impulse": 5,
                },
                "outcomes": outcomes,
            },
            "post_2019_exploratory": {
                "event_counts": {
                    "reflation_impulse": 5,
                    "slowdown_disinflation_impulse": 5,
                },
                "outcomes": outcomes,
            },
        },
    }

    text = render_markdown(report)

    assert "JOINT-AXIS EXPLORATORY STUDY COMPLETE" in text
    assert "reused historical evidence, not an untouched holdout" in text
    assert "Post-2019 exploratory era" in text
    assert "JOINT-AXIS HOLDOUT COMPLETE" not in text
    assert "Holdout:" not in text
