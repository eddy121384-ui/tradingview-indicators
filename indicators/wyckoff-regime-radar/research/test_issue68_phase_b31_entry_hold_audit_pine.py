#!/usr/bin/env python3
import unittest

import generate_issue68_phase_b31_entry_hold_audit_pine as gen


class Issue68V31AuditPineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = gen.generate(gen.HERE / gen.SOURCE_RELATIVE)

    def test_is_pure_indicator(self):
        self.assertIn('indicator("Chase Risk Radar｜Issue #68 Entry/Hold v3.1 Audit"', self.text)
        self.assertNotIn('strategy.', self.text)

    def test_reuses_c2_strong_candidate_without_new_threshold(self):
        self.assertIn('issue68V31StrongStage = strongCandidate ? topId : 0', self.text)
        self.assertIn('issue68V31StrongStage == 2', self.text)
        self.assertIn('issue68V31StrongStage == 5', self.text)
        self.assertNotIn('input.float(', self.text.split('// Issue #68 Phase B3.1 preregistered Entry / Hold Separation.', 1)[1])

    def test_holding_does_not_require_strong_candidate(self):
        self.assertIn('if issue68V31Before == 1\n            issue68V31After := 1', self.text)
        self.assertIn('if issue68V31Before == -1\n            issue68V31After := -1', self.text)

    def test_no_v2_handshake_or_early_fail(self):
        for token in ('issue68ArmedDir', 'issue68EarlyFail', 'LONG SETUP', 'SHORT SETUP'):
            self.assertNotIn(token, self.text)


if __name__ == '__main__':
    unittest.main()
