from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from generate_issue66_phase_d1_parity_pine import SOURCE_RELATIVE, generate as generate_d1  # noqa: E402
from generate_issue66_phase_d1b_log_capture_pine import FIELDS, generate as generate_d1b  # noqa: E402
from parse_issue66_phase_d1b_pine_logs import COLUMNS, parse_text  # noqa: E402


class Issue66PhaseD1BLogCaptureTests(unittest.TestCase):
    def test_log_harness_is_d1_plus_transport_only(self) -> None:
        source = HERE / SOURCE_RELATIVE
        d1 = generate_d1(source)
        d1b = generate_d1b(source)
        self.assertTrue(d1b.startswith(d1.rstrip()))
        transport = d1b[len(d1.rstrip()):]
        self.assertIn("Issue #66 Phase D-1B Pine Logs transport", transport)
        self.assertIn('input.int(1200, "D1B Pine Logs capture bars"', transport)
        self.assertIn("log.info(", transport)
        self.assertEqual(len(FIELDS), 36)

    def test_parser_accepts_fixed_schema(self) -> None:
        values1 = ["1700000000000", "1", "2", "0.5", "1.5"] + [str(i) for i in range(36)]
        values2 = ["1700086400000", "1.5", "2.5", "1", "2"] + [str(i + 100) for i in range(36)]
        text = "noise\nINFO D1B|" + "|".join(values1) + "\nother D1B|" + "|".join(values2) + "\n"
        frame = parse_text(text)
        self.assertEqual(list(frame.columns), COLUMNS)
        self.assertEqual(len(frame), 2)
        self.assertEqual(frame.iloc[0]["close"], 1.5)
        self.assertEqual(frame.iloc[1]["PARITY formal_id"], 133.0)


if __name__ == "__main__":
    unittest.main()
