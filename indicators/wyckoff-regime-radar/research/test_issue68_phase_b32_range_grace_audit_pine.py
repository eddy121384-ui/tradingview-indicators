#!/usr/bin/env python3
from __future__ import annotations

import unittest

import generate_issue68_phase_b32_range_grace_audit_pine as gen


class Issue68RangeGraceAuditPineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = gen.generate(gen.HERE / gen.SOURCE_RELATIVE)

    def test_is_indicator_not_strategy(self):
        self.assertIn('indicator("Chase Risk Radar｜Issue #68 Range-Grace v3.2 Audit"', self.text)
        self.assertNotIn("strategy.", self.text)

    def test_reuses_c2_price_only_lineage(self):
        self.assertIn("Issue #66 C-2", self.text)
        self.assertIn('volumeMode = "Off"', self.text)
        self.assertIn('mtfMode = "Off"', self.text)
        self.assertIn('divMode = "Off"', self.text)

    def test_range_grace_contract_present(self):
        self.assertIn("issue68V32Stage == 1 or issue68V32Stage == 4", self.text)
        self.assertIn("issue68V32GraceAfter >= confirmBars", self.text)
        self.assertIn("issue68V32RangeExitLong := true", self.text)
        self.assertIn("issue68V32RangeExitShort := true", self.text)
        self.assertIn("Issue68 V32 range grace bars", self.text)

    def test_legacy_breakout_lifecycle_absent(self):
        for token in ("issue68ArmedDir", "issue68EarlyFail", "LONG SETUP", "SHORT SETUP", "D1B|"):
            self.assertNotIn(token, self.text)


if __name__ == "__main__":
    unittest.main()
