# Issue #57 — Transition health → price outcomes (pre-outcome decision)

Status: **REUSED-DATA STRUCTURAL / PRICE-RELEVANCE DIAGNOSTIC ONLY**.

This diagnostic is defined before inspecting its price outcomes. It does not modify v0.6 and does not select a production threshold.

## Question

After an initial bridge handoff in which the carried new stage already leads the old context stage, does the observable health of that handoff at bar +3 have useful information about subsequent real price behavior?

## Frozen observation point

Use **bar +3 after the handoff onset**. Include only handoff events that remain unresolved through +3, matching the prior hold-persistence eligibility rule (`resolution_lag > 3`).

At +3 classify mechanically:

- **healthy_hold**: carried stage has remained strictly above the old context stage on every bar from onset through +3.
- **damaged_retake**: the old context stage has tied or exceeded the carried stage at least once before or at +3.

No severity, duration, companion, Formal, or price filter is added.

## Price measurement timing

The decision state is observable only at the close of +3. Therefore all forward price outcomes start from the **+3 close**, not from the original handoff onset.

For the original intended transition direction, report at fixed horizons **5 / 10 / 20 bars after +3**:

- direction-aligned close-to-close price return;
- favorable excursion (MFE) from the +3 close using future highs/lows;
- adverse excursion (MAE) from the +3 close using future highs/lows;
- direction hit rate (`aligned_return > 0`).

These are price-path diagnostics, not a backtested entry/exit strategy. No costs, stops, sizing, or trading rule are introduced.

## Aggregation

Report:

1. pooled event counts;
2. per-pair group metrics;
3. median across FX pairs for each metric;
4. number of comparable FX pairs where healthy_hold beats damaged_retake on aligned return and hit rate.

Do not choose a horizon after seeing results. All 5/10/20 horizons remain descriptive.

## Interpretation boundary

A useful result requires more than the indicator predicting its own future state. The healthy group should show meaningfully better subsequent price path across multiple FX pairs. If price differences are small or inconsistent, transition-health structure remains descriptive only and should not be promoted to a trading signal.
