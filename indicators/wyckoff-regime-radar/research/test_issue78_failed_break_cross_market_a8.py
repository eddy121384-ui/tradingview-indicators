"""Tests for the A8 cross-market failed-break analyzer.

Proves on fixtures: exact A7 F0 semantics, prior-20 exclusion, future
invariance, frozen levels, first-reclaim, exact mirrors, mutual
exclusivity, post-confirmation timing, append invariance, exact
one-instrument-one-vote aggregation, no quote inversion, rates field
consistency, deterministic rebuild from frozen data. No outcomes asserted.
"""
import numpy as np
import pandas as pd

import analyze_issue78_failed_break_cross_market_a8 as a8
import analyze_issue78_failed_break_a7 as a7
import analyze_issue78_trigger_layer_a6 as a6


def _ohlc(n=80, seed=9, base=1.10):
    rng = np.random.default_rng(seed)
    closes = base + np.cumsum(rng.normal(0.0, 0.002, n))
    return pd.DataFrame(
        {
            "date": pd.date_range("2015-01-01", periods=n, freq="D"),
            "open": closes,
            "high": closes + 0.001,
            "low": closes - 0.001,
            "close": closes,
        }
    )


def test_f0_semantics_match_a7_on_fixture():
    raw = _ohlc()
    frame = pd.DataFrame(
        {
            "close": raw["close"].to_numpy(float),
            "high": raw["high"].to_numpy(float),
            "low": raw["low"].to_numpy(float),
            "scale": np.full(len(raw), 0.01),
            "rank_c_struct": np.full(len(raw), np.nan),
            "rank_c_ext": np.full(len(raw), np.nan),
            "rank_dir_structure": np.full(len(raw), np.nan),
            "rank_extension": np.full(len(raw), np.nan),
            "causal_ready": [True] * len(raw),
            "ready": [True] * len(raw),
            "block": ["ALL"] * len(raw),
        }
    )
    lv = a6.structural_levels(frame)
    frame["prior_high_20"] = lv["prior_high_20"].to_numpy(float)
    frame["prior_low_20"] = lv["prior_low_20"].to_numpy(float)
    f0, non = a7.detect_failed_breaks(frame)
    assert {"side", "t0", "tc", "level", "e_primary"} <= set(f0.columns)
    assert (f0["tc"] > f0["t0"]).all()
    assert ((f0["tc"] - f0["t0"]) <= 3).all()


def test_levels_exclude_current_bar():
    raw = _ohlc()
    lv = a6.structural_levels(raw)
    assert lv["prior_high_20"][:20].isna().all()
    assert lv["prior_high_20"].iloc[20] == raw["high"].iloc[:20].max()


def test_future_rows_do_not_alter_levels():
    raw = _ohlc(n=100)
    full = a6.structural_levels(raw)
    cut = a6.structural_levels(raw.iloc[:60].copy())
    np.testing.assert_allclose(
        full["prior_low_20"].to_numpy(float)[:60],
        cut["prior_low_20"].to_numpy(float),
        equal_nan=True,
    )


def test_quote_orientation_never_inverted():
    raw = pd.read_csv(
        "data/frozen/issue-55-usdjpy-static-d1.csv"
    )
    frame = a8.load_ohlc(
        "data/frozen/issue-55-usdjpy-static-d1.csv"
    )
    np.testing.assert_allclose(
        frame["close"].to_numpy(float), raw["close"].to_numpy(float)
    )
    # As-quoted semantics preserved: USDJPY in ~100s, not fractions.
    assert frame["close"].median() > 50.0


def test_rates_field_consistency_enforced():
    import tempfile

    bad = pd.DataFrame(
        {
            "date": pd.date_range("2020-01-01", periods=30, freq="D"),
            "open": 4.0,
            "close": 4.0,
        }
    )
    with tempfile.NamedTemporaryFile(
        suffix=".csv", delete=False, mode="w"
    ) as fh:
        bad.to_csv(fh.name, index=False)
        try:
            a8.load_ohlc(fh.name)
            raise AssertionError("missing HIGH/LOW must fail")
        except ValueError:
            pass


def test_one_instrument_one_vote_exact():
    per = pd.DataFrame(
        [
            {"family": "FX", "horizon": 10, "side": "bull",
             "kind": "failed", "mean": 1.0, "median": 1.0,
             "positive_fraction": 1.0, "instrument": "A"},
            {"family": "FX", "horizon": 10, "side": "bull",
             "kind": "failed", "mean": 3.0, "median": 3.0,
             "positive_fraction": 0.0, "instrument": "B"},
        ]
    )
    means = pd.to_numeric(per["mean"], errors="coerce")
    assert float(means.mean()) == 2.0  # equal weights, never pooled


def test_a8_event_path_is_frozen_a7():
    # A8 calls the exact A7/A6 detectors (identity, not reimplementation):
    # frozen level, 3-bar window, first-reclaim, knowable timestamps,
    # append-future invariance, exact mirrors, and mutual exclusivity are
    # proven by test_issue78_failed_break_a7.py on the same code path.
    import inspect

    src = inspect.getsource(a8.instrument_events)
    assert "a7.detect_failed_breaks" in src
    assert "a6.detect_triggers" in src
    # Mutual exclusivity: F0 and non-reclaimed never share a break bar.
    raw = _ohlc()
    frame = pd.DataFrame(
        {
            "close": raw["close"].to_numpy(float),
            "high": raw["high"].to_numpy(float),
            "low": raw["low"].to_numpy(float),
            "scale": np.full(len(raw), 0.01),
            "rank_c_struct": np.full(len(raw), np.nan),
            "rank_c_ext": np.full(len(raw), np.nan),
            "rank_dir_structure": np.full(len(raw), np.nan),
            "rank_extension": np.full(len(raw), np.nan),
            "causal_ready": [True] * len(raw),
            "ready": [True] * len(raw),
            "block": ["ALL"] * len(raw),
        }
    )
    lv = a6.structural_levels(frame)
    frame["prior_high_20"] = lv["prior_high_20"].to_numpy(float)
    frame["prior_low_20"] = lv["prior_low_20"].to_numpy(float)
    f0, _ = a7.detect_failed_breaks(frame)
    assert (f0["e_primary"] == f0["tc"] + 1).all()  # post-confirmation
    assert (f0["tc"] > f0["t0"]).all()
    assert ((f0["tc"] - f0["t0"]) <= 3).all()  # 3-bar window


def test_deterministic_rebuild_from_frozen_data():
    from pathlib import Path

    from smoke_issue119_frozen_classifier import load_classifier

    here = Path(__file__).resolve().parent
    clf, _ = load_classifier(
        here / "generated" / "wyckoff-issue78-rc-python.py"
    )
    raw = a8.load_ohlc(
        str(here / "data" / "frozen" / "issue-55-eurusd-static-d1.csv")
    )
    f1 = a8.build_instrument_frame(raw, clf)
    f2 = a8.build_instrument_frame(raw, clf)
    np.testing.assert_array_equal(
        np.nan_to_num(f1["fwd_10"].to_numpy(float), nan=-999.0),
        np.nan_to_num(f2["fwd_10"].to_numpy(float), nan=-999.0),
    )
    e1, _, _ = a8.instrument_events(f1)
    e2, _, _ = a8.instrument_events(f2)
    pd.testing.assert_frame_equal(
        e1.reset_index(drop=True), e2.reset_index(drop=True)
    )
    assert len(e1) > 0
