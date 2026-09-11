# Issue #76 — Current Nine-Market Data Acceptance

## Decision

Proceed with the currently collected TradingView Pine Log exports. No further DE10Y re-export is required.

This is an explicit measurement-scope acceptance, not a classifier change and not an assertion that the DE10Y export is complete.

## Current data set

Nine frozen feeds are present:

- OANDA:EURUSD — 5,397 marker rows, 2005-04-07 to 2026-08-10
- OANDA:GBPUSD — 5,454 marker rows, 2005-04-18 to 2026-08-10
- OANDA:USDJPY — 5,305 marker rows, 2005-04-06 to 2026-08-10
- TVC:US10Y — 9,832 marker rows, 1980-03-26 to 2026-08-09
- TVC:DE10Y — 10,000 marker rows, 1984-06-08 to 2026-08-11
- TVC:FR10Y — 8,303 marker rows, 1988-12-01 to 2026-08-11
- TVC:GB10Y — 9,722 marker rows, 1982-11-24 to 2026-08-10
- TVC:AU10Y — 9,957 marker rows, 1986-01-01 to 2026-08-10
- TVC:JP10Y — 4,148 marker rows, 2009-03-12 to 2026-08-10

Total accepted marker rows: 68,118.

## DE10Y caveat

The DE10Y export contains exactly 10,000 marker rows, which matches the pipeline's preregistered possible-log-cap warning condition. The underlying chart history begins around 1980, while the first emitted Issue #76 event row is 1984-06-08 at event bar 1,164.

The gap between raw chart start and first emitted event can also be partly or entirely explained by the classifier's long warmup / rank windows and periods with no formal stage. Therefore the current evidence does not prove whether any valid DE10Y event rows were lost to a Pine Logs limit.

For this Phase-A pass:

- keep the current DE10Y export;
- treat its early-history completeness as ambiguous;
- do not use the exact DE10Y row count or start date as evidence for classifier behavior;
- require cross-market consistency before advancing any hypothesis;
- preserve this caveat in every pooled/final finding.

## Zero-RV artifact handling

Ten `rv5` / `rvn5` values were emitted as `NaN`: 8 in DE10Y and 2 in JP10Y.

Each affected event was mechanically checked against the next five consecutive event bars. All five one-bar moves were exactly zero in every affected case, so the mathematically correct 5-bar RMS realized-volatility value is exactly zero. These ten values are therefore repaired to `0.0` for measurement only.

No stage ID, forward move, MFE, MAE, classifier threshold, weight, lifecycle state, or HARD-cap behavior is modified.

## Scope status

Accepted for Issue #76 Phase-A descriptive analysis with the DE10Y completeness caveat above.
