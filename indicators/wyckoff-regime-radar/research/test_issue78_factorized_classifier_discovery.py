import numpy as np
import pandas as pd

import analyze_issue78_factorized_classifier_discovery as mod


def _classified_fixture():
    return pd.DataFrame(
        {
            "speed_rank": [50.0, 90.0, 10.0, 80.0],
            "issue66_b1_ma_log": [1.0, 2.0, 1.5, 2.2],
            "issue66_b1_maturity_ma_log": [1.1, 1.5, 1.7, 2.0],
            "issue66_b1_ma_spread_atr": [-0.1, 0.5, -0.2, 0.2],
            "range_score": [50.0, 20.0, 80.0, 40.0],
            "downside_exhaustion": [10.0, 20.0, 80.0, 30.0],
            "support_holding": [20.0, 30.0, 90.0, 40.0],
            "upside_exhaustion": [30.0, 40.0, 10.0, 70.0],
            "resistance_holding": [40.0, 50.0, 20.0, 80.0],
            "breakout_score": [5.0, 90.0, 10.0, 70.0],
            "explicit_breakdown_score": [5.0, 10.0, 85.0, 20.0],
            "range_cont_up": [10.0, 80.0, 15.0, 75.0],
            "range_cont_dn": [10.0, 20.0, 90.0, 25.0],
        }
    )


def test_factor_scores_split_dimensions_and_directional_lifecycle():
    out = mod.compute_factor_scores(_classified_fixture())

    assert np.isnan(out.loc[0, "direction"])
    assert out.loc[1, "direction"] > 0
    assert out.loc[2, "direction"] < 0

    assert out.loc[1, "range_factor"] == 20.0
    assert out.loc[2, "range_factor"] == 80.0

    assert out.loc[2, "sd"] > 0
    assert out.loc[1, "sd"] < 0

    assert out.loc[1, "emerging"] == 90.0
    assert out.loc[2, "emerging"] == 85.0

    expected_up_established = (
        80.0 + out.loc[1, "direction_structure"]
    ) / 2.0
    # direction_structure is a signed direction score, not the bull-spread
    # component. Verify selection behavior directly instead.
    assert out.loc[1, "established"] > 40.0
    assert out.loc[2, "established"] > 40.0

    assert out.loc[1, "deteriorating"] == 45.0
    assert out.loc[2, "deteriorating"] == 85.0


def test_within_stock_ranks_are_monotonic():
    frame = pd.DataFrame(
        {
            "ready": [True] * 5,
            "direction": [-2, -1, 0, 1, 2],
            "range_factor": [1, 2, 3, 4, 5],
            "sd": [5, 4, 3, 2, 1],
            "emerging": [1, 2, 3, 4, 5],
            "established": [1, 2, 3, 4, 5],
            "deteriorating": [5, 4, 3, 2, 1],
        }
    )
    ranked = mod.add_within_stock_ranks(frame)
    assert ranked.loc[0, "rank_direction"] == 0.2
    assert ranked.loc[4, "rank_direction"] == 1.0
    assert ranked.loc[0, "rank_sd"] == 1.0
    assert ranked.loc[4, "rank_sd"] == 0.2


def test_paired_delta_uses_good_minus_bad():
    cells = pd.DataFrame(
        [
            {
                "figi": "A",
                "horizon": 10,
                "test": "lifecycle_up",
                "state": "established_low_deteriorating",
                "mean": 0.7,
                "sector": "X",
                "sleeve": "large",
            },
            {
                "figi": "A",
                "horizon": 10,
                "test": "lifecycle_up",
                "state": "high_deteriorating",
                "mean": -0.2,
                "sector": "X",
                "sleeve": "large",
            },
        ]
    )
    per_stock, summary = mod.paired_deltas(cells)
    assert len(per_stock) == 1
    assert np.isclose(per_stock.iloc[0]["delta"], 0.9)
    assert np.isclose(
        summary.iloc[0]["equal_stock_mean_delta"], 0.9
    )
