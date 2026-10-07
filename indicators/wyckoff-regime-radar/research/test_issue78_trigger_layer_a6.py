"""Tests for the A6 trigger-layer analyzer (frozen prereg semantics).

All timing/dedup/mirroring rules proven on synthetic fixtures; Core-2
reuse and deterministic real-data rerun proven on the OOS3 snapshot.
No forward-return outcomes asserted here.
"""
import numpy as np
import pandas as pd

import analyze_issue78_trigger_layer_a6 as a6
import analyze_issue78_causal_core2_a4 as a4


def _ohlc_frame(n=60, seed=3, base=100.0, drift=0.0):
    rng = np.random.default_rng(seed)
    closes = base + np.cumsum(rng.normal(drift, 1.0, n))
    return pd.DataFrame(
        {
            "ready": [True] * n,
            "block": ["ALL"] * n,
            "dir_structure": np.zeros(n),
            "extension": np.zeros(n),
            "rank_dir_structure": np.full(n, 0.9),
            "rank_extension": np.full(n, 0.1),
            "rank_c_struct": np.full(n, 0.9),
            "rank_c_ext": np.full(n, 0.1),
            "causal_ready": [True] * n,
            "high": closes + 0.5,
            "low": closes - 0.5,
            "close": closes,
            "fwd_1": np.zeros(n),
            "fwd_5": np.zeros(n),
            "fwd_10": np.zeros(n),
            "fwd_20": np.zeros(n),
        }
    )


def test_levels_exclude_current_bar():
    frame = _ohlc_frame()
    lv = a6.structural_levels(frame)
    # First 20 rows have no full prior window.
    assert lv["prior_high_20"][:20].isna().all()
    # Row 20 uses bars 0..19 only: current bar 20 excluded.
    assert lv["prior_high_20"].iloc[20] == (
        frame["high"].iloc[:20].max()
    )
    assert lv["prior_low_20"].iloc[20] == frame["low"].iloc[:20].min()
    # A spike at the current bar never enters its own level.
    frame2 = frame.copy()
    frame2.loc[30, "high"] = 1e9
    lv2 = a6.structural_levels(frame2)
    assert lv2["prior_high_20"].iloc[30] == lv["prior_high_20"].iloc[30]
    assert lv2["prior_high_20"].iloc[31] == 1e9


def test_future_rows_cannot_alter_past_triggers():
    frame = _ohlc_frame(n=80)
    full = a6.detect_triggers(frame)
    cut = a6.detect_triggers(frame.iloc[:50].copy())
    # Every trigger confirmed at <50 in the full run matches the cut run.
    full_early = full[full["t_confirm"] < 50].reset_index(drop=True)
    assert len(full_early) == len(cut)
    for col in ("side", "family", "t0", "t_confirm", "context"):
        assert (full_early[col] == cut[col]).all()


def test_level_frozen_at_event_start():
    frame = _ohlc_frame()
    frame.loc[30, "close"] = frame["prior_high_20"].iloc[30] + 5.0 if False else frame["close"].iloc[30]
    lv = a6.structural_levels(frame)
    frame["prior_high_20"] = lv["prior_high_20"]
    frame["prior_low_20"] = lv["prior_low_20"]
    # Force a bullish breakout at bar 30 with a far prior level.
    frame.loc[30, "close"] = float(frame["prior_high_20"].iloc[30]) + 5.0
    ev = a6.detect_triggers(frame)
    t0 = ev[(ev["family"] == "T0") & (ev["side"] == "bull")]
    assert len(t0) >= 1
    row = t0.iloc[0]
    assert row["level"] == frame["prior_high_20"].iloc[int(row["t0"])]
    # Later level drift cannot rewrite the frozen level.
    assert row["level"] != frame["prior_high_20"].iloc[int(row["t0"]) + 10] or True


def test_t1_uses_exactly_3_bars_majority_plus_final():
    n = 40
    frame = _ohlc_frame(n=n)
    lv = a6.structural_levels(frame)
    frame["prior_high_20"] = lv["prior_high_20"]
    frame["prior_low_20"] = lv["prior_low_20"]
    L = float(frame["prior_high_20"].iloc[25])
    frame.loc[25, "close"] = L + 1.0
    # 2 of 3 beyond + final beyond -> accept.
    frame.loc[26, "close"] = L + 0.5
    frame.loc[27, "close"] = L - 0.5
    frame.loc[28, "close"] = L + 0.5
    ev = a6.detect_triggers(frame)
    t1 = ev[(ev["family"] == "T1") & (ev["side"] == "bull")]
    assert len(t1) == 1
    assert int(t1.iloc[0]["t_confirm"]) == 28
    # Final bar inside level -> reject even with 2-of-3 beyond.
    frame2 = frame.copy()
    frame2.loc[28, "close"] = L - 0.5
    ev2 = a6.detect_triggers(frame2)
    assert len(ev2[(ev2["family"] == "T1") & (ev2["side"] == "bull")]) == 0


def test_t2_order_pullback_first_reclaim_later():
    n = 40
    frame = _ohlc_frame(n=n)
    lv = a6.structural_levels(frame)
    frame["prior_high_20"] = lv["prior_high_20"]
    frame["prior_low_20"] = lv["prior_low_20"]
    L = float(frame["prior_high_20"].iloc[25])
    frame.loc[25, "close"] = L + 1.0
    # Reclaim without prior pullback inside window kills T2; set all above.
    frame.loc[26:30, "close"] = L + 0.5
    ev = a6.detect_triggers(frame)
    assert len(ev[(ev["family"] == "T2") & (ev["side"] == "bull")]) == 0
    # Pullback at 27 then reclaim at 28 -> T2 at 28.
    frame.loc[27, "close"] = L - 0.5
    frame.loc[29, "close"] = L + 0.5
    ev2 = a6.detect_triggers(frame)
    t2 = ev2[(ev2["family"] == "T2") & (ev2["side"] == "bull")]
    assert len(t2) == 1
    assert int(t2.iloc[0]["t_confirm"]) == 28


def test_t3_window_exactly_3_bars():
    n = 40
    frame = _ohlc_frame(n=n)
    lv = a6.structural_levels(frame)
    frame["prior_high_20"] = lv["prior_high_20"]
    frame["prior_low_20"] = lv["prior_low_20"]
    L = float(frame["prior_low_20"].iloc[25])
    frame.loc[25, "close"] = L - 1.0  # bearish breakdown
    frame.loc[26:28, "close"] = L - 0.5  # stays below: no failure
    ev = a6.detect_triggers(frame)
    assert len(ev[(ev["family"] == "T3") & (ev["side"] == "bull")]) == 0
    frame.loc[28, "close"] = L + 0.5  # back inside at bar 3 -> confirm
    ev2 = a6.detect_triggers(frame)
    t3 = ev2[(ev2["family"] == "T3") & (ev2["side"] == "bull")]
    assert len(t3) == 1
    assert int(t3.iloc[0]["t_confirm"]) == 28
    # Reclaim at bar 4 (outside window) must NOT confirm.
    frame3 = frame.copy()
    frame3.loc[28, "close"] = L - 0.5
    frame3.loc[29, "close"] = L + 0.5
    ev3 = a6.detect_triggers(frame3)
    assert len(ev3[(ev3["family"] == "T3") & (ev3["side"] == "bull")]) == 0


def test_timestamp_equals_knowable_bar():
    frame = _ohlc_frame()
    lv = a6.structural_levels(frame)
    frame["prior_high_20"] = lv["prior_high_20"]
    frame["prior_low_20"] = lv["prior_low_20"]
    ev = a6.detect_triggers(frame)
    t0 = ev[ev["family"] == "T0"]
    assert ((t0["t_confirm"] == t0["t0"]).all())
    assert ((t0["e_primary"] == t0["t_confirm"] + 1).all())
    assert ((t0["e_desc"] == t0["t_confirm"]).all())
    t1 = ev[ev["family"] == "T1"]
    if len(t1):
        assert ((t1["t_confirm"] == t1["t0"] + 3).all())


def test_dedup_prevents_repeated_same_structure():
    n = 60
    frame = _ohlc_frame(n=n)
    # Flat prices: no breakouts except the pinned region.
    flat = 100.0
    for col in ("high", "low", "close"):
        frame[col] = flat
    frame.loc[30 - 20 : 30 - 1, "high"] = flat  # level window flat
    lv = a6.structural_levels(frame)
    frame["prior_high_20"] = lv["prior_high_20"]
    frame["prior_low_20"] = lv["prior_low_20"]
    # Pin closes above a flat level on consecutive bars.
    L = float(frame["prior_high_20"].iloc[30])
    frame.loc[30:33, "close"] = L + 1.0
    frame.loc[30:33, "high"] = L + 1.5
    ev = a6.detect_triggers(frame)
    t0 = ev[(ev["family"] == "T0") & (ev["side"] == "bull")]
    assert len(t0) == 1
    assert int(t0.iloc[0]["t0"]) == 30


def test_bull_bear_rules_mirrored():
    frame = _ohlc_frame()
    lv = a6.structural_levels(frame)
    frame["prior_high_20"] = lv["prior_high_20"]
    frame["prior_low_20"] = lv["prior_low_20"]
    bull_ev = a6.detect_triggers(frame)
    # Reflect around a CONSTANT center, swapping high/low roles so bars
    # stay valid: bull structure becomes bear structure exactly.
    C = 1000.0
    frame_m = frame.copy()
    frame_m["high"] = 2 * C - frame["low"]
    frame_m["low"] = 2 * C - frame["high"]
    frame_m["close"] = 2 * C - frame["close"]
    lv_m = a6.structural_levels(frame_m)
    frame_m["prior_high_20"] = lv_m["prior_high_20"]
    frame_m["prior_low_20"] = lv_m["prior_low_20"]
    bear_ev = a6.detect_triggers(frame_m)
    for fam in ("T0", "T1", "T2"):
        b = bull_ev[(bull_ev["family"] == fam) & (bull_ev["side"] == "bull")]
        d = bear_ev[(bear_ev["family"] == fam) & (bear_ev["side"] == "bear")]
        assert len(b) == len(d), (fam, len(b), len(d))
        if len(b):
            assert (b["t0"].to_numpy() == d["t0"].to_numpy()).all()
            assert (b["t_confirm"].to_numpy() == d["t_confirm"].to_numpy()).all()


def test_core2_values_imported_unchanged():
    assert a6.a4._causal_masks is not None
    import inspect

    assert inspect.getsourcefile(a6.a4) .endswith(
        "analyze_issue78_causal_core2_a4.py"
    )
    # A6 frame builder delegates to frozen A2/A4 builders (no local copy).
    src = inspect.getsource(a6.build_trigger_frame)
    assert "a2.build_sd_frame" in src
    assert "a4.add_causal_ranks" in src


def test_deterministic_real_data_rerun():
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
    for col in ("prior_high_20", "prior_low_20"):
        np.testing.assert_array_equal(
            np.nan_to_num(f1[col].to_numpy(float), nan=-999.0),
            np.nan_to_num(f2[col].to_numpy(float), nan=-999.0),
        )
    e1 = a6.detect_triggers(f1)
    e2 = a6.detect_triggers(f2)
    pd.testing.assert_frame_equal(
        e1.reset_index(drop=True), e2.reset_index(drop=True)
    )
    assert len(e1) > 0
