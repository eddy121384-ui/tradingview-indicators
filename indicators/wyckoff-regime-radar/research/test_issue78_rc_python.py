from __future__ import annotations

import numpy as np
import pandas as pd

import generate_issue78_rc_python as m


def synthetic_ohlcv(rows: int = 2300) -> pd.DataFrame:
    x = np.arange(rows, dtype=float)
    close = 80.0 * np.exp(0.00015 * x + 0.08 * np.sin(x / 47.0) + 0.02 * np.sin(x / 8.0))
    open_ = close * np.exp(0.003 * np.sin(x / 5.0))
    spread = close * (0.008 + 0.002 * (1.0 + np.sin(x / 19.0)))
    high = np.maximum(open_, close) + spread
    low = np.maximum(0.01, np.minimum(open_, close) - spread)
    volume = 2_000_000.0 * (1.0 + 0.35 * np.sin(x / 13.0) + 0.12 * np.sin(x / 3.0))
    return pd.DataFrame(
        {
            "date": pd.date_range("2000-01-03", periods=rows, freq="B"),
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
    )


def compute(frame: pd.DataFrame) -> pd.DataFrame:
    ns = m.load_issue78_rc_namespace()
    return ns["compute_price_only"](frame)


def test_generated_source_contains_frozen_production_deltas():
    text = m.render_issue78_rc_python_source()
    assert "ISSUE #66 PHASE C-2" in text
    assert "ctx_down_ex_gate = np.minimum(downside_exhaustion_gate, current_bear_gate)" in text
    assert "ctx_up_ex_gate = np.minimum(upside_exhaustion_gate, current_bull_gate)" in text
    assert "volume_quality_score" in text
    assert "volume_weight_governed" in text
    assert "volume_breakout_confirmation" in text
    assert "volume_breakdown_confirmation" in text


def test_synthetic_stock_run_is_nontrivial():
    out = compute(synthetic_ohlcv())
    assert out["formal_id"].between(0, 6).all()
    assert out["candidate_display_id"].between(0, 6).all()
    assert out["top_id"].between(1, 6).all()
    valid = out["prob_acc"].notna()
    assert int(valid.sum()) > 300
    assert out.loc[valid, "formal_id"].nunique() > 1


def test_auto_volume_witness_activates_on_liquid_stock_fixture():
    out = compute(synthetic_ohlcv())
    active = out["volume_weight_applied"] > 0
    assert int(active.sum()) > 100
    assert float(out.loc[active, "volume_weight_applied"].max()) <= 0.20 + 1e-12
    assert float(out.loc[active, "volume_weight_governed"].max()) <= 0.20 + 1e-12


def test_missing_volume_falls_back_without_crashing():
    frame = synthetic_ohlcv().drop(columns=["volume"])
    out = compute(frame)
    assert np.nanmax(out["volume_weight_applied"].to_numpy(float)) == 0.0
    assert out["formal_id"].between(0, 6).all()


def test_future_mutation_cannot_change_past_outputs():
    frame = synthetic_ohlcv()
    base = compute(frame)
    cutoff = 2050
    changed = frame.copy()
    changed.loc[cutoff:, ["open", "high", "low", "close"]] *= 1.35
    changed.loc[cutoff:, "volume"] *= 4.0
    alt = compute(changed)
    for column in (
        "sym_atr",
        "volume_quality_score",
        "volume_weight_applied",
        "prob_markup",
        "prob_markdown",
        "evidence_strength",
        "formal_id",
    ):
        left = base.loc[: cutoff - 1, column].to_numpy()
        right = alt.loc[: cutoff - 1, column].to_numpy()
        np.testing.assert_allclose(left, right, atol=0.0, rtol=0.0, equal_nan=True)
