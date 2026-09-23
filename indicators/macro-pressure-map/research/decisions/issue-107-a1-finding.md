# Issue #107 — A1 Public-Feed Screening Finding

Status: **A1 COMPLETE — NO A2 TRIGGER**

Phase A verdict: **`modern_policy_relation_period_dependent`**

## Executive decision

The preregistered A1 public-feed screen completed successfully on GitHub Actions run `35808738793` at head `32b510861efaed5ff63e50653f2c39263d2ddc7a`.

The central Issue #107 hypothesis does **not** earn `continuous_policy_information_stable`.

The evidence says:

- adding the preregistered policy starting point (`real_policy_rate`) can contain useful OOS information in some modern subperiods;
- that information is materially period-dependent rather than stable across the full predeclared temporal split;
- adding the six preregistered GPI/IPI trajectory features on top of levels + stance does **not** provide stable incremental value;
- therefore A1 does **not** trigger A2 TradingView-feed confirmation;
- Phase B / Policy Pressure Proxy design is **not authorized**;
- V6.6 production logic remains frozen and unchanged.

No post-outcome feature, horizon, threshold, or lookback change was made.

---

## 1. Research integrity / engineering status

Preregistration revalidation: **PASS** — 8 tests.

Evaluator unit tests: **PASS** — 5 tests.

A1 screening: **PASS**.

Research boundary enforcement: **PASS**.

Artifact: `issue-107-a1-public-screening`  
Artifact ID: `10728562458`  
Artifact ZIP SHA256: `7dd1935241639f90d2dfaa814ffd88bf3345a6b1e53616199e5c033d3e927c34`

OOS sample:

- first origin: `2015-01`
- last origin: `2025-06`
- rows: `126`

The PCEPILFE transport blocker was resolved without changing the preregistered data definition. The evaluator now reads a frozen official FRED PCEPILFE index snapshot for 2005–2025 and still fails closed on the preregistered official checkpoints.

---

## 2. Full-sample expanding-window result

| Model | RMSE | MAE | Correlation | Direction accuracy (>25bp) |
|---|---:|---:|---:|---:|
| M0 — GPI + IPI | 0.8829 | 0.5905 | -0.1495 | 45.6% |
| M1 — M0 + real policy rate | 0.7749 | 0.6288 | 0.5508 | 57.4% |
| M2 — M1 + trajectory | 0.8022 | 0.6414 | 0.5074 | 54.4% |

### M1 minus M0

- RMSE: **-0.1080** (improves)
- MAE: **+0.0382** (worsens)
- correlation: **+0.7004**
- direction accuracy: **+11.8 pp**

So the stance variable has a real full-sample signal, but the primary error metrics are already mixed.

### M2 minus M1

- RMSE: **+0.0273** (worsens)
- MAE: **+0.0127** (worsens)
- correlation: **-0.0434**
- direction accuracy: **-2.9 pp**

The preregistered trajectory layer does not improve the full-sample expanding OOS result.

---

## 3. Predeclared temporal validation

### 2015–2019 — pre_COVID_modern

M1 versus M0:

- RMSE: 0.6216 vs 0.5705 — worse
- MAE: 0.5237 vs 0.4344 — worse
- correlation: -0.3592 vs -0.1340 — worse
- direction: 33.3% vs 50.0% — worse

M2 versus M1 is also worse on all four diagnostics.

This period directly contradicts a stable modern policy-reaction relation.

### 2020–2022 — COVID_inflation_transition

M1 versus M0:

- RMSE: 0.9740 vs 1.3692 — materially better
- MAE: 0.7316 vs 0.9210 — better
- correlation: 0.6633 vs -0.0455 — much better
- direction: 100.0% vs 47.1% on 17 nontrivial moves

This is the strongest subperiod for the stance variable.

M2 versus M1 again worsens RMSE, MAE, and correlation, with no directional gain.

### 2023–2025-06 — higher_rate_disinflation

M1 versus M0:

- RMSE: 0.7815 vs 0.6111 — worse
- MAE: 0.7155 vs 0.5062 — worse
- correlation: 0.7483 vs -0.2875 — better
- direction: 66.7% vs 33.3% — better

This is mixed: ranking/directional information improves, but forecast error worsens.

M2 versus M1 only produces tiny error improvements here (RMSE -0.0027, MAE -0.0128) while correlation deteriorates and directional accuracy is unchanged. That is not stable incremental evidence.

---

## 4. Rolling-96 diagnostic

The diagnostic 8-year rolling window does not rescue the trajectory hypothesis.

Full sample:

- M1 improves M0 on RMSE, MAE, correlation, and direction.
- M2 then worsens RMSE, MAE, and correlation; direction improves only +1.5 pp.

Temporal behavior remains non-uniform:

- pre-COVID: M1 is worse than M0 on RMSE/MAE/correlation;
- COVID transition: M1 is strongly better;
- higher-rate disinflation: M1 improves RMSE/correlation/direction but slightly worsens MAE.

M2 improvements appear only as small, inconsistent pockets and reverse across periods/windows.

---

## 5. Preregistered verdict selection

The preregistered rules define:

- `continuous_policy_information_stable` only if M2 improves M1 without material directional degradation and the gain is not isolated to one temporal segment;
- `levels_and_stance_sufficient_dynamics_add_no_value` if M1 improves M0 and M2 adds no stable value;
- `modern_policy_relation_period_dependent` if useful full-sample information exists but incremental signs/performance materially reverse or concentrate in one temporal segment.

The second label is too strong for these results because M1 itself is not temporally stable.

The best match is therefore:

**`modern_policy_relation_period_dependent`**

The most defensible substantive reading is:

> The real-policy starting point contains some useful OOS information, especially around the 2020–2022 inflation/policy transition, but the relationship is not stable across the predeclared modern subperiods. GPI/IPI trajectory features do not add stable incremental information on top of levels + stance.

---

## 6. Research decision

Issue #107 A1 does **not** pass the gate required to continue toward a production Policy Pressure Proxy.

Therefore:

- **DO NOT start A2** under the current preregistration.
- **DO NOT design a Phase B display formula.**
- **DO NOT add Hawkish / Neutral / Dovish buckets or thresholds.**
- **DO NOT retune 20 / 63 windows, V6.6 weights, thresholds, or axis formulas.**
- **DO NOT add JOLTS, yield curve, term premium, market-implied cuts, balance-sheet variables, asset returns, or portfolio outcomes to rescue this run.**
- **KEEP PR #108 Draft/Open/Unmerged.**

If a future stance-only or alternative policy-reaction hypothesis is pursued, it must be separately preregistered because the present 2015–2025 sample has now been inspected.

---

## 7. Durable output hashes

From the A1 manifest:

- monthly features: `70247798d820db1ff5bc5b1cd870520f4eaec9709b9367fbdd6890016de07392`
- expanding predictions: `865df197a0a2eaeddf8e276c8105fa0e2c82dbd4241e5fc1f60dece4e5b77329`
- rolling-96 predictions: `4ee90d7e7148095d011a10f3d99daa4bbf9bd73af7080ae56b4cf51a0e60d7c8`
- summary: `8b3ab6ff4a6e1a5873cb46f349529f3a83923dd2c14a58ef246b92443c122ece`
- incremental: `38a8c388bb734b8e860f82a0c7310b0663a0a385abfdc85def9b53c6ab938cc5`
- coefficients: `22563d163a468615654c178c6a23846a8457a4204be46e1a3450757743161098`

## Final conclusion

A1 falsifies the strong version of the Issue #107 hypothesis.

There is evidence that policy starting point matters in some eras, but not that a stable continuous reaction function can be recovered from frozen V6.6 levels + trajectory + real-policy stance across the full modern sample.

The preregistered trajectory layer fails to add stable OOS value.

**Final A1 verdict: `modern_policy_relation_period_dependent`.**
