from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from generate_issue66_phase_d1_parity_pine import SOURCE_RELATIVE, VISUAL_MARKER  # noqa: E402
from generate_issue66_phase_d2_visual_review_pine import D2_TITLE, generate  # noqa: E402


class Issue66PhaseD2VisualReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source_path = HERE / SOURCE_RELATIVE
        cls.source = cls.source_path.read_text(encoding="utf-8")
        cls.generated = generate(cls.source_path)

    def test_visual_dashboard_alert_tail_is_byte_stable(self) -> None:
        source_tail = self.source.split(VISUAL_MARKER, 1)[1].rstrip()
        generated_tail = self.generated.split(VISUAL_MARKER, 1)[1].rstrip()
        self.assertEqual(generated_tail, source_tail)

    def test_c2_price_only_core_is_present(self) -> None:
        text = self.generated
        self.assertIn(D2_TITLE, text)
        self.assertIn("maLog   = ta.sma(logPrice, maLen)", text)
        self.assertIn("symATR  = ta.rma(logTR, atrLen)", text)
        self.assertIn("nonEndDnGate = f_gate(100.0 - endRiskDnRaw, 35.0, 80.0)", text)
        self.assertIn("bullBackgroundForDistGate", text)
        self.assertIn("100.0 - heatUp, 0.20", text)
        self.assertIn(
            "topId == 1 and resistanceHolding >= absorbThreshold and upsideExhaustion >= absorbThreshold and not markdownContinuationOverride",
            text,
        )
        self.assertIn("Issue #57 Phase-B stale-pressure persistence", text)

    def test_price_only_witness_boundary_is_frozen(self) -> None:
        text = self.generated
        self.assertIn('volumeMode = "Off"  // Issue #66 D-2 forced price-only visual review', text)
        self.assertIn('mtfMode = "Off"  // Issue #66 D-2 forced price-only visual review', text)
        self.assertIn('divMode = "Off"  // Issue #66 D-2 forced price-only visual review', text)
        self.assertIn('witnessStageBiasMode = "Conservative"  // Issue #66 D-2 forced price-only visual review', text)
        self.assertNotIn('volumeMode = input.string("Auto"', text)
        self.assertNotIn('mtfMode = input.string("Observe Only"', text)
        self.assertNotIn('divMode = input.string("Observe Only"', text)

    def test_production_visual_surface_is_retained_without_parity_transport(self) -> None:
        text = self.generated
        self.assertEqual(text.count(VISUAL_MARKER), 1)
        self.assertIn("// v0.3.8.2 Dual Layer Background", text)
        self.assertIn("// Dashboard Table", text)
        self.assertIn("paceOneLine =", text)
        self.assertIn('plot(endRiskUp, "上漲末段風險"', text)
        self.assertIn("alertcondition(", text)
        self.assertNotIn("PARITY formal_id", text)
        self.assertNotIn("Issue #66 Phase D-1 parity export", text)
        self.assertNotIn("D1B|", text)
        self.assertNotIn("Phase D-1B Pine Logs transport", text)


if __name__ == "__main__":
    unittest.main()
