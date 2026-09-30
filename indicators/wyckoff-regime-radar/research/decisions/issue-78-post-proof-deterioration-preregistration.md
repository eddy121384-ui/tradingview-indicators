# Issue #78 — Post-Proof Deterioration Signal Preregistration

## Purpose

Issue #78 has now frozen two viable add-risk benchmarks:

1. simple benchmark: 25% probe -> 100% after +1 entry-ATR directional proof;
2. progressive benchmark: 25% -> 50% at +0.5 ATR -> 75% at +1 ATR -> 100% at +2 ATR.

The next unresolved question is the de-risk side:

> **After a trend has already proved itself, which causal deterioration signal best distinguishes a normal pullback from a trend that is genuinely losing continuation potential?**

This pass is diagnostic. It does not choose de-risk percentages and does not optimize a production stop.

## Frozen sample

Reuse the accepted Issue #76 nine-market daily sample:

- 68,118 accepted event rows;
- 1,624 completed known-start Markup / Markdown episodes;
- same entry-ATR normalization;
- same formal-regime boundaries;
- no classifier changes.

## Frozen post-proof eligibility

Primary deterioration analysis begins only after an episode has first reached **+1.0 entry ATR** of direction-aligned cumulative progress.

Why +1 ATR:

- it is already frozen from the Confirmation Tax study;
- it is the simple add-risk benchmark's Full-exposure trigger;
- the progressive ladder has already reached at least 75% exposure there;
- using it avoids mixing initial-entry failure with management deterioration.

The +1 ATR proof requirement is fixed before deterioration outcomes are inspected.

## Deterioration family A — Giveback from running favorable extreme

Use only the already-frozen Issue #78 giveback landmarks:

- 0.5 ATR
- 1.0 ATR
- 2.0 ATR
- 4.0 ATR

For each episode and threshold, record only the **first** post-proof crossing where current cumulative progress is that many entry ATR below the running favorable close-path extreme.

No other giveback threshold may be introduced.

## Deterioration family B — Stalled progress / no new favorable extreme

Use only the already-reused lifecycle landmarks:

- 5 completed moves without a new favorable close-path extreme;
- 10 moves;
- 20 moves.

The stall clock resets whenever a new favorable extreme is observed.

For each threshold, record the first post-proof event where the current active trend has gone that many completed moves without a new favorable extreme.

No other stall length may be introduced.

## Frozen forward outcomes

At each first deterioration event, using only path after the event:

1. **Recovery flag:** does the same formal episode make a new favorable close-path extreme above the pre-event running extreme before formal regime loss?
2. **Bars to recovery** if recovery occurs.
3. **Regime ends before recovery** flag.
4. **Additional favorable excursion from event close** before formal regime loss.
5. **Additional adverse excursion from event close** before formal regime loss.
6. **Net direction-aligned move from event close to formal regime loss.**
7. **Remaining regime life** in completed moves.
8. **Future +1 ATR continuation flag** from event close.
9. **Future +2 ATR continuation flag** from event close.

Already-realized pre-event movement is excluded from forward outcomes.

## Primary comparisons

### A. Giveback severity gradient

Across 0.5 / 1 / 2 / 4 ATR first-passage giveback events, ask:

- does recovery probability decline monotonically?
- does regime-end-before-recovery increase?
- does future favorable excursion shrink?
- does future adverse excursion rise?
- does remaining regime life shorten?

### B. Stall-duration gradient

Across 5 / 10 / 20 moves without a new extreme, ask the same questions.

### C. Giveback versus stall

Compare whether one family provides a cleaner, broader deterioration ordering across:

- markets;
- Markup / Markdown;
- 2010–2014;
- 2015–2019;
- 2020–2026.

No scalar winner is selected from pooled data alone.

## Decision logic

A deterioration family is promotable to the next de-risk-policy study only if it shows broadly consistent forward orientation:

- stronger deterioration -> lower recovery probability;
- stronger deterioration -> more frequent regime end before recovery;
- stronger deterioration -> less remaining favorable opportunity and/or more adverse path;
- relationship visible in a clear majority of markets;
- no dependence on only one direction;
- temporal slices remain broadly interpretable, including 2015–2019.

### Interpretation categories

This diagnostic may support a later architecture such as:

- **warning / stop-add:** deterioration is common but recovery remains frequent;
- **de-risk:** deterioration materially lowers recovery and continuation;
- **hard defensive state:** severe deterioration rarely recovers before formal regime loss.

These action labels are interpretations only in this pass. No exposure percentage is assigned yet.

## Guardrails

- no new ATR thresholds;
- no new stall-day thresholds;
- no market-specific rules;
- no separate Markup / Markdown optimization;
- no alternate +1 ATR proof gate;
- no classifier retuning;
- no de-risk exposure percentage search;
- no same-bar hindsight action;
- no threshold chosen solely because it maximizes PnL;
- all current evidence remains in-sample discovery.

## Intended output

Answer:

> **After a trend has earned meaningful exposure, what observable deterioration is merely normal trend noise, and what deterioration is strong enough to justify stopping adds or reducing risk?**

Only after this diagnostic is frozen may Issue #78 convert the surviving deterioration family into an explicit de-risk ladder.

Refs #78, #80, #76.
