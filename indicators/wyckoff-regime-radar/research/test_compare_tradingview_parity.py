from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from compare_tradingview_parity import TV_TO_PY, compare  # noqa: E402
from price_only_core import compute_price_only  # noqa: E402
from test_price_only_core import synthetic_ohlc  # noqa: E402


class TradingViewParityComparatorTests(unittest.TestCase):
    def test_identical_engine_export_passes(self) -> None:
        source = synthetic_ohlc(1900)
        py = compute_price_only(source)
        exported = source.copy()
        for tv_name, py_name in TV_TO_PY.items():
            values = py[py_name].to_numpy(copy=True)
            if py_name in {
                "acc_gate",
                "markup_gate",
                "reacc_gate",
                "dist_gate",
                "markdown_gate",
                "redist_gate",
            }:
                values = values * 100.0
            # TradingView exports often prefix indicator names; verify fuzzy suffix matching.
            exported[f"ChaseRisk #55 Parity: {tv_name}"] = values

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tv.csv"
            exported.to_csv(path, index=False)
            report = compare(path)

        self.assertTrue(report["acceptance"]["pass"], json.dumps(report["acceptance"], indent=2))
        self.assertAlmostEqual(report["comparisons"]["formal_id"]["agreement_rate"], 1.0)
        self.assertLessEqual(report["comparisons"]["prob_markup"]["max_abs_error"], 1e-12)

    def test_formal_state_damage_fails_gate(self) -> None:
        source = synthetic_ohlc(1900)
        py = compute_price_only(source)
        exported = source.copy()
        for tv_name, py_name in TV_TO_PY.items():
            values = py[py_name].to_numpy(copy=True)
            if py_name in {
                "acc_gate",
                "markup_gate",
                "reacc_gate",
                "dist_gate",
                "markdown_gate",
                "redist_gate",
            }:
                values = values * 100.0
            if py_name == "formal_id":
                finite = np.flatnonzero(np.isfinite(values))
                values[finite[-50:]] = (values[finite[-50:]] + 1) % 7
            exported[tv_name] = values

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tv.csv"
            exported.to_csv(path, index=False)
            report = compare(path)

        self.assertFalse(report["acceptance"]["formal_stage_agreement_at_least_99_5pct"])
        self.assertFalse(report["acceptance"]["pass"])


if __name__ == "__main__":
    unittest.main()
