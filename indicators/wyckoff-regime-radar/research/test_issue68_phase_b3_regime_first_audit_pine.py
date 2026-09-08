#!/usr/bin/env python3
from __future__ import annotations

import unittest

import generate_issue68_phase_b3_regime_first_audit_pine as gen


class Issue68RegimeFirstAuditPineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = gen.generate(gen.HERE / gen.SOURCE_RELATIVE)

    def test_is_indicator_without_strategy_orders(self):
        self.assertIn('indicator("Chase Risk Radar｜Issue #68 Regime-first v3 Audit"', self.text)
        self.assertNotIn("strategy.", self.text)
        self.assertNotIn("strategy(", self.text)

    def test_reuses_runtime_validated_c2_core(self):
        self.assertIn("Issue #66 C-2", self.text)
        self.assertIn('volumeMode = "Off"', self.text)
        self.assertIn('mtfMode = "Off"', self.text)
        self.assertIn('divMode = "Off"', self.text)

    def test_v2_breakout_handshake_and_early_fail_are_absent(self):
        for token in ("issue68ArmedDir", "issue68EarlyFail", "issue68ArmLong", "LONG SETUP", "SHORT SETUP"):
            self.assertNotIn(token, self.text)

    def test_regime_first_mapping_is_present(self):
        required = (
            "issue68V3Stage == 2",
            "issue68V3After := 1",
            "issue68V3Stage == 5",
            "issue68V3After := -1",
            "issue68V3Stage == 1 or issue68V3Stage == 4",
            "issue68V3Stage == 3",
            "issue68V3Before == 1 ? 1 : 0",
            "issue68V3Stage == 6",
            "issue68V3Before == -1 ? -1 : 0",
            "issue68V3Stage == 0",
            "issue68V3After := issue68V3Before",
        )
        for token in required:
            self.assertIn(token, self.text)

    def test_breakout_is_visual_witness_only(self):
        self.assertIn("showIssue68V3BreakWitness", self.text)
        state_start = self.text.index("if issue68V3Ready")
        pane_start = self.text.index("// Audit pane: +1 Long / 0 Flat / -1 Short.")
        state_body = self.text[state_start:pane_start]
        self.assertNotIn("rangeBreakUp", state_body)
        self.assertNotIn("rangeBreakDn", state_body)


if __name__ == "__main__":
    unittest.main()
