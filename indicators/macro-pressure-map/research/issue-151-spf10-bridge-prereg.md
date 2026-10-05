# Issue #151 Preregistration — SPF 10Y CPI Inflation Expectations Bridge

Status: **FROZEN BEFORE ANY ISSUE #151 ANALOGUE-vs-EXACT BRIDGE METRIC**

Issue: #151  
Draft PR: #152  
Branch: `research/issue-151-spf10-bridge`

This study follows the best frozen long-history bridge to date, Issue #145:

- formal verdict: `signal_bridge_v2_failed`;
- holdout IPI correlation: 0.8998539583;
- IPI slope-sign agreement: 0.8181818182;
- regime agreement: 0.5675675676;
- R7 precision: 0.8000000000;
- R7 recall: 0.6153846154;
- trigger F1: 0.5000000000.

Issue #149's Cleveland expected-inflation + inflation-risk-premium construction was worse than Issue #145 and is not inherited.

Issue #151 changes exactly one source role from Issue #145:

Cleveland 10Y expected inflation -> Philadelphia Fed SPF median 10Y CPI inflation forecast.

## Hard firewall

Issue #151 is signal-only.

Do not fetch, join, inspect, summarize, or condition any choice on:

- SPY/TLT forward returns;
- S&P 500 / Treasury returns;
- Equity-minus-Duration spreads;
- Issue #136 payoff outcomes;
- 1993–2006 historical asset outcomes.

Only exact V6.6 signal objects may be used as bridge targets.

`outcome_data_loaded=false` is a hard result-contract requirement.

## Phase-A source freeze

Source-only workflow run:

`37264957977`

Source head:

`d006572bd02ce447af4c0e2dd812310062198330`

Artifact digest:

`sha256:5a2f681c340f0de0a6bc8eaa56143b2d3731f2b017cf0e1bb178abd8abceb9b6`

No exact V6.6 signal or asset outcome was loaded in Phase A.

### Official SPF forecast source

Federal Reserve Bank of Philadelphia Survey of Professional Forecasters.

Official workbook:

`Inflation.xlsx`

Raw SHA256:

`2bef852b0b4c4365ce9d38796c408ecb2648f024b2cc1d40a8c1426afe62e2e5`

Frozen sheet:

`INFLATION`

Frozen target column:

`INFCPI10YR`

Meaning:

median annual-average CPI inflation forecast over the current and next nine years.

Survey coverage:

- first non-missing survey: `1991:Q4`;
- last frozen survey: `2026:Q3`;
- 140 survey observations.

### Official release-date source

Philadelphia Fed SPF historical deadline / news-release file.

Raw SHA256:

`c5f4c4dc349068ba9dc1f421c68474be26d0fe613fff83f70aa41eed96696ee3`

Parsed release-date coverage:

- first survey row: `1990:Q2`;
- last frozen survey row: `2026:Q3`;
- 146 release rows.

## Frozen causal quarterly-to-monthly mapping

The survey quarter label is **not** the availability date.

For each completed calendar month end:

1. include only SPF forecasts whose official public news-release date is <= that month end;
2. use the latest such `INFCPI10YR`;
3. carry it forward unchanged until the next public release;
4. do not interpolate between surveys;
5. do not backfill a new survey value to the beginning of its survey quarter.

This rule handles actual release anomalies causally. For example, the 2026:Q1 SPF released on 2026-03-06 becomes available in March 2026, not February.

Frozen causal monthly series:

- first month: `1991-11`;
- last month: `2026-08`;
- rows: 418;
- source surveys used: 140.

Normalized causal monthly CSV SHA256:

`bfd9a8e76d882007a80584a439289f456bf06999223d2f1f30f85bb02f4e65e5`

Deterministic gzip SHA256:

`8d21fb8a3b346d160a63d8b67ac1fe454b27a20605388033f886cf3406681c3c`

The evaluator must load the repository-frozen causal monthly series and fail closed on hash drift.

## Frozen inherited Issue #145 inputs

Do not change:

- structural GPI analogue;
- DBIQ `DBLCDBCE` broad-commodity month-end level;
- World Bank monthly WTI;
- MGASNYH gasoline;
- monthly score lengths 12 / 1 / 3;
- rolling standard deviation `ddof=1`;
- component raw weights 0.5 level / 0.3 momentum / 0.2 direction;
- IPI weights 0.35 / 0.40 / 0.25;
- exact V6.6 +/-10 state thresholds;
- exact 3x3 regime mapping;
- Issue #136 asynchronous-turn definition;
- +/-1 month deterministic trigger matching.

## Frozen SPF component score

Apply the inherited monthly component-score formula directly to the positive SPF 10Y CPI forecast level.

No transformation of the survey level is allowed other than the existing component-score formula.

In particular, do not:

- interpolate quarterly forecasts;
- difference the SPF level before scoring;
- smooth the SPF level;
- add an inflation risk premium;
- convert CPI inflation to PCE inflation;
- apply a fitted scale or intercept;
- lead or lag the series.

## Frozen IPI SPF bridge

`IPI_SPF = 0.35 * SPF10_score + 0.40 * DBIQ_score + 0.25 * energy_score`

where:

- `SPF10_score` = frozen monthly score of causal SPF `INFCPI10YR`;
- `DBIQ_score` = frozen Issue #145 commodity score;
- energy score = arithmetic mean of frozen World Bank WTI and MGASNYH gasoline scores.

No missing-component renormalization is allowed.

## Historical eligibility

The causal SPF monthly series begins 1991-11.

Under the frozen 12/1/3 component score, the first finite SPF component score is:

`1993-01`.

Therefore the untouched historical signal window, if the bridge passes, is frozen as:

`1993-01 through 2006-12`.

No historical asset outcome may be joined inside Issue #151.

## Exact V6.6 bridge target

Reuse frozen Issue #133 exact monthly snapshot.

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

The holdout end remains 2026-03 because the inherited frozen Issue #145 DBIQ/WTI/gasoline panel ends there.

Holdout temporal subsegments:

- 2017-01 through 2019-12;
- 2020-01 through 2022-12;
- 2023-01 through 2026-03.

Development results cannot alter the design.

## Bridge metrics

Use the exact Issue #141 / #145 metric implementations:

- GPI Pearson level correlation;
- IPI Pearson level correlation;
- GPI one-month slope-sign agreement;
- IPI one-month slope-sign agreement;
- exact 3x3 regime-id agreement;
- R7 precision;
- R7 recall;
- asynchronous-turn trigger precision / recall / F1 within +/-1 month;
- analogue/exact trigger-count ratio;
- regime agreement by holdout temporal subsegment.

Slope sign uses exact mathematical sign {-1,0,+1}.

## Formal bridge gate

Issue #151 reuses the same 12 frozen pass criteria as Issues #141 and #145.

Verdict `signal_bridge_spf_passed` only if all are true:

1. holdout common eligible months >=60;
2. exact holdout asynchronous-turn triggers >=4;
3. GPI Pearson correlation >=0.70;
4. IPI Pearson correlation >=0.70;
5. GPI slope-sign agreement >=0.70;
6. IPI slope-sign agreement >=0.70;
7. exact 3x3 regime agreement >=0.60;
8. R7 precision >=0.60;
9. R7 recall >=0.60;
10. trigger F1 within +/-1 month >=0.60;
11. trigger-count ratio between 0.50 and 2.00 inclusive;
12. every evaluable holdout temporal subsegment has regime agreement >=0.45.

If gates 1 or 2 fail:

`signal_bridge_spf_inconclusive_sample`.

Otherwise if any fidelity gate fails:

`signal_bridge_spf_failed`.

There is no suggestive rescue verdict.

## Frozen descriptive comparison to Issue #145

After the formal SPF verdict is computed, report changes versus Issue #145:

- IPI correlation: 0.8998539583;
- IPI slope-sign agreement: 0.8181818182;
- regime agreement: 0.5675675676;
- R7 precision: 0.8000000000;
- R7 recall: 0.6153846154;
- trigger F1: 0.5000000000.

This comparison cannot alter the formal gate.

## Additional descriptive diagnostics

Report, without selection or retuning:

- fraction of causal monthly SPF levels unchanged from prior month;
- months in which a new SPF survey becomes effective;
- exact vs SPF-bridge trigger pairs;
- development and holdout results separately.

These are descriptive only.

## Historical signal output

The evaluator may emit analogue signals for 1993-01 through 2006-12 for audit.

Every row must carry:

`validated_for_outcome_testing = (bridge_verdict == "signal_bridge_spf_passed")`.

No downstream study may join historical asset outcomes unless the flag is true.

## Anti-tuning rules

After the first Issue #151 bridge metric is observed, do not:

- change median to mean;
- switch CPI10 to PCE10;
- interpolate quarterly forecasts;
- backfill to quarter start;
- use survey deadline instead of public release date;
- add a fixed publication lag;
- change SPF horizon;
- combine SPF with Cleveland;
- rescale SPF;
- change DBIQ / WTI / gasoline;
- change 12/1/3;
- change IPI weights;
- change +/-10 thresholds;
- change bridge periods;
- change trigger logic or matching tolerance;
- loosen any gate.

Any alternative requires a new preregistered issue.

## Product / outcome boundary

`production_authorized=false`.

No V6.6/V6.7 production change is authorized.

Historical asset outcomes remain forbidden inside Issue #151.
