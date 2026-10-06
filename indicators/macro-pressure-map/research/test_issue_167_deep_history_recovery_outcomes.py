#!/usr/bin/env python
"""Tests for the Issue #167 frozen evaluator.

Frozen by research/issue-167-deep-history-recovery-outcomes-prereg.md.
Deterministic; no pandas/numpy. Run from indicators/macro-pressure-map/research/:

    python test_issue_167_deep_history_recovery_outcomes.py
"""

from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

import issue_167_deep_history_recovery_outcomes as ev


class TestMonthMath(unittest.TestCase):
    def test_add_months(self):
        self.assertEqual(ev.add_months("2026-08", 1), "2026-09")
        self.assertEqual(ev.add_months("2026-01", -3), "2025-10")
        self.assertEqual(ev.add_months("1966-01", 13), "1967-02")
        self.assertEqual(ev.add_months("2025-12", 1), "2026-01")

    def test_month_range_len(self):
        self.assertEqual(len(ev.month_range("1966-03", "2026-08")), 726)
        self.assertEqual(len(ev.month_range("2026-08", "2026-08")), 1)

    def test_payoff_months_start_at_t_plus_2(self):
        self.assertEqual(ev.payoff_months("1966-03", 3), ["1966-05", "1966-06", "1966-07"])
        self.assertEqual(ev.payoff_months("1966-03", 1), ["1966-05"])
        self.assertEqual(ev.payoff_months("1966-03", 3, extra_delay=1),
                         ["1966-06", "1966-07", "1966-08"])


class TestClassification(unittest.TestCase):
    def test_primary_state_boundaries_inclusive_of_plus_10(self):
        macro = {"2020-01": {"g": 10.0, "i": 10.0}}
        c = ev.classify(macro, ["2020-01"])["2020-01"]
        self.assertTrue(c["primary_state"])
        self.assertFalse(c["deep_dual_weak"])

    def test_primary_state_excludes_above_10(self):
        macro = {"2020-01": {"g": 10.0001, "i": 0.0}}
        self.assertFalse(ev.classify(macro, ["2020-01"])["2020-01"]["primary_state"])

    def test_deep_dual_weak_strictly_below_minus_10(self):
        macro = {"2020-01": {"g": -10.0, "i": -10.0}}
        c = ev.classify(macro, ["2020-01"])["2020-01"]
        self.assertFalse(c["deep_dual_weak"])            # not strictly below
        self.assertTrue(c["mild_transition_weak"])
        macro2 = {"2020-01": {"g": -10.5, "i": -12.0}}
        c2 = ev.classify(macro2, ["2020-01"])["2020-01"]
        self.assertTrue(c2["deep_dual_weak"])
        self.assertTrue(c2["primary_state"])
        self.assertFalse(c2["mild_transition_weak"])

    def test_severity_partition_is_exhaustive_and_exclusive(self):
        macro = {"2020-01": {"g": 5.0, "i": 3.0}, "2020-02": {"g": -20.0, "i": -20.0}}
        for m, c in ev.classify(macro, ["2020-01", "2020-02"]).items():
            self.assertNotEqual(c["deep_dual_weak"] and c["mild_transition_weak"], True)
            if c["primary_state"]:
                self.assertTrue(c["deep_dual_weak"] or c["mild_transition_weak"])

    def test_trajectory_needs_both_positive_and_t_minus_3(self):
        macro = {
            "2020-01": {"g": -20.0, "i": -20.0},
            "2020-02": {"g": -19.0, "i": -19.0},
            "2020-03": {"g": -18.0, "i": -18.0},
            "2020-04": {"g": -5.0, "i": -5.0},   # d3G=+15 d3I=+15 vs 2020-01
        }
        months = list(macro)
        c = ev.classify(macro, months)
        self.assertFalse(c["2020-03"]["trajectory_valid"])   # t-3 = 2019-12 missing
        self.assertTrue(c["2020-04"]["trajectory_valid"])
        self.assertTrue(c["2020-04"]["qualifying"])

    def test_trajectory_requires_both_axes_positive(self):
        macro = {
            "2020-01": {"g": -20.0, "i": -20.0},
            "2020-02": {"g": -19.0, "i": -19.0},
            "2020-03": {"g": -18.0, "i": -18.0},
            "2020-04": {"g": -5.0, "i": -21.0},   # d3G=+15, d3I=-1 -> not positive
        }
        c = ev.classify(macro, list(macro))
        self.assertFalse(c["2020-04"]["trajectory_positive"])
        self.assertFalse(c["2020-04"]["qualifying"])


class TestEpisodesAndControls(unittest.TestCase):
    def setUp(self):
        # 6 months, primary state true throughout except 2020-04 (G high)
        # trajectories: only 2020-06 qualifies (needs t-3 = 2020-03)
        self.macro = {
            "2020-01": {"g": -20.0, "i": -20.0},
            "2020-02": {"g": -21.0, "i": -21.0},
            "2020-03": {"g": -22.0, "i": -22.0},
            "2020-04": {"g": -23.0, "i": -23.0},
            "2020-05": {"g": -24.0, "i": -24.0},
            "2020-06": {"g": 0.0, "i": 0.0},     # d3G=+22, d3I=+22 -> qualifying
            "2020-07": {"g": 1.0, "i": 1.0},
        }
        self.months = list(self.macro)
        self.c = ev.classify(self.macro, self.months)

    def test_single_episode_first_trigger_only(self):
        rows, eps = ev.primary_signals_controls(self.c, self.months)
        self.assertEqual(len(eps), 1)
        sig = [r["month"] for r in rows if r["role"] == "signal"]
        self.assertEqual(sig, ["2020-06"])                  # 2020-07 also qualifies but is excluded

    def test_controls_are_pre_trigger_eligible_months_only(self):
        rows, eps = ev.primary_signals_controls(self.c, self.months)
        ctl = sorted(r["month"] for r in rows if r["role"] == "control")
        # eligible (t-3 available) months before the trigger
        self.assertEqual(ctl, ["2020-04", "2020-05"])
        # post-trigger month 2020-07 is neither signal nor control
        self.assertNotIn("2020-07", [r["month"] for r in rows])

    def test_macro_hole_breaks_episode_contiguity(self):
        macro = {
            "2020-01": {"g": 0.0, "i": 0.0},
            "2020-03": {"g": 0.0, "i": 0.0},   # 2020-02 missing
        }
        c = ev.classify(macro, ["2020-01", "2020-03"])
        eps = ev.build_episodes({m: True for m in macro}, list(macro))
        self.assertEqual(len(eps), 2)

    def test_never_triggering_episode_keeps_all_eligible_months_as_controls(self):
        macro = {
            "2020-01": {"g": 0.0, "i": 0.0},
            "2020-02": {"g": -1.0, "i": -1.0},
            "2020-03": {"g": -2.0, "i": -2.0},
            "2020-04": {"g": -3.0, "i": -3.0},   # d3G = -3, d3I = -3 -> never triggers
        }
        c = ev.classify(macro, list(macro))
        rows, eps = ev.primary_signals_controls(c, list(macro))
        self.assertEqual([r for r in rows if r["role"] == "signal"], [])
        self.assertEqual(len([r for r in rows if r["role"] == "control"]), 1)  # only 2020-04 is eligible


class TestPayoff(unittest.TestCase):
    def test_compound_and_spread(self):
        eq = {"2020-05": 0.10, "2020-06": 0.0, "2020-07": 0.0}
        tsy = {"2020-05": 0.02, "2020-06": 0.0, "2020-07": 0.0}
        sp = ev.spreads_for(eq, tsy, "2020-03", [3])
        self.assertAlmostEqual(sp[3]["spread"], 0.08, places=10)

    def test_missing_payoff_month_yields_none(self):
        eq = {"2020-05": 0.10}
        tsy = {"2020-05": 0.02}
        sp = ev.spreads_for(eq, tsy, "2020-03", [3])
        self.assertIsNone(sp[3]["spread"])

    def test_no_return_from_t_or_t_plus_1_enters_payoff(self):
        ms = ev.payoff_months("2020-03", 3)
        self.assertNotIn("2020-03", ms)
        self.assertNotIn("2020-04", ms)
        self.assertEqual(ms[0], "2020-05")


class TestGatesAndVerdict(unittest.TestCase):
    def _obs(self, sig, ctl, era="1966-1984", ep_sig=0, ep_ctl=0):
        out = []
        for i, v in enumerate(sig):
            out.append({"role": "signal", "spread": v, "era": era, "episode_id": i})
        for v in ctl:
            out.append({"role": "control", "spread": v, "era": era, "episode_id": 900})
        return out

    def test_few_episodes_gives_inconclusive_sample(self):
        obs = self._obs([0.1] * 3, [0.01] * 3)
        boot = {"ci_lower": 0.01, "ci_upper": 0.2}
        gates, _ = ev.evaluate_gates(obs, [], boot, 0.05, 0.05)
        self.assertEqual(ev.verdict_from(gates, 0.05),
                         "deep_history_recovery_outcome_inconclusive_sample")

    def test_negative_direction_gives_not_supported(self):
        obs = self._obs([-0.1] * 8, [0.05] * 8)
        boot = {"ci_lower": -0.3, "ci_upper": 0.0}
        gates, _ = ev.evaluate_gates(obs, [], boot, -0.15, -0.15)
        self.assertEqual(ev.verdict_from(gates, -0.15),
                         "deep_history_recovery_outcome_not_supported")

    def test_positive_but_robustness_failure_gives_suggestive(self):
        obs = self._obs([0.10] * 8, [0.01] * 8)
        boot = {"ci_lower": -0.01, "ci_upper": 0.3}       # gate 4 fails
        gates, _ = ev.evaluate_gates(obs, [], boot, 0.09, 0.09)
        self.assertTrue(gates["gate2_signal_mean_gt_0"])
        self.assertTrue(gates["gate3_incremental_gt_0"])
        self.assertEqual(ev.verdict_from(gates, 0.09),
                         "deep_history_recovery_outcome_suggestive_not_robust")

    def test_strongest_trigger_share_gate(self):
        # one trigger episode dominates -> gate 8 must fail
        obs = [{"role": "signal", "spread": 0.9, "era": "1966-1984", "episode_id": 0}]
        obs += [{"role": "signal", "spread": 0.01, "era": "1985-2004", "episode_id": i}
                for i in range(1, 8)]
        obs += [{"role": "control", "spread": 0.0, "era": "1966-1984", "episode_id": 900}]
        boot = {"ci_lower": 0.001, "ci_upper": 0.5}
        gates, detail = ev.evaluate_gates(obs, [], boot, 0.1, 0.1)
        self.assertFalse(gates["gate8_strongest_share_le_50pct"])
        self.assertGreater(detail["strongest_positive_share"], 0.5)


class TestBootstrap(unittest.TestCase):
    def test_deterministic_under_fixed_seed(self):
        obs = [{"episode_id": i, "role": "signal", "spread": 0.02 * i}
               for i in range(1, 12)]
        obs += [{"episode_id": i, "role": "control", "spread": 0.001 * i}
                for i in range(1, 12)]
        a = ev.episode_cluster_bootstrap(obs, sorted({o["episode_id"] for o in obs}))
        b = ev.episode_cluster_bootstrap(obs, sorted({o["episode_id"] for o in obs}))
        self.assertEqual(a, b)
        self.assertEqual(a["valid_replications"], ev.N_BOOTSTRAP_VALID_REQUIRED)
        self.assertLess(a["ci_lower"], a["ci_upper"])

    def test_resamples_episodes_not_months(self):
        # one episode with 50 controls and one signal; another with 1 signal + 1 control
        obs = [{"episode_id": 0, "role": "signal", "spread": 0.5}]
        obs += [{"episode_id": 0, "role": "control", "spread": 0.0} for _ in range(50)]
        obs += [{"episode_id": 1, "role": "signal", "spread": 0.5},
                {"episode_id": 1, "role": "control", "spread": 0.0}]
        r = ev.episode_cluster_bootstrap(obs, [0, 1])
        self.assertEqual(r["n_episodes"], 2)
        self.assertEqual(r["valid_replications"], ev.N_BOOTSTRAP_VALID_REQUIRED)

    def test_no_episode_with_both_roles(self):
        obs = [{"episode_id": 0, "role": "signal", "spread": 0.5}]
        r = ev.episode_cluster_bootstrap(obs, [0])
        self.assertEqual(r["valid_replications"], 0)
        self.assertIsNone(r["ci_lower"])


class TestSecondaryCohort(unittest.TestCase):
    def test_high_inflation_slowdown_can_trigger(self):
        """Regression: cohort triggers must use the COHORT state, not the primary state.

        A month with I > +10 can never satisfy the primary state, so reusing the
        primary `qualifying` flag would suppress every secondary trigger.
        """
        macro = {
            "2020-01": {"g": -20.0, "i": 5.0},
            "2020-02": {"g": -19.0, "i": 6.0},
            "2020-03": {"g": -18.0, "i": 7.0},
            "2020-04": {"g": -5.0, "i": 12.0},   # G<=+10 AND I>+10; d3G=+15, d3I=+7
        }
        months = list(macro)
        c = ev.classify(macro, months)
        self.assertFalse(c["2020-04"]["primary_state"])          # not primary (I > +10)
        self.assertTrue(c["2020-04"]["trajectory_positive"])
        rows, eps = ev.cohort_rows(c, months, "high_inflation_slowdown")
        sig = [r["month"] for r in rows if r["role"] == "signal"]
        self.assertEqual(sig, ["2020-04"])

    def test_primary_cohort_ignores_high_inflation_months(self):
        macro = {
            "2020-01": {"g": -20.0, "i": 5.0},
            "2020-02": {"g": -19.0, "i": 6.0},
            "2020-03": {"g": -18.0, "i": 7.0},
            "2020-04": {"g": -5.0, "i": 12.0},
        }
        rows, eps = ev.cohort_rows(ev.classify(macro, list(macro)), list(macro), "primary")
        self.assertEqual([r for r in rows if r["role"] == "signal"], [])

    def test_every_triggered_episode_row_reports_a_severity(self):
        """Regression: episode rows must never omit trigger_severity.

        main() and the tests once used two divergent episode builders, which left
        trigger_severity blank in the emitted episodes CSV.
        """
        macro = {
            "2020-01": {"g": -20.0, "i": -20.0},
            "2020-02": {"g": -21.0, "i": -21.0},
            "2020-03": {"g": -22.0, "i": -22.0},
            "2020-04": {"g": 0.0, "i": 0.0},     # qualifying -> trigger
            "2020-05": {"g": 0.0, "i": 0.0},
        }
        c = ev.classify(macro, list(macro))
        for cohort in ("primary", "high_inflation_slowdown"):
            _, eps = ev.cohort_rows(c, list(macro), cohort)
            for e in eps:
                self.assertIn("trigger_severity", e)
                self.assertIn("post_trigger_excluded", e)
                if e["trigger_month"] is not None:
                    self.assertIn(e["trigger_severity"],
                                  ("deep_dual_weak", "mild_transition_weak"))

    def test_alias_matches_cohort_builder(self):
        macro = {
            "2020-01": {"g": -20.0, "i": -20.0},
            "2020-02": {"g": -21.0, "i": -21.0},
            "2020-03": {"g": -22.0, "i": -22.0},
            "2020-04": {"g": 0.0, "i": 0.0},
        }
        c = ev.classify(macro, list(macro))
        self.assertEqual(ev.primary_signals_controls(c, list(macro)),
                         ev.cohort_rows(c, list(macro), "primary"))


class TestEmittedArtifacts(unittest.TestCase):
    """Validation of the committed Issue #167 outputs (self-consistency invariants)."""

    OUT = Path(__file__).resolve().parent / "generated" / "issue-167"

    @classmethod
    def setUpClass(cls):
        cls.res = json.loads((cls.OUT / "recovery-primary-result.json").read_text())
        cls.rows = list(csv.DictReader((cls.OUT / "recovery-signal-control.csv").open(newline="")))

    def test_required_flags(self):
        self.assertTrue(self.res["outcome_data_loaded"])
        self.assertFalse(self.res["production_authorized"])
        self.assertTrue(self.res["revised_macro_history"])
        self.assertFalse(self.res["real_time_vintage_claim"])

    def test_nine_gates_present(self):
        self.assertEqual(len(self.res["gates"]), 9)
        self.assertTrue(all(isinstance(v, bool) for v in self.res["gates"].values()))

    def test_leg_mean_identity(self):
        """mean(Equity minus Treasury) must equal mean(Equity) - mean(Treasury)."""
        for role in ("signal", "control"):
            sel = [r for r in self.rows
                   if r["role"] == role
                   and r["spread_3m"] and r["equity_3m"] and r["treasury_3m"]]
            exp = ev.mean([float(r["equity_3m"]) for r in sel]) - \
                  ev.mean([float(r["treasury_3m"]) for r in sel])
            got = self.res[f"{role}_3m"]["mean"]
            self.assertAlmostEqual(got, exp, places=12)
            self.assertAlmostEqual(self.res[f"{role}_3m"]["equity_leg_mean"],
                                   ev.mean([float(r["equity_3m"]) for r in sel]), places=12)

    def test_3x3_map_covers_all_macro_valid_months(self):
        m = self.res["descriptive_3x3_map"]
        self.assertEqual(len(m), 9)
        self.assertEqual(sum(x["months"] for x in m),
                         self.res["inputs"]["macro_valid_months_in_window"])

    def test_state_quadrants_partition_each_state(self):
        by_state = {}
        for x in self.res["descriptive_trajectory_quadrants_within_state"]:
            key = (x["growth_band"], x["inflation_band"])
            by_state[key] = by_state.get(key, 0) + x["months"]
        self.assertEqual(len(by_state), 9)
        for cell in self.res["descriptive_3x3_map"]:
            key = (cell["growth_band"], cell["inflation_band"])
            # months with no valid t-3 fall outside all four quadrants
            self.assertLessEqual(by_state[key], cell["months"])
            self.assertLessEqual(cell["months"] - by_state[key], 3)

    def test_timing_columns_present_and_shifted(self):
        for r in self.rows:
            self.assertEqual(ev.add_months(r["macro_state_month"], 1),
                             r["signal_available_month"])

    def test_verdict_is_one_of_the_frozen_three(self):
        self.assertIn(self.res["verdict"], (
            "deep_history_recovery_outcome_supported",
            "deep_history_recovery_outcome_suggestive_not_robust",
            "deep_history_recovery_outcome_not_supported",
            "deep_history_recovery_outcome_inconclusive_sample",
        ))

    def test_bootstrap_is_episode_cluster_not_iid(self):
        b = self.res["bootstrap"]
        self.assertEqual(b["method"], "primary-state-episode cluster bootstrap")
        self.assertEqual(b["valid_replications"], 10000)
        self.assertEqual(b["seed"], 19660101)


class TestFrozenInputs(unittest.TestCase):
    def test_macro_blob_hash_matches_prereg(self):
        from pathlib import Path
        # anchored to this file's directory so the guard cannot silently skip
        # when the suite is run from the repository root
        p = (Path(__file__).resolve().parent
             / "generated/issue-160/deep-history-v01-monthly.csv")
        self.assertTrue(p.exists(), f"frozen macro CSV missing: {p}")
        self.assertEqual(ev.blob_sha256(p), ev.MACRO_BLOB_SHA256)

    def test_frozen_constants_unchanged(self):
        self.assertEqual(ev.SEED, 19660101)
        self.assertEqual(ev.N_BOOTSTRAP, 10000)
        self.assertEqual(ev.PRIMARY_THRESHOLD, 10.0)
        self.assertEqual(ev.DEEP_THRESHOLD, -10.0)
        self.assertEqual(ev.TRAJECTORY_LAG, 3)
        self.assertEqual(len(ev.ERAS), 3)
        self.assertEqual(ev.PAYOFF_LAG, 2)
        self.assertEqual(ev.AVAIL_LAG, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
