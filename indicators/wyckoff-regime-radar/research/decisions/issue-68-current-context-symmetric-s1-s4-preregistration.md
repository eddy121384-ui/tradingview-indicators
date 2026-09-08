# Issue #68 — Symmetric S1/S4 Current-Context Validation Preregistration

Status: preregistered classifier-repair safety audit only. Production C-2 remains frozen.

Branch: `research/issue-68-lifecycle-retest-symmetry-repaired`

Draft PR #73 must remain Draft / Open. Issue #68 must remain open.

## Why this audit is required

The preregistered Fresh-S1 preservation control found consistent semantic selectivity on JP10Y, US10Y, and GB10Y: current-context-consistent Fresh-S1 was retained materially more often than Other PROD-S1 while a large share of Other S1 was removed.

That is sufficient to advance the repair hypothesis, but it is not sufficient to authorize a one-sided S1 production change. C-2 was explicitly repaired for reciprocal directional symmetry in Issue #66. A production intervention that changes Accumulation without its exact Distribution mirror would silently reintroduce a structural non-isomorphism.

Therefore the next step is a frozen **paired S1/S4 counterfactual**. No independent S4 tuning is allowed.

## Frozen symmetric counterfactual

### S1 Accumulation

Use exactly the already-tested current-context cap:

`currentBearGate = gate(bearBg, 35, 75)`

`ctxDownExGate = min(downsideExhaustionGate, currentBearGate)`

Replace only the direct DownEx gate input inside S1 Accumulation effective gating.

### S4 Distribution — exact reciprocal mirror

`currentBullGate = gate(bullBg, 35, 75)`

`ctxUpExGate = min(upsideExhaustionGate, currentBullGate)`

Replace only the direct UpEx gate input inside S4 Distribution effective gating.

The S4 formula must be the exact directional mirror of the S1 formula. The 35/75 bounds are inherited from the existing production current-background gate range; they are not tunable parameters in this audit.

Everything else remains frozen: RAW definitions, all other gates, S2/S3/S5/S6, stage weights, smoothing, gamma, MA lengths, Break, Structure, Strong, Formal, Volume, MTF, Divergence, and lifecycle logic.

## No-lookahead semantic preservation anchors

### Fresh-S1

A bar is Fresh-S1 only when:

1. production global TOP = S1;
2. current `bearBg >= 35`;
3. current `downsideExhaustion >= 35`;
4. `close - close[20] <= 0`.

### Fresh-S4

The exact reciprocal anchor:

1. production global TOP = S4;
2. current `bullBg >= 35`;
3. current `upsideExhaustion >= 35`;
4. `close - close[20] >= 0`.

The 20-bar conditions are sign-only and introduce no magnitude threshold. `Other PROD-S1` and `Other PROD-S4` are the complements within their respective production TOP populations.

These are semantic preservation controls, not ground-truth labels.

## Primary chart scope

Run full mechanically eligible history after the frozen warm-up on:

- JP10Y 1D
- US10Y 1D
- GB10Y 1D
- FR10Y 1D
- DE10Y 1D

The first three are prior major-Bull / Fresh-S1 controls. FR10Y and DE10Y are the adverse rates cases that motivated the S1 persistence investigation. Do not hand-pick event windows from counterfactual output.

## Required measurements

For both S1 and S4 on every chart report:

- production TOP count;
- Fresh count and Fresh share of production stage;
- Fresh retained under the paired CTX counterfactual;
- Fresh lost and destination family;
- Other production-stage removed;
- production vs paired-CTX stage gate average on Fresh bars;
- cap-bind share on Fresh bars;
- average current-background gate and exhaustion gate on Fresh bars;
- average current background score and exhaustion score on Fresh bars;
- maximum consecutive Fresh run and maximum consecutive Fresh-retained run.

Also report global paired-counterfactual diagnostics:

- number and share of valid bars whose global TOP changes;
- production S1 -> non-S1 count;
- production S4 -> non-S4 count;
- bars entering S1 or S4 from another production TOP, if any;
- destination-family distribution of all changed TOP bars.

Because the paired intervention can only reduce the S1 and S4 effective scores, any apparent direct increase in their effective scores is a reconstruction failure.

## Symmetry contract

The audit must statically verify that the S4 intervention is the exact reciprocal algebraic mirror of S1. No separate S4 thresholds, weights, path horizons, or exception clauses may be introduced.

If the existing reciprocal-OHLC harness can be reused without changing this counterfactual, report paired-CTX TOP mirror consistency as an additional diagnostic. Failure to run the reciprocal harness does not permit a one-sided production repair; static algebraic symmetry remains mandatory.

## Interpretation frozen before results

Advance the repair hypothesis only if all of the following are qualitatively supported:

1. Fresh-S1 is retained materially more strongly than Other PROD-S1;
2. Fresh-S4 is retained materially more strongly than Other PROD-S4;
3. neither Fresh anchor is routinely routed into the opposite directional family;
4. continuity is reduced selectively rather than erased wholesale;
5. no structural asymmetry is introduced by the paired formulas;
6. full-history TOP churn is interpretable and not dominated by pathological opposite-family flips.

If S4 behaves like indiscriminate deletion even while S1 remains selective, the current-context repair is **not production-authorizable as a symmetric pair**. Do not keep the S1-only version by exception and do not tune 35/75 to rescue S4.

If both sides are selective, advance to final full-history classifier-repair validation before any production proposal.

## Hard boundary

No PnL. No Strategy Tester selection. No threshold search. No weight tuning. No production edit. No merge. Do not close Issue #68.