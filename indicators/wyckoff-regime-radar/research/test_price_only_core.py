from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from pine_math import percentrank  # noqa: E402
from price_only_core import PriceOnlyConfig, compute_price_only  # noqa: E402


def synthetic_ohlc(rows: int = 1900) -> pd.DataFrame:
    x = np.arange(rows, dtype=float)
    # Multiple slow and fast cycles plus a weak drift create both trending and
    # ranging environments without introducing randomness into the tests.
    close = 1.10 + 0.000025 * x + 0.055 * np.sin(x / 53.0) + 0.012 * np.sin(x / 9.0)
    open_ = close + 0.0015 * np.sin(x / 4.0)
    spread = 0.004 + 0.0015 * (1.0 + np.sin(x / 17.0))
    high = np.maximum(open_, close) + spread
    low = np.minimum(open_, close) - spread
    return pd.DataFrame(
        {
            "date": pd.date_range("2010-01-01", periods=rows, freq="D"),
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
        }
    )


class PineMathTests(unittest.TestCase):
    def test_percentrank_maps_monotonic_extreme_to_100(self) -> None:
        values = np.arange(20, dtype=float)
        rank = percentrank(values, 10)
        self.assertAlmostEqual(rank[-1], 100.0)

    def test_percentrank_maps_window_low_to_zero(self) -> None:
        values = np.array([10, 11, 12, 13, 14, 15, 16, 17, 18, 1], dtype=float)
        rank = percentrank(values, 10)
        self.assertAlmostEqual(rank[-1], 0.0)


class PriceOnlyMirrorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.frame = synthetic_ohlc()
        cls.result = compute_price_only(cls.frame)

    def test_probability_weights_sum_to_100_when_available(self) -> None:
        columns = [
            "prob_acc",
            "prob_markup",
            "prob_reacc",
            "prob_dist",
            "prob_markdown",
            "prob_redist",
        ]
        probs = self.result[columns]
        valid = probs.notna().all(axis=1)
        self.assertGreater(int(valid.sum()), 100)
        totals = probs.loc[valid].sum(axis=1).to_numpy()
        np.testing.assert_allclose(totals, 100.0, atol=1e-9, rtol=0.0)

    def test_state_ids_stay_inside_frozen_contract(self) -> None:
        self.assertTrue(self.result["formal_id"].between(0, 6).all())
        self.assertTrue(self.result["candidate_display_id"].between(0, 6).all())
        self.assertTrue(self.result["top_id"].between(1, 6).all())

    def test_default_run_produces_nontrivial_formal_states(self) -> None:
        tail = self.result.loc[self.result["prob_acc"].notna(), "formal_id"]
        self.assertGreater(len(tail), 100)
        self.assertGreater(tail.nunique(), 1)

    def test_future_mutation_cannot_change_past_outputs(self) -> None:
        cutoff = 1650
        mutated = self.frame.copy()
        mutated.loc[cutoff:, "close"] *= 1.20
        mutated.loc[cutoff:, "open"] *= 1.20
        mutated.loc[cutoff:, "high"] *= 1.20
        mutated.loc[cutoff:, "low"] *= 1.20
        changed = compute_price_only(mutated)

        columns = [
            "prob_acc",
            "prob_markup",
            "prob_reacc",
            "prob_dist",
            "prob_markdown",
            "prob_redist",
            "top_gap",
            "evidence_strength",
            "formal_id",
        ]
        for column in columns:
            left = self.result.loc[: cutoff - 1, column].to_numpy()
            right = changed.loc[: cutoff - 1, column].to_numpy()
            if np.issubdtype(left.dtype, np.number):
                np.testing.assert_allclose(left, right, atol=0.0, rtol=0.0, equal_nan=True)
            else:
                self.assertEqual(left.tolist(), right.tolist())

    def test_price_only_output_does_not_depend_on_witness_columns(self) -> None:
        noisy = self.frame.copy()
        noisy["volume"] = np.linspace(1.0, 1_000_000.0, len(noisy))
        noisy["mtf_fake"] = np.sin(np.arange(len(noisy)))
        noisy["div_fake"] = np.cos(np.arange(len(noisy)))
        changed = compute_price_only(noisy)
        np.testing.assert_array_equal(self.result["formal_id"].to_numpy(), changed["formal_id"].to_numpy())


if __name__ == "__main__":
    unittest.main()
