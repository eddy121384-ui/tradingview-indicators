#!/usr/bin/env python3
"""Synthetic contracts for Issue #68 B3.17 global false-release / churn audit."""
from __future__ import annotations

import numpy as np

import diagnose_issue68_phase_b317_global_false_release_churn as b317


def main() -> None:
    mask = np.array([False, True, True, False, True, False, True, True, True], dtype=bool)
    assert b317.contiguous_runs(mask, 0) == [(1, 3), (4, 5), (6, 9)]
    assert b317.contiguous_runs(mask, 4) == [(4, 5), (6, 9)]

    v = np.array([np.nan, -1.0, -0.5, 0.2, 0.3, -0.1, 0.1, 0.2])
    assert b317.positive_transition_count(v, 1) == 3

    r = b317.build_report()
    a = r["aggregate"]
    assert r["primary_gate_pass"]
    assert a["unexplained_episode_accounting"] == 0
    assert a["minimum_eligibility_mirror_agreement"] >= b317.GATE
    assert a["minimum_advance_mirror_agreement"] >= b317.GATE
    assert a["minimum_episode_outcome_mirror_agreement"] >= b317.GATE
    # Transition-count reciprocity is preregistered as a diagnostic output, not a hard gate.
    assert 0.0 <= a["minimum_transition_count_mirror_agreement"] <= 1.0
    assert a["max_break_reconstruction_error"] <= b317.TOL
    assert a["max_observed_reconstruction_error"] <= b317.TOL
    assert a["max_shadow_reconstruction_error"] <= b317.TOL

    text = str(r).lower()
    for forbidden in ("sharpe", "sortino", "profit_factor", "net_profit", "strategy_return"):
        assert forbidden not in text

    print("B3.17 synthetic/global contracts PASS")


if __name__ == "__main__":
    main()
