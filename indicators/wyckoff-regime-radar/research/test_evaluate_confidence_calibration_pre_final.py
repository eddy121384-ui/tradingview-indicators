from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from evaluate_confidence_calibration_pre_final import (  # noqa: E402
    MIN_DEV_STATE_N,
    confidence_bin,
    development_cutpoints,
)


class ConfidenceCalibrationTests(unittest.TestCase):
    def test_development_cutpoints_require_minimum_sample(self) -> None:
        self.assertIsNone(development_cutpoints(np.arange(MIN_DEV_STATE_N - 1, dtype=float)))

    def test_development_cutpoints_are_ordered(self) -> None:
        cutpoints = development_cutpoints(np.arange(90, dtype=float))
        self.assertIsNotNone(cutpoints)
        low, high = cutpoints
        self.assertLess(low, high)

    def test_confidence_bin_respects_development_thresholds(self) -> None:
        self.assertEqual(confidence_bin(10.0, 20.0, 40.0), "low")
        self.assertEqual(confidence_bin(30.0, 20.0, 40.0), "medium")
        self.assertEqual(confidence_bin(50.0, 20.0, 40.0), "high")
        self.assertIsNone(confidence_bin(float("nan"), 20.0, 40.0))


if __name__ == "__main__":
    unittest.main()
