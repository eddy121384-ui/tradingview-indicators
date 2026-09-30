# Issue #78 — Second-Entry / Add-Risk Economic Policy Study Preregistration

## Purpose

Definition-only Resume research is complete.

R1 (full favorable close extreme) and R5 (frozen retest-segment favorable close break) form a confirmation frontier:

- R5 is slightly earlier and broader;
- R1 is slightly later and cleaner;
- R4 (+0.5 ATR progress from t+3) remains a conservative momentum benchmark;
- no additional Resume definition is authorized in this study.

The unresolved question is economic rather than semantic:

> **When a Wyckoff Markup / Markdown episode reaches a healthy breakout / acceptance state, does waiting for Resume confirmation improve the return / risk of adding exposure, or does the confirmation tax cost more trend harvest than the extra false-resume protection is worth?**

This study compares complete causal exposure policies. It explicitly includes no-trigger / missed-opportunity cases and does not condition conclusions on triggered episodes only.

This remains in-sample discovery on normalized underlying-move units. It is not executable futures / cash PnL and does not establish production alpha.

## Frozen research principles

- universal-first;
- equal-market weighting;
- same rule across all markets;
- same rule for Markup and Markdown;
- no threshold optimization;
- no market-specific or direction-specific tuning;
- no use of future information in exposure decisions;
- 2015–2019 remains the required stress era;
- no production claim from this sample;
- PR #80 remains Draft / open / unmerged.

## Frozen sample and event construction

Reuse the accepted Issue #76 daily sample and the already-frozen Issue #78 breakout / retest construction:

- 68,118 accepted formal-stage event rows;
- 1,624 completed known-start Markup / Markdown episodes;
- same entry-ATR normalization;
- same right-censor exclusion;
- first genuine post-entry breakout only;
- breakout search begins only after the already-frozen five completed post-entry bars;
- same causal five-bar pre-breakout box;
- same t+1 ... t+3 acceptance window;
- same P0 / P1 / P2 / P3 path classification known at the close of t+3.

No event definition is changed in this study.

## Frozen exposure units

Reuse the already-preregistered Participation Ramp exposure units:

- **Probe = 25%**
- **Full = 100%**

The study does not search alternative probe sizes or add-on sizes.

The economic object being tested is therefore the timing of the additional 75 percentage points of exposure.

## Common policy architecture

All policies begin every completed formal Markup / Markdown episode at **25% Probe exposure**.

Exposure decided at close t applies only to move t -> t+1.

The policies are intentionally identical outside the P1 / P2 Resume question.

### Before a usable t+3 breakout state exists

Remain at Probe.

This includes:

- the initial formal-trend bars;
- episodes with no qualifying first breakout;
- episodes where the first breakout is too near formal-regime end to complete the frozen three-bar acceptance window.

### P0 — No-touch / Immediate Expansion

P0 is already admitted as a healthy continuation path and does not require a retest Resume.

At the close of t+3:

> raise exposure from Probe to Full for the next move.

This treatment is identical across all candidate policies.

### P3 — Failed Acceptance

P3 is negative evidence.

Remain at Probe for the rest of the formal episode.

No later recursive breakout / Resume search is allowed.

### P1 / P2 — Retest Hold / Reclaim

Only here do the candidate policies differ.

Once path state is known at the close of t+3, compare the frozen add-risk rules below.

## Candidate policies

### Policy R0 — Immediate add at t+3

For P1 / P2:

> raise from 25% to 100% immediately after the t+3 state is known.

Exposure is Full beginning with move t+3 -> t+4.

Interpretation:

> healthy retest / reclaim is already sufficient evidence; do not wait for a separate Resume trigger.

This is the no-Resume benchmark.

### Policy R5 — Local-close Resume

For P1 / P2:

- freeze the favorable CLOSE boundary of the first-touch -> t+3 retest segment exactly as preregistered;
- raise from Probe to Full only after the first later close breaks that frozen local-close boundary;
- the new exposure applies to the next move.

If R5 never triggers before formal-regime end:

> remain at Probe for the rest of the episode.

No anchor reset is allowed.

### Policy R1 — Full favorable-close Resume

For P1 / P2:

- freeze the best favorable close from breakout bar t through t+3 exactly as already defined;
- raise from Probe to Full only after the first later close exceeds that frozen R1 anchor;
- the new exposure applies to the next move.

If R1 never triggers before formal-regime end:

> remain at Probe for the rest of the episode.

No anchor reset is allowed.

### Policy R4 — +0.5 ATR momentum benchmark

For P1 / P2:

- reuse the frozen R4 anchor at t+3 +/- 0.5 entry ATR;
- raise from Probe to Full only after the first later close reaches that directional progress level;
- the new exposure applies to the next move.

If R4 never triggers before formal-regime end:

> remain at Probe for the rest of the episode.

R4 is a conservative benchmark only. It is not a new definition search.

## Diagnostic accounting baselines

Two non-candidate accounting anchors may be reported:

### Probe Only

25% exposure for the complete formal episode.

Purpose:

> measure the economic value of the 75pp add-on itself.

### Formal Hold

100% exposure for the complete formal episode.

Purpose:

> retain continuity with prior Issue #78 economic / risk-adjusted audits.

Neither accounting baseline changes the candidate-policy admission logic.

## Primary isolation rule

The primary study contains **no deterioration / damage-latch overlay** after adding risk.

Once Full is earned, the policy remains Full until formal-regime loss.

Reason:

> the purpose is to isolate the economic value of add-risk timing. Mixing Warning-First / Gentle / Balanced management into the primary comparison would confound entry confirmation with later deterioration control.

A later separately preregistered composition study may combine a surviving add-risk policy with deterioration management. No such combination is selected here.

## Normalized return accounting

Reuse the prior Issue #78 causal convention.

For every completed episode:

- one-bar underlying move is direction-aligned and divided by episode entry ATR;
- strategy return for the move equals exposure known at the prior close x normalized move;
- the formal-loss triggering move is included if the prior close was still in the formal trend;
- zero strategy return is assigned outside completed active formal episodes.

For yield series this remains yield-direction movement normalized by entry ATR, not executable bond / futures dollar PnL.

## Primary whole-system metrics

For each market x policy, construct the complete accepted daily path through the last included completed episode and report:

- cumulative normalized return;
- mean daily normalized return;
- annualized normalized return;
- annualized normalized volatility;
- Sharpe-like ratio;
- Sortino-like ratio;
- maximum drawdown;
- 5% expected shortfall / CVaR;
- 1% daily return quantile;
- average exposure;
- annualized exposure turnover.

Primary cross-market aggregation remains equal-market.

Also report, for every policy:

- markets with positive annualized normalized return;
- equal-market mean / median Sharpe-like ratio;
- equal-market mean Sortino-like ratio;
- equal-market mean max drawdown;
- equal-market mean 5% expected shortfall;
- equal-market mean average exposure;
- equal-market mean annualized turnover.

## Equal-volatility diagnostic

Reuse the existing Issue #78 equal-vol decomposition.

Within each market use Policy R0 volatility as the local reference for the Resume comparison:

`equal_vol_scale_vs_R0 = R0_vol / policy_vol`

`equal_vol_ann_return_vs_R0 = policy_ann_return x equal_vol_scale_vs_R0`

This asks:

> if a delayed Resume policy is simply safer because it carries less exposure, does scaling it back to R0 volatility recover or exceed R0 return?

No leverage cap is imposed because this is a diagnostic decomposition, not a trading recommendation.

Formal Hold equal-vol fields may also be reported for continuity, but R0 is the primary add-risk comparator.

## Primary P1 / P2 economic comparison

Whole-system metrics can dilute the actual Resume tradeoff because most exposure is common across policies.

Therefore also report the frozen P1 / P2 eligible population with **all eligible episodes retained, including no-trigger cases**.

For each policy report:

- eligible episode count;
- trigger rate / no-trigger rate;
- mean and median total episode normalized return;
- mean post-t+3 normalized return;
- mean add-on return generated by the extra 75pp exposure;
- win rate of the add-on sleeve;
- add-on turnover;
- average post-t+3 exposure;
- mean and median remaining Full-exposure bars;
- share of episodes never reaching Full.

### Economic confirmation tax

Define a direct economic confirmation-cost measure against R0:

`foregone_add_return_vs_R0 = R0_add_on_return - policy_add_on_return`

Interpretation:

- positive = waiting surrendered favorable trend harvest;
- negative = waiting avoided enough adverse movement to outperform the immediate add.

Report this on **all P1 / P2 episodes**, not only common triggers.

Also report per-market paired mean differences for R5 vs R1, but do not use the paired subset as the primary conclusion.

## Large-trend harvest / failed-trend damage slices

Reuse already-established episode MFE landmarks. Do not invent new thresholds.

Report the P1 / P2 policy comparison for:

- **MFE < 4 ATR** — failed / small trend diagnostic;
- **MFE >= 8 ATR** — large-trend harvest diagnostic.

For each slice report:

- mean total episode return;
- mean add-on return;
- average exposure;
- turnover;
- no-trigger rate;
- R0-relative foregone add-on return.

Interpretation:

> the economic value of confirmation is a tradeoff between reducing add-on damage in failed / small trends and preserving add-on harvest in large trends.

No policy may be chosen from only one slice.

## False-resume / breakout-damage diagnostic

In addition to MFE slices, report a common post-t+3 box-failure diagnostic for P1 / P2:

> whether any of the next three completed closes after t+3 re-enters the old breakout box.

This label is used only for ex-post diagnostics.

For failed-box and non-failed-box groups report each policy's:

- add-on return;
- total return;
- average exposure.

Do not create a new conditional policy from this result.

## Temporal robustness

Repeat unchanged whole-system and P1 / P2 economic comparisons for:

- 2010–2014;
- 2015–2019;
- 2020–2026.

2015–2019 remains the mandatory stress era.

No era-specific policy is allowed.

## Direction robustness

Report Markup and Markdown separately with unchanged rules.

Do not tune by direction.

## Cross-market consistency

For the primary policy deltas report:

- equal-market mean;
- median market delta;
- count of markets with the same sign.

Required direct comparisons:

- R5 vs R0;
- R1 vs R0;
- R4 vs R0;
- R5 vs R1.

Metrics for direct comparison include:

- annualized normalized return;
- Sharpe-like ratio;
- max drawdown;
- 5% expected shortfall;
- equal-vol return vs R0;
- P1 / P2 add-on return;
- MFE<4 add-on return;
- MFE>=8 add-on return.

## Interpretation / decision logic

No single scalar metric chooses a winner.

### Resume confirmation has economic value

Supported only if R5 and/or R1, relative to R0, broadly show:

- lower failed / small-trend add-on damage;
- improved drawdown and/or left-tail behavior;
- competitive whole-system normalized return;
- competitive or improved Sharpe / Sortino;
- competitive equal-vol return;
- large-trend harvest not reduced enough to erase the risk benefit;
- cross-market breadth;
- no material 2015–2019 collapse;
- no one-direction dependence.

### R5 improves the economic frontier versus R1

Supported only if its earlier / broader admission produces:

- higher add-on and/or whole-system return;
- without a material deterioration in risk-adjusted return, drawdown or expected shortfall;
- with broad market and temporal support.

### R1 earns its stricter confirmation

Supported if its lower exposure / later entry materially improves risk or failed-trend damage enough to compensate for lower trend harvest.

### R0 is sufficient

If delayed confirmation reduces return more than risk and equal-vol return does not improve, the correct conclusion is:

> the extra Resume wait is descriptive evidence but does not add economic value as an add-risk timing rule on this sample.

### R4

R4 remains a conservative benchmark. Do not promote it solely because it has the lowest raw risk or false-resume rate.

## Tail / concentration diagnostics

Report, without optimization:

- top 1% contribution to positive P1 / P2 add-on returns;
- result after removing each market's single best P1 / P2 add-on episode;
- result after removing each market's top 1% winning P1 / P2 add-on episodes.

These diagnostics test whether a policy's apparent benefit is carried by a tiny number of large trends.

## Guardrails

- no R6 / R7 / R8;
- no Resume threshold search;
- no alternative t+3 window;
- no alternate box lookback;
- no alternate probe / Full sizing;
- no damage-latch overlay in the primary study;
- no market-specific policy;
- no direction-specific policy;
- no path-specific P1 vs P2 tuning;
- no dropping no-trigger episodes;
- no conditioning the main conclusion on common-trigger episodes;
- no instrument-cost estimate invented from normalized data;
- no classifier changes;
- no merge of PR #80.

## Intended answer

> **Does the extra trend return captured by earlier add-risk (R0 / R5) compensate for its additional false-resume risk, or does stricter confirmation (R1 / R4) improve the complete policy's economic risk / return after missed opportunities are counted?**

Refs #78, #80, #76.
