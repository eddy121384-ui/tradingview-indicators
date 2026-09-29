# Issue #117 preregistration — Long-history Gold vs Cash concept validation

Status: **PREREGISTERED BEFORE CONDITIONED GOLD-vs-CASH PAYOFF RESULTS**

## Research role

This is a concept-equivalent long-history validation of the Gold > Cash relationship observed in modern V6.6 defensive states.

It is not exact historical V6.6.

The modern hypothesis is already known, so this is not untouched OOS evidence. The value of this study is historical breadth and regime diversity.

## Primary window

- target start: **1975-01**
- end: latest common completed month supported by all frozen sources
- required minimum span: **45 years**
- expected span: approximately 1975–2026

If source coverage shortens the actual common sample below 45 years, stop as inconclusive before conditioned payoff analysis.

## Macro state model

Use a monthly extension of the already-frozen Issue #91 HMRA-v0.1 semantics.

Sources:
- Growth: Federal Reserve Industrial Production, B50001 / INDPRO-equivalent total industrial production, seasonally adjusted
- Inflation: BLS CPI-U All Items, CUUR0000SA0, not seasonally adjusted

Monthly transforms for source month m:

- growth_rate_m = 100 * ln(IP_m / IP_m-12)
- inflation_rate_m = 100 * ln(CPI_m / CPI_m-12)
- growth_accel_m = growth_rate_m - growth_rate_m-12
- inflation_accel_m = inflation_rate_m - inflation_rate_m-12

Normalization:
- trailing 60 monthly observations
- reference window strictly before source month m
- population standard deviation
- if reference std = 0 or insufficient history, score is missing

For each axis:
- level_z = current rate vs prior 60-month rate history
- accel_z = current acceleration vs prior 60-month acceleration history
- raw = 0.70 * level_z + 0.30 * accel_z
- score = 100 * tanh(raw / 2)

Thresholds:
- low: score < -10
- neutral: -10 <= score <= +10
- high: score > +10

State map:
- growth low + inflation low = Slowdown / Disinflation
- growth low + inflation neutral = Growth Slowdown / Stable Inflation
- growth low + inflation high = Stagflation Pressure

These three states are the preregistered pooled defensive Gold state.

No other state is allowed into the primary Gold > Cash hypothesis.

## Publication lag

Decision month t uses macro source month t-2.

Rationale:
- CPI and IP for month t-1 are generally not both known on the first day of month t;
- a two-month lag is a simple conservative timing rule.

Current-vintage macro histories are used. Therefore:
- timing is causal with respect to calendar release lag;
- real-time-vintage revision bias is not eliminated;
- no claim of vintage-perfect historical observability is allowed.

## Gold source

Primary Gold outcome transport:
- datasets/gold-prices GitHub mirror
- exact mirror commit frozen before payoff analysis
- mirror README documents that 1960-present data come from World Bank Commodity Markets Pink Sheet
- field: monthly nominal USD gold price per troy ounce
- monthly average, not an executable month-end fill

Upstream provider:
- World Bank Commodity Price Data (Pink Sheet)

No GLD ETF is used in the long-history primary analysis.

## Cash source

Primary Cash outcome:
- Kenneth French Data Library monthly RF
- one-month U.S. Treasury bill return
- monthly simple percentage return converted to decimal

Documented source semantics:
- through May 2024: Ibbotson Associates one-month T-bill rate
- from June 2024: ICE BofA US 1-Month Treasury Bill Index

No zero-return cash assumption.
No TB3MS yield-as-return substitution in the primary analysis.

FRED TB3MS may be used only as a source-level diagnostic.

## Forward outcome timing

State label is assigned to decision month t using macro source month t-2.

Because Gold is a monthly-average price series, outcomes begin one full month after the decision month.

Primary 3M outcome:
- Gold: P[t+4] / P[t+1] - 1
- Cash: compound RF for months t+1, t+2, t+3
- spread: Gold_3M - Cash_3M

Diagnostics:
- 1M: P[t+2] / P[t+1] - 1 versus RF[t+1]
- 6M: P[t+7] / P[t+1] - 1 versus compounded RF[t+1..t+6]

Interpretation:
- these are forward monthly-average price-return comparisons;
- they are structural payoff evidence, not executable fill backtests.

## Primary inference sample

Primary inference uses 3M outcomes.

To reduce overlap:
- sort eligible defensive-state decision months chronologically;
- select the earliest eligible decision month;
- next selected decision month must be at least 3 calendar months after the prior selected decision month;
- this selector is applied to the pooled defensive-state sample, not separately by sub-state.

All-monthly results are diagnostic only.

Minimum full primary sample for a material verdict: n >= 30 selected observations.

## Temporal eras

Freeze four eras by decision month:

1. 1975-01 through 1989-12
2. 1990-01 through 2006-12
3. 2007-01 through 2019-12
4. 2020-01 through latest

Era inference:
- era is evaluable if it has >= 5 primary selected observations
- structural-support gate requires at least 3 evaluable eras
- at least 3 evaluable eras must have positive mean Gold-minus-Cash spread
- no evaluable era may have mean spread below -5 percentage points over the 3M horizon

Do not change era boundaries after payoff inspection.

## Episode robustness

A defensive episode is a consecutive run of decision months classified in any of the three pooled defensive states.

Direct transitions among Regimes 7/8/9 remain the same pooled defensive episode.

Episode contribution:
- sum of all-monthly 3M Gold-minus-Cash spreads for decision months in that episode

Primary episode robustness:
- identify strongest positive-contribution episode
- remove every primary-inference observation whose decision month lies in that episode
- recompute primary mean spread
- leaveout mean must remain positive

Concentration gate:
- strongest positive episode share <= 35% of total positive episode contribution

## Leave-one-substate-out robustness

Run three fixed pooled counterfactuals:
- remove Slowdown / Disinflation
- remove Growth Slowdown / Stable Inflation
- remove Stagflation Pressure

For each:
- rerun the same pooled non-overlap selector
- require primary mean Gold-minus-Cash spread > 0

This is robustness only.
Do not select the best surviving subset.

## Statistical summary

For full pooled primary sample:
- n
- arithmetic mean spread
- median spread
- positive fraction
- standard deviation
- 95% bootstrap CI of the mean

Bootstrap:
- 10,000 iid resamples of the non-overlapping primary observations
- deterministic stable seed based on issue/study label

Because non-overlap is already enforced, no overlapping monthly observations enter the primary bootstrap.

Era and leaveout summaries use the same descriptive statistics but are not multiplicity-adjusted hypothesis tests.

## Modern overlap bridge

Diagnostic only.

Where frozen exact V6.6 state history exists:
- map monthly decisions to exact V6.6 state from the previous eligible frozen signal observation
- compare whether exact V6.6 is in Regime 7/8/9 versus monthly HMRA defensive state
- report agreement, precision/recall-style overlap, and Gold-minus-Cash direction under each label

Do not tune monthly HMRA to increase overlap.

The bridge is not required for the long-history structural verdict if frozen exact-state transport is unavailable on the current branch.

## Verdict gate

Allowed conclusions:

### long_history_supports_structural_gold_cash_relationship

All must hold:
1. common sample span >= 45 years
2. pooled primary n >= 30
3. full pooled 95% bootstrap CI excludes zero on the positive side
4. at least 3 eras are evaluable
5. at least 3 evaluable eras have positive mean spread
6. no evaluable era mean spread < -0.05
7. strongest-positive-episode leaveout mean remains positive
8. strongest positive episode share <= 0.35
9. all three leave-one-substate-out pooled means remain positive

### long_history_relationship_era_dependent

Use if:
- full pooled CI excludes zero positively
- but one or more stability gates 4–9 fail

### long_history_no_material_gold_cash_relationship

Use if:
- span >=45 years
- pooled primary n >=30
- full pooled 95% CI includes zero
- no data-integrity block exists

### inconclusive_data_or_definition_limitations

Use if:
- span <45 years
- pooled primary n <30
- required source or timing validation fails
- fewer than 3 eras are evaluable

No discretionary override.

## Forbidden rescue paths

Do not:
- change 60M normalization
- change 12M rate or acceleration horizons
- change 70/30 score weights
- change ±10 thresholds
- change the t-2 macro lag
- add unemployment after seeing Gold returns
- add absolute CPI thresholds after seeing Gold returns
- add Reflation or any non-defensive state
- change 3M primary horizon
- replace RF with zero cash
- change Gold transport because results are weak
- change era boundaries
- choose a favorable leave-one-substate subset
- optimize Gold weight or portfolio weights

## Research boundary

This study tests a structural pairwise relationship.

It does not authorize:
- a production portfolio weight
- a +5pp rule
- leverage
- options
- a full 3x3 allocation matrix

No conditioned Gold-vs-Cash payoff result had been computed when this preregistration was committed.
