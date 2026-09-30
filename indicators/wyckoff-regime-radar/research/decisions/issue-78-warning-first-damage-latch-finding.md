# Issue #78 — Warning-First Damage-Latch Policy Finding

## Scope

This finding executes the frozen preregistration in
`issue-78-warning-first-damage-latch-preregistration.md`.

The policy comparison is 2 frozen add-risk architectures × 4 management overlays:

- add-risk: +1 ATR one-step, progressive +0.5 / +1 / +2 ATR ladder;
- management: none, Gentle + latch, Balanced + latch, Warning-First + latch.

No threshold, exposure step, or recovery rule was changed after results were inspected.

## Result 1 — Warning-First is a clean middle frontier

### Simple +1 ATR add-risk

Failed / small MFE <4 ATR:

- no de-risk: **-1.645 ATR**
- Gentle + latch: **-1.282**
- Balanced + latch: **-1.054**
- Warning-First + latch: **-1.467**

Large MFE >=8 ATR:

- no de-risk: **+9.183 ATR**
- Gentle + latch: **+6.436**
- Balanced + latch: **+5.020**
- Warning-First + latch: **+7.641**

Warning-First therefore reduces failed-trend damage by about **10.8%** versus no de-risk while retaining about **83.2%** of no-de-risk large-trend harvest.

### Progressive add-risk ladder

Failed / small MFE <4 ATR:

- no de-risk: **-1.579 ATR**
- Gentle + latch: **-1.271**
- Balanced + latch: **-1.044**
- Warning-First + latch: **-1.394**

Large MFE >=8 ATR:

- no de-risk: **+9.056 ATR**
- Gentle + latch: **+6.445**
- Balanced + latch: **+5.029**
- Warning-First + latch: **+7.478**

Warning-First reduces failed-trend damage by about **11.7%** versus no de-risk while retaining about **82.6%** of no-de-risk large-trend harvest.

## Result 2 — Cross-market direction is exceptionally consistent

For both add-risk architectures:

- Warning-First improves failed/small-trend harvest versus **no de-risk in 9/9 markets**.
- Warning-First preserves more large-trend harvest than **Gentle in 9/9 markets**.
- Warning-First preserves more large-trend harvest than **Balanced in 9/9 markets**.
- Warning-First protects failed/small trends less than Gentle / Balanced in 9/9 markets.
- Warning-First sacrifices some large-trend harvest versus no de-risk in 9/9 markets.

That is exactly the expected Pareto ordering.

## Result 3 — Warning-First materially reduces resize churn

All-episode equal-market turnover:

### Simple +1 ATR add-risk

- no de-risk: **1.44**
- Gentle + latch: **2.27**
- Balanced + latch: **2.98**
- Warning-First + latch: **1.78**

### Progressive add-risk

- no de-risk: **1.42**
- Gentle + latch: **2.18**
- Balanced + latch: **2.86**
- Warning-First + latch: **1.77**

For the +1 ATR add-risk benchmark, MFE >=8 episodes average approximately:

- Gentle: 8.35 de-risk and 4.12 re-risk events;
- Balanced: 11.82 de-risk and 5.85 re-risk events;
- Warning-First: 4.65 de-risk and 2.30 re-risk events.

Warning-First is still an active management policy, but it is materially less twitchy.

## Result 4 — It does not improve raw all-episode harvest versus no de-risk

All-episode equal-market harvest:

### Simple +1 ATR add-risk

- no de-risk: **+0.441 ATR**
- Warning-First: **+0.339**
- Gentle: +0.267
- Balanced: +0.165

### Progressive add-risk

- no de-risk: **+0.444 ATR**
- Warning-First: **+0.333**
- Gentle: +0.275
- Balanced: +0.175

So Warning-First is not an alpha enhancer in this discovery sample.

Its value is risk-path shaping:

> less failed-trend damage and less aggressive large-trend sacrifice than the older de-risk ladders, with lower turnover.

## Result 5 — 2015–2019 remains a failure regime

Warning-First does not repair the previously documented temporal weakness.

### Simple +1 ATR add-risk

2015–2019 equal-market harvest:

- no de-risk: **-0.043 ATR**
- Warning-First: **-0.153**
- Gentle: -0.163
- Balanced: -0.190

### Progressive add-risk

- no de-risk: **-0.052**
- Warning-First: **-0.160**
- Gentle: -0.179
- Balanced: -0.186

Do not tune this era away.

## Result 6 — Add-risk architecture still does not resolve into one winner

Once Warning-First management is applied:

- simple +1 ATR add-risk all-episode harvest: **+0.339 ATR**
- progressive add-risk all-episode harvest: **+0.333 ATR**

The two remain economically close.

The progressive version carries slightly lower exposure but does not produce a decisive management advantage.

Therefore both add-risk architectures remain useful frozen benchmarks; complexity is not yet justified solely by this sample.

## Research decision

**Warning-First passes as a useful de-risk Pareto-frontier candidate.**

It is meaningfully less aggressive than Gentle / Balanced and operationally cleaner, while still reducing failed-trend damage versus no de-risk across all nine markets.

However:

- it does not dominate no de-risk on gross harvest;
- it does not fix the 2015–2019 weakness;
- it does not establish stable profitability;
- it does not prove the progressive add-risk ladder is superior to the simple +1 ATR add-risk rule.

The practical state-machine interpretation is now:

1. begin with controlled exposure;
2. let price proof earn more exposure;
3. tolerate mild 0.5–1 ATR damage without forced cutting;
4. begin progressive de-risk only once damage reaches the 2 ATR region;
5. become more defensive at 4 ATR;
6. re-risk only after a new favorable close-path extreme.

This is still discovery architecture, not a production rule.

## Next gate

Before any production selection, the surviving architecture should be frozen and challenged on genuinely new evidence:

- heterogeneous new markets / asset classes;
- weekly data;
- or prospective observations.

If Issue #78 continues in-sample, the next useful pass is not another threshold search. It should measure executable-policy risk metrics and transaction-cost sensitivity for the frozen survivors.

Refs #78, #80 and #76.
