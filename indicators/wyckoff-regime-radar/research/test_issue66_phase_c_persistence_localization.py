"""Contracts for Issue #66 Phase C actual stale-pressure localization."""
import unittest

import numpy as np

import diagnose_issue66_phase_c_persistence_localization_v3 as cdiag


class Issue66PhaseCPersistenceLocalizationTests(unittest.TestCase):
    def test_actual_phaseb_persistence_is_exact_under_mirrored_inputs(self):
        rng = np.random.default_rng(66)
        n = 1600
        strong_stage = rng.integers(0, 7, size=n, dtype=int)
        strong_stage[rng.random(n) < 0.62] = 0
        mirrored_strong = cdiag.v1.mirror_stage(strong_stage)

        display = rng.integers(0, 7, size=n, dtype=int)
        display[rng.random(n) < 0.45] = 0
        mirrored_display = cdiag.v1.mirror_stage(display)
        chaos = rng.random(n) < 0.20
        coexist = rng.random(n) < 0.18
        active = np.where(rng.random(n) < 0.20, 1, 3).astype(int)

        left = cdiag.replay_phaseb_persistence(strong_stage, display, chaos, coexist, active, 3)
        right = cdiag.replay_phaseb_persistence(mirrored_strong, mirrored_display, chaos, coexist, active, 3)

        self.assertTrue(np.array_equal(cdiag.v1.mirror_stage(left["formal"]), right["formal"]))
        self.assertTrue(np.array_equal(cdiag.v1.mirror_stage(left["candidate"]), right["candidate"]))
        self.assertTrue(np.array_equal(left["candidate_bars"], right["candidate_bars"]))
        self.assertTrue(np.array_equal(left["stale_bars"], right["stale_bars"]))
        self.assertTrue(np.array_equal(left["stale_reason"], right["stale_reason"]))

    def test_phase_c_exact_replay_and_attribution_contract(self):
        report = cdiag.build_report()
        self.assertEqual(report["diagnostic_revision"], "v3_actual_issue57_phaseb_stale_pressure_contract")
        self.assertTrue(report["all_original_replays_exact"])
        self.assertTrue(all(report["replay_exact_fields"].values()))
        self.assertEqual(
            report["strong_stage_mismatch_attribution"]["unexplained"]["strong_stage_mismatch_overlap"],
            0,
        )
        # Candidate display was already near mirror-exact at B-7, but the strong
        # confirmation-eligible subset is intentionally measured rather than assumed.
        self.assertGreaterEqual(report["agreements"]["candidate_display"], 0.99)
        self.assertGreaterEqual(report["state_carry_share_of_formal_mismatch"], 0.0)
        self.assertLessEqual(report["state_carry_share_of_formal_mismatch"], 1.0)
        self.assertNotIn("pnl", report)
        self.assertNotIn("strategy", report)


if __name__ == "__main__":
    unittest.main()
