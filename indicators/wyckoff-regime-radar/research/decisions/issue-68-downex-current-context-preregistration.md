# Issue #68 — DownEx Current-Context Preregistration

Status: discovery-only counterfactual. Production C-2 remains frozen.

## Trigger

FR10Y vs DE10Y attribution has localized the cross-market semantic split to the direct `downsideExhaustionGate` route inside S1 Accumulation. The indirect MarkdownContinuation route is negligible.

The production S1 gate is:

`rangeGate * bearBackgroundForAccGate * downsideExhaustionGate * supportHoldingGate * nonMarkdownContinuationGate`

where:

`bearBackgroundForAccGate = gate(max(bearBg, bearMaturityTrace), 35, 75)`

This permits historical bearish maturity trace to keep S1 eligible even after current `bearBg` has weakened.

## Primary semantic question

Should downside exhaustion be allowed to support Accumulation more strongly than the *current* bearish/down-leg context that gives exhaustion its meaning?

## Frozen counterfactual

No thresholds are changed.

Define current bearish context using the existing `bearBg` input and the exact same 35/75 bounds already used by the production Accumulation background gate:

`currentBearContextGate = gate(bearBg, 35, 75)`

Define a context-bound direct exhaustion gate:

`contextBoundDownExGate = min(downsideExhaustionGate, currentBearContextGate)`

The support-invariant diagnostic receives the same semantic bound:

`contextBoundSIDownExGate = min(issue68SIDownExGate, currentBearContextGate)`

The `min()` form is preregistered because it expresses a semantic ceiling: exhaustion may not be more active than current bearish context. It does not introduce a new weight or threshold and does not multiply two partially-active gates into an arbitrary new scale.

## Four frozen views

1. **PROD** — unchanged production C-2.
2. **PROD+CTX** — production RAW and all other stages frozen; only S1 direct DownEx gate is capped by current bear context.
3. **SI** — previously frozen support-invariant full-bp shadow.
4. **SI+CTX** — support-invariant shadow with the same current-context cap applied only to S1 direct DownEx gate.

For PROD+CTX, all non-S1 effective scores remain production values.
For SI+CTX, all non-S1 effective scores remain the existing support-invariant shadow values.

## Primary discovery window

- FR10Y 1D: 2022-01-03 through 2023-12-29.
- DE10Y 1D: same window.
- Expected semantic family: Bull yield regime.

## Measurements

- currentBearContextGate average;
- `bearBackgroundForAccGate - currentBearContextGate` average and share > 0 (trace advantage diagnostic);
- share where production DownEx gate is capped by current context;
- share where support-invariant DownEx gate is capped by current context;
- S1 gate average for PROD / PROD+CTX / SI / SI+CTX;
- S1 effective average for all four views;
- pairwise S2 effective > S1 share;
- S1 TOP share;
- Bull TOP share (S2+S3);
- TOP-changed share versus each view's baseline.

## Preregistered interpretation

- **FR Bull TOP materially improves under PROD+CTX, while DE remains reasonable, and SI+CTX no longer collapses both markets into S1:** strong evidence that stale-context permission at the direct DownEx gate is an architecture defect and that context binding is a viable repair family.
- **PROD+CTX changes little but SI+CTX materially improves:** log-domain support and stale-context routing interact; continue with transform-safe context semantics before any production proposal.
- **Both PROD+CTX and SI+CTX remain S1-heavy:** current `bearBg` is not sufficient context; do not tune 35/75. Trace the semantic definition of down-leg context instead.
- **FR improves but DE/controls are damaged:** reject this repair form as overfit.

## Controls required before any production repair

A successful FR/DE discovery result is not sufficient for merge. Before proposing a production change, run frozen controls including JP10Y, GB10Y and US10Y over their previously defined major-yield-regime windows.

## Hard boundary

No PnL, no threshold search, no weight changes, no MA changes, no Break/Structure changes, no TOP-gap or confirmation changes, and no production code modification.