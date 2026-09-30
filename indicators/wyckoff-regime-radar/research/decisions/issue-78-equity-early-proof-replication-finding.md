# Issue #78 — Equity Early-Proof Replication finding

Date: 2026-09-30

## Status

This document records the **first untouched Bloomberg 300-stock early-proof replication output**.

The E5 / E10 feature family and the Failed <4 ATR / Large >=8 ATR labels were frozen independently in the 2026-09-15 nine-market Big Trend vs Failed Trend study, before the Bloomberg stock OOS2 result existed.

The stock OOS2 economic outcome and autopsy were already known before this run, so this is not a pristine new stock-cohort OOS test. It is an external-feature replication diagnostic plus a post-outcome B3 mechanism diagnostic.

No threshold, composite score, or sizing policy is selected by this finding.

---

## Sample

- completed eligible stock episodes: **19,926**
- Failed (<4 ATR): **14,645**
- Middle (4–8 ATR): **3,243**
- Large (>=8 ATR): **2,038**
- NoUsableB3: **8,288**
- UsableB3: **11,638**

Decision-time survival:

- Failed surviving E5: **91.14%**
- Failed surviving E10: **73.40%**
- Large surviving E5 / E10: **100% / 100%**
- NoUsableB3 surviving E5: **84.34%**
- NoUsableB3 surviving E10: **52.98%**
- UsableB3 surviving E5 / E10: **100% / 100%**

E5 / E10 comparisons condition only on episodes for which that decision time exists.

---

## Primary replication — Failed vs Large

The previously frozen early-proof signal transports strongly into individual equities.

### E5

Cumulative aligned move:

- eligible stocks: **197**
- equal-stock mean AUC: **0.7372**
- median AUC: **0.7328**
- stocks with AUC >0.50: **194 / 197 (98.48%)**
- Large median: **+0.948 ATR**
- Failed median: **-0.293 ATR**

Directional path efficiency:

- equal-stock mean AUC: **0.7234**
- median AUC: **0.7212**
- AUC >0.50: **195 / 197 (98.98%)**

Early MFE remains strong but label-adjacent:

- mean AUC: **0.7145**

Low giveback is secondary:

- mean AUC: **0.6677**

### E10

Cumulative aligned move:

- eligible stocks: **197**
- equal-stock mean AUC: **0.8265**
- median AUC: **0.8324**
- stocks with AUC >0.50: **197 / 197 (100%)**
- Large median: **+2.143 ATR**
- Failed median: **-0.267 ATR**

Directional path efficiency:

- equal-stock mean AUC: **0.8044**
- median AUC: **0.8118**
- AUC >0.50: **197 / 197 (100%)**

Early MFE:

- mean AUC: **0.7932**

Low giveback:

- mean AUC: **0.6970**

---

## Replication versus the prior nine-market study

Prior nine-market equal-market AUC versus stock equal-stock AUC:

- E5 cumulative move: **0.776 -> 0.737**
- E5 directional efficiency: **0.755 -> 0.723**
- E10 cumulative move: **0.842 -> 0.826**
- E10 directional efficiency: **0.815 -> 0.804**

The signal weakens modestly at E5 but is remarkably close to the prior study by E10.

The strongest conclusion is therefore replication, not discovery:

> **large trends tend to prove themselves early after the probe is live, and that behavior transports from the original macro-market study into a broad individual-equity cross-section.**

---

## Quintile ordering

Within-stock quality quintiles are fully ordered for the two main features.

### Failed vs Large — E5 cumulative move

Q1 -> Q5:

- Large share: **3.68% -> 21.02%**
- Failed share: **90.44% -> 45.80%**
- frozen R0 whole-episode harvest: **-0.594 -> +0.399 ATR**

### Failed vs Large — E10 cumulative move

Q1 -> Q5:

- Large share: **2.36% -> 31.50%**
- Failed share: **93.10% -> 26.77%**
- frozen R0 whole-episode harvest: **-0.671 -> +0.621 ATR**

Directional efficiency shows the same monotonic ordering.

The whole-episode R0 harvest diagnostic is descriptive only because it includes the early moves used to assign the quintile. It is not a causal estimate of a new sizing policy.

---

## Robustness

### Direction

Failed-vs-Large cumulative aligned move:

- E5 Markup AUC: **0.698**
- E5 Markdown AUC: **0.760**
- E10 Markup AUC: **0.786**
- E10 Markdown AUC: **0.862**

The quality signal is present in both directions.

This is important because the stock OOS2 autopsy showed much worse Markdown economics. The two facts are compatible:

- early proof can identify comparatively better Markdown trends;
- the frozen R0 Markdown policy can still have poor absolute economics.

No separate direction-specific policy is authorized.

### Size sleeve

Failed-vs-Large E10 cumulative AUC:

- large: **0.808**
- mid: **0.836**
- small: **0.850**

The discriminator does not disappear where raw R0 expectancy was weakest. In fact, separation is at least as strong in smaller stocks.

### Time

Failed-vs-Large E10 cumulative AUC:

- 2000–2004: **0.895**
- 2005–2009: **0.816**
- 2010–2014: **0.815**
- 2015–2019: **0.787**
- 2020–2026: **0.850**

The signal survives every frozen block, including the post-2010 regimes where the raw R0 strategy was negative.

### Sector

Failed-vs-Large E10 cumulative AUC is positive and strong in every adequately represented sector, ranging approximately from:

- **0.776** in Energy
- to **0.852** in Communication Services.

For E10 cumulative move, every eligible stock in every sector slice has AUC >0.50 under the slice-reporting sample.

---

## Secondary mechanism target — UsableB3 vs NoUsableB3

### E5 — clean pre-B3 mechanism evidence

The frozen B3 search cannot begin until after the E5 information set, so E5 is the clean causal mechanism diagnostic.

Cumulative aligned move:

- eligible stocks: **256**
- equal-stock mean AUC: **0.7131**
- median AUC: **0.7158**
- AUC >0.50: **252 / 256 (98.44%)**
- UsableB3 median: **+0.395 ATR**
- NoUsableB3 median: **-0.655 ATR**

Directional path efficiency:

- mean AUC: **0.7093**
- AUC >0.50: **252 / 256 (98.44%)**

Low giveback:

- mean AUC: **0.6931**

This supports the stock-autopsy mechanism:

> **among probes still alive after five completed moves, trends that will later reach a usable B3 state already tend to show better directional progress and path efficiency.**

### E10 caveat

The raw E10 UsableB3-vs-NoUsableB3 AUCs are very high:

- cumulative move: **0.8230**
- directional efficiency: **0.8203**

However, the earliest frozen B3 + t+3 path evidence can already be known by approximately the E10 decision horizon.

Therefore E10 is **not clean evidence of predicting a future B3 state**. It is retained as a descriptive association only and must not be presented as a causal pre-B3 predictor.

The E5 mechanism result is the clean one.

---

## Interpretation

The stock OOS2 failure does **not** imply that the classifier contains no useful information.

The combined evidence now separates the architecture into three layers:

1. **Fresh formal entry alone is too permissive for individual stocks.**
   Many probes die before enough evidence accumulates.

2. **Early causal price proof is highly portable.**
   E5 is already useful; E10 is substantially stronger for distinguishing eventual Large from Failed trends.

3. **The B3 / retest evidence chain and WarningFirst remain useful downstream components.**
   The stock autopsy showed positive usable-B3 path economics in aggregate, particularly on Markup, and strong WarningFirst defensive portability.

The best-supported architecture is therefore still:

> **Probe first; require the trend to earn larger participation through early causal directional proof.**

What failed was the idea that every fresh formal trend deserves the same mechanical path toward larger exposure.

---

## What this finding does NOT authorize

It does not authorize:

- a best E5 / E10 threshold;
- a top-quintile trading rule;
- a combined cumulative-move + efficiency score;
- a new Full-exposure schedule;
- a long-only rescue;
- a large-cap-only rescue;
- a sector-specific rule.

Those would be new policy hypotheses.

---

## Next justified experiment

Freeze a very small proof-based sizing policy **before** seeing results on a new untouched equity cohort.

A practical next validation cohort can be drawn deterministically from the unselected remainder of the same Bloomberg SPX / MID / SML source universes, excluding:

- the current 300-stock cohort;
- AAPL / JPM / XOM calibration fixtures.

This would preserve the same data pipeline and population while providing new securities on which a proof-based sizing policy has not yet been inspected.

PR #80 remains Draft / open / unmerged.

Refs #78, #131, #132, #80.
