# Issue #78 — Confirmation Tax / Time-to-Proof Preregistration

## Purpose

Issue #78 has established two relevant facts:

1. beginning a fresh Markup / Markdown episode with controlled exposure reduces false-start damage, but delayed participation sacrifices some large-trend harvest;
2. realized directional progress is a cleaner add-risk state variable than adding directional path efficiency as a second gate.

The next question is therefore:

> **How much directional price proof should be required before increasing exposure, and how much trend opportunity is consumed while waiting for that proof?**

This study measures the **confirmation tax**. It does not optimize a production threshold.

## Frozen sample

Reuse the accepted Issue #76 nine-market daily sample and completed known-start Markup / Markdown episodes used by prior Issue #78 studies.

Expected accepted data:

- 68,118 event rows;
- 1,624 completed known-start trend episodes;
- same nine daily markets;
- same entry-ATR normalization;
- no classifier changes.

## Frozen proof thresholds

Use only existing Issue #76 / #78 discovery landmarks:

- **+0.5 entry ATR**
- **+1.0 entry ATR**
- **+2.0 entry ATR**

A proof threshold is reached on the first completed daily move whose cumulative direction-aligned move from episode entry is at or above the threshold.

No other ATR threshold may be introduced after outcomes are inspected.

## Frozen time-to-proof buckets

For episodes that reach a threshold, classify first-passage time using existing lifecycle landmarks:

- **Fast:** 1–5 completed moves
- **Medium:** 6–10
- **Slow:** 11–20
- **Very slow:** 21+

These buckets are diagnostic. They are not sizing rules.

## Primary questions

### A. What fraction of trend episodes ever earn each proof threshold?

For each threshold report:

- share of all episodes that reach it;
- Markup / Markdown diagnostics;
- per-market hit rate;
- temporal slices 2010–2014, 2015–2019, 2020–2026.

This quantifies how restrictive each confirmation level is.

### B. How much opportunity remains after proof?

At the first passage of each threshold, measure only future path from the proof close onward:

- remaining directional net move;
- remaining favorable excursion;
- remaining adverse excursion;
- probability of at least +1 / +2 / +4 ATR additional favorable excursion;
- remaining regime life.

Already-realized pre-proof movement is excluded from forward outcomes.

### C. How large is the confirmation tax?

For each episode and threshold report:

- proof threshold itself;
- realized directional move consumed before proof;
- fraction of total episode MFE already consumed when proof occurs;
- fraction of total favorable opportunity still remaining;
- bars required to prove.

The main practical question is whether stronger proof filters false starts faster than it consumes later opportunity.

### D. Does proof speed matter beyond proof magnitude?

Within each threshold, compare Fast / Medium / Slow / Very slow first passage.

Question:

> At the same proof magnitude, does reaching it quickly leave meaningfully better continuation than reaching it slowly?

This is the main candidate second dimension because prior research did not justify path efficiency as an independent add-risk gate.

### E. Simple causal exposure audit

Without optimizing exposure percentages, compare two frozen conceptual policies:

1. **Full-at-entry baseline:** 100% exposure from fresh Markup / Markdown.
2. **Probe-then-full proof policy:** 25% exposure until the threshold is first reached, then 100% from the next completed move onward; if proof is never reached, remain at 25% until formal regime loss.

Run separately for +0.5 / +1 / +2 ATR proof.

Report:

- harvested direction-aligned move;
- failed/small episode damage for MFE <4 ATR;
- large-trend harvest for MFE >=8 ATR;
- average exposure;
- time below full exposure;
- difference versus Full-at-entry.

The 25% probe is reused from the already-preregistered Participation Ramp architecture and is not optimized here.

## Primary decision logic

This study does **not** select the numerically best threshold.

A proof level is considered practically interesting only if it shows a credible frontier:

- materially less exposure to episodes that never develop;
- substantial remaining favorable opportunity after proof;
- no dependence on one market or one direction;
- relationship remains visible across eras, including 2015–2019;
- faster proof is not merely a hindsight label and is measurable causally.

If +2 ATR consumes too much of the trend before Full exposure, it is too late even if it is more selective.

If +0.5 ATR barely separates failed episodes from durable trends, it is too early even if its confirmation tax is low.

## Anti-overfit guardrails

- no new proof thresholds;
- no search over 0.25 / 0.75 / 1.5 ATR or other intermediate levels;
- no optimizing probe percentage;
- no market-specific thresholds;
- no separate Markup / Markdown policy;
- no classifier retuning;
- no selecting a preferred rule from one scalar PnL metric;
- no future MFE / final trend label in live proof decisions;
- final MFE slices are evaluation labels only;
- all proof decisions are first-passage and next-bar causal;
- all current evidence remains in-sample discovery.

## Intended output

The research should answer:

> **How much confirmation is enough to reduce false-start exposure without paying an excessive confirmation tax in genuine large trends?**

If the frontier is clear, a later preregistration may freeze one or more candidate proof ramps for heterogeneous / weekly / prospective validation.

Refs #78, #80, #76.
