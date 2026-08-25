from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from generate_issue66_phase_d1_parity_pine import generate  # noqa: E402


class Issue66PhaseD1ParityPineTests(unittest.TestCase):
    def test_generator_applies_accepted_c2_lineage_to_frozen_pine(self) -> None:
        source = HERE.parent / "src" / "chase-risk-market-regime-radar-v0.5.2.1.pine"
        pine = generate(source)

        self.assertIn('indicator("Chase Risk Radar｜Issue #66 C-2 Parity"', pine)
        self.assertIn('volumeMode = "Off"', pine)
        self.assertIn('mtfMode = "Off"', pine)
        self.assertIn('divMode = "Off"', pine)

        # v0.6 + B-1 representation.
        self.assertIn("f_issue66_softBreakAbove", pine)
        self.assertIn("maLog   = ta.sma(logPrice, maLen)", pine)
        self.assertIn("symATR  = ta.rma(logTR, atrLen)", pine)
        self.assertIn("maCrossUp      = ta.crossover(logPrice, maLog)", pine)
        self.assertIn("rangeBreakUpStrength = f_issue66_softBreakAbove", pine)

        # B-2/B-3.
        self.assertIn("breakoutRangeEvidence = f_clamp(nz(recentRangeBreakUpStrength", pine)
        self.assertIn("breakoutGate = f_clamp(breakoutScore / 100.0", pine)
        self.assertIn("nonEndDnGate = f_gate(100.0 - endRiskDnRaw", pine)
        self.assertNotIn("f_gate(panicHeatDn, 40.0, 80.0) *\n     structureWeakGate", pine)

        # B-5/B-6/B-7.
        self.assertIn("redistRaw0 = f_weighted5(bearBg, 0.20, rangeScore, 0.20, resistanceHolding, 0.25, 100.0 - heatUp", pine)
        self.assertIn("distRaw0 = f_weighted5(bullMaturityTrace, 0.20, rangeScore, 0.20, upsideExhaustion, 0.25, resistanceHolding, 0.25, lowVolScore", pine)
        self.assertIn("bullBackgroundForDistGate = f_gate(math.max(bullBg, bullMaturityTrace), 35.0, 75.0)", pine)
        self.assertIn("distGate     = rangeGate * bullBackgroundForDistGate", pine)

        # C-2 reciprocal Stage-1 candidate conflict.
        self.assertIn(
            "topId == 1 and resistanceHolding >= absorbThreshold and upsideExhaustion >= absorbThreshold and not markdownContinuationOverride",
            pine,
        )
        self.assertNotIn("topId == 1 and ((resistanceHolding >= absorbThreshold and reboundFailureGate > 0.50)", pine)

        # Issue #57 Phase-B persistence.
        self.assertIn("var int stalePressureBars = 0", pine)
        self.assertIn("staleLimit = confirmBars * 2", pine)
        self.assertIn("weakChallenger = confirmedId != 0", pine)
        self.assertIn("candidateDisplayId = candidateDisplayRawId", pine)

        # Parity harness is below Pine's 64-plot cap and strips production visuals.
        self.assertEqual(pine.count("plot("), 36)
        self.assertNotIn("// Visuals", pine)
        self.assertIn('plot(float(formalId), "PARITY formal_id"', pine)
        self.assertIn('plot(float(stalePressureReason), "PARITY stale_pressure_reason"', pine)

    def test_frozen_source_file_is_not_the_generated_harness(self) -> None:
        source = HERE.parent / "src" / "chase-risk-market-regime-radar-v0.5.2.1.pine"
        frozen = source.read_text(encoding="utf-8")
        self.assertIn("Chase Risk Market Regime Radar v0.5.2.1｜Non-functional Cleanup", frozen)
        self.assertNotIn("Issue #66 C-2 Parity", frozen)


if __name__ == "__main__":
    unittest.main()
