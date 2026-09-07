# Issue #68 — DownEx Current-Context Fresh-S1 Preserve Preregistration

Status: preregistered discovery safety control only. Production C-2 remains frozen.

Branch: `research/issue-68-lifecycle-retest-symmetry-repaired`

Draft PR #73 must remain Draft / Open. Issue #68 must remain open.

## Motivation

The current-context counterfactual strongly reduces stale S1 Accumulation in the FR10Y/DE10Y 2022-2023 adverse Bull-yield case, and the preregistered JP10Y/US10Y/GB10Y major-Bull controls lose zero existing Bull TOP bars. However, the DownEx cap binds on >92% of bars in all three Bull controls. Before any repair proposal, the cap must be tested against S1 semantics that are current-context-consistent rather than stale-memory S1.

This control deliberately avoids hand-picking a historical event window after seeing the repair result.

## No-lookahead Fresh-S1 semantic anchor

A bar enters the Fresh-S1 control population only when all of the following are true using frozen production information available on that bar:

1. production global TOP is S1 Accumulation (`topId == 1`);
2. current bearish background has entered the existing production gate range (`bearBg >= 35`);
3. downside exhaustion has entered its existing production gate range (`downsideExhaustion >= 35`);
4. the current 20-bar path is not already rising (`close - close[20] <= 0`).

The values 35 are not new thresholds: they are the existing lower gate bounds already used by the production bear-background and downside-exhaustion gates. The 20-bar condition is sign-only; no magnitude threshold is introduced.

This population is called **Fresh-S1** rather than ground-truth S1. It is a no-lookahead semantic preservation control: production says S1, current downside context is still present, exhaustion evidence is active, and the recent path has not already turned into a 20-bar rise.

For contrast, **Other PROD-S1** is every production S1 TOP bar that does not meet all Fresh-S1 conditions.

## Frozen counterfactual

Use exactly the already-tested current-context cap:

`currentBearGate = gate(bearBg, 35, 75)`

`ctxDownExGate = min(downsideExhaustionGate, currentBearGate)`

Only the direct DownEx gate input to S1 Accumulation is changed. S1 RAW, all other S1 gates, S2-S6, weights, thresholds, MA lengths, Break, Structure, Strong, Formal, gamma, and all auxiliary witnesses remain frozen.

## Population scope

Use every mechanically eligible bar after the frozen rank warm-up on the chart. Do not select dates from the counterfactual output.

Primary control charts: JP10Y 1D, US10Y 1D, GB10Y 1D. FR10Y and DE10Y may be shown as secondary diagnostics but are not required for this safety decision.

## Required measurements

For each chart report:

- total production S1 TOP bars;
- Fresh-S1 count and share of production S1;
- Fresh-S1 retained as S1 under CTX;
- Fresh-S1 lost under CTX, including destination family (Bull / Neutral / Bear);
- Other PROD-S1 removed under CTX;
- average production vs CTX S1 gate on Fresh-S1 bars;
- share of Fresh-S1 bars on which the DownEx cap actually binds;
- average currentBearGate and downsideExhaustionGate on Fresh-S1 bars;
- maximum consecutive Fresh-S1 run and maximum consecutive Fresh-S1-retained run;
- reconstruction sanity: CTX TOP must be computed from the same frozen effective scores except for the capped S1 gate.

## Interpretation frozen before results

- If Fresh-S1 retention is materially stronger than Other-S1 retention while stale/other S1 is removed, the current-context cap has the desired semantic selectivity and can advance to a broader cross-regime repair-validation stage.
- If Fresh-S1 is removed at roughly the same rate as Other-S1, the simple `min()` cap is too blunt even if it improves Bull regimes. Do not tune the 35/75 bounds; replace the repair hypothesis with a time-aware/down-leg eligibility design.
- If Fresh-S1 loss is concentrated in bars where the cap binds despite strong current bearish background, inspect the context routing algebra before changing any threshold.
- If the audit has too few Fresh-S1 bars on a chart, report insufficient support rather than selecting a different favorable window.

No new pass/fail percentage threshold is introduced in this audit. The purpose is causal semantic preservation, not optimization.

## Hard boundary

No PnL. No threshold search. No weight tuning. No production edit. No merge. Do not close Issue #68.