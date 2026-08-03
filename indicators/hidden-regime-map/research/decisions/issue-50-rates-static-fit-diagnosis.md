# Issue #50 — static rates HMM diagnosis

Date: 2026-08-03

## Decision

The pre-result static-fit U.S. rates experiment is **inconclusive because both HMM candidates lose state diversity out of sample**.

This is not evidence that the U.S. rates market lacks regimes. It is evidence that a single HMM fitted through 2018-10-04 and held fixed through 2026 is not a defensible production design for this feature set.

Primary frozen-evaluator outcome:

`inconclusive_instability`

Frozen implementation outcome without the occupancy override, but retaining the numerical exploratory-contradiction rules:

`no_incremental_value`

Original written-spec outcome:

`indeterminate_protocol`

The original written specification did not numerically define either state instability or a material exploratory contradiction. Under every reproducible interpretation, HMM utility was not established and Issue #41 cannot advance.

Input:

- 4,888 frozen common-date observations before feature warm-up;
- 4,868 observations after causal feature and return alignment;
- 2007-01-03 through 2026-07-30 raw common-date sample;
- decompressed SHA-256 `f85a37d574f58ed927c1b490f14d0057a2f1c295c7061cf2a5d08b433995c104`.

Split after warm-up:

- fit ends 2018-10-04;
- exploratory OOS ends 2022-08-29;
- final OOS runs 2022-08-30 through 2026-07-30.

## Protocol integrity

The evaluator committed before the formal final-period run contained two outcome-affecting implementation rule sets that were incompletely described in the original written specification.

### Occupancy classification

The frozen evaluator:

- evaluates soft-posterior state occupancy in the fit and final OOS periods;
- marks a candidate unstable if any state occupies less than 1% in either period;
- emits `inconclusive_instability` when every candidate is unstable;
- excludes unstable candidates from promotion.

The original written experiment specification listed occupancy as a metric but omitted the numerical threshold, the periods to which it applied, and its effect on the primary outcome.

### Exploratory contradiction

The frozen evaluator marks an HMM-versus-baseline pair contradictory when exploratory-OOS HMM Sharpe is more than 0.10 below the baseline or HMM annualized return is more than 2 percentage points below the baseline. A raw final-period pass is qualified only when neither condition holds.

The original written specification said only to avoid a “material contradiction” and omitted these numerical thresholds.

Neither rule was introduced after final-period observation, but the written protocol cannot independently reproduce the classification. Therefore this report preserves three distinct interpretations:

1. frozen evaluator: `inconclusive_instability`;
2. frozen implementation with the occupancy override disabled but exploratory thresholds retained: `no_incremental_value`;
3. original written specification alone: `indeterminate_protocol`.

None of the three interpretations establishes HMM utility. The omissions are protocol defects and must remain visible.

## Corrected implementation

Codex review identified that target-weight turnover had initially been measured against the previous target weights rather than the previous holdings after market-price drift.

The corrected evaluator computes pre-trade weights by drifting the prior holdings with the prior asset returns, then charges:

`portfolio turnover = 0.5 × sum(abs(target weight - drifted pre-trade weight))`

A focused regression confirms that a constant equal-weight target still incurs rebalancing turnover when its assets earn different returns.

Run #18 (`30783310318`) recomputed the complete experiment on the unchanged frozen input after this correction. The mechanical outcome remained `inconclusive_instability`.

Subsequent review also required two durable safeguards:

- an unstable candidate cannot enter `trading_winners` or `risk_winners`, even when another candidate remains stable;
- CI recursively compares the entire committed status JSON with regenerated output, including metrics, comparisons, gates, restart records, and diagnostics.

These safeguards do not change the current result because both candidates are unstable and neither has two qualified baseline passes.

## State-collapse evidence

### K=3

Training posterior occupancy:

- state 0: 42.3271%;
- state 1: 42.8583%;
- state 2: 14.8146%.

Exploratory OOS occupancy:

- state 0: 1.6090%;
- state 1: 35.0415%;
- state 2: 63.3495%.

Final OOS occupancy:

- state 0: 0.001435%;
- state 1: effectively 0%;
- state 2: 99.998565%.

The fixed mapping assigns state 2 to IEF. The final strategy therefore becomes almost a static intermediate-duration position rather than a functioning regime allocator.

### K=4

Training posterior occupancy:

- state 0: 44.8613%;
- state 1: 27.1385%;
- state 2: 13.6152%;
- state 3: 14.3850%.

Exploratory OOS occupancy:

- state 0: 38.4753%;
- state 1: effectively 0%;
- state 2: 2.8916%;
- state 3: 58.6331%.

Final OOS occupancy:

- state 0: effectively 0%;
- state 1: effectively 0%;
- state 2: 3.7468%;
- state 3: 96.2532%.

The fixed mapping assigns state 3 to IEF and state 2 to cash. This is also effectively an intermediate-duration strategy with a small cash overlay.

Both candidates violate the implementation-frozen 1% state-occupancy stability rule. The written protocol also omitted the frozen numerical exploratory-contradiction thresholds; both omissions are disclosed above.

## Distribution-shift diagnosis

The following figures are descriptive diagnostics calculated with the fit-period StandardScaler. They were not used to repair the model or change the frozen outcome.

Mean standardized features:

| period | curve level | 2s10s slope | 5s30s slope | daily level change | 20-day level-change vol |
|---|---:|---:|---:|---:|---:|
| fit | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| exploratory OOS | -0.805 | -1.398 | -1.143 | 0.015 | -0.227 |
| final OOS | 2.147 | -2.156 | -1.679 | 0.039 | 0.511 |

Raw period means:

| period | curve level | 2s10s slope | 5s30s slope | 20-day level-change vol (bp) |
|---|---:|---:|---:|---:|
| fit | 2.366% | 1.579% | 1.576% | 4.532 |
| exploratory OOS | 1.678% | 0.524% | 0.794% | 4.069 |
| final OOS | 4.201% | -0.046% | 0.427% | 5.573 |

The final period combines a much higher yield level, a deeply shifted/inverted 2s10s distribution, a flatter 5s30s curve, and higher volatility than the static fit generally observed.

The posterior collapse is therefore consistent with a structural distribution shift: the fixed scaler, emissions, and transition matrix have no mechanism to adapt when the rates environment moves far from the pre-2018 training distribution.

This is an inference supported by the frozen feature distributions and posterior occupancies. It is not a claim that one feature alone caused the collapse.

## Corrected final-period metrics

| variant | annualized return | cash-excess Sharpe | maximum drawdown | Calmar | annualized turnover |
|---|---:|---:|---:|---:|---:|
| TLT buy-and-hold | -3.95% | -0.494 | -24.03% | -0.164 | 0.000 |
| equal duration | 0.35% | -0.502 | -11.35% | 0.031 | 0.324 |
| inverse-volatility 63d | 2.15% | -0.617 | -4.59% | 0.468 | 0.580 |
| duration trend 200d | -8.65% | -1.566 | -30.09% | -0.288 | 23.262 |
| volatility-targeted TLT | -1.13% | -0.628 | -10.66% | -0.106 | 5.125 |
| HMM K=3 duration blend | 1.24% | -0.416 | -10.16% | 0.122 | 0.004 |
| HMM K=4 duration blend | 1.09% | -0.442 | -10.16% | 0.107 | 2.499 |

The HMM candidates did reduce losses and drawdown relative to TLT and the failed trend rule. K=3 also had the least-negative cash-excess Sharpe among the tested duration strategies.

Those facts do not establish incremental value:

- neither candidate beat at least two strong baselines under the written promotion gates;
- inverse-volatility produced higher absolute return, much lower drawdown, and much higher Calmar;
- all duration strategies had negative cash-excess Sharpe in the high-cash-rate final period;
- both HMM candidates fail the implementation-frozen state-diversity rule;
- the apparent K=3 low turnover is itself a symptom of state collapse, not proof of efficient regime timing.

## What Issue #50 establishes

Issue #50 supports these bounded conclusions:

1. U.S. rates contain economically meaningful curve and volatility state variables, but a once-fitted static HMM is not robust across the 2007–2026 monetary-policy regimes.
2. Static state labels can become economically stale when the yield-level and curve distributions shift.
3. A rates HMM should be tested with causal rolling or expanding refits, explicit state-identity handling, and fold-by-fold diagnostics.
4. The current result must not advance Issue #41 or be presented as evidence of trading utility.
5. The written protocol was incomplete because it omitted the occupancy outcome rule; future experiments must place every classification threshold in both code and specification before evaluation.

Issue #50 does **not** support:

- “HMM does not work in rates”;
- “the K=3 final return proves a useful strategy”;
- changing K, features, mapping, or thresholds against the already observed final period;
- treating the current final period as untouched evidence in a redesigned experiment.

## Next justified experiment

A separate diagnostic should test a preregistered walk-forward design while preserving:

- the same frozen input;
- the same five features;
- K=3 and K=4 only;
- the same deterministic restarts;
- the same risk-score mapping;
- one-bar lag and drift-aware turnover costs;
- fold-level state occupancy and mapping records;
- every stability threshold written into the specification before execution.

Suggested design:

- minimum five-year training history;
- expanding-window refit at fixed quarterly boundaries;
- each fitted model used only until the next scheduled refit;
- no parameter search based on the observed Issue #50 final period;
- comparison against the same five non-HMM baselines;
- result classified as a post-Issue-50 diagnostic, not independent confirmation.

Even a successful walk-forward diagnostic would require either a new market, a future forward period, or another genuinely untouched sample before promotion.

## Final status

`complete_inconclusive_static_fit_with_protocol_defects`

`can_start_issue_41 = false`
