# Issue #78 — Evidence Basis Challenge Research Direction

## Why this track is being added

Issue #78 has produced a coherent progressive-exposure architecture, but most of the numerical proof / deterioration landmarks studied so far were expressed in **episode-entry ATR units**.

That was deliberate and useful:

- entry ATR gives a fixed causal cross-market scale;
- it makes EURUSD, USDJPY and sovereign-yield series comparable;
- it avoids a moving denominator during an episode;
- it lets exposure-management rules be tested without asset-specific point values.

However, this creates an important research dependency:

> The current findings show what works **inside an ATR-normalized architecture**. They do not prove that ATR is the uniquely correct basis for trend proof, invalidation, or risk budgeting.

The next research frontier should therefore challenge the **basis of evidence**, not optimize more ATR cutoffs.

## Updated conceptual decomposition

Future work should explicitly separate five layers that were partly conflated in earlier Issue #78 experiments.

### 1. Opportunity / regime

What market state makes a directional opportunity eligible?

Current answer: the frozen formal Markup / Markdown classifier.

No classifier retuning belongs in this track.

### 2. Proof / evidence

What observable behavior justifies increasing risk?

ATR progress is only one candidate.

Candidate evidence families include:

- absolute directional progress normalized by entry ATR;
- price-structure confirmation such as break of a frozen swing / consolidation boundary;
- repeated favorable extension / new-extreme behavior;
- failure-to-confirm / time-to-proof;
- conditional statistical evidence if it adds information beyond raw progress.

Proof should answer **why the market has earned more risk**, not merely how far price moved in one chosen unit.

### 3. Normalizer

How should heterogeneous markets be put onto a comparable scale?

Current baseline:

- fixed episode-entry ATR.

Challenger families may include:

- fixed pre-entry realized-volatility / sigma normalization;
- robust range normalization such as median true range;
- other preregistered volatility scales.

Changing the normalizer is distinct from changing the proof signal.

### 4. Invalidation / deterioration

What observable evidence means the trend has lost enough quality to stop adding or reduce risk?

Current ATR baseline:

- giveback from the running favorable extreme in entry-ATR units.

Challenger families may include:

- structural failure;
- relative retracement of the trend's earned excursion;
- failure to make a new favorable extreme within a frozen time window;
- thesis / regime-health deterioration where independently observable.

A deterioration rule should not automatically reuse the same unit merely because the add-risk rule used it.

### 5. Sizing / risk budget

How much risk should be carried after evidence changes?

Current experiments used fixed exposure fractions such as 25 / 50 / 75 / 100%.

A separate challenger family is **open-risk pyramiding**:

- position size may increase as the invalidation / stop level improves;
- nominal exposure can rise while total open risk remains approximately fixed;
- the rule should be compared with fixed-percentage exposure ladders.

This is conceptually different from "price reached +1 ATR, therefore exposure becomes 100%."

## What the Market Wizards review changes

The Market Wizards series does **not** suggest one universal indicator.

Across generations, successful traders use very different evidence:

- breakout / trend continuation;
- price structure and relative strength;
- macro thesis plus price confirmation;
- crowding and failure of expected market reaction;
- statistical pattern recognition;
- event / information catalysts;
- asymmetric payoff;
- price stops and time stops;
- volatility / range primarily as a risk and normalization tool.

The useful commonality is architectural:

> **Risk increases when evidence improves, decreases when evidence weakens, and sizing is distinct from the signal itself.**

Therefore Issue #78 should not search for "the ATR replacement." It should test whether ATR belongs mainly in the **normalization / risk-unit layer**, while proof and invalidation may be better expressed using other evidence.

## Frozen status of existing ATR work

Existing Issue #78 results are **not invalidated**.

They remain the frozen baseline architecture:

- ATR-normalized progress gives a clean causal confirmation frontier;
- directional path efficiency did not show stable incremental information beyond progress and remains diagnostic only;
- time-to-proof showed interesting but temporally unstable incremental value and remains diagnostic only;
- progressive proof ladders reshape failed-trend vs large-trend participation but did not create a clear Sharpe advantage;
- giveback is a cleaner / earlier deterioration family than pure stall duration;
- Warning-First damage management reduces drawdown / left-tail risk but did not improve equal-vol / Sharpe outcomes;
- Progressive / No de-risk is currently the closest near-Sharpe-neutral risk-path improvement.

These results define the benchmark that challenger evidence bases must beat.

## Proposed research sequence

### Track A — Normalizer challenge

Hold the basic progress concept fixed and compare a small frozen set of normalization bases.

Primary question:

> Does ATR outperform or merely approximate other cross-market volatility scales?

Do not search arbitrary lookbacks after outcomes are visible.

### Track B — Proof-basis challenge

Hold the opportunity regime fixed and compare:

1. ATR-normalized directional progress baseline;
2. preregistered price-structure proof;
3. preregistered failure-to-confirm / time evidence;
4. only a very small number of conceptually distinct candidates.

Primary question:

> At comparable confirmation cost, which evidence best separates durable continuation from failed trend states?

### Track C — Invalidation-basis challenge

Compare:

1. ATR giveback baseline;
2. relative retracement of earned favorable excursion;
3. structural failure;
4. frozen time-stop / no-new-extreme evidence.

Primary question:

> Which deterioration basis reduces bad exposure without overreacting to normal trend noise?

### Track D — Risk-budget challenge

Compare fixed exposure ladders with a frozen open-risk architecture.

Primary question:

> Can position size rise while total risk-to-invalidation remains controlled, improving return / drawdown / turnover without relying on a fixed nominal exposure ladder?

## Cross-track evaluation

Every challenger must be evaluated against the same universal-first framework:

- equal-market weighting;
- causal next-bar execution;
- failed-trend damage;
- large-trend harvest;
- annualized normalized return;
- volatility;
- Sharpe / Sortino;
- max drawdown;
- left-tail expected shortfall;
- turnover;
- equal-vol scaling;
- 2010–2014 / 2015–2019 / 2020–2026;
- Markup / Markdown diagnostics only;
- eventual new-market / weekly / prospective validation.

## Anti-overfit guardrails

- no broad indicator zoo;
- no post-hoc search over RSI / MACD / ADX / MA variants;
- no market-specific basis;
- no long / short-specific basis;
- no threshold search inside a challenger family after outcomes are visible;
- no dropping the ATR baseline because a challenger looks better;
- no treating Market Wizards anecdotes as validation;
- no production claim from the existing nine-market discovery sample.

## Research objective

The next objective is no longer:

> "What ATR threshold should control exposure?"

It is:

> **What observable evidence deserves more or less risk, what unit should normalize that evidence across markets, and can that separation improve risk-adjusted outcomes beyond the frozen ATR baseline?**

Refs #78, #81, #85, #87, #76.
