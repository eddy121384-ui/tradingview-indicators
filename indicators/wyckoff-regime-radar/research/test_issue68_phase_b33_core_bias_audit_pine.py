#!/usr/bin/env python3
from __future__ import annotations

import unittest

import generate_issue68_phase_b33_core_bias_audit_pine as gen


class Issue68CoreBiasAuditPineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = gen.generate(gen.HERE / gen.SOURCE_RELATIVE)

    def test_is_indicator_not_strategy(self):
        self.assertIn('indicator("Chase Risk Radar｜Issue #68 Core Bias v3.3 Audit"', self.text)
        self.assertNotIn("strategy.", self.text)

    def test_reuses_c2_price_only_lineage(self):
        self.assertIn("Issue #66 C-2", self.text)
        self.assertIn('volumeMode = "Off"', self.text)
        self.assertIn('mtfMode = "Off"', self.text)
        self.assertIn('divMode = "Off"', self.text)

    def test_core_bias_contract_present(self):
        self.assertIn("issue68V33Stage == 5 or issue68V33Stage == 6 ? -1 : 1", self.text)
        self.assertIn("issue68V33Stage == 2 or issue68V33Stage == 3 ? 1 : -1", self.text)
        self.assertIn("Issue68 V33 core bias memory", self.text)
        self.assertIn("bias is regime memory, NOT executable desired exposure", self.text)

    def test_legacy_lifecycle_absent(self):
        for token in ("issue68ArmedDir", "issue68EarlyFail", "LONG SETUP", "SHORT SETUP", "D1B|"):
            self.assertNotIn(token, self.text)


if __name__ == "__main__":
    unittest.main()
