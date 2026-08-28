#!/usr/bin/env python3
from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np

import diagnose_issue68_phase_b35_core_bias_reversal as diag
import generate_issue68_phase_b35_reversal_stack_audit_pine as pine


class TestIssue68B35ReversalAudit(unittest.TestCase):
    def test_trend_direction_mapping_is_symmetric_family_mapping(self) -> None:
        stages = np.arange(7, dtype=int)
        got = diag.trend_direction(stages)
        self.assertEqual(got.tolist(), [0, 0, 1, 1, 0, -1, -1])

    def test_direction_mirror_requires_sign_inversion_and_preserves_neutral(self) -> None:
        a = np.array([0, 1, 0, -1, 1, -1], dtype=int)
        b = -a
        m = diag._direction_mirror(a, b, 0)
        self.assertEqual(m["mirror_agreement"], 1.0)
        self.assertEqual(m["mismatch_bars"], 0)

    def test_generated_pine_is_forensic_only_and_keeps_frozen_core_semantics(self) -> None:
        text = pine.generate(Path(pine.HERE / pine.SOURCE_RELATIVE))
        for token in (
            "TOP -> STRONG -> FORMAL -> CORE",
            "TOP direction band",
            "STRONG direction band",
            "FORMAL direction band",
            "CORE direction memory band",
            "issue68B35Strong = issue68B35Ready and strongCandidate ? issue68B35Top : 0",
            "formalId == 5 or formalId == 6 ? -1 : 1",
            "formalId == 2 or formalId == 3 ? 1 : -1",
            "B35 Formal-to-Core invariant violation",
        ):
            self.assertIn(token, text)
        for forbidden in ("strategy.", "issue68B34A", "issue68B34B", "issue68B34C"):
            self.assertNotIn(forbidden, text)

    def test_generated_pine_defaults_to_clean_four_band_view(self) -> None:
        text = pine.generate(Path(pine.HERE / pine.SOURCE_RELATIVE))
        self.assertIn('showIssue68B35Marks = input.bool(false', text)
        self.assertIn('showIssue68B35Legend = input.bool(true', text)
        self.assertNotIn("bgcolor(", text.split("Issue #68 Phase B3.5 preregistered reversal-stack forensic.", 1)[1])


if __name__ == "__main__":
    unittest.main()
