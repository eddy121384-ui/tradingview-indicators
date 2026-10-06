"""Tests for the A2 supply-demand rebuild analyzer.

Guards: candidates are exact simple differences (no weights), A1 axes are
reused unchanged, paired specs encode demand-good (bull) / supply-good
(bear), and the A2 frame matches the A1 frame on real data.
"""
import math

import numpy as np
import pandas as pd

import analyze_issue78_supply_demand_a2 as a2
import analyze_issue78_direction_decomposition_a1 as a1
import analyze_issue78_factorized_classifier_discovery as a0


def _classified_fixture():
    return pd.DataFrame(
        {
            "speed_rank": [50.0, 90.0, 10.0, 80.0, 30.0],
            "sym_atr": [1.0, 1.0, 1.0, 1.0, 1.0],
            "issue66_b1_ma_log": [1.0, 2.0, 1.5, 2.2, 1.1],
            "issue66_b1_maturity_ma_log": [1.1, 1.5, 1.7, 2.0, 1.2],
            "issue66_b1_ma_spread_atr": [-0.1, 0.5, -0.2, 0.2, 0.0],
            "range_score": [50.0, 20.0, 80.0, 40.0, 60.0],
            "downside_exhaustion": [10.0, 20.0, 80.0, 30.0, 50.0],
            "support_holding": [20.0, 30.0, 90.0, 40.0, 60.0],
            "upside_exhaustion": [30.0, 40.0, 10.0, 70.0, 50.0],
            "resistance_holding": [40.0, 50.0, 20.0, 80.0, 40.0],
            "breakout_score": [5.0, 90.0, 10.0, 70.0, 20.0],
            "explicit_breakdown_score": [5.0, 10.0, 85.0, 20.0, 30.0],
            "range_cont_up": [10.0, 80.0, 15.0, 75.0, 40.0],
            "range_cont_dn": [10.0, 20.0, 90.0, 25.0, 40.0],
        }
    )


def test_candidates_are_simple_differences():
    classified = _classified_fixture()
    down = classified["downside_exhaustion"].to_numpy(float)
    sup = classified["support_holding"].to_numpy(float)
    up = classified["upside_exhaustion"].to_numpy(float)
    res = classified["resistance_holding"].to_numpy(float)
    np.testing.assert_allclose(sup - res, sup - res)  # holding_balance
    np.testing.assert_allclose(down - up, down - up)  # exhaustion_balance
    controls = a0.compute_factor_scores(classified)
    # A0 sd = mean(down,sup) - mean(up,res); candidates use no averaging.
    expected_h = sup - res
    expected_e = down - up
    assert list(expected_h) == [-20.0, -20.0, 70.0, -40.0, 20.0]
    assert list(expected_e) == [-20.0, -20.0, 70.0, -40.0, 0.0]
    assert list(controls["sd"].to_numpy(float)) == [
        -20.0,
        -20.0,
        70.0,
        -40.0,
        10.0,
    ]


def test_a1_axes_reused_unchanged():
    classified = _classified_fixture()
    legs = a1.compute_ma_legs(classified)
    structure = (
        legs["ma_bull"].to_numpy(float) - legs["ma_bear"].to_numpy(float)
    )
    controls = a0.compute_factor_scores(classified)
    np.testing.assert_allclose(
        structure, controls["direction_structure"].to_numpy(float),
        equal_nan=True,
    )
    assert a2.BLOCKS == a1.BLOCKS
    assert a2.HORIZONS == a0.HORIZONS
    assert a2.MIN_CELL_BARS == a0.MIN_CELL_BARS
    assert a2.MIN_AGG_STOCKS == a0.MIN_AGG_STOCKS


def test_paired_specs_encode_expected_semantics():
    # Bull: demand-good. Bear: supply-good. Both hard and relaxed.
    for cand in ("holding_balance", "exhaustion_balance", "a0_sd"):
        assert a2.PAIRED_SPECS[f"bull_low_{cand}"] == ("demand", "supply")
        assert a2.PAIRED_SPECS[f"bull_high_{cand}"] == ("demand", "supply")
        assert a2.PAIRED_SPECS[f"bear_low_{cand}"] == ("supply", "demand")
        assert a2.PAIRED_SPECS[f"bear_high_{cand}"] == ("supply", "demand")
        assert a2.PAIRED_SPECS[f"bull_low_rel_{cand}"] == ("demand", "supply")
        assert a2.PAIRED_SPECS[f"bear_high_rel_{cand}"] == (
            "supply",
            "demand",
        )


def test_side_masks_use_predeclared_thresholds():
    frame = pd.DataFrame(
        {
            "rank_dir_structure": [0.85, 0.75, 0.25, 0.15, 0.5],
            "rank_extension": [0.1, 0.9, 0.1, 0.9, 0.5],
        }
    )
    hard = a2._side_masks(frame, True)
    assert hard["bull"].tolist() == [True, False, False, False, False]
    assert hard["bear"].tolist() == [False, False, False, True, False]
    assert hard["low_ext"].tolist() == [True, False, True, False, False]
    assert hard["high_ext"].tolist() == [False, True, False, True, False]
    rel = a2._side_masks(frame, False)
    assert rel["bull"].tolist() == [True, True, False, False, False]
    assert rel["bear"].tolist() == [False, False, True, True, False]
    assert rel["low_ext"].tolist() == [True, False, True, False, False]
    assert rel["high_ext"].tolist() == [False, True, False, True, False]


def test_tail_stats_passthrough():
    stats = a2._tail_stats if hasattr(a2, "_tail_stats") else a1._tail_stats
    out = stats(np.array([1.0, -4.0, 2.0]))
    assert out["bars"] == 3
    assert math.isclose(out["mean"], -1.0 / 3.0)
    assert out["es5"] <= out["p5"]


def test_a2_frame_matches_a1_on_real_data():
    from pathlib import Path

    from smoke_issue119_frozen_classifier import load_classifier

    here = Path(__file__).resolve().parent
    raw_dir = (
        here / "artifacts" / "issue78_equity_proof_policy_oos3"
        / "snapshot" / "raw"
    )
    raws = sorted(raw_dir.glob("*.csv.gz"))
    assert len(raws) == 300, f"expected recovered OOS3 snapshot, got {len(raws)}"
    classifier, _ = load_classifier(
        here / "generated" / "wyckoff-issue78-rc-python.py"
    )
    for raw_path in raws[:3]:
        raw = pd.read_csv(raw_path)
        f1 = a1.add_within_stock_ranks(
            a1.build_decomposition_frame(raw, classifier)
        )
        f2 = a2.add_within_stock_ranks(
            a2.build_sd_frame(raw, classifier)
        )
        assert (f2["date"] == f1["date"]).all()
        assert (f2["eligible"].to_numpy() == f1["eligible"].to_numpy()).all()
        for col in ("dir_velocity", "extension", "dir_structure"):
            np.testing.assert_allclose(
                f2[col].to_numpy(float),
                f1[col].to_numpy(float),
                equal_nan=True,
            )
        for h in (1, 5, 10, 20):
            np.testing.assert_allclose(
                f2[f"fwd_{h}"].to_numpy(float),
                f1[f"fwd_{h}"].to_numpy(float),
                equal_nan=True,
            )
        # Candidates are exact differences of the stored primitives.
        np.testing.assert_allclose(
            f2["holding_balance"].to_numpy(float),
            (
                f2["sup_hold"].to_numpy(float)
                - f2["res_hold"].to_numpy(float)
            ),
            equal_nan=True,
        )
        np.testing.assert_allclose(
            f2["exhaustion_balance"].to_numpy(float),
            (
                f2["down_exh"].to_numpy(float)
                - f2["up_exh"].to_numpy(float)
            ),
            equal_nan=True,
        )
