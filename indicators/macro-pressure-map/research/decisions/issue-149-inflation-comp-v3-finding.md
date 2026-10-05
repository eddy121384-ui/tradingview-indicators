# Issue #149 — Inflation Compensation Bridge v3 Finding

Status: **bridge failed — adding Cleveland inflation risk premium made fidelity worse**

Issue: #149  
Draft PR: #150  
Branch: `research/issue-149-inflation-comp-v3`

## Research integrity / ordering

Phase A source freeze was completed before any v3 analogue-vs-exact metric:

- source run: `37258981774`
- source head: `2cdf1bb5eeebe43a5ae60b212348c55a833cb690`
- source artifact digest:
  `sha256:b679efc77f8eee89f6fb2c28bdffe97f3680eee6ea281341e6e4765cadace2fd`

Frozen Cleveland workbook SHA256:

`20701ccf394d280fe1db38fa9def5628f2385dd0aef148ff989e33ff15caba95`

Frozen source definition:

`CLEVELAND_COMP10 = 10Y Expected Inflation + Inflation Risk Premium`

Normalized compensation CSV SHA256:

`a07dbdb377a2ae1dedc7a176d43b20b14d951caddde776aef18dfcf810256a10`

Preregistration commit, before any v3 bridge result:

`029e50245364b1c4576bc54350214ae5216561f5`

Evaluator / workflow were committed afterward.

Final validated v3 bridge run:

- workflow run: `37259207817`
- validated bridge head:
  `604492027036fff319fd73620fd15ac686decbd6`
- artifact digest:
  `sha256:7f0feb4b9a1748af0bec1438141d9ec67c240780b196be8baa6368819a8f6096`

Research firewall remained intact:

- `outcome_data_loaded=false`
- `production_authorized=false`

No 1990–2006 Equity-vs-Duration outcome was loaded or inspected.

## Formal verdict

**`signal_bridge_v3_failed`**

`validated_for_outcome_testing=false`

The v3 inflation-compensation redesign must not be used to unlock historical outcome testing.

## What v3 changed

Issue #145 IPI v2 used pure Cleveland 10Y expected inflation.

Issue #149 changed exactly one semantic input:

`10Y Expected Inflation`

to

`10Y Expected Inflation + Inflation Risk Premium`.

Everything else remained frozen:

- DBIQ DBLCDBCE;
- World Bank WTI;
- MGASNYH gasoline;
- monthly 12/1/3 scoring;
- IPI weights 0.35 / 0.40 / 0.25;
- structural GPI;
- +/-10 regime thresholds;
- Issue #136 asynchronous-turn rule;
- +/-1 month trigger matching.

GPI replay integrity continued to match the frozen Issue #141 result exactly before use.

## Holdout result: 2017-01 through 2026-03

Common eligible months: **111**.

### Axis fidelity

- GPI correlation: **0.89844**
- IPI correlation: **0.89035**
- GPI slope-sign agreement: **86.36%**
- IPI slope-sign agreement: **79.09%**

The axis-level gates pass, but both IPI measures are worse than Issue #145.

### State fidelity

- exact 3x3 regime agreement: **55.86%**
- R7 precision: **78.95%**
- R7 recall: **57.69%**

Frozen gates:

- regime agreement >=60% — **FAIL**
- R7 precision >=60% — PASS
- R7 recall >=60% — **FAIL**

### Trigger fidelity

- exact triggers: **6**
- v3 analogue triggers: **8**
- matched within +/-1 month: **3**
- trigger precision: **37.50%**
- trigger recall: **50.00%**
- trigger F1: **42.86%**
- trigger-count ratio: **1.3333**

Frozen trigger-F1 gate >=60% — **FAIL**.

Matched pairs remain:

- exact 2019-05 -> v3 2019-05
- exact 2023-03 -> v3 2023-03
- exact 2018-10 -> v3 2018-11

The compensation redesign adds extra false-positive trigger episodes without recovering the missing exact trigger chronology.

## Holdout temporal diagnostics

Regime agreement:

- 2017–2019: **63.89%**
- 2020–2022: **52.78%**
- 2023–2026-03: **51.28%**

All three remain above the frozen 45% subsegment floor.

## Gate table

PASS:

1. common eligible months >=60;
2. exact triggers >=4;
3. GPI correlation >=0.70;
4. IPI correlation >=0.70;
5. GPI slope agreement >=0.70;
6. IPI slope agreement >=0.70;
8. R7 precision >=0.60;
11. trigger-count ratio between 0.50 and 2.00;
12. every evaluable temporal subsegment regime agreement >=0.45.

FAIL:

7. regime agreement >=0.60;
9. R7 recall >=0.60;
10. trigger F1 >=0.60.

Thus **9 of 12** gates pass.

## Direct comparison versus Issue #145

Every primary IPI/state/trigger fidelity measure deteriorates:

- IPI correlation:
  0.89985 -> **0.89035**
  delta **-0.00951**

- IPI slope-sign agreement:
  81.82% -> **79.09%**
  delta **-2.73pp**

- regime agreement:
  56.76% -> **55.86%**
  delta **-0.90pp**

- R7 precision:
  80.00% -> **78.95%**
  delta **-1.05pp**

- R7 recall:
  61.54% -> **57.69%**
  delta **-3.85pp**

- trigger F1:
  50.00% -> **42.86%**
  delta **-7.14pp**

Therefore the primary v3 hypothesis is rejected.

Adding the Cleveland model's inflation risk premium does **not** make the historical inflation leg more faithful to the exact V6.6 T10YIE role under the frozen bridge tests.

## Historical diagnostic: 1990-02 through 2006-12

The v3 analogue remains fully computable:

- rows: 203
- all rows eligible: true
- R7 months: 19
- asynchronous-turn triggers: 5

Diagnostic trigger months:

- 1991-11
- 1998-01
- 1998-07
- 2000-07
- 2001-10

These happen to match the Issue #145 diagnostic dates, but remain **unauthorized for outcome testing** because the v3 bridge failed.

## Research interpretation

The remaining Issue #145 mismatch is not repaired by converting Cleveland expected inflation into Cleveland expected inflation plus its inflation risk premium.

This is useful negative evidence:

- the remaining state-boundary / timing error is not simply "breakeven contains an inflation risk premium, so add it";
- Issue #145 pure Cleveland expected inflation remains the better of the two Cleveland constructions tested;
- the next defensible study should examine a genuinely different historical expectations source / timing process rather than further algebraic recombination of the same Cleveland model.

Candidates for a future separately preregistered study may include survey-based long-horizon expectations such as the Philadelphia Fed SPF 10-year CPI forecast, or another independently sourced historical expectations proxy. Those alternatives are not tested or selected inside Issue #149.

## Research boundary

Do not inside Issue #149:

- remove only part of the risk premium;
- fit a risk-premium coefficient;
- lag the risk premium;
- add/subtract the real risk premium;
- change Cleveland horizon;
- change DBIQ, WTI, gasoline, weights, score lengths, thresholds, or trigger rules;
- inspect 1990–2006 asset outcomes.

Any next design requires a new preregistered issue.

No V6.6/V6.7 production change is authorized.
