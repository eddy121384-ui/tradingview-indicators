# Issue #121 Phase 1 preregistration — ultra-long-history rematch

Status: **PREREGISTERED BEFORE ISSUE #121 REMATCH CLASSIFICATIONS**

## Research role

This is a full losers' bracket rematch of previously rejected / non-production Macro Pressure Map asset mappings.

The macro state model is not changed.

Exactly reuse Issue #91 HMRA-v0.1 and its frozen asset-source backbone.

Primary question:

> Which mappings revive under ultra-long history when judged on strict-causal state_t -> return_{t+2} evidence rather than the short modern V6.6 sample?

## Frozen state model

No change from Issue #91 HMRA-v0.1.

All 9 HMRA cells are evaluated.

No state may be dropped after outcomes are inspected.

## Eligible pairwise spreads

### Equity minus Treasury
- primary return history: 1928–2025
- strict-causal state years paired to return year t+2

### Treasury minus Cash
- primary return history: 1928–2025
- strict-causal state years paired to return year t+2

### Gold minus Cash
- primary investable-Gold return years: 1975–2025
- strict-causal state year may begin before 1975 if return year t+2 is >=1975
- pre-1975 return years are excluded from resurrection inference

Broad Commodities minus Cash is handled by a separate source gate and does not block these three core spreads.

## Primary timing

Primary resurrection evidence:

state_t -> annual spread return_{t+2}

Same-year state_t <-> return_t is structural/descriptive support only.

No t+1 rescue.

## Statistics

For each cell x spread and for both structural and causal pairings:

- n
- arithmetic mean
- median
- sample standard deviation
- positive fraction
- 10,000-resample percentile bootstrap 95% CI of mean

Bootstrap seed is deterministic from Issue 121 + pairing + cell + spread.

## Era robustness

Reuse the frozen Issue #91 era label already attached to HMRA states.

For each strict-causal cell x spread:

- eligible era = n >= 3
- candidate sign = sign of full strict-causal mean
- count eligible eras with same sign
- flag opposite-sign eligible era with absolute mean > 0.05

Required for resurrection:
- at least 2 eligible eras
- at least 2 eligible eras have candidate sign
- no eligible era has opposite-sign mean with |mean| > 0.05

## Leave-one-era-out

For each strict-causal cell x spread:

- omit each era that contributes at least one observation
- require remaining n >= 8 to evaluate
- recompute mean
- any evaluated leaveout sign flip fails resurrection

If no leaveout is evaluable because remaining n <8, classification is inconclusive.

## Era concentration

For each strict-causal cell x spread:

- era contribution proxy = absolute value of sum(spread returns) within each era
- strongest-era share = max(era contribution proxy) / sum(all era contribution proxies)

Required for resurrection:
- strongest-era share <= 0.50

If denominator is zero, classification is inconclusive.

## Same-year support

For resurrection, same-year structural mean must have the same nonzero sign as strict-causal mean.

The same-year CI does not need to exclude zero for resurrection because timing-safe evidence is primary.

## Classification

Each cell x spread receives exactly one classification.

### revived_long_history_candidate

All must hold:

1. strict-causal n >= 8
2. strict-causal mean nonzero
3. strict-causal 95% CI excludes zero
4. same-year structural mean has same nonzero sign
5. >=2 eligible eras
6. >=2 eligible eras share candidate sign
7. no eligible opposite-sign era has |mean| > 0.05
8. every evaluable leave-one-era-out retains sign
9. at least one leave-one-era-out is evaluable
10. strongest-era contribution share <=0.50

### long_history_structural_but_timing_unstable

Use if:
- structural n >=8
- structural CI excludes zero
- but strict-causal CI includes zero OR strict-causal sign differs from structural sign

### long_history_era_dependent

Use if:
- strict-causal n>=8
- strict-causal CI excludes zero
- structural sign matches
- but one or more era / leaveout / concentration gates fail

### remains_unconfirmed

Use if:
- strict-causal n>=8
- strict-causal CI includes zero
- and structural CI does not meet the timing-unstable definition

### inconclusive_long_history_sample

Use if:
- strict-causal n<8
- or fewer than 2 eligible eras
- or no evaluable leave-one-era-out
- or concentration denominator is zero
- or source integrity fails

No discretionary override.

## Direction interpretation

The rematch is direction-agnostic.

If a cell revives with positive spread:
- Equity-Treasury => Equity > Treasury
- Treasury-Cash => Treasury > Cash
- Gold-Cash => Gold > Cash

If a cell revives with negative spread, the opposite preference is reported.

Do not force the old expected direction.

## Known prior information

The following are already known and must not be presented as new discovery:

- Reflation Equity-Treasury looked strong in #91.
- Slowdown/Disinflation Treasury-Cash had strong same-year #91 evidence.
- Disinflationary Drift Treasury-Cash had strong same-year #91 evidence.
- absolute CPI >=4% changed Treasury-Cash behavior in some cells.
- #117 found no generic long-history Gold-Cash effect under a different monthly IP+CPI analogue.

Issue #121 still applies the exact same gate to every cell.

## Absolute-inflation interaction

Reuse #91's frozen <4% vs >=4% interaction only as:

known_prior_long_history_interaction

It does not alter resurrection classification in Phase 1.

No new CPI threshold may be searched.

## Commodity boundary

Broad Commodities-Cash is excluded from core classification until a >=50-year broad commodity **total-return** source is frozen.

Spot-only commodity price indices are not acceptable substitutes.

A source-gate block must be reported explicitly, not rescued with an ETF.

## Phase 2 boundary

Only revived_long_history_candidate mappings may enter a later portfolio-policy rematch.

Phase 1 authorizes no production position, weight, leverage, or allocation matrix.

No Issue #121 rematch classification had been computed when this preregistration was committed.
