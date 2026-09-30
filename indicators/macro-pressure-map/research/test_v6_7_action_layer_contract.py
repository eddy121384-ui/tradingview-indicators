#!/usr/bin/env python3
"""Deterministic contract tests for Issue #129 V6.7 shadow Action Layer."""
from __future__ import annotations

from pathlib import Path

from v6_6_core import V66Config, core_regime


MACRO_ROOT = Path(__file__).resolve().parents[1]
V66_PATH = MACRO_ROOT / "src" / "macro-pressure-map-v6.6.pine"
V67_PATH = MACRO_ROOT / "src" / "macro-pressure-map-v6.7.pine"

OLD_HEADER = 'indicator("Macro Pressure Map V6.6 [Tiered GPI/IPI/FCPI]", shorttitle="MPM V6.6", overlay=false, max_labels_count=50, max_lines_count=50)'
NEW_HEADER = 'indicator("Macro Pressure Map V6.7 [Tiered GPI/IPI/FCPI + Shadow Action Layer]", shorttitle="MPM V6.7", overlay=false, max_labels_count=50, max_lines_count=50)'

START = "// ISSUE-129 SHADOW ACTION LAYER BEGIN"
END = "// ISSUE-129 SHADOW ACTION LAYER END"


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _shadow_block(v67: str) -> str:
    start = v67.index(START)
    end = v67.index(END, start) + len(END)
    return v67[start:end]


def _strip_v67_delta(v67: str) -> str:
    """Remove the authorized V6.7 deltas and restore frozen V6.6 text."""
    block_start = v67.index("\n" + START)
    block_end = v67.index(END + "\n", block_start) + len(END + "\n")
    normalized = v67[:block_start] + v67[block_end:]
    normalized = normalized.replace(NEW_HEADER, OLD_HEADER, 1)
    return normalized.replace('table.cell(dash, 1, 0, "V6.7"', 'table.cell(dash, 1, 0, "V6.6"', 1)


def _expected_tilt(growth: float, inflation: float, cfg: V66Config) -> tuple[int, int, int, int]:
    active = growth > cfg.growth_threshold and inflation > cfg.inflation_threshold
    return (1, -1, 0, 0) if active else (0, 0, 0, 0)


def test_v67_is_v66_plus_only_header_dashboard_version_and_shadow_block() -> None:
    v66 = _source(V66_PATH)
    v67 = _source(V67_PATH)
    assert _strip_v67_delta(v67) == v66


def test_shadow_block_is_non_user_facing_and_disabled() -> None:
    block = _shadow_block(_source(V67_PATH))

    required = (
        "shadowActionLayerEnabled = false",
        "shadowActionSignalActive = growthPositive and inflationPositive",
        "shadowEquityTilt = shadowActionSignalActive ? 1 : 0",
        "shadowDurationTilt = shadowActionSignalActive ? -1 : 0",
        "shadowCashTilt = 0",
        "shadowInflationHedgeTilt = 0",
        "shadowEquityPp = shadowActionSignalActive ? 5.0 : 0.0",
        "shadowDurationPp = shadowActionSignalActive ? -5.0 : 0.0",
        "shadowCashPp = 0.0",
        "shadowInflationHedgePp = 0.0",
    )
    for line in required:
        assert line in block

    forbidden = ("input.", "plot(", "plotchar(", "plotshape(", "alertcondition(", "table.cell(", "strategy.")
    for token in forbidden:
        assert token not in block


def test_only_exact_v66_regime_3_receives_tilt() -> None:
    cfg = V66Config()
    cases = {
        (20.0, -20.0): (1, (0, 0, 0, 0)),
        (20.0, 0.0): (2, (0, 0, 0, 0)),
        (20.0, 20.0): (3, (1, -1, 0, 0)),
        (0.0, -20.0): (4, (0, 0, 0, 0)),
        (0.0, 0.0): (5, (0, 0, 0, 0)),
        (0.0, 20.0): (6, (0, 0, 0, 0)),
        (-20.0, -20.0): (7, (0, 0, 0, 0)),
        (-20.0, 0.0): (8, (0, 0, 0, 0)),
        (-20.0, 20.0): (9, (0, 0, 0, 0)),
    }

    expected_names = {
        1: "Goldilocks / Disinflationary Expansion",
        2: "Benign Expansion / Stable Inflation",
        3: "Reflation / Inflation Rising",
        4: "Disinflationary Drift",
        5: "Neutral / Range-bound Macro",
        6: "Inflation Pressure without Growth Confirmation",
        7: "Slowdown / Disinflation",
        8: "Growth Slowdown / Stable Inflation",
        9: "Stagflation Pressure",
    }

    for (g, i), (regime_id, expected_tilt) in cases.items():
        assert core_regime(g, i, cfg) == expected_names[regime_id]
        assert _expected_tilt(g, i, cfg) == expected_tilt


def test_regime_3_uses_exact_v66_mild_threshold_boundaries() -> None:
    cfg = V66Config()

    assert _expected_tilt(10.0, 20.0, cfg) == (0, 0, 0, 0)
    assert _expected_tilt(20.0, 10.0, cfg) == (0, 0, 0, 0)
    assert _expected_tilt(10.0001, 10.0001, cfg) == (1, -1, 0, 0)
    assert _expected_tilt(60.0, 60.0, cfg) == (1, -1, 0, 0)
