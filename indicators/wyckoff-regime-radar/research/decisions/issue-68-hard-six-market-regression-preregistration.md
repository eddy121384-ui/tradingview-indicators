# Issue #68 — Yield-Safe HARD Six-Market Regression Preregistration

## Goal

Evaluate the exact symmetric HARD current-context cap after the yield-safe representation repair has passed runtime control checks. This phase is an A/B classifier regression, not a strategy or PnL study.

The comparison is deliberately isolated:

- A = Yield-safe C-2 baseline without HARD current-context caps.
- B = Exact same yield-safe C-2 plus HARD S1/S4 caps.

All representation logic, stage RAW formulas, thresholds, weights, witness modes, lifecycle settings, and visual semantics are identical between A and B. The only allowed A/B difference is:

- S1: `min(downsideExhaustionGate, currentBearGate)`
- S4: `min(upsideExhaustionGate, currentBullGate)`

## Markets / timeframe

Frozen panel, 1D:

1. FR10Y — motivating case, inspect 2022–2023 first.
2. US10Y
3. DE10Y
4. GB10Y
5. AU10Y
6. JP10Y

No market may be removed because it looks inconvenient.

## Primary questions

1. Does HARD reduce stale S1/S4 TOP classifications when current directional background no longer supports them?
2. Are changes symmetric between S1 and S4 rather than one-sided?
3. Does HARD avoid creating long new runs of the opposite stage merely through denominator/ranking release?
4. Are S2/S3/S5/S6 pre-normalization effective scores exact parity between A and B?
5. On bars where neither cap binds, do all TOP outputs remain exact parity?

## Mechanical invariants

For every valid bar:

- `hardS1Eff <= baselineS1Eff`.
- `hardS4Eff <= baselineS4Eff`.
- S2/S3/S5/S6 effective scores are unchanged.
- If neither cap binds, `baselineTop == hardTop`.
- HARD may change normalized weights/rankings downstream because the shared denominator changes; that is expected.
- Cross-release is allowed: another stage may become TOP even though its own effective score is unchanged.

Any violation of the first four invariants is an implementation failure and stops the regression.

## Regression observations

For each market record:

- valid bars;
- S1 cap-binding bars;
- S4 cap-binding bars;
- total TOP changes;
- baseline S1 removed by HARD;
- baseline S4 removed by HARD;
- HARD cross-release into S1;
- HARD cross-release into S4;
- changed bars ending in Bull-family (S2/S3), Bear-family (S5/S6), or opposite neutral extreme (S1/S4);
- maximum consecutive changed-bar run;
- motivating-period visual review where applicable.

The first pass is TOP/regime routing. Formal-state lifecycle effects are reviewed only after this mechanical layer is clean, so a stateful confirmation artifact cannot be mistaken for a direct gate effect.

## Acceptance / rejection logic

PASS TO FORMAL-LIFECYCLE REVIEW only if:

- all mechanical invariants hold in all six markets;
- the FR10Y 2022–2023 stale-confidence motivating case is materially reduced rather than preserved unchanged;
- no market shows a new persistent opposite-stage run attributable to cross-release;
- S1/S4 behavior remains qualitatively symmetric across the pooled panel;
- no new representation failure, NA hole, lookahead, or path-dependent routing appears.

REJECT / STOP if any invariant fails or if HARD creates a clearly persistent new lifecycle pathology in a control market.

No numeric retention target is introduced here because the intervention is safety-oriented and the stale cohort was already causally characterized in the earlier audits. We will not tune thresholds to force a pass.

## Hard boundaries

- NO PNL / Strategy Tester / Sharpe / hit rate / drawdown.
- NO threshold search.
- NO stage-weight tuning.
- NO market-specific exceptions.
- NO confirmBars change.
- NO Stateful/grace revival.
- NO representation changes unless a new reproducible domain failure is found.
- NO production-source overwrite, merge, or Issue #68 close during this regression.
