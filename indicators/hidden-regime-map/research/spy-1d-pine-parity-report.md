# SPY 1D Pine Parity Report

## Current outcome

Primary outcome: **feed mismatch**.

The TradingView run used dividend-adjusted SPY daily OHLC, while the frozen Python fixture was generated from Yahoo Finance adjusted OHLC. ATR percentage and trend strength exceeded the provisional feature tolerances, so this run does not establish Pine inference parity against the Python posteriors.

The revised diagnostics independently show posterior agreement, probability normalization, and dominant-state agreement. These are useful cross-feed diagnostics, not proof of inference parity under identical inputs.

This remains a research spike. It is not a cross-asset claim, strategy result, or production acceptance.

## Test setup

- profile: `spy-1d-v0.1`
- chart: SPY, 1D
- Pine version: v6
- verification method: embedded on-chart checkpoints because CSV chart-data export was unavailable on the active TradingView plan
- checkpoint source: `research/fixtures/spy-1d-parity-checkpoints.json`
- checkpoint count: 12
- first manual verification: 2026-07-22
- revised manual verification: 2026-07-22 17:10 UTC+8

## Revised summary

| Check | Result | Provisional tolerance | Status |
|---|---:|---:|---|
| Checkpoints evaluated | 12 / 12 | 12 / 12 | pass |
| Feature check | — | all feature thresholds | **fail** |
| Posterior agreement | max error `0.00200773` | `0.01` | diagnostic pass |
| Probability-sum check | max error `0.000000000000` | `1e-10` | pass |
| Dominant-state agreement | 12 / 12 | 12 / 12 | diagnostic pass |
| Overall verdict | `Feed mismatch` | — | final result |

### Maximum observed errors

| Metric | Maximum error | Provisional tolerance | Status |
|---|---:|---:|---|
| Close relative error | 0.00000964 | 0.0005 | pass |
| Standardized-return error | 0.00100710 | 0.005 | pass |
| ATR-percent error | 0.00052424 | 0.00005 | **fail** |
| Trend-strength error | 0.02947913 | 0.01 | **fail** |
| Posterior error | 0.00200773 | 0.01 | diagnostic pass |
| Probability-sum error | 0.000000000000 | 1e-10 | pass |

## Checkpoint-level evidence

All values below are absolute errors displayed by the revised Pine on-chart evidence table. `Dom` records whether the dominant state matched the Python fixture.

| Date | Close rel. | Std return | ATR pct | Trend | Posterior | Sum | Dom |
|---|---:|---:|---:|---:|---:|---:|:---:|
| 2010-05-26 | 0.00000526 | 0.00100710 | 0.00000172 | 0.00009205 | 0 | 0.000000000000 | Y |
| 2010-09-21 | 0.00000152 | 0.00002940 | 0.00000070 | 0.00011522 | 0.00018769 | 0.000000000000 | Y |
| 2010-10-27 | 0.00000190 | 0.00006261 | 0.00000129 | 0.00051413 | 0.00200773 | 0.000000000000 | Y |
| 2011-08-08 | 0.00000400 | 0.00000392 | 0.00000235 | 0.00004966 | 0.00019511 | 0.000000000000 | Y |
| 2017-06-30 | 0.00000323 | 0.00000667 | 0.00000027 | 0.00011024 | 0.00000044 | 0.000000000000 | Y |
| 2018-12-24 | 0.00000544 | 0.00000198 | 0.00000093 | 0.00007887 | 0 | 0.000000000000 | Y |
| 2020-03-16 | 0.00000771 | 0.00000242 | 0.00001729 | 0.00029678 | 0 | 0.000000000000 | Y |
| 2020-06-08 | 0.00000964 | 0.00001833 | 0.00052424 | 0.02947913 | 0.00019184 | 0.000000000000 | Y |
| 2022-06-13 | 0.00000141 | 0.00000194 | 0.00000012 | 0.00001283 | 0 | 0.000000000000 | Y |
| 2023-04-21 | 0.00000089 | 0.00000548 | 0.00000054 | 0.00010034 | 0.00000417 | 0.000000000000 | Y |
| 2023-04-24 | 0.00000091 | 0.00000386 | 0.00000054 | 0.00012569 | 0.00001735 | 0.000000000000 | Y |
| 2026-07-21 | 0.00000004 | 0.00000028 | 0.00000035 | 0.00007300 | 0.00057419 | 0.000000000000 | Y |

## Interpretation boundary

Feature parity failed because ATR-percent and trend-strength errors exceeded their thresholds. Therefore:

- the formal result is `feed mismatch`;
- posterior and dominant-state agreement are recorded only as cross-feed diagnostics;
- Pine inference parity is not declared from this run;
- posterior, probability-sum, and dominant-state failures would remain visible even when feature parity fails.

A separate scalar Python mirror reproduces the frozen model artifact to machine precision. That supports the exported parameter orientation and log-space formula, but it does not replace a Pine runtime comparison on identical inputs.

## Tolerance rationale

The feature thresholds are provisional research gates intended to catch formula or vendor-feed differences before posterior comparison:

- close relative error: `0.0005`;
- standardized-return error: `0.005`;
- ATR-percent error: `0.00005`;
- trend-strength error: `0.01`.

The posterior threshold of `0.01` means one percentage point in state probability. It is a diagnostic threshold only when feature parity fails; it cannot independently approve inference across different input feeds.

The probability-sum threshold is `1e-10`. The revised table displays twelve decimal places and separately reports the probability-sum pass/fail result.

## Decision

- Record the Pine-versus-Python result as **feed mismatch**.
- Preserve the observed cross-feed posterior and dominant-state agreement without calling it inference parity.
- Do not loosen feature tolerances to force a pass.
- Do not generalize the SPY profile to other symbols or timeframes.
- A future strict inference-parity claim requires identical input features, such as a TradingView-adjusted export consumed by both implementations or a shared synthetic sequence.

## Next gate

The revised evidence is complete. PR #23 may return to correctness review after CI passes. Product work remains out of scope until this research PR is reviewed and merged.
