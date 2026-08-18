from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from diagnose_post_handoff_hold_persistence import build_rows
from transition_health_online import (
    CHECKPOINT,
    STATE_DAMAGED,
    STATE_HEALTHY,
    compute_transition_health,
)


COLS = (
    "prob_acc",
    "prob_markup",
    "prob_reacc",
    "prob_dist",
    "prob_markdown",
    "prob_redist",
)


def frame(rows: list[tuple[float, float, float, float, float, float]]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=COLS)


class TransitionHealthOnlineTests(unittest.TestCase):
    def test_healthy_requires_continuous_lead_through_plus_three(self) -> None:
        model = frame(
            [
                (35, 60, 3, 1, 1, 0),  # tracked {1,2} onset
                (30, 64, 4, 1, 1, 0),
                (28, 63, 7, 1, 1, 0),
                (25, 61, 11, 1, 1, 1),  # +3 unresolved and continuously held
                (5, 60, 32, 1, 1, 1),   # same-direction {2,3} resolves
                (2, 2, 2, 60, 30, 4),
            ]
        )
        out = compute_transition_health(model)
        self.assertTrue(bool(out.loc[0, "transition_health_handoff_pulse"]))
        self.assertTrue(bool(out.loc[3, "transition_health_healthy_pulse"]))
        self.assertFalse(bool(out["transition_health_damaged_pulse"].any()))
        self.assertEqual(int(out.loc[3, "transition_health_state"]), STATE_HEALTHY)
        self.assertEqual(int(out.loc[3, "transition_health_direction"]), 1)

    def test_any_tie_or_retake_before_plus_three_freezes_damaged(self) -> None:
        model = frame(
            [
                (35, 60, 3, 1, 1, 0),
                (52, 43, 3, 1, 1, 0),  # old context retakes
                (40, 54, 4, 1, 1, 0),
                (35, 58, 5, 1, 1, 1),  # carried recovered, but health stays damaged
                (5, 60, 32, 1, 1, 1),
            ]
        )
        out = compute_transition_health(model)
        self.assertTrue(bool(out.loc[3, "transition_health_damaged_pulse"]))
        self.assertFalse(bool(out.loc[3, "transition_health_healthy_pulse"]))
        self.assertEqual(int(out.loc[3, "transition_health_state"]), STATE_DAMAGED)

    def test_resolution_on_or_before_checkpoint_emits_no_health_label(self) -> None:
        model = frame(
            [
                (35, 60, 3, 1, 1, 0),
                (30, 64, 4, 1, 1, 0),
                (5, 60, 32, 1, 1, 1),  # actionable at +2
                (35, 60, 3, 1, 1, 0),
                (5, 60, 32, 1, 1, 1),
            ]
        )
        out = compute_transition_health(model)
        self.assertFalse(bool(out["transition_health_healthy_pulse"].any()))
        self.assertFalse(bool(out["transition_health_damaged_pulse"].any()))

    def test_context_dominant_watch_suppresses_later_seizure_until_resolution(self) -> None:
        model = frame(
            [
                (60, 35, 3, 1, 1, 0),  # context-dominant bridge starts hidden watch
                (35, 60, 3, 1, 1, 0),  # would be a seizure if overlap were allowed
                (30, 64, 4, 1, 1, 0),
                (25, 65, 5, 1, 1, 0),
                (5, 60, 32, 1, 1, 1),  # resolves hidden watch
                (35, 60, 3, 1, 1, 0),  # next bar can start a new visible watch
                (30, 64, 4, 1, 1, 0),
                (28, 63, 7, 1, 1, 0),
                (25, 61, 11, 1, 1, 1),
                (5, 60, 32, 1, 1, 1),
            ]
        )
        out = compute_transition_health(model)
        handoff_indices = np.flatnonzero(out["transition_health_handoff_pulse"].to_numpy(bool)).tolist()
        self.assertEqual(handoff_indices, [5])
        self.assertTrue(bool(out.loc[8, "transition_health_healthy_pulse"]))

    def test_online_plus_three_pulses_match_frozen_research_extractor(self) -> None:
        model = frame(
            [
                (35, 60, 3, 1, 1, 0),
                (30, 64, 4, 1, 1, 0),
                (28, 63, 7, 1, 1, 0),
                (25, 61, 11, 1, 1, 1),
                (5, 60, 32, 1, 1, 1),
                (2, 2, 2, 35, 60, 3),
                (2, 2, 2, 52, 43, 1),
                (2, 2, 2, 40, 54, 2),
                (2, 2, 2, 35, 58, 1),
                (2, 2, 2, 5, 60, 32),
                (35, 60, 3, 1, 1, 0),
                (30, 64, 4, 1, 1, 0),
                (5, 60, 32, 1, 1, 1),  # early resolution: no +3 row
                (1, 1, 1, 35, 60, 3),
                (1, 1, 1, 30, 64, 4),
                (1, 1, 1, 28, 63, 7),
                (1, 1, 1, 25, 61, 11),
                (1, 1, 1, 5, 60, 32),
            ]
        )
        _, checkpoints = build_rows(model)
        expected: dict[int, int] = {}
        for item in checkpoints:
            if int(item["checkpoint"]) != CHECKPOINT:
                continue
            bar = int(item["onset"]) + CHECKPOINT
            expected[bar] = STATE_HEALTHY if bool(item["lead_held_through_checkpoint"]) else STATE_DAMAGED

        out = compute_transition_health(model)
        actual: dict[int, int] = {}
        for bar in np.flatnonzero(
            out["transition_health_healthy_pulse"].to_numpy(bool)
            | out["transition_health_damaged_pulse"].to_numpy(bool)
        ):
            actual[int(bar)] = int(out.loc[bar, "transition_health_state"])
        self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
