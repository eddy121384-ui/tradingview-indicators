# SPY 1D Pine Parity Report

## Outcome

Primary outcome: **feed mismatch observed; Pine inference parity passed within the provisional research tolerance**.

The TradingView on-chart verification reproduced the Python model closely enough to validate the Pine forward-filter implementation, while also confirming small vendor-data differences between Yahoo Finance adjusted OHLC and TradingView dividend-adjusted OHLC.

This is a research acceptance result for the SPY 1D parity spike. It is not a claim of exact cross-vendor data equality, cross-asset validity, strategy profitability, or a production-ready universal indicator.

## Test setup

- profile: `spy-1d-v0.1`
- chart: SPY, 1D
- Pine version: v6
- verification method: on-chart embedded checkpoints because CSV chart-data export was unavailable on the active TradingView plan
- checkpoint source: `research/fixtures/spy-1d-parity-checkpoints.json`
- checkpoint count: 12
- date of manual verification: 2026-07-22

## Results

| Metric | Result |
|---|---:|
| Checkpoints evaluated | 12 / 12 |
| Dominant-state agreement | 12 / 12 |
| Maximum close relative error | 0.00000964 |
| Maximum standardized-return error | 0.00100710 |
| Maximum ATR-percent error | 0.00052424 |
| Maximum trend-strength error | 0.02947913 |
| Maximum posterior error | 0.00200773 |
| Maximum probability-sum error | 0 |

## Interpretation

The close and standardized-return differences remained small. ATR percentage and trend strength exceeded the initial provisional feature thresholds, so exact feature-feed parity did not pass.

The inference layer remained stable despite those input differences:

- all 12 dominant states matched the Python fixture;
- the largest posterior difference was approximately 0.20 percentage points;
- posterior probabilities remained normalized;
- no checkpoint changed state classification.

Therefore the observed discrepancy is classified as a **minor vendor-feed mismatch**, not a Pine HMM implementation failure.

## Decision

- Accept the Pine causal forward-filter implementation as correct for the SPY 1D research spike.
- Preserve the feed mismatch in the record rather than loosening tolerances until it disappears.
- Do not claim exact Yahoo-to-TradingView feature parity.
- Do not generalize the SPY profile to other symbols or timeframes.
- Any future production profile should either be refit from the intended deployment feed or explicitly accept and document bounded cross-feed differences.

## Next gate

The parity spike is ready for correctness review. Product work such as visual simplification, alerts, multi-asset profiles, public-release copy, or strategy claims remains out of scope until this research PR is reviewed and merged.
