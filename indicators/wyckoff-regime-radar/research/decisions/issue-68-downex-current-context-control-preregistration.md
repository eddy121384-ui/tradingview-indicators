# Issue #68 — DownEx Current-Context Cross-Market Control Preregistration

Status: validation/control only. Production C-2 remains frozen. No PnL, no tuning.

## Trigger

The discovery counterfactual on FR10Y and DE10Y showed that capping the direct S1 DownEx gate by current bearish context materially reduced stale S1 dominance during the 2022–2023 yield-rise regime:

`contextBoundDownExGate = min(downsideExhaustionGate, gate(bearBg, 35, 75))`

The repair family is not eligible for production consideration until it survives frozen cross-market controls.

## Frozen control windows

These windows are inherited from prior Issue #68 semantic work; they are not selected from the new context-cap output.

All charts are 1D and expected **Bull** for the displayed 10Y yield series.

1. `JP10Y 2022-01-04 -> 2024-12-30` — preregistered Core Semantic Validity validation window.
2. `US10Y 2020-08-04 -> 2023-10-19` — preregistered Core Semantic Validity validation window.
3. `GB10Y 2022-01-03 -> 2023-12-29` — previously frozen lower-error comparison window from Cross-Market Formal-Path Attribution.

No window may be moved, shortened, extended, or replaced after seeing this audit.

## Frozen counterfactual

Production is unchanged.

Only S1 Accumulation's direct DownEx gate is changed in the shadow:

- production direct gate: `downsideExhaustionGate`;
- context-bound direct gate: `min(downsideExhaustionGate, gate(bearBg, 35, 75))`.

All S1 RAW inputs, all other S1 gates, all other stage scores, ranking rules, and confirmation logic remain frozen.

## Measurements

For PROD and PROD+CTX inside each fixed control window:

- Bull TOP occupancy: S2/S3;
- Bear TOP occupancy: S5/S6;
- Neutral TOP occupancy: S1/S4;
- Bull TOP delta in percentage points;
- share of production Bull bars retained as Bull under context cap;
- share of bars lost from Bull (`PROD Bull -> CTX non-Bull`);
- share of bars rescued into Bull (`PROD non-Bull -> CTX Bull`);
- S1 TOP occupancy;
- TOP-changed share;
- longest continuous CTX Bear run.

## Existing semantic failure rule reused unchanged

To avoid inventing a new acceptance threshold, reuse the already-preregistered Core Semantic Validity hard rule for the expected Bull regime. The CTX shadow is a hard semantic FAIL if either:

1. Bear/opposite occupancy is more than 50% of scored bars; or
2. CTX remains continuously Bear/opposite for more than 63 daily bars.

This is an audit acceptance criterion, not a classifier parameter.

## Control interpretation

- **Clean control:** CTX does not create a hard semantic FAIL and does not materially convert existing Bull bars into non-Bull; Bull occupancy is preserved or improved.
- **Mixed control:** no hard FAIL, but Bull retention materially deteriorates or a large Bull-loss population appears. Do not propose production repair; localize the damaged window first.
- **Failed control:** CTX creates a hard semantic FAIL in any previously cleaner control market. Reject this repair form as unsafe.

Passing these major-regime controls is necessary but not sufficient for production. A separate preservation check on genuine S1 / fresh-exhaustion populations is still required before any production change.

## Hard boundary

- no PnL / returns / Sharpe / drawdown;
- no threshold search;
- no weight changes;
- no MA / Break / Structure / confirmation changes;
- no production C-2 change;
- PR #73 remains Draft / Open;
- Issue #68 remains Open.