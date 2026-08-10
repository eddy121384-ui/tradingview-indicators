#!/usr/bin/env python3

from __future__ import annotations

import json
import unittest

from diagnose_v06_breakout20_sensitivity import run_breakout20_sweep


class V06Breakout20SensitivityTests(unittest.TestCase):
    def test_development_only_20bar_probe_runs(self) -> None:
        report = run_breakout20_sweep()
        self.assertEqual(report["summary"]["case_count"], 8)
        self.assertGreater(report["summary"]["event_toggle_cases"], 0)
        self.assertGreater(report["summary"]["event_toggle_isolated_from_50bar_band_cases"], 0)
        compact = [
            {
                "pair": row["pair"],
                "side": row["side"],
                "distance50_atr": row["distance_20_to_50_atr"],
                "event": [row["event_below"], row["event_above"]],
                "recent": [row["recent_below"], row["recent_above"]],
                "continuation": [row["continuation_below"], row["continuation_above"]],
                "v05_l1": row["v05_probability_l1_jump"],
                "v06_l1": row["v06_probability_l1_jump"],
                "v06_top": row["v06_top"],
                "v06_candidate": row["v06_candidate"],
            }
            for row in report["cases"]
        ]
        print("V06_BREAKOUT20_CASES=" + json.dumps(compact, sort_keys=True))
        print("V06_BREAKOUT20_SUMMARY=" + json.dumps(report["summary"], sort_keys=True))


if __name__ == "__main__":
    unittest.main()
