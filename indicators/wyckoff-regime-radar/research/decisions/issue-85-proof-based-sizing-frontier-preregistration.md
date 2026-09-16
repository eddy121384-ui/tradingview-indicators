# Issue #85 — Proof-Based Sizing Frontier preregistration

Date: 2026-09-16

## Purpose

Issue #81 found that early trend responsiveness is not exhausted by cumulative directional progress alone. The strongest incremental survivor was directional path efficiency, with repeated favorable frontier extension as a weaker secondary survivor.

This study asks the next economic question:

> Can those causal responsiveness signals improve position sizing relative to the existing age-only Persistence + Gentle architecture, without changing the frozen classifier and without optimizing thresholds or weights on the observed sample?

This is still in-sample research on the accepted Issue #76 sample. It is not OOS validation and does not establish stable profitability.

## Frozen sample

Reuse the exact accepted Issue #76 nine-market daily sample:

- OANDA:EURUSD
- OANDA:GBPUSD
- OANDA:USDJPY
- TVC:US10Y
- TVC:DE10Y
- TVC:FR10Y
- TVC:GB10Y
- TVC:AU10Y
- TVC:JP10Y

Expected contract:

- 68,118 accepted event rows;
- 1,624 completed known-start formal Markup / Markdown episodes.

The Issue #68 classifier remains frozen and unchanged.

## Common mechanics

All policies are evaluated on direction-aligned one-bar returns normalized by entry ATR, exactly as in the Issue #78 participation/economic-value research.

All policies use the previously frozen **Gentle damage latch** as the damage-management layer. Therefore this study isolates the participation / upgrade rule rather than simultaneously changing both participation and damage control.

Gentle damage-latch mapping remains:

- giveback < 0.5 ATR: 100%
- 0.5–1.0 ATR: 100%
- 1.0–2.0 ATR: 75%
- 2.0–4.0 ATR: 50%
- >=4.0 ATR: 25%

The final exposure on each bar is `min(participation_cap, gentle_damage_latch)`.

## Frozen policies

No additional policy may be added after results are inspected.

### P0 — Persistence + Gentle baseline

Existing accepted baseline from Issue #78.

Age-only participation cap:

- age < 5 completed moves: 25%
- age 5–9: 50%
- age 10–19: 75%
- age >=20: 100%

This is the benchmark the proof rules must beat economically.

### P1 — Excursion-Proof + Gentle baseline

Existing frozen proof baseline from Issue #78.

Participation cap is earned from the running favorable excursion already observed before the next move:

- peak < +0.5 ATR: 25%
- +0.5 to <+1.0 ATR: 50%
- +1.0 to <+2.0 ATR: 75%
- >=+2.0 ATR: 100%

These thresholds predate Issue #81 and are not selected from the new outcomes.

### P2 — Proof + Path-Efficiency Gate + Gentle

Start from the same Excursion-Proof cap as P1, but an upgrade above the 25% probe is permitted only when the direction-aligned path efficiency observed from entry through the current completed close is at least **0.50**.

`dir_eff = cumulative directional progress / total absolute directional path`.

The 0.50 cutoff is frozen as a simple geometric interpretation: at least half of the traveled path must survive as net directional progress. It is not optimized over the Issue #81 sample.

If `dir_eff < 0.50`, participation remains capped at 25% even if excursion thresholds have been reached. If `dir_eff >= 0.50`, the normal P1 excursion cap applies.

### P3 — Proof + Path Efficiency + Favorable Extension Gate + Gentle

Start from P2. In addition, an upgrade above 25% is permitted only when the current completed close itself establishes a **new favorable cumulative close-path extreme** since entry.

This uses the Issue #81 favorable-extension finding without introducing a second fitted rate threshold. It asks for fresh confirmation at the actual upgrade point rather than optimizing a historical new-high frequency cutoff.

Once an exposure tier has been earned, it is not automatically revoked merely because the next close is not a new favorable extreme; damage control remains the job of the unchanged Gentle latch. Higher participation tiers can only be newly earned on a fresh favorable extreme satisfying the path-efficiency gate.

## Timing and causality

Exposure for move `t -> t+1` may use only information known through close `t`.

No policy may use the current move to decide its own exposure.

This study therefore charges the full economic cost of waiting for proof. E5/E10 classification AUCs are not used directly as decision timestamps; the proof state is updated causally bar by bar.

## Primary economic metrics

Report per market first, then equal-market aggregation.

Primary metrics:

1. equal-market mean episode return;
2. positive-mean market count;
3. equal-market median profit factor;
4. equal-market mean max drawdown on the sequential normalized step-return path;
5. turnover;
6. break-even friction and the already-used frozen friction grid: 0.00, 0.01, 0.02, 0.05, 0.10 ATR-equivalent per unit turnover;
7. bootstrap 95% interval for equal-market mean episode return using the existing fixed seed / method;
8. leave-one-market-out minimum equal-market mean.

## Large-vs-Failed economic decomposition

Using the already-frozen Issue #78 labels only for diagnostics:

- Failed: final directional MFE < 4 entry ATR;
- Large: final directional MFE >= 8 entry ATR;
- Middle is retained in all-sample economics but excluded from the Large-vs-Failed decomposition.

For each policy report:

- mean/median return on Failed episodes;
- mean/median return on Large episodes;
- Large-trend harvest relative to P0;
- Failed-trend damage relative to P0;
- average exposure and time / bars to full participation;
- share of Large episodes that ever reach full actual exposure.

The desired frontier is not merely higher average return. A useful proof policy should reduce Failed-trend damage without destroying a disproportionate amount of Large-trend harvest.

## Temporal falsification

Repeat equal-market mean episode return and market-count diagnostics unchanged for:

- 2010–2014
- 2015–2019
- 2020–2026

The 2015–2019 slice remains a stress test, not a tuning target.

No era-specific policy changes are allowed.

## Direction diagnostic

Report Markup and Markdown separately, but do not create direction-specific rules or thresholds.

## Interpretation rules

### Economic survivor

A proof policy may be called an economic survivor only if it shows a credible trade-off versus P0 across several dimensions, especially:

- lower Failed-trend damage and/or lower drawdown;
- retains a substantial majority of Large-trend harvest;
- does not rely on one direction or one market;
- does not collapse in the 2015–2019 stress slice;
- turnover/friction does not erase the apparent benefit.

### Weak / descriptive

A policy that improves one headline metric but loses too much Large-trend participation, becomes fragile to friction, or is temporally inconsistent remains descriptive only.

### Reject

Reject if the extra gate mostly delays participation without a compensating reduction in failed-trend damage or drawdown, or if behavior is cross-market / temporal inconsistent.

## Explicit guardrails

- no classifier changes;
- no new E0 entry filter;
- no asset-specific parameters;
- no Markup/Markdown-specific parameters;
- no 2015–2019 special case;
- no threshold search;
- no weight optimizer;
- no composite score fitting;
- no best-of-many policy search;
- do not reinterpret an E10 classification advantage as an economic advantage without charging delayed participation;
- current results remain in-sample discovery until heterogeneous / prospective validation.

## Intended decision

This study should answer a narrow practical question:

> Does the trader-like rule “start small, then size up only when the market proves itself cleanly” actually improve the economic frontier, or is the extra path-quality gate just a sophisticated way to enter late?

Refs #81 #78 #76 #68.
