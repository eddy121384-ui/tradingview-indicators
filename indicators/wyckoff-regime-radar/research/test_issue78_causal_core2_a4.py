"""Tests for the A4 causal Core-2 translation analyzer.

Proves (synthetically + on real OOS3 data): strict prior-only ranks,
append-future invariance, the 252-bar warmup boundary, exact hard/relaxed
masks, unchanged A1 axes, unchanged A3 retrospective outputs, and
deterministic rebuilds. No forward-return outcomes are asserted here.
"""
import math

import numpy as np
import pandas as pd

import analyze_issue78_causal_core2_a4 as a4
import analyze_issue78_supply_demand_a2 as a2


def _causal_frame_fixture(n=400, seed=11):
    rng = np.random.default_rng(seed)
    return pd.DataFrame(
        {
            "ready": [True] * n,
            "block": ["ALL"] * n,
            "dir_structure": rng.normal(0.0, 30.0, n),
            "extension": np.abs(rng.normal(40.0, 25.0, n)),
            "rank_dir_structure": rng.random(n),
            "rank_extension": rng.random(n),
            "fwd_1": rng.normal(0.0, 1.0, n),
            "fwd_5": rng.normal(0.0, 1.0, n),
            "fwd_10": rng.normal(0.0, 1.0, n),
            "fwd_20": rng.normal(0.0, 1.0, n),
        }
    )


def test_future_rows_cannot_alter_earlier_ranks():
    frame = _causal_frame_fixture()
    out = a4.add_causal_ranks(frame)
    for cut in (260, 300, 400):
        early = a4.add_causal_ranks(frame.iloc[:cut].copy())
        np.testing.assert_allclose(
            out["rank_c_struct"].to_numpy(float)[:cut],
            early["rank_c_struct"].to_numpy(float),
            equal_nan=True,
        )
        np.testing.assert_allclose(
            out["rank_c_ext"].to_numpy(float)[:cut],
            early["rank_c_ext"].to_numpy(float),
            equal_nan=True,
        )


def test_append_future_invariance():
    frame = _causal_frame_fixture()
    base = a4.add_causal_ranks(frame.iloc[:300].copy())
    extended = a4.add_causal_ranks(frame.copy())
    for col in ("rank_c_struct", "rank_c_ext", "causal_ready"):
        left = base[col].to_numpy()
        right = extended[col].to_numpy()[:300]
        if col == "causal_ready":
            assert (left == right).all()
        else:
            np.testing.assert_allclose(left, right, equal_nan=True)


def test_exactly_252_prior_ready_required():
    n = 260
    frame = pd.DataFrame(
        {
            "ready": [True] * n,
            "block": ["ALL"] * n,
            "dir_structure": np.arange(n, dtype=float),
            "extension": np.arange(n, dtype=float),
            "rank_dir_structure": np.linspace(0.01, 0.99, n),
            "rank_extension": np.linspace(0.01, 0.99, n),
            "fwd_1": 0.0,
            "fwd_5": 0.0,
            "fwd_10": 0.0,
            "fwd_20": 0.0,
        }
    )
    out = a4.add_causal_ranks(frame)
    # Bar t has t prior ready bars: available exactly from t >= 252.
    assert out["causal_ready"][:252].sum() == 0
    assert bool(out["causal_ready"].iloc[252])
    assert math.isnan(out["rank_c_struct"].iloc[251])
    assert np.isfinite(out["rank_c_struct"].iloc[252])
    # Non-ready bars never enter the reference set nor evaluate.
    frame2 = frame.copy()
    frame2.loc[100, "ready"] = False
    out2 = a4.add_causal_ranks(frame2)
    assert bool(out2["causal_ready"].iloc[253])
    assert math.isnan(out2["rank_c_struct"].iloc[100])


def test_hard_80_20_masks_exact():
    frame = pd.DataFrame(
        {
            "causal_ready": [True] * 6,
            "rank_c_struct": [0.85, 0.75, 0.65, 0.25, 0.15, 0.5],
            "rank_c_ext": [0.1, 0.1, 0.1, 0.9, 0.9, 0.5],
        }
    )
    hard = a4._causal_masks(frame, True)
    assert hard["bull_low"][0].tolist() == [True] + [False] * 5
    assert hard["bear_high"][0].tolist() == [False] * 4 + [True, False]
    assert hard["bull_low"][1] == 1.0
    assert hard["bear_low"][1] == -1.0


def test_relaxed_70_30_masks_exact():
    frame = pd.DataFrame(
        {
            "causal_ready": [True] * 6,
            "rank_c_struct": [0.85, 0.75, 0.65, 0.25, 0.15, 0.5],
            "rank_c_ext": [0.1, 0.1, 0.1, 0.9, 0.9, 0.5],
        }
    )
    rel = a4._causal_masks(frame, False)
    hard = a4._causal_masks(frame, True)
    assert rel["bull_low"][0].tolist() == [True, True, False] + [False] * 3
    assert rel["bear_high"][0].tolist() == [False] * 3 + [True, True, False]
    assert rel["bull_low"][0].sum() >= hard["bull_low"][0].sum()


def test_a1_raw_axes_unchanged_on_real_data():
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
    raw = pd.read_csv(raws[0])
    f2 = a2.add_within_stock_ranks(a2.build_sd_frame(raw, classifier))
    np.testing.assert_allclose(
        f2["extension"].to_numpy(float),
        np.abs(f2["dir_velocity"].to_numpy(float)),
        rtol=0,
        atol=0,
        equal_nan=True,
    )
    assert f2["ready"].sum() > 0


def test_a3_retrospective_outputs_unchanged():
    from pathlib import Path

    a3_path = (
        Path(__file__).resolve().parent / "artifacts"
        / "issue78_ablation_a3" / "core_summary.csv"
    )
    assert a3_path.exists(), "committed A3 artifact must exist"
    core = pd.read_csv(a3_path)
    row = core[
        (core["test"] == "core")
        & (core["state"] == "bull_low")
        & (core["block"] == "ALL")
        & (core["horizon"] == 10)
    ]
    assert len(row) == 1
    assert abs(float(row.iloc[0]["equal_stock_mean"]) - (-0.072470)) < 1e-6
    assert int(row.iloc[0]["stocks"]) == 258


def test_deterministic_rebuild_on_real_data():
    from pathlib import Path

    from smoke_issue119_frozen_classifier import load_classifier

    here = Path(__file__).resolve().parent
    raw_dir = (
        here / "artifacts" / "issue78_equity_proof_policy_oos3"
        / "snapshot" / "raw"
    )
    raws = sorted(raw_dir.glob("*.csv.gz"))
    classifier, _ = load_classifier(
        here / "generated" / "wyckoff-issue78-rc-python.py"
    )
    for raw_path in raws[:2]:
        raw = pd.read_csv(raw_path)
        fa = a4.add_causal_ranks(
            a2.add_within_stock_ranks(a2.build_sd_frame(raw, classifier))
        )
        fb = a4.add_causal_ranks(
            a2.add_within_stock_ranks(a2.build_sd_frame(raw, classifier))
        )
        for col in ("rank_c_struct", "rank_c_ext"):
            np.testing.assert_array_equal(
                np.nan_to_num(fa[col].to_numpy(float), nan=-999.0),
                np.nan_to_num(fb[col].to_numpy(float), nan=-999.0),
            )
        assert (fa["causal_ready"].to_numpy() == fb["causal_ready"].to_numpy()).all()
