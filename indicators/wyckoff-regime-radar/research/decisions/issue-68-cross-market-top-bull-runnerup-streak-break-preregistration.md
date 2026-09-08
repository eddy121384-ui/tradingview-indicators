# Issue #68 — Cross-Market TOP Bull Runner-Up / Strong Streak-Break Attribution Preregistration

## Status

Discovery-only attribution. Production C-2 remains frozen. No PnL, no tuning, no classifier repair.

## Why this gate exists

The FR10Y vs DE10Y `TOP Bull -> Strong` audit localized the catastrophic separation further:

- both markets can surface Bull-family TOP bars;
- `hasSharp`, dominant weight and Evidence are not primary FR-specific blockers;
- FR10Y has materially weaker TOP-gap quality than DE10Y;
- FR10Y Strong-Bull occupancy is sparse and its longest consecutive Strong-Bull run is only 2 bars, so it never reaches a Bull Formal acquisition;
- DE10Y reaches a 5-bar Strong-Bull run and acquires Bull Formal once.

This phase asks two linked but distinct attribution questions:

1. **Runner-up competition:** when TOP is already Bull, which stage most often occupies second place and compresses `topGap`, especially on `topGap < topGapMin` bars?
2. **Strong-streak termination:** after a Strong-Bull bar, what frozen condition ends the consecutive Strong-Bull run on the next bar?

## Fixed window and primary contrast

All charts: 1D.

Shared discovery window:

`2022-01-03 -> 2023-12-29`

Primary contrast:

- FR10Y — catastrophic adverse case
- DE10Y — negative-rate-history control that eventually rescues to Bull Core

JP10Y may be inspected only after the FR/DE interpretation is frozen.

## Frozen production lineage

Use existing C-2 values without modification:

- `topId`, `secondId`
- `topVal`, `secondVal`, `topGap`
- `hasSharp`
- `dominantMin`, `topGapMin`
- `hasEvidence`
- `candidateConflict`
- `strongCandidate`
- `formalId`

Bull family is fixed as stages S2 Markup + S3 Reacc.

## Required runner-up outputs

Condition on Bull-family TOP bars only (`topId == 2 or topId == 3`).

For each possible runner-up stage S1-S6 report:

- count;
- share of all TOP-Bull bars;
- average `topGap` when that stage is runner-up;
- count and share among TOP-gap failures (`topGap < topGapMin`).

Also report family-level runner-up shares:

- Bull sibling: S2/S3;
- Neutral: S1/S4;
- Bear: S5/S6.

The audit must not reinterpret or re-rank stages.

## Required Strong-streak termination outputs

A Strong-Bull streak break is counted when the previous bar is Bull TOP + `strongCandidate`, but the current bar is not.

Attribute each break mutually exclusively in this order:

1. TOP leaves Bull family;
2. `hasSharp` fails;
3. `topVal < dominantMin`;
4. `topGap < topGapMin`;
5. `hasEvidence` fails;
6. `candidateConflict` becomes true;
7. other / residual.

Also report:

- total Strong-Bull bars;
- number of Strong-Bull streak breaks;
- longest Strong-Bull run;
- Bull Formal acquisition count.

## Interpretation rules locked before results

- If FR gap-failure bars are disproportionately associated with one runner-up stage versus DE, localize the gap compression to that stage competition.
- If S1 is not disproportionately the FR runner-up, reject the simple `S1 keeps biting S2` explanation even though S1 RAW is elevated.
- If FR and DE runner-up profiles are similar but streak-break reasons differ, move the failure boundary to temporal continuity rather than score competition.
- If both runner-up profile and streak-break profile differ, retain a two-stage explanation; do not collapse it into one culprit.
- No result from this audit authorizes changing `topGapMin`, `confirmBars`, stage weights, or any component.

## Observed FR10Y / DE10Y result — frozen before Path-Geometry audit

TradingView observations on the shared window:

- Runner-up family is overwhelmingly **Neutral** on both FR10Y and DE10Y; the simple `Bear runner-up keeps biting Bull` story is rejected.
- DE10Y: `Strong bars = 31`, `Max run = 5`, `Formal Bull acquire = 1`.
- FR10Y: `Strong bars = 5`, `Max run = 2`, `Formal Bull acquire = 0`.
- FR10Y Strong-streak breaks: Gap fail is the largest observed reason (`2 / 4 = 50%`), with TOP leaving Bull (`1 / 4 = 25%`) and Conflict (`1 / 4 = 25%`).
- DE10Y Strong-streak breaks in the observed chart are dominated by Conflict (`20 / 20`), while Gap is not the break driver.

Interpretation frozen from these results:

> The catastrophic FR failure is not explained by an opposite-family runner-up. The sharper cross-market distinction is that FR Bull leadership is too thin and temporally discontinuous: Bull TOP can appear, but top-gap quality frequently collapses and Strong-Bull runs never reach the normal confirmation length. DE can sustain Bull Strong long enough to formalize once.

This observation motivates a separate FR-vs-DE Path-Geometry / Transformation audit. It does **not** authorize any threshold or confirmation change.

## Hard boundary

- no Strategy Tester, returns, PnL, Sharpe, drawdown, hit rate
- no threshold search
- no changes to `topGapMin`, `dominantMin`, `evidenceMin`, `confirmBars`, fast-switch rules, persistence, weights, MA lengths, Break, Structure, Heat, Range, maturity or trace
- no stage removal, tie-priority change, runner-up suppression or counterfactual
- no Exposure / A-vs-C decision
- no Volume / MTF / Divergence / HMM rescue
- production C-2 unchanged

PR #73 must remain Draft / Open. Issue #68 must remain Open. Do not merge or close either without Eddy's explicit approval.
