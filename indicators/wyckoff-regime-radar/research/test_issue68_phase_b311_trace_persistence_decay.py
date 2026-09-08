#!/usr/bin/env python3
"""Synthetic contracts for Issue #68 B3.11 Trace persistence audit."""
from __future__ import annotations

import numpy as np
import pandas as pd

import diagnose_issue68_phase_b311_trace_persistence_decay as b311


def _model(trace_edges: list[float]) -> pd.DataFrame:
    n = len(trace_edges)
    d: dict[str, np.ndarray] = {}
    # Make each non-Trace weighted edge exactly +1.0 in the S2 direction.
    specs = {
        "break": ("b38_breakout", "b38_breakdown"),
        "heat": ("b38_heat_up", "b38_panic_dn"),
        "structure": ("b38_structure_up", "b38_structure_dn"),
        "extension": ("b38_extension_up", "b38_extension_dn"),
        "continuation": ("b38_continuation_up", "b38_continuation_dn"),
    }
    import diagnose_issue68_phase_b38_raw_feature_attribution as b38
    for name, (up, dn) in specs.items():
        w = b38.COMPONENT_WEIGHTS[name]
        d[up] = np.full(n, 1.0 / w)
        d[dn] = np.zeros(n)

    trace_edges_arr = np.asarray(trace_edges, dtype=float)
    d["b38_acc_trace"] = np.zeros(n)
    d["b38_dist_trace"] = -trace_edges_arr / b38.COMPONENT_WEIGHTS["trace"]
    # Source-age inputs are diagnostic only in this fixture.
    d["b38_acc_raw0"] = np.zeros(n)
    d["b38_dist_raw0"] = d["b38_dist_trace"].copy()

    direct = 5.0 + trace_edges_arr
    d["b38_markup_raw0"] = direct
    d["b38_markdown_raw0"] = np.zeros(n)
    return pd.DataFrame(d)


def test_rolling_max_source_age_uses_most_recent_equal_max() -> None:
    raw = np.asarray([1.0, 3.0, 2.0, 3.0, 1.0])
    trace = np.asarray([np.nan, np.nan, 3.0, 3.0, 3.0])
    age = b311.rolling_max_source_age(raw, trace, 3)
    assert np.isnan(age[0]) and np.isnan(age[1])
    assert age[2] == 1.0
    assert age[3] == 0.0
    assert age[4] == 1.0


def test_stale_trace_visible_vs_blocking_are_separated() -> None:
    # Five non-Trace edges sum to +5. Trace=-3 is visible residual; Trace=-6 blocks S2.
    model = _model([-3.0, -6.0, -3.0, -6.0, 1.0])
    out = b311.direction_trace_audit(model, direction=1, warmup=0, window=1)
    assert out["stale_opposition_bars"] == 4
    assert out["stale_visible_only_bars"] == 2
    assert out["stale_raw_blocking_bars"] == 2
    assert out["trace_blocks_target_bars"] == 2
    assert out["unexplained_sign_flip_bars"] == 0


def test_trace_sign_flip_is_reciprocal_under_component_negation() -> None:
    model = _model([-3.0, -6.0, -3.0, -6.0, 1.0])
    bull = b311.direction_trace_audit(model, direction=1, warmup=0, window=1)

    # The same component arrays viewed in the opposite audit direction invert target semantics.
    bear = b311.direction_trace_audit(model, direction=-1, warmup=0, window=1)
    assert bull["_arrays"]["stale"].shape == bear["_arrays"]["stale"].shape
    # On this one-sided fixture the masks should not spuriously overlap.
    assert not np.any(bull["_arrays"]["stale"] & bear["_arrays"]["stale"])


def main() -> None:
    test_rolling_max_source_age_uses_most_recent_equal_max()
    test_stale_trace_visible_vs_blocking_are_separated()
    test_trace_sign_flip_is_reciprocal_under_component_negation()
    print("B3.11 synthetic contracts PASS")


if __name__ == "__main__":
    main()
