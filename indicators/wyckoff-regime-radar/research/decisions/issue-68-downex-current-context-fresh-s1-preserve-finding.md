# Issue #68 — DownEx Current-Context Fresh-S1 Preservation Finding

Status: human-read TradingView safety result. Production C-2 remains frozen.

Branch: `research/issue-68-lifecycle-retest-symmetry-repaired`

Draft PR #73 remains Draft / Open. Issue #68 remains open.

## Frozen question

Does the already-tested current-context cap

`currentBearGate = gate(bearBg, 35, 75)`

`ctxDownExGate = min(downsideExhaustionGate, currentBearGate)`

selectively remove stale/other production S1 Accumulation while preserving a mechanically defined no-lookahead Fresh-S1 population?

Fresh-S1 was preregistered as production TOP=S1 with current `bearBg >= 35`, current `downsideExhaustion >= 35`, and `close - close[20] <= 0`.

## TradingView results supplied 2026-09-07

| Chart | PROD S1 | Fresh S1 | Fresh retained | Fresh retention | Other PROD-S1 | Other removed | Other removal | Fresh retention minus Other retention |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| JP10Y 1D | 1,488 | 479 | 377 | 78.71% | 1,009 | 602 | 59.66% | +38.37 pp |
| US10Y 1D | 1,775 | 467 | 347 | 74.30% | 1,308 | 599 | 45.80% | +20.10 pp |
| GB10Y 1D | 1,650 | 406 | 286 | 70.44% | 1,244 | 602 | 48.39% | +18.83 pp |
| pooled | 4,913 | 1,352 | 1,010 | 74.70% | 3,561 | 1,803 | 50.63% | +25.33 pp |

The pooled Other-S1 retention rate is 49.37%, versus 74.70% for Fresh-S1.

### Fresh-S1 loss destinations

- JP10Y: 102 Fresh-S1 lost; destination Bull / Neutral / Bear = 56 / 46 / 0.
- US10Y: 120 lost; 35 / 81 / 4.
- GB10Y: 120 lost; 44 / 73 / 3.
- Pooled: 342 lost; 135 / 200 / 7.

Only 7 of 342 Fresh-S1 losses route into the Bear family. Most losses become Neutral or Bull rather than reversing into the opposite semantic family.

### Gate / continuity diagnostics

- JP10Y: cap binds on 43.01% of Fresh-S1 bars; S1 gate average 0.50 -> 0.36; max Fresh run / retained run = 21 / 15.
- US10Y: cap binds on 61.88%; S1 gate average 0.50 -> 0.34; max run = 17 / 12.
- GB10Y: cap binds on 65.76%; S1 gate average 0.52 -> 0.33; max run = 11 / 11.

Fresh-S1 current-context averages remain substantial rather than trivially sitting at the lower gate boundary: average BearBg = 73.28 / 69.56 / 66.34 on JP10Y / US10Y / GB10Y, with average downside-exhaustion score = 60.80 / 68.64 / 68.04.

## Interpretation against preregistration

The preregistered positive branch is met qualitatively and consistently across all three primary controls:

- Fresh-S1 retention is materially stronger than Other-S1 retention on every chart, not just in aggregate.
- The intervention removes a large share of Other PROD-S1 while retaining roughly 70-79% of Fresh-S1.
- Fresh-S1 losses almost never route into the Bear family.
- Continuity is weakened but not erased; GB10Y preserves the full maximum Fresh run, while JP10Y and US10Y shorten but retain substantial runs.

Therefore the simple `min()` cap is **not behaving like indiscriminate S1 deletion** on these controls.

This result does **not** authorize production. Roughly 21-30% of Fresh-S1 is still lost, and the cap remains broad enough that full-history cross-regime side effects must be audited before any production proposal.

## Decision

**ADVANCE TO BROADER CROSS-REGIME REPAIR VALIDATION.**

Do not tune 35/75. Do not change weights or any other classifier component. Keep C-2 production frozen.

The next audit should test the exact same cap over full histories for stage-family churn, S1 continuity, destination routing, and adverse side effects across preregistered rates charts before any repair authorization.

## Hard boundary

No PnL. No threshold search. No weight tuning. No production edit. No merge. Do not close Issue #68.