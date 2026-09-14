# Issue #78 — Economic Value / Profitability Audit Preregistration

## Purpose

Test whether the already-frozen Issue #78 participation + damage-management candidates show a positive **risk-normalized directional expectancy** when all completed trend episodes are chained together, rather than judging them only by median episode outcome or selected large-trend slices.

This is still in-sample discovery on the accepted Issue #76 nine-market daily sample. It is not a production backtest, broker-fill simulation, or out-of-sample validation.

## Critical interpretation constraint

The current research feed measures movement of the charted underlying series in entry-ATR units. For yield series this is yield-direction movement, not cash bond / futures PnL. Therefore this audit may establish or reject **directional economic value in normalized underlying-move units**, but it cannot by itself establish executable dollar profitability.

A later instrument-mapped test is required for actual futures / cash implementation, transaction costs, DV01 / contract sizing, slippage, financing and carry.

## Frozen sample

Use the same accepted Issue #76 daily universe and logger evidence already used by Issue #78:

- OANDA:EURUSD
- OANDA:GBPUSD
- OANDA:USDJPY
- TVC:US10Y
- TVC:DE10Y
- TVC:FR10Y
- TVC:GB10Y
- TVC:AU10Y
- TVC:JP10Y

Use completed known-start Markup and Markdown episodes only. Right-censored terminal episodes remain excluded.

## Frozen policy set

No new policy is invented in this audit. Compare only rules already defined before this preregistration:

1. Formal Hold — full exposure until formal trend loss.
2. Full-at-entry + Gentle damage latch.
3. Full-at-entry + Balanced damage latch.
4. Persistence Ramp + Gentle damage latch.
5. Persistence Ramp + Balanced damage latch.
6. Excursion-Proof Ramp + Gentle damage latch.
7. Excursion-Proof Ramp + Balanced damage latch.

Persistence + Health is excluded because the prior first-pass decision downgraded it before this audit.

## Causal accounting convention

- Exposure decided at close `t` applies only to move `t -> t+1`.
- Entry ATR remains fixed for each episode, matching prior Issue #78 analysis.
- Positive normalized return means movement favorable to the formal trend direction.
- Formal-loss triggering move remains included when the policy is still exposed because the new formal state is not known until the next close.
- Zero exposure is assumed outside active Markup / Markdown management episodes.

## Primary economic-value metrics

For each policy, report:

### Per-market

- episode count;
- mean episode normalized return;
- median episode normalized return;
- win rate;
- mean winner;
- mean loser;
- profit factor = sum positive episode returns / absolute sum negative episode returns;
- cumulative normalized return;
- maximum drawdown of the sequential normalized-return path;
- total exposure turnover;
- break-even normalized friction = cumulative gross return / total turnover when gross return is positive.

### Universal / cross-market

Primary aggregation is equal-market, not pooled-row weighting:

- equal-market mean of per-market mean episode return;
- number of markets with positive mean episode return;
- number of markets with profit factor > 1;
- number of markets with positive cumulative normalized return;
- equal-market median profit factor;
- equal-market mean maximum drawdown;
- leave-one-market-out sign robustness for equal-market mean episode return.

## Tail-dependence audit

Trend-following systems may have negative medians yet positive expectancy because a minority of very large winners dominate returns. Therefore report, without using the result to optimize rules:

- share of gross positive return contributed by the top 1% winning episodes;
- cumulative result after removing the single best episode in each market;
- cumulative result after removing the top 1% winning episodes globally within each market;
- cumulative result after capping each episode at the market's 95th percentile positive outcome;
- sign of equal-market mean episode return under each stress.

These are robustness diagnostics, not alternative strategies.

## Sampling uncertainty

Use a deterministic bootstrap with a frozen random seed to resample completed episodes **within each market**, preserving equal-market aggregation. Report a descriptive 95% interval for the equal-market mean episode return. This bootstrap is an approximation and does not remove serial-regime dependence; do not present it as a formal iid significance test.

Frozen settings:

- random seed: `7801`;
- bootstrap replications: `5000`.

## Friction sensitivity

Do not invent real bid/ask or commission estimates for heterogeneous instruments.

Instead report a generic normalized friction sensitivity in entry-ATR units per 100% exposure turnover and, where gross return is positive, the policy's break-even normalized friction. This is only a portability diagnostic until instrument mapping is performed.

## Decision language

Allowed conclusions:

- `no gross normalized edge detected`;
- `gross normalized edge is positive but fragile / tail-dependent`;
- `gross normalized edge is cross-market broad but still in-sample`;
- `candidate merits instrument-mapped OOS validation`.

Not allowed from this audit:

- `profitable trading system`;
- `stable alpha`;
- `production-ready`;
- choosing a policy solely because it has the largest in-sample return / Sharpe-like metric.

## Anti-overfit guardrails

- no new thresholds, holding periods, ATR landmarks or exposure weights;
- no asset-specific policy branches;
- no separate long / short tuning;
- no dropping markets because they hurt results;
- no parameter optimization after inspecting these outputs;
- no classifier changes;
- retain PR #80 as Draft during this audit.

Refs #78, #80 and #76.
