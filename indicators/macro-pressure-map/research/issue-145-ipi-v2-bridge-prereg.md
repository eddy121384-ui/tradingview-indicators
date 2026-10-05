# Issue #145 Preregistration — IPI Bridge v2

Status: **FROZEN BEFORE ANY ISSUE #145 ANALOGUE-vs-EXACT BRIDGE METRIC**

Issue: #145  
Draft PR: #146  
Branch: `research/issue-145-ipi-bridge-v2`

This study follows:

- Issue #141: first monthly structural analogue bridge, formal verdict `signal_bridge_failed`;
- Issue #143: IPI attribution, formal verdict `ipi_attribution_valid`, holdout primary-cause label `commodity_proxy_primary`.

Issue #145 changes source semantics only. It does not retune the monthly scoring or state/turning logic.

## Hard firewall

Issue #145 is signal-only.

Do not fetch, join, inspect, summarize, or condition any choice on:

- SPY/TLT forward returns;
- S&P 500 / Treasury returns;
- Equity-minus-Duration spreads;
- Issue #136 payoff outcomes;
- 1990–2006 historical asset outcomes.

The only allowed validation targets are exact V6.6 signal objects:

- GPI;
- IPI;
- regime id;
- Regime-7 membership;
- Issue #136 asynchronous-turn trigger timing.

`outcome_data_loaded=false` is a hard result-contract requirement.

## Phase-A source freeze

Source-only workflow run:

`36959024098`

Source code head:

`9d65ae01b6b72eab6734c9420111b4e18e45b0c0`

Artifact digest:

`sha256:8cd46ba84f11195ee52da3343613429c42af30cbcbda43c937a2cc85c4ae539c`

The source-only run loaded neither exact V6.6 signals nor asset outcomes.

### DBIQ commodity-futures benchmark

Official Deutsche Bank DBIQ public REST source:

- index id: `95400`;
- index name: `DBIQ Optimum Yield Diversified Commodity Index Excess Return`;
- ticker: `DBLCDBCE`;
- benchmark family: Commodity Futures;
- historical inception: `1988-12-02`.

Official endpoints:

- metadata:
  `https://index.db.com/dbiq-web/rest/webdata/95400`
- graphData:
  `https://index.db.com/dbiq-web/rest/webdata/95400/graphData`
- monthlyReturns:
  `https://index.db.com/dbiq-web/rest/webdata/95400/monthlyReturns`
- returnData:
  `https://index.db.com/dbiq-web/rest/webdata/95400/returnData`

Source validation established before bridge metrics:

- 9,870 positive daily level rows;
- first daily date: 1988-12-02;
- first daily level: 100;
- 448 month-end levels through the frozen source end;
- frozen source end: `2026-03`;
- 447 official monthly-return cross-check rows;
- maximum absolute difference between return computed from official graphData month-end levels and official rounded monthlyReturns:
  `0.0049864533 percentage points`.

The v2 commodity level is the official DBIQ level itself. No wealth reconstruction from rounded monthly returns is needed.

### Historical gasoline

Series:

`MGASNYH — Conventional Gasoline Prices: New York Harbor, Regular`

Economic source:

U.S. Energy Information Administration via FRED.

Because direct FRED downloads were unreliable in CI, the frozen source is the commit-pinned gretl FRED database mirror:

- mirror repo: `gretl-project/gretl`;
- commit:
  `65dc8bdfb56feb64a19c36d38f696e7797591eb6`;
- frequency: monthly;
- first period: `1986-06`;
- frozen last period: `2026-03`;
- finite observations: 478.

Fail-closed identity anchors:

- 1986-06 = 0.420;
- 1986-07 = 0.340;
- 1986-08 = 0.426.

### Retained structural sources

From the frozen Issue #141 source family:

- Cleveland Fed 10Y expected inflation;
- World Bank monthly WTI.

Frozen source hashes:

- World Bank monthly XLSX:
  `9fdcfa8a2aed9a1bb545a10c1a5ce036c6a0acd4766f450424ca800b4b5a0225`
- Cleveland inflation-expectations XLSX:
  `20701ccf394d280fe1db38fa9def5628f2385dd0aef148ff989e33ff15caba95`

### Frozen normalized v2 source panel

Columns:

- DBIQ official month-end level;
- MGASNYH gasoline;
- World Bank WTI;
- Cleveland 10Y expected inflation.

Coverage:

- first complete period: `1988-12`;
- last complete period: `2026-03`;
- complete rows: 448.

Normalized CSV SHA256:

`848a7ba847b3637b3b8b4715df7b555598c6a7a3bcced76d85aed1e42b29ecaa`

The bridge workflow must rebuild the source panel and fail closed if this normalized SHA changes.

## Exact V6.6 bridge target

Reuse the frozen Issue #133 exact monthly snapshot.

Normalized exact signal SHA256:

`1d03923503e7fe82a69b033897484c48aa646279ecf70164d090ed62a5a70719`

Only:

- date;
- exact GPI;
- exact IPI;
- exact regime id

may be read.

No Issue #136 payoff data may be read.

## Frozen GPI analogue

Issue #145 does not redesign GPI.

Reuse Issue #141's frozen five-component monthly structural GPI exactly:

1. Fama/French SMB wealth;
2. equal-weight 12-industry breadth vs value-weight market;
3. Durables/Shops cyclical wealth vs NoDur defensive wealth;
4. Manufacturing wealth vs Utilities wealth;
5. World Bank Copper / Gold.

Equal-weight mean of the five frozen monthly component scores.

No GPI proxy or formula may change inside Issue #145.

## Frozen monthly component score

Reuse Issue #141 / #143 without modification.

For any positive monthly level series X:

- `zLen = 12`;
- `fastLen = 1`;
- `midLen = 3`;
- rolling standard deviation uses `ddof=1`;
- raw score weights = 0.5 level / 0.3 momentum / 0.2 direction;
- final score = `100 * tanh(raw / 2)`.

No affine scaling, calibration, lagging, sign flip, or target fitting is permitted.

## Frozen IPI v2

### Inflation-expectations component

Level:

Cleveland Fed 10Y expected inflation.

Component score:

frozen monthly component score.

Weight:

`0.35`.

### Broad-commodity component

Level:

official DBIQ `DBLCDBCE` month-end level.

Component score:

frozen monthly component score.

Weight:

`0.40`.

### Energy component

Two levels:

- World Bank monthly WTI;
- MGASNYH monthly gasoline.

Compute one frozen monthly component score for each.

Energy score:

arithmetic mean of WTI score and gasoline score.

Weight:

`0.25`.

### Final IPI v2

`IPI_V2 = 0.35 * expected_inflation_score + 0.40 * DBIQ_score + 0.25 * energy_score`.

A month is v2-eligible only when all four underlying component scores are finite.

No missing-component renormalization is allowed.

## Historical eligibility

The complete source panel begins 1988-12.

With the frozen 12/1/3 component-score warmup, the first month in which every IPI v2 component score is finite is frozen as:

`1990-02`.

Therefore the untouched historical signal window, if the bridge passes, is:

`1990-02 through 2006-12`.

No asset outcome may be joined inside Issue #145.

## Frozen regime and turning signal

Use exact V6.6 mild thresholds:

- positive axis: > +10;
- neutral axis: -10 through +10 inclusive;
- negative axis: < -10.

Use the exact V6.6 3x3 regime-id mapping.

Regime 7:

`GPI_A < -10 AND IPI_V2 < -10`.

Apply Issue #136's frozen asynchronous-turn definition:

For each axis X in {GPI_A, IPI_V2}:

`dX_t = X_t - X_(t-1)`.

A turning event occurs when:

- `dX_t > 0`; and
- `dX_(t-1) <= 0`.

At month t, `R7_ASYNC_TURN` requires:

1. current analogue regime = Regime 7;
2. GPI_A turning event occurred in {t,t-1,t-2};
3. IPI_V2 turning event occurred in {t,t-1,t-2}.

Only the first completion inside each contiguous analogue Regime-7 episode is a trigger.

## Bridge periods

Development diagnostic:

`2007-01 through 2016-12`.

Primary untouched holdout:

`2017-01 through 2026-03`.

Holdout temporal subsegments:

- 2017-01 through 2019-12;
- 2020-01 through 2022-12;
- 2023-01 through 2026-03.

Development results may not alter the v2 design.

## Bridge metrics

Use Issue #141's metric definitions without modification.

### Axis fidelity

- GPI Pearson level correlation;
- IPI Pearson level correlation;
- GPI one-month slope-sign agreement;
- IPI one-month slope-sign agreement.

Correlation is evaluable with at least 12 paired months.

Slope sign uses exact mathematical sign {-1,0,+1} and is evaluable with at least 12 paired consecutive-month observations.

### State fidelity

- exact 3x3 regime-id agreement;
- R7 precision;
- R7 recall.

Zero precision/recall denominator = unevaluable and fails closed.

### Trigger fidelity

One-to-one exact-vs-analogue trigger matching within +/-1 calendar month.

Deterministic matching:

1. sort eligible pairs by absolute month distance;
2. then exact month;
3. then analogue month;
4. greedily accept unused exact/analogue pairs.

Report:

- precision;
- recall;
- F1;
- analogue/exact trigger-count ratio.

## Primary bridge gate

Issue #145 deliberately reuses the **same frozen Issue #141 pass criteria**. No gate is loosened after the #141 failure.

Verdict `signal_bridge_v2_passed` only if all are true:

1. holdout has at least 60 common eligible months;
2. holdout contains at least 4 exact asynchronous-turn triggers;
3. GPI Pearson correlation >= 0.70;
4. IPI Pearson correlation >= 0.70;
5. GPI slope-sign agreement >= 0.70;
6. IPI slope-sign agreement >= 0.70;
7. exact 3x3 regime agreement >= 0.60;
8. R7 precision >= 0.60;
9. R7 recall >= 0.60;
10. trigger F1 within +/-1 month >= 0.60;
11. trigger-count ratio between 0.50 and 2.00 inclusive;
12. every evaluable holdout temporal subsegment has regime agreement >= 0.45.

A temporal subsegment is evaluable with at least 12 common eligible months.

If gates 1 or 2 fail:

`signal_bridge_v2_inconclusive_sample`.

Otherwise if any fidelity gate fails:

`signal_bridge_v2_failed`.

There is no suggestive rescue verdict.

## Descriptive comparison to Issue #141

After the v2 bridge verdict is computed, report descriptive changes versus the frozen Issue #141 holdout:

Issue #141 holdout reference:

- GPI correlation: 0.8980438446;
- IPI correlation: 0.6829508192;
- GPI slope-sign agreement: 0.8608695652;
- IPI slope-sign agreement: 0.6956521739;
- regime agreement: 0.4568965517;
- R7 precision: 0.7222222222;
- R7 recall: 0.5000000000;
- trigger F1: 0.1818181818.

This comparison cannot alter the formal v2 gate.

## Historical signal output

The evaluator may emit 1990-02 through 2006-12 analogue signals regardless of verdict for audit.

Every historical row must carry:

`validated_for_outcome_testing = (bridge_verdict == "signal_bridge_v2_passed")`.

No future study may join historical asset outcomes unless that flag is true.

## Anti-tuning rules

After the first Issue #145 bridge metric is observed, do not:

- replace DBIQ with another commodity index;
- change DBIQ index id/ticker;
- change gasoline source;
- revert gasoline to natural gas;
- change Cleveland expected inflation;
- change WTI source;
- change 12/1/3;
- change score formula weights;
- change IPI 0.35/0.40/0.25 weights;
- change GPI analogue;
- rescale or calibrate GPI/IPI;
- change +/-10 thresholds;
- change development/holdout dates;
- change trigger logic or matching tolerance;
- loosen any bridge gate.

Any such idea requires a new preregistered issue.

## Product and outcome boundary

`production_authorized=false`.

No V6.6 or V6.7 production change is authorized.

No historical Equity-vs-Duration outcome may be inspected inside Issue #145.
