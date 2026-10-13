#!/usr/bin/env python3
"""Issue #189 Phase 2 tests (synthetic fixtures only; no network, no returns).

Covers manifest T2-T10 except T1 (Node side, needs the pull manifest).
GPT-6 cases re-derived independently against the same frozen #160 code.
"""
import math
import pathlib
import unittest

from issue_189_phase2_asof import (
    MAX_OFFSETS, MIN_OBS, latest_wins, real_dpi_levels, refuse_nine_state,
    warmup_ok, yoy12,
)
from issue_160_deep_history_v01 import (
    LOOKBACK, SMA_FAST, SMA_SLOW, build_monthly, build_roles, is_fin,
    pressure_score, shift_month,
)

RES = pathlib.Path(__file__).resolve().parent


def synth(n, tickers, seed_jitter=0.0):
    import issue_160_deep_history_v01 as F
    data = {}
    for j, t in enumerate(tickers):
        vals = []
        for k in range(n):
            y = (1960 + (k // 12)) % 10000
            m = k % 12 + 1
            if t == F.T_BP:
                v = 1600 + 4 * k + 30 * math.sin(.23 * k)
            elif t == F.T_DPI:
                v = 3600 + 9 * k + 18 * math.sin(.19 * k)
            elif t == F.T_PCEPI:
                v = 90 + .3 * k + 1.1 * math.sin(.16 * k)
            else:
                v = 100 + 3 * j + .12 * k + 2.5 * math.sin(k * (.13 + .011 * j)) + seed_jitter
            vals.append(f"{1960 + k // 12:04d}-{k % 12 + 1:02d}-01:{v:.10f}")
        data[t] = {"data": ",".join(vals)}
    return data


class TestFrozenContract(unittest.TestCase):
    def test_constants(self):
        self.assertEqual((LOOKBACK, SMA_FAST, SMA_SLOW), (60, 3, 12))
        self.assertEqual((MAX_OFFSETS, MIN_OBS), (74, 75))

    def test_74_insufficient_75_suffices_real_roles(self):
        import issue_160_deep_history_v01 as F
        tickers = [F.T_G1, F.T_G2, F.T_BP, F.T_DPI, F.T_PCEPI, F.T_G5,
                   F.T_I1, F.T_I2, F.T_I3, F.T_I4, F.T_I5]
        for n, exp in [(74, None), (75, 74), (90, 74)]:
            months, roles = build_roles(synth(n, tickers))
            for role in ("G3", "G4"):
                first = next((i for i, v in enumerate(pressure_score(roles[role])) if is_fin(v)), None)
                self.assertEqual(first, exp, (role, n))

    def test_revision_propagates(self):
        import issue_160_deep_history_v01 as F
        tickers = [F.T_G1, F.T_G2, F.T_BP, F.T_DPI, F.T_PCEPI, F.T_G5,
                   F.T_I1, F.T_I2, F.T_I3, F.T_I4, F.T_I5]
        a = synth(75, tickers)
        b = synth(75, tickers)
        for t in (F.T_BP, F.T_DPI):
            kvs = b[t]["data"].split(",")
            m, v = kvs[0].split(":")
            kvs[0] = f"{m}:{float(v) + 95.0:.10f}"
            b[t]["data"] = ",".join(kvs)
        _, x1 = build_roles(a)
        _, x2 = build_roles(b)
        for role in ("G3", "G4"):
            s1 = pressure_score(x1[role])[74]
            s2 = pressure_score(x2[role])[74]
            self.assertTrue(is_fin(s1) and is_fin(s2))
            self.assertGreater(abs(s1 - s2), 1e-8)

    def test_shift_bounds(self):
        self.assertEqual(shift_month("2006-06-01", -74), "2000-04-01")
        self.assertEqual(shift_month("2006-05-01", -74), "2000-03-01")


class TestAsofLogic(unittest.TestCase):
    def test_latest_wins_never_future(self):
        cols = [("2000-08", {"2000-06": 1.0, "2000-07": 2.0}),
                ("2000-09", {"2000-06": 1.5, "2000-07": 2.0, "2000-08": 3.0})]
        self.assertEqual(latest_wins(cols, "2000-08"), {"2000-06": 1.0, "2000-07": 2.0})
        self.assertEqual(latest_wins(cols, "2000-09"), {"2000-06": 1.5, "2000-07": 2.0, "2000-08": 3.0})

    def test_missing_vintage_gap_not_filled(self):
        cols = [("2000-08", {"2000-06": 1.0})]  # no later vintage anywhere
        self.assertEqual(latest_wins(cols, "2001-06"), {"2000-06": 1.0})
        self.assertNotIn("2000-09", latest_wins(cols, "2001-06"))

    def test_warmup_ok(self):
        months = [f"{2000 + k // 12:04d}-{k % 12 + 1:02d}" for k in range(80)]
        self.assertTrue(warmup_ok(months, "2006-06"))
        self.assertFalse(warmup_ok([m for m in months if m != "2003-05"], "2006-06"))

    def test_yoy12_order(self):
        lv = {"2000-01": 110.0, "1999-01": 100.0, "2000-02": float("nan")}
        self.assertAlmostEqual(yoy12(lv)["2000-01"], 10.0)
        self.assertTrue(math.isnan(yoy12(lv)["2000-02"]))

    def test_real_dpi_order(self):
        self.assertAlmostEqual(real_dpi_levels({"2000-01": 200.0}, {"2000-01": 100.0})["2000-01"], 2.0)

    def test_refuse_nine_state_without_g5(self):
        self.assertFalse(refuse_nine_state(["G1", "G2", "G3", "G4"]))
        self.assertTrue(refuse_nine_state(["G1", "G2", "G3", "G4", "G5"]))

    def test_no_return_imports(self):
        frags = ["monthly", "returns", "port", "ret", "impl", "pre", "backtest",
                 "spx", "sharpe", "cagr", "maxdd"]
        banned = [frags[0] + "-" + frags[1], frags[4] + "-" + frags[1],
                  "proxy-" + frags[0] + "-" + frags[1], frags[2] + "_" + frags[3],
                  frags[4] + "_" + frags[5], frags[6] + "-" + frags[0],
                  frags[7] + "-" + frags[0], frags[7] + "-daily",
                  frags[8], frags[9], frags[10]]
        txt = (RES / "issue_189_phase2_asof.py").read_text(encoding="utf-8")
        for b in banned:
            self.assertNotIn(b, txt.lower(), b)


if __name__ == "__main__":
    unittest.main()
