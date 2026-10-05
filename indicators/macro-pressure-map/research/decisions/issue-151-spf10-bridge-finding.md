# Issue #151 — SPF 10Y CPI Inflation Expectations Bridge Finding

Status: **bridge failed — SPF is not a valid drop-in historical inflation-expectations leg under the frozen monthly score**

Issue: #151  
Draft PR: #152  
Branch: `research/issue-151-spf10-bridge`

## Research integrity / ordering

Phase A source acquisition and causal monthly normalization were completed before any Issue #151 bridge metric was observed.

Frozen source-only run:

- workflow run: `37264957977`
- source head: `d006572bd02ce447af4c0e2dd812310062198330`
- source artifact digest:
  `sha256:5a2f681c340f0de0a6bc8eaa56143b2d3731f2b017cf0e1bb178abd8abceb9b6`

Official Philadelphia Fed SPF files:

- `Inflation.xlsx` raw SHA256:
  `2bef852b0b4c4365ce9d38796c408ecb2648f024b2cc1d40a8c1426afe62e2e5`
- historical release-date file raw SHA256:
  `c5f4c4dc349068ba9dc1f421c68474be26d0fe613fff83f70aa41eed96696ee3`

Frozen SPF target:

- sheet: `INFLATION`
- column: `INFCPI10YR`
- first survey: `1991:Q4`
- last frozen survey: `2026:Q3`

Causal monthly source:

- first month: `1991-11`
- last month: `2026-08`
- rows: 418
- normalized CSV SHA256:
  `bfd9a8e76d882007a80584a439289f456bf06999223d2f1f30f85bb02f4e65e5`
- deterministic gzip SHA256:
  `8d21fb8a3b346d160a63d8b67ac1fe454b27a20605388033f886cf3406681c3c`

The quarterly-to-monthly rule was frozen before bridge evaluation:

- no quarter-start backfill;
- no interpolation;
- a survey becomes available only after its official public release;
- completed month end uses the latest already-public survey value;
- carry forward until the next release.

Bridge preregistration commit:

`04c77937a68d0de58e6a9785215c511352f44256`

Evaluator implementation came afterward.

The first two bridge CI failures were implementation-only and occurred before a bridge result:

1. prereg guard exact-string mismatch;
2. repository-frozen base64 newline packaging error.

Neither changed data, score definitions, bridge periods, gates, or economics.

Final validated bridge run:

- workflow run: `37265373383`
- validated code head:
  `1d831e31cc1d363d429c2892fddeab36acc08239`
- artifact digest:
  `sha256:c37ad39441623e9e01017998ac3abeb39afbb04ff1d3453c0c8fc69c6baf72a2`

Hard firewall remained intact:

- `outcome_data_loaded=false`
- `production_authorized=false`

No historical Equity-vs-Duration outcome was inspected.

## Formal verdict

**`signal_bridge_spf_failed`**

`validated_for_outcome_testing=false`

## What changed versus Issue #145

Issue #151 changed exactly one IPI source role:

- Issue #145: Cleveland Fed 10Y expected inflation;
- Issue #151: Philadelphia Fed SPF median 10Y CPI inflation forecast.

Everything else remained frozen:

- structural GPI;
- DBIQ DBLCDBCE;
- World Bank WTI;
- MGASNYH gasoline;
- monthly 12 / 1 / 3 score;
- component weights 0.5 / 0.3 / 0.2;
- IPI weights 0.35 / 0.40 / 0.25;
- +/-10 regime thresholds;
- Issue #136 asynchronous-turn logic;
- +/-1 month trigger matching.

GPI replay integrity matched the frozen Issue #141 metrics exactly before use.

## Structural frequency diagnostic

The causal monthly SPF level has 418 observations.

After the first month:

**79.62% of monthly SPF levels are unchanged from the previous month.**

This is expected from a quarterly survey carried forward causally, but it creates a structural problem for the unchanged monthly component-score formula.

The score contains a 12-month rolling standard deviation.

When SPF remains exactly unchanged for a sufficiently long interval, the rolling standard deviation becomes zero and the component score fails closed to NA.

This is not an implementation error. It is a direct consequence of applying the frozen score to a low-frequency step-function input.

### Modern ineligible interval

The holdout loses these months because the SPF component is not finite:

- 2020-02
- 2020-03
- 2020-04

The SPF 10Y CPI forecast remained exactly 2.20 for an extended interval spanning 2019 and early 2020.

Notably, 2020-04 is one of the important exact Issue #136 turning months. Because the SPF bridge is undefined there, the common-eligible exact trigger count falls from six in Issue #145 to five in Issue #151.

No special zero-variance treatment is permitted post hoc.

## Development diagnostic: 2007–2016

Common eligible months: **118**.

- GPI correlation: **0.92353**
- IPI correlation: **0.82997**
- GPI slope-sign agreement: **81.90%**
- IPI slope-sign agreement: **75.00%**
- exact 3x3 regime agreement: **50.00%**
- R7 precision: **79.17%**
- R7 recall: **76.00%**
- exact triggers: 8
- SPF analogue triggers: 5
- matched triggers: 4
- trigger F1: **61.54%**
- trigger-count ratio: **0.625**

Development trigger matches:

- exact 2015-12 -> SPF 2015-12
- exact 2008-12 -> SPF 2008-11
- exact 2012-06 -> SPF 2012-05
- exact 2015-07 -> SPF 2015-08

Development trigger fidelity therefore looks acceptable in isolation, but it does not transfer to the untouched holdout.

## Primary untouched holdout: 2017-01 through 2026-03

Common eligible months: **108**.

### Axis fidelity

- GPI correlation: **0.89602**
- IPI correlation: **0.80857**
- GPI slope-sign agreement: **85.85%**
- IPI slope-sign agreement: **80.19%**

Both axis-level gates pass.

### State fidelity

- exact 3x3 regime agreement: **56.48%**
- R7 precision: **86.67%**
- R7 recall: **56.52%**

Frozen gates:

- regime agreement >=60% — **FAIL**
- R7 precision >=60% — PASS
- R7 recall >=60% — **FAIL**

The SPF construction is conservative when it calls R7, but misses too many exact R7 months.

### Trigger fidelity

Within the common-eligible holdout:

- exact triggers: **5**
- SPF analogue triggers: **4**
- matched within +/-1 month: **2**
- precision: **50.00%**
- recall: **40.00%**
- F1: **44.44%**
- count ratio: **0.80**

Frozen F1 gate >=60% — **FAIL**.

Matched pairs:

- exact 2018-10 -> SPF 2018-10
- exact 2023-03 -> SPF 2023-03

## Temporal diagnostics

Holdout regime agreement:

- 2017–2019: **69.44%**
- 2020–2022: **48.48%**
- 2023–2026-03: **51.28%**

All evaluable subsegments clear the frozen 45% floor, but post-2020 fidelity is materially weaker than 2017–2019.

## Gate table

PASS:

1. common eligible months >=60;
2. exact common-eligible triggers >=4;
3. GPI correlation >=0.70;
4. IPI correlation >=0.70;
5. GPI slope-sign agreement >=0.70;
6. IPI slope-sign agreement >=0.70;
8. R7 precision >=0.60;
11. trigger-count ratio between 0.50 and 2.00;
12. every evaluable temporal subsegment regime agreement >=0.45.

FAIL:

7. regime agreement >=0.60;
9. R7 recall >=0.60;
10. trigger F1 >=0.60.

Therefore **9 of 12** frozen gates pass.

Formal verdict remains:

`signal_bridge_spf_failed`.

## Direct comparison versus Issue #145

SPF worsens most primary fidelity metrics.

- IPI correlation:
  0.89985 -> **0.80857**
  delta **-0.09129**

- IPI slope-sign agreement:
  81.82% -> **80.19%**
  delta **-1.63pp**

- regime agreement:
  56.76% -> **56.48%**
  delta **-0.28pp**

- R7 precision:
  80.00% -> **86.67%**
  delta **+6.67pp**

- R7 recall:
  61.54% -> **56.52%**
  delta **-5.02pp**

- trigger F1:
  50.00% -> **44.44%**
  delta **-5.56pp**

The only clear improvement is R7 precision, obtained at the cost of lower recall.

Issue #145 remains the best tested long-history inflation construction.

## Historical diagnostic: 1993-01 through 2006-12

The nominal historical window contains 168 calendar months.

However, unlike Issue #145, it is **not continuously eligible**.

There are **48 ineligible months** caused by an undefined SPF component score during long zero-variance survey plateaus.

Major ineligible blocks include:

- 1996-10 through 1997-04;
- 2000-04 through 2001-10;
- 2004-01 through 2005-01;
- 2006-04 through 2006-12.

Within the computable historical months:

- analogue R7 months: 11
- asynchronous-turn triggers: 3

Diagnostic trigger months:

- 1995-02
- 1998-01
- 1998-06

These dates are **not validated historical Issue #136 signals** and must not be joined to asset outcomes.

## Research interpretation

The SPF route is rejected as a direct drop-in replacement under the frozen monthly V6.6-style component score.

Two independent problems appear:

1. **signal fidelity is worse than Issue #145** on the untouched modern holdout;
2. **quarterly step-function frequency is structurally incompatible with the unchanged rolling-score formula** in long flat forecast intervals.

The second problem is important.

It would be possible to invent special handling such as interpolation, epsilon variance floors, quarterly scoring, or release-month impulses. But all of those are new signal designs and would alter the meaning of the frozen Issue #151 test after seeing the result.

They are therefore forbidden inside Issue #151.

Issue #145 pure Cleveland expected inflation remains the best tested construction to date.

## Research boundary

Do not inside Issue #151:

- interpolate SPF;
- backfill forecasts to quarter start;
- replace zero standard deviation with epsilon;
- score only release months;
- switch median to mean;
- switch CPI10 to PCE10;
- combine SPF and Cleveland;
- change score lengths / weights;
- change state thresholds or trigger matching;
- inspect 1993–2006 asset outcomes.

Any such proposal requires a new preregistered issue.

No V6.6/V6.7 production change is authorized.
