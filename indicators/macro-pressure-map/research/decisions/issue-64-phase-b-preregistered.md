# Issue #64 Phase B — preregistered Reflation allocation test

This contract is frozen **before Phase B portfolio PnL is viewed**.

## Question

Does one coarse V6.6 Reflation override improve portfolio-level outcomes relative to holding the exact same neutral portfolio statically?

Phase A selected this as an **exploratory** hypothesis after inspecting 81 regime / horizon / asset-pair comparisons. Phase B therefore remains reused-history exploratory evidence even if the result is favorable.

## Frozen allocation

Default / all non-Reflation regimes:

- SPY 40%
- TLT 40%
- GLD 20%

Reflation / Inflation Rising:

- SPY 60%
- TLT 20%
- GLD 20%

This is exactly a 20 percentage-point transfer from TLT to SPY. No other regime gets a special recipe. There is no Stagflation override in the primary test and no weight-magnitude sweep.

## Execution and rebalancing

- Regime signal is lagged one common trading row before it can change the target.
- Scheduled rebalance: first common trading day of each calendar month.
- Event rebalance: additionally when the lagged target template changes between neutral and Reflation.
- A transition among two non-Reflation regimes does not cause a trade.
- Between trades, weights drift self-financing with adjusted close-to-close returns.
- Turnover is `0.5 * sum(abs(target - drifted_pretrade_weights))`.

## Costs

Primary cost assumption: **5 bps per 100% one-way turnover**.

Sensitivity: 0 bps and 10 bps. These are diagnostics, not alternative parameter-selection runs.

## Benchmarks

- fixed 60/40 SPY/TLT;
- fixed equal-weight SPY/TLT/GLD;
- fixed neutral 40/40/20 SPY/TLT/GLD — this is the **primary incremental control**;
- causal inverse-volatility, 63 trading-row lookback, estimated only through t-1 and rebalanced monthly.

All strategies use the same common evaluation dates. The common start is delayed until the lagged 63-row inverse-volatility estimate is finite for all three assets. End date is the frozen signal cutoff, 2026-08-14.

## Required metrics

CAGR, annualized return, annualized volatility, Sharpe (0% risk-free assumption), maximum drawdown, Calmar, turnover, rebalance count, transaction-cost drag and average weights.

Report full reused history plus 2007–2019 and 2020–2026 slices. Neither slice is untouched OOS because Phase A already inspected both eras.

## Decision rule

The primary question is **incremental value versus fixed neutral 40/40/20**, not whether the strategy beats every benchmark on every metric.

After results are viewed, do not tune the 60/20/20 Reflation template, lag, monthly schedule, cost assumption or universe to rescue the result. A negative result is valid.

A later Stagflation-gold experiment, if any, must be separately preregistered and reported incrementally rather than folded into this result.

Machine-readable source of truth: `issue-64-phase-b-preregistered.json`.
