# Issue #68 — B3.12 Human Review Closeout / B3.13 Direction

Status: diagnostic research only; no classifier or strategy change.

## B3.12 human review

Reviewed TradingView B3.12 Structure-step audit on:

- FR10Y 1D — primary adverse long-rates case;
- JGB10Y 1D — control;
- GB10Y 1D and US10Y 1D — supplementary cross-market checks.

Observed pattern:

- Structure is visibly a major discrete recognition switch and repeatedly lines up with MA50/MA200 relation changes.
- FR10Y shows the clearest adverse pattern: price/yield trend can look established while Break/RAW/Structure remain fragmented before later alignment.
- JGB10Y is the cleaner control: once Structure/MA relations align with the rising-yield direction, the target side is more persistent.
- GB10Y and US10Y confirm that the Structure layer can remain choppy in less-clean trend paths.
- The universal story `Break knows early and simply waits for MA50` is rejected. Frozen-FX B3.12 found Break already target-positive at t-1 in only 83/373 handoffs (22.3%).

## Mechanical context retained

B3.12 frozen-FX result:

- 373 exact S2/S5 raw handoffs;
- Structure improves on 308/373 (82.6%);
- MA50-only crossing on 280 handoffs, MA200-only 14, both 14, neither 65;
- all Structure improvements explained by MA-relation changes;
- reciprocal attribution gates >=99%.

B3.11 already demoted Trace: it is visibly stale but did not keep total raw on the old side in any of 1,479 five-component-consensus stale-Trace bars.

## Decision

Proceed to **B3.13 — Continuous Structure Shadow Audit** before changing C-2.

The question is narrow: does replacing only the discrete Structure step with a continuous, symmetry-preserving shadow representation produce earlier S2/S5 raw recognition without materially increasing raw sign churn?

No PnL, no Strategy Tester, no parameter search, no MA-length tuning, no Structure-weight tuning, and no production formula change are allowed in B3.13.
