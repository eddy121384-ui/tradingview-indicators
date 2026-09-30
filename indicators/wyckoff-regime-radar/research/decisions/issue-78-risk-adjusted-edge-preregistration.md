# Issue #78 — Risk-Adjusted Edge / Equal-Volatility Audit Preregistration

## Purpose

Issue #78 has identified several causal exposure-control architectures that reduce failed-trend damage and reshape the capture-vs-giveback frontier.

The unresolved economic question is now:

> **Do these sizing rules merely reduce risk by carrying less exposure, or do they improve return per unit of risk?**

This audit is designed to distinguish simple deleveraging from genuine state-dependent risk allocation.

It remains an in-sample discovery audit on normalized underlying-move units. It is not executable futures / cash PnL and does not establish production alpha.

## Interpretation

A policy that mechanically halves exposure should approximately halve both mean return and volatility, leaving Sharpe broadly unchanged. That is not evidence of a sizing edge.

A policy is economically more interesting if it selectively removes bad exposure so that:

- return falls less than volatility;
- Sharpe / Sortino improve;
- drawdown and left-tail loss improve;
- after scaling the policy back to the same volatility as a benchmark, expected normalized return is higher.

The last comparison is the primary test against the "it only looks safer because it is smaller" explanation.

## Frozen sample

Reuse the accepted Issue #76 nine-market daily sample:

- 68,118 accepted formal-stage event rows;
- 1,624 completed known-start Markup / Markdown episodes;
- same entry-ATR normalization;
- same right-censor exclusion;
- same causal next-bar exposure timing;
- zero strategy return outside completed active Markup / Markdown episodes.

Per-market daily paths are built on each ticker's accepted event-row sequence through the end of its last completed included episode. No calendar filling or synthetic weekend observations are introduced.

## Frozen policy set

No new policy is invented in this audit.

### Baseline

1. **Formal Hold** — 100% from fresh formal trend entry until formal regime loss.

### Simple +1 ATR add-risk family

2. **Simple / No de-risk** — 25% until +1 ATR favorable proof, then 100%.
3. **Simple / Warning-First** — same add-risk; tolerate <2 ATR giveback, reduce one 25pp step at 2–4 ATR, two 25pp steps at 4+ ATR; re-risk only on a new favorable extreme.
4. **Simple / Gentle latch** — same add-risk plus frozen Gentle damage latch.
5. **Simple / Balanced latch** — same add-risk plus frozen Balanced damage latch.

### Progressive proof-ladder family

6. **Progressive / No de-risk** — 25% -> 50% at +0.5 ATR -> 75% at +1 ATR -> 100% at +2 ATR.
7. **Progressive / Warning-First** — same ladder plus Warning-First latch.
8. **Progressive / Gentle latch** — same ladder plus Gentle latch.
9. **Progressive / Balanced latch** — same ladder plus Balanced latch.

No policy parameters may change after results are viewed.

## Daily normalized return construction

For each completed episode:

- convert each one-bar move into direction-aligned entry-ATR units;
- determine exposure using information available before that move;
- daily normalized strategy return = exposure × direction-aligned move;
- assign that return to the corresponding accepted logger row;
- all accepted rows outside completed active episodes receive zero strategy return.

This creates one comparable normalized daily path per market and policy.

## Primary per-market metrics

For every market × policy report:

- mean daily normalized return;
- annualized normalized return = mean daily return × 252;
- annualized volatility = sample standard deviation × sqrt(252);
- Sharpe-like ratio = mean / standard deviation × sqrt(252), with zero risk-free rate;
- downside deviation using negative daily returns;
- Sortino-like ratio = annualized mean / annualized downside deviation;
- cumulative normalized return;
- maximum drawdown of the cumulative normalized-return path;
- Calmar-like ratio = annualized normalized return / max drawdown where defined;
- 5% expected shortfall / CVaR of daily normalized returns;
- 1% daily return quantile;
- average daily exposure;
- annualized exposure turnover.

These are normalized-move diagnostics, not dollar-return claims.

## Primary equal-volatility test

Within each market, use **Formal Hold annualized volatility** as the frozen reference volatility.

For every non-baseline policy with positive nonzero volatility:

`equal_vol_scale = formal_hold_vol / policy_vol`

`equal_vol_ann_return = policy_ann_return × equal_vol_scale`

No leverage cap is imposed because this is a diagnostic decomposition, not a proposed trading implementation.

Interpretation:

- if a lower-risk policy merely deleverages indiscriminately, equal-vol scaling should approximately restore the baseline return;
- if equal-vol scaled return exceeds Formal Hold, the policy has allocated exposure more efficiently in that sample.

Also perform family-local comparisons:

- Simple / Warning-First vs Simple / No de-risk;
- Progressive / Warning-First vs Progressive / No de-risk;
- Gentle / Balanced vs their corresponding no-de-risk add-risk benchmark.

For each comparison report the count of markets where:

- Sharpe-like ratio improves;
- Sortino-like ratio improves;
- max drawdown declines;
- 5% expected shortfall becomes less negative;
- equal-vol scaled annualized return exceeds the comparator's annualized return.

## Return-retention versus risk-retention diagnostic

For each market and policy relative to Formal Hold:

- return retention = policy annualized return / Formal Hold annualized return where the baseline mean is nonzero;
- volatility retention = policy volatility / Formal Hold volatility.

Where signs permit interpretation, a policy has favorable compression when return retention exceeds volatility retention.

Because ratios become unstable around zero or negative baseline means, the equal-vol test and Sharpe comparison remain primary.

## Cross-market aggregation

Primary aggregation remains equal-market.

Report:

- equal-market mean and median Sharpe-like ratio;
- equal-market mean and median Sortino-like ratio;
- equal-market mean annualized normalized return;
- equal-market mean annualized volatility;
- equal-market mean max drawdown;
- equal-market mean 5% expected shortfall;
- equal-market mean annualized turnover;
- equal-market mean equal-vol annualized return;
- count of markets with positive mean return;
- count of markets with Sharpe improvement versus the frozen comparator.

Do not rank policies by one scalar metric alone.

## Temporal robustness

Repeat unchanged policy metrics in:

- 2010–2014;
- 2015–2019;
- 2020–2026.

The 2015–2019 slice remains a required stress era and may not be tuned away.

The temporal question is not whether every era has positive Sharpe. It is whether the risk-adjusted improvement versus the relevant frozen comparator persists or flips materially.

## Primary decision language

A policy may be described as showing **in-sample risk-adjusted edge** only if the evidence broadly supports all of the following:

1. Sharpe-like ratio improves versus its relevant frozen comparator on an equal-market basis.
2. The Sharpe improvement occurs in a clear majority of markets.
3. Equal-vol scaling leaves higher normalized return than the comparator in a clear majority of markets.
4. Drawdown and/or left-tail risk improve rather than being hidden by a few large gains.
5. The result is not explained solely by one direction or one temporal era.
6. Turnover does not explode enough to make the result obviously operationally implausible.

Allowed wording remains **risk-adjusted edge in normalized underlying-move units**.

Do not call the result stable alpha, executable alpha, or production profitability without instrument mapping and out-of-sample evidence.

## Guardrails

- no new thresholds;
- no new exposure percentages;
- no market-specific scaling rule except the frozen equal-vol diagnostic;
- no separate Markup / Markdown optimization;
- no Sharpe maximization or parameter search;
- no dropping negative markets or eras;
- no classifier changes;
- no transaction-cost estimate invented for heterogeneous instruments;
- PR #80 remains Draft / unmerged.

## Intended output

Answer:

> **Do the frozen Issue #78 exposure controls improve the amount of normalized return earned per unit of risk, or are they mostly just lower-exposure versions of the same strategy?**

Refs #78, #80, #76.
