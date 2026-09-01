#!/usr/bin/env python3
"""Synthetic contracts for Issue #68 B3.15 event-window / stale-memory audit."""
import numpy as np

from diagnose_issue68_phase_b315_event_window_stale_memory import find_event_ma_flip, measure_window


def main() -> None:
    ma = np.array([False, False, True, True, True, False, False], dtype=bool)
    direct = np.array([-1.0, -0.5, 0.2, 0.4, 0.5, -0.1, -0.2])

    flip, pop = find_event_ma_flip(4, ma, direct, 0)
    assert flip == 2
    assert pop == "MA_TARGET_AT_BLOCKER"

    old_mem = np.array([False, False, True, True, False, False, False], dtype=bool)
    new_range = np.array([False, False, False, True, True, False, False], dtype=bool)
    break_edge = np.array([-1.0, -1.0, -0.8, -0.3, 0.4, -0.2, -0.2])
    w = measure_window(flip, ma, old_mem, new_range, break_edge)
    assert w["old_range_survival_bars"] == 2
    assert w["new_range_delay_bars"] == 1
    assert w["break_release_delay_bars"] == 2
    assert w["stale_overlap_bars"] == 2
    assert w["break_old_overlap_bars"] == 2
    assert w["has_stale_overlap_break_old"] is True
    assert w["new_range_before_old_clear"] is True

    ma2 = np.array([False, False, False, True, True, False], dtype=bool)
    direct2 = np.array([-1.0, -0.5, 0.3, 0.4, 0.2, -0.2])
    flip2, pop2 = find_event_ma_flip(2, ma2, direct2, 0)
    assert flip2 == 3
    assert pop2 == "PRE_MA_FLIP_AT_BLOCKER"

    ma3 = np.array([False, False, False, True], dtype=bool)
    direct3 = np.array([-1.0, -0.5, 0.3, -0.1])
    flip3, pop3 = find_event_ma_flip(2, ma3, direct3, 0)
    assert flip3 is None
    assert pop3 == "PRE_MA_FLIP_AT_BLOCKER"

    print("B3.15 synthetic event-window contracts PASS")


if __name__ == "__main__":
    main()
