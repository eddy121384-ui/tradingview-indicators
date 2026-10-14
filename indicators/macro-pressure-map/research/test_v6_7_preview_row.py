#!/usr/bin/env python3
"""Minimal regression tests for Issue #190 V6.7 informational preview row."""
from __future__ import annotations

from pathlib import Path

from v6_6_core import V66Config

MACRO_ROOT = Path(__file__).resolve().parents[1]
V67_PATH = MACRO_ROOT / "src" / "macro-pressure-map-v6.7.pine"

START = "// ISSUE-190 INFORMATIONAL PREVIEW ROW BEGIN"
END = "// ISSUE-190 INFORMATIONAL PREVIEW ROW END"


def _source() -> str:
    return V67_PATH.read_text(encoding="utf-8")


def _block(src: str) -> str:
    return src[src.index(START):src.index(END, src.index(START)) + len(END)]


def _preview_view(growth: float, inflation: float) -> str:
    if growth is None or inflation is None:
        return "Data unavailable"
    cfg = V66Config()
    active = growth > cfg.growth_threshold and inflation > cfg.inflation_threshold
    return "Research: Equity favored vs Duration" if active else "No View"


def test_preview_block_frozen_text() -> None:
    block = _block(_source())
    for s in (
        "Research: Equity favored vs Duration",
        "研究：股票相對長債偏多",
        "No View",
        "Data unavailable",
        "Allocation Research",
        "配置研究",
        "shadowActionSignalActive",
        "na(GPI) or na(IPI)",
    ):
        assert s in block, s
    for token in ("5pp", "+5", "-5", "%", "plot(", "alertcondition(", "strategy.", "input."):
        assert token not in block, token


def test_preview_nine_regimes_and_boundaries() -> None:
    assert _preview_view(20.0, 20.0) == "Research: Equity favored vs Duration"
    for g, i in [(20.0, -20.0), (20.0, 0.0), (0.0, -20.0), (0.0, 0.0),
                 (0.0, 20.0), (-20.0, -20.0), (-20.0, 0.0), (-20.0, 20.0)]:
        assert _preview_view(g, i) == "No View", (g, i)
    assert _preview_view(10.0, 20.0) == "No View"
    assert _preview_view(20.0, 10.0) == "No View"
    assert _preview_view(10.0001, 10.0001) == "Research: Equity favored vs Duration"
    assert _preview_view(None, 20.0) == "Data unavailable"
    assert _preview_view(20.0, None) == "Data unavailable"


def test_preview_row_wired_neutrally() -> None:
    src = _source()
    assert "table.cell(dash, 0, 20, lblAllocationResearch" in src
    assert "table.cell(dash, 1, 20, allocationResearchView" in src
    assert "shadowActionLayerEnabled = false" in src
