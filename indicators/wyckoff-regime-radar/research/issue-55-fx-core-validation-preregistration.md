# Issue #55 — Wyckoff FX Core Validation Preregistration

## Frozen subject

- Pine source: `indicators/wyckoff-regime-radar/src/chase-risk-market-regime-radar-v0.5.2.1.pine`
- Frozen source blob SHA: `ab6861181a27697ad566c19bf405a0571be2eb1a`
- Version: Chase Risk Market Regime Radar v0.5.2.1
- Validation mode: Price Action / Structure only

The following layers are excluded from the first utility experiment and must contribute zero stage-bias weight:

- Volume
- MTF
- Divergence
- witness governance effects

The first experiment is not allowed to add or tune indicator features after final OOS is opened.

## Primary markets

Daily FX:

- EURUSD
- USDJPY
- GBPUSD
- AUDUSD

SPY is deliberately excluded as the primary validation market because persistent positive equity drift can make long-biased regime rules appear useful even when the classifier adds little incremental information.

## Mirror boundary

The Python research mirror must reproduce the causal price-only path that affects formal regime output:

1. heat / panic heat;
2. trend maturity;
3. breakout / breakdown context;
4. range score and market structure;
5. absorption / distribution price evidence;
6. trend extension and continuation scores;
7. six raw stage scores;
8. six price-only gates and effective scores;
9. gamma sharpening and six relative stage weights;
10. top / second stage and top gap;
11. price-only evidence strength;
12. candidate qualification, confirmation bars, fast-switch behavior, no-regime logic, and formal stage.

UI, dashboard rendering, colors, alerts, and witness-only diagnostics are not part of the Python mirror.

## Parity gate

Utility analysis is blocked until Pine and Python are compared on fixed historical checkpoints.

Required comparison fields:

- six stage weights;
- candidate stage;
- formal stage;
- top gap;
- price-only evidence strength;
- any confirmation-state variables required to explain a mismatch.

Feed differences must be measured rather than silently tolerated.

## Data and evaluation contract

- Acquire daily OHLC automatically where practical.
- Freeze the exact inputs used for each FX pair with source, date range, row count, and SHA-256.
- Default chronological split: 60% development / 20% exploratory OOS / 20% final OOS.
- Final OOS remains unopened until the mirror, metrics, stage-response mapping, lag, and cost assumptions are frozen.
- Once final OOS is observed, changes require a new independent evaluation sample.

## State-information tests

For each formal state, evaluate both bar-level and episode-level outcomes at 5 / 10 / 20 / 60 observations:

- forward return;
- MFE;
- MAE;
- realized volatility;
- continuation / new-high / new-low behavior where meaningful;
- tail outcomes;
- sample count;
- episode duration;
- next-state transition.

The six Wyckoff labels are not treated as ground truth. The question is whether the states produce distinct and stable future-path distributions.

## Confidence calibration

Test whether higher stage weight, larger top gap, and stronger price-only evidence produce more useful or better-separated OOS outcomes. These values are relative scores, not statistical probabilities.

## Final utility gate

Before final OOS is opened, freeze a simple regime-response map consistent with the product's intended use and compare it against transparent FX baselines with one-bar lag and explicit costs.

Allowed final outcomes:

- `validated_incremental_utility`
- `descriptive_but_not_incremental`
- `insufficient_state_separation`
- `unstable_across_fx_pairs_or_oos`
- `parity_or_data_blocked`

A negative result is a valid completed experiment.