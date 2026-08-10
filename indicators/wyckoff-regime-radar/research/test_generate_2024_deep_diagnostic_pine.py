from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from generate_2024_deep_diagnostic_pine import generate  # noqa: E402


class Generate2024DeepDiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        source = HERE.parent / "src" / "chase-risk-market-regime-radar-v0.5.2.1.pine"
        cls.generated = generate(source)

    def test_keeps_original_plot_budget(self) -> None:
        self.assertEqual(self.generated.count("plot("), 10)

    def test_adds_exactly_one_focused_diagnostic_table(self) -> None:
        self.assertEqual(self.generated.count("table.new("), 2)
        self.assertEqual(self.generated.count("Issue #55 2024-04-16 deep divergence diagnostic"), 1)
        self.assertIn("position.bottom_right", self.generated)
        self.assertIn('timestamp(syminfo.timezone, 2024, 4, 16, 0, 0)', self.generated)

    def test_deep_table_covers_both_decision_paths(self) -> None:
        required = [
            "SpeedRank",
            "PanicHeat",
            "RangeScore",
            "UpExh",
            "ResistHold",
            "DistRaw",
            "DistGate%",
            "DistEff",
            "ProbDist",
            "DownExh",
            "SupportHold",
            "MdExt",
            "MdCont",
            "MdRaw",
            "MdGate%",
            "MdEff",
            "ProbMd",
        ]
        for label in required:
            with self.subTest(label=label):
                self.assertIn(f'"{label}"', self.generated)


if __name__ == "__main__":
    unittest.main()
