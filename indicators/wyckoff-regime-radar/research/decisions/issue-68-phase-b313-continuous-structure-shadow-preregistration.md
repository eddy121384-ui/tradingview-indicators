# Issue #68 Phase B3.13 — Continuous Structure Shadow Audit Preregistration

Status: preregistered diagnostic only / frozen C-2 / no performance use.

## Question

Does the current discrete Structure primitive materially delay S2-vs-S5 fresh-trend raw recognition, relative to a single locked continuous shadow that uses the same MA50/MA200 information and the same existing rank horizon?

## Frozen production baseline

Do not change C-2.

Current fresh-trend Structure difference is discrete:

- `bullStructure - bearStructure = -100 / 0 / +100` from close relative to MA50 and MA200;
- weighted S2-vs-S5 Structure edge = `0.17 * (bullStructure - bearStructure)`.

## One locked shadow only

No formula bakeoff is allowed.

Use existing C-2 diagnostics only:

- `distRank`: percentile rank of log-price displacement from MA50 normalized by symmetric ATR;
- `maturityDistRank`: percentile rank of log-price displacement from MA200 normalized by maturity symmetric ATR;
- existing `rankLen = 756`.

Define:

`continuousStructureDelta = (distRank - 50) + (maturityDistRank - 50)`

Properties:

- range remains approximately `[-100,+100]`, matching the old Structure-difference scale;
- MA50 and MA200 retain equal 50-point maximum contribution;
- no new lookback, threshold, weight, transform parameter, or fitted constant is introduced.

Shadow weighted edge:

`continuousStructureEdge = 0.17 * continuousStructureDelta`

Shadow fresh raw duel:

`shadowDirect = originalDirect - originalStructureEdge + continuousStructureEdge`

No other component changes.

## Mechanical diagnostics

On the frozen four-FX burned baseline and reciprocal OHLC:

1. verify original six-component reconstruction identity;
2. verify shadow reciprocal sign/continuous-edge symmetry at >=99% agreement;
3. retain original exact S2<->S5 raw handoffs as anchors;
4. at each original handoff, measure whether shadow raw is already target-positive at t-1 and at t;
5. measure the final contiguous target-positive shadow run ending at the original handoff (`stable lead bars`), with no arbitrary search window;
6. count original-vs-shadow raw target-side boolean transitions across scored history as a churn diagnostic;
7. report shadow sign flips that occur with no corresponding original handoff as diagnostics only.

## Engineering acceptance only

Primary PASS/FAIL is limited to:

- exact old-raw reconstruction <= 1e-9;
- no unexplained accounting;
- reciprocal shadow target-side agreement >=99%;
- reciprocal continuous-Structure-side agreement >=99%;
- no performance metrics or strategy rules.

Earlier recognition and churn are **research outputs**, not tuned acceptance thresholds.

## Human gate if mechanically coherent

Only after the mechanical audit is coherent, generate a simple TradingView shadow visual for:

- FR10Y 1D, 2021–2024, Bull — primary adverse case;
- JGB10Y 1D, 2021–2024, Bull — control;
- GB10Y / US10Y only if needed as supplementary checks.

The human question is whether the continuous shadow resolves visibly late recognition in the adverse rates reversal without obviously turning the control into rapid red/green churn.

## Hard boundary

No PnL, no Strategy Tester, no MA-length search, no weight search, no alternate continuous formulas, no threshold shopping, no production C-2 modification, and no Exposure A/C selection in B3.13.
