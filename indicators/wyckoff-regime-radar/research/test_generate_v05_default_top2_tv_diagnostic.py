#!/usr/bin/env python3

from __future__ import annotations

import unittest

from generate_v05_default_top2_tv_diagnostic import (
    EXPECTED_SOURCE_BLOB_SHA,
    SOURCE,
    git_blob_sha,
    render,
)


class V05DefaultTop2TvDiagnosticTests(unittest.TestCase):
    def test_frozen_source_unchanged(self) -> None:
        self.assertEqual(git_blob_sha(SOURCE.read_bytes()), EXPECTED_SOURCE_BLOB_SHA)

    def test_real_defaults_are_preserved(self) -> None:
        source = render()
        self.assertIn('volumeMode = input.string("Auto"', source)
        self.assertIn('mtfMode = input.string("Observe Only"', source)
        self.assertIn('divMode = input.string("Observe Only"', source)
        self.assertNotIn('string volumeMode = "Off"', source)

    def test_action_compatible_top2_rule_is_present(self) -> None:
        source = render()
        self.assertIn('(topId == 2 and secondId == 3)', source)
        self.assertIn('(topId == 5 and secondId == 6)', source)
        self.assertIn('issue57Top2Sum >= 90.0', source)

    def test_original_visuals_removed_and_compact_table_added(self) -> None:
        source = render()
        self.assertNotIn('// Visuals', source)
        self.assertIn('var table issue57Table', source)
        self.assertIn('Issue57 volume quality', source)
        self.assertEqual(source.count('plot('), 8)

    def test_causal_horizon_scoring_uses_past_signal(self) -> None:
        source = render()
        for horizon in (5, 10, 20, 60):
            self.assertIn(f'issue57Top2Signal[{horizon}]', source)
            self.assertIn(f'close[{horizon}]', source)


if __name__ == "__main__":
    unittest.main()
