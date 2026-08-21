# Issue #64 — Macro Pressure Map V6.6 Asset-Allocation Research Contract

## Purpose

Validate Macro Pressure Map V6.6 for its intended portfolio role: identifying macro regimes that may justify different asset mixes.

This is not a short-horizon trading-signal study. The primary question is whether portfolio composition conditioned on the frozen V6.6 macro state improves portfolio outcomes versus transparent fixed allocations.

## Inherited evidence from Issue #59

Issue #59 is treated as completed prior evidence:

- Pine ↔ Python parity passed.
- GPI, IPI and FCPI remain descriptive macro-state axes.
- V6.6 production formulas, weights, lookbacks and thresholds remain frozen.
- The prior study did not establish robust standalone directional alpha or incremental predictive lift from GPI+IPI confirmation.
- Historical data already inspected in #59 must not be relabeled as newly untouched evidence.

## Frozen state definition

Primary allocation state = existing V6.6 Growth × Inflation 3×3 regime derived from raw GPI and raw IPI state thresholds.

FCPI is diagnostic / risk context in the first slice. It does not create a 27-state cube in Phase A.

No changes to:

- GPI / IPI / FCPI component definitions;
- component weights;
- lookbacks;
- thresholds;
- raw-vs-smoothed state semantics;
- regime labels;
- production Pine code.

## Phase A — descriptive cross-asset regime map

Initial investable universe:

- SPY — U.S. equities;
- TLT — long-duration U.S. Treasuries;
- GLD — gold.

If a chosen public series does not provide a usable common history, the implementation may substitute an economically equivalent total-return proxy only if the substitution and resulting date boundary are documented before result interpretation.

Primary horizons:

- approximately 1 month;
- approximately 3 months;
- approximately 6 months.

For every 3×3 Growth × Inflation regime, report:

- observation count and occupancy;
- regime episode count and duration distribution;
- forward total-return distribution for SPY / TLT / GLD;
- annualized volatility where meaningful;
- downside behaviour / drawdown context;
- relative asset ranking;
- cross-asset correlation / diversification behaviour;
- uncertainty intervals with overlapping forward windows handled explicitly.

Phase A is descriptive. It must be completed before constructing a regime-conditioned allocation rule.

## Phase B — minimal portfolio test

Compare the eventual frozen regime allocation against:

1. fixed 60/40 SPY/TLT;
2. fixed equal-weight SPY/TLT/GLD;
3. causal inverse-volatility allocation when data support it;
4. V6.6 regime-conditioned allocation.

The V6.6 mapping must use a small explainable set of discrete allocation templates. No unrestricted mean-variance optimization or per-regime weight fitting is allowed.

The exact mapping must be determined from development evidence only and frozen before later evaluation.

## Portfolio accounting contract

- state decisions use only information available at the decision date;
- execute no earlier than the next bar after a confirmed state;
- turnover is measured against drifted pre-trade portfolio weights;
- apply a fixed transaction-cost sensitivity separately from gross results;
- no same-day future information;
- no retroactive state relabeling;
- no result-driven threshold changes;
- preserve explicit development / exploratory / untouched boundaries.

## Primary portfolio metrics

- CAGR / annualized return;
- annualized volatility;
- Sharpe;
- maximum drawdown;
- Calmar;
- turnover;
- transaction-cost drag;
- average allocation by regime;
- asset contribution;
- regime contribution;
- concentration of performance in a small number of episodes.

## Interpretation categories

The final study must choose one bounded verdict:

- `useful_for_regime_asset_allocation`
- `risk_management_value_only`
- `descriptive_cross_asset_structure_only`
- `no_material_allocation_value`
- `inconclusive_insufficient_evidence`

A regime need not significantly forecast every individual asset to be useful for portfolio allocation. The relevant test is whether regime information improves portfolio composition and portfolio-level outcomes versus transparent fixed benchmarks.

## Expansion gate

Do not add short-duration bonds, cash, USD/FX, crude oil, credit or FCPI-conditioned portfolio rules before the SPY/TLT/GLD first slice is understood.

If the first slice is negative or incoherent, stop rather than adding assets to search for a better result.

## Deliverables

- deterministic evaluator using the merged V6.6 Python mirror;
- explicit public-data provenance and common-date boundary;
- regime-conditioned asset statistics;
- machine-readable Phase A results;
- benchmark and regime-allocation evaluator if Phase A supports Phase B;
- accounting / lag / turnover / period-separation tests;
- final decision memo.

Refs #64, #59 and merged PR #60.
