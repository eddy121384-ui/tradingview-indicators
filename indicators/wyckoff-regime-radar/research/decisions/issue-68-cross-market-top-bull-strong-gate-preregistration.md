# Issue #68 — Cross-Market TOP Bull → Strong Gate Attribution Preregistration

## Status

Discovery-only attribution. Production C-2 remains frozen. No PnL, no tuning, no classifier repair.

## Why this gate exists

The 2022–2023 10Y yield-rise comparison has localized the adverse-case divergence further:

- FR10Y and DE10Y both show `RAW Bull = 0%` in the shared window.
- Both also show abnormally elevated S1 Accumulation primitives, especially Bear maturity trace and Range score.
- DE10Y nevertheless eventually acquires a Bull Formal state and its Core then stays mostly aligned.
- FR10Y never acquires Bull Formal in the same window.
- The first observable cross-market separation therefore occurs after TOP begins surfacing Bull candidates but before / at Strong qualification.

This phase asks only:

> When TOP is already in the Bull family, which frozen Strong-gate condition separates FR10Y from DE10Y?

## Fixed window and primary contrast

All charts: 1D.

Shared window:

`2022-01-03 -> 2023-12-29`

Primary contrast:

- FR10Y — catastrophic adverse case
- DE10Y — negative-rate-history control that eventually rescues to Bull Core

JP10Y may be inspected later only as a descriptive adverse control after the FR/DE interpretation is frozen.

## Frozen production gate

The existing C-2 Strong rule is not changed:

`strongCandidate = hasSharp and topVal >= dominantMin and topGap >= topGapMin and hasEvidence and not candidateConflict`

For Bull-family TOP bars (`topId == 2 or topId == 3`), report without changing semantics:

1. TOP Bull bar count and S2/S3 composition.
2. Strong pass rate.
3. Mean `topVal` and margin to `dominantMin`.
4. Mean `topGap` and margin to `topGapMin`.
5. Mean `evidenceStrength` and margin to `evidenceMin`.
6. Mean `stageSupportStrength`.
7. Pass rate of each frozen gate:
   - `hasSharp`
   - `topVal >= dominantMin`
   - `topGap >= topGapMin`
   - `hasEvidence`
   - `not candidateConflict`
8. Mutually exclusive first-blocker attribution in the same logical order as the production conjunction.
9. Confirmation context after Strong qualification:
   - fast-switch share
   - average active confirmation bars
   - longest consecutive Strong-Bull run
   - Bull Formal acquisition count

## Interpretation rules locked before results

- If one frozen Strong gate shows a large FR-vs-DE pass-rate split while upstream TOP Bull composition is comparable, localize the catastrophic FR failure to that gate family.
- If several Strong gates fail together on FR, retain a multi-gate explanation; do not select the prettiest single culprit.
- If FR and DE Strong-gate profiles are similar, do not tune Strong. Move the attribution boundary to confirmation/persistence timing.
- `candidateConflict` is descriptive only here; no override or exemption may be added in this phase.
- This audit cannot validate the earlier log-domain hypothesis. Log-domain / zero-crossing remains a separate upstream architecture question.

## Hard boundary

- no Strategy Tester, returns, PnL, Sharpe, drawdown, hit rate
- no threshold search
- no changes to `dominantMin`, `topGapMin`, `evidenceMin`, `evidenceHigh`
- no changes to `confirmBars`, fast-switch thresholds, MA lengths, smoothing, weights, Break, Structure, Heat, Range, maturity, or trace
- no component removal
- no counterfactual repair
- no Exposure / A-vs-C decision
- no Volume / MTF / Divergence / HMM rescue
- production C-2 unchanged

PR #73 must remain Draft / Open. Issue #68 must remain Open. Do not merge or close either without Eddy's explicit approval.
