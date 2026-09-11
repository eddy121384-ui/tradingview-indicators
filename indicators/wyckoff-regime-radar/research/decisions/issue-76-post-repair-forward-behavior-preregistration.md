# Issue #76 — Post-Repair Forward-Behavior Study Preregistration

## Purpose

Measure whether the repaired Wyckoff six-stage classifier contains stable information about subsequent market behavior before constructing or optimizing any trading strategy.

This is an event / forward-distribution study. It is not a Strategy Tester optimization pass.

## Frozen classifier baseline

- Merge commit: `d29b673857e7e2c64a67254efd398b3271b7f172`
- Source: `indicators/wyckoff-regime-radar/src/chase-risk-market-regime-radar-issue68-rc.pine`
- Frozen source blob SHA: `e5c3fd2622841a6d3f97bdda4b9d0a6378ebda55`
- Lineage: frozen v0.5.2.1 + accepted Issue #66 C-2 + Issue #68 yield-safe representation + exact symmetric HARD current-context cap.

During Phase A there is no classifier tuning. Thresholds, stage weights, `confirmBars`, representation routing, lifecycle logic, Volume, MTF, Divergence, and HARD semantics remain frozen.

## Primary universe

Daily observations.

FX:
- EURUSD
- GBPUSD
- USDJPY

10Y government yields:
- US10Y
- DE10Y
- FR10Y
- GB10Y
- AU10Y
- JP10Y

Exact TradingView feed identifiers must be frozen before data collection. A substitution is permitted only when the intended feed is unavailable and must be documented before results are inspected.

## Event layers

1. Stage occupancy: every confirmed bar in formal S1…S6.
2. Fresh formal-stage entry: first confirmed bar after formal stage changes into S1…S6.
3. Canonical transitions:
   - S1 → S2
   - S2 → S3
   - S3 → S2
   - S4 → S5
   - S5 → S6
   - S6 → S5

Other transitions may be reported descriptively but are not primary Phase-A hypotheses.

## Frozen forward horizons

- 1 bar
- 5 bars
- 10 bars
- 20 bars

No alternative horizon search is allowed after viewing results to rescue a weak finding.

## Outcomes

For each market / event / horizon:

- sample count;
- mean forward move;
- median forward move;
- directional hit rate;
- MFE;
- MAE;
- future realized volatility;
- distribution quantiles.

Raw and normalized views:

- FX: log return plus event-time ATR / volatility-normalized move.
- Government yields: basis-point change plus event-time ATR / volatility-normalized move.

MFE and MAE use only a causal normalization scale known at the event bar.

## Directional interpretation

- S2 Markup and S3 Re-accumulation are bullish-direction continuation candidates.
- S5 Markdown and S6 Redistribution are bearish-direction continuation candidates.
- S1 Accumulation and S4 Distribution are transition / exhaustion states; no immediate next-bar reversal is assumed.
- Reciprocal comparisons use direction-aligned normalized outcomes, especially S2/S3 versus S5/S6.

## Anti-overfitting boundary

Full-history descriptive measurement is permitted because Phase A does not select a trading rule. However:

- no stop / target optimization;
- no holding-period optimization;
- no confidence cutoff search;
- no market-specific filters;
- no stage-weight or classifier threshold changes;
- no cherry-picking the best cell into a strategy inside this issue.

If a coherent edge appears, freeze that hypothesis first and open a separate strategy issue with chronological and/or market holdout OOS validation.

## Phase-A decision questions

1. Do formal stages have materially different forward distributions?
2. Does fresh entry contain more information than stage occupancy?
3. Do canonical transitions behave more coherently than stage labels alone?
4. Are S2/S3 and S5/S6 approximately reciprocal after direction alignment?
5. Is any observed edge broad enough across markets and horizons to justify a frozen strategy hypothesis?

Possible decisions:

- `advance_to_frozen_strategy_hypothesis`
- `useful_regime_context_but_not_direct_signal`
- `weak_or_unstable_forward_information`
- `measurement_or_data_pipeline_blocked`

## Operational order

1. Freeze exact classifier source and feed identifiers.
2. Inventory reusable historical data already in the repository.
3. Build deterministic event extractor and tiny fixture tests.
4. Acquire only the missing frozen-feed data.
5. Run the nine-market matrix once.
6. Write pooled, cross-market, reciprocal-symmetry, and final findings before any strategy design.
