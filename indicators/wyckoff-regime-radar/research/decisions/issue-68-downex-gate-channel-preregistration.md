# Issue #68 — DownEx Gate-Channel Decomposition Preregistration

Status: discovery-only causal attribution. Production C-2 remains frozen.

## Trigger

The support-invariant slope shadow and the DownEx routing decomposition show that the FR10Y/DE10Y divergence is amplified primarily through the S1 Accumulation gate route, not through S1 RAW. In the shared 2022–2023 window, a gate-only shadow collapses Bull TOP to roughly the same low level in FR and DE while RAW-only changes are much smaller.

The frozen S1 gate contains two distinct DownEx-dependent channels:

1. **direct channel**
   - `downsideExhaustion`
   - `downsideExhaustionGate`
   - multiplicative factor inside `accGate`

2. **indirect continuation channel**
   - `downsideExhaustion`
   - `markdownContinuationScore`
   - `nonMarkdownContinuationGate`
   - multiplicative factor inside `accGate`

## Primary question

Which of these two channels creates most of the FR/DE S1-gate divergence under the support-invariant slope shadow?

## Frozen counterfactual algebra

Keep production S1 RAW and every non-DownEx S1 gate factor fixed.

Let:

- `B = rangeGate * bearBackgroundForAccGate * supportHoldingGate`
- `D0 = downsideExhaustionGate`
- `D1 = support-invariant downside-exhaustion gate`
- `C0 = nonMarkdownContinuationGate`
- `C1 = support-invariant non-Markdown-continuation gate`

Then compare four S1 gate variants:

- `PROD = B * D0 * C0`
- `DIRECT-ONLY = B * D1 * C0`
- `INDIRECT-ONLY = B * D0 * C1`
- `BOTH = B * D1 * C1`

S1 effective score in every variant uses **production `accRaw`** and frozen witness multipliers. All other stage effective scores remain production values.

## Frozen population

- Window: 2022-01-03 through 2023-12-29 inclusive.
- Charts: FR10Y 1D and DE10Y 1D.
- Expected semantic family: Bull yield regime.
- No PnL.
- No threshold search.
- No weight changes.
- No production formula changes.

## Required measurements

For PROD / DIRECT-ONLY / INDIRECT-ONLY / BOTH:

1. average S1 gate;
2. average S1 effective score;
3. share `S2 EFF > S1`;
4. S1 TOP share;
5. Bull TOP share;
6. TOP-changed share vs production.

Channel diagnostics:

7. production vs shadow `downsideExhaustionGate` average;
8. production vs shadow `markdownContinuationScore` average;
9. production vs shadow `nonMarkdownContinuationGate` average;
10. share of bars where `downsideExhaustion > supportHolding` in production and shadow, because the indirect continuation term only directly depends on DownEx when DownEx wins the `max(downsideExhaustion, supportHolding)` comparison;
11. average change in S1 EFF attributable to direct channel, indirect channel, and their interaction.

## Preregistered interpretation

- **DIRECT-ONLY explains most of BOTH and INDIRECT-ONLY is small:** root localization moves to `downsideExhaustionGate` itself. The indirect continuation route is secondary.
- **INDIRECT-ONLY explains most of BOTH:** root localization moves to `markdownContinuationScore -> nonMarkdownContinuationGate` routing.
- **Both independent effects are material but interaction is small:** two real gate routes jointly amplify the transform defect; later repair must address routing architecture, not only one threshold.
- **Interaction dominates:** the multiplicative composition itself is the primary nonlinear amplifier.
- **Neither channel reproduces BOTH:** stop and audit implementation algebra before any semantic conclusion.

## Repair boundary

This audit authorizes no production repair. Any later change requires a frozen repair candidate and cross-market controls, including FR/DE plus JP/GB/US, before merge consideration.