from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from generate_price_only_parity_pine import (  # noqa: E402
    FROZEN_SOURCE_BLOB_SHA,
    generate,
    git_blob_sha,
)


class GenerateParityPineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = HERE.parent / "src" / "chase-risk-market-regime-radar-v0.5.2.1.pine"
        cls.generated = generate(cls.source)

    def test_frozen_source_blob_is_exact(self) -> None:
        self.assertEqual(git_blob_sha(self.source.read_bytes()), FROZEN_SOURCE_BLOB_SHA)

    def test_witnesses_are_forced_off(self) -> None:
        self.assertIn('volumeMode = "Off"  // Issue #55 forced price-only', self.generated)
        self.assertIn('mtfMode = "Off"  // Issue #55 forced price-only', self.generated)
        self.assertIn('divMode = "Off"  // Issue #55 forced price-only', self.generated)
        self.assertIn('witnessStageBiasMode = "Conservative"  // Issue #55 forced price-only', self.generated)

    def test_required_parity_fields_are_exported(self) -> None:
        required = [
            "PARITY prob_acc",
            "PARITY prob_markup",
            "PARITY prob_reacc",
            "PARITY prob_dist",
            "PARITY prob_markdown",
            "PARITY prob_redist",
            "PARITY top_gap",
            "PARITY evidence_strength",
            "PARITY candidate_display_id",
            "PARITY formal_id",
        ]
        for field in required:
            with self.subTest(field=field):
                self.assertIn(field, self.generated)

    def test_original_visual_layer_is_removed(self) -> None:
        self.assertNotIn("// Visuals", self.generated)
        self.assertNotIn('plot(endRiskUp, "上漲末段風險"', self.generated)
        self.assertNotIn("table.new(", self.generated)
        self.assertNotIn("alertcondition(", self.generated)

    def test_plot_budget_is_exactly_ten(self) -> None:
        self.assertEqual(self.generated.count("plot("), 10)
        self.assertEqual(self.generated.count("Issue #55 Price-only parity export"), 1)


if __name__ == "__main__":
    unittest.main()
