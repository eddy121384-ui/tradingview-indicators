#!/usr/bin/env python3
"""#189 independent Phase 1C: run the ACTUAL frozen #160 Python implementation.
No market-return files or network reads. Synthetic macro observations only.
Run: python3 -m unittest indicators/macro-pressure-map/research/test_issue_189_gpt6_phase1c.py
(Or cd indicators/macro-pressure-map/research && python3 -m unittest test_issue_189_gpt6_phase1c.py)
"""
from __future__ import annotations

import importlib.util
import math
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent
SOURCE = ROOT / "issue_160_deep_history_v01.py"
spec = importlib.util.spec_from_file_location("dh160_immutable_for_189_gpt6", SOURCE)
assert spec is not None and spec.loader is not None
frozen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(frozen)

SYMBOLS = [
    frozen.T_G1, frozen.T_G2, frozen.T_BP, frozen.T_DPI, frozen.T_PCEPI,
    frozen.T_G5, frozen.T_I1, frozen.T_I2, frozen.T_I3, frozen.T_I4, frozen.T_I5,
]


def ymonth(k: int, anchor_year: int = 1960, anchor_month: int = 1) -> str:
    y, m = divmod(anchor_year * 12 + (anchor_month - 1) + k, 12)
    return f"{y:04d}-{m + 1:02d}-01"


def synthetic(n: int, revision: bool = False) -> dict:
    """All 11 positive, varying macro series, without market/return inputs."""
    data = {}
    for j, ticker in enumerate(SYMBOLS):
        vals = []
        for k in range(n):
            # Preserve nonzero denominators and nondegenerate SD.
            if ticker == frozen.T_BP:
                v = 1600 + 4*k + 30*math.sin(.23*k) + 11*math.cos(.09*k)
            elif ticker == frozen.T_DPI:
                v = 3600 + 9*k + 18*math.sin(.19*k) + 7*math.cos(.13*k)
            elif ticker == frozen.T_PCEPI:
                v = 90 + .3*k + 1.1*math.sin(.16*k)
            else:
                v = 100 + 3*j + .12*k + 2.5*math.sin(k*(.13 + .011*j))
            if revision and k == 0 and ticker in (frozen.T_BP, frozen.T_DPI):
                v += 95
            vals.append(f"{ymonth(k)}:{v:.12f}")
        data[ticker] = {"data": ",".join(vals)}
    return data


def first_finite(xs: list) -> int | None:
    return next((i for i, v in enumerate(xs) if frozen.is_fin(v)), None)


class Phase1CTrueWarmup(unittest.TestCase):
    def test_constants_match_frozen_contract(self):
        self.assertEqual(frozen.LOOKBACK, 60)
        self.assertEqual(frozen.SMA_FAST, 3)
        self.assertEqual(frozen.SMA_SLOW, 12)

    def test_74_raw_months_are_insufficient_and_75_suffice(self):
        # G3/G4 YoY needs raw[t-12]; first valid momentum needs derived[t-3];
        # 60 valid momentum observations => t >= 12+3+(60-1) == 74.
        for n, expected in [(74, None), (75, 74), (76, 74)]:
            raw = synthetic(n)
            months, roles = frozen.build_roles(raw)
            self.assertEqual(len(months), n)
            for role in ("G3", "G4"):
                score = frozen.pressure_score(roles[role])
                self.assertEqual(first_finite(score), expected, (role, n))
            monthly = frozen.build_monthly(raw)
            g_first = next((i for i, row in enumerate(monthly)
                            if frozen.is_fin(row[1])), None)
            self.assertEqual(g_first, expected, n)
        self.assertEqual(ymonth(74), "1966-03-01")

    def test_vintage_history_revision_propagates_into_score(self):
        before = synthetic(75, revision=False)
        after = synthetic(75, revision=True)
        _, x1 = frozen.build_roles(before)
        _, x2 = frozen.build_roles(after)
        for role in ("G3", "G4"):
            a = frozen.pressure_score(x1[role])[74]
            b = frozen.pressure_score(x2[role])[74]
            self.assertTrue(math.isfinite(a) and math.isfinite(b))
            self.assertGreater(abs(a-b), 1e-8, role)

    def test_2006_reference_vs_asof_lag_oldest_raw_period(self):
        # This is an observation-reference-month bound, NOT a vintage-availability proof.
        self.assertEqual(frozen.shift_month("2006-06-01", -74), "2000-04-01")
        self.assertEqual(frozen.shift_month("2006-05-01", -74), "2000-03-01")
        self.assertEqual(frozen.shift_month("2006-04-01", -74), "2000-02-01")


if __name__ == "__main__":
    unittest.main()
