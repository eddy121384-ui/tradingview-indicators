#!/usr/bin/env python3
"""Issue #171 — frozen unit tests for cross-layer divergence autopsy (pure stdlib).

All expectations are analytic, structural, or synthetic end-to-end panels with
forced outcomes. No TradingView data, no network, no asset outcomes (one
integration class reads frozen repo macro files only, skipped when absent).

Run:  python -m unittest -v test_issue_171_divergence_autopsy
"""

import math
import os
import unittest

import issue_171_divergence_autopsy as au


def months(a, b):
    out, mo = [], a
    while mo <= b:
        out.append(mo)
        y, m = int(mo[:4]), int(mo[5:7]) + 1
        if m > 12:
            m, y = 1, y + 1
        mo = f"{y:04d}-{m:02d}-01"
    return out


class TestStateAndD3(unittest.TestCase):
    def test_state_boundaries_inclusive(self):
        st, _, _ = au.build_layer(
            ["2000-01-01", "2000-02-01", "2000-03-01", "2000-04-01"],
            lambda m: 10.0, lambda m: 10.0)
        self.assertTrue(all(s["elig"] for s in st))
        st, _, _ = au.build_layer(
            ["2000-01-01", "2000-02-01"],
            lambda m: 10.0001, lambda m: 0.0)
        self.assertFalse(any(s["elig"] for s in st))

    def test_d3_positional_strict_and_nan(self):
        mos = months("2000-01-01", "2000-08-01")
        vals = {m: 0.0 for m in mos}
        vals["2000-06-01"] = 5.0
        st, _, _ = au.build_layer(mos, vals.get, vals.get)
        by_m = {s["m"]: s for s in st}
        # d3 at Jun = Jun - Mar = 5 - 0 > 0 ; at Jul = Jul - Apr = 0 - 0 = 0 (not >0)
        self.assertEqual(by_m["2000-06-01"]["d3G"], 5.0)
        self.assertTrue(by_m["2000-06-01"]["qual"])
        self.assertFalse(by_m["2000-07-01"]["qual"])
        # first three months have NaN d3
        for m in months("2000-01-01", "2000-03-01"):
            self.assertTrue(math.isnan(by_m[m]["d3G"]))

    def test_d3_missing_neighbor_is_nan(self):
        mos = months("2000-01-01", "2000-06-01")
        vals = {m: 1.0 for m in mos}
        del vals["2000-03-01"]
        st, _, _ = au.build_layer(mos, vals.get, vals.get)
        by_m = {s["m"]: s for s in st}
        # d3 at Jun needs Mar -> NaN; state still eligible
        self.assertTrue(math.isnan(by_m["2000-06-01"]["d3G"]))
        self.assertTrue(by_m["2000-06-01"]["elig"])
        self.assertFalse(by_m["2000-06-01"]["qual"])


class TestTriggersAndEpisodes(unittest.TestCase):
    def test_first_trigger_per_episode(self):
        # one 6-month eligible run, qualifying at months 4 and 6 -> only month 4 fires
        mos = months("2000-01-01", "2000-12-01")
        G = {m: 20.0 for m in mos}
        I = {m: 20.0 for m in mos}
        for m in months("2000-03-01", "2000-08-01"):
            G[m] = -5.0
            I[m] = -5.0
        G["2000-06-01"] = 0.0
        I["2000-06-01"] = 0.0
        G["2000-08-01"] = 0.0
        I["2000-08-01"] = 0.0
        _, eps, trg = au.build_layer(mos, G.get, I.get)
        self.assertEqual(len(eps), 1)
        self.assertEqual([t["date"] for t in trg], ["2000-06-01"])

    def test_gap_breaks_episode(self):
        mos = months("2000-01-01", "2000-06-01")
        G = {m: 0.0 for m in mos}
        G["2000-03-01"] = 99.0  # ineligible hole (cannot be NaN here; use high value)
        _, eps, _ = au.build_layer(mos, G.get, G.get)
        self.assertEqual(len(eps), 2)


class TestMatching(unittest.TestCase):
    def test_greedy_window_ties_and_reuse(self):
        dh = [{"date": d} for d in ("2000-01-01", "2000-06-01")]
        ex = [{"date": d} for d in ("2000-02-01", "2000-03-01", "2000-09-01")]
        matched, dh_only, ex_only = au.classify(dh, ex)
        # Jan-DH pairs Feb (|1| beats |2|); Jun-DH pairs Sep
        self.assertEqual([(m["dh"], m["exact"]) for m in matched],
                         [("2000-01-01", "2000-02-01"), ("2000-06-01", "2000-09-01")])
        self.assertEqual([t["date"] for t in dh_only], [])
        self.assertEqual([t["date"] for t in ex_only], ["2000-03-01"])

    def test_outside_window_unmatched(self):
        dh = [{"date": "2000-01-01"}]
        ex = [{"date": "2000-05-01"}]  # lag 4 > 3
        matched, dh_only, ex_only = au.classify(dh, ex)
        self.assertEqual(matched, [])
        self.assertEqual(len(dh_only), 1)
        self.assertEqual(len(ex_only), 1)

    def test_each_trigger_used_once(self):
        dh = [{"date": "2000-06-01"}]
        ex = [{"date": d} for d in ("2000-05-01", "2000-07-01")]
        matched, _, _ = au.classify(dh, ex)
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0]["exact"], "2000-05-01")  # tie |1| vs |1| -> earliest


class TestLabels(unittest.TestCase):
    def test_all_eight(self):
        cases = {
            (False, False, False): "timing_only",
            (True, False, False): "state_only",
            (False, True, False): "growth_trajectory_only",
            (False, False, True): "inflation_trajectory_only",
            (False, True, True): "both_trajectories",
            (True, True, False): "state_plus_growth",
            (True, False, True): "state_plus_inflation",
            (True, True, True): "state_plus_both",
        }
        for (s, g, i), want in cases.items():
            self.assertEqual(au.attribute_label(s, g, i), want)

    def test_na_never_counts_as_mismatch(self):
        self.assertEqual(au.attribute_label(False, "na", "na"), "timing_only")
        self.assertEqual(au.attribute_label(True, "na", False), "state_only")


class TestLeadLagConvention(unittest.TestCase):
    def test_sign_convention(self):
        # lag = exact - dh ; positive means DH first
        prof = au.nearest_profile(["2000-01-01", "2000-06-01"], ["2000-03-01"])
        self.assertEqual(prof["lags"], [2, -3])
        self.assertEqual((prof["dh_first"], prof["ex_first"], prof["same"]), (1, 1, 0))
        self.assertEqual(prof["median"], -0.5)

    def test_onsets_require_sign_change(self):
        grid = [("2000-%02d-01" % m, v) for m, v in
                [(1, 0.0), (2, 0.0), (3, 0.0), (4, 1.0), (5, 2.0)]]
        # d3: idx3 = 1-0 >0 but d3[idx2] NaN -> no onset; idx4: d3=2>0, prev d3=1>0 -> no onset
        self.assertEqual(au.positive_d3_onsets(grid), [])


class TestVerdict(unittest.TestCase):
    def test_branches(self):
        self.assertEqual(au.decide_verdict(0.7, 0.2, 1.0), "cross_layer_divergence_growth_dominant")
        self.assertEqual(au.decide_verdict(0.2, 0.7, 1.0), "cross_layer_divergence_inflation_dominant")
        self.assertEqual(au.decide_verdict(0.68, 0.84, 1.0), "cross_layer_divergence_joint_and_rotating")
        self.assertEqual(au.decide_verdict(0.9, 0.1, 0.5), "cross_layer_divergence_insufficient_component_evidence")
        self.assertEqual(au.decide_verdict(0.9, 0.1, 2.0 / 3.0), "cross_layer_divergence_growth_dominant")

    def test_determinism(self):
        mos = months("2000-01-01", "2001-12-01")
        G = {m: (0.0 if m < "2000-06-01" else -20.0) for m in mos}
        I = dict(G)
        st1, _, _ = au.build_layer(mos, G.get, I.get)
        st2, _, _ = au.build_layer(mos, G.get, I.get)
        self.assertEqual([(s["m"], s["elig"], s["qual"]) for s in st1],
                         [(s["m"], s["elig"], s["qual"]) for s in st2])


class TestFrozenIntegration(unittest.TestCase):
    def test_dh_trigger_count(self):
        import pathlib
        p = pathlib.Path(__file__).resolve().parent / "generated" / "issue-160" / "deep-history-v01-monthly.csv"
        if not p.exists():
            self.skipTest("repo macro files absent")
        dh = au.load_dh_csv(str(p))
        mos = sorted(dh)
        _, _, trig = au.build_layer(
            mos, lambda m: dh[m]["growth_dh"], lambda m: dh[m]["inflation_dh"])
        self.assertEqual(len(trig), 27)

    def test_snapshot_rejects_wrong_bytes(self):
        import gzip
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".b64", delete=False, mode="w") as f:
            import base64
            f.write(base64.b64encode(gzip.compress(b"date,gpi,ipi,regime\n2000-01-31,0,0,1\n")).decode())
            name = f.name
        with self.assertRaises(SystemExit):
            au.load_snapshot_b64(name)


if __name__ == "__main__":
    unittest.main()
