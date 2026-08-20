# Issue #59 — Macro Pressure Map V6.6 TradingView parity

Date: 2026-08-17

## Decision

**PASS — frozen V6.6 default market-only path has Pine ↔ Python engineering parity.**

This is not an economic-validity result. It only establishes that the Python research mirror reproduces the existing Pine V6.6 calculation when both engines receive the same TradingView source history.

## Evidence

User-supplied TradingView Pine Logs CSV:

- SHA-256: `c0220d4974b2fd0154c4cf8f33b4b3effb27a58e21ee96a1b0109011ce638e3d`
- size: 1,894,288 bytes
- log rows: 4,943
- unique daily rows: 4,935
- history: 2007-01-03 through 2026-08-14
- chart: SPY 1D
- V6.6 mode: default market-only path

The helper logged the same 20 default TradingView source series used by V6.6 plus the original smoothed GPI, IPI, and FCPI plots.

## Initial failure

GPI and IPI matched after startup, but FCPI diverged intermittently in older history. The original Python mirror showed FCPI errors as large as approximately **24.89 index points**, especially around 2011–2013, 2016–2017, 2019–2023.

This was an implementation-parity defect, not evidence about the indicator's economic quality.

## Root cause

The defect was in the Python mirror's rolling `na` semantics.

The V6.6 real-yield component uses percentage ROC. The 10Y real-yield series can equal or cross zero, so ROC is undefined when the lagged denominator is exactly zero. That creates isolated `na` momentum observations.

Pine's `ta.sma()` / `ta.stdev()` rolling behavior ignores `na` source observations and works from the latest required number of valid observations. The first Python mirror instead used pandas fixed-bar rolling windows with `min_periods=length`. One isolated `na` therefore invalidated the Python momentum Z-score for the next 252 bars.

That error propagated through:

`scoreRealYield -> RatesDollarConstraint -> FCPI`

Positive-price GPI/IPI inputs rarely hit this edge case, which is why those axes already matched.

## Fix

The mirror now uses Pine-compatible rolling mean and biased standard deviation over the latest non-`na` observations. Regression tests explicitly cover:

- rolling Z-score recovery after an internal `na`;
- real-yield zero-denominator ROC events not poisoning the following 252 bars.

The production Pine V6.6 was **not changed**.

## Post-fix parity

The log starts in 2007, while the original Pine indicator can see earlier chart history. Therefore the first 355 logged rows are mechanically excluded from parity evaluation: 63 lag bars + 252 valid momentum observations + 40 EMA(5) seed-decay bars.

Evaluation begins 2008-06-02, with 4,580 comparable rows per axis.

| Axis | Mean abs error | p99 abs error | Max abs error |
|---|---:|---:|---:|
| GPI plot | 2.71e-9 | 5.08e-9 | 3.34e-7 |
| IPI plot | 2.57e-9 | 4.97e-9 | 8.16e-8 |
| FCPI plot | 2.55e-9 | 4.95e-9 | 1.13e-7 |

Predeclared engineering gate:

- at least 100 comparable rows per axis;
- p99 absolute error <= 0.10 index points;
- maximum absolute error <= 0.50 points.

**Result: PASS by a very large margin.**

## Scope boundary

This pass covers the frozen V6.6 **default market-only** configuration only:

- macro confirmation off;
- official FCI off;
- T5YIE optional component off;
- industrial-metals optional component off;
- KRE stress add-on off;
- EMA(5) plotting on.

It does not establish parity for those optional paths, public Yahoo/FRED feed equivalence, predictive usefulness, regime usefulness, or trading profitability.

## Next research gate

With formula parity established, Issue #59 may proceed to historical diagnostics of the frozen V6.6 default path:

1. axis construct validity;
2. level versus transition information;
3. regime fingerprints across assets;
4. incremental information versus simple baselines;
5. robustness across different market eras.

No V6.6 weights or thresholds should be tuned before that descriptive validation is recorded.
