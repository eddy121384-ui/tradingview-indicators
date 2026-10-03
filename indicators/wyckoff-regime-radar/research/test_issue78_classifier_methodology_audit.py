from __future__ import annotations

import numpy as np

import analyze_issue78_classifier_methodology_audit as m


def test_formal_age_resets_on_change_and_zero():
    ids = [0, 2, 2, 2, 0, 2, 2, 5, 5, 5, 5]
    assert m.formal_age(ids).tolist() == [
        0, 0, 1, 2, 0, 0, 1, 0, 1, 2, 3
    ]


def test_family_scores_are_frozen_sums():
    p = np.array(
        [
            [10, 20, 30, 5, 25, 10],
            [15, 5, 5, 20, 35, 20],
        ],
        dtype=float,
    )
    got = m.family_scores(p)
    assert np.allclose(
        got,
        np.array(
            [
                [50, 15, 35],
                [10, 35, 55],
            ],
            dtype=float,
        ),
    )


def test_winner_ids_use_left_to_right_tie_priority():
    values = np.array(
        [
            [5.0, 5.0, 4.0],
            [1.0, 3.0, 3.0],
        ]
    )
    top, second = m.winner_ids(values)
    assert top.tolist() == [1, 2]
    assert second.tolist() == [2, 3]


def test_frozen_methodology_contract():
    assert m.HORIZONS == (1, 5, 10, 20)
    assert m.MIN_CELL_BARS == 5
    assert m.MIN_AGG_STOCKS == 30
    assert m.STAGES[2] == "Markup"
    assert m.STAGES[5] == "Markdown"
    assert m.EXPECTED_FIGI_SET_SHA == (
        "017e9360402afa002dc0970088649e7c411c4f02333dec550f2432be3c0dd701"
    )
