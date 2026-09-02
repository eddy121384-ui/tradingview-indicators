# Issue #64 Phase C — preregistered Stagflation gold-over-equity override

This contract was frozen in Issue #64 comment `5403402932` **before any Phase C portfolio PnL was viewed**.

## Hypothesis

Phase A secondary exploratory hypothesis:

- regime: `Stagflation Pressure`;
- relative asset view: GLD over SPY;
- evidence remains reused/development history, not untouched OOS confirmation.

## Frozen templates

- neutral: SPY / TLT / GLD = **40 / 40 / 20**;
- Reflation: **60 / 20 / 20** (unchanged from Phase B);
- Stagflation: **20 / 40 / 40**.

The Stagflation rule moves exactly 20 percentage points from SPY to GLD and leaves TLT unchanged. No weight sweep or optimizer is allowed.

## Primary comparison

Compare the Phase C combined strategy against the already-frozen Phase B Reflation-only strategy. Also report a Stagflation-only diagnostic against fixed neutral 40/40/20.

Implementation remains frozen at one trading-row lag, monthly plus lagged-template-change rebalance, 5 bp primary transaction cost, 0/10 bp sensitivity, the same common SPY/TLT/GLD evaluation calendar, and the same pre-2020 / post-2019 temporal split.

If the primary result is positive, interpretation requires realized-exposure-matched attribution that preserves the Phase B Reflation structure, Stagflation episode concentration, leave-largest-winning-episode-out, cost sensitivity, and era decomposition.

A positive full-history result alone is not sufficient. V6.6 parameters and regime thresholds remain frozen.
