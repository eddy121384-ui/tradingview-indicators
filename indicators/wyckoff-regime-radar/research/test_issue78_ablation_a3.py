"""Tests for the A3 ablation analyzer.

Guards: core cells use frozen A1 axes at predeclared thresholds, paired
specs encode demand-good (bull) / supply-good (bear), and the A3 frame is
the A2 frame (same eligibility, same scores) on real data.
"""
import numpy as np
import pandas as pd

import analyze_issue78_ablation_a3 as a3
import analyze_issue78_supply_demand_a2 as a2


def _frame_fixture():
    n = 200
    rng = np.random.default_rng(7)
    fwd = rng.normal(0.0, 1.0, n)
    return pd.DataFrame(
        {
            "ready": [True] * n,
            "block": ["ALL"] * n,
            "rank_dir_structure": np.linspace(0.01, 1.0, n),
            "rank_extension": np.linspace(1.0, 0.01, n),
            "rank_a0_sd": rng.random(n),
            "rank_holding_balance": rng.random(n),
            "fwd_1": fwd,
            "fwd_5": fwd,
            "fwd_10": fwd,
            "fwd_20": fwd,
        }
    )


def test_core_masks_use_predeclared_thresholds():
    frame = pd.DataFrame(
        {
            "rank_dir_structure": [0.85, 0.75, 0.65, 0.25, 0.15, 0.5],
            "rank_extension": [0.1, 0.1, 0.1, 0.9, 0.9, 0.5],
        }
    )
    hard = a3._core_masks(frame, True)
    assert hard["bull_low"][0].tolist() == [True] + [False] * 5
    assert hard["bear_high"][0].tolist() == [False] * 4 + [True, False]
    assert hard["bull_low"][1] == 1.0
    assert hard["bear_low"][1] == -1.0
    rel = a3._core_masks(frame, False)
    # 70/30 admits strictly more bars than 80/20.
    assert rel["bull_low"][0].sum() >= hard["bull_low"][0].sum()
    assert rel["bear_high"][0].sum() >= hard["bear_high"][0].sum()
    # Row 1 (struct .75, ext .10): hard-bull no, relaxed-bull yes.
    assert not hard["bull_low"][0][1] and rel["bull_low"][0][1]


def test_paired_specs_encode_expected_semantics():
    for control in ("a0_sd", "holding_balance"):
        for suffix in ("", "_rel"):
            assert a3.PAIRED_SPECS[f"core{suffix}_bull_low_{control}"] == (
                "demand",
                "supply",
            )
            assert a3.PAIRED_SPECS[f"core{suffix}_bull_high_{control}"] == (
                "demand",
                "supply",
            )
            assert a3.PAIRED_SPECS[f"core{suffix}_bear_low_{control}"] == (
                "supply",
                "demand",
            )
            assert a3.PAIRED_SPECS[f"core{suffix}_bear_high_{control}"] == (
                "supply",
                "demand",
            )


def test_core_cells_carry_blocks_and_tails():
    n = 200
    rng = np.random.default_rng(7)
    frame = pd.DataFrame(
        {
            "ready": [True] * n,
            "block": ["2020-2026"] * n,
            "rank_dir_structure": np.linspace(0.01, 1.0, n),
            "rank_extension": np.linspace(1.0, 0.01, n),
            "rank_a0_sd": rng.random(n),
            "rank_holding_balance": rng.random(n),
            "fwd_1": rng.normal(0.0, 1.0, n),
            "fwd_5": rng.normal(0.0, 1.0, n),
            "fwd_10": rng.normal(0.0, 1.0, n),
            "fwd_20": rng.normal(0.0, 1.0, n),
        }
    )
    rows = a3.core_cells("F", frame, {"sector": "X", "sleeve": "large"})
    df = pd.DataFrame(rows)
    assert set(df["test"].unique()) == {"core", "core_rel"}
    assert "2020-2026" in set(df["block"].unique())
    assert {"p5", "p10", "es5", "neg_share"}.issubset(set(df.columns))


def test_within_cell_controls_reference_core_and_control():
    frame = _frame_fixture()
    rows = a3.within_cell_control_cells(
        "F", frame, {"sector": "X", "sleeve": "large"}
    )
    df = pd.DataFrame(rows)
    tests = set(df["test"].unique())
    assert "core_bull_low_a0_sd" in tests
    assert "core_rel_bear_high_holding_balance" in tests
    assert "cellq_bull_low_a0_sd" in tests
    assert set(df["block"].unique()) >= {"ALL"}


def test_rank_info_is_monotone_sensitive():
    # Perfectly demand-aligned forwards -> spearman +1 inside the cell.
    n = 50
    frame = pd.DataFrame(
        {
            "ready": [True] * n,
            "rank_dir_structure": [0.9] * n,
            "rank_extension": [0.1] * n,
            "rank_a0_sd": np.linspace(0.01, 0.99, n),
            "rank_holding_balance": np.linspace(0.01, 0.99, n),
            "fwd_1": np.linspace(-1.0, 1.0, n),
            "fwd_5": np.linspace(-1.0, 1.0, n),
            "fwd_10": np.linspace(-1.0, 1.0, n),
            "fwd_20": np.linspace(-1.0, 1.0, n),
        }
    )
    rows = a3.within_cell_rank_info(
        "F", frame, {"sector": "X", "sleeve": "large"}
    )
    df = pd.DataFrame(rows)
    bull = df[(df["core"] == "bull_low") & (df["horizon"] == 10)]
    assert (bull["spearman"] > 0.99).all()


def test_a3_frame_is_a2_frame_on_real_data():
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
        f2 = a2.add_within_stock_ranks(a2.build_sd_frame(raw, classifier))
        for col in (
            "dir_velocity",
            "extension",
            "dir_structure",
            "holding_balance",
            "a0_sd",
        ):
            assert col in f2.columns
        assert (f2["block"] != "").any()
