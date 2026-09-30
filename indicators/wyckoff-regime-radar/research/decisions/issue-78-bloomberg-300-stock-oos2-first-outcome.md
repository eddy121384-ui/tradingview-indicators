# Issue #78 — Bloomberg 300-Stock OOS2 Diagnostic
## First untouched economic outcome lock

## Status

This document records the **first untouched workstation economic output** from the preregistered Bloomberg 300-stock survivorship-limited OOS2 diagnostic.

The analyzer, cohort, entry eligibility, aggregation rules and interpretation gates were frozen before this result was inspected.

No rescue retuning is permitted after this point.

PR #80 remains Draft / open / unmerged.

---

## Integrity

- frozen classifier blob:
  `1eec08e791403453853b589373bb2270c508c3bb`
- frozen universe SHA-256:
  `e6f07371c9306f2598115cb886cc1cd5d4970d9fdc5e87dd1882bbac304c5712`
- raw files: **300**
- raw failures: **0**
- stocks in universe: **300**
- completed eligible episodes: **19,926**
- B3 events: **11,638**
- P1/P2 events: **3,772**
- primary stocks with >=5 completed eligible episodes: **268**
- survivorship-limited: **true**

Path-construction diagnostics:

- accepted: 11,638
- no breakout: 5,476
- too short: 2,332
- B3 ineligible: 480

---

## Primary R0 NoDerisk result

Primary cross-sectional weighting is one stock, one vote.

- stocks: **268**
- episodes represented: **19,896**
- equal-stock mean expectancy: **-0.142345 ATR**
- median stock expectancy: **-0.149439 ATR**
- positive-stock fraction: **32.84%**
- 25th percentile stock expectancy: **-0.358331 ATR**
- 75th percentile stock expectancy: **+0.086148 ATR**
- equal-stock win rate: **29.74%**
- equal-stock average winner: **+2.370148 ATR**
- equal-stock average loser: **-1.210233 ATR**
- equal-stock payoff ratio: **2.0492**
- equal-stock profit factor: **0.9071**
- equal-stock average exposure: **0.4333**
- equal-stock turnover per episode: **1.0524**

Frozen classification:

> **Diagnostic Weak / Failed**

The failure is cross-sectional breadth, not dependence on one exceptional winner.

---

## R0 concentration

Among 88 stocks with positive mean expectancy:

- top 1% positive-stock count: **1**
- top 1% contribution share: **7.52%**
- top 5% positive-stock count: **5**
- top 5% contribution share: **25.00%**
- best single-stock positive contribution share: **7.52%**
- equal-stock mean after removing top 1% positive stocks:
  **-0.150323 ATR**

The concentration gate itself passes, but the aggregate expectancy remains negative.

---

## Frozen R0 interpretation gates

- equal-stock mean > 0: **FAIL**
- median stock expectancy > 0: **FAIL**
- positive-stock fraction >=55%: **FAIL**
- top 1% positive contribution share <25%: **PASS**
- equal-stock mean remains >0 after top-1% removal: **FAIL**
- >=4 of 5 temporal blocks positive: **FAIL**
- >=8 sectors positive: **FAIL**
- no single sector required for positive mean: **FAIL**

Adequate temporal blocks:

- represented: **5 / 5**
- positive: **2 / 5**

Adequate sectors:

- represented: **11 / 11**
- positive: **1 / 11**

This is not a borderline classification.

---

## R0 + WarningFirst

Primary equal-stock result:

- equal-stock mean expectancy: **-0.124254 ATR**
- median stock expectancy: **-0.119002 ATR**
- positive-stock fraction: **31.34%**
- equal-stock win rate: **29.20%**
- equal-stock average winner: **+2.116058 ATR**
- equal-stock average loser: **-1.055798 ATR**
- equal-stock payoff ratio: **2.0704**
- equal-stock profit factor: **0.9017**
- equal-stock average exposure: **0.3948**
- equal-stock turnover per episode: **1.1287**

WarningFirst improves equal-stock raw expectancy versus R0 by:

**+0.018091 ATR per stock-mean episode**

but does not turn the cross-sectional expectancy positive.

---

## WarningFirst defensive transport

The frozen defensive gate passes strongly:

- lower bar volatility: **100.0%** of eligible stocks
- lower max drawdown: **91.79%**
- better / less-negative ES5: **99.63%**
- better MFE <4 ATR harvest: **85.82%**
- MFE >=8 R0 equal-stock mean harvest: **+4.624687 ATR**
- MFE >=8 WarningFirst mean harvest: **+4.184273 ATR**
- large-trend retention: **90.48%**
- strong defensive gate: **PASS**

Therefore the defensive risk-shaping layer transports much better than the underlying cross-sectional raw-return edge.

WarningFirst is not a rescue of R0 expectancy; it is a portable damage-control mechanism on this diagnostic cohort.

---

## Immediate interpretation

The first 300-stock diagnostic rejects the hypothesis that the already-frozen R0 architecture has broad positive expectancy across present-day U.S. individual equities.

The evidence is broad:

- mean expectancy is negative;
- median expectancy is negative;
- only 32.84% of primary stocks are positive;
- only 2 of 5 temporal blocks are positive;
- only 1 of 11 adequately represented sectors is positive.

The positive-stock contribution is not excessively concentrated, so the failure cannot be explained as a small number of winners distorting an otherwise positive cross-section.

The strongest transported component is WarningFirst risk shaping, not R0 raw expectancy.

---

## Firewall after first outcome

The following remain prohibited on this cohort:

- stock-specific thresholds;
- sector-specific thresholds;
- separate Markup / Markdown policy;
- changing price or liquidity eligibility;
- changing the 5-episode rule;
- dropping weak sectors or names;
- adding a new Resume trigger;
- WarningFirst v2;
- adding a third policy.

Further work on this cohort is diagnostic only.

The next step is to inspect the already-generated frozen diagnostic tables for:

- temporal block pattern;
- sector pattern;
- Markup / Markdown split;
- size-sleeve pattern;
- MFE slices;
- WarningFirst risk-shaping detail.

These diagnostics explain the failure; they must not be used to retune this cohort.

Refs #78, #119, #131, #80.
