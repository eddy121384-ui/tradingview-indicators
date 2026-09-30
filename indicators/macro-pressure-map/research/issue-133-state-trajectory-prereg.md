# Issue #133 Preregistration — Macro Pressure Map State × Trajectory

Status: **FROZEN BEFORE RESULT ANALYSIS**

Issue: #133  
Branch: `research/issue-133-state-trajectory`

## Research question

Does trajectory add incremental asset-allocation information beyond the existing Macro Pressure Map V6.6 static regime state?

The motivating case is the late-recession / early-recovery setup where GPI and IPI levels may still classify as Slowdown / Disinflation even though both have started to recover.

This study is research-only. It does not modify V6.6, V6.7, Issue #129, PR #130, or any production Action Layer.

## Frozen primary hypothesis

Exact V6.6 state:

`Regime 7 — Slowdown / Disinflation`

Primary trajectory definition:

- current exact V6.6 regime = Regime 7;
- raw monthly GPI change over 3 completed months > 0;
- raw monthly IPI change over 3 completed months > 0.

Label:

`R7_RECOVERING`

Control:

`R7_NONRECOVERING`

= all other eligible Regime-7 observations with enough lag history.

Directional hypothesis:

`R7_RECOVERING` has stronger next-month `SPY - TLT` total-return spread than `R7_NONRECOVERING`.

## Frozen lookback

Primary trajectory lookback = **3 completed months**.

No magnitude threshold is permitted in the primary definition. Sign only.

A 1-month trajectory definition may be reported as a secondary sensitivity check, but may not replace the primary result.

## Frozen outcome

Primary outcome:

next completed monthly total-return spread:

`SPY return - TLT return`

Primary comparison:

`mean(R7_RECOVERING forward SPY-TLT) - mean(R7_NONRECOVERING forward SPY-TLT)`

Also report medians and positive-spread hit rates descriptively.

Secondary horizon:

compounded next 3-month SPY-TLT spread.

The 3-month horizon may not rescue a failed primary 1-month result.

## Timing / causality

Use completed monthly observations only.

The trajectory label at month t may use only values observable at or before month t.

No future regime transition may be used to label month t.

Forward returns begin after the signal observation.

A one-month delayed-signal robustness test is required.

## Primary gate

H1 receives verdict `state_trajectory_candidate` only if all are true:

1. at least 12 eligible R7_RECOVERING observations;
2. at least 4 distinct R7_RECOVERING episodes;
3. mean next-month SPY-TLT in R7_RECOVERING > 0;
4. incremental mean vs R7_NONRECOVERING > 0;
5. bootstrap 95% CI for the incremental mean excludes 0 on the positive side;
6. at least 2 inherited modern temporal segments are evaluable;
7. at least 2/3 evaluable temporal segments have positive incremental spread; if only 2 are evaluable, both must be positive;
8. every evaluable leave-one-R7_RECOVERING-episode-out incremental spread remains positive;
9. no single positive episode contributes more than 50% of total positive contribution;
10. one-month delayed-signal robustness keeps a positive incremental sign.

If sample-size gates fail:

`inconclusive_sample`

If direction is positive but robustness fails:

`trajectory_suggestive_not_robust`

Otherwise, if the core directional result is not supported:

`trajectory_not_confirmed`

## Frozen temporal segmentation

Use the same modern segmentation convention as Issue #127:

- pre-2020
- 2020–2022
- 2023+

Do not redefine temporal windows after observing outcomes.

## Frozen episode definition

An R7_RECOVERING episode is one or more consecutive monthly observations labeled R7_RECOVERING.

Episode concentration is measured on positive contribution to the primary next-month SPY-TLT spread.

## Secondary trajectory buckets

Within each exact V6.6 regime, classify using the same frozen 3-month raw changes:

1. GPI rising / IPI rising;
2. GPI rising / IPI falling-or-flat;
3. GPI falling-or-flat / IPI rising;
4. GPI falling-or-flat / IPI falling-or-flat.

For every regime × trajectory bucket report:

- n;
- episode count;
- mean next-month SPY;
- mean next-month TLT;
- mean SPY-TLT;
- median SPY-TLT;
- positive-spread hit rate;
- temporal-segment counts.

This matrix is descriptive only.

No cell discovered in the matrix may be promoted to a production rule inside Issue #133.

## Secondary transition study

Using only current and lagged completed states, report:

- R7 -> R4
- R7 -> R5
- R4 -> R1
- R5 -> R1
- R5 -> R2

For each transition report next-month SPY-TLT spread, n, episode count, and temporal concentration.

These are exploratory / hypothesis-generating only.

## Explicit anti-data-mining rules

After results are observed, do not:

- change the primary 3-month lookback;
- add slope magnitude thresholds;
- retune V6.6 regime thresholds;
- redefine Regime 7;
- choose a different primary asset pair;
- optimize the forward-return horizon;
- add FCPI filters;
- add price-trend filters;
- add valuation filters;
- cherry-pick historical windows;
- use future states in current labels;
- convert an exploratory transition or regime×trajectory cell into a production rule.

Any such follow-up requires a new preregistered issue.

## Relationship to existing Action Layer

The completed static-state research remains separate:

- #121: long-history state rematch;
- #123: long-history Reflation portfolio translation;
- #125: HMRA ↔ exact V6.6 bridge, 9/10;
- #127: modern exact V6.6 Reflation translation, 11/11;
- #129 / PR #130: Regime-3 +5pp Equity / -5pp Duration shadow implementation.

Issue #133 does not alter or supersede those results.

## Required deliverables

- deterministic research code;
- tests;
- machine-readable CSV outputs;
- primary R7 recovery comparison;
- temporal validation;
- episode concentration;
- leave-one-episode-out;
- delayed-signal robustness;
- transition table;
- 9-regime × 4-trajectory descriptive map;
- durable finding document with deterministic verdict.

## Product boundary

A positive result does not authorize production.

No V6.6 or V6.7 production code changes are allowed in this issue.

PR #128 and PR #130 must remain unmerged unless separately authorized.
