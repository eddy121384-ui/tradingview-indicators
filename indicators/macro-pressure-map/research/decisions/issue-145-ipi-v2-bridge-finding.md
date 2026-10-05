# Issue #145 — IPI Bridge v2 Finding

Status: **bridge failed — historical signals are NOT validated for outcome testing**

Issue: #145  
Draft PR: #146  
Branch: `research/issue-145-ipi-bridge-v2`

## Research integrity / ordering

Issue #145 source acquisition was completed without exact V6.6 signals and without any asset-return outcome.

Frozen source-only run:

- run: `36959024098`
- source head: `9d65ae01b6b72eab6734c9420111b4e18e45b0c0`
- source artifact digest:
  `sha256:8cd46ba84f11195ee52da3343613429c42af30cbcbda43c937a2cc85c4ae539c`

The normalized v2 source panel was then frozen at:

`848a7ba847b3637b3b8b4715df7b555598c6a7a3bcced76d85aed1e42b29ecaa`

The v2 bridge preregistration preceded any Issue #145 bridge metric:

- preregistration commit:
  `2a71059c99ea703be6b80792106d6409d1a56f04`

The evaluator was committed only afterward.

Final validated bridge run:

- workflow run: `37254759657`
- validated head:
  `b05b779c8dbff20847d53ec8107bf5e8e7ebf3fc`
- artifact digest:
  `sha256:7de45355e6a10aeba646b79d4f57718928f9b04a8118dd4285cc2bdd08c4b5a7`

Hard firewall remained intact:

- `outcome_data_loaded=false`
- `production_authorized=false`

No 1990–2006 Equity-vs-Duration outcome was inspected.

## Source design

IPI v2 retained the frozen monthly score and weights from Issues #141/#143:

- monthly score lengths: 12 / 1 / 3;
- component score weights: 0.5 / 0.3 / 0.2;
- IPI weights: 0.35 / 0.40 / 0.25;
- exact V6.6 +/-10 state thresholds;
- Issue #136 asynchronous-turn rule.

Only source semantics changed:

- inflation expectations: Cleveland Fed 10Y expected inflation;
- broad commodity: official DBIQ Optimum Yield Diversified Commodity Index Excess Return, DBLCDBCE;
- oil: World Bank WTI;
- gasoline: MGASNYH.

### DBIQ source validation

Official DBIQ REST source supplied:

- 9,870 positive daily index levels;
- history from 1988-12-02;
- first level = 100;
- 448 month-end levels through frozen source end 2026-03.

447 monthly returns recomputed from official graphData were cross-checked against DBIQ's official rounded monthlyReturns.

Maximum absolute difference:

**0.00499 percentage points**.

### GPI replay integrity

Issue #145 did not redesign GPI.

The Issue #141 structural GPI replay exactly reproduces the frozen #141 holdout integrity metrics over 2017–2026-08:

- GPI correlation: **0.8980438446**
- slope-sign agreement: **0.8608695652**

Therefore the v2 result is not caused by an accidental GPI implementation change.

## Formal verdict

**`signal_bridge_v2_failed`**

`validated_for_outcome_testing=false`

## Primary untouched holdout: 2017-01 through 2026-03

Common eligible months: **111**.

### Axis fidelity

GPI:

- level correlation: **0.89844**
- slope-sign agreement: **86.36%**

IPI v2:

- level correlation: **0.89985**
- slope-sign agreement: **81.82%**

Both axes comfortably pass the frozen 0.70 correlation and slope gates.

### State fidelity

Exact 3x3 regime agreement:

**56.76%**

Frozen gate:

>=60%.

**FAIL.**

R7 diagnostics:

- exact R7 months: 26
- analogue R7 months: 20
- overlapping R7 months: 16
- R7 precision: **80.00%**
- R7 recall: **61.54%**

Both R7 gates pass the frozen 60% thresholds.

### Trigger fidelity

Exact Issue #136-style first triggers: **6**.

v2 analogue triggers: **6**.

Matched within +/-1 month: **3**.

Trigger metrics:

- precision: **50.00%**
- recall: **50.00%**
- F1: **50.00%**
- trigger-count ratio: **1.00**

Frozen F1 gate:

>=60%.

**FAIL.**

Matched pairs:

- exact 2019-05 -> v2 2019-05
- exact 2023-03 -> v2 2023-03
- exact 2018-10 -> v2 2018-11

The total trigger count is correct, but half of the trigger chronology is still attached to different R7 episodes/months.

## Temporal diagnostics

All three holdout subsegments pass the frozen 45% regime-agreement floor:

- 2017–2019: **69.44%**
- 2020–2022: **55.56%**
- 2023–2026-03: **46.15%**

The fidelity still deteriorates in the most recent period, but no subsegment fails the preregistered temporal floor.

## Gate table

PASS:

1. common eligible months >=60;
2. exact holdout triggers >=4;
3. GPI correlation >=0.70;
4. IPI correlation >=0.70;
5. GPI slope agreement >=0.70;
6. IPI slope agreement >=0.70;
8. R7 precision >=0.60;
9. R7 recall >=0.60;
11. trigger-count ratio between 0.50 and 2.00;
12. every evaluable holdout subsegment regime agreement >=0.45.

FAIL:

7. exact 3x3 regime agreement >=0.60;
10. trigger F1 within +/-1 month >=0.60.

Therefore **10 of 12** bridge gates pass, but the deterministic formal verdict remains:

`signal_bridge_v2_failed`.

There is no suggestive rescue verdict.

## Improvement versus Issue #141

v2 materially improves the failed first analogue bridge.

Frozen holdout comparison:

- IPI correlation:
  0.6830 -> **0.8999**
  (+21.69 percentage points)

- IPI slope-sign agreement:
  69.57% -> **81.82%**
  (+12.25pp)

- regime agreement:
  45.69% -> **56.76%**
  (+11.07pp)

- R7 precision:
  72.22% -> **80.00%**
  (+7.78pp)

- R7 recall:
  50.00% -> **61.54%**
  (+11.54pp)

- trigger F1:
  18.18% -> **50.00%**
  (+31.82pp)

Thus the DBIQ + gasoline source redesign worked in the intended direction.

It did not work enough to satisfy the frozen bridge.

## Development diagnostic: 2007–2016

Development remains descriptive only.

- GPI correlation: 0.9240
- IPI correlation: 0.8531
- GPI slope agreement: 81.51%
- IPI slope agreement: 62.18%
- regime agreement: 52.50%
- R7 precision: 76.67%
- R7 recall: 92.00%
- trigger F1: 46.15%

Matched development triggers:

- exact 2011-08 -> v2 2011-08
- exact 2015-12 -> v2 2015-12
- exact 2008-12 -> v2 2009-01

The v2 source design therefore improves level/state fidelity but does not solve trigger chronology consistently across both development and holdout periods.

## Historical diagnostic: 1990-02 through 2006-12

The frozen v2 analogue is fully computable for every month in the historical window:

- rows: 203
- all rows eligible: true
- analogue R7 months: 19
- analogue asynchronous-turn triggers: 5

Diagnostic trigger months:

- 1991-11
- 1998-01
- 1998-07
- 2000-07
- 2001-10

These dates are **not validated Issue #136 historical signals**.

They must not be joined to Equity-vs-Duration outcomes because:

`validated_for_outcome_testing=false`.

## Research interpretation

Issue #145 materially improves the long-history IPI representation.

The broad-commodity and gasoline redesign fixes most of the severe Issue #141 IPI-level mismatch:

- IPI correlation rises close to 0.90;
- slope agreement rises above 80%;
- R7 precision reaches 80%;
- R7 recall clears the frozen gate.

However, the bridge still misses the required fidelity in the two objects most relevant to the intended historical Issue #136 test:

1. exact 3x3 state classification;
2. asynchronous-turn episode timing.

The remaining error is therefore no longer best described as a broad "IPI level proxy" failure.

It is now primarily a **state-boundary / turning-chronology fidelity problem**.

Given Issue #143 already identified Cleveland expected inflation as the other major historical IPI weakness, the next defensible research question is a separately preregistered inflation-expectations / timing redesign.

Issue #145 itself must not be retuned.

## Research boundary

Do not inside Issue #145:

- lower the 60% regime gate;
- lower the 60% trigger-F1 gate;
- shift trigger tolerance beyond +/-1 month;
- alter DBIQ;
- alter gasoline;
- change IPI weights;
- change monthly score lengths;
- rescale Cleveland expected inflation;
- inspect 1990–2006 asset outcomes.

Any next design requires a new issue.

No V6.6/V6.7 production behavior is authorized to change.
