# SPY 1D Pine Parity Report

## Current outcome

Primary outcome: **feed mismatch**.

The TradingView run used dividend-adjusted SPY daily OHLC, while the frozen Python fixture was generated from Yahoo Finance adjusted OHLC. ATR percentage and trend strength exceeded the provisional feature tolerances, so the current run cannot independently establish Pine inference parity against the Python posteriors.

The observed 12/12 dominant-state agreement and small posterior differences are useful diagnostics, but they are not proof that initialization, transition orientation, and filtering math are correct under identical inputs.

This remains a research spike. It is not a cross-asset claim, strategy result, or production acceptance.

## Test setup

- profile: `spy-1d-v0.1`
- chart: SPY, 1D
- Pine version: v6
- verification method: embedded on-chart checkpoints because CSV chart-data export was unavailable on the active TradingView plan
- checkpoint source: `research/fixtures/spy-1d-parity-checkpoints.json`
- checkpoint count: 12
- first manual verification: 2026-07-22

## First observed run

| Metric | Result | Provisional tolerance | Status |
|---|---:|---:|---|
| Checkpoints evaluated | 12 / 12 | 12 / 12 | pass |
| Dominant-state agreement | 12 / 12 | 12 / 12 | diagnostic pass |
| Maximum close relative error | 0.00000964 | 0.0005 | pass |
| Maximum standardized-return error | 0.00100710 | 0.005 | pass |
| Maximum ATR-percent error | 0.00052424 | 0.00005 | fail |
| Maximum trend-strength error | 0.02947913 | 0.01 | fail |
| Maximum posterior error | 0.00200773 | 0.01 | diagnostic pass |
| Maximum probability-sum error | not established at sufficient display precision | 1e-10 | pending |

## Interpretation boundary

Feature parity failed because two feature errors exceeded their thresholds. Therefore:

- the formal result is `feed mismatch`;
- posterior and dominant-state agreement are recorded only as cross-feed diagnostics;
- Pine inference parity is not declared from this run;
- a posterior failure must still remain visible even when a feature failure also exists.

A separate scalar Python mirror reproduces the frozen model artifact to machine precision. That supports the exported parameter orientation and log-space formula, but it does not replace a Pine runtime comparison on identical inputs.

## Tolerance rationale

The feature thresholds are provisional research gates intended to catch formula or vendor-feed differences before posterior comparison:

- close relative error: `0.0005`;
- standardized-return error: `0.005`;
- ATR-percent error: `0.00005`;
- trend-strength error: `0.01`.

The posterior threshold of `0.01` means one percentage point in state probability. It is a diagnostic threshold only when feature parity fails; it cannot independently approve inference across different input feeds.

The probability-sum threshold is `1e-10`. The first table displayed only eight decimal places, so its apparent zero was not sufficient evidence.

## Review-fix verification path

The revised Pine script now:

- reports feature, posterior-agreement, probability-sum, and dominant-state checks independently;
- reports a combined verdict when feature and inference diagnostics both fail;
- displays probability-sum errors to twelve decimal places and a separate pass/fail result;
- displays a 12-row checkpoint table containing per-checkpoint close, standardized-return, ATR, trend, posterior, probability-sum, and dominant-state results.

The checkpoint-level measurements from the revised script are **pending a new TradingView run**. They must be captured before this report is final and before PR #23 returns to Ready for review.

## Next gate

1. Compile the revised Pine script in TradingView Pine v6 on SPY 1D.
2. Capture the summary diagnostics and the 12-row checkpoint evidence table.
3. Update this report with the new checkpoint-level results.
4. Re-run correctness review.
