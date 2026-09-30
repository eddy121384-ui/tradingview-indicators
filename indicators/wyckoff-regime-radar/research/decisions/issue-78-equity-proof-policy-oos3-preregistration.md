# Issue #78 — Equity Proof-Based Sizing OOS3 preregistration

Date: 2026-09-30

## Purpose

The first Bloomberg 300-stock diagnostic showed that the frozen R0 architecture does not have broad standalone cross-sectional expectancy, but the independent early-proof feature family replicated strongly:

- E5 / E10 cumulative direction-aligned move;
- E5 / E10 directional path efficiency;
- strong Failed-vs-Large separation;
- clean E5 separation of future UsableB3 vs NoUsableB3.

This study asks the next causal question:

> Can a previously frozen proof-based participation architecture improve the stock cross-sectional risk / return frontier on a completely untouched second stock cohort?

This is a policy transport study. It is not a threshold search.

---

## Untouched OOS3 cohort

Build a second deterministic 300-stock cohort from the **same frozen Issue #119 Bloomberg candidate snapshot**, not from a refreshed index-membership query.

Source sleeves remain:

- SPX Index: 100 stocks;
- MID Index: 100 stocks;
- SML Index: 100 stocks.

Before sampling, exclude:

1. all FIGIs in the first 300-stock Issue #119 / OOS2 cohort;
2. AAPL / JPM / XOM calibration fixtures;
3. any security failing the same frozen Issue #119 eligibility rules.

Use the same equal-sector-within-sleeve deterministic allocation logic.

New seed:

`issue78-equity-proof-policy-oos3-v1`

The OOS3 universe SHA-256 must be frozen before any OOS3 price history or strategy economics are inspected.

No failed or sparse security may be replaced after outcomes are visible.

This remains a current-constituent survivorship-limited diagnostic cohort; it is not a point-in-time / delisted-security test.

---

## Data and episode contract

Reuse the exact Issue #119 / Issue #78 stock pipeline:

- raw Bloomberg OHLCV start: 1998-01-01;
- formal event window: 2000-01-03 through 2026-08-31;
- split-adjusted, not cash-dividend-backadjusted;
- same OHLC normalization;
- same frozen classifier blob:
  `1eec08e791403453853b589373bb2270c508c3bb`;
- same fresh formal Markup / Markdown episode construction;
- same entry eligibility:
  - >=252 prior valid daily OHLC rows;
  - split-adjusted close >=$5;
  - prior 60 sessions all finite close / volume;
  - trailing 60-session median dollar volume >=$5m;
- same completed-episode accounting;
- same one-stock-one-vote primary aggregation;
- same >=5 completed eligible episodes requirement for primary stock tables.

No stock-specific, sector-specific, direction-specific, or era-specific parameters.

---

## Frozen policy set

All exposure decisions use only information available through the completed current bar and apply to the **next** move.

### A. R0_NoDerisk

Existing frozen stock benchmark:

- 25% Probe at fresh formal entry;
- first usable frozen B3 path;
- P0 / P1 / P2 -> Full at the frozen t+3 decision;
- P3 / no usable B3 -> remain Probe;
- no deterioration overlay.

### B. R0_WarningFirst

Existing frozen R0 plus the frozen WarningFirst deterioration latch.

No WarningFirst v2.

### C. Proof1_NoDerisk

Previously frozen macro proof architecture, transported without retuning:

- 25% Probe from fresh formal entry;
- when cumulative direction-aligned close move from entry first reaches **+1.0 entry ATR**, earn 100% exposure for the next move;
- if +1 ATR is never reached, remain at 25% until formal regime loss;
- no B3 requirement;
- no deterioration overlay.

### D. Proof1_WarningFirst

Same +1 ATR earned-exposure rule, with the **existing frozen WarningFirst** deterioration latch applied to currently earned exposure.

### E. ProgressiveProof_NoDerisk

Previously frozen progressive proof ladder:

- 25% before +0.5 entry ATR proof;
- 50% after +0.5 ATR proof;
- 75% after +1.0 ATR proof;
- 100% after +2.0 ATR proof;
- proof is first-passage cumulative direction-aligned close move from episode entry;
- exposure change applies to the next move;
- earned proof levels are not revoked by the participation layer;
- formal regime loss exits;
- no B3 requirement;
- no deterioration overlay.

### F. ProgressiveProof_WarningFirst

Same progressive proof ladder with the existing frozen WarningFirst deterioration latch applied to currently earned exposure.

No other proof level, exposure percentage, timeout, efficiency gate, or B3 hybrid is permitted in this pass.

---

## WarningFirst overlay contract

Reuse the already-frozen stock WarningFirst semantics without change:

- giveback <2 ATR: no reduction;
- giveback 2–4 ATR: reduce currently earned exposure by 25 percentage points;
- giveback >=4 ATR: reduce currently earned exposure by 50 percentage points;
- minimum positive exposure remains 25%;
- reductions latch;
- a new favorable close extreme resets the deterioration latch.

This overlay is evaluated only as the already-frozen damage-control layer.

---

## Primary questions

### 1. Does proof-based sizing improve broad stock expectancy?

For each policy report:

- equal-stock mean expectancy;
- median stock expectancy;
- positive-stock fraction;
- equal-stock profit factor;
- win rate;
- average winner / loser;
- average exposure;
- turnover.

### 2. Does it specifically reduce failed-trend bleed?

For final MFE <4 ATR report:

- equal-stock mean harvest;
- fraction of primary stocks whose harvest improves vs R0_NoDerisk.

### 3. How much large-trend participation is retained?

For final MFE >=8 ATR report:

- equal-stock mean harvest;
- retention vs R0_NoDerisk;
- fraction of primary stocks retaining at least the benchmark directionally.

### 4. Does WarningFirst still add defensive value on top of proof sizing?

For paired NoDerisk / WarningFirst versions report:

- bar-return volatility;
- max drawdown;
- ES5;
- MFE<4 harvest;
- MFE>=8 harvest retention;
- turnover.

---

## Primary breadth / robustness diagnostics

Without retuning, report:

- Markup / Markdown;
- large / mid / small sleeve;
- 11 frozen current-sector labels;
- event-entry blocks:
  - 2000–2004
  - 2005–2009
  - 2010–2014
  - 2015–2019
  - 2020–2026.

No subgroup creates a separate policy.

---

## Interpretation gates

The same broad positive-expectancy gates used in OOS2 remain the standard for any standalone policy claim:

- equal-stock mean expectancy >0;
- median stock expectancy >0;
- >=55% primary stocks positive;
- top 1% positive-stock contribution share <25%;
- mean remains >0 after removing top 1% positive stocks;
- >=4/5 adequate temporal blocks positive;
- >=8/11 adequate sectors positive;
- no single sector required for a positive overall mean.

A proof policy can still be called a **useful transport / frontier improvement** without passing the standalone-alpha gate only if all of the following are true:

- equal-stock mean expectancy is better than R0_NoDerisk;
- median stock expectancy is better than R0_NoDerisk;
- positive-stock fraction is better than R0_NoDerisk;
- MFE<4 harvest improves in >=60% of paired primary stocks;
- MFE>=8 equal-stock harvest retention vs R0_NoDerisk is >=80%.

These are frozen before OOS3 outcomes are inspected.

No single scalar metric chooses a winner.

---

## Explicit guardrails

After OOS3 results are inspected, do not:

- change +0.5 / +1 / +2 ATR proof levels;
- change 25 / 50 / 75 / 100% exposure states;
- add E5 or E10 timeout rules;
- add directional-efficiency gates;
- combine B3 and proof in a new hybrid;
- drop Markup or Markdown;
- filter by size sleeve or sector;
- change liquidity or price eligibility;
- replace failed securities;
- create a new WarningFirst version;
- select stock-specific thresholds;
- retune based on 2015–2019 or 2020–2026.

Any such idea requires a new preregistered study and a new untouched cohort.

PR #80 remains Draft / open / unmerged.

Refs #78, #131, #132, #80.
