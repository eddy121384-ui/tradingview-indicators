# Issue #68 — Downside-Exhaustion Routing Decomposition Preregistration

Status: discovery-only causal decomposition. Production C-2 remains frozen.

## Trigger

The support-invariant slope shadow replaced the log-support-dependent slope rank with a full-support 20D bp-slope percentile while keeping the same 15/55 slope-dulling gate and symmetric positive/negative slope treatment.

On the shared 2022-01-03 through 2023-12-29 Bull-yield window, FR10Y and DE10Y converged strongly under that shadow:

- slope rank: DE ~55.08, FR ~55.12;
- NegSlopeDull: DE ~64.44, FR ~65.09;
- DownEx: DE ~68.61, FR ~69.40.

However both markets became strongly S1-heavy rather than becoming correctly Bull/Markup. The support-invariant shadow increased S1 effective score much more than S2 effective score:

- DE S1 EFF ~48.31 -> ~62.21 while S2 EFF ~39.25 -> ~39.85;
- FR S1 EFF ~57.97 -> ~64.90 while S2 EFF ~44.92 -> ~45.47.

This is consistent with a routing-amplification hypothesis because downside exhaustion enters S1 twice:

1. directly inside S1 Accumulation RAW with 25% weight;
2. again through the multiplicative Accumulation gate, directly via `downsideExhaustionGate` and indirectly through the non-Markdown-continuation path.

The support-invariant shadow therefore changes both the S1 evidence level and the S1 admission multiplier at the same time.

## Primary question

When the slope-support defect is removed, is the large S1 amplification caused mainly by:

- the **RAW route** of DownEx into Accumulation evidence;
- the **Gate route** of DownEx into Accumulation admission;
- or a **multiplicative interaction / double-route synergy** between the two?

## Frozen counterfactuals

Use the existing support-invariant DownEx shadow but change only how it is routed into S1. S2 and all other production effective scores remain frozen for the pairwise/global attribution below.

For S1 define four variants:

1. **PROD**
   - production `accRaw`
   - production `accGate`

2. **RAW-ONLY**
   - support-invariant S1 RAW (`issue68SIAccRaw`)
   - production `accGate`

3. **GATE-ONLY**
   - production `accRaw`
   - support-invariant S1 gate (`issue68SIAccGate`)

4. **BOTH / S1-ONLY FULL**
   - support-invariant S1 RAW
   - support-invariant S1 gate

All four use the same frozen production S1 Volume/MTF/Divergence multipliers.

For clean S1 attribution, compare each S1 variant against **production** `markupEff` and against the other five **production** stage effective scores. Do not let S2 or other stages inherit support-invariant changes in this decomposition.

## Measurements

For each market over the frozen window:

1. average S1 effective score for PROD / RAW-ONLY / GATE-ONLY / BOTH;
2. change in average S1 EFF from PROD for each counterfactual;
3. share of bars with production S2 EFF > each S1 variant;
4. global TOP occupancy of S1 and Bull family (S2/S3) when only S1 is counterfactually replaced;
5. number/share of bars whose TOP changes versus production for each variant;
6. average S1 RAW and S1 gate under production vs support-invariant inputs;
7. additive decomposition on average S1 EFF:
   - RAW contribution = RAW-ONLY − PROD;
   - Gate contribution = GATE-ONLY − PROD;
   - Total = BOTH − PROD;
   - Interaction = Total − RAW contribution − Gate contribution.

The interaction term is descriptive causal bookkeeping for the frozen counterfactual, not a fitted parameter.

## Preregistered interpretation

- **Gate-only explains most of the S1 EFF increase / Bull-TOP collapse:** DownEx routing through the multiplicative S1 gate is the primary amplifier. Next audit should localize direct `downsideExhaustionGate` versus downstream `nonMarkdownContinuationGate`; do not alter slope semantics yet.
- **Raw-only explains most:** support-invariant slope semantics make S1 evidence itself too high. Focus next on the meaning/calibration of downside exhaustion as an Accumulation RAW component.
- **RAW-only and Gate-only are each moderate but BOTH is much larger, with a large positive interaction:** duplicated routing creates a genuine nonlinear double-count synergy. Repair research should test single-route architectures before any threshold tuning.
- **Neither S1 route explains the full-system shadow outcome:** the main amplification is outside S1 routing; inspect reciprocal UpEx/continuation propagation and other stages.

## Repair boundary

This audit authorizes no production change. No PnL, no threshold search, no weight change, no gate removal, no stage-remapping, and no merge/close action. Any repair proposal must first pass a frozen counterfactual across FR/DE plus JP/GB/US controls.
