#!/usr/bin/env python3
from __future__ import annotations

import unittest
from pathlib import Path

from generate_issue68_phase_b34_exposure_bakeoff_audit_pine import generate
from generate_price_only_parity_pine import SOURCE_RELATIVE

HERE = Path(__file__).resolve().parent


class Issue68B34ExposureBakeoffPineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = generate(HERE / SOURCE_RELATIVE)

    def test_reuses_runtime_validated_price_only_core(self):
        self.assertIn("Issue #66 C-2", self.text)
        self.assertIn('volumeMode = "Off"', self.text)
        self.assertIn('mtfMode = "Off"', self.text)
        self.assertIn('divMode = "Off"', self.text)
        self.assertIn("flatActionLevel", self.text)
        self.assertIn("paceCode", self.text)

    def test_core_bias_memory_remains_b33_semantics(self):
        self.assertIn("issue68B34Stage == 5 or issue68B34Stage == 6 ? -1 : 1", self.text)
        self.assertIn("issue68B34Stage == 2 or issue68B34Stage == 3 ? 1 : -1", self.text)

    def test_candidate_a_is_formal_family_only(self):
        self.assertIn("issue68B34Bias == 1 and (formalId == 2 or formalId == 3)", self.text)
        self.assertIn("issue68B34Bias == -1 and (formalId == 5 or formalId == 6)", self.text)

    def test_candidate_b_is_existing_flat_action_authorization(self):
        self.assertIn("issue68B34Bias == 1 and (flatActionLevel == 2 or flatActionLevel == 3)", self.text)
        self.assertIn("issue68B34Bias == -1 and (flatActionLevel == 4 or flatActionLevel == 5)", self.text)

    def test_candidate_c_uses_preregistered_mirrored_pace_defense(self):
        self.assertIn("paceCode == 0 or paceCode == 40 or paceCode == 70 or paceCode == 71 or paceCode == 75", self.text)
        self.assertIn("paceCode == 0 or paceCode == 15 or paceCode == 70 or paceCode == 71 or paceCode == 74", self.text)
        self.assertIn("issue68B34CBefore != 0 and issue68B34CBefore != issue68B34Bias", self.text)
        self.assertIn("no direct executable flip", self.text)

    def test_hard_bias_violation_diagnostics_present(self):
        self.assertIn("issue68B34ViolationA", self.text)
        self.assertIn("issue68B34ViolationB", self.text)
        self.assertIn("issue68B34ViolationC", self.text)

    def test_audit_has_no_strategy_or_legacy_lifecycle(self):
        for token in ("strategy.", "issue68ArmedDir", "issue68EarlyFail", "LONG SETUP", "SHORT SETUP", "D1B|"):
            self.assertNotIn(token, self.text)

    def test_human_readable_ui_is_default(self):
        self.assertIn("Human-readable audit rendering", self.text)
        self.assertIn('showIssue68B34StageBg = input.bool(false', self.text)
        self.assertIn('showIssue68B34Marks = input.bool(false', self.text)
        self.assertIn('showIssue68B34Legend = input.bool(true', self.text)
        self.assertIn('table.new(position.top_right, 2, 5', self.text)
        self.assertIn('CORE Bias band', self.text)
        self.assertIn('A Formal-family exposure', self.text)
        self.assertIn('B Flat-Action exposure', self.text)
        self.assertIn('C Stateful exposure', self.text)
        self.assertNotIn('plot.style_stepline', self.text)
        self.assertNotIn('Core Bias lane center', self.text)
        self.assertNotIn('A lane center', self.text)

    def test_transition_marks_are_optional_and_small(self):
        for token in (
            '"CORE -> LONG"',
            '"CORE -> SHORT"',
            '"A -> FLAT"',
            '"B -> FLAT"',
            '"C -> FLAT"',
            'size=size.tiny',
        ):
            self.assertIn(token, self.text)

    def test_data_window_semantic_counters_are_preserved(self):
        for token in (
            "B34 A Flat share %",
            "B34 B Flat share %",
            "B34 C Flat share %",
            "B34 A transitions",
            "B34 B transitions",
            "B34 C transitions",
        ):
            self.assertIn(token, self.text)


if __name__ == "__main__":
    unittest.main()
