#!/usr/bin/env python3
from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from evaluate_stage_lifecycle_base import stage_lifecycle_signal
from evaluate_stage_lifecycle_early_damage import (
    FROZEN_TH_BLOBS,
    early_damage_pulses,
    git_blob_sha,
    stage_lifecycle_with_early_damage,
    verify_frozen_transition_health_files,
    HERE,
)


class StageLifecycleEarlyDamageTests(unittest.TestCase):
    def test_transition_health_dependency_blobs_are_exact_issue57_versions(self) -> None:
        verify_frozen_transition_health_files()
        for name, expected in FROZEN_TH_BLOBS.items():
            self.assertEqual(git_blob_sha(HERE / name), expected)

    def test_early_damage_is_first_true_to_false_lead_loss_inside_plus3(self) -> None:
        th = pd.DataFrame(
            {
                "transition_health_tracked": [True, True, True, True, True],
                "transition_health_lead_held": [True, True, False, False, False],
                "transition_health_watch_age": [0, 1, 2, 3, 4],
            }
        )
        got = early_damage_pulses(th)
        np.testing.assert_array_equal(got, np.array([False, False, True, False, False]))

    def test_no_damage_overlay_is_identical_to_base_lifecycle(self) -> None:
        formal = np.array([1, 1, 2, 2, 3, 2, 4, 5, 6, 4])
        up = np.array([True, False, False, True, False, True, False, False, False, False])
        down = np.array([False, False, False, False, False, False, True, False, False, False])
        base, _ = stage_lifecycle_signal(formal, up, down, warmup=0, confirm_bars=3)
        managed, _ = stage_lifecycle_with_early_damage(
            formal,
            up,
            down,
            early_damage=np.zeros(len(formal), dtype=bool),
            th_direction=np.zeros(len(formal), dtype=int),
            th_resolution=np.zeros(len(formal), dtype=bool),
            warmup=0,
            confirm_bars=3,
        )
        np.testing.assert_array_equal(managed, base)

    def test_matching_damage_exits_blocks_until_resolution_and_does_not_auto_reenter(self) -> None:
        formal = np.array([2, 2, 2, 2, 2, 2, 2])
        up = np.array([True, False, False, True, False, True, False])
        down = np.zeros(len(formal), dtype=bool)
        damage = np.array([False, False, True, False, False, False, False])
        direction = np.array([1, 1, 1, 1, 0, 0, 0])
        resolution = np.array([False, False, False, False, True, False, False])
        managed, stats = stage_lifecycle_with_early_damage(
            formal, up, down, damage, direction, resolution, warmup=0, confirm_bars=3
        )
        self.assertEqual(managed[0], 1)
        self.assertEqual(managed[2], 0)  # matching Early Damaged exits.
        self.assertEqual(managed[3], 0)  # fresh break is blocked during same watch.
        self.assertEqual(managed[4], 0)  # resolution alone does not auto re-enter.
        self.assertEqual(managed[5], 1)  # a later fresh Stage-2 break can re-enter.
        self.assertEqual(stats["early_damage_long_exits"], 1)
        self.assertEqual(stats["blocked_bull_entry_attempts"], 1)
        self.assertEqual(stats["damage_block_resolutions"], 1)

    def test_opposite_direction_damage_does_not_exit_unrelated_position(self) -> None:
        formal = np.array([2, 2, 2, 2])
        up = np.array([True, False, False, False])
        down = np.zeros(len(formal), dtype=bool)
        damage = np.array([False, False, True, False])
        direction = np.array([0, -1, -1, -1])
        resolution = np.zeros(len(formal), dtype=bool)
        managed, stats = stage_lifecycle_with_early_damage(
            formal, up, down, damage, direction, resolution, warmup=0, confirm_bars=3
        )
        self.assertTrue(np.all(managed == 1))
        self.assertEqual(stats["early_damage_long_exits"], 0)

    def test_damage_cancels_matching_armed_setup_before_it_can_confirm(self) -> None:
        formal = np.array([1, 1, 1, 2, 2, 2])
        up = np.array([True, False, False, False, False, True])
        down = np.zeros(len(formal), dtype=bool)
        damage = np.array([False, False, True, False, False, False])
        direction = np.array([1, 1, 1, 1, 0, 0])
        resolution = np.array([False, False, False, False, True, False])
        managed, stats = stage_lifecycle_with_early_damage(
            formal, up, down, damage, direction, resolution, warmup=0, confirm_bars=3
        )
        self.assertEqual(managed[3], 0)
        self.assertEqual(stats["early_damage_bull_setup_cancels"], 1)
        self.assertEqual(managed[5], 1)  # fresh break after resolution required.


if __name__ == "__main__":
    unittest.main()
