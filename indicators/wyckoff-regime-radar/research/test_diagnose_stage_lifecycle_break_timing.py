#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

import numpy as np

from diagnose_stage_lifecycle_break_timing import (
    first_target_lag,
    last_event_age,
    summarize_break_side,
    summarize_target_onsets,
)
from generate_v06_phase_b_core import render_phase_b_source

HERE = Path(__file__).resolve().parent


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


class StageLifecycleBreakTimingTests(unittest.TestCase):
    def test_carried_forward_v06_dependencies_are_exact_issue57_blobs(self) -> None:
        expected = {
            "generate_v06_price_only_core.py": "36c8b1b7b311562a92620bc2167b1f6bd7db1577",
            "generate_v06_phase_b_core.py": "a81ac3c999da7b63b0628ad261bc45822a8d6e21",
            "v06_boundary_scores.py": "2d895d244100c6f614e127363e923597178ecde8",
        }
        for name, sha in expected.items():
            self.assertEqual(git_blob_sha(HERE / name), sha, name)

    def test_generated_phase_b_exposes_fresh_break_and_stale_decay_diagnostics(self) -> None:
        source = render_phase_b_source()
        self.assertIn('"range_break_up": range_break_up.astype(float)', source)
        self.assertIn('"range_break_dn": range_break_dn.astype(float)', source)
        self.assertIn('"formal_id": formal_id', source)
        self.assertIn('"stale_pressure_bars": stale_pressure_bars_series', source)

    def test_first_target_lag_uses_only_present_and_future_bars(self) -> None:
        formal = np.array([1, 1, 0, 2, 2, 3])
        self.assertEqual(first_target_lag(formal, 1, 2, horizon=5), 2)
        self.assertEqual(first_target_lag(formal, 3, 2, horizon=5), 0)
        self.assertIsNone(first_target_lag(formal, 4, 5, horizon=1))

    def test_break_already_inside_target_is_not_counted_as_later_confirmation(self) -> None:
        formal = np.array([0, 1, 2, 2, 2, 3, 0, 2, 2])
        events = np.array([False, False, False, True, False, False, True, False, False])
        result = summarize_break_side(formal, events, target=2, warmup=0)
        self.assertEqual(result["fresh_breaks"], 2)
        self.assertEqual(result["already_target_before_break"], 1)
        self.assertEqual(result["not_already_target_before_break"], 1)
        self.assertEqual(result["confirmation_within"]["1"], 1)

    def test_last_event_age_is_causal_and_looks_backward_only(self) -> None:
        events = np.array([False, True, False, False, True, False])
        self.assertEqual(last_event_age(events, 3, horizon=5), 2)
        self.assertEqual(last_event_age(events, 4, horizon=5), 0)
        self.assertIsNone(last_event_age(events, 0, horizon=5))

    def test_renewal_transition_reports_same_bar_fresh_break(self) -> None:
        formal = np.array([0, 3, 3, 2, 2, 6, 5])
        up_events = np.array([False, False, False, True, False, False, False])
        result = summarize_target_onsets(
            formal,
            up_events,
            target=2,
            initial_from=1,
            renewal_from=3,
            warmup=0,
        )
        renewal = result["renewal_transition"]
        self.assertEqual(renewal["events"], 1)
        self.assertEqual(renewal["fresh_break_same_bar"], 1)
        self.assertEqual(renewal["fresh_break_within_prior"]["1"], 1)


if __name__ == "__main__":
    unittest.main()
