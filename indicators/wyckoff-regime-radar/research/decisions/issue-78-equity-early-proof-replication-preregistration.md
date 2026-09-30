# Issue #78 — Equity Early-Proof Replication preregistration

Date: 2026-09-30

## Status and epistemic label

This protocol is frozen **before any 300-stock early-proof separation result is inspected**.

The underlying 300-stock OOS2 economic outcome and its autopsy have already been inspected, so this is **not a pristine new OOS test of the stock cohort**.

However, the feature definitions and the primary Failed / Large label thresholds were frozen independently on 2026-09-15 in the earlier nine-market Big Trend vs Failed Trend study, before the Bloomberg 300-stock OOS2 result existed.

Therefore this study has two explicitly different roles:

1. **External-feature replication diagnostic** — does the previously frozen E5 / E10 early-proof signal transport from nine macro markets into individual equities?
2. **Post-outcome mechanism diagnostic** — does the same early proof distinguish future usable-B3 development from the NoUsableB3 failure mode identified in the stock autopsy?

No result from this study may be used to retune the frozen 300-stock OOS2 cohort.

---

## Frozen cohort and data

Use exactly the Issue #119 Bloomberg 300-stock snapshot and the frozen Issue #78 stock OOS2 entry eligibility / episode construction from PR #131.

Universe SHA-256:

`e6f07371c9306f2598115cb886cc1cd5d4970d9fdc5e87dd1882bbac304c5712`

Classifier blob:

`1eec08e791403453853b589373bb2270c508c3bb`

Use completed eligible episodes only.

Do not replace stocks, change liquidity thresholds, alter the 5-episode primary rule, or change the classifier.

---

## Frozen feature set

No new feature search is allowed.

Reuse only the already-frozen features from the 2026-09-15 Big Trend vs Failed Trend study:

### E5

After the first five completed directional daily moves after entry:

- cumulative direction-aligned move / entry ATR;
- early MFE / entry ATR;
- giveback from early favorable close-path extreme / entry ATR;
- directional path efficiency.

### E10

The same four features after ten completed daily moves.

Expected orientations are unchanged:

- cumulative move: higher is better;
- early MFE: higher is better;
- giveback: lower is better;
- directional path efficiency: higher is better.

No E0 feature is promoted in this replication.

No new window such as E3 / E7 / E15 is permitted.

---

## Primary target A — Failed vs Large trend replication

Reuse the previously frozen labels:

- Failed / small: final directional MFE < 4 entry ATR;
- Large: final directional MFE >= 8 entry ATR;
- 4 <= MFE < 8 retained as Middle and excluded from the binary AUC contrast.

This is the closest apples-to-apples replication of the nine-market feature study.

For E5 / E10, only episodes still alive long enough for the decision to exist are eligible for that information set.

Do not treat episodes that ended before E5 / E10 as if their future feature values were zero.

---

## Secondary target B — NoUsableB3 vs UsableB3 mechanism

Path target:

- NoUsableB3: no usable frozen B3 + t+3 path becomes available before episode termination;
- UsableB3: path is one of P0 / P1 / P2 / P3.

This target is explicitly post-outcome exploratory because the stock autopsy motivated it.

At E5 / E10, evaluate only episodes still alive long enough for the information set.

Separately report the share of NoUsableB3 episodes that terminate before E5 and before E10. This is a persistence diagnostic, not a predictive score.

---

## Primary evaluation

For every feature, information set and target:

1. compute ROC AUC within each stock when at least 3 positive and 3 negative examples exist;
2. report equal-stock mean / median AUC;
3. report number and fraction of eligible stocks with AUC > 0.50;
4. form within-stock feature quintiles over all episodes eligible for that information set;
5. report target positive / negative shares by quintile;
6. report frozen R0 NoDerisk mean episode harvest by quintile as a descriptive economic diagnostic.

No cut-point selection, no optimizer, no classification threshold, no logistic model and no composite score.

---

## Robustness diagnostics

Without retuning, repeat equal-stock AUC aggregation by:

- Markup vs Markdown;
- large / mid / small frozen cohort sleeve;
- the 11 frozen current-sector labels;
- event-entry blocks:
  - 2000–2004
  - 2005–2009
  - 2010–2014
  - 2015–2019
  - 2020–2026.

A subgroup requires at least 5 eligible stocks for reporting.

These slices are explanatory only. They cannot authorize subgroup-specific thresholds.

---

## Frozen interpretation

For target A, the prior nine-market benchmarks are descriptive references only:

- E5 cumulative move ~0.776 equal-market AUC;
- E10 cumulative move ~0.842;
- E5 directional efficiency ~0.755;
- E10 directional efficiency ~0.815.

No minimum AUC is required for success.

The central question is transport:

> Does early causal price proof remain directionally useful across a broad individual-equity cross-section, or was the prior signal specific to macro markets?

For target B, the central mechanism question is:

> Among probes that are still alive at E5 / E10, does early causal proof identify which formal trends will later mature into a usable B3 evidence state?

---

## Guardrails after results

After the first equity early-proof result is inspected:

- no changing E5 / E10;
- no changing 4 / 8 ATR labels;
- no new feature families;
- no stock / sector / sleeve-specific thresholds;
- no separate long / short policy;
- no using early MFE as a hidden optimized production rule;
- no building a composite score on this same cohort.

Any position-sizing policy based on a survivor must be separately preregistered and tested on a new cohort.

Refs #78, #131, #80.
