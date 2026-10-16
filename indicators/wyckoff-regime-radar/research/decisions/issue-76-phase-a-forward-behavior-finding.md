# Issue #76 — Phase-A Forward-Behavior Finding

## Status

**Phase A decision: `advance_to_frozen_strategy_hypothesis`, but only for one narrow candidate: fresh formal S5 entry followed by 10-bar bearish-direction continuation.**

This is not a production trading rule and not an in-sample PnL claim. It is a descriptive full-history finding selected from the preregistered event layers and frozen 1/5/10/20-bar horizons. Any strategy claim must be frozen first and tested in a separate OOS issue.

The current nine-market data set is accepted under `issue-76-current-nine-market-data-acceptance.md`; DE10Y retains the explicit possible-10,000-log-cap / early-history completeness caveat.

## Accepted sample

Total formal-stage event rows: **68,118**.

Formal-stage occupancy:

| Stage | Rows |
|---|---:|
| S1 | 5,510 |
| S2 | 26,517 |
| S3 | 124 |
| S4 | 5,669 |
| S5 | 30,277 |
| S6 | 21 |

Fresh entries:

| Stage | Fresh entries |
|---|---:|
| S1 | 426 |
| S2 | 813 |
| S3 | 20 |
| S4 | 412 |
| S5 | 819 |
| S6 | 3 |

Primary canonical-transition counts:

- S1 -> S2: 165
- S2 -> S3: 6
- S3 -> S2: 15
- S4 -> S5: 174
- S5 -> S6: 1
- S6 -> S5: 2

The practical consequence is important: the current classifier behaves overwhelmingly as an S1/S2/S4/S5 system in this nine-market daily sample. S3 and especially S6 are too sparse for a defensible direct-signal conclusion.

## Main finding — fresh S5, 10 bars

For a fresh formal S5 entry, define the aligned direction as bearish / lower series level over the next 10 daily bars.

All **9 of 9 markets** have a positive direction-aligned median normalized 10-bar move.

| Market | Fresh S5 n | Aligned median normalized 10-bar move | Bearish hit rate |
|---|---:|---:|---:|
| AU10Y | 120 | 0.689 | 59.17% |
| DE10Y | 120 | 0.039 | 50.83% |
| EURUSD | 70 | 0.208 | 55.71% |
| FR10Y | 96 | 0.129 | 55.21% |
| GB10Y | 127 | 0.051 | 51.97% |
| GBPUSD | 63 | 0.627 | 55.56% |
| JP10Y | 47 | 0.164 | 57.45% |
| US10Y | 112 | 0.510 | 58.04% |
| USDJPY | 64 | 0.250 | 54.69% |

Cross-market equal-weight summary:

- markets with positive aligned median: **9 / 9**;
- total fresh-S5 observations: **819**;
- equal-market mean bearish hit rate: **55.40%**;
- pooled bearish hit rate: **55.19%**;
- equal-market median of aligned normalized medians: **0.208 event-time symATR**;
- equal-market mean of aligned normalized medians: **0.296 event-time symATR**;
- pooled median aligned normalized move: **0.237 event-time symATR**.

Horizon coherence is not monotonic but is interpretable:

- 5 bars: 7 / 9 markets have positive aligned median; equal-market mean hit rate 53.13%;
- 10 bars: 9 / 9; 55.40%;
- 20 bars: 6 / 9; 52.68%.

Thus 10 bars is the strongest preregistered descriptive horizon. Because this horizon is selected after inspecting the four preregistered horizons, it must be treated as a hypothesis-selection result and validated OOS before any strategy claim.

## Fresh entry versus occupancy

S5 occupancy itself carries weaker bearish-continuation information:

- 10-bar S5 occupancy: 7 / 9 markets have positive aligned median; equal-market mean aligned hit rate **52.24%**;
- fresh S5 10-bar entry: 9 / 9; **55.40%**.

This supports the Phase-A question that **fresh entry contains more information than simple occupancy for S5**, at least at the 10-bar horizon.

The same conclusion does not generalize to S2.

Fresh S2 at 10 bars:

- only **3 / 9** markets have a strictly positive aligned median;
- equal-market mean bullish hit rate: **49.13%**;
- pooled bullish hit rate: **48.83%**.

Therefore a symmetric `fresh S2 long / fresh S5 short` strategy is **not** supported by this Phase-A sample.

## Reciprocal-symmetry finding

Classifier construction is reciprocal, but realized forward behavior is not.

At the fresh-entry 10-bar horizon, S5 is materially more coherent than S2 in 8 of 9 markets by hit-rate difference; EURUSD is the only small exception. The directional asymmetry is particularly visible in rates, but the fresh-S5 10-bar result is also positive across all three FX markets.

This does not prove a classifier defect. Market conditional behavior is not required to be symmetric merely because the classifier logic is symmetric.

## Baseline-drift check

To guard against interpreting long-run yield decline as classifier information, fresh-S5 10-bar behavior was compared descriptively with each market's own all-formal-stage 10-bar baseline.

- bearish hit-rate lift is positive in **8 / 9** markets;
- normalized-median lift is positive in **6 / 9** markets;
- all three FX markets show positive hit-rate lift and positive normalized-median lift.

DE10Y is the weakest market on this comparison and retains the separate data-completeness caveat. FR10Y and GB10Y show weaker median lift despite positive fresh-S5 bearish medians.

The cross-asset result is therefore not explained solely by the secular decline in developed-market yields, although the magnitude is not uniformly strong.

## Canonical-transition finding

Canonical lifecycle transitions do not generally improve on fresh-stage entry.

- S4 -> S5 has 174 total observations. At 10 bars, 7 / 9 markets have positive aligned median and the equal-market mean bearish hit rate is about 52.36% — weaker than generic fresh S5.
- S1 -> S2 has 165 observations and is not consistently bullish at 1/5/10 bars; its 20-bar result is better but not strong enough to override the weak shorter-horizon evidence.
- S2 -> S3, S3 -> S2, S5 -> S6, and S6 -> S5 are too sparse for a serious direct-signal conclusion.

Thus the current evidence favors **fresh formal S5 entry itself**, not a specific preceding-stage transition.

## Answers to preregistered Phase-A questions

1. **Do formal stages have different forward distributions?** Yes, descriptively. The clearest difference is the bearish continuation associated with S5 versus the weak/neutral behavior of S2.
2. **Does fresh entry contain more information than occupancy?** Yes for S5 at 10 bars; not as a universal rule across stages.
3. **Do canonical transitions behave more coherently than stage labels alone?** No. S4 -> S5 is weaker than generic fresh S5, and the other canonical transitions are either weak or underpowered.
4. **Are S2/S3 and S5/S6 approximately reciprocal after direction alignment?** No in realized forward behavior. S3/S6 are also too sparse to make the intended six-stage reciprocal comparison operationally balanced.
5. **Is any edge broad enough to justify a frozen strategy hypothesis?** Yes, narrowly: fresh S5 -> bearish 10-bar continuation merits a separate OOS hypothesis test.

## What this finding does NOT authorize

Do not change classifier thresholds, weights, confirmBars, representation logic, witnesses, lifecycle memory, HARD caps, or market-specific routing from these results.

Do not add stops, targets, confidence cutoffs, volatility filters, market exclusions, or alternative holding periods inside Issue #76.

Do not call fresh S5 a proven trading edge. The 10-bar horizon has now been selected using the Phase-A full-history descriptive sample and therefore requires independent chronological and/or market-holdout OOS testing.

## Recommended successor hypothesis

Freeze exactly one minimal strategy candidate for the next issue:

> On the first confirmed bar of a fresh formal S5 entry, take the bearish direction of the underlying series and evaluate a fixed 10-bar hold, with no stop, target, confidence filter, or market-specific tuning in the first OOS pass.

Use the next issue to define admissible execution timing, transaction-cost assumptions where relevant, chronological holdout boundaries, and market-holdout tests before any production or PnL conclusion.
