# Issue #78 — R0 + Warning-First Composition Study Preregistration
## Evidence-based add-risk × frozen deterioration management

## Purpose

The Second-Entry / Add-Risk Economic Policy Study retained **R0 Immediate** as the current in-sample add-risk baseline:

- every formal Markup / Markdown episode starts at 25% Probe;
- P0 No-touch / Immediate Expansion promotes to 100% Full at t+3;
- P1 Wick Hold promotes to Full at t+3;
- P2 Reclaim promotes to Full at t+3;
- P3 Failed Acceptance remains at Probe;
- episodes without a usable B3 breakout remain at Probe.

That study deliberately used **no deterioration overlay** in order to isolate second-entry timing.

Separately, the already-frozen Warning-First study found a useful deterioration-management frontier:

- tolerate giveback <2 entry ATR;
- at 2–4 ATR reduce earned exposure by one 25 percentage-point step;
- at 4+ ATR reduce by two 25 percentage-point steps;
- latch the reduction;
- restore only after a new favorable close-path extreme.

The next question is composition rather than another signal search:

> **Does attaching the already-frozen Warning-First deterioration layer to the R0 evidence-based add-risk architecture improve the complete system's risk / return frontier without surrendering too much trend harvest?**

This is still in-sample discovery on normalized underlying-move units. It is not executable instrument PnL and cannot establish production alpha.

## Frozen research principles

- preregistration before composition results;
- universal-first;
- equal-market weighting;
- identical rules across markets;
- identical rules for Markup and Markdown;
- no new threshold, lookback, exposure level, or Resume rule;
- no future information in exposure decisions;
- 2015–2019 remains the mandatory stress era;
- no tuning to repair an unfavorable era;
- no production claim from this sample;
- PR #80 remains Draft / open / unmerged.

## Frozen sample

Reuse exactly the accepted Issue #76 daily evidence and the Issue #78 breakout / retest path construction:

- 68,118 accepted formal-stage event rows;
- 1,624 completed known-start Markup / Markdown episodes;
- 997 B3 breakout events;
- 236 P1 / P2 Resume-eligible events;
- same entry-ATR normalization;
- same right-censor exclusion;
- same first genuine post-entry breakout;
- same causal five-bar box;
- same t+1 ... t+3 acceptance window;
- same P0 / P1 / P2 / P3 state known at the close of t+3.

No event definition may change.

## Frozen add-risk architecture — R0 Immediate

Every completed formal episode begins at:

> **25% Probe**

Before a usable t+3 breakout state exists, remain at Probe.

At the close of t+3:

- P0 -> earned participation becomes 100% Full;
- P1 -> earned participation becomes 100% Full;
- P2 -> earned participation becomes 100% Full;
- P3 -> earned participation stays 25% Probe.

Episodes with no qualifying / usable B3 breakout remain at Probe.

The earned participation upgrade applies only to the next move. No same-bar hindsight action is allowed.

No later Resume trigger is required. No R5 / R1 / R4 timing gate is reintroduced.

## Frozen management layers

The primary comparison is between:

### A. R0 + No De-risk

Actual exposure equals the R0 earned participation state.

Once Full is earned, remain Full until formal-regime loss.

### B. R0 + Warning-First

Reuse the already-frozen Warning-First deterioration logic **without modification**.

The damage measure is the running favorable close-path giveback from the formal-episode entry, normalized by the episode's frozen entry ATR.

Management is active from the beginning of the formal episode; it is **not restarted at breakout or t+3**.

At any close:

- giveback <2 ATR -> zero reduction steps;
- giveback 2–4 ATR -> one 25pp reduction step;
- giveback >=4 ATR -> two 25pp reduction steps.

The reduction state is latched.

Actual exposure is:

> **max(25%, earned participation - 25pp × latched reduction steps)**

Therefore:

- earned 100% -> 75% at 2–4 ATR -> 50% at 4+ ATR;
- earned 25% remains 25% even if a warning is already latched.

A temporary giveback improvement does not restore exposure.

A **new favorable close-path extreme** resets the damage reduction to zero for the next move.

Formal regime loss sets exposure to zero.

### Important composition rule

The R0 evidence layer and Warning-First damage layer remain separate.

R0 determines what exposure has been **earned**.

Warning-First determines whether current deterioration requires actual exposure to be below that earned cap.

If Warning-First is already latched when R0 promotes an episode at t+3, the latch is **not cleared** merely because new participation was earned.

This is intentional and follows the previously frozen Warning-First semantics. No special t+3 reset is introduced.

## Secondary frozen comparators

For frontier context only, also compose R0 with the already-frozen:

### R0 + Gentle latch

- <1 ATR giveback -> 100% damage cap;
- 1–2 -> 75%;
- 2–4 -> 50%;
- 4+ -> 25%;
- latched until new favorable close-path extreme.

### R0 + Balanced latch

- <0.5 ATR -> 100%;
- 0.5–1 -> 75%;
- 1–2 -> 50%;
- 2–4 -> 25%;
- 4+ -> 0%;
- latched until new favorable close-path extreme.

These are secondary benchmarks only. No management threshold is searched.

## Accounting anchors

Retain for interpretation:

- Probe Only — 25% for the complete formal episode;
- Formal Hold — 100% for the complete formal episode.

Neither is a candidate composition rule.

## Causal ordering

At each completed close t:

1. determine the R0 earned participation state using only evidence known through t;
2. measure current favorable close-path giveback using only information through t;
3. apply the currently latched management reduction;
4. set actual exposure for move t -> t+1;
5. observe the next move;
6. if that move creates a new favorable close-path extreme, reset the management latch for the following move only.

This preserves both the prior R0 and prior damage-latch causal conventions.

## Primary whole-system metrics

For each market × policy construct the complete accepted daily normalized-return path and report:

- cumulative normalized return;
- annualized normalized return;
- annualized normalized volatility;
- Sharpe-like ratio;
- Sortino-like ratio;
- maximum drawdown;
- 5% expected shortfall / CVaR;
- 1% daily return quantile;
- average exposure;
- annualized exposure turnover.

Primary aggregation remains equal-market.

## Equal-volatility diagnostic

Use **R0 + No De-risk** as the local reference.

For each market:

`equal_vol_scale_vs_R0 = R0_vol / policy_vol`

`equal_vol_ann_return_vs_R0 = policy_ann_return × equal_vol_scale_vs_R0`

This asks whether any lower raw return from Warning-First is merely the mechanical result of carrying less risk.

Equal-vol is diagnostic only; it is not a leverage recommendation.

## Episode-level frontier diagnostics

For each policy report equal-market episode summaries for:

- all completed episodes;
- MFE <4 ATR failed / small trends;
- MFE 4–8 ATR middle trends;
- MFE >=8 ATR large trends.

Report:

- mean normalized harvest;
- median normalized harvest;
- average exposure;
- turnover;
- fraction of bars below earned participation;
- de-risk count;
- re-risk count;
- maximum reduction from earned participation.

For R0 + Warning-First versus R0 + No De-risk explicitly report:

- failed / small-trend damage improvement;
- large-trend harvest retained;
- all-episode return delta;
- turnover delta.

## Post-promotion diagnostics

For P0 / P1 / P2 episodes that earn Full at t+3, report:

- share already carrying a Warning-First latch at the promotion close;
- actual exposure for the next move after promotion;
- frequency of first 2 ATR / 4 ATR deterioration after promotion;
- harvest after promotion;
- de-risk and re-risk counts after promotion.

These are diagnostics only. They may not be used to invent a special t+3 reset or a path-specific management rule.

## Temporal robustness

Repeat the unchanged comparison for:

- 2010–2014;
- 2015–2019;
- 2020–2026.

2015–2019 is mandatory.

No era-specific management is allowed.

## Direction robustness

Report Markup and Markdown separately.

No direction-specific thresholds or exposure rules are allowed.

## Cross-market consistency

For the primary R0 + Warning-First versus R0 + No De-risk delta, report:

- equal-market mean;
- median market delta;
- number of markets with the same sign.

At minimum for:

- annualized return;
- Sharpe-like;
- Sortino-like;
- max drawdown;
- 5% expected shortfall;
- equal-vol annualized return;
- turnover;
- MFE<4 harvest;
- MFE>=8 harvest.

## Tail / concentration diagnostics

Without optimizing:

- top 1% contribution to positive episode return;
- equal-market result after removing each market's single best episode;
- equal-market result after removing each market's top 1% winning episodes.

These diagnose trend-following tail dependence.

## Decision logic

### Warning-First improves the composition frontier

Supported only if, relative to R0 + No De-risk, it shows most of:

- materially lower failed / small-trend damage;
- better max drawdown and/or left-tail risk;
- operationally acceptable turnover;
- competitive whole-system normalized return;
- competitive Sharpe / Sortino;
- competitive equal-vol return;
- sufficiently high large-trend harvest retention;
- broad cross-market support;
- no material 2015–2019 collapse;
- no one-direction dependence.

It need not dominate every metric.

### Warning-First remains only an optional defensive overlay

If it consistently improves tail / failed-trend damage but lowers raw and equal-vol return, or fails temporal robustness, retain it as a defensive risk-shaping option but do not make it the default management layer.

### Warning-First fails composition

If it loses meaningful trend harvest without material drawdown / tail improvement, increases operational churn excessively, or worsens the stress era without compensating robustness elsewhere, do not attach it to the R0 default architecture.

### Gentle / Balanced

They are secondary frozen comparators only. Do not promote them merely because they minimize one risk metric.

## Anti-overfit guardrails

- no change to R0;
- no R5 / R1 / R4 reintroduction;
- no new giveback threshold;
- no new exposure step;
- no special t+3 reset;
- no breakout-specific damage anchor;
- no stall-duration gate;
- no FVG / EMA / RSI / ADX / candlestick filter;
- no market-specific management;
- no direction-specific management;
- no P0 / P1 / P2-specific management;
- no dropping no-breakout or P3 episodes;
- no optimization on Sharpe / PnL;
- no classifier changes;
- no merge of PR #80.

## Stop rule

This composition study answers whether the **existing** evidence-based R0 add-risk layer and the **existing** Warning-First deterioration layer belong together.

If Warning-First does not improve the complete frontier under these frozen rules:

> do not invent Warning-First v2 on this sample.

The next move must instead be genuine OOS / weekly / prospective validation of the frozen surviving architecture.

If Warning-First does improve the frontier:

> freeze the composition before any new-data validation; do not continue threshold research.

## Intended answer

> **After P0 / P1 / P2 evidence earns Full exposure, does the already-frozen 2 / 4 ATR Warning-First damage latch improve the complete R0 system's risk path enough to justify the trend harvest it gives up?**

Refs #78, #80, #76.
