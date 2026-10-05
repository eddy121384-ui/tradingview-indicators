# Issue #149 Preregistration — Inflation Compensation Bridge v3

Status: **FROZEN BEFORE ANY ISSUE #149 ANALOGUE-vs-EXACT BRIDGE METRIC**

Issue: #149  
Draft PR: #150  
Branch: `research/issue-149-inflation-comp-v3`

Issue #149 follows the frozen Issue #145 result:

- formal verdict: `signal_bridge_v2_failed`;
- holdout IPI correlation: 0.89985;
- holdout IPI slope-sign agreement: 81.82%;
- holdout regime agreement: 56.76%;
- holdout R7 precision / recall: 80.00% / 61.54%;
- holdout trigger F1: 50.00%.

Issue #149 changes exactly one semantic input: the inflation-expectations leg.

## Hard firewall

Issue #149 is signal-only.

Do not fetch, join, inspect, summarize, or condition any choice on:

- SPY/TLT forward returns;
- S&P 500 / Treasury returns;
- Equity-minus-Duration spreads;
- Issue #136 payoff outcomes;
- 1990–2006 historical asset outcomes.

The only validation targets are exact V6.6 GPI/IPI/regime/turning signals.

`outcome_data_loaded=false` is a hard result-contract requirement.

## Phase-A source freeze

Source-only workflow run:

`37258981774`

Source head:

`2cdf1bb5eeebe43a5ae60b212348c55a833cb690`

Artifact digest:

`sha256:b679efc77f8eee89f6fb2c28bdffe97f3680eee6ea281341e6e4765cadace2fd`

No exact V6.6 signal or asset outcome was loaded.

Official Cleveland Fed workbook SHA256:

`20701ccf394d280fe1db38fa9def5628f2385dd0aef148ff989e33ff15caba95`

Frozen sheet:

`Ten-year Expected Chart`

Frozen columns:

- `Model Output Date`
- `10 year Expected Inflation`
- `Inflation Risk Premium`

Coverage:

- first finite month: `1982-01`;
- last finite month: `2026-09`;
- no missing values in the primary compensation series.

Normalized source CSV SHA256:

`a07dbdb377a2ae1dedc7a176d43b20b14d951caddde776aef18dfcf810256a10`

## Economic definition

The exact V6.6 input is 10Y market breakeven inflation.

Market breakeven is an inflation-compensation object rather than a pure expectations object.

The Cleveland Fed publishes separate model estimates of:

- expected inflation;
- inflation risk premium;
- real risk premium;
- real interest rate.

Primary v3 inflation level is frozen as:

`CLEVELAND_COMP10_t = EXPECTED_INFLATION_10Y_t + INFLATION_RISK_PREMIUM_10Y_t`

Coefficients are exactly +1 and +1.

No intercept, scaling coefficient, regression, lag, sign flip, clipping, winsorization, or calibration to T10YIE is permitted.

The source-only audit established that `CLEVELAND_COMP10` is strictly positive over the full frozen history, so the existing positive-level component-score formula is applicable without modification.

## Frozen elements inherited from Issue #145

Do not change:

- Issue #141 structural GPI analogue;
- DBIQ DBLCDBCE broad-commodity level;
- World Bank WTI;
- MGASNYH gasoline;
- monthly score lengths 12 / 1 / 3;
- rolling std convention `ddof=1`;
- component raw weights 0.5 level / 0.3 momentum / 0.2 direction;
- IPI weights 0.35 / 0.40 / 0.25;
- exact V6.6 +/-10 state thresholds;
- exact 3x3 regime mapping;
- Issue #136 asynchronous-turn rule;
- +/-1 month deterministic trigger matching.

## Frozen IPI v3

### Inflation-compensation component

Level:

`CLEVELAND_COMP10`.

Component score:

frozen monthly 12/1/3 component score.

Weight:

`0.35`.

### Broad commodity

Official DBIQ `DBLCDBCE` month-end level.

Weight:

`0.40`.

### Energy

Frozen Issue #145 energy pair:

- World Bank WTI;
- MGASNYH gasoline.

Energy score:

arithmetic mean of their separate monthly component scores.

Weight:

`0.25`.

### Final IPI

`IPI_V3 = 0.35 * COMP10_score + 0.40 * DBIQ_score + 0.25 * energy_score`.

No missing-component renormalization is allowed.

## Historical eligibility

The inherited Issue #145 source-common panel begins 1988-12.

The inflation-compensation source begins in 1982 and therefore does not shorten the v2 window.

The first fully scored v3 IPI month is frozen as:

`1990-02`.

Untouched historical signal window, if v3 passes:

`1990-02 through 2006-12`.

No historical asset outcome may be joined inside Issue #149.

## Exact V6.6 target

Reuse the frozen Issue #133 monthly exact snapshot.

Normalized exact signal SHA256:

`1d03923503e7fe82a69b033897484c48aa646279ecf70164d090ed62a5a70719`

Only:

- date;
- exact GPI;
- exact IPI;
- exact regime id

may be read.

## Bridge periods

Development diagnostic:

`2007-01 through 2016-12`.

Primary untouched holdout:

`2017-01 through 2026-03`.

Holdout temporal subsegments:

- 2017-01 through 2019-12;
- 2020-01 through 2022-12;
- 2023-01 through 2026-03.

Development results cannot alter the v3 design.

## Frozen bridge metrics and gates

Use the exact Issue #145 / Issue #141 definitions.

Metrics:

- GPI level Pearson correlation;
- IPI level Pearson correlation;
- GPI one-month slope-sign agreement;
- IPI one-month slope-sign agreement;
- exact 3x3 regime agreement;
- R7 precision;
- R7 recall;
- asynchronous-turn trigger precision / recall / F1 within +/-1 month;
- analogue/exact trigger-count ratio;
- regime agreement by holdout subsegment.

Verdict `signal_bridge_v3_passed` only if all are true:

1. holdout common eligible months >=60;
2. exact holdout triggers >=4;
3. GPI correlation >=0.70;
4. IPI correlation >=0.70;
5. GPI slope-sign agreement >=0.70;
6. IPI slope-sign agreement >=0.70;
7. exact 3x3 regime agreement >=0.60;
8. R7 precision >=0.60;
9. R7 recall >=0.60;
10. trigger F1 within +/-1 month >=0.60;
11. trigger-count ratio between 0.50 and 2.00 inclusive;
12. every evaluable temporal subsegment regime agreement >=0.45.

If gates 1 or 2 fail:

`signal_bridge_v3_inconclusive_sample`.

Otherwise if any fidelity gate fails:

`signal_bridge_v3_failed`.

There is no suggestive rescue verdict.

## Frozen descriptive comparison to Issue #145

After the v3 verdict is computed, report the change versus frozen Issue #145 holdout:

- IPI correlation: 0.8998539583;
- IPI slope-sign agreement: 0.8181818182;
- regime agreement: 0.5675675676;
- R7 precision: 0.8000000000;
- R7 recall: 0.6153846154;
- trigger F1: 0.5000000000.

This comparison is descriptive and cannot alter the gate.

## Anti-tuning rules

After the first Issue #149 bridge metric is observed, do not:

- change +1/+1 compensation formula;
- add real risk premium;
- subtract real risk premium;
- switch to Michigan expectations;
- switch to SPF expectations;
- use another Cleveland horizon;
- scale or center the compensation level;
- change DBIQ / WTI / gasoline;
- change 12/1/3;
- change IPI weights;
- change +/-10 thresholds;
- change bridge periods;
- change trigger rules;
- change matching tolerance;
- loosen any gate.

Any alternative requires a new preregistered issue.

## Product / outcome boundary

`production_authorized=false`.

No V6.6/V6.7 production change is authorized.

Historical asset outcomes remain forbidden inside Issue #149.
