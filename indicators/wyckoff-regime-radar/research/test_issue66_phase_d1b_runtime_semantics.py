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

from compare_issue66_phase_d1_tradingview_parity import PERCENT_GATE_FIELDS, TV_TO_PY, compare, compute_c2  # noqa: E402
from pine_math import percentrank  # noqa: E402
from test_price_only_core import synthetic_ohlc  # noqa: E402


class Issue66PhaseD1BRuntimeSemanticsTests(unittest.TestCase):
    def test_percentrank_uses_previous_length_observations(self) -> None:
        values = np.array([1.0, 2.0, 3.0, 4.0, 0.0])
        ranks = percentrank(values, 3)
        self.assertTrue(np.isnan(ranks[0]))
        self.assertTrue(np.isnan(ranks[1]))
        self.assertTrue(np.isnan(ranks[2]))
        # 4 is above all three *previous* observations -> 100.
        self.assertAlmostEqual(ranks[3], 100.0)
        # 0 is below all three previous observations -> 0.
        self.assertAlmostEqual(ranks[4], 0.0)

    def _identical_export(self):
        source = synthetic_ohlc(1900)
        py = compute_c2(source)
        exported = source.copy()
        for tv_name, py_name in TV_TO_PY.items():
            values = py[py_name].to_numpy(copy=True)
            if py_name in PERCENT_GATE_FIELDS:
                values = values * 100.0
            exported[f"ChaseRisk #66 C2 Parity: {tv_name}"] = values
        return exported

    def test_acceptance_ignores_pre_warmup_id_rows(self) -> None:
        exported = self._identical_export()
        with tempfile.TemporaryDirectory() as tmp:
            clean_path = Path(tmp) / "clean.csv"
            exported.to_csv(clean_path, index=False)
            clean = compare(clean_path)
            first_common = clean["first_all_fields_comparable_row_index"]
            self.assertIsNotNone(first_common)
            self.assertGreater(first_common, 0)

            damaged = exported.copy()
            formal_column = next(column for column in damaged.columns if column.endswith("PARITY formal_id"))
            damaged.loc[: first_common - 1, formal_column] = 6
            damaged_path = Path(tmp) / "damaged_pre_warmup.csv"
            damaged.to_csv(damaged_path, index=False)
            report = compare(damaged_path)

        # Raw per-field diagnostics notice the pre-warmup mismatch, but the
        # preregistered runtime acceptance window remains fully comparable only.
        self.assertLess(report["comparisons"]["formal_id"]["agreement_rate"], 1.0)
        self.assertAlmostEqual(report["common_window_comparisons"]["formal_id"]["agreement_rate"], 1.0)
        self.assertTrue(report["acceptance"]["pass"], json.dumps(report["acceptance"], indent=2))


if __name__ == "__main__":
    unittest.main()
