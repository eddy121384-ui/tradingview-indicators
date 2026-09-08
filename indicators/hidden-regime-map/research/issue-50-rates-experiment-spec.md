# Issue #50 — U.S. rates regime-utility experiment

Status: pre-result specification with documented protocol omissions

## Question

Can causal HMM regime probabilities derived from the U.S. Treasury yield curve improve duration allocation among SHY, IEF, TLT, and cash, relative to strong transparent non-HMM rates baselines?

This is a new experiment. It does not repair or retune the Issue #40 SPY result.

## Frozen sample

The formal sample will be acquired once and committed as a compressed CSV plus a SHA-256 checksum before the evaluator is allowed to expose final-period metrics.

- start: 2007-01-01;
- end: 2026-07-31;
- FRED series: DGS3MO, DGS2, DGS5, DGS10, DGS30;
- adjusted ETF prices: SHY, IEF, TLT;
- rows: dates on which all yield and ETF observations are present;
- no interpolation across missing yield observations;
- duplicate dates rejected;
- all prices and yields must be finite; ETF prices must be positive.

The first CI run is acquisition-only when no frozen file exists. Formal model evaluation starts only after the exact file and checksum are committed.

## Features

Exactly five causal daily curve features:

1. `curve_level`: mean of 2Y, 5Y, 10Y, and 30Y yields;
2. `slope_2s10s`: 10Y minus 2Y;
3. `slope_5s30s`: 30Y minus 5Y;
4. `level_change_bp`: one-day change in curve level, in basis points;
5. `level_vol_20_bp`: trailing 20-observation population standard deviation of `level_change_bp`.

Warm-up rows are dropped before splitting. Scaling is fitted on the fit period only.

## Split

After feature warm-up and return alignment:

- 60% chronological fit;
- 20% exploratory OOS;
- 20% untouched final OOS.

The split fractions and all rules below are fixed before final-period evaluation, subject to the protocol-omission disclosure below.

## HMM candidates

Exactly two diagonal-Gaussian HMM ensembles:

- K=3;
- K=4.

For each K:

- independent group seeds: 42, 84, 126;
- restart offsets inherited from `compare_state_counts.py`: 0, 1, 2;
- best finite converged training likelihood retained within each group;
- state labels aligned to the first group by emission-distribution distance;
- aligned causal forward-filtered probabilities averaged across the three groups;
- no smoothed or future-aware states.

No extra K, features, seeds, or restart schedules may be added after final metrics are observed.

## Protocol-omission disclosure

The evaluator committed before the formal final-period run already contained two outcome-affecting rule sets that the original written specification did not define numerically.

### State-occupancy rule

The frozen evaluator:

- calculates soft-posterior state occupancy separately in the fit and final OOS periods;
- classifies a candidate as unstable when any state has occupancy below 1% in either period;
- emits `inconclusive_instability` when every HMM candidate is unstable;

The original written specification listed occupancy as a metric but omitted the 1% threshold, the tested periods, and its effect on the primary outcome.

### Exploratory-contradiction rule

For each HMM-versus-baseline pair, the frozen evaluator marks a material exploratory-OOS contradiction when either:

- HMM cash-excess Sharpe is more than 0.10 below the baseline; or
- HMM annualized return is more than 2 percentage points below the baseline.

A raw final-period trading or risk pass is qualified only when neither contradiction condition is met.

The original written specification said only that promotion must avoid a “material contradiction” and did not define these two thresholds.

### Post-result promotion safeguard

After the first formal result was observed, review identified a general evaluator defect: if only one candidate were unstable, that candidate could still enter `trading_winners` or `risk_winners`. The evaluator was corrected to exclude every unstable candidate from promotion while still allowing a stable peer to be evaluated.

This safeguard was added after result observation. It did not change the current Issue #50 output because both candidates are unstable and both winner dictionaries were already empty. It is not part of the frozen pre-result rule set and must not be described as preregistered.

### Interpretation consequence

Neither rule was added, relaxed, or tuned after observing the final period; both existed in the frozen evaluator beforehand. Nevertheless, the written protocol was incomplete and cannot independently reproduce the primary classification.

The durable interpretation must therefore distinguish:

1. **Frozen pre-result evaluator outcome:** applies the implementation-frozen occupancy classification and exploratory-contradiction rules.
2. **Current corrected evaluator outcome:** adds the post-result safeguard excluding isolated unstable winners; it produces the same result on this sample.
3. **Frozen implementation without the occupancy override:** retains the numerical exploratory-contradiction rules but ignores the 1% instability classification.
4. **Original written-spec outcome:** indeterminate because both “instability” and “material contradiction” lacked complete numerical definitions.

This disclosure is not a retroactive preregistration claim. Future experiments must place every outcome-affecting threshold in both the code and written specification before execution.

## Fixed state-to-duration mapping

The HMM is a state estimator, not an expected-return oracle.

For each aligned state, define a duration-risk score from standardized emission means:

`risk_score = level_change_bp + 0.75 * level_vol_20_bp`

States are sorted from lowest to highest risk score.

- K=3: lowest -> TLT, middle -> IEF, highest -> SHY;
- K=4: lowest -> TLT, next -> IEF, next -> SHY, highest -> cash.

Portfolio target weights are the posterior-probability blend of the state one-hot allocations. No threshold optimization is allowed.

## Execution and costs

- targets formed from confirmed data on date t;
- positions executed on date t+1;
- long-only;
- fully invested across SHY, IEF, TLT, and cash;
- no leverage or short selling;
- portfolio turnover is `0.5 × sum(abs(target weight - drifted pre-trade weight))`;
- transaction cost: 2 basis points per unit of that portfolio-turnover measure;
- cash earns the prior observed DGS3MO annualized rate divided by 252.

## Baselines

All baselines use the same dates, lag, costs, and cash return:

1. `tlt_buy_hold`: 100% TLT;
2. `equal_duration`: one-third SHY, IEF, and TLT;
3. `inverse_vol_63`: trailing 63-day inverse-volatility weights across SHY, IEF, and TLT;
4. `trend_duration_200`: TLT when TLT is above its 200-day moving average, otherwise SHY;
5. `vol_target_tlt_20`: TLT scaled to an 8% annualized-volatility target using trailing 20-day realized volatility, remainder cash, exposure clipped to [0, 1].

## Metrics

For exploratory and final OOS periods:

- annualized return;
- annualized volatility;
- cash-excess Sharpe;
- maximum drawdown, seeded with opening equity 1.0;
- Calmar;
- total and annualized turnover;
- transaction-cost drag;
- average asset weights;
- active days;
- top-five positive-day P&L concentration;
- HMM state occupancy and mapping;
- selected restart seeds and attempts.

## Mechanical promotion gate

For a given baseline, an HMM candidate earns a trading-value pass if:

- final-period Sharpe improvement is at least 0.10;
- final-period annualized return sacrifice is no more than 1 percentage point;
- top-five positive-day concentration is no worse than 50%;
- at least 100 final-period observations carry non-cash duration exposure.

It earns a risk-value pass if:

- final-period maximum drawdown magnitude is reduced by at least 20%;
- final-period Calmar improves by at least 0.10;
- annualized return sacrifice is no more than 2 percentage points;
- the concentration and activity guardrails above pass.

Promotion requires one stable HMM candidate to pass trading-value or risk-value gates against at least two non-HMM baselines, and to avoid material contradiction in exploratory OOS.

Even a mechanical pass remains provisional until an adjacent-window or walk-forward sensitivity check succeeds.

## Outcomes

The evaluator must emit exactly one primary outcome:

- `incremental_value_supported`;
- `risk_value_only`;
- `no_incremental_value`;
- `inconclusive_instability`.

## Boundaries

- No final-period threshold repair.
- No expected-return state mapping learned from final-period asset returns.
- No commodities, equities, options, leverage, short selling, or reinforcement learning.
- No advancement of Issue #41 solely because one attractive equity curve appears.
