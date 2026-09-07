# Issue #68 — Current-Context Lost-Fresh Subset Audit Preregistration

Status: preregistered before reading the lost-fresh subset audit output.

Branch: `research/issue-68-lifecycle-retest-symmetry-repaired`

Production C-2 remains frozen. PR #73 stays Draft/Open. Do not merge and do not close Issue #68.

## Why this audit exists

The exact symmetric current-context intervention has now shown useful selectivity across US10Y, DE10Y, FR10Y, GB10Y, AU10Y, and JP10Y: Fresh S1/S4 is generally retained more often than Other/possibly-stale S1/S4 is retained. The remaining safety question is not whether the cap can remove stale-looking state; it is whether the Fresh cases it removes are mostly marginal / fading-context cases or whether it also removes strong, early, semantically convincing Fresh anchors.

The audit therefore inspects only the already-defined no-lookahead Fresh-S1 and Fresh-S4 subsets and compares **retained vs lost** cases. It does not alter the intervention.

## Frozen intervention

S1 exact rule:

`currentBearGate = gate(bearBg, 35, 75)`

`ctxDownExGate = min(downsideExhaustionGate, currentBearGate)`

S4 exact mirror:

`currentBullGate = gate(bullBg, 35, 75)`

`ctxUpExGate = min(upsideExhaustionGate, currentBullGate)`

No 35/75 threshold search, no weight tuning, no alternative MA/Break/Structure/Strong/Formal/gamma logic, and no asymmetric S1/S4 exception.

## Frozen Fresh anchors

Fresh-S1 is unchanged:

- production TOP = S1,
- current `bearBg >= 35`,
- current `downsideExhaustion >= 35`,
- `close - close[20] <= 0`,
- no lookahead.

Fresh-S4 is the exact mirror:

- production TOP = S4,
- current `bullBg >= 35`,
- current `upsideExhaustion >= 35`,
- `close - close[20] >= 0`,
- no lookahead.

## Primary charts

Run the same audit on full available history for:

- US10Y 1D
- DE10Y 1D
- FR10Y 1D
- GB10Y 1D
- AU10Y 1D
- JP10Y 1D

No date-window selection is permitted after seeing results.

## Lost-fresh anatomy to report

For S1 and S4 separately, compare **Fresh retained** versus **Fresh lost** on:

1. production winner margin over the best non-stage runner-up;
2. fixed descriptive margin bands `<=5`, `(5,10]`, and `>10` score points (descriptive only; not repair thresholds);
3. current-context gate average;
4. exhaustion gate average;
5. cap pressure = `exhaustionGate - currentContextGate`;
6. current background score;
7. current exhaustion score;
8. absolute 20-day yield move in bp;
9. Fresh-run age in bars;
10. cap-bind share;
11. lost destination Bull / Neutral / Bear;
12. maximum production margin among Fresh-lost cases.

## Preregistered interpretation

### Outcome A — selective loss / repair candidate strengthened

Evidence points this way if, across markets and both mirrors, Fresh-lost cases are generally more marginal and/or later/fading-context than Fresh-retained cases: lower production margin, lower current-context gate, larger positive cap pressure, later Fresh-run age, or more transition-like destination. A small number of high-margin casualties is inspectable but does not by itself invalidate the intervention.

### Outcome B — blunt cap / production blocked

Evidence points this way if Fresh-lost cases are routinely high-margin, early-run, and still have current context as strong as or stronger than retained Fresh anchors, or if loss routes frequently jump directly to the opposite directional family. In that case the simple `min()` cap is too blunt even if it fixes stale S1/S4 elsewhere.

### Outcome C — mirror inconsistency

If S1 and S4 show materially different anatomy under the exact mirror, do not create a one-sided exception. Localize the asymmetry before any production change.

No numerical acceptance threshold will be invented after the output is seen; the purpose is causal/safety attribution, not classifier optimization.

## Hard boundaries

- no Strategy Tester, PnL, returns, Sharpe, drawdown, hit rate, or trade optimization;
- no threshold or weight search;
- no production edit;
- no one-sided S1/S4 patch;
- no merge;
- do not close Issue #68.
