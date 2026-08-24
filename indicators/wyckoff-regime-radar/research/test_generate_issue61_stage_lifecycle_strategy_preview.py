from __future__ import annotations

import hashlib
import unittest

from generate_issue61_stage_lifecycle_strategy_preview import SOURCE, build

EXPECTED_SOURCE_GIT_BLOB = "0745b61c9807d51762b60fb4f8c49222105f7087"


def git_blob_sha(data: bytes) -> str:
    payload = f"blob {len(data)}\0".encode() + data
    return hashlib.sha1(payload).hexdigest()


class Issue61StrategyPreviewContractTest(unittest.TestCase):
    def test_archived_v06_visual_source_is_byte_locked(self) -> None:
        self.assertEqual(git_blob_sha(SOURCE.read_bytes()), EXPECTED_SOURCE_GIT_BLOB)

    def test_generated_script_is_strategy_not_indicator(self) -> None:
        text = build()
        self.assertIn('strategy("Chase Risk Radar v0.6｜Stage Lifecycle Strategy Preview"', text)
        self.assertNotIn('indicator("Chase Risk Radar v0.6｜Transition Health Preview"', text)
        self.assertIn("process_orders_on_close=false", text)
        self.assertIn("default_qty_type=strategy.fixed", text)
        self.assertIn("default_qty_value=1", text)
        self.assertIn("commission_value=0.02", text)

    def test_visual_audit_events_exist(self) -> None:
        text = build()
        for token in (
            "issue61ArmLong",
            "issue61ArmShort",
            "issue61EntryLong",
            "issue61EntryShort",
            "issue61EarlyFailLong",
            "issue61EarlyFailShort",
            "issue61OppositeExitLong",
            "issue61OppositeExitShort",
            "issue61AddLongCandidate",
            "issue61AddShortCandidate",
            'text="ARM"',
            'text="ADD?"',
            'text="FAIL"',
            'text="EXIT"',
        ):
            self.assertIn(token, text)

    def test_flat_trader_does_not_chase_running_stage2_or_stage5(self) -> None:
        text = build()
        self.assertIn("rangeBreakUp and issue61Stage == 2 and formalId[1] == 1", text)
        self.assertIn("rangeBreakDn and issue61Stage == 5 and formalId[1] == 4", text)
        self.assertIn("rangeBreakUp and issue61Stage == 1", text)
        self.assertIn("rangeBreakDn and issue61Stage == 4", text)
        self.assertNotIn("if rangeBreakUp and issue61Stage == 2\n", text)
        self.assertNotIn("if rangeBreakDn and issue61Stage == 5\n", text)
        self.assertNotIn("RE-LONG", text)
        self.assertNotIn("RE-SHORT", text)

    def test_exit_requires_explicit_opposite_family(self) -> None:
        text = build()
        self.assertIn("issue61Stage == 4 or issue61Stage == 5 or issue61Stage == 6", text)
        self.assertIn("issue61Stage == 1 or issue61Stage == 2 or issue61Stage == 3", text)
        self.assertNotIn("not (issue61Stage == 2 or issue61Stage == 3)", text)
        self.assertNotIn("not (issue61Stage == 5 or issue61Stage == 6)", text)

    def test_early_invalidation_remains_but_has_no_auto_reentry(self) -> None:
        text = build()
        self.assertIn("issue61EntryAge <= confirmBars", text)
        self.assertIn("close <= issue61EntryLevel", text)
        self.assertIn("close >= issue61EntryLevel", text)
        self.assertIn("brand-new setup cycle", text)
        self.assertNotIn("issue61StoppedDir", text)
        self.assertNotIn("strategy.exit(", text)

    def test_continuation_break_is_candidate_not_order(self) -> None:
        text = build()
        self.assertIn("issue61Pos == 1 and issue61Stage == 2 and rangeBreakUp", text)
        self.assertIn("issue61Pos == -1 and issue61Stage == 5 and rangeBreakDn", text)
        self.assertIn("ADD CANDIDATES only", text)
        self.assertNotIn("pyramiding=1", text)

    def test_dashboard_tail_is_removed(self) -> None:
        text = build()
        self.assertNotIn("// v0.3.8 Dashboard Label Semantics Layer", text)
        self.assertNotIn("Flat Action｜空手行動分級", text)


if __name__ == "__main__":
    unittest.main()
