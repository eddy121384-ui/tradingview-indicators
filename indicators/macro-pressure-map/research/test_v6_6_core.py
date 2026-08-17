#!/usr/bin/env python3
"""Tests for the frozen Macro Pressure Map V6.6 Python mirror."""
from __future__ import annotations

import numpy as np
import pandas as pd

from v6_6_core import (
    SOURCE_COLUMNS,
    V66Config,
    component_score,
    compute_v66,
    core_regime,
    fcpi_state,
    gpi_state,
    ipi_state,
    weighted_avg_series,
    zscore,
)


def _synthetic_sources(rows: int = 520, seed: int = 7) -> pd.DataFrame:
    index = pd.date_range("2018-01-01", periods=rows, freq="B")
    rng = np.random.default_rng(seed)
    data: dict[str, np.ndarray] = {}
    for offset, column in enumerate(SOURCE_COLUMNS):
        shocks = rng.normal(0.0, 0.006 + offset * 0.00001, rows)
        data[column] = (80.0 + offset) * np.exp(np.cumsum(shocks))
    return pd.DataFrame(data, index=index)


def test_threshold_boundaries_match_pine() -> None:
    cfg = V66Config()
    assert gpi_state(10.0, cfg) == "Growth Neutral"
    assert gpi_state(10.0001, cfg) == "Mild Growth"
    assert gpi_state(60.0, cfg) == "Growth Euphoria"
    assert gpi_state(-10.0, cfg) == "Growth Neutral"
    assert gpi_state(-10.0001, cfg) == "Mild Slowdown"
    assert gpi_state(-60.0, cfg) == "Severe Slowdown"

    assert ipi_state(10.0, cfg) == "Stable Inflation"
    assert ipi_state(10.0001, cfg) == "Inflation Rising"
    assert ipi_state(60.0, cfg) == "Inflation Shock"
    assert ipi_state(-60.0, cfg) == "Deflation Pressure"

    assert fcpi_state(30.0, cfg) == "Neutral Conditions"
    assert fcpi_state(30.0001, cfg) == "Conditions Tightening"
    assert fcpi_state(60.0, cfg) == "Financial Stress"
    assert fcpi_state(-30.0, cfg) == "Neutral Conditions"
    assert fcpi_state(-30.0001, cfg) == "Conditions Easing"
    assert fcpi_state(-60.0, cfg) == "Very Loose Conditions"


def test_core_regime_covers_all_nine_cells() -> None:
    cfg = V66Config()
    cases = {
        (20.0, -20.0): "Goldilocks / Disinflationary Expansion",
        (20.0, 0.0): "Benign Expansion / Stable Inflation",
        (20.0, 20.0): "Reflation / Inflation Rising",
        (0.0, -20.0): "Disinflationary Drift",
        (0.0, 0.0): "Neutral / Range-bound Macro",
        (0.0, 20.0): "Inflation Pressure without Growth Confirmation",
        (-20.0, -20.0): "Slowdown / Disinflation",
        (-20.0, 0.0): "Growth Slowdown / Stable Inflation",
        (-20.0, 20.0): "Stagflation Pressure",
    }
    for values, expected in cases.items():
        assert core_regime(*values, cfg) == expected


def test_weighted_average_reweights_around_missing_values() -> None:
    index = pd.RangeIndex(3)
    a = pd.Series([10.0, np.nan, 10.0], index=index)
    b = pd.Series([20.0, 20.0, np.nan], index=index)
    result = weighted_avg_series([(a, 0.25), (b, 0.75)])
    assert np.allclose(result.to_numpy(), [17.5, 20.0, 10.0], equal_nan=True)


def test_zscore_uses_last_non_na_values_like_pine() -> None:
    src = pd.Series([1.0, 2.0, 3.0, np.nan, 4.0])
    result = zscore(src, 3)
    expected = (4.0 - 3.0) / np.std([2.0, 3.0, 4.0], ddof=0)
    assert np.isclose(result.iloc[-1], expected)


def test_zero_real_yield_roc_na_does_not_poison_following_252_bars() -> None:
    cfg = V66Config()
    src = pd.Series(np.linspace(-1.2, 1.3, 700))
    src.iloc[300] = 0.0
    score = component_score(src, False, cfg.z_len_daily, cfg)

    # A zero denominator makes ROC undefined exactly 20 and 63 bars later.
    assert pd.isna(score.iloc[320])
    assert pd.isna(score.iloc[363])

    # Pine's rolling statistics ignore those isolated na values, so the next
    # valid bar recovers immediately instead of being poisoned for 252 bars.
    assert np.isfinite(score.iloc[321])
    assert np.isfinite(score.iloc[364])


def test_default_market_only_path_produces_axes_and_states() -> None:
    out = compute_v66(_synthetic_sources())
    finite = out[["GPI", "IPI", "FCPI"]].dropna()
    assert not finite.empty
    assert {"gpi_state", "ipi_state", "fcpi_state", "core_regime", "risk_note"}.issubset(out.columns)
    assert (out.loc[finite.index, ["GPI", "IPI", "FCPI"]].abs() <= 100.0 + 1e-12).all().all()


def test_future_rows_do_not_change_prior_outputs() -> None:
    sources = _synthetic_sources(rows=560)
    shorter = sources.iloc[:520]
    short_out = compute_v66(shorter)
    long_out = compute_v66(sources)
    cols = ["GPI", "IPI", "FCPI", "plot_GPI", "plot_IPI", "plot_FCPI"]
    pd.testing.assert_frame_equal(
        short_out[cols],
        long_out.loc[short_out.index, cols],
        check_exact=False,
        rtol=1e-12,
        atol=1e-12,
    )
