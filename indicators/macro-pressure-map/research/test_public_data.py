#!/usr/bin/env python3
from __future__ import annotations

import numpy as np
import pandas as pd

from public_data import align_to_anchor, build_public_sources, selected_specs


def test_default_selection_matches_v66_market_only_contract() -> None:
    names = {spec.canonical for spec in selected_specs()}
    expected = {
        "spy", "iwm", "rsp", "xly", "xlp", "xli", "xlu", "copper", "gold",
        "breakeven_10y", "oil", "gasoline", "commodity_basket",
        "dxy", "vix", "move", "hyg", "ief", "hy_oas", "real_yield",
    }
    assert names == expected
    assert not {"breakeven_5y", "industrial_metals", "kre", "nfci", "pmi"} & names


def test_optional_selection_is_explicit() -> None:
    names = {spec.canonical for spec in selected_specs(
        include_t5yie=True,
        include_industrial_metals=True,
        include_kre=True,
        include_official_fci=True,
        include_macro=True,
    )}
    for expected in ("breakeven_5y", "industrial_metals", "kre", "nfci", "stlfsi", "pmi", "cpi", "wage"):
        assert expected in names


def test_align_to_anchor_forward_fills_but_never_backfills() -> None:
    anchor_idx = pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06", "2020-01-07"])
    spy = pd.Series([100.0, 101.0, 102.0, 103.0], index=anchor_idx)
    macro = pd.Series([2.0, 3.0], index=pd.to_datetime(["2020-01-03", "2020-01-07"]))
    frame = align_to_anchor({"spy": spy, "breakeven_10y": macro})
    assert np.isnan(frame.loc[pd.Timestamp("2020-01-02"), "breakeven_10y"])
    assert frame.loc[pd.Timestamp("2020-01-06"), "breakeven_10y"] == 2.0
    assert frame.loc[pd.Timestamp("2020-01-07"), "breakeven_10y"] == 3.0


def test_align_to_anchor_preserves_weekend_observation_for_next_trading_day() -> None:
    anchor_idx = pd.to_datetime(["2020-01-03", "2020-01-06", "2020-01-07"])
    spy = pd.Series([100.0, 101.0, 102.0], index=anchor_idx)
    monthly = pd.Series([7.0], index=pd.to_datetime(["2020-01-04"]))  # Saturday

    frame = align_to_anchor({"spy": spy, "pmi": monthly})

    assert np.isnan(frame.loc[pd.Timestamp("2020-01-03"), "pmi"])
    assert frame.loc[pd.Timestamp("2020-01-06"), "pmi"] == 7.0
    assert frame.loc[pd.Timestamp("2020-01-07"), "pmi"] == 7.0


def test_build_public_sources_uses_anchor_calendar_and_records_manifest() -> None:
    calendar = pd.bdate_range("2020-01-01", periods=8)

    def fake_download(spec, start, end):
        if spec.canonical == "spy":
            return pd.Series(np.arange(8, dtype=float) + 100.0, index=calendar)
        return pd.Series(np.arange(4, dtype=float) + 10.0, index=calendar[::2])

    frame, manifest = build_public_sources(
        "2020-01-01", "2020-02-01", downloader=fake_download
    )
    assert frame.index.equals(calendar)
    assert len(frame) == 8
    assert manifest["anchor_calendar"] == "spy"
    assert manifest["rows"] == 8
    assert len(manifest["series"]) == len(selected_specs())
    assert "Public providers are not TradingView" in manifest["parity_warning"]
    by_name = {entry["canonical"]: entry for entry in manifest["series"]}
    assert by_name["copper"]["pine_symbol"] == "COMEX:HG1!"
    assert by_name["copper"]["public_symbol"] == "HG=F"
    assert by_name["copper"]["aligned_coverage_pct"] == 100.0
