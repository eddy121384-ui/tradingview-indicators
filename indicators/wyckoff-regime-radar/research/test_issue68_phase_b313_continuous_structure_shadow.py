#!/usr/bin/env python3
"""Synthetic contracts for Issue #68 B3.13."""
from __future__ import annotations

import numpy as np
import pandas as pd

import diagnose_issue68_phase_b313_continuous_structure_shadow as b313


def test_locked_formula_scale_and_symmetry() -> None:
    model = pd.DataFrame({
        "b313_dist_rank": [100.0, 75.0, 50.0, 25.0, 0.0],
        "b313_maturity_dist_rank": [100.0, 75.0, 50.0, 25.0, 0.0],
    })
    edge = b313.continuous_structure_edge(model)
    expected = np.array([17.0, 8.5, 0.0, -8.5, -17.0])
    assert np.allclose(edge, expected), (edge, expected)

    inverse = pd.DataFrame({
        "b313_dist_rank": 100.0 - model["b313_dist_rank"],
        "b313_maturity_dist_rank": 100.0 - model["b313_maturity_dist_rank"],
    })
    inv_edge = b313.continuous_structure_edge(inverse)
    assert np.allclose(edge, -inv_edge), (edge, inv_edge)


def test_stable_lead_is_bounded_by_original_loss_run() -> None:
    # Original is target-positive at bar 1, then loses bars 2-4 and hands off at 5.
    # Shadow has been positive since bar 1, but only bars 2-4 may count as lead.
    original = np.array([-1.0, 1.0, -1.0, -1.0, -1.0, 1.0])
    shadow = np.array([-1.0, 1.0, 1.0, 1.0, 1.0, 1.0])
    scored = np.ones(len(original), dtype=bool)
    lead = b313.stable_lead_within_original_loss_run(original, shadow, scored, 5, 0)
    assert lead == 3, lead

    shadow2 = np.array([-1.0, 1.0, -1.0, -1.0, 1.0, 1.0])
    lead2 = b313.stable_lead_within_original_loss_run(original, shadow2, scored, 5, 0)
    assert lead2 == 1, lead2


def test_transition_counter() -> None:
    side = np.array([False, False, True, True, False, True], dtype=bool)
    scored = np.ones(len(side), dtype=bool)
    assert b313.transitions(side, scored) == 3
    scored[4] = False
    assert b313.transitions(side, scored) == 1


if __name__ == "__main__":
    test_locked_formula_scale_and_symmetry()
    test_stable_lead_is_bounded_by_original_loss_run()
    test_transition_counter()
    print("B3.13 synthetic contracts PASS")
