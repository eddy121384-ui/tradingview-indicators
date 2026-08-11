# Issue #57 — Top-2 directional consensus hypothesis

Status: **RECORDED BEFORE NEW DIAGNOSTIC**

## Why this note exists

User trading experience with the prior Wyckoff Radar suggests that the **Formal / dominant regime by itself is often late and error-prone**, while the combination of the **first candidate and second-strongest regime weight** may contain more useful directional information.

The practical heuristic observed by the user was approximately:

- identify the two largest six-stage regime weights on the current bar;
- map each stage into a directional family;
- require the top two stages to point in the same direction;
- require their combined weight to be very high (user example: around **90%**);
- when those conditions hold, the subsequent market direction appeared subjectively more likely to follow through than when trading from Formal state alone.

This is a **new research hypothesis**, not a validated claim.

## Directional family mapping for the diagnostic

Use the original six stage weights, not the four-state Formal label:

- bullish family: 1 Accumulation, 2 Markup, 3 Re-accumulation;
- bearish family: 4 Distribution, 5 Markdown, 6 Redistribution.

This preserves the user's actual intuition: the signal is about **agreement among the model's strongest internal hypotheses**, not about the persisted Formal ID.

## Primary signal definition

For every bar, rank the six normalized stage weights from largest to smallest.

Let `Top1` and `Top2` be the two largest stage weights.

A **Top-2 directional consensus** exists when:

1. `Top1` and `Top2` belong to the same directional family; and
2. `Top1 + Top2 >= 90%`.

Direction:

- bullish-family consensus = `+1`;
- bearish-family consensus = `-1`;
- otherwise = `0` / no signal.

The 90% threshold is the **primary preregistered diagnostic threshold because it came from the user's prior live usage heuristic**, not from optimizing the burned research sample.

Nearby thresholds (80%, 85%, 95%) may be reported only as sensitivity diagnostics. They must not replace 90% merely because one produces better PnL.

## What to compare on burned data

The first diagnostic may use already-consumed data only. It is allowed to answer whether this hypothesis is worth a new untouched test, but it cannot validate the signal.

Compare Top-2 directional consensus with:

- Formal-state direction;
- Top-1 directional family alone;
- broad bullish-family weight minus bearish-family weight;
- always-flat / no-signal reference where relevant.

Measure at 5 / 10 / 20 / 60 bars:

- stage-aligned forward return (`direction * forward_return`);
- hit rate (`direction * forward_return > 0`);
- MFE / MAE aligned to direction;
- signal frequency / coverage;
- persistence / episode duration;
- one-bar-lag trading diagnostic with the same 1-pip-per-unit-turnover convention used previously.

The key question is **not** whether 90% maximizes backtest PnL. It is whether high same-direction Top-2 agreement shows a materially cleaner and more stable directional relationship than Formal state.

## Research boundary

The following samples are already burned and cannot validate this hypothesis independently:

- Issue #55 EURUSD / USDJPY / GBPUSD / AUDUSD research partitions, including its Final OOS;
- Issue #57 Phase-E USDCAD / USDCHF / EURCHF cross-market holdout.

They may be used only for hypothesis development / diagnostics.

If the Top-2 consensus hypothesis looks materially stronger on burned data, freeze the definition before obtaining **another untouched sample**. Any final positive claim requires that new sample.

## Interpretation shift under test

This hypothesis intentionally tests whether the Wyckoff engine is more useful as a **directional evidence aggregator** than as a single-label regime classifier.

A positive result would not mean Formal state becomes irrelevant for visualization or context. It would mean the actionable directional layer should be based on internal weight agreement rather than the persisted Formal label.
