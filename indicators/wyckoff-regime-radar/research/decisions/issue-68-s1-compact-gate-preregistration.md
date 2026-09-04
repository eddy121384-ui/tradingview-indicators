# Issue #68 — FR10Y vs DE10Y S1 Compact Gate Root Attribution

Status: preregistered discovery audit only. No production change.

Branch: `research/issue-68-lifecycle-retest-symmetry-repaired`

Draft PR: #73 must remain Draft / Open. Issue #68 must remain Open.

## Motivation

The preceding S1/S2 effective-gate audit shows that FR10Y is not suffering from a uniquely weak S2 Markup path: FR10Y has higher average S2 RAW and S2 effective score than DE10Y, while both markets use the Breakout Markup gate as the dominant S2 path. Yet FR10Y still spends much less time with S2 as the global TOP.

This narrows the next question to S1 Accumulation persistence: which S1 gate component allows S1 to remain effective in FR10Y more persistently than in DE10Y?

## Frozen scope

Window: 2022-01-03 through 2023-12-29.
Primary pair: FR10Y vs DE10Y, daily.

No PnL. No parameter tuning. No threshold search. No changes to `breakoutBars`, stage weights, MA lengths, Strong gates, Formal confirmation, gamma, or production classifier logic.

## Audit outputs

For each market, report:

- S1 RAW / total gate / effective score averages.
- S2 RAW / total gate / effective score averages as reference only.
- Share of bars with RAW S2 > S1.
- Share of bars with EFF S2 > S1.
- Share and count of `RAW S2 > S1` bars that flip to `EFF S1 >= S2` after gates.
- Average S1 sub-gates:
  - `rangeGate`
  - `bearBackgroundForAccGate`
  - `downsideExhaustionGate`
  - `supportHoldingGate`
  - `nonMarkdownContinuationGate`
- For each bar, identify the minimum S1 sub-gate (the multiplicative bottleneck) and report each sub-gate's bottleneck share.

## Interpretation rule

1. If FR10Y has materially higher S1 total gate than DE10Y while S1 RAW is similar, the primary pathology is post-RAW S1 gating.
2. If one S1 sub-gate is both higher on average in FR10Y and rarely acts as the bottleneck there relative to DE10Y, that gate becomes the next causal candidate.
3. If S1 total gates are similar but FR10Y still has much more S1 persistence, do not tune gates; investigate time-distribution / state-history interaction next.
4. A gate is not a repair candidate merely because its average differs. Repair requires a subsequent causal shadow/counterfactual and cross-market controls.

This audit is attribution only and cannot authorize a production change.