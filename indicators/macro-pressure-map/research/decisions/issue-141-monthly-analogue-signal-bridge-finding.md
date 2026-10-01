# Issue #141 — Monthly Structural Analogue Signal Bridge Finding

Status: **bridge failed — historical signals are NOT validated for outcome testing**

Issue: #141  
Draft PR: #142  
Branch: `research/issue-141-signal-bridge`

## Research integrity / ordering

Source acquisition occurred without exact V6.6 signals and without asset outcomes.

The analogue specification and bridge gates were then frozen before any analogue-vs-exact bridge metric:

- initial bridge preregistration: `d3c9b30167d684a2733d3dc7d886a4683ae07fc6`
- pre-outcome metric edge-case freeze: `0b19993c328d0fea31c48c1e3e97ec84624932f0`
- evaluator implementation only afterward: `bed29d585eaf98e849811477b71f07a12eb3d99a`

The first bridge run produced the same primary bridge metrics as the final run. A later implementation-only fix corrected a historical-output slice that had accidentally returned zero pre-2007 rows; it did not change any bridge metric or verdict.

Final validated run:

- workflow run: `36841538838`
- validated code head: `7db08451a6e0c1cfe1c993a32f5f9c39e7d2987e`
- artifact digest: `sha256:32f6037e3dcee6b584e37cdd9de0a3cefb475659054d14284849ef4b7a1c212c`

Research firewall:

- `outcome_data_loaded=false`
- `production_authorized=false`

No Equity-vs-Duration outcome was loaded or inspected.

## Frozen source hashes

- Fama/French 3 Factors monthly:
  `593f4fbef03181bc0b22ff6292f217689dd1fb79355049ca905d95b262040a66`
- Fama/French 12 Industry Portfolios monthly:
  `309eb6b2bdbb5bc45f039b9814753b079cd40bd4038ffda9afb6c5e0563fd120`
- World Bank Pink Sheet monthly:
  `9fdcfa8a2aed9a1bb545a10c1a5ce036c6a0acd4766f450424ca800b4b5a0225`
- Cleveland Fed inflation-expectations workbook:
  `20701ccf394d280fe1db38fa9def5628f2385dd0aef148ff989e33ff15caba95`

Exact V6.6 bridge target SHA:

`1d03923503e7fe82a69b033897484c48aa646279ecf70164d090ed62a5a70719`

## Formal verdict

**`signal_bridge_failed`**

`validated_for_outcome_testing=false`

The structural analogue must not be used to test 1984–2006 Equity-vs-Duration outcomes.

## Development diagnostic: 2007–2016

The development interval was descriptive only; no parameter was changed after it was observed.

Common eligible months: 120.

### Axis fidelity

- GPI level correlation: **0.9240**
- IPI level correlation: **0.7336**
- GPI slope-sign agreement: **81.51%**
- IPI slope-sign agreement: **57.14%**

### State fidelity

- exact 3x3 regime agreement: **50.83%**
- R7 precision: **72.41%**
- R7 recall: **84.00%**

### Trigger fidelity

- exact asynchronous-turn triggers: 8
- analogue triggers: 5
- matched within +/-1 month: 4
- trigger precision: **80.00%**
- trigger recall: **50.00%**
- trigger F1: **61.54%**
- trigger-count ratio: **0.625**

Matched development triggers:

- exact 2008-12 -> analogue 2009-01
- exact 2011-08 -> analogue 2011-08
- exact 2015-07 -> analogue 2015-08
- exact 2015-12 -> analogue 2015-12

The development period therefore looked partially promising, especially for GPI and trigger precision. It was not allowed to alter the frozen model.

## Primary untouched holdout: 2017–2026-08

Common eligible months: **116**.

### Axis fidelity

- GPI level correlation: **0.8980**
- IPI level correlation: **0.6830**
- GPI slope-sign agreement: **86.09%**
- IPI slope-sign agreement: **69.57%**

GPI transfers strongly out of sample.

IPI does not meet the preregistered correlation or slope-sign gates.

### State fidelity

- exact 3x3 regime agreement: **45.69%**
- analogue R7 months: 18
- exact R7 months: 26
- overlapping R7 months: 13
- R7 precision: **72.22%**
- R7 recall: **50.00%**

Interpretation:

When the analogue says R7, it is often right, hence the acceptable precision. But it misses half of the exact R7 months, so it is not a faithful substitute for the exact state process.

### Trigger fidelity

Holdout exact asynchronous-turn triggers: **6**.

Holdout analogue asynchronous-turn triggers: **5**.

The trigger counts look superficially similar, but timing fidelity is poor:

- matched within +/-1 month: **1**
- trigger precision: **20.00%**
- trigger recall: **16.67%**
- trigger F1: **18.18%**
- trigger-count ratio: **0.8333**

The only matched holdout trigger is:

- exact 2023-03 -> analogue 2023-03.

This is the decisive failure for the intended Issue #136 historical extension. Similar total trigger counts are not enough if the analogue identifies different episodes/months.

## Holdout temporal diagnostics

Exact 3x3 regime agreement deteriorates through time:

- 2017–2019: **55.56%**
- 2020–2022: **44.44%**
- 2023–2026-08: **38.64%**

The latter two subsegments do not satisfy the frozen 45% floor.

## Gate table

PASS:

1. common eligible months >=60;
2. exact holdout triggers >=4;
3. GPI correlation >=0.70;
5. GPI slope-sign agreement >=0.70;
8. R7 precision >=0.60;
11. trigger-count ratio within 0.50–2.00.

FAIL:

4. IPI correlation >=0.70;
6. IPI slope-sign agreement >=0.70;
7. regime agreement >=0.60;
9. R7 recall >=0.60;
10. trigger F1 >=0.60;
12. every evaluable temporal segment regime agreement >=0.45.

Six of twelve bridge gates fail.

Therefore the failure is not a single arbitrary threshold miss. The analogue does not adequately preserve the exact state/turning object.

## Historical diagnostic output: 1984–2006

The frozen analogue is technically computable for every month from 1984-01 through 2006-12:

- rows: 276
- eligible rows: 276
- analogue R7 months: 38
- analogue asynchronous-turn triggers: 9

Diagnostic trigger months:

- 1984-11
- 1985-09
- 1986-08
- 1989-09
- 1996-09
- 1998-07
- 1998-12
- 2001-10
- 2003-05

These dates are **not validated historical Issue #136 signals**.

They must not be joined to historical Equity-vs-Duration outcomes under Issue #141 because:

`validated_for_outcome_testing=false`.

The presence of nine old triggers is not evidence that the economic hypothesis works or fails.

## What the bridge teaches

The GPI reconstruction is materially successful:

- level correlation near 0.90 in the untouched holdout;
- slope-sign agreement above 86%.

The main fidelity problem is the inflation axis and the resulting state/turning chronology:

- IPI misses its correlation gate;
- IPI narrowly misses slope-sign agreement;
- overall regime agreement is low;
- R7 recall is only 50%;
- asynchronous-turn timing fidelity collapses out of sample.

This suggests that a future research effort, if pursued, should investigate the **historical inflation-pressure representation** as a new signal-engineering question rather than adjust Issue #141 post hoc.

Such a study must receive a new issue and preregistration. It may not use Issue #141 asset outcomes, because none have been inspected.

## Research boundary

Do not:

- lower Issue #141 bridge gates;
- alter the 12/1/3 analogue score lengths;
- change weights after seeing these metrics;
- replace natural gas with another energy proxy inside Issue #141;
- rescale IPI to improve correlation;
- choose a different historical proxy based on 1984–2006 asset returns;
- inspect historical Equity-vs-Duration outcomes for the nine diagnostic trigger dates.

Issue #141 is a clean failed bridge.

No production behavior is authorized to change.
