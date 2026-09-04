"""Contracts for Issue #68 Phase A lifecycle transplant."""
from __future__ import annotations

import unittest

import numpy as np

import diagnose_issue68_phase_a_lifecycle_transplant as diag
from issue68_lifecycle_v2 import lifecycle_v2


MIRROR = np.array([0, 4, 5, 6, 1, 2, 3], dtype=int)


def run(formal, up, down, close, hi=None, lo=None, *, warmup=0, confirm=3):
    n = len(formal)
    if hi is None:
        hi = np.full(n, 100.0)
    if lo is None:
        lo = np.full(n, 95.0)
    return lifecycle_v2(
        np.asarray(formal, dtype=int),
        np.asarray(up, dtype=bool),
        np.asarray(down, dtype=bool),
        np.asarray(close, dtype=float),
        np.asarray(hi, dtype=float),
        np.asarray(lo, dtype=float),
        warmup=warmup,
        confirm_bars=confirm,
    )


class Issue68LifecycleV2SemanticTests(unittest.TestCase):
    def test_no_flat_chase_inside_already_running_stage2_or_stage5(self):
        long_case = run([2, 2, 2, 2], [0, 1, 0, 1], [0, 0, 0, 0], [101, 102, 103, 104])
        short_case = run([5, 5, 5, 5], [0, 0, 0, 0], [0, 1, 0, 1], [94, 93, 92, 91])
        self.assertTrue(np.all(long_case.position == 0))
        self.assertTrue(np.all(short_case.position == 0))
        self.assertFalse(np.any(long_case.events["entry_long"]))
        self.assertFalse(np.any(short_case.events["entry_short"]))

    def test_exact_precursor_to_target_transition_break_is_accepted(self):
        long_case = run([1, 2], [0, 1], [0, 0], [99, 101])
        short_case = run([4, 5], [0, 0], [0, 1], [96, 94])
        self.assertEqual(int(long_case.position[-1]), 1)
        self.assertEqual(int(short_case.position[-1]), -1)
        self.assertTrue(bool(long_case.events["direct_transition_long"][-1]))
        self.assertTrue(bool(short_case.events["direct_transition_short"][-1]))

    def test_formal_zero_holds_and_only_opposite_family_exits(self):
        life = run(
            [1, 2, 0, 3, 2, 4],
            [1, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [99, 101, 102, 103, 104, 103],
        )
        self.assertEqual(list(life.position), [0, 1, 1, 1, 1, 0])
        self.assertTrue(bool(life.events["opposite_exit_long"][-1]))

    def test_early_fail_only_during_first_confirm_bars(self):
        # Entry at t=1, anchor=100. Ages 1/2/3 survive. A failure at age 4 must
        # not exit because the structural protection has already retired.
        life = run(
            [1, 2, 2, 2, 2, 2],
            [1, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [99, 101, 101, 101, 101, 99],
        )
        self.assertTrue(bool(life.events["entry_long"][1]))
        self.assertFalse(np.any(life.events["early_fail_long"]))
        self.assertEqual(int(life.position[-1]), 1)

    def test_early_fail_blocks_same_trend_reentry_until_brand_new_setup(self):
        life = run(
            [1, 2, 2, 2, 1, 2],
            [1, 0, 0, 1, 1, 0],
            [0, 0, 0, 0, 0, 0],
            [99, 101, 99, 102, 99, 101],
        )
        self.assertTrue(bool(life.events["early_fail_long"][2]))
        # t=3 is a fresh break inside already-running Stage 2: no chase.
        self.assertEqual(int(life.position[3]), 0)
        self.assertFalse(bool(life.events["entry_long"][3]))
        # t=4 is a genuinely new Stage-1 arm; t=5 confirms Stage 2.
        self.assertTrue(bool(life.events["arm_long"][4]))
        self.assertTrue(bool(life.events["entry_long"][5]))
        self.assertEqual(int(life.position[5]), 1)

    def test_synthetic_reciprocal_state_machine_is_exact(self):
        formal = np.array([1, 2, 0, 2, 4, 4, 5, 5, 5, 4, 5, 0, 5, 1], dtype=int)
        up = np.array([1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], dtype=bool)
        down = np.array([0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0], dtype=bool)
        close = np.array([99, 101, 102, 103, 102, 96, 94, 96, 94, 96, 94, 93, 92, 93], dtype=float)
        hi = np.full(len(formal), 100.0)
        lo = np.full(len(formal), 95.0)

        left = run(formal, up, down, close, hi, lo)
        inv_formal = MIRROR[formal]
        right = run(inv_formal, down, up, 1.0 / close, 1.0 / lo, 1.0 / hi)

        np.testing.assert_array_equal(left.position, -right.position)
        np.testing.assert_array_equal(left.armed_dir, -right.armed_dir)
        pairs = diag.EVENT_MIRRORS
        for event, mirror_event in pairs.items():
            np.testing.assert_array_equal(left.events[event], right.events[mirror_event], err_msg=event)


class Issue68PhaseAActualDataContractTests(unittest.TestCase):
    def test_preregistered_actual_lifecycle_mirror_gate(self):
        report = diag.build_report()
        self.assertTrue(report["primary_gate_pass"])
        self.assertGreaterEqual(
            report["aggregate"]["desired_position_mirror_agreement"],
            diag.PHASE_A_GATE,
        )
        self.assertGreater(
            report["aggregate"]["desired_position_mirror_agreement"],
            diag.OLD_LIFECYCLE_MIRROR_BASELINE,
        )
        self.assertEqual(report["status"], "LIFECYCLE_V2_TRANSPLANT_REUSED_DATA_NO_PNL")
        self.assertNotIn("strategy_metrics", report)
        self.assertNotIn("pnl", report)


if __name__ == "__main__":
    unittest.main()
