# Issue #87 — Responsiveness Bonus Overlay preregistration

Date: 2026-09-16

## Purpose

Issue #81 found that post-entry Market Responsiveness contains real information beyond cumulative progress, especially directional path efficiency and repeated favorable extension. Issue #85 then showed that converting that information into a hard participation gate is economically too expensive: it reduces Failed-trend damage but gives up too much Large-trend harvest.

This study tests the asymmetric alternative:

> Keep the existing Persistence + Gentle baseline intact, and use Market Responsiveness only to **reward** already-healthy winners with additional exposure.

Responsiveness may never reduce baseline exposure in this experiment.

## Frozen sample

Use exactly the accepted Issue #76 daily universe and reconstruction contract used by Issues #78 / #81 / #85:

- OANDA:EURUSD
- OANDA:GBPUSD
- OANDA:USDJPY
- TVC:US10Y
- TVC:DE10Y
- TVC:FR10Y
- TVC:GB10Y
- TVC:AU10Y
- TVC:JP10Y

Hard drift gates remain:

- 68,118 accepted event rows;
- 1,624 completed known-start formal trend episodes.

Frozen labels remain descriptive only:

- Failed: final directional MFE `< 4 entry ATR`;
- Large: final directional MFE `>= 8 entry ATR`;
- Middle: `4 <= MFE < 8`.

## Baseline exposure contract

The base position is exactly the existing **Persistence + Gentle** architecture.

Persistence participation cap:

- bars 1–5: `0.25`;
- bars 6–10: `0.50`;
- bars 11–20: `0.75`;
- bar 21 onward: `1.00`.

The existing Gentle damage latch remains unchanged. Baseline actual exposure is:

`min(persistence_cap, gentle_damage_latch)`.

No responsiveness rule may lower this value.

## Frozen bonus policies

Only three policies are allowed in this study.

### B0 — baseline

`Persistence + Gentle` unchanged.

No bonus exposure.

### B1 — E5 responsiveness bonus

After the first **5 completed post-entry daily moves**, evaluate:

- cumulative direction-aligned progress `>= +0.5 entry ATR`;
- directional path efficiency `>= 0.50`.

If both are true, the episode **earns one +0.25 bonus tier**.

Causality:

- the E5 decision uses bars 1–5 only;
- the bonus can first affect bar 6;
- no E5 condition is recomputed or optimized later.

The earned bonus may be active only while the existing Gentle damage latch is fully healthy (`1.00`). If the latch de-risks below `1.00`, bonus exposure becomes zero for those bars. If the latch later returns to `1.00`, the previously earned bonus may resume.

Total exposure is:

`baseline_actual + active_bonus`, capped at `1.25`.

### B2 — E5 + E10 two-tier responsiveness bonus

B2 uses the same first tier as B1.

After the first **10 completed post-entry daily moves**, a second +0.25 tier is earned only if:

1. the E5 first tier was already earned;
2. cumulative direction-aligned progress over bars 1–10 is `>= +1.0 entry ATR`;
3. directional path efficiency over bars 1–10 is `>= 0.50`;
4. `new_high_rate >= 0.50` over bars 1–10, where `new_high_rate` is the fraction of the first 10 cumulative close-path endpoints that establish a new favorable extreme relative to all prior completed endpoints since entry, with entry level treated as zero.

Causality:

- the E10 decision uses bars 1–10 only;
- the second tier can first affect bar 11;
- the decision is not revisited later.

Both earned tiers may be active only while the Gentle damage latch equals `1.00`.

Total exposure is capped at `1.50`.

## Why these constants are frozen

No constants are selected by Issue #87 outcomes.

- `+0.5 ATR` and `+1.0 ATR` are existing proof levels from earlier Issue #78 architecture.
- `dir_eff >= 0.50` is the already-frozen Issue #85 path-efficiency gate.
- `new_high_rate >= 0.50` is a simple majority rule, not an optimized percentile or cut point.
- `+0.25` is the existing exposure-ladder increment.
- maximum exposures `1.25` and `1.50` follow from one or two fixed +0.25 bonus tiers.

Do not test neighboring thresholds or bonus sizes after seeing results.

## Primary economic evaluation

For B0 / B1 / B2 report:

1. equal-market mean episode return;
2. positive-return market count;
3. equal-market median profit factor;
4. equal-market mean maximum drawdown;
5. turnover per episode and friction sensitivity;
6. bootstrap interval and leave-one-market-out diagnostics;
7. Failed-trend mean return and incremental damage vs B0;
8. Large-trend mean return and harvest gain vs B0;
9. Middle-trend descriptive result;
10. Markup / Markdown diagnostics;
11. 2010–2014 / 2015–2019 / 2020–2026 diagnostics;
12. bonus activation rate and average exposure;
13. descriptive return-to-drawdown efficiency.

A policy does **not** succeed merely because raw return increases after allowing leverage above 1.00. The main question is whether incremental Large-trend harvest is worth the added Failed-trend damage, drawdown, turnover, and temporal fragility.

## Interpretation rules

### Useful overlay

Evidence should show most of:

- higher equal-market return than B0;
- no collapse in cross-market breadth;
- Large-trend harvest increases materially;
- Failed-trend damage rises much less than Large-trend harvest;
- drawdown / return trade-off does not deteriorate materially;
- both Markup and Markdown remain viable;
- 2015–2019 does not reveal a qualitatively worse failure mode;
- friction does not erase the gain.

### Weak / descriptive only

Raw return improves mainly because gross exposure is larger, while drawdown, Failed-trend damage, or temporal instability rises proportionally or worse.

### Reject

No meaningful return improvement, poor breadth, disproportionate Failed-trend damage, or materially worse return/drawdown efficiency.

## Explicit guardrails

- no Issue #68 classifier changes;
- no entry filtering;
- baseline Persistence + Gentle exposure is never reduced by responsiveness;
- no asset-class-specific rules;
- no separate Markup / Markdown rules;
- no 2015–2019 special case;
- no threshold search;
- no post-outcome bonus-size changes;
- no multivariate optimization;
- this remains in-sample discovery, not OOS validation or a production sizing rule.

Refs #87 #85 #81 #78 #76 #68.
