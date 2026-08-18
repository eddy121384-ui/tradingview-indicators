from __future__ import annotations

import re
import unittest

from generate_v06_parity_pine import EXPECTED_SOURCE_BLOB_SHA, SOURCE, git_blob_sha
from generate_v06_transition_health_preview_pine import render_preview_source


class TransitionHealthPreviewGeneratorTests(unittest.TestCase):
    def test_frozen_source_hash_is_unchanged(self) -> None:
        self.assertEqual(git_blob_sha(SOURCE.read_bytes()), EXPECTED_SOURCE_BLOB_SHA)

    def test_preview_preserves_visual_layer_and_forces_price_only_boundary(self) -> None:
        output = render_preview_source()
        self.assertIn('indicator("Chase Risk Radar v0.6｜Transition Health Preview"', output)
        self.assertIn('// Visuals', output)
        self.assertIn('plot(endRiskUp, "上漲末段風險"', output)
        self.assertIn('string volumeMode = "Off"', output)
        self.assertIn('string mtfMode = "Off"', output)
        self.assertIn('string divMode = "Off"', output)
        self.assertNotIn('volumeMode = input.string(', output)
        self.assertNotIn('mtfMode = input.string(', output)
        self.assertNotIn('divMode = input.string(', output)

    def test_preview_contains_only_frozen_transition_health_rules(self) -> None:
        output = render_preview_source()
        self.assertIn('int V06_TH_CHECKPOINT = 3', output)
        self.assertIn('int V06_TH_MAX_WATCH = 20', output)
        self.assertIn('v06ThCarriedWeight0 > v06ThContextWeight0', output)
        self.assertIn('v06ThContextWeightNow >= v06ThCarriedWeightNow', output)
        self.assertIn('v06ThWatchAge == V06_TH_CHECKPOINT and not v06ThResolvesNow', output)
        self.assertIn('"Handoff ↑"', output)
        self.assertIn('"Healthy ↑"', output)
        self.assertIn('"Damaged ↑"', output)
        self.assertIn('Transition Health State｜0 none 1 handoff 2 healthy 3 damaged', output)
        self.assertIn('transitionHealthParityLogs = input.bool(false', output)

    def test_preview_does_not_add_tuned_price_filters(self) -> None:
        output = render_preview_source()
        transition = output.split('// ===== Issue #57 v0.6 Transition Health｜frozen +3 OOS candidate =====', 1)[1]
        transition = transition.split('// ===== End Issue #57 Transition Health =====', 1)[0]
        forbidden = (
            'close >',
            'close <',
            'ta.atr',
            'ta.sma',
            'ta.ema',
            'return',
            'profit',
            'stop',
            'target',
        )
        for token in forbidden:
            self.assertNotIn(token, transition.lower())

    def test_plot_count_stays_below_tradingview_limit(self) -> None:
        output = render_preview_source()
        plot_calls = len(re.findall(r'(?m)^\s*plot\(', output))
        plotshape_calls = len(re.findall(r'(?m)^\s*plotshape\(', output))
        # hline/fill/table/label do not consume plot slots the same way as plot/plotshape.
        self.assertLessEqual(plot_calls + plotshape_calls, 64)


if __name__ == "__main__":
    unittest.main()
