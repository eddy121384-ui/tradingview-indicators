# Issue #143 — Historical IPI Bridge Attribution Finding

Status: **attribution valid; signal-only; no historical outcome authorization**

Issue: #143  
Draft PR: #144  
Branch: `research/issue-143-ipi-attribution`

## Research integrity / ordering

Issue #143 was intentionally separated into source acquisition and attribution.

Source-only acquisition succeeded before any exact-IPI attribution metric was observed:

- source run: `36954294127`
- source code head: `0c16847c07321648422cbc718a480cc32a1f2236`
- exact V6.6 signal loaded: false
- asset outcome loaded: false

The attribution design was then preregistered:

- preregistration commit:
  `0b98f95ec9e3a23f98c17cdbf6f3a98ff7610e5b`

Only afterward was the evaluator implemented:

- evaluator commit:
  `4d9107c13742c0d03ee0529fa30d29917b6bca48`

Final validated attribution run:

- workflow run: `36954642736`
- evaluator head: `9f318f790fe9869ae655d76292557eb8421c6ed0`
- artifact digest:
  `sha256:f71ea9a312bae1f7b8d07ca3fac49b187828ae3e94844aa13c50342f3e41a960`

Hard firewall remained intact:

- `outcome_data_loaded=false`
- `historical_outcome_testing_authorized=false`
- `production_authorized=false`

No 1984–2006 Equity-vs-Duration outcome was inspected.

## Formal verdict

**`ipi_attribution_valid`**

Formal preregistered primary-cause label:

**`commodity_proxy_primary`**

This label is based on the frozen 2017–2026-08 holdout damage-score rules.

It does not mean the commodity proxy is the only problem. The Cleveland expected-inflation substitution is also materially damaging, and the relative ordering differs in the earlier development interval.

## 1. D0 public exact-input anchor passes all gates

D0 uses:

- T10YIE public mirror splice;
- Yahoo DBC;
- Yahoo CL=F;
- Yahoo RB=F;
- original V6.6 daily 252/20/63 score;
- month-end sampling.

Holdout 2017-01 through 2026-08:

- common eligible months: 116
- IPI correlation: **0.99397**
- IPI slope-sign agreement: **88.70%**
- IPI 3-state agreement: **96.55%**
- exact 3x3 regime agreement, using exact GPI: **96.55%**
- R7 precision: **96.15%**
- R7 recall: **96.15%**
- exact async triggers: 6
- D0 async triggers: 8
- matched within +/-1 month: 6
- trigger F1: **85.71%**

Every frozen D0 gate passes:

1. >=100 common months — PASS
2. correlation >=0.90 — PASS
3. slope agreement >=0.80 — PASS
4. IPI-state agreement >=0.75 — PASS
5. regime agreement >=0.70 — PASS
6. R7 precision >=0.65 — PASS
7. R7 recall >=0.65 — PASS
8. trigger F1 >=0.60 — PASS

This establishes that the attribution anchor is adequate.

The public-feed approximation is not identical to TradingView, but it is sufficiently faithful for the preregistered decomposition.

## 2. Frequency / monthly-score translation is not the main problem

M0 uses the same public economic inputs as D0 but converts them to completed-month levels and applies the frozen Issue #141 12/1/3 monthly score.

Holdout M0:

- IPI correlation: **0.98644**
- slope agreement: **91.30%**
- IPI-state agreement: **95.69%**
- regime agreement: **95.69%**
- R7 precision: **92.59%**
- R7 recall: **96.15%**
- trigger F1: **85.71%**

The preregistered D0 -> M0 damage score is only:

**0.00863**

Slope agreement actually improves and all six exact holdout triggers are matched by M0.

Therefore the failed Issue #141 IPI bridge is **not primarily caused by translating the daily 252/20/63 score into the monthly 12/1/3 score**.

This materially narrows the problem.

## 3. One-at-a-time source substitutions

### M-BE — T10YIE -> Cleveland 10Y expected inflation

Holdout:

- IPI correlation: **0.92007**
- slope agreement: **84.35%**
- state agreement: **79.31%**
- regime agreement: **79.31%**
- R7 precision: **91.67%**
- R7 recall: **84.62%**
- trigger F1: **71.43%**

Damage score vs M0:

**0.10443**

This is a material degradation.

Cleveland expected inflation is therefore not a neutral historical substitute for market breakeven inflation in the V6.6 IPI construction.

### M-COM — DBC -> World Bank equal-weight spot commodity basket

Holdout:

- IPI correlation: **0.89366**
- slope agreement: **85.22%**
- state agreement: **72.41%**
- regime agreement: **72.41%**
- R7 precision: **80.77%**
- R7 recall: **80.77%**
- trigger F1: **76.92%**

Damage score vs M0:

**0.13988**

This is the largest frozen atomic holdout damage score.

The formal primary-cause label is therefore:

`commodity_proxy_primary`.

The World Bank equal-weight geometric spot-price basket does not adequately preserve the DBC role inside V6.6 IPI.

### M-OIL — Yahoo WTI futures -> World Bank WTI

Holdout:

- IPI correlation: **0.98792**
- slope agreement: **91.30%**
- state agreement: **95.69%**
- regime agreement: **95.69%**
- R7 precision: **96.15%**
- R7 recall: **96.15%**
- trigger F1: **92.31%**

Damage score:

**0.00000**

Under the frozen metric, the World Bank WTI replacement causes no positive damage and in several diagnostics slightly improves fidelity.

WTI provider choice is not an important cause of the failed #141 bridge.

### M-GAS — RBOB gasoline -> World Bank US natural gas

Holdout:

- IPI correlation: **0.97146**
- slope agreement: **89.57%**
- state agreement: **88.79%**
- regime agreement: **88.79%**
- R7 precision: **91.30%**
- R7 recall: **80.77%**
- trigger F1: **83.33%**

Damage score:

**0.05155**

Natural gas is an imperfect substitute for gasoline and causes meaningful R7-recall damage, but it is materially less damaging than the broad-commodity or breakeven substitutions.

## 4. Full Issue #141 IPI substitution

M-ALL combines:

- Cleveland expected inflation;
- World Bank equal-weight commodity basket;
- World Bank WTI;
- World Bank US natural gas;
- monthly 12/1/3 score.

Holdout:

- IPI correlation: **0.68295**
- slope agreement: **69.57%**
- state agreement: **62.07%**
- regime agreement: **62.07%**
- R7 precision: **75.00%**
- R7 recall: **69.23%**
- trigger F1: **57.14%**

Total M0 -> M-ALL damage score:

**0.27488**

This reproduces the weak IPI fidelity seen in Issue #141 when IPI is isolated from GPI.

The degradation is therefore attributable to the combined historical source substitutions, not to the monthly-score translation itself.

## 5. Holdout damage ranking

Frozen atomic damage scores:

1. commodity proxy: **0.13988**
2. breakeven proxy: **0.10443**
3. gasoline proxy: **0.05155**
4. frequency / score translation: **0.00863**
5. WTI provider: **0.00000**

The top-minus-second gap is approximately **0.03545**, which exceeds the preregistered 0.03 separation threshold.

Therefore the deterministic holdout label is:

`commodity_proxy_primary`.

## 6. Important temporal qualification

The development interval 2007–2016 shows a different source-damage ordering.

Development damage scores:

- breakeven proxy: approximately **0.13917**
- commodity proxy: approximately **0.04771**
- frequency translation: approximately **0.02331**
- gasoline proxy: approximately **0.01737**
- WTI provider: approximately **0.00493**

In development, Cleveland expected inflation is the largest source substitution problem.

In the untouched holdout, the World Bank commodity basket becomes the largest.

Therefore the robust economic interpretation is not:

> only the commodity basket is wrong.

It is:

> the Issue #141 IPI bridge is primarily damaged by the **commodity-basket and inflation-expectations proxy family**, with their relative importance varying by era.

The preregistered formal holdout label remains `commodity_proxy_primary`.

## 7. Trigger-timing evidence

Exact holdout Issue #136 triggers:

- 2018-10
- 2019-05
- 2020-04
- 2022-08
- 2023-03
- 2025-04

M0 matches all six within +/-1 month, and in fact all six are same-month matches.

M-BE matches five of six.

M-COM matches five of six, but three of the five are shifted by one month.

M-OIL matches all six same-month.

M-GAS matches five of six.

M-ALL matches four of six.

This again isolates the failure to the proxy substitutions rather than monthly timing compression.

## 8. Interaction

The combined M-ALL degradation is not a simple arithmetic sum of one-at-a-time effects.

Preregistered interaction residuals vary by metric:

- IPI correlation: +0.13084
- slope agreement: +0.06957
- IPI-state agreement: -0.12931
- regime agreement: -0.12931
- R7 precision: +0.07116
- R7 recall: -0.15385
- trigger F1: +0.09707

This indicates meaningful nonlinear interaction once several proxy substitutions are combined.

Per preregistration, interaction is descriptive and does not alter the primary-cause label.

## Research implication

Issue #143 successfully identifies why Issue #141 failed.

The main lesson is:

- **keep the monthly score translation**;
- **World Bank WTI is acceptable** for this bridge role;
- do not treat the World Bank equal-weight spot basket as a faithful DBC substitute;
- do not treat Cleveland expected inflation as a neutral T10YIE substitute;
- natural gas is usable only with caution and is not the largest problem.

The next study should be a new, separately preregistered **IPI Bridge v2 source-design study**.

It should seek:

1. a historical broad-commodity series structurally closer to DBC / DBIQ diversified commodity futures;
2. a pre-2003 inflation-expectations representation closer to market breakeven behavior;
3. optionally a gasoline/predecessor energy series closer to the original energy-pressure semantic.

It should keep:

- the monthly 12/1/3 score;
- the exact +/-10 state thresholds;
- the Issue #136 turning rule;
- the signal-only firewall.

No historical asset outcome may be inspected until a redesigned bridge passes a new untouched signal-fidelity gate.

## Product boundary

Issue #143 authorizes no production change.

It does not alter Issue #141's failed verdict.

It does not authorize the nine 1984–2006 diagnostic trigger dates for outcome testing.

`historical_outcome_testing_authorized=false`

`production_authorized=false`
