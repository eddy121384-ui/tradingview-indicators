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
        self.assertIn("process_orders_on_close=true", text)
        self.assertIn("commission_value=0.02", text)

    def test_visual_audit_events_exist(self) -> None:
        text = build()
        for token in (
            "issue61ArmLong",
            "issue61ArmShort",
            "issue61ManagedEntryLong",
            "issue61ManagedEntryShort",
            "issue61EarlyFailLong",
            "issue61EarlyFailShort",
            "issue61RegimeExitLong",
            "issue61RegimeExitShort",
            'text="ARM"',
            'text="FAIL"',
            'text="EXIT"',
        ):
            self.assertIn(token, text)

    def test_frozen_entry_and_early_invalidation_semantics_are_visible(self) -> None:
        text = build()
        self.assertIn("rangeBreakUp and issue61Stage == 2", text)
        self.assertIn("rangeBreakDn and issue61Stage == 5", text)
        self.assertIn("rangeBreakUp and issue61Stage == 1", text)
        self.assertIn("rangeBreakDn and issue61Stage == 4", text)
        self.assertIn("issue61EntryAge <= confirmBars", text)
        self.assertIn("close <= issue61EntryLevel", text)
        self.assertIn("close >= issue61EntryLevel", text)
        self.assertNotIn("strategy.exit(", text)

    def test_dashboard_tail_is_removed(self) -> None:
        text = build()
        self.assertNotIn("// v0.3.8 Dashboard Label Semantics Layer", text)
        self.assertNotIn("Flat Action｜空手行動分級", text)


if __name__ == "__main__":
    unittest.main()
