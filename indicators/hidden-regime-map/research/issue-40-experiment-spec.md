# Issue #40 — Predeclared HMM trading-utility experiment

This specification is frozen before the final evaluation period is inspected. The experiment asks whether causal HMM regime information adds out-of-sample trading or risk-management value beyond transparent no-HMM strategies and a simpler moving-average regime filter.

## Frozen input

- Symbol/timeframe: SPY 1D.
- Source: Hidden Regime Market Validation Run #58, artifact `hidden-regime-SPY`, artifact id `8590548073`.
- Decompressed `ohlc.csv` SHA-256: `016448a0492769c527a8dc8e24d60fbda4c4e0e4bbdbcf27506caf30b76dddc4`.
- Durable repository copy: `research/data/issue-40-spy-1d-run58.csv.gz`.
- The evaluator must hash the decompressed CSV before using it. A mismatch is an error, not a reason to fetch fresh data.

## Chronological periods

After the existing causal feature warm-up:

1. first 60%: HMM fitting and training-only scaling;
2. next 20%: exploratory OOS reporting;
3. final 20%: untouched final OOS decision period.

No parameter, state-role rule, baseline rule, threshold, cost, or candidate may be changed after final-period results are observed.

## HMM candidates

Two predeclared candidates are evaluated:

- `k3_baseline`: K=3 with the original three features;
- `k8_baseline_er_downside`: K=8 with the five-feature `baseline_er_downside` set.

For each candidate:

- use group seeds 42, 84, and 126;
- use existing restart offsets 0, 1, and 2;
- fit scaling and HMM parameters on the first 60% only;
- align seed-group models by Gaussian emissions;
- average aligned causal forward-filtered posteriors;
- never use smoothed future-aware states.

## State-role mapping

State roles are determined from training-only aligned emission means in standardized feature space.

Risk score weights:

- standardized return: -1;
- ATR percent: +1;
- trend strength: -1;
- signed efficiency ratio: -1 when present;
- downside variance share: +1 when present.

The lowest-risk 25% of states, rounded up, are favorable. The highest-risk 25%, rounded up, are defensive. For K=3 this means one favorable and one defensive state; for K=8 this means two of each.

## No-HMM baselines

All rules are long-only and use confirmed daily closes:

- `buy_and_hold`: target exposure 1.0;
- `trend_100`: exposure 1.0 when close is above its 100-day moving average;
- `momentum_63`: exposure 1.0 when the 63-day return is positive.

The simpler non-HMM regime comparator is `sma200_filter`: each baseline is allowed only when close is above its 200-day moving average.

## HMM roles

For every baseline and HMM candidate:

- `favorable_filter`: allow the baseline only when favorable-state posterior probability is at least 0.50;
- `size_modifier`: multiply baseline exposure by `0.25 + 0.75 × favorable_probability`;
- `defensive_switch`: allow the baseline unless defensive-state posterior probability is at least 0.50.

## Execution and costs

- A target calculated at bar t is applied to the close-to-close return of bar t+1.
- Exposure is constrained to [0, 1].
- Cost is 5 basis points per unit of absolute exposure turnover.
- No leverage, shorting, borrowing return, or risk-free-rate subtraction.

## Reported evidence

For exploratory and final periods, report:

- annualized return and volatility;
- Sharpe, Sortino, and Calmar;
- maximum drawdown;
- active days, average exposure, round-trip entries, and turnover;
- active-day payoff percentiles and win rate;
- share of positive PnL contributed by the five best days;
- contiguous positive-exposure trade-episode count, payoff percentiles, duration, win rate, censoring flags, and positive-trade concentration.

## Predeclared decision gates

A candidate/role must pass on at least two of the three baselines.

### Trading-value pass

For the same candidate/role/baseline:

- exploratory Sharpe improvement versus no HMM is positive;
- final Sharpe improvement versus no HMM is at least 0.15;
- final annualized-return sacrifice versus no HMM is no worse than 1 percentage point;
- final Sharpe beats the SMA200-filter comparator by at least 0.05;
- final active days are at least 100;
- the five best positive days contribute no more than 50% of positive PnL.

### Risk-value pass

For the same candidate/role/baseline:

- exploratory maximum drawdown improves versus no HMM;
- final maximum-drawdown magnitude is reduced by at least 20%;
- final Calmar improves by at least 0.10;
- final annualized-return sacrifice versus no HMM is no worse than 2 percentage points;
- final drawdown magnitude is at least 5% lower than the SMA200-filter comparator;
- final active days and concentration satisfy the same guardrails above.

## Mechanical outcome

- `adds_oos_trading_value`: at least one candidate/role clears the trading-value gate on two or more baselines;
- `adds_oos_risk_value_only`: no trading winner, but at least one candidate/role clears the risk-value gate on two or more baselines;
- `no_incremental_value`: all experiments complete but neither gate is cleared;
- `inconclusive`: the frozen input, fitting, causal inference, or required evaluation cannot be completed truthfully.

A negative result must be retained. Thresholds and guardrails may not be relaxed to manufacture a positive outcome.

## Evidence-completeness addendum after the first run

Self-QC after the first generated result found that the initial report included entry counts, active-day payoff statistics, and positive-day concentration but did not directly report the issue's requested trade-level payoff distribution. Contiguous positive-exposure episode metrics were therefore added as descriptive evidence.

This addendum does not change the input, candidates, periods, strategy rules, state mapping, costs, thresholds, decision gates, or outcome. Period-boundary episodes are retained and explicitly marked as left- or right-censored so their payoff statistics are not mistaken for fully observed round trips.
