from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from compare_issue66_phase_d1_tradingview_parity import (  # noqa: E402
    PERCENT_GATE_FIELDS,
    TV_TO_PY,
    compare,
    compute_c2,
)
from test_price_only_core import synthetic_ohlc  # noqa: E402


class Issue66PhaseD1TradingViewParityTests(unittest.TestCase):
    def _export(self, damage_formal: bool = False):
        source = synthetic_ohlc(1900)
        py = compute_c2(source)
        exported = source.copy()
        for tv_name, py_name in TV_TO_PY.items():
            values = py[py_name].to_numpy(copy=True)
            if py_name in PERCENT_GATE_FIELDS:
                values = values * 100.0
            if damage_formal and py_name == "formal_id":
                finite = np.flatnonzero(np.isfinite(values))
                values[finite[-50:]] = (values[finite[-50:]] + 1) % 7
            exported[f"ChaseRisk #66 C2 Parity: {tv_name}"] = values
        return exported

    def test_identical_c2_export_passes(self) -> None:
        exported = self._export()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tv.csv"
            exported.to_csv(path, index=False)
            report = compare(path)

        self.assertTrue(report["acceptance"]["pass"], json.dumps(report["acceptance"], indent=2))
        self.assertEqual(report["reference"], "accepted C-2 price-only Python core")
        self.assertAlmostEqual(report["comparisons"]["formal_id"]["agreement_rate"], 1.0)
        # CSV decimal serialization introduces tiny (~1e-12) round-trip noise.
        # This is a unit-test tolerance only; the preregistered runtime gate stays P99 <= 0.50 points.
        self.assertLessEqual(report["comparisons"]["prob_markup"]["max_abs_error"], 1e-10)
        self.assertAlmostEqual(report["comparisons"]["stale_pressure_reason"]["agreement_rate"], 1.0)

    def test_formal_damage_fails_preregistered_gate(self) -> None:
        exported = self._export(damage_formal=True)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tv.csv"
            exported.to_csv(path, index=False)
            report = compare(path)

        self.assertFalse(report["acceptance"]["formal_stage_agreement_at_least_99_5pct"])
        self.assertFalse(report["acceptance"]["pass"])


if __name__ == "__main__":
    unittest.main()
