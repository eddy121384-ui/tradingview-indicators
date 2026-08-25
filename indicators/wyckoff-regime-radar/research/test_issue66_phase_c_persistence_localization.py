"""Contracts for Issue #66 Phase C Candidate→Formal persistence localization."""
import unittest

import numpy as np

import diagnose_issue66_phase_c_persistence_localization_v2 as cdiag


class Issue66PhaseCPersistenceLocalizationTests(unittest.TestCase):
    def test_generic_inertia_loop_is_exact_under_mirrored_inputs(self):
        rng = np.random.default_rng(66)
        n = 1200
        strong_stage = rng.integers(0, 7, size=n, dtype=int)
        strong_stage[rng.random(n) < 0.58] = 0
        mirrored_stage = cdiag.v1.mirror_stage(strong_stage)
        chaos = rng.random(n) < 0.27
        active = np.where(rng.random(n) < 0.18, 1, 3).astype(int)

        left = cdiag.v1.replay_formal(strong_stage, chaos, active, 3)
        right = cdiag.v1.replay_formal(mirrored_stage, chaos, active, 3)
        self.assertTrue(np.array_equal(cdiag.v1.mirror_stage(left), right))

        for kwargs in (
            {"immediate_confirm": True},
            {"immediate_chaos_reset": True},
            {"retain_confirmed": False},
        ):
            left_variant = cdiag.v1.replay_formal(strong_stage, chaos, active, 3, **kwargs)
            right_variant = cdiag.v1.replay_formal(mirrored_stage, chaos, active, 3, **kwargs)
            self.assertTrue(np.array_equal(cdiag.v1.mirror_stage(left_variant), right_variant))

    def test_stored_formal_replay_is_exact_per_fixture(self):
        for pair, frame in cdiag.v1.phasea.load_frozen_pairs().items():
            model, inverse, cfg, _warmup = cdiag.v1.load_pair(frame)
            for side, result in (("original", model), ("inverse", inverse)):
                top = cdiag.v1.arr_int(result, "top_id")
                strong = cdiag.v1.arr_bool(result, "strong_candidate")
                strong_stage = np.where(strong, top, 0).astype(int)
                chaos = cdiag.v1.arr_bool(result, "chaos")
                fast = cdiag.v1.arr_bool(result, "fast_switch")
                active = np.where(fast, cfg.fast_switch_confirm_bars, cfg.confirm_bars).astype(int)
                replay = cdiag.v1.replay_formal(strong_stage, chaos, active, int(cfg.confirm_bars))
                formal = cdiag.v1.arr_int(result, "formal_id")
                mismatch = np.flatnonzero(replay != formal)
                if len(mismatch):
                    i = int(mismatch[0])
                    lo = max(0, i - 4)
                    hi = min(len(formal), i + 3)
                    candidate_id = cdiag.v1.arr_int(result, "candidate_id")
                    candidate_bars = cdiag.v1.arr_int(result, "candidate_bars")
                    detail = {
                        "pair": pair,
                        "side": side,
                        "first_mismatch": i,
                        "window": [lo, hi],
                        "top": top[lo:hi].tolist(),
                        "strong": strong[lo:hi].astype(int).tolist(),
                        "strong_stage": strong_stage[lo:hi].tolist(),
                        "chaos": chaos[lo:hi].astype(int).tolist(),
                        "fast": fast[lo:hi].astype(int).tolist(),
                        "active_confirm": active[lo:hi].tolist(),
                        "candidate_id": candidate_id[lo:hi].tolist(),
                        "candidate_bars": candidate_bars[lo:hi].tolist(),
                        "stored_formal": formal[lo:hi].tolist(),
                        "replay_formal": replay[lo:hi].tolist(),
                    }
                    self.fail(f"Stored formal replay diverged: {detail}")

    def test_phase_c_replay_and_attribution_contract(self):
        report = cdiag.build_report()
        self.assertEqual(
            report["diagnostic_revision"],
            "v2_full_history_replay_before_warmup_scoring",
        )
        self.assertTrue(report["all_original_replays_exact"])
        self.assertEqual(
            report["strong_stage_mismatch_attribution"]["unexplained"]["strong_stage_mismatch_overlap"],
            0,
        )
        self.assertGreaterEqual(report["agreements"]["strong_stage"], 0.99)
        self.assertGreater(report["agreements"]["strong_stage"], report["agreements"]["formal"])
        self.assertGreaterEqual(report["state_carry_share_of_formal_mismatch"], 0.0)
        self.assertLessEqual(report["state_carry_share_of_formal_mismatch"], 1.0)
        self.assertNotIn("pnl", report)
        self.assertNotIn("strategy", report)


if __name__ == "__main__":
    unittest.main()
