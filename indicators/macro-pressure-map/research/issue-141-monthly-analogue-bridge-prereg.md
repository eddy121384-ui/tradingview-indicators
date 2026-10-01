# Issue #141 Preregistration — Monthly Structural Analogue Signal Bridge

Status: **FROZEN BEFORE ANY ANALOGUE-vs-EXACT BRIDGE METRIC**

Issue: #141  
Draft PR: #142  
Branch: `research/issue-141-signal-bridge`

## Research firewall

Issue #141 is signal-only.

No Equity-vs-Duration outcome has been loaded in Phase A and none may be loaded in the bridge evaluator.

Forbidden until a future issue:

- S&P 500 forward returns;
- Treasury forward returns;
- SPY/TLT forward returns;
- Equity-minus-Duration spreads;
- any payoff-conditioned proxy selection.

The only bridge target is exact V6.6 signal behavior.

## Phase A source freeze

Source-only acquisition run #6:

- workflow run: `36840750891`;
- source code head: `022fb22aa1d7e938ec96f25ed799f758e789e927`;
- `outcome_data_loaded=false`;
- `exact_v66_signal_loaded=false`.

Frozen raw-source hashes from the source audit:

- Fama/French 3 Factors monthly ZIP:
  `593f4fbef03181bc0b22ff6292f217689dd1fb79355049ca905d95b262040a66`
- Fama/French 12 Industry Portfolios monthly ZIP:
  `309eb6b2bdbb5bc45f039b9814753b079cd40bd4038ffda9afb6c5e0563fd120`
- World Bank Pink Sheet monthly XLSX:
  `9fdcfa8a2aed9a1bb545a10c1a5ce036c6a0acd4766f450424ca800b4b5a0225`
- Cleveland Fed inflation-expectations XLSX:
  `20701ccf394d280fe1db38fa9def5628f2385dd0aef148ff989e33ff15caba95`

The bridge evaluator must fail closed if downloaded raw bytes differ from these hashes.

## Source coverage established before bridge metrics

- Fama/French factors and 12 industries: 1926-07 through 2026-08.
- World Bank Copper / Gold / Aluminum / Wheat / Maize / Coffee / Sugar / US natural gas: 1960-01 through 2026-08.
- World Bank WTI: 1982-01 through 2026-08.
- Cleveland Fed 10Y expected inflation: 1982-01 through 2026-09.

Therefore the source-common structural analogue can be fully formed from 1982 onward. The untouched historical signal window is conservatively frozen as **1984-01 through 2006-12**, after monthly score warmup.

## Exact V6.6 bridge target

Reuse the frozen Issue #133 exact monthly V6.6 snapshot used by Issue #136.

Normalized exact signal SHA256:

`1d03923503e7fe82a69b033897484c48aa646279ecf70164d090ed62a5a70719`

The bridge evaluator may read only:

- date;
- exact GPI;
- exact IPI;
- exact regime id.

It may not read Issue #136 asset outcomes.

Exact bridge window starts 2007-01.

## Frozen monthly structural analogue

No parameters are estimated from the exact bridge target.

There is no affine calibration, regression, threshold fitting, sign flip, lag optimization, or proxy selection after bridge metrics are observed.

### Monthly component-score translation

For any positive monthly level series `X_t`:

- `zLen = 12`;
- `fastLen = 1`;
- `midLen = 3`.

Define:

`lvl_t = zscore(X_t, 12)`

`rocFast_t = pct_change(X_t, 1) * 100`

`rocMid_t = pct_change(X_t, 3) * 100`

`momRaw_t = 0.6 * rocFast_t + 0.4 * rocMid_t`

`mom_t = zscore(momRaw_t, 12)`

`dirRaw_t = (SMA_1(X)_t - SMA_3(X)_t) / stdev_12(X)_t`

`dir_t = tanh(dirRaw_t)`

`raw_t = 0.5 * lvl_t + 0.3 * mom_t + 0.2 * dir_t`

`score_t = 100 * tanh(raw_t / 2)`

Population-vs-sample standard-deviation convention must match pandas rolling default `ddof=1` consistently for every analogue component. This convention is frozen before bridge outcomes.

Missing component scores are not dynamically renormalized in the primary analogue. A month is primary-eligible only when **all frozen primary components are available**.

### GPI structural roles

Five equal-weight component scores:

1. **Small-cap relative strength**
   - source: Fama/French SMB monthly factor;
   - build a positive relative-wealth level:
     `SMB_WEALTH_t = SMB_WEALTH_(t-1) * (1 + SMB_t/100)`;
   - component score: monthly score of `SMB_WEALTH`.

2. **Equal-weight breadth vs value-weight market**
   - source: 12 Fama/French industry portfolio returns + Fama/French market return;
   - monthly equal-industry return:
     simple arithmetic mean of all 12 industry returns;
   - monthly market return:
     `Mkt-RF + RF`;
   - build separate positive wealth indices and use:
     `BREADTH_LEVEL = INDUSTRY_EW_WEALTH / MARKET_WEALTH`;
   - component score: monthly score of `BREADTH_LEVEL`.

3. **Cyclical / defensive**
   - cyclical monthly return:
     arithmetic mean of `Durbl` and `Shops`;
   - defensive monthly return:
     `NoDur`;
   - build positive wealth indices;
   - level = cyclical wealth / defensive wealth;
   - component score of that level.

4. **Manufacturing / utilities**
   - source returns: `Manuf` and `Utils`;
   - build positive wealth indices;
   - level = manufacturing wealth / utilities wealth;
   - component score of that level.

5. **Copper / Gold**
   - World Bank Pink Sheet monthly prices;
   - level = `Copper / Gold`;
   - component score of that level.

Structural GPI:

`GPI_A = mean(score1, score2, score3, score4, score5)`.

### IPI structural roles

1. **10Y expected inflation**
   - Cleveland Fed `10 year Expected Inflation`;
   - monthly level component score;
   - weight 0.35.

2. **Broad commodity basket**
   - World Bank Pink Sheet monthly prices:
     - Crude oil, WTI;
     - Natural gas, US;
     - Aluminum;
     - Copper;
     - Wheat, US HRW;
     - Maize;
     - Coffee, Arabica;
     - Sugar, world.
   - basket level = equal-weight geometric mean of the eight positive price series:
     `exp(mean(log(price_i)))`;
   - component score;
   - weight 0.40.

3. **Energy pressure**
   - World Bank `Crude oil, WTI` and `Natural gas, US`;
   - compute a separate monthly component score for each;
   - energy score = arithmetic mean of WTI score and US natural-gas score;
   - weight 0.25.

Structural IPI:

`IPI_A = 0.35 * expected_inflation_score + 0.40 * commodity_basket_score + 0.25 * energy_score`.

No weight renormalization is permitted in primary-eligible months because all primary components must be present.

## Frozen analogue regime

Use the exact V6.6 mild thresholds with no fitting:

- growth positive: `GPI_A > +10`;
- growth neutral: `-10 <= GPI_A <= +10`;
- growth negative: `GPI_A < -10`;

and the identical three-way rule for `IPI_A`.

Regime ids must use the exact Issue #133 / V6.6 3x3 mapping.

Regime 7 remains:

`GPI_A < -10 AND IPI_A < -10`.

## Frozen asynchronous-turn analogue

Apply Issue #136's signal definition without modification:

For axis X in {GPI_A, IPI_A}:

`dX_t = X_t - X_(t-1)`.

A turning event occurs when:

- `dX_t > 0`; and
- `dX_(t-1) <= 0`.

At month t, analogue `R7_ASYNC_TURN` requires:

1. analogue regime = Regime 7;
2. GPI_A had a turning event in {t, t-1, t-2};
3. IPI_A had a turning event in {t, t-1, t-2}.

Only the first completion inside each contiguous analogue Regime-7 episode is a trigger.

No future information is used.

## Bridge periods

### Development diagnostic

`2007-01 through 2016-12`

This period is reported descriptively only. No parameter may be changed after seeing it.

### Untouched primary holdout

`2017-01 through latest common completed exact/analogue month`.

Primary bridge verdict is based on this holdout.

Holdout temporal subsegments:

- 2017-2019;
- 2020-2022;
- 2023+.

## Frozen bridge metrics

All metrics use calendar-month alignment.

### Axis fidelity

- Pearson correlation of analogue vs exact GPI levels.
- Pearson correlation of analogue vs exact IPI levels.
- GPI one-month slope-sign agreement, with sign classes {-1, 0, +1}.
- IPI one-month slope-sign agreement.

### State fidelity

- exact 3x3 regime-id agreement fraction.
- Regime-7 precision:
  analogue R7 months that are exact R7 / all analogue R7 months.
- Regime-7 recall:
  exact R7 months captured by analogue R7 / all exact R7 months.

### Trigger fidelity

One-to-one matching of exact Issue #136-style first triggers to analogue first triggers.

A trigger pair is eligible when absolute calendar-month distance <=1.

Matching is deterministic:

1. enumerate all eligible pairs;
2. sort by absolute month distance;
3. then exact date;
4. then analogue date;
5. greedily accept pairs whose exact and analogue triggers are both still unmatched.

Compute:

- trigger precision = matched / analogue triggers;
- trigger recall = matched / exact triggers;
- trigger F1;
- analogue-trigger-count / exact-trigger-count ratio.

## Primary holdout gate

Verdict `signal_bridge_passed` only if all are true:

1. holdout has at least 60 common eligible months;
2. holdout contains at least 4 exact asynchronous-turn triggers;
3. GPI Pearson correlation >= 0.70;
4. IPI Pearson correlation >= 0.70;
5. GPI slope-sign agreement >= 0.70;
6. IPI slope-sign agreement >= 0.70;
7. exact 3x3 regime agreement >= 0.60;
8. Regime-7 precision >= 0.60;
9. Regime-7 recall >= 0.60;
10. trigger F1 within +/-1 month >= 0.60;
11. trigger-count ratio between 0.50 and 2.00 inclusive;
12. each evaluable holdout subsegment has regime agreement >= 0.45.

If gates 1 or 2 fail:

`signal_bridge_inconclusive_sample`.

Otherwise if any fidelity gate fails:

`signal_bridge_failed`.

There is no "suggestive" rescue verdict.

## Historical window after bridge

Only if `signal_bridge_passed`:

- freeze analogue code and source hashes;
- emit structural-analogue signals for `1984-01 through 2006-12`;
- do **not** join any asset outcome inside Issue #141.

A future separate preregistered issue is required to test 1984-2006 Equity-vs-Duration outcomes.

If the bridge fails, historical signals may be emitted for diagnostics but must be explicitly labeled **not validated for outcome testing**.

## Anti-tuning rules

After the first bridge metrics are observed, do not:

- change any proxy source;
- change the eight-series commodity basket;
- replace natural gas with gasoline;
- alter GPI component count;
- alter IPI weights;
- alter 12/1/3 score lengths;
- alter score formula weights;
- rescale or affine-fit GPI_A/IPI_A;
- change +/-10 regime thresholds;
- optimize sign or lag;
- change development/holdout boundaries;
- loosen any bridge gate;
- redefine trigger matching tolerance;
- use asset outcomes to choose among alternatives.

Any alternative requires a new preregistered study.

## Product boundary

Research only.

`production_authorized=false`.

Do not modify V6.6 or V6.7.
Do not modify Issue #136's frozen result.

## Pre-outcome metric implementation clarifications

These rules are frozen before the first analogue-vs-exact bridge metric is computed.

### Common eligible month

A bridge month is common-eligible only when all are available for that calendar month:

- exact GPI;
- exact IPI;
- exact regime id;
- analogue GPI_A;
- analogue IPI_A;
- analogue regime id.

Calendar alignment is by calendar month, not exact day-of-month timestamp.

### Pearson correlation

A level correlation is evaluable only with at least 12 paired common-eligible months.

If fewer than 12 paired months are available, the metric is unevaluable and its gate fails closed.

### Slope-sign agreement

For each axis, slope sign is computed as the exact mathematical sign of the one-month difference:

- negative -> -1;
- exactly zero -> 0;
- positive -> +1.

Rows lacking either current or immediately prior aligned observation for either exact or analogue axis are excluded from that axis's slope-sign denominator.

A slope-sign metric is evaluable only with at least 12 paired signs; otherwise its gate fails closed.

### R7 precision / recall

- precision denominator = number of analogue R7 common-eligible months;
- recall denominator = number of exact R7 common-eligible months.

A zero denominator makes the metric unevaluable and the corresponding gate fails closed.

### Trigger precision / recall / F1

If the holdout has exact triggers but zero analogue triggers:

- trigger precision = 0;
- trigger recall = 0;
- trigger F1 = 0.

If both sides have zero triggers, trigger metrics are unevaluable; however the preregistered exact-trigger sample gate will already fail.

### Evaluable holdout subsegment

A holdout subsegment is evaluable for Gate 12 only if it contains at least 12 common-eligible months.

Every evaluable subsegment must have exact regime-id agreement >= 0.45.

If no holdout subsegment is evaluable, Gate 12 fails closed.

### Historical signal validity flag

The evaluator may always emit 1984-01 through 2006-12 structural-analogue signals for audit.

The output must contain:

`validated_for_outcome_testing = (bridge_verdict == "signal_bridge_passed")`.

No downstream study may join historical asset outcomes unless that flag is true.
