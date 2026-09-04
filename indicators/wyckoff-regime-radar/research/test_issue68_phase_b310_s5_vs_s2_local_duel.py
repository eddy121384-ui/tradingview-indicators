#!/usr/bin/env python3
from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np

import diagnose_issue68_phase_b310_s5_vs_s2_local_duel as b310
import generate_issue68_phase_b310_s5_vs_s2_local_duel_audit_pine as pine


class TestIssue68B310LocalDuel(unittest.TestCase):
    def _fixture(self):
        comps = {name: np.zeros(4, dtype=float) for name in b310.COMPONENTS}
        comps["break"][:] = [0.4, -0.8, -0.5, 0.3]
        comps["heat"][:] = [0.3, -0.2, 1.5, 0.4]
        comps["structure"][:] = [0.1, 0.0, 0.0, 0.1]
        comps["extension"][:] = [0.1, 0.0, 0.0, 0.1]
        comps["continuation"][:] = [0.05, 0.0, 0.0, 0.05]
        comps["trace"][:] = [0.05, 0.0, 0.0, 0.05]
        direct = np.sum(np.column_stack([comps[n] for n in b310.COMPONENTS]), axis=1)
        return {**comps, "direct": direct, "reconstructed": direct.copy()}

    def test_exact_handoff_final_blocker_and_driver(self):
        arrays = self._fixture()
        out = b310.direction_duel_from_arrays(arrays, 1, warmup=0)
        self.assertEqual(out["handoff_events"], 1)
        self.assertEqual(out["final_blocker_counts"]["break"], 1)
        self.assertEqual(out["handoff_driver_counts"]["heat"], 1)
        self.assertLessEqual(out["max_reconstruction_error"], b310.RECON_TOL)

    def test_reciprocal_oriented_handoff_is_exact(self):
        arrays = self._fixture()
        inverse = {
            name: -np.asarray(arrays[name], dtype=float) for name in b310.COMPONENTS
        }
        inverse["direct"] = -np.asarray(arrays["direct"], dtype=float)
        inverse["reconstructed"] = inverse["direct"].copy()
        bull = b310.direction_duel_from_arrays(arrays, 1, warmup=0)
        inv_bear = b310.direction_duel_from_arrays(inverse, -1, warmup=0)
        mirror = b310._mirror_event_compare(bull, inv_bear, warmup=0)
        self.assertEqual(mirror["event_agreement"], 1.0)
        self.assertEqual(mirror["final_blocker_agreement"], 1.0)
        self.assertEqual(mirror["handoff_driver_agreement"], 1.0)

    def test_generated_pine_is_diagnostic_only(self):
        text = pine.generate(Path(pine.HERE / pine.SOURCE_RELATIVE))
        self.assertIn("Issue #68 B3.10 exact S2 Markup vs S5 Markdown raw0 duel audit only", text)
        self.assertIn("B310 S2>S5 RAW band", text)
        self.assertIn("B310 BREAK EDGE band", text)
        self.assertIn("B310 TRACE EDGE band", text)
        self.assertIn("LARGEST S5 EDGE", text)
        self.assertNotIn("strategy.", text)
        self.assertNotIn("issue68B34A", text)


if __name__ == "__main__":
    unittest.main()
