#!/usr/bin/env python3
from __future__ import annotations

import unittest
from pathlib import Path

import generate_issue68_phase_b_lifecycle_pine as phase_b
import generate_issue68_phase_b2_lifecycle_audit_pine as phase_b2
from generate_price_only_parity_pine import SOURCE_RELATIVE


HERE = Path(__file__).resolve().parent


class Issue68PhaseB2AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = HERE / SOURCE_RELATIVE
        cls.strategy = phase_b.generate(cls.source, "visual")
        cls.audit = phase_b2.generate(cls.source)

    def test_audit_is_indicator_without_strategy_orders(self) -> None:
        self.assertIn('indicator("Chase Risk Radar｜Issue #68 Lifecycle Semantic Audit"', self.audit)
        self.assertNotIn("strategy.", self.audit)
        self.assertNotIn('strategy("', self.audit)

    def test_lifecycle_state_machine_is_byte_identical_to_phase_b(self) -> None:
        strategy_segment = phase_b2.state_machine_segment(self.strategy, phase_b2.ORDER_MARKER)
        audit_segment = phase_b2.state_machine_segment(self.audit, phase_b2.AUDIT_MARKER)
        self.assertEqual(strategy_segment, audit_segment)

    def test_audit_pane_has_single_close_clock_visualization(self) -> None:
        required = (
            'plot(issue68Ready ? float(issue68Pos) : na, "Issue68 desired position"',
            'plot(issue68Ready and issue68ArmedDir != 0 ? float(issue68ArmedDir) * 0.5 : na',
            'title="Issue68 Bull ARM"',
            'title="Issue68 Bear ARM"',
            'title="Issue68 Long entry"',
            'title="Issue68 Short entry"',
            'title="Issue68 Long Early Fail"',
            'title="Issue68 Short Early Fail"',
            'title="Issue68 Long opposite exit"',
            'title="Issue68 Short opposite exit"',
            "location=location.absolute",
        )
        for token in required:
            self.assertIn(token, self.audit)

    def test_runtime_validated_c2_lineage_is_preserved(self) -> None:
        self.assertIn("Issue #66 C-2 runtime-validated price-only lineage", self.audit)
        self.assertIn("formalId = confirmedId", self.audit)
        self.assertIn("rangeBreakUp", self.audit)
        self.assertIn("rangeBreakDn", self.audit)


if __name__ == "__main__":
    unittest.main()
