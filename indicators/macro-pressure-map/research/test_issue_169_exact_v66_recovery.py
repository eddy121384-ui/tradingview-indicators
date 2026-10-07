#!/usr/bin/env python3
"""Issue #169 — frozen unit tests for exact-V6.6 recovery translation (pure stdlib).

All expectations are analytic, structural, or synthetic end-to-end panels with
forced outcomes (the all-green panel mirrors a Node-verified construction:
identical signal payoffs above every possible control payoff, so all gates
are deterministic). No TradingView data, no network, no asset outcomes.

Run:  python -m unittest -v test_issue_169_exact_v66_recovery
"""

import math
import unittest

import issue_169_exact_v66_recovery as ev


def months(a, b):
    out, mo = [], a
    while mo <= b:
        out.append(mo)
        y, m = int(mo[:4]), int(mo[5:7]) + 1
        if m > 12:
            m, y = 1, y + 1
        mo = f"{y:04d}-{m:02d}-01"
    return out


def eom(mo):
    import calendar
    return f"{mo[:7]}-{calendar.monthrange(int(mo[:4]), int(mo[5:7]))[1]:02d}"


class TestRNG(unittest.TestCase):
    def test_vectors(self):
        g = ev.mulberry32(169)
        for want in (0.31359018199145794, 0.077723853290081024, 0.61011338210664690,
                     0.11753928987309337, 0.84225041815079749):
            self.assertAlmostEqual(g(), want, places=12)

    def test_determinism_and_range(self):
        a, b = ev.mulberry32(169), ev.mulberry32(169)
        seq_a = [a() for _ in range(50)]
        self.assertEqual(seq_a, [b() for _ in range(50)])
        self.assertTrue(all(0.0 <= x < 1.0 for x in seq_a))
        self.assertNotEqual(seq_a, [ev.mulberry32(170)() for _ in range(50)])


class TestStateAndTriggers(unittest.TestCase):
    def test_primary_inclusive_and_deep_strict(self):
        snap = [
            {"date": "2000-01-31", "gpi": 10.0, "ipi": 10.0, "regime": 1},
            {"date": "2000-02-29", "gpi": 10.0001, "ipi": 0.0, "regime": 1},
            {"date": "2000-03-31", "gpi": -10.0, "ipi": -10.0, "regime": 7},
            {"date": "2000-04-30", "gpi": -10.0001, "ipi": -10.0001, "regime": 7},
        ]
        st = ev.build_states(snap)
        self.assertTrue(st[0]["elig"])   # +10 inclusive
        self.assertFalse(st[1]["elig"])  # just above +10
        self.assertTrue(st[2]["elig"])
        self.assertFalse(st[2]["gpi"] < -10.0 and st[2]["ipi"] < -10.0)  # -10 not deep
        self.assertTrue(st[3]["gpi"] < -10.0 and st[3]["ipi"] < -10.0)   # strictly below is deep

    def test_d3_strict_and_joint(self):
        snap = [{"date": eom(m), "gpi": 0.0, "ipi": 0.0, "regime": 1}
                for m in months("2000-01-01", "2000-08-01")]
        snap[5]["gpi"] = 5.0  # d3G > 0 but d3I == 0 -> no joint trigger
        st = ev.build_states(snap)
        self.assertEqual(ev.build_triggers(st, ev.build_episodes(st)), [])
        snap[5]["ipi"] = 5.0
        st = ev.build_states(snap)
        trg = ev.build_triggers(st, ev.build_episodes(st))
        self.assertEqual(len(trg), 1)
        self.assertEqual(trg[0]["date"], "2000-06-30")

    def test_controls_exclude_post_trigger(self):
        snap = [{"date": eom(m), "gpi": -5.0, "ipi": -5.0, "regime": 7}
                for m in months("2000-01-01", "2000-06-01")]
        snap[3]["gpi"] = 0.0
        snap[3]["ipi"] = 0.0
        st = ev.build_states(snap)
        eps = ev.build_episodes(st)
        trg = ev.build_triggers(st, eps)
        sig, ctl = ev.build_obs(st, eps, trg)
        self.assertEqual([s["date"] for s in sig], ["2000-04-30"])
        self.assertEqual([c["date"] for c in ctl],
                         ["2000-01-31", "2000-02-29", "2000-03-31"])
        # 2000-05/06 (post-trigger) are neither signal nor control

    def test_severity_split(self):
        # isolated 4-month runs separated by 3-month +20 gaps (d3 isolation):
        # deep run idx1-4 (-30 x3, lift to -15 at idx4); mild run idx8-11
        # (-5 x3, lift to 0.0 at idx11); baseline +20 elsewhere.
        snap = [{"date": eom(m), "gpi": 20.0, "ipi": 20.0, "regime": 1}
                for m in months("2000-01-01", "2000-12-01")]
        all_mos = months("2000-01-01", "2000-12-01")
        for m in ("2000-02-01", "2000-03-01", "2000-04-01"):
            i = all_mos.index(m)
            snap[i]["gpi"] = -30.0
            snap[i]["ipi"] = -30.0
        i = all_mos.index("2000-05-01")
        snap[i]["gpi"] = -15.0
        snap[i]["ipi"] = -15.0
        for m in ("2000-09-01", "2000-10-01", "2000-11-01"):
            i = all_mos.index(m)
            snap[i]["gpi"] = -5.0
            snap[i]["ipi"] = -5.0
        i = all_mos.index("2000-12-01")
        snap[i]["gpi"] = 0.0
        snap[i]["ipi"] = 0.0
        st = ev.build_states(snap)
        eps = ev.build_episodes(st)
        trg = ev.build_triggers(st, eps)
        self.assertEqual(len(trg), 2)
        by_date = {t["date"]: t for t in trg}
        self.assertTrue(by_date["2000-05-31"]["deep"])
        self.assertFalse(by_date["2000-05-31"]["mild"])
        self.assertTrue(by_date["2000-12-31"]["mild"])
        self.assertFalse(by_date["2000-12-31"]["deep"])


class TestPayoff(unittest.TestCase):
    def test_compounding_and_delay(self):
        snap = [{"date": eom(m), "gpi": 0.0, "ipi": 0.0, "regime": 1}
                for m in months("2000-01-01", "2000-12-01")]
        eq = {m: 0.0 for m in months("2000-01-01", "2001-06-01")}
        ty = {m: 0.0 for m in months("2000-01-01", "2001-06-01")}
        for m in ("2000-03-01", "2000-04-01", "2000-05-01"):
            eq[m] = 0.10
            ty[m] = 0.01
        p = ev.payoff_for(snap, eq, ty, 0, 2, 3)  # Jan t -> Mar/Apr/May
        self.assertAlmostEqual(p["eq"], 1.1 ** 3 - 1, places=12)
        self.assertAlmostEqual(p["ty"], 1.01 ** 3 - 1, places=12)
        self.assertAlmostEqual(p["spread"], p["eq"] - p["ty"], places=12)

    def test_incomplete_window_is_none(self):
        snap = [{"date": eom(m), "gpi": 0.0, "ipi": 0.0, "regime": 1}
                for m in months("2000-01-01", "2000-04-01")]
        eq = {m: 0.01 for m in months("2000-01-01", "2000-05-01")}
        del eq["2000-04-01"]
        ty = {m: 0.01 for m in months("2000-01-01", "2000-06-01")}
        self.assertIsNone(ev.payoff_for(snap, eq, ty, 0, 2, 3))

    def test_era_assignment(self):
        self.assertEqual(ev.era_of("2019-12-31"), "pre-2020")
        self.assertEqual(ev.era_of("2020-01-31"), "2020-2022")
        self.assertEqual(ev.era_of("2022-12-31"), "2020-2022")
        self.assertEqual(ev.era_of("2023-01-31"), "2023+")

    def test_loo_single_episode_not_evaluable(self):
        snap = [{"date": eom(m), "gpi": -5.0, "ipi": -5.0, "regime": 7}
                for m in months("2000-01-01", "2000-06-01")]
        snap[3]["gpi"] = 0.0
        snap[3]["ipi"] = 0.0
        eq = {m: 0.02 for m in months("2000-01-01", "2001-01-01")}
        ty = {m: 0.0 for m in months("2000-01-01", "2001-01-01")}
        res = ev.evaluate(snap, eq, ty)
        self.assertEqual(len(res["triggers"]), 1)
        # dropping the only trigger episode leaves no signals -> not evaluable
        self.assertFalse(res["loo"][0]["evaluable"])


def episodic_panel(trig_starts, never_starts, boost):
    """Isolated 4-month eligible runs on a +20 baseline (d3 isolation).

    Each trigger run: months s..s+3 eligible at -5 with a lift to 0.0 at s+3,
    so exactly s+3 qualifies (d3 = +5 against the run base). Run starts are
    >= 12 months apart, so no d3 window reaches across runs. boost: monthly
    equity return written over each trigger window (t+2..t+4). Treasury is
    always 0. Returns span 1990-01..2032-12.
    """
    mos = months("1990-01-01", "2032-12-01")
    G = {m: 20.0 for m in mos}
    I = {m: 20.0 for m in mos}
    for s in trig_starts + never_starts:
        for k in range(4):
            G[ev.shift_month(s, k)] = -5.0
            I[ev.shift_month(s, k)] = -5.0
    for s in trig_starts:
        t = ev.shift_month(s, 3)
        G[t] = 0.0
        I[t] = 0.0
    eq = {m: 0.0 for m in mos}
    ty = {m: 0.0 for m in mos}
    for s in trig_starts:
        t = ev.shift_month(s, 3)
        for k in (2, 3, 4):
            eq[ev.shift_month(t, k)] = boost
    snap = [{"date": eom(m), "gpi": G[m], "ipi": I[m], "regime": 1} for m in mos]
    return snap, eq, ty


TRIG12 = ["1995-03-01", "2000-03-01", "2005-03-01", "2010-03-01", "2015-03-01",
          "2018-03-01", "2020-03-01", "2021-03-01", "2022-03-01", "2023-03-01",
          "2024-03-01", "2025-03-01"]


class TestVerdicts(unittest.TestCase):
    def test_supported(self):
        snap, eq, ty = episodic_panel(TRIG12, ["1996-01-01"], 0.015)
        res = ev.evaluate(snap, eq, ty)
        self.assertEqual(len(res["triggers"]), 12)
        self.assertTrue(all(res["gates"]), res["gates"])
        self.assertEqual(res["verdict"], "exact_v66_recovery_translation_supported")

    def test_inconclusive(self):
        snap, eq, ty = episodic_panel(TRIG12[:3], [], 0.015)
        res = ev.evaluate(snap, eq, ty)
        self.assertLess(len(res["triggers"]), 8)
        self.assertEqual(res["verdict"],
                         "exact_v66_recovery_translation_inconclusive_sample")

    def test_not_supported(self):
        snap, eq, ty = episodic_panel(TRIG12[:8], [], -0.01)
        res = ev.evaluate(snap, eq, ty)
        self.assertGreaterEqual(len(res["triggers"]), 8)
        self.assertEqual(res["verdict"],
                         "exact_v66_recovery_translation_not_supported")

    def test_suggestive(self):
        # positive direction, one dominant trigger -> concentration fails
        snap, eq, ty = episodic_panel(TRIG12[:8], [], 0.002)
        t0 = ev.shift_month(TRIG12[0], 3)
        for k in (2, 3, 4):
            eq[ev.shift_month(t0, k)] = 0.15
        res = ev.evaluate(snap, eq, ty)
        self.assertGreaterEqual(len(res["triggers"]), 8)
        self.assertTrue(res["gates"][1] and res["gates"][2])
        self.assertFalse(res["gates"][7])
        self.assertEqual(res["verdict"],
                         "exact_v66_recovery_translation_directionally_consistent_not_robust")


if __name__ == "__main__":
    unittest.main()
