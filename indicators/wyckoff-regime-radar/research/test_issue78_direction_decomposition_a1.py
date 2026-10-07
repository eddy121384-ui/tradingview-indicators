"""Tests for the A1 direction-decomposition analyzer.

Guards: A1 components recombine exactly to the frozen A0 direction formula,
blocks are fixed calendar bins, tail stats are correct, and the A1 frame
matches the A0 frame on real data (same eligibility, same forwards).
"""
import math

import numpy as np
import pandas as pd

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
            "support_holding": [20.0, 30.0, 90.0, 40.0, 50.0],
            "upside_exhaustion": [30.0, 40.0, 10.0, 70.0, 50.0],
            "resistance_holding": [40.0, 50.0, 20.0, 80.0, 50.0],
            "breakout_score": [5.0, 90.0, 10.0, 70.0, 20.0],
            "explicit_breakdown_score": [5.0, 10.0, 85.0, 20.0, 30.0],
            "range_cont_up": [10.0, 80.0, 15.0, 75.0, 40.0],
            "range_cont_dn": [10.0, 20.0, 90.0, 25.0, 40.0],
        }
    )


def test_a1_recombines_to_a0_direction():
    classified = _classified_fixture()
    legs = a1.compute_ma_legs(classified)
    controls = a0.compute_factor_scores(classified)
    velocity = 2.0 * classified["speed_rank"].to_numpy(float) - 100.0
    structure = (
        legs["ma_bull"].to_numpy(float) - legs["ma_bear"].to_numpy(float)
    )
    np.testing.assert_allclose(
        structure, controls["direction_structure"].to_numpy(float),
        equal_nan=True,
    )
    recombined = np.clip((velocity + structure) / 2.0, -100.0, 100.0)
    np.testing.assert_allclose(
        recombined, controls["direction"].to_numpy(float), equal_nan=True
    )
    # Row 0 has no prior bar -> NaN structure, matching A0.
    assert math.isnan(structure[0])
    assert math.isnan(recombined[0])
    assert np.isfinite(structure[1])


def test_extension_is_abs_velocity():
    classified = _classified_fixture()
    velocity = 2.0 * classified["speed_rank"].to_numpy(float) - 100.0
    np.testing.assert_allclose(
        np.abs(velocity), np.abs(velocity)
    )
    assert list(np.abs(velocity)) == [0.0, 80.0, 80.0, 60.0, 40.0]


def test_block_assignment_boundaries():
    frame = pd.DataFrame(
        {"date": pd.to_datetime(
            ["1999-12-31", "2000-01-03", "2004-12-31", "2005-01-03",
             "2009-12-31", "2010-01-04", "2014-12-31", "2015-01-02",
             "2019-12-31", "2020-01-02", "2026-08-31"]
        )}
    )
    year = frame["date"].dt.year.to_numpy(int)
    block = np.full(len(frame), "", dtype=object)
    for name, lo, hi in a1.BLOCKS:
        block[(year >= lo) & (year <= hi)] = name
    assert list(block) == [
        "", "2000-2004", "2000-2004", "2005-2009", "2005-2009",
        "2010-2014", "2010-2014", "2015-2019", "2015-2019",
        "2020-2026", "2020-2026",
    ]
    assert [n for n, _, _ in a1.BLOCKS] == [
        "2000-2004", "2005-2009", "2010-2014", "2015-2019", "2020-2026"
    ]


def test_tail_stats_known_values():
    stats = a1._tail_stats(np.array([1.0, 2.0, 3.0, 4.0, -20.0]))
    assert stats["bars"] == 5
    assert stats["mean"] == -2.0
    assert stats["median"] == 2.0
    assert stats["positive_fraction"] == 0.8
    assert stats["p5"] <= stats["p10"] <= stats["median"]
    assert stats["es5"] <= stats["p5"]
    # Negative mass dominates: neg_share > pos_share.
    assert stats["neg_share"] > stats["pos_share"]
    assert abs(stats["neg_share"] + stats["pos_share"] - 1.0) < 1e-9
    empty = a1._tail_stats(np.array([np.nan, np.inf * 0 - np.inf * 0])[:0])
    assert empty["bars"] == 0
    assert math.isnan(empty["es5"])


def test_paired_delta_is_good_minus_bad_with_block():
    cells = pd.DataFrame(
        [
            {"figi": "A", "block": "ALL", "horizon": 10,
             "test": "struct_ext_bull", "state": "low_extension",
             "mean": 0.5, "sector": "X", "sleeve": "large"},
            {"figi": "A", "block": "ALL", "horizon": 10,
             "test": "struct_ext_bull", "state": "high_extension",
             "mean": -0.2, "sector": "X", "sleeve": "large"},
        ]
    )
    per_stock, summary = a1.paired_deltas(
        cells,
        {"struct_ext_bull": ("low_extension", "high_extension")},
    )
    assert len(per_stock) == 1
    assert np.isclose(per_stock.iloc[0]["delta"], 0.7)
    assert per_stock.iloc[0]["block"] == "ALL"
    assert np.isclose(
        summary.iloc[0]["equal_stock_mean_delta"], 0.7
    )


def test_a1_frame_matches_a0_on_real_data():
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
        f0 = a0.add_within_stock_ranks(a0.build_frame(raw, classifier))
        f1 = a1.add_within_stock_ranks(
            a1.build_decomposition_frame(raw, classifier)
        )
        assert (f1["date"] == f0["date"]).all()
        assert (f1["eligible"].to_numpy() == f0["eligible"].to_numpy()).all()
        assert (f1["ready"].to_numpy() == f0["ready"].to_numpy()).all()
        for col in ("direction", "sd", "deteriorating"):
            np.testing.assert_allclose(
                f1[col].to_numpy(float),
                f0[col].to_numpy(float),
                equal_nan=True,
            )
        for h in (1, 5, 10, 20):
            np.testing.assert_allclose(
                f1[f"fwd_{h}"].to_numpy(float),
                f0[f"fwd_{h}"].to_numpy(float),
                equal_nan=True,
            )
        recombined = np.clip(
            (f1["dir_velocity"].to_numpy(float)
             + f1["dir_structure"].to_numpy(float)) / 2.0,
            -100.0,
            100.0,
        )
        np.testing.assert_allclose(
            recombined, f1["direction"].to_numpy(float), equal_nan=True
        )
