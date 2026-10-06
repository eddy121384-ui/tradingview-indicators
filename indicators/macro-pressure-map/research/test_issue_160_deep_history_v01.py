#!/usr/bin/env python3
"""Issue #160 — frozen unit tests for Deep-History v0.1 (pure stdlib).

Every expectation below is either an exact analytic value, a structural
property of the preregistered formulas, or a synthetic end-to-end check with
a perfect-agreement control. No TradingView data, no network, no outcomes.

Run:  python -m unittest -v test_issue_160_deep_history_v01
"""

import math
import unittest

import issue_160_deep_history_v01 as dh


def synth_raw(n=200, start_y=2007, start_m=1):
    """Deterministic wiggly monthly panel for all 11 source tickers.

    Two multiplicative dips guarantee deep joint troughs (hence R7 months
    and axis turns) in long panels; DH-vs-V66 agreement properties are
    unaffected because both sides use identical series.
    """
    months = []
    y, m = start_y, start_m
    for _ in range(n):
        months.append(f"{y:04d}-{m:02d}-01")
        m += 1
        if m > 12:
            m, y = 1, y + 1
    raw = {}
    for t in (dh.T_G1, dh.T_G2, dh.T_BP, dh.T_DPI, dh.T_PCEPI, dh.T_G5,
              dh.T_I1, dh.T_I2, dh.T_I3, dh.T_I4, dh.T_I5):
        seed = sum(ord(c) for c in t)
        pts = []
        for i, mo in enumerate(months):
            v = 100.0 + 20.0 * math.sin(i / 5.0 + seed) + 8.0 * math.sin(i / 13.0)
            v *= (1.0 - 0.45 * math.exp(-((i - 150) / 8.0) ** 2)
                      - 0.35 * math.exp(-((i - 300) / 10.0) ** 2))
            pts.append(f"{mo}:{v:.6f}")
        raw[t] = {"desc": t, "unit": "X", "count": n, "data": ",".join(pts)}
    return raw


class TestFrozenConstants(unittest.TestCase):
    def test_lookbacks_and_weights(self):
        self.assertEqual(dh.LOOKBACK, 60)
        self.assertEqual((dh.SMA_FAST, dh.SMA_SLOW), (3, 12))
        self.assertEqual((dh.W_LEVEL, dh.W_MOM, dh.W_DIR), (0.5, 0.3, 0.2))
        self.assertEqual((dh.STATE_LO, dh.STATE_HI), (-10.0, 10.0))

    def test_tickers(self):
        self.assertEqual(dh.T_G1, "ECONOMICS:USIPYY")
        self.assertEqual(dh.T_G2, "ECONOMICS:USUR")
        self.assertEqual(dh.T_BP, "ECONOMICS:USBP")
        self.assertEqual(dh.T_DPI, "ECONOMICS:USDPI")
        self.assertEqual(dh.T_PCEPI, "ECONOMICS:USPCEPI")
        self.assertEqual(dh.T_G5, "ECONOMICS:USMNO")
        self.assertEqual(dh.T_I1, "ECONOMICS:USIRYY")
        self.assertEqual(dh.T_I2, "ECONOMICS:USCPCEPIAC")
        self.assertEqual(dh.T_I3, "ECONOMICS:USPPIYY")
        self.assertEqual(dh.T_I4, "ECONOMICS:USWG")
        self.assertEqual(dh.T_I5, "ECONOMICS:USEI")

    def test_snapshot_and_r7(self):
        self.assertEqual(dh.SNAPSHOT_SHA256,
                         "1d03923503e7fe82a69b033897484c48aa646279ecf70164d090ed62a5a70719")
        self.assertEqual(dh.R7_LABEL, "Slowdown / Disinflation")
        self.assertEqual(dh.EXACT_WINDOW_START, "2007-01-01")


class TestPrimitives(unittest.TestCase):
    def test_mean_sd_biased(self):
        mean, sd = dh.mean_sd_biased([1.0, 2.0, 3.0])
        self.assertAlmostEqual(mean, 2.0, places=12)
        self.assertAlmostEqual(sd, math.sqrt(2.0 / 3.0), places=12)

    def test_axis_state_boundaries(self):
        self.assertEqual(dh.axis_state(-10.0001), -1)
        self.assertEqual(dh.axis_state(-10.0), 0)
        self.assertEqual(dh.axis_state(0.0), 0)
        self.assertEqual(dh.axis_state(10.0), 0)
        self.assertEqual(dh.axis_state(10.0001), 1)

    def test_core_regime_r7_cell(self):
        self.assertEqual(dh.core_regime(-10.1, -10.1), dh.R7_LABEL)
        # Exact -10 boundary is neutral, hence NOT R7:
        self.assertEqual(dh.core_regime(-10.0, -10.0), "Neutral / Range-bound Macro")
        self.assertEqual(dh.core_regime(11.0, -11.0), "Goldilocks / Disinflationary Expansion")
        self.assertEqual(dh.core_regime(-11.0, 11.0), "Stagflation Pressure")

    def test_axis_turns(self):
        self.assertEqual(dh.axis_turns([5, 4, 3, 2, 3, 4]),
                         [False, False, False, False, True, False])
        # Equal-prev (<= 0) still turns:
        self.assertTrue(dh.axis_turns([0, 0, 1])[2])
        # NaN-safe:
        self.assertEqual(dh.axis_turns([1, float("nan"), 2, 3]),
                         [False, False, False, False])

    def test_direction_agreement_zero_handling(self):
        self.assertEqual(dh.direction_agreement([1, 1, 2], [1, 1, 2]), 1.0)
        self.assertEqual(dh.direction_agreement([1, 2, 1], [1, 1, 1]), 0.0)


class TestPressureScore(unittest.TestCase):
    def test_constant_series_is_nan(self):
        self.assertTrue(all(math.isnan(v) for v in dh.pressure_score([5.0] * 70)))

    def test_too_short_is_nan(self):
        self.assertTrue(all(math.isnan(v) for v in dh.pressure_score([float(i) for i in range(10)])))

    def test_sawtooth_antisymmetry(self):
        # Integer-analytic case: lookback=2, fast=1, slow=2.
        # i=4: lz=-1, mz=-1, dir=tanh(-1) -> score in (-44.5,-44.0);
        # i=5: mirror image -> score in (44.0,44.5); earlier points lack
        # sufficient momentum history and stay NaN.
        xs = [0.0, 10.0, 0.0, 10.0, 0.0, 10.0]
        s = dh.pressure_score(xs, lookback=2, sma_fast=1, sma_slow=2)
        self.assertTrue(all(math.isnan(v) for v in s[:4]))
        self.assertGreater(s[4], -44.5)
        self.assertLess(s[4], -44.0)
        self.assertGreater(s[5], 44.0)
        self.assertLess(s[5], 44.5)

    def test_score_bounds_and_finiteness(self):
        import random
        rng = random.Random(7)
        xs = [rng.uniform(-5, 5) for _ in range(80)]
        s = dh.pressure_score(xs, lookback=20, sma_fast=3, sma_slow=6)
        fin = [v for v in s if not math.isnan(v)]
        self.assertGreater(len(fin), 10)
        for v in fin:
            self.assertGreaterEqual(v, -100.0)
            self.assertLessEqual(v, 100.0)


class TestBuild(unittest.TestCase):
    def test_g2_inversion_wiring(self):
        raw = synth_raw(n=90)
        months, X = dh.build_roles(raw)
        plain = dh.pressure_score(X["G2"])
        rows = dh.build_monthly(raw)
        self.assertTrue(any(not math.isnan(v) for v in plain))
        for (mo, G, I, g, f), p in zip(rows, plain):
            if math.isnan(p):
                self.assertTrue(math.isnan(g[1]))
            else:
                self.assertAlmostEqual(g[1], -p, places=9)

    def test_composite_requires_all_finite(self):
        raw = synth_raw(n=90)
        rows = dh.build_monthly(raw)
        for mo, G, I, g, f in rows:
            if math.isnan(G):
                self.assertTrue(any(math.isnan(v) for v in g))
            else:
                self.assertTrue(all(not math.isnan(v) for v in g))
            if math.isnan(I):
                self.assertTrue(any(math.isnan(v) for v in f))

    def test_gap_month_is_nan(self):
        raw = synth_raw(n=90)
        # Remove one in-sample month entirely from the unemployment series.
        pts = raw[dh.T_G2]["data"].split(",")
        removed = pts[80].split(":")[0]
        del pts[80]
        raw[dh.T_G2]["data"] = ",".join(pts)
        raw[dh.T_G2]["count"] = len(pts)
        rows = dh.build_monthly(raw)
        missing = [r[0] for r in rows if math.isnan(r[1])]
        self.assertIn(removed, missing)
        self.assertGreaterEqual(len(missing), 2)  # hole + momentum neighbors


class TestTriggers(unittest.TestCase):
    def test_first_trigger_per_episode(self):
        gv = [0, 0, 0, -2, -1, 0, 5, 5, 5, -3, -2, -1]
        grid = [{"date": f"2020-{i + 1:02d}-01", "g": float(v), "i": float(v),
                 "r7": (3 <= i <= 5) or (9 <= i <= 10)}
                for i, v in enumerate(gv)]
        # Turns (both axes) at idx 4 and idx 10 only; first trigger of each
        # episode wins even though later episode months also satisfy the window.
        self.assertEqual(dh.first_triggers(grid), ["2020-05-01", "2020-11-01"])

    def test_greedy_match(self):
        matched, med = dh.greedy_match(["2020-01-15", "2020-04-15"], ["2020-02-15", "2020-09-15"])
        self.assertEqual((matched, med), (1, 1.0))
        matched, med = dh.greedy_match(["2020-01-15"], [])
        self.assertEqual(matched, 0)
        self.assertTrue(math.isnan(med))


class TestEndToEnd(unittest.TestCase):
    def _panel(self, transform=None):
        raw = synth_raw(n=440, start_y=1995, start_m=1)
        rows = dh.build_monthly(raw)
        dh_rows = [(mo, G, I) for mo, G, I, _, _ in rows]
        snap = []
        for mo, G, I, _, _ in rows:
            y, m = int(mo[:4]), int(mo[5:7])
            last = 28 if m == 2 else (30 if m in (4, 6, 9, 11) else 31)
            GG, II = (G, I) if transform is None else transform(G, I)
            if math.isnan(GG) or math.isnan(II):
                regime = 1
            else:
                regime = 7 if dh.core_regime(GG, II) == dh.R7_LABEL else 1
            snap.append({"date": f"{y:04d}-{m:02d}-{last:02d}",
                         "gpi": GG, "ipi": II, "regime": regime})
        return dh_rows, [s for s in snap if s["date"] >= "2007-01-01"
                         and not (math.isnan(s["gpi"]) or math.isnan(s["ipi"]))]

    def test_perfect_agreement_passes_all_gates(self):
        dh_rows, snap = self._panel()
        ov, m, v_trig, d_trig = dh.evaluate_overlap(dh_rows, snap)
        self.assertGreaterEqual(m["n"], 180)
        self.assertGreater(m["r7_ref_n"], 0)
        self.assertTrue(all(m["gates"]), m["gates"])
        self.assertEqual(m["verdict"], "deep_history_v01_overlap_passed")

    def test_inverted_axes_fail(self):
        dh_rows, snap = self._panel(transform=lambda G, I: (-G, -I))
        ov, m, v_trig, d_trig = dh.evaluate_overlap(dh_rows, snap)
        self.assertGreaterEqual(m["n"], 180)
        self.assertEqual(m["verdict"], "deep_history_v01_overlap_failed")


if __name__ == "__main__":
    unittest.main()
