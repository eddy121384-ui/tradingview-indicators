#!/usr/bin/env python3
"""Issue #177 — third, toolchain-independent mirror of the frozen policy rules.

The Node builder and the Node acceptance suite cover the JS path. This module is a
deliberately separate re-implementation in Python + pandas + numpy that:

  * rebuilds the macro 3x3 states from the frozen DH v0.1 monthly file;
  * rebuilds the frozen state episodes independently;
  * recomputes the policy-relevant statistics (mean Cash excess, episode excess hit
    rate, 10th-percentile monthly Cash excess, worst-episode return,
    P(monthly Cash excess < -2pp), ex-worst-episode mean) from the RAW monthly returns
    for the #176 hardened S&P 500 and investable-oil series and from the frozen #174
    tables for the other sleeves;
  * applies the frozen tier / zero-rule / cash-bias logic and compares every one of the
    72 non-cash cells and all 9 Cash rows against the committed artifacts.

It imports neither the builder nor the Node tests and shares no code with them.
Run:  python -m unittest test_issue_177_pandas_mirror     (cwd = this directory)
"""
from __future__ import annotations

import pathlib
import unittest

import numpy as np
import pandas as pd

RES = pathlib.Path(__file__).resolve().parent
G174 = RES / "generated" / "issue-174"
G176 = RES / "generated" / "issue-176"
G177 = RES / "generated" / "issue-177"

NONCASH = ["sp500", "nasdaq", "russell", "treasury2y", "treasury10y", "longtreasury", "gold", "oil"]
POINTS = {"High": 2, "Neutral": 1, "Low": 0, "0": -1}


def _band(s: float) -> str:
    return "Low" if s < -10 else ("High" if s > 10 else "Neutral")


def _calnext(mo: str) -> str:
    y, m = int(mo[:4]), int(mo[5:7]) + 1
    if m > 12:
        m, y = 1, y + 1
    return f"{y:04d}-{m:02d}-01"


class FrozenRecompute:
    """Independent pandas/numpy reconstruction of the frozen policy inputs."""

    def __init__(self) -> None:
        macro = pd.read_csv(
            RES / "generated" / "issue-160" / "deep-history-v01-monthly.csv",
            usecols=["date", "growth_dh", "inflation_dh"],
        ).dropna()
        macro["state"] = "G_" + macro.growth_dh.map(_band) + "/I_" + macro.inflation_dh.map(_band)
        macro = (
            macro[(macro.date >= "1966-03-01") & (macro.date <= "2026-08-01")]
            .sort_values("date")
            .reset_index(drop=True)
        )
        r174 = pd.read_csv(G174 / "nine-sleeve-monthly-returns.csv").rename(columns={"oil": "oil_spot"})
        r176 = pd.read_csv(G176 / "hardened-monthly-returns.csv")
        self.df = macro.merge(r174, on="date", how="left").merge(r176, on="date", how="left")

        # frozen state episodes: contiguous runs of the same state over macro months
        eps, s = [], 0
        dates = list(self.df.date)
        for k in range(1, len(dates)):
            if self.df.state[k] == self.df.state[s] and _calnext(dates[k - 1]) == dates[k]:
                continue
            eps.append((self.df.state[s], dates[s], dates[k - 1]))
            s = k
        eps.append((self.df.state[s], dates[s], dates[-1]))
        self.episodes = eps

        self.ev = pd.read_csv(G174 / "evidence-classification.csv").set_index(["state", "sleeve"])
        self.dg = pd.read_csv(G174 / "downside-danger.csv").set_index(["state", "sleeve"])
        self.z = pd.read_csv(G174 / "future-zero-candidates.csv").set_index(["state", "sleeve"])
        self.sens = pd.read_csv(G176 / "affected-state-sensitivity.csv").set_index(["state", "sleeve"])
        self.inv = pd.read_csv(G176 / "oil-investable-state-cells.csv").set_index("state")
        self.matrix = pd.read_csv(G177 / "policy-matrix.csv")
        self.cash = pd.read_csv(G177 / "cash-bias.csv")

    # ---- raw-return statistics (frozen definitions) ----
    def stats(self, state: str, col: str) -> dict:
        o = self.df[(self.df.state == state) & self.df[col].notna() & self.df.cash.notna()]
        ex = (o[col] - o.cash).to_numpy()
        worst_rs, wstart, wend, hits = np.nan, None, None, []
        for st, a, b in self.episodes:
            if st != state:
                continue
            em = o[(o.date >= a) & (o.date <= b)]
            if not len(em):
                continue
            rs = float(np.prod(1 + em[col].to_numpy()) - 1)
            rc = float(np.prod(1 + em.cash.to_numpy()) - 1)
            hits.append((1 + rs) / (1 + rc) - 1 > 0)
            if np.isnan(worst_rs) or rs < worst_rs:
                worst_rs, wstart, wend = rs, a, b
        keep = o[~((o.date >= wstart) & (o.date <= wend))] if wstart else o
        return {
            "n": len(o), "nE": len(hits),
            "meanEx": float(ex.mean()) if len(ex) else np.nan,
            "p10ex": float(np.percentile(ex, 10)) if len(ex) else np.nan,
            "pMat": float((ex < -0.02).mean()) if len(ex) else np.nan,
            "epHit": float(np.mean(hits)) if hits else np.nan,
            "worstEp": worst_rs,
            "exWorst": float((keep[col] - keep.cash).mean()) if len(keep) else np.nan,
        }

    def policy_input(self, state: str, sleeve: str):
        if sleeve == "sp500":
            s, evid, flag = self.stats(state, "sp500_tr_hardened"), self.sens.loc[(state, sleeve)].ev_new, bool(self.sens.loc[(state, sleeve)].zero_new)
        elif sleeve == "oil":
            s, evid, flag = self.stats(state, "oil_investable_return"), self.inv.loc[state].evidence, bool(self.inv.loc[state].zero_candidate)
        else:
            raw = self.stats(state, sleeve)
            e, d = self.ev.loc[(state, sleeve)], self.dg.loc[(state, sleeve)]
            evid, flag = e.evidence, bool(self.z.loc[(state, sleeve)].future_zero_weight_candidate)
            s = {
                "n": raw["n"], "nE": raw["nE"], "meanEx": e.mean_ex, "p10ex": d.p10_ex,
                "pMat": d.p_material_monthly, "epHit": e.ep_hit,
                "worstEp": d.worst_episode, "exWorst": e.ex_worst_mean_ex,
            }
        return s, evid, flag


def _zero_path_b(s: dict, evid: str) -> bool:
    return (
        evid == "historically_unfavorable"
        and s["meanEx"] < 0
        and s["epHit"] <= 0.40
        and ((s["p10ex"] <= -0.04) or (s["worstEp"] <= -0.15) or (s["pMat"] >= 0.10))
        and s["exWorst"] < 0
    )


def _tier(evid: str, mean_ex: float, flag_a: bool, path_b: bool) -> str:
    if evid == "historically_favored":
        return "High"
    if evid == "historically_unfavorable":
        return "0" if (flag_a or path_b) else "Low"
    if evid == "mixed":
        return "Neutral" if mean_ex >= 0 else "Low"
    if evid == "insufficient_sample":
        return "Neutral"
    raise ValueError(evid)


class TestIssue177PandasMirror(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.r = FrozenRecompute()

    def test_all_72_tiers_reproduce(self):
        checked, bad = 0, []
        for _, row in self.r.matrix.iterrows():
            if row.sleeve not in NONCASH:
                continue
            s, evid, flag = self.r.policy_input(row.state, row.sleeve)
            want = _tier(evid, s["meanEx"], flag, _zero_path_b(s, evid))
            checked += 1
            if want != row.exposure:
                bad.append(f"{row.state}|{row.sleeve}: recomputed {want}, artifact {row.exposure}")
            # pandas and JS sum in different orders: the frozen comparison tolerance is 1e-12
            self.assertLess(abs(s["meanEx"] - float(row.mean_ex)), 1e-12, f"{row.state}|{row.sleeve} mean_ex")
            self.assertLess(abs(s["epHit"] - float(row.ep_hit)), 1e-12, f"{row.state}|{row.sleeve} ep_hit")
        self.assertEqual(checked, 72)
        self.assertEqual(bad, [], "tier mismatches")

    def test_low_low_oil_zero_justification(self):
        s, evid, flag = self.r.policy_input("G_Low/I_Low", "oil")
        self.assertEqual(evid, "historically_unfavorable")
        self.assertFalse(flag, "strict frozen zero flag is false (n=34 < 60); the zero comes from rule B")
        self.assertTrue(_zero_path_b(s, evid))
        self.assertEqual(s["n"], 34)
        self.assertLess(s["p10ex"], -0.04)
        self.assertLess(s["worstEp"], -0.15)
        self.assertLess(s["exWorst"], 0)

    def test_zero_cells_only_three(self):
        zeros = self.r.matrix[(self.r.matrix.sleeve != "cash") & (self.r.matrix.exposure == "0")]
        self.assertEqual(
            sorted(zip(zeros.state, zeros.sleeve)),
            [("G_High/I_Low", "gold"), ("G_Low/I_Low", "oil"), ("G_Neutral/I_High", "russell")],
        )

    def test_cash_scores_and_biases(self):
        m = self.r.matrix.set_index(["state", "sleeve"])
        for _, c in self.r.cash.iterrows():
            score = sum(POINTS[m.loc[(c.state, s)].exposure] for s in NONCASH)
            bias = "high" if score <= 3 else ("neutral" if score <= 8 else "low")
            self.assertEqual(score, int(c.opportunity_score), c.state)
            self.assertEqual(bias, c.cash_bias, c.state)
            self.assertEqual(c.cash_role, "residual")

    def test_invariants(self):
        m = self.r.matrix
        self.assertEqual(len(m), 72)  # non-cash cells; Cash lives in cash-bias.csv
        self.assertEqual(len(self.r.cash), 9)
        self.assertEqual(len(m[(m.sleeve != "cash") & (m.evidence == "historically_unfavorable") & (m.exposure == "High")]), 0)
        ins = m[(m.sleeve != "cash") & (m.evidence == "insufficient_sample")]
        self.assertTrue((ins.exposure == "Neutral").all())
        self.assertTrue((ins.low_confidence == True).all())  # noqa: E712 - CSV booleans
        self.assertEqual(int((m[m.sleeve != "cash"].confidence == "limited").sum()), 36)


if __name__ == "__main__":
    unittest.main(verbosity=2)
