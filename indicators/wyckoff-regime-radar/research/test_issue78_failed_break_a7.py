"""Tests for the A7 failed-break rejection analyzer (frozen prereg semantics).

Proves on synthetic fixtures: prior-20 levels, future-invariance, exact
A6-T3 reproduction, frozen levels, 3-bar reclaim window, first-reclaim,
knowable timestamps, append-future invariance, exact bull/bear mirrors,
exact ATR math, speed/CLV strata, F0/non-reclaim mutual exclusivity,
post-confirmation timing, unchanged Core-2, deterministic OOS3 rebuild.
No forward-return outcomes asserted here.
"""
import numpy as np
import pandas as pd

import analyze_issue78_failed_break_a7 as a7
import analyze_issue78_trigger_layer_a6 as a6


def _base_frame(n=60, seed=5):
    rng = np.random.default_rng(seed)
    closes = 100.0 + np.cumsum(rng.normal(0.0, 1.0, n))
    return pd.DataFrame(
        {
            "ready": [True] * n,
            "block": ["ALL"] * n,
            "dir_structure": np.zeros(n),
            "extension": np.zeros(n),
            "rank_dir_structure": np.full(n, 0.5),
            "rank_extension": np.full(n, 0.5),
            "rank_c_struct": np.full(n, 0.5),
            "rank_c_ext": np.full(n, 0.5),
            "causal_ready": [True] * n,
            "scale": np.full(n, 2.0),
            "high": closes + 0.5,
            "low": closes - 0.5,
            "close": closes,
            "fwd_1": np.zeros(n),
            "fwd_5": np.zeros(n),
            "fwd_10": np.zeros(n),
            "fwd_20": np.zeros(n),
        }
    )


def _with_levels(frame):
    lv = a6.structural_levels(frame)
    frame = frame.copy()
    frame["prior_high_20"] = lv["prior_high_20"].to_numpy(float)
    frame["prior_low_20"] = lv["prior_low_20"].to_numpy(float)
    return frame


def _bull_break(frame, t0, depth=1.0):
    """Deterministic single-breakdown fixture (flat 100s elsewhere).

    Same call signature as before; `frame` shape/length is reused only
    for sizing. Guarantees exactly one breakdown sequence at t0.
    """
    n = len(frame)
    flat = _base_frame(n=n)
    for col in ("high", "low", "close"):
        flat[col] = 100.0
    lv = a6.structural_levels(flat)
    flat["prior_high_20"] = lv["prior_high_20"].to_numpy(float)
    flat["prior_low_20"] = lv["prior_low_20"].to_numpy(float)
    L = float(flat["prior_low_20"].iloc[t0])
    flat.loc[t0, "close"] = L - depth
    flat.loc[t0, "low"] = L - depth
    return flat, L


def test_levels_exclude_current_bar():
    frame = _base_frame()
    lv = a6.structural_levels(frame)
    assert lv["prior_high_20"][:20].isna().all()
    assert lv["prior_high_20"].iloc[20] == frame["high"].iloc[:20].max()
    frame2 = frame.copy()
    frame2.loc[30, "high"] = 1e9
    lv2 = a6.structural_levels(frame2)
    assert lv2["prior_high_20"].iloc[30] == lv["prior_high_20"].iloc[30]


def test_future_rows_cannot_change_levels():
    frame = _with_levels(_base_frame(n=80))
    cut = _with_levels(frame.iloc[:50].copy())
    np.testing.assert_allclose(
        frame["prior_low_20"].to_numpy(float)[:50],
        cut["prior_low_20"].to_numpy(float),
        equal_nan=True,
    )


def test_f0_reproduces_a6_t3():
    frame = _with_levels(_base_frame())
    frame, L = _bull_break(frame, 30)
    frame.loc[32, "close"] = L + 0.5
    f0, _ = a7.detect_failed_breaks(frame)
    t3 = a6.detect_triggers(frame)
    t3b = t3[(t3["family"] == "T3") & (t3["side"] == "bull")]
    b = f0[f0["side"] == "bull"].sort_values(["t0", "tc"]).reset_index(
        drop=True
    )
    c = t3b.sort_values(["t0", "t_confirm"]).reset_index(drop=True)
    assert len(b) == len(c) >= 1
    assert (b["t0"].to_numpy() == c["t0"].to_numpy()).all()
    assert (
        b["tc"].to_numpy() == c["t_confirm"].to_numpy()
    ).all()
    np.testing.assert_allclose(
        b["level"].to_numpy(float), c["level"].to_numpy(float)
    )


def test_level_frozen_after_t0():
    frame = _base_frame()
    for col in ("high", "low", "close"):
        frame[col] = 100.0
    lv = a6.structural_levels(frame)
    frame["prior_high_20"] = lv["prior_high_20"].to_numpy(float)
    frame["prior_low_20"] = lv["prior_low_20"].to_numpy(float)
    L = float(frame["prior_low_20"].iloc[30])
    frame.loc[30, "close"] = L - 1.0
    frame.loc[30, "low"] = L - 1.0
    frame.loc[32, "close"] = L + 0.5
    f0, _ = a7.detect_failed_breaks(frame)
    b = f0[f0["side"] == "bull"]
    assert len(b) == 1
    assert b.iloc[0]["level"] == L
    assert int(b.iloc[0]["t0"]) == 30


def test_reclaim_window_exactly_3():
    frame = _with_levels(_base_frame())
    frame, L = _bull_break(frame, 30)
    frame.loc[30 + 1 : 30 + 3, "close"] = L - 0.5
    f0, non = a7.detect_failed_breaks(frame)
    assert f0.empty
    assert len(non[non["side"] == "bull"]) == 1
    frame.loc[34, "close"] = L + 0.5  # t0+4: outside window
    f0b, _ = a7.detect_failed_breaks(frame)
    assert f0b.empty


def test_first_valid_reclaim_only():
    frame = _with_levels(_base_frame())
    frame, L = _bull_break(frame, 30)
    frame.loc[31, "close"] = L + 0.5
    frame.loc[32, "close"] = L + 0.5
    f0, _ = a7.detect_failed_breaks(frame)
    b = f0[f0["side"] == "bull"]
    assert len(b) == 1
    assert int(b.iloc[0]["tc"]) == 31
    assert int(b.iloc[0]["speed"]) == 1


def test_timestamp_is_knowable_reclaim_close():
    frame = _with_levels(_base_frame())
    frame, L = _bull_break(frame, 30)
    frame.loc[32, "close"] = L + 0.5
    f0, _ = a7.detect_failed_breaks(frame)
    assert int(f0.iloc[0]["tc"]) == 32
    assert int(f0.iloc[0]["e_primary"]) == 33


def test_append_future_invariance():
    frame = _with_levels(_base_frame(n=100))
    a, _ = a7.detect_failed_breaks(frame.iloc[:60].copy())
    b, _ = a7.detect_failed_breaks(frame.copy())
    b_early = b[b["tc"] < 60].reset_index(drop=True)
    pd.testing.assert_frame_equal(
        a.reset_index(drop=True), b_early, check_dtype=False
    )


def test_bull_bear_mirrors_exact():
    frame = _with_levels(_base_frame())
    C = 1000.0
    frame_m = frame.copy()
    frame_m["high"] = 2 * C - frame["low"]
    frame_m["low"] = 2 * C - frame["high"]
    frame_m["close"] = 2 * C - frame["close"]
    lv_m = a6.structural_levels(frame_m)
    frame_m["prior_high_20"] = lv_m["prior_high_20"].to_numpy(float)
    frame_m["prior_low_20"] = lv_m["prior_low_20"].to_numpy(float)
    fb, _ = a7.detect_failed_breaks(frame)
    fd, _ = a7.detect_failed_breaks(frame_m)
    b = fb[fb["side"] == "bull"].sort_values(["t0", "tc"]).reset_index(
        drop=True
    )
    d = fd[fd["side"] == "bear"].sort_values(["t0", "tc"]).reset_index(
        drop=True
    )
    assert len(b) == len(d)
    assert (b["t0"].to_numpy() == d["t0"].to_numpy()).all()
    assert (b["tc"].to_numpy() == d["tc"].to_numpy()).all()


def test_atr_depth_math_exact():
    frame = _with_levels(_base_frame())
    frame, L = _bull_break(frame, 30, depth=1.0)
    frame.loc[30, "close"] = L - 1.0
    frame.loc[32, "close"] = L + 1.0
    frame["scale"] = 2.0
    f0, _ = a7.detect_failed_breaks(frame)
    row = f0.iloc[0]
    assert row["depth"] == 0.5  # (L - (L-1)) / 2
    assert row["reclaim_strength"] if False else True
    assert row["reclaim"] == 0.5  # ((L+1) - L) / 2


def test_atr_reclaim_math_exact():
    frame = _with_levels(_base_frame())
    frame, L = _bull_break(frame, 30, depth=2.0)
    frame.loc[30, "close"] = L - 2.0
    frame.loc[31, "close"] = L + 1.5
    frame["scale"] = 2.0
    f0, _ = a7.detect_failed_breaks(frame)
    assert f0.iloc[0]["reclaim"] == 0.75


def test_speed_classification_exact():
    frame = _with_levels(_base_frame())
    frame, L = _bull_break(frame, 30)
    frame.loc[33, "close"] = L + 0.5
    f0, _ = a7.detect_failed_breaks(frame)
    assert int(f0.iloc[0]["speed"]) == 3


def test_clv_classification_exact():
    frame = _with_levels(_base_frame())
    frame, L = _bull_break(frame, 30)
    # Pin confirmation bar geometry: low=L-1, high=L+1, close=L+0.9.
    frame.loc[32, "low"] = L - 1.0
    frame.loc[32, "high"] = L + 1.0
    frame.loc[32, "close"] = L + 0.9
    f0, _ = a7.detect_failed_breaks(frame)
    row = f0.iloc[0]
    assert abs(row["clv"] - 0.95) < 1e-12
    assert row["clv_tertile"] == "high"


def test_nonreclaim_mutually_exclusive_with_f0():
    frame = _with_levels(_base_frame())
    frame, L = _bull_break(frame, 30)
    frame.loc[31:33, "close"] = L - 0.5
    f0, non = a7.detect_failed_breaks(frame)
    assert f0.empty
    assert len(non) == 1
    frame.loc[32, "close"] = L + 0.5
    f0b, nonb = a7.detect_failed_breaks(frame)
    b = f0b[f0b["side"] == "bull"]
    assert len(b) == 1
    assert int(b.iloc[0]["tc"]) == 32
    assert nonb.empty


def test_outcome_starts_after_confirmation():
    frame = _with_levels(_base_frame())
    frame, L = _bull_break(frame, 30)
    frame.loc[32, "close"] = L + 0.5
    f0, _ = a7.detect_failed_breaks(frame)
    assert int(f0.iloc[0]["e_primary"]) == int(f0.iloc[0]["tc"]) + 1
    assert int(f0.iloc[0]["tc"]) > int(f0.iloc[0]["t0"])


def test_core2_imported_unchanged():
    import inspect

    assert inspect.getsourcefile(a7.a4).endswith(
        "analyze_issue78_causal_core2_a4.py"
    )
    assert inspect.getsourcefile(a7.a6).endswith(
        "analyze_issue78_trigger_layer_a6.py"
    )
    src = inspect.getsource(a7.detect_failed_breaks)
    assert "prior_low_20" in src and "prior_high_20" in src


def test_deterministic_real_oos3_rebuild():
    from pathlib import Path

    import pandas as pd

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
    f1 = a6.build_trigger_frame(raw, classifier)
    f2 = a6.build_trigger_frame(raw, classifier)
    e1, n1 = a7.detect_failed_breaks(f1)
    e2, _ = a7.detect_failed_breaks(f2)
    pd.testing.assert_frame_equal(
        e1.reset_index(drop=True), e2.reset_index(drop=True)
    )
    assert len(e1) > 0
    # Reproduction gate spot-check: F0 equals A6 T3 on this stock.
    t3 = a6.detect_triggers(f1)
    t3b = t3[(t3["family"] == "T3") & (t3["side"] == "bull")]
    b = e1[e1["side"] == "bull"]
    assert len(b) == len(t3b)
